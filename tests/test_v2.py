"""Contracts for the evidence-informed v2 model; written before implementation."""
import math
from dataclasses import replace
import numpy as np
import pytest


def api():
    from src import statewide
    return statewide


def test_public_births_reconcile_and_aliases_do_not_double_count_installations():
    m=api(); sites=m.load_sites()
    assert sum(s.births for s in sites)==46711
    assert len(sites)==65
    assert next(s.births for s in sites if s.name=='Cairns')==2223


def test_pilot_denominators_and_volume_are_distinct():
    m=api(); sites=m.select_sites(m.load_sites(),'pilot'); p=m.Parameters()
    assert sum(s.births for s in sites)==486
    result=m.evaluate(sites,p)
    assert result['consultations']==37.5
    assert result['site_count']==3


def test_primary_spoke_portfolio_excludes_hubs_and_readiness_sites():
    m=api(); sites=m.select_sites(m.load_sites(),'spokes')
    assert all(s.group not in {'hub','readiness'} for s in sites)
    assert sum(s.births for s in sites)<46711


def test_unknown_portfolio_rejected():
    with pytest.raises(ValueError): api().select_sites(api().load_sites(),'unknown')


def test_rebased_cpi_is_not_divided_across_incompatible_bases():
    m=api(); v=m.index_air_cost()
    expected=18670*102.03/(115.125*(99.73/143.6))
    assert math.isclose(v,expected)
    assert 23000<v<25000


@pytest.mark.parametrize('kwargs',[{'reliability':-0.1},{'marginal_fraction':1.1},{'life_years':0},{'equipment_cost':float('nan')},{'odds_ratio':0},{'birth_growth':-1},{'case_mix':(.5,.5,.5)},{'rescue_rate':1.2}])
def test_invalid_inputs_fail_closed(kwargs):
    with pytest.raises(ValueError): api().Parameters(**kwargs)


def test_no_effect_means_cost_increase_not_invented_savings():
    m=api(); r=m.evaluate(m.select_sites(m.load_sites(),'pilot'),m.Parameters(odds_ratio=1))
    assert r['avoided_transfers']==0
    assert r['net_saving']<0


def test_failed_video_falls_back_to_phone_not_no_consultation():
    m=api(); r=m.evaluate(m.select_sites(m.load_sites(),'pilot'),m.Parameters(reliability=0))
    assert r['avoided_transfers']==0
    assert r['programme_cost']>0


def test_critical_cases_are_not_credited_as_avoidable_transfers():
    m=api(); r=m.evaluate(m.select_sites(m.load_sites(),'pilot'),m.Parameters(case_mix=(0,0,1)))
    assert r['avoided_transfers']==0


def test_sunk_capital_changes_cost_not_effect():
    m=api(); s=m.select_sites(m.load_sites(),'pilot'); a=m.evaluate(s,m.Parameters()); b=m.evaluate(s,m.Parameters(include_capital=False))
    assert a['avoided_transfers']==b['avoided_transfers']
    assert a['programme_cost']>b['programme_cost']


def test_delayed_rescue_reduces_net_value():
    m=api(); s=m.select_sites(m.load_sites(),'pilot')
    a=m.evaluate(s,m.Parameters(rescue_rate=0));b=m.evaluate(s,m.Parameters(rescue_rate=.2))
    assert b['avoided_transfers']<a['avoided_transfers']
    assert b['net_saving']<a['net_saving']


def test_negative_effect_increases_transfers():
    m=api(); r=m.evaluate(m.select_sites(m.load_sites(),'pilot'),m.Parameters(odds_ratio=1.3))
    assert r['avoided_transfers']<0 and r['net_saving']<0


def test_zero_marginal_fraction_is_not_full_allocated_saving():
    m=api(); s=m.select_sites(m.load_sites(),'pilot'); a=m.evaluate(s,m.Parameters(marginal_fraction=0,downstream_delta=0,rescue_rate=0))
    assert a['net_saving']==-a['programme_cost']


def test_qep_missing_remains_none_and_benchmarks_are_separate():
    m=api(); r=m.funding_ledger(nwau=2,qwau=2.1,nep=7418,qep=None)
    assert r['national_benchmark']==14836
    assert r['queensland_benchmark'] is None
    assert 'combined_funding' not in r
    assert m.funding_ledger(2,2.1,7418,7000)['queensland_benchmark']==14700


def test_mchs_year_gate_does_not_claim_2026_parity():
    m=api(); assert m.mchs_support(2025)=='historical_interface_only'
    assert m.mchs_support(2026)=='official_GEN_WAU_export_required'


def test_annuity_and_price_zero_rate_limits():
    m=api(); assert m.annuity(10000,5,0)==2000
    assert m.annuity(10000,5,.05)>2000


def test_seeded_psa_reproducible_and_signed():
    m=api(); s=m.select_sites(m.load_sites(),'pilot')
    a=m.psa(s,n=500,seed=7);b=m.psa(s,n=500,seed=7)
    assert a['summary']==b['summary']
    assert np.array_equal(a['draws']['net_saving'],b['draws']['net_saving'])
    assert np.min(a['draws']['effect_or'])<1<np.max(a['draws']['effect_or'])


