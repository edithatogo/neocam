"""Behavioural contracts for distinct five-option investment decisions."""
import importlib
from dataclasses import replace
import numpy as np
import pytest
from src.statewide import Parameters, evaluate, load_sites, select_sites, psa


def api():
    return importlib.import_module('src.strategies')


def test_five_distinct_complete_configurations():
    m = api()
    assert [a.key for a in m.STRATEGIES] == ['telephone', 'mobile', 'panda', 'fixed', 'obsbot']
    assert [a.installed_cost for a in m.STRATEGIES] == [0,45000,10000,47000,4500]
    assert not m.STRATEGIES[-1].documented_local_service


def test_telephone_is_incremental_zero_not_no_consultation():
    m=api(); s=select_sites(load_sites(),'pilot'); r=m.compare(s)
    for field in ['programme_cost','net_saving','avoided_transfers','societal_net_saving']:
        assert r['telephone'][field] == pytest.approx(0)
    assert r['telephone']['consultations'] == pytest.approx(37.5)


def test_panda_exactly_reproduces_existing_reference():
    m=api(); s=select_sites(load_sites(),'pilot'); old=evaluate(s); new=m.compare(s)['panda']
    for k in ['programme_cost','net_saving','avoided_transfers','societal_net_saving','cash_running_cost']:
        assert new[k] == pytest.approx(old[k],rel=1e-12)


def test_equal_video_effects_and_cost_order():
    r=api().compare(select_sites(load_sites(),'pilot'))
    assert len({round(r[k]['avoided_transfers'],12) for k in ('mobile','panda','fixed','obsbot')})==1
    assert r['obsbot']['net_saving'] > r['panda']['net_saving'] > r['mobile']['net_saving'] > r['fixed']['net_saving']


def test_psa_preserves_previous_panda_draws():
    m=api(); s=select_sites(load_sites(),'pilot')
    old=psa(s,n=256,seed=811)['draws']
    new=m.compare_psa(s,n=256,seed=811)['draws']['panda']
    for k in ('programme_cost','net_saving','avoided_transfers'):
        np.testing.assert_allclose(new[k],old[k],rtol=1e-12)


def test_psa_shared_effects_not_independent_unpaired_draws():
    r=api().compare_psa(select_sites(load_sites(),'pilot'),n=256,seed=811)
    np.testing.assert_array_equal(r['draws']['obsbot']['avoided_transfers'],r['draws']['panda']['avoided_transfers'])
    assert sum(v['p_optimal'] for v in r['summary'].values()) == pytest.approx(1)
    assert r['cost_only_evpi'] >=0


def test_sunk_panda_capital_does_not_make_new_obsbot_free():
    m=api(); s=select_sites(load_sites(),'pilot')
    green=m.compare(s); incumbent=m.compare(s,sunk=('panda',))
    assert incumbent['panda']['programme_cost'] == pytest.approx(green['panda']['cash_running_cost'])
    assert incumbent['obsbot']['programme_cost'] == pytest.approx(green['obsbot']['programme_cost'])
    assert incumbent['panda']['net_saving'] > incumbent['obsbot']['net_saving']


def test_no_video_benefit_costs_still_positive():
    r=api().compare(select_sites(load_sites(),'pilot'),parameters=replace(Parameters(),odds_ratio=1))
    assert r['telephone']['net_saving']==0
    assert all(r[k]['net_saving']<0 for k in ('mobile','panda','fixed','obsbot'))


def test_unusable_video_falls_back_to_phone_not_free_service():
    m=api(); s=select_sites(load_sites(),'pilot')
    r=m.compare(s,overrides={'obsbot':{'reliability':0}})
    assert r['obsbot']['avoided_transfers']==0
    assert r['obsbot']['programme_cost']>0


@pytest.mark.parametrize('override',[{'bogus':1},{'reliability':1.1},{'capital_share':-1},{'installed_cost':-5},{'workflow_per_call':True}])
def test_invalid_strategy_overrides_rejected(override):
    with pytest.raises(ValueError):api().compare(select_sites(load_sites(),'pilot'),overrides={'obsbot':override})


def test_shared_capital_allocation_does_not_reduce_full_purchase_cost():
    m=api();r=m.compare(select_sites(load_sites(),'pilot'),overrides={'mobile':{'capital_share':.1}})
    assert r['mobile']['full_purchase_capital']==135000
    assert r['mobile']['attributed_capital']==13500


def test_unknown_sunk_strategy_rejected():
    with pytest.raises(ValueError):api().compare(select_sites(load_sites(),'pilot'),sunk=('unknown',))


def test_empty_sites_rejected():
    with pytest.raises(ValueError):api().compare([])


def test_source_documentation_is_not_clinical_validation():
    assert api().STRATEGIES[2].documented_local_service
    assert not api().STRATEGIES[-1].documented_local_service


def test_duplicate_sites_rejected():
    s=select_sites(load_sites(),'pilot')
    with pytest.raises(ValueError):api().compare(s+s[:1])


@pytest.mark.parametrize('sunk',[('panda','panda'),('telephone',)])
def test_bad_sunk_set_rejected(sunk):
    with pytest.raises(ValueError):api().compare(select_sites(load_sites(),'pilot'),sunk=sunk)


@pytest.mark.parametrize('override',[
    {'reliability':np.array([True])},{'reliability':np.array([.8,.9])},
    {'reliability':np.array([[.8]])},{'reliability':'0.8'},
    {'installed_cost':np.nan},{'installed_cost':np.inf},{'life_years':0},
])
def test_nonfinite_or_wrong_shape_override_rejected(override):
    with pytest.raises(ValueError):api().compare(select_sites(load_sites(),'pilot'),overrides={'obsbot':override})


@pytest.mark.parametrize('eligible',[(),('panda','panda'),('bogus',)])
def test_invalid_eligibility_rejected(eligible):
    with pytest.raises(ValueError):api().summarise({},eligible=eligible)


def test_nonfinite_or_empty_summary_rejected():
    for a in (np.array([]),np.array([np.nan])):
        with pytest.raises(ValueError):api().summarise({'panda':{'net_saving':a}},eligible=('panda',))


def test_invalid_override_strategy_rejected():
    for name in ('telephone','unknown'):
        with pytest.raises(ValueError):api().compare(select_sites(load_sites(),'pilot'),overrides={name:{'installed_cost':5}})


def test_disabling_capital_is_not_a_false_free_procurement_claim():
    s=select_sites(load_sites(),'pilot');p=replace(Parameters(),include_capital=False)
    r=api().compare(s,parameters=p)
    assert r['mobile']['programme_cost']==pytest.approx(r['mobile']['cash_running_cost'])
    assert r['mobile']['incremental_purchase_capital']==135000
