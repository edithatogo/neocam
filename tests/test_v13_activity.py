"""Repeated contacts do not multiply infants or clinical outcome opportunities."""
from dataclasses import replace
import numpy as np
import pytest
from src.statewide import Parameters, load_sites, select_sites
from src.pathways_v6 import PathwaySpec, compare_v6


def api():
    from src.activity import ActivitySpec
    return ActivitySpec


@pytest.mark.parametrize('basis,episodes,contacts', [('contacts',18.75,37.5),('episodes',37.5,75)])
def test_forecast_exposures(basis,episodes,contacts):
    e,c=api()(basis,2).exposures(np.array([37.5]))
    assert e[0]==episodes and c[0]==contacts


@pytest.mark.parametrize('ratio',[True,False,0,.9,float('nan'),float('inf'),'2'])
def test_invalid_ratio(ratio):
    with pytest.raises(ValueError):api()('contacts',ratio)


def test_invalid_basis():
    with pytest.raises(ValueError):api()('infants',1)


@pytest.mark.parametrize('forecast',[np.array([True]),np.array([-1]),np.array([np.nan]),np.array([]),np.array([[2]])])
def test_invalid_exposure(forecast):
    with pytest.raises(ValueError):api()().exposures(forecast)


def test_default_is_reference_equivalent():
    sites=select_sites(load_sites(),'pilot')
    a=compare_v6(sites);b=compare_v6(sites,activity=api()('contacts',1))
    for k in a:
        for name in a[k]:np.testing.assert_array_equal(a[k][name],b[k][name])
    assert a['panda']['contacts'][0]==37.5==a['panda']['episodes'][0]


def test_fixed_episode_clinical_outcomes_unchanged_and_workload_doubled():
    sites=select_sites(load_sites(),'pilot')
    a=compare_v6(sites);b=compare_v6(sites,activity=api()('episodes',2))
    for k in a:
        for field in ('eventual_transfers','delayed_rescues','final_local','care_resource_cost','avoided_transfers'):
            np.testing.assert_allclose(a[k][field],b[k][field])
    assert b['panda']['hub_hours'][0]==2*a['panda']['hub_hours'][0]
    assert b['panda']['local_workflow_cost'][0]==2*a['panda']['local_workflow_cost'][0]
    assert b['panda']['contacts'][0]==75


def test_fixed_contacts_outcomes_halved_not_time():
    sites=select_sites(load_sites(),'pilot')
    a=compare_v6(sites);b=compare_v6(sites,activity=api()('contacts',2))
    for k in a:
        for field in ('eventual_transfers','delayed_rescues','final_local','care_resource_cost','avoided_transfers'):
            np.testing.assert_allclose(.5*a[k][field],b[k][field])
    assert b['panda']['hub_hours'][0]==a['panda']['hub_hours'][0]
    assert b['panda']['capital_annualised'][0]==a['panda']['capital_annualised'][0]


def test_contact_effect_does_not_exponentiate_reliability():
    sites=select_sites(load_sites(),'pilot');p=Parameters(reliability=.5)
    a=compare_v6(sites,p);b=compare_v6(sites,p,activity=api()('episodes',3))
    np.testing.assert_allclose(a['panda']['avoided_transfers'],b['panda']['avoided_transfers'])


def test_perspective_and_budget_use_activity():
    from scripts.analyse_v7 import evaluate_perspectives
    from src.statewide import _base_arrays
    from src.configuration import load_configuration
    from src.equipment import mixed_cash_budget
    from pathlib import Path
    p=Parameters();s=PathwaySpec();sites=select_sites(load_sites(),'pilot');x=_base_arrays(p,1)
    _,ledgers,_=evaluate_perspectives(sites,p,s,x,{},activity=api()('contacts',2))
    for ledger in ledgers.values():
        np.testing.assert_allclose(ledger['state']+ledger['commonwealth']+ledger['patient_family'],ledger['societal_bounded'])
    cfg=load_configuration(Path.cwd())
    first=mixed_cash_budget(sites,'panda',cfg.owned_assets,p,s,activity=api()('episodes',2))
    base=mixed_cash_budget(sites,'panda',cfg.owned_assets,p,s)
    assert first[0]['cash_running']>base[0]['cash_running']
    assert first[0]['capital']==base[0]['capital']


@pytest.mark.parametrize('bad',[False,{},[],0,'contacts'])
def test_falsey_untyped_activity_is_not_silently_defaulted(bad):
    with pytest.raises(ValueError):compare_v6(select_sites(load_sites(),'pilot'),activity=bad)


def test_contact_overflow_rejected():
    with pytest.raises(ValueError):api()('episodes',1e308).exposures(np.array([1e308]))