def test_shared_draw_doubling_does_not_reduce_systematic_uncertainty():
    m=api(); site=m.select_sites(m.load_sites(),'pilot')[0]
    p=m.Parameters(hub_annual_cost=0,capacity_step_cost=0)
    a=m.psa([site],n=300,seed=17,parameters=p)
    b=m.psa([site,replace(site,name='duplicate')],n=300,seed=17,parameters=p)
    assert np.allclose(b['draws']['net_saving'],2*a['draws']['net_saving'])


def test_clinical_extension_counts_morbid_survival_and_costs():
    m=api(); r=m.survival_extension(100,.01,.5,discount=.05)
    assert r['extra_survivors']==1
    assert r['major_morbidity_survivors']==.5
    assert r['qalys']>0 and r['costs']>0


def test_published_effect_is_not_independent_replication_in_evidence_map():
    import csv
    from pathlib import Path
    data=list(csv.DictReader((Path(__file__).parents[1]/'evidence/literature_parameter_map.csv').open()))
    assert len(data)==7
    assert 'double-count' in next(r for r in data if r['study_id']=='THAO2022')['limitations']


def test_empty_portfolio_has_no_cost():
    m=api(); r=m.evaluate([],m.Parameters())
    assert r['programme_cost']==0 and r['net_saving']==0


def test_posterior_is_not_claimed_for_researcher_priors():
    m=api(); r=m.psa(m.select_sites(m.load_sites(),'pilot'),n=100,seed=9)
    assert r['summary']['interpretation']=='conditional researcher-prior PSA; not an empirical posterior'


def test_psa_respects_explicit_critical_only_case_mix():
    m=api(); p=m.Parameters(case_mix=(0,0,1));r=m.psa(m.select_sites(m.load_sites(),'pilot'),n=100,parameters=p)
    assert np.all(r['draws']['avoided_transfers']==0)


@pytest.mark.parametrize('mode',['published','null','skeptical'])
def test_effect_structures_are_runnable(mode):
    m=api(); r=m.psa(m.select_sites(m.load_sites(),'spokes'),n=40,effect_mode=mode)
    assert np.all(np.isfinite(r['draws']['net_saving']))
    if mode=='null':assert np.all(r['draws']['avoided_transfers']==0)


@pytest.mark.parametrize('bad',[-1,0,float('nan')])
def test_invalid_cpi_fails(bad):
    with pytest.raises(ValueError):api().index_air_cost(base_cpi=bad)


@pytest.mark.parametrize('args',[(-1,5,0),(1,0,0),(1,5,-.1)])
def test_invalid_annuity_fails(args):
    with pytest.raises(ValueError):api().annuity(*args)


def test_budget_capital_replacement_and_continuation():
    m=api();s=m.select_sites(m.load_sites(),'pilot')
    a=m.budget_impact(s,6,True);b=m.budget_impact(s,6,False)
    assert a[0]['capital']==30000 and a[5]['capital']==30000
    assert a[1]['capital']==0 and sum(r['capital'] for r in b)==0
    with pytest.raises(ValueError):m.budget_impact(s,0)


@pytest.mark.parametrize('n',[1,1000001])
def test_invalid_psa_size(n):
    with pytest.raises(ValueError):api().psa([],n=n)


def test_invalid_effect_structure():
    with pytest.raises(ValueError):api().psa([],n=10,effect_mode='magic')


@pytest.mark.parametrize('p',[0,.01,.3,.7,.99,1])
@pytest.mark.parametrize('odds',[.1,1,10])
def test_odds_transformation_properties(p,odds):
    m=api(); out=m._odds(np.array([p]),np.array([odds]))[0]
    assert 0<=out<=1
    if odds==1:assert math.isclose(out,p)
    if odds<1:assert out<=p
    if odds>1:assert out>=p


def test_marginal_cost_savings_monotonicity_for_positive_effect():
    m=api();s=m.select_sites(m.load_sites(),'pilot')
    values=[m.evaluate(s,m.Parameters(marginal_fraction=f))['net_saving'] for f in np.linspace(0,1,21)]
    assert values==sorted(values)


def test_all_portfolios_preserve_coverage_partition():
    m=api();s=m.load_sites()
    assert len(m.select_sites(s,'all_public'))==65
    assert sum(x.births for x in m.select_sites(s,'rural'))>486
    assert len(m.select_sites(s,'readiness'))>0


@pytest.mark.parametrize('args',[(float('nan'),.1,.5),(10,2,.5),(10,.1,2)])
def test_invalid_survival_extension(args):
    with pytest.raises(ValueError):api().survival_extension(*args)


def test_funding_rejects_negative_and_does_not_replace_missing_units():
    m=api()
    with pytest.raises(ValueError):m.funding_ledger(-1,1,7418,7000)
    assert m.funding_ledger(1,None,7418,7000)['queensland_benchmark'] is None
