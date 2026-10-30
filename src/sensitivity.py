"""Exact deterministic sensitivity surfaces: design frequencies are not probabilities."""
from __future__ import annotations
from dataclasses import dataclass
from itertools import product
import numpy as np
from src.statewide import Parameters, Site, _base_arrays
from src.strategies import KEYS, compare_inputs


@dataclass(frozen=True)
class Variable:
    """A prespecified sensitivity coordinate, not an empirically fitted distribution."""
    name: str
    label: str
    low: float
    high: float
    reference: float
    rationale: str


VARIABLES = (
    Variable('odds_ratio','Video transfer odds ratio',.35,1.3,float(np.sqrt(.48)), 'Common clinical-effect uncertainty, including no effect/increased transfer'),
    Variable('calls_per_site','Calls per pilot site/year',5,25,12.5,'Wider deterministic utilisation stress test than 10–15 forecast'),
    Variable('marginal_fraction','Avoidable retrieval fraction',.1,1,.5,'Resource fraction, not full reported tariff'),
    Variable('downstream_delta','Hospital cost difference, AUD',-4000,10000,2000,'Additional local care may exceed receiving-hospital offset'),
    Variable('life_years','Equipment life, years',3,7,5,'Existing equipment-life range'),
    Variable('critical_share','Critical case share',.05,.40,.15,'Critical transfer unchanged; low/moderate remainder shares preserved'),
    Variable('common_reliability','Established-video usable connection',.8,1,.95,'Technical delivery assumption, not comparative clinical efficacy'),
    Variable('workflow_per_call','Extra video workflow, AUD/call',0,175,75,'Increment above telephone workload'),
    Variable('obsbot_installed_cost','Complete OBSBOT kit, AUD/site',2500,10000,4500,'Unquoted complete-system range; includes tablet/mount/integration'),
    Variable('obsbot_reliability','Tablet/OBSBOT usable connection',.7,1,.95,'Hypothetical alternative; not measured quality'),
    Variable('mobile_capital_share','Mobile neonatal capital attribution',.05,1,1,'Cross-use allocation only; does not reduce full procurement cash'),
    Variable('fixed_capital_share','Fixed PTZ neonatal capital attribution',.05,1,1,'Cross-use allocation only; may be infeasible at some sites'),
)
NAMES=tuple(v.name for v in VARIABLES)


def reference_design() -> np.ndarray:
    """Return the deterministic reference point in named coordinate order."""
    return np.array([v.reference for v in VARIABLES])


def from_unit(unit: np.ndarray) -> np.ndarray:
    """Map independent unit design coordinates to prespecified ranges."""
    u=np.asarray(unit,dtype=float)
    if u.ndim!=2 or u.shape[1]!=len(VARIABLES) or not np.all(np.isfinite(u)) or np.any((u<0)|(u>1)):
        raise ValueError('Expected a finite n-by-d design within [0,1]')
    low=np.array([v.low for v in VARIABLES]);high=np.array([v.high for v in VARIABLES])
    return low+u*(high-low)


def evaluate_design(sites: list[Site], design: np.ndarray, *, sunk: tuple[str,...] = (),
                    metric: str = 'net_saving') -> np.ndarray:
    """Evaluate exact five-arm outcomes for a bounded multivariable design."""
    d=np.asarray(design,dtype=float)
    if d.ndim!=2 or d.shape[0]<1 or d.shape[1]!=len(VARIABLES) or not np.all(np.isfinite(d)):
        raise ValueError('Expected finite n-by-d nonempty design')
    low=np.array([v.low for v in VARIABLES]);high=np.array([v.high for v in VARIABLES])
    if np.any(d<low-1e-10) or np.any(d>high+1e-10):
        raise ValueError('Outside prespecified deterministic range')
    if metric not in {'net_saving','societal_net_saving','programme_cost','avoided_transfers'}:
        raise ValueError('Unsupported sensitivity outcome')
    p=Parameters();x=_base_arrays(p,len(d));v={name:d[:,i] for i,name in enumerate(NAMES)}
    mapping={'odds_ratio':'odds_ratio','calls_per_site':'calls_per_pilot_site','marginal_fraction':'marginal_fraction',
             'downstream_delta':'downstream_delta','life_years':'life_years','common_reliability':'reliability',
             'workflow_per_call':'workflow_per_call'}
    for name,target in mapping.items():x[target]=v[name].copy()
    remainder=1-v['critical_share']
    x['case_mix']=np.column_stack((remainder*7/17,remainder*10/17,v['critical_share']))
    overrides={'obsbot':{'installed_cost':v['obsbot_installed_cost'],'reliability':v['obsbot_reliability']},
               'mobile':{'capital_share':v['mobile_capital_share']},'fixed':{'capital_share':v['fixed_capital_share']}}
    out=compare_inputs(sites,p,x,sunk=sunk,overrides=overrides)
    return np.column_stack([out[k][metric] for k in KEYS])


