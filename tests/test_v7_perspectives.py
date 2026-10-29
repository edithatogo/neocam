"""Contracts for perspective accounting and fixed-decision regret."""
import importlib
import numpy as np
import pytest

def api():
    try:
        return importlib.import_module('src.perspectives_v7')
    except ModuleNotFoundError:
        pytest.fail('V7 perspective implementation is absent')

def test_vop_uses_fixed_expected_decision_not_oracle():
    # A wins expected under p; B wins expected under q. Fixed regret=1, oracle=5.
    p=np.array([[9.,0.],[1.,0.]])
    q=np.array([[0.,10.],[8.,0.]])
    r=api().perspective_regret(p,q)
    assert r['value']==pytest.approx(1.)
    assert r['choose_indices']==[0] and r['target_indices']==[1]

def test_vop_diagonal_and_ties():
    a=np.array([[1.,1.],[3.,3.]])
    assert api().perspective_regret(a,a)['value']==0.
    assert np.allclose(api().optimal_probabilities(a),[.5,.5])

def test_ledger_subsidy_does_not_change_societal_resources():
    m=api(); c=dict(health_cost=np.array([100.]),family_gross=np.array([40.]),
                   family_subsidy=np.array([20.]),commonwealth=np.array([30.]),provider_cost=np.array([70.]))
    a=m.reconcile_ledger(**c)
    assert a['societal']==pytest.approx([140.])
    assert a['patient_family']==pytest.approx([20.])
    assert a['state']==pytest.approx([90.])
    assert a['state']+a['commonwealth']+a['patient_family']==pytest.approx(a['societal'])
    c['family_subsidy']=np.array([0.]);b=m.reconcile_ledger(**c)
    assert np.array_equal(a['societal'],b['societal'])

def test_ledger_signed_incremental_costs_reconcile():
    a=api().reconcile_ledger(health_cost=np.array([-100.,0.]),family_gross=np.array([-40.,0.]),
       family_subsidy=np.array([-20.,0.]),commonwealth=np.array([-30.,0.]),provider_cost=np.array([10.,0.]))
    assert np.allclose(a['state']+a['commonwealth']+a['patient_family'],a['societal'])
    assert np.allclose(a['provider_chhhs'],[10,0])

@pytest.mark.parametrize('a,b',[(np.array([1]),np.array([1])),(np.ones((2,2)),np.ones((3,2))),
                              (np.array([[np.nan]]),np.array([[0.]]))])
def test_vop_rejects_invalid(a,b):
    with pytest.raises(ValueError): api().perspective_regret(a,b)
