"""Site eligibility, shared hub accounting and mixed deployment decisions."""
from dataclasses import replace
import numpy as np
import pytest
from src.statewide import Parameters, Site, _base_arrays
from src.pathways_v6 import PathwaySpec, compare_v6
from src.portfolios_v7 import portfolio
from src.configuration import load_configuration
from src.activity import ActivitySpec
from pathlib import Path


def api():
    from src import deployment
    return deployment


def env(sites=None, strategy='panda', conditional=True):
    m=api();sites=sites or portfolio('pilot')
    records=m.eligibility_catalogue(sites,allow_hypothetical=conditional)
    p=m.DeploymentPolicy('test',tuple((s.name,strategy) for s in sites),conditional)
    return m,sites,records,p


def test_reported_current_operation_not_approval_everywhere():
    m,s,e,p=env(portfolio('chhhs'),conditional=False)
    with pytest.raises(ValueError,match='eligib'):m.validate_policy(s,p,e)
    keep=m.policy_catalogue(s)[1]
    m.validate_policy(s,keep,e)
    assert dict(keep.assignments)['Atherton']=='panda'
    assert dict(keep.assignments)['Cairns']=='telephone'


def test_kit_is_conditional_not_strict_eligible():
    m,s,e,p=env(strategy='obsbot')
    m.validate_policy(s,p,e)
    with pytest.raises(ValueError):m.validate_policy(s,replace(p,conditional=False),e)


@pytest.mark.parametrize('assignments', [(),(('Atherton','panda'),), (('Atherton','panda'),)*3, (('invented','panda'),)])
def test_bad_assignment_scope(assignments):
    m,s,e,p=env()
    with pytest.raises(ValueError):m.validate_policy(s,replace(p,assignments=assignments),e)


def test_unknown_and_duplicate_eligibility():
    m,s,e,p=env()
    with pytest.raises(ValueError):m.validate_policy(s,p,e+(e[0],))
    with pytest.raises(ValueError):m.Eligibility('Atherton','obsbot','approved','unverified')


def test_uniform_policy_is_exact_reference_without_retention():
    m,s,e,p=env()
    result=m.evaluate_policy(s,p,e,Parameters(),PathwaySpec(),(),retain=False)
    ref=compare_v6(s)['panda']
    for k in ref:np.testing.assert_allclose(result[k],ref[k],atol=1e-7)


def test_mixed_clinical_mass_and_retained_capital():
    m,s,e,p=env(portfolio('chhhs'))
    assets=load_configuration(Path.cwd()).owned_assets
    p=m.policy_catalogue(s)[3]  # retain Panda + new kit
    r=m.evaluate_policy(s,p,e,Parameters(),PathwaySpec(),assets)
    assert r['incremental_purchase_capital'][0]==7*4500
    assert r['contacts'][0]>=r['episodes'][0]
    assert r['eventual_transfers'][0]+r['final_local'][0]==pytest.approx(r['episodes'][0])
    table=m.policy_cash_budget(s,p,e,Parameters(),PathwaySpec(),assets)
    assert table[0]['capital']==7*4500
    assert table[2]['capital']==30000
    assert table[5]['capital']==7*4500


def test_hub_capacity_not_summed_per_group_or_site():
    sites=[Site('S1',0,2022,'readiness','regional'),Site('S2',0,2022,'readiness','regional')]
    m,s,e,p=env(sites)
    p=replace(p,assignments=(('S1','panda'),('S2','obsbot')))
    calls={'S1':np.array([300.]),'S2':np.array([300.])}
    result=m.evaluate_policy(s,p,e,Parameters(),PathwaySpec(),(),site_calls=calls)
    assert result['hub_hours'][0]==150
    assert result['hub_cash_cost'][0]==40000
    assert result['hub_capacity_blocks'][0]==1
    assert result['cash_running_cost'][0]==pytest.approx(result['local_ready_cost'][0]+result['local_workflow_cost'][0]+40000)
    budget=m.policy_cash_budget(s,p,e,Parameters(),PathwaySpec(),(),site_calls=calls)
    assert budget[0]['hub_cash_capacity']==40000


def test_single_contact_vs_repeated_clinical_cases():
    m,s,e,p=env()
    r=m.evaluate_policy(s,p,e,Parameters(),PathwaySpec(),(),activity=ActivitySpec('contacts',2))
    assert r['episodes'][0]==18.75
    assert r['contacts'][0]==37.5
    assert r['hub_hours'][0]==9.375


def test_shared_draws_and_input_immutability():
    from src.audit_v7 import sample_v7
    m,s,e,p=env();x,z=sample_v7(n=128,seed=99)
    original={k:v.copy() for k,v in x.items()}
    r=m.evaluate_policy(s,p,e,Parameters(),PathwaySpec(),(),inputs=x,structural_draws=z,retain=False)
    direct=compare_v6(s,inputs=x,structural_draws=z)['panda']
    for k in r:np.testing.assert_allclose(r[k],direct[k],atol=1e-7)
    for k in x:np.testing.assert_array_equal(x[k],original[k])


def test_more_transfers_remain_signed_not_clipped():
    m,s,e,p=env();r=m.evaluate_policy(s,p,e,Parameters(odds_ratio=1.4),PathwaySpec(),())
    assert r['avoided_transfers'][0]<0
    assert r['net_saving'][0]<0


def test_null_policy_phone_and_expired_assets():
    m,s,e,p=env(strategy='telephone')
    r=m.evaluate_policy(s,p,e,Parameters(),PathwaySpec(),())
    assert r['programme_cost'][0]==0 and r['net_saving'][0]==0
    from src.equipment import OwnedAsset
    p=replace(p,assignments=tuple((site.name,'panda') for site in s))
    expired=(OwnedAsset('Atherton','panda',0),)
    r=m.evaluate_policy(s,p,e,Parameters(),PathwaySpec(),expired)
    assert r['incremental_purchase_capital'][0]==30000


def test_policy_scope_and_life_validation():
    m,s,e,p=env()
    with pytest.raises(ValueError):m.policy_cash_budget(s,p,e,Parameters(),PathwaySpec(),(),years=True)
    with pytest.raises(ValueError):m.evaluate_policy(s,p,e,Parameters(),PathwaySpec(),(),retain='false')


def test_multiple_policies_reuse_only_identical_ephemeral_groups(monkeypatch):
    m,s,e,p=env(portfolio('chhhs'))
    policies=m.policy_catalogue(s)
    seen=[];real=m.compare_v6
    def recorded(sites,*args,**kwargs):
        seen.append(tuple(site.name for site in sites))
        return real(sites,*args,**kwargs)
    monkeypatch.setattr(m,'compare_v6',recorded)
    result=m.evaluate_policies(s,policies,e,Parameters(),PathwaySpec(),())
    assert len(result)==6
    assert len(seen)==len(set(seen))==3
    # No persisted cache: a new call with new parameters must evaluate afresh.
    changed=m.evaluate_policies(s,policies,e,Parameters(odds_ratio=1),PathwaySpec(),())
    assert len(seen)==6
    assert changed['retain_pilot_expand_obsbot']['net_saving'][0]!=result['retain_pilot_expand_obsbot']['net_saving'][0]


def test_policy_results_do_not_share_mutable_arrays():
    m,s,e,p=env(portfolio('chhhs'))
    result=m.evaluate_policies(s,m.policy_catalogue(s),e,Parameters(),PathwaySpec(),())
    first=result['retain_pilot_only']['episodes'];second=result['telephone']['episodes']
    assert not np.shares_memory(first,second)