def _check_points(points: int) -> None:
    if type(points) is not int or not 2<=points<=101:
        raise ValueError('Grid resolution must be an integer between 2 and 101')


def one_way(sites: list[Site], points: int = 21, *, sunk: tuple[str,...] = ()) -> list[dict]:
    """Full curves around a fixed reference; not jointly sampled priors."""
    _check_points(points);rows=[]
    for j,var in enumerate(VARIABLES):
        d=np.tile(reference_design(),(points,1));d[:,j]=np.linspace(var.low,var.high,points)
        y=evaluate_design(sites,d,sunk=sunk)
        for i,values in enumerate(y):
            best=KEYS[int(np.argmax(values))]
            for z,key in enumerate(KEYS):
                rows.append({'parameter':var.name,'value':float(d[i,j]),'strategy':key,
                             'net_saving':float(values[z]),'best':best})
    return rows


def _design_rows(design: np.ndarray, outcome: np.ndarray, axes: list[str], kind: str) -> list[dict]:
    rows=[]
    for i,values in enumerate(outcome):
        order=np.argsort(values)
        rows.append({**{name:float(design[i,NAMES.index(name)]) for name in axes},
                     **{key:float(values[j]) for j,key in enumerate(KEYS)},
                     'best':KEYS[int(order[-1])], 'runner_up':KEYS[int(order[-2])],
                     'margin':float(values[order[-1]]-values[order[-2]]),'design_kind':kind})
    return rows


def two_way(sites: list[Site], x_name: str, y_name: str, points: int = 31,
            *, sunk: tuple[str,...] = ()) -> list[dict]:
    """Evaluate all pairs on a complete named two-dimensional grid."""
    _check_points(points)
    if x_name==y_name or x_name not in NAMES or y_name not in NAMES:
        raise ValueError('Two distinct known coordinates required')
    a,b=[NAMES.index(name) for name in (x_name,y_name)]
    va,vb=VARIABLES[a],VARIABLES[b]
    d=np.tile(reference_design(),(points**2,1))
    d[:,[a,b]]=np.array(list(product(np.linspace(va.low,va.high,points),np.linspace(vb.low,vb.high,points))))
    return _design_rows(d,evaluate_design(sites,d,sunk=sunk),[x_name,y_name],'deterministic_grid_not_probability')


def k_way(sites: list[Site], axes: list[str], levels: int = 5,
          *, sunk: tuple[str,...] = ()) -> list[dict]:
    """Exact bounded Cartesian design in selected high-value dimensions."""
    _check_points(levels)
    if not axes or len(set(axes))!=len(axes) or any(name not in NAMES for name in axes):
        raise ValueError('Unique known coordinates required')
    if levels**len(axes)>100000:
        raise ValueError('Cartesian grid exceeds 100000-point guardrail')
    indexes=[NAMES.index(name) for name in axes]
    d=np.tile(reference_design(),(levels**len(axes),1))
    d[:,indexes]=np.array(list(product(*[np.linspace(VARIABLES[i].low,VARIABLES[i].high,levels) for i in indexes])))
    return _design_rows(d,evaluate_design(sites,d,sunk=sunk),axes,'deterministic_cartesian_not_probability')


def decision_quality(predicted: np.ndarray, truth: np.ndarray) -> dict[str, float]:
    """Evaluate surrogate choices against exact outcomes, including decision regret."""
    p=np.asarray(predicted,dtype=float);t=np.asarray(truth,dtype=float)
    if p.ndim!=2 or p.shape!=t.shape or len(p)<1 or p.shape[1]!=len(KEYS) or not np.all(np.isfinite(p)) or not np.all(np.isfinite(t)):
        raise ValueError('Aligned finite n-by-five prediction and exact outcomes required')
    choice=np.argmax(p,axis=1);actual=np.argmax(t,axis=1)
    regret=t.max(axis=1)-t[np.arange(len(t)),choice]
    return {'accuracy':float(np.mean(choice==actual)), 'mean_regret':float(regret.mean()),
            'max_regret':float(regret.max()),'regret_95th':float(np.quantile(regret,.95)),
            'near_optimal_100':float(np.mean(regret<=100)),
            'near_optimal_1000':float(np.mean(regret<=1000))}
