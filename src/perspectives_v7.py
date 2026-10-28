"""Small perspective ledger and Value-of-Perspective adapter.

Method contract informed by vop_poc_nz perspective.py, commit
ad84d3090a2d97f2805a86e94a7b9614a3d1ab14. This is an independently coded
NumPy adapter, not an import or claim of execution of that whole package.
All costs supplied to the ledger are SIGNED incremental network-year amounts.
"""
from __future__ import annotations
import numpy as np


def _matrix(value: np.ndarray) -> np.ndarray:
    a=np.asarray(value,dtype=float)
    if a.ndim!=2 or min(a.shape)==0 or not np.isfinite(a).all():
        raise ValueError('Require finite draw by strategy matrix')
    return a


def optimal_probabilities(values: np.ndarray, atol: float=1e-9) -> np.ndarray:
    a=_matrix(values)
    winners=np.isclose(a,a.max(axis=1,keepdims=True),atol=atol,rtol=0)
    return (winners/winners.sum(axis=1,keepdims=True)).mean(axis=0)


def perspective_regret(choose: np.ndarray, evaluate: np.ndarray, atol: float=1e-9) -> dict:
    """Fixed current-information choice, with an explicit equal-lottery tie policy.

    Per-draw loss may be negative. Only the EXPECTATION is a regret. This is
    not perfect information and the network-year value is not population-scaled.
    Tie bounds disclose the range among equally optimal source decisions.
    """
    a,b=_matrix(choose),_matrix(evaluate)
    if a.shape!=b.shape:raise ValueError('Paired perspectives must have equal shapes')
    ma,mb=a.mean(axis=0),b.mean(axis=0)
    selected=np.flatnonzero(np.isclose(ma,ma.max(),atol=atol,rtol=0))
    target=np.flatnonzero(np.isclose(mb,mb.max(),atol=atol,rtol=0))
    loss=b[:,target].mean(axis=1)-b[:,selected].mean(axis=1)
    return {'value':max(0.,float(loss.mean())),
            'choose_indices':selected.tolist(),'target_indices':target.tolist(),
            'source_tied':len(selected)>1,'target_tied':len(target)>1,
            'tie_policy':'equal lottery over expected-value optima',
            'minimum_tie_regret':max(0.,float(mb.max()-mb[selected].max())),
            'maximum_tie_regret':max(0.,float(mb.max()-mb[selected].min())),
            'unit':'AUD per network-year; no population rescaling'}


def reconcile_ledger(*, health_cost: np.ndarray, family_gross: np.ndarray,
                     family_subsidy: np.ndarray, commonwealth: np.ndarray,
                     provider_cost: np.ndarray) -> dict[str,np.ndarray]:
    """Reconcile fiscal allocations without counting internal transfers as resources.

    State includes the family subsidy; patient/family is net of it. Provider
    CHHHS is an attribution within the health system, not an additive perspective.
    The fiscal split is a scenario, not a statutory price/payment prediction.
    """
    arrays=[np.asarray(x,dtype=float) for x in (health_cost,family_gross,family_subsidy,commonwealth,provider_cost)]
    if any(x.shape!=arrays[0].shape or not np.isfinite(x).all() for x in arrays):
        raise ValueError('Ledger inputs must be paired finite arrays of equal shape')
    h,f,s,c,p=arrays
    return {'health_system':h,'societal_bounded':h+f,'societal':h+f,
            'patient_family':f-s,'commonwealth':c,'state':h-c+s,
            'provider_chhhs':p,'family_gross':f,'family_subsidy':s}
