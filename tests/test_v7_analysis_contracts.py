import numpy as np
import pytest
from src.statewide import Parameters,_base_arrays,load_sites,select_sites
from src.pathways_v6 import PathwaySpec,compare_v6
from src.audit_v7 import sample_v7
from scripts.analyse_v7 import evaluate_perspectives


def test_subsidy_allocation_cannot_create_social_resources():
    sites=select_sites(load_sites(),'pilot');p=Parameters();s=PathwaySpec();x=_base_arrays(p,1)
    _,a,_=evaluate_perspectives(sites,p,s,x,{},subsidy_fraction=0)
    _,b,_=evaluate_perspectives(sites,p,s,x,{},subsidy_fraction=1)
    for k in a:
        assert np.allclose(a[k]['societal_bounded'],b[k]['societal_bounded'])
        assert np.allclose(a[k]['state']+a[k]['patient_family'],b[k]['state']+b[k]['patient_family'])

def test_fixed_funding_reference_is_no_claim_about_total_commonwealth_payment():
    _,a,_=evaluate_perspectives(select_sites(load_sites(),'pilot'),Parameters(),PathwaySpec(),_base_arrays(Parameters(),1),{})
    assert all(np.all(v['commonwealth']==0) for v in a.values())


def test_non_reference_beta_sampler_has_no_upper_boundary_atom():
    x,e=sample_v7(Parameters(reliability=.8,marginal_fraction=.8),PathwaySpec(hospital_marginal_fraction=.8),n=10000)
    for a in (x['reliability'],x['marginal_fraction'],e['hospital_fraction']):
        assert np.all((a>0)&(a<1))
        assert abs(a.mean()-.8)<.02


def test_default_kernel_unchanged_when_no_activity_overrides():
    sites=select_sites(load_sites(),'pilot');a=compare_v6(sites);b=compare_v6(sites,site_calls={})
    for k in a:
        for v in a[k]:assert np.array_equal(a[k][v],b[k][v])

@pytest.mark.parametrize('kw', [{'receiver_share':-1},{'subsidy_fraction':2},{'funding_response':float('nan')}])
def test_bad_perspective_fractions_rejected(kw):
    with pytest.raises(ValueError):evaluate_perspectives(select_sites(load_sites(),'pilot'),Parameters(),PathwaySpec(),_base_arrays(Parameters(),1),{},**kw)
