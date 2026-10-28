"""Bounded distributions and non-interchangeable health metrics."""
import importlib
import numpy as np
import pytest

def api():
    try:return importlib.import_module('src.audit_v7')
    except ModuleNotFoundError:pytest.fail('V7 audited numerical helpers absent')

def test_beta_preserves_mean_without_clipped_boundary_mass():
    x=api().beta_mean(np.random.default_rng(1),.8,20,100000)
    assert x.mean()==pytest.approx(.8,abs=.004)
    assert np.all((x>0)&(x<1))

def test_beta_degenerate_boundaries():
    for p in [0.,1.]: assert np.all(api().beta_mean(np.random.default_rng(1),p,20,5)==p)

@pytest.mark.parametrize('p,k', [(-.1,20),(1.1,20),(.5,0),(.5,np.nan)])
def test_beta_rejects_invalid(p,k):
    with pytest.raises(ValueError):api().beta_mean(np.random.default_rng(1),p,k,3)

def test_qaly_threshold_not_effect_estimate():
    m=api(); assert m.required_health_gain(10000,50000)==pytest.approx(.2)
    assert m.required_health_gain(-10000,50000)==0
    assert m.discounted_health_years([1,1],[.5,.5],0)==1

def test_survival_and_disability_are_separate_inputs():
    m=api(); assert m.dalys(yll=5,prevalent_years=10,disability_weight=.2)==7
    with pytest.raises(ValueError):m.dalys(yll=-1,prevalent_years=10,disability_weight=.2)

def test_age_eleven_bridge_is_discounted_from_birth():
    from src.audit_v7 import discounted_health_years
    early=discounted_health_years([1]*5,[.13]*5,.05,start_year=1)
    later=discounted_health_years([1]*5,[.13]*5,.05,start_year=11)
    assert later==pytest.approx(early/(1.05**10))
