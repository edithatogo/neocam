"""Generative contracts for the active pathway and perspective model.

Missing Hypothesis remains blocked, not a successful skipped test suite. Historical
examples remain covered by ordinary regressions; these properties target current code.
"""
from dataclasses import replace
import numpy as np
from hypothesis import given, settings, strategies as st
from src.pathways_v6 import PathwaySpec, compare_v6
from src.statewide import Parameters, Site, _base_arrays
from src.audit_v7 import sample_v7
from scripts.analyse_v7 import evaluate_perspectives

settings.register_profile('panda_ci',max_examples=100,deadline=None,derandomize=True)
settings.load_profile('panda_ci')
SITE=Site('Atherton',157,2022,'rural_proxy','regional',True)
PROBABILITY=st.floats(min_value=0,max_value=1,allow_nan=False,allow_infinity=False)
MONEY=st.floats(min_value=0,max_value=1000000,allow_nan=False,allow_infinity=False)


@given(PROBABILITY,MONEY)
def test_null_all_effects_equal_has_no_resource_benefit(reliability,cost):
    p=Parameters(odds_ratio=1,reliability=reliability,equipment_cost=cost)
    result=compare_v6([SITE],p,PathwaySpec())
    for arm in result.values():
        np.testing.assert_allclose(arm['gross_resource_benefit'],0,atol=1e-7)
        assert arm['net_saving'][0]<=1e-7


@given(PROBABILITY,PROBABILITY,st.floats(min_value=.01,max_value=10,allow_nan=False,allow_infinity=False))
def test_disjoint_paths_conserve_population(reliability,rescue,odds):
    p=Parameters(reliability=reliability,odds_ratio=odds)
    result=compare_v6([SITE],p,PathwaySpec(extra_rescue=rescue))
    for arm in result.values():
        np.testing.assert_allclose(arm['immediate_transfers']+arm['delayed_rescues']+arm['final_local'],arm['consultations'],atol=1e-8)


@given(PROBABILITY,PROBABILITY)
def test_perspective_transfers_do_not_create_social_resources(subsidy,funding):
    p=Parameters();s=PathwaySpec();x=_base_arrays(p,1)
    _,ledger,_=evaluate_perspectives([SITE],p,s,x,{},subsidy_fraction=subsidy,funding_response=funding)
    for arm in ledger.values():
        np.testing.assert_allclose(arm['state']+arm['commonwealth']+arm['patient_family'],arm['societal_bounded'],atol=1e-7)


@given(st.integers(min_value=0,max_value=2**31-1))
@settings(max_examples=25)
def test_active_shared_psa_draws_remain_paired(seed):
    p=Parameters();s=PathwaySpec();x,e=sample_v7(p,s,80,seed)
    a=compare_v6([SITE],p,s,inputs=x,structural_draws=e)
    b=compare_v6([SITE,replace(SITE,name='Mareeba')],p,s,inputs=x,structural_draws=e)
    # Economic hourly value is additive; cash capacity steps intentionally are not.
    for key in a:np.testing.assert_allclose(b[key]['net_saving'],2*a[key]['net_saving'],atol=1e-7)


@given(st.integers(min_value=0,max_value=2**31-1))
@settings(max_examples=25)
def test_current_sampler_seed_reproducibility(seed):
    a,b=sample_v7(n=50,seed=seed);c,d=sample_v7(n=50,seed=seed)
    for key in a:np.testing.assert_array_equal(a[key],c[key])
    for key in b:np.testing.assert_array_equal(b[key],d[key])


# Active v13 properties. These are required but not claimed executed without Hypothesis.
from src.activity import ActivitySpec
from src.deployment import DeploymentPolicy, eligibility_catalogue, evaluate_policy


@given(st.floats(min_value=1,max_value=5,allow_nan=False,allow_infinity=False))
def test_repeat_contacts_do_not_multiply_clinical_episodes(ratio):
    a=compare_v6([SITE])['panda']
    b=compare_v6([SITE],activity=ActivitySpec('episodes',ratio))['panda']
    np.testing.assert_allclose(a['eventual_transfers'],b['eventual_transfers'])
    np.testing.assert_allclose(a['hub_hours']*ratio,b['hub_hours'])


@given(st.floats(min_value=1,max_value=5,allow_nan=False,allow_infinity=False),PROBABILITY)
def test_policy_and_contact_population_conservation(ratio,reliability):
    sites=[SITE,replace(SITE,name='Mareeba')]
    policy=DeploymentPolicy('mixed',(('Atherton','panda'),('Mareeba','telephone')))
    result=evaluate_policy(sites,policy,eligibility_catalogue(sites),Parameters(reliability=reliability),PathwaySpec(),(),activity=ActivitySpec('contacts',ratio))
    np.testing.assert_allclose(result['eventual_transfers']+result['final_local'],result['episodes'],atol=1e-8)
    np.testing.assert_allclose(result['contacts'],ratio*result['episodes'],atol=1e-8)
