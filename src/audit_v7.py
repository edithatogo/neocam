"""Auditable probability and health-metric helpers; no clinical effect is inferred."""
from __future__ import annotations
from numbers import Real
import numpy as np
from src.pathways_v6 import PathwaySpec, sample_v6
from src.statewide import Parameters


def _finite(value: float, lower: float=0., upper: float=float('inf')) -> float:
    if isinstance(value,bool) or not isinstance(value,Real) or not np.isfinite(value) or not lower<=value<=upper:
        raise ValueError('Invalid finite numeric input')
    return float(value)


def beta_mean(rng: np.random.Generator, mean: float, concentration: float, n: int) -> np.ndarray:
    """Parameterise beta by mean and assumed precision; never scale then clip."""
    m=_finite(mean,0,1);k=_finite(concentration)
    if k<=0 or type(n) is not int or n<1:raise ValueError('Positive precision and size required')
    if m in (0,1):return np.full(n,m)
    return rng.beta(m*k,(1-m)*k,n)


def sample_v7(p: Parameters|None=None,spec: PathwaySpec|None=None,n: int=20000,
              seed: int=20261028,effect_mode: str='attenuated') -> tuple[dict,dict]:
    """Preserve reference v6 draws; repair non-reference beta mean changes.

    No data are fitted. Beta concentration20 and all transported clinical-effect
    assumptions are researcher priors. A zero mean is a degenerate distribution.
    """
    p=p or Parameters();s=spec or PathwaySpec()
    x,e=sample_v6(p,s,n,seed,effect_mode);rng=np.random.default_rng(seed+71000)
    if p.reliability!=.95:x['reliability']=beta_mean(rng,p.reliability,20,n)
    if p.marginal_fraction!=.5:x['marginal_fraction']=beta_mean(rng,p.marginal_fraction,4,n)
    if s.hospital_marginal_fraction!=.5:e['hospital_fraction']=beta_mean(rng,s.hospital_marginal_fraction,4,n)
    if s.phone_delay_share!=.05:e['delay_share']=beta_mean(rng,s.phone_delay_share,20,n)
    return x,e


def required_health_gain(incremental_cost: float, value_per_health_year: float) -> float:
    """Threshold only; money per specified health metric is a scenario, not policy."""
    c=_finite(incremental_cost,-float('inf'));v=_finite(value_per_health_year)
    if v<=0:raise ValueError('Positive value per health-year required')
    return max(0.,c/v)


def discounted_health_years(survival,utilities,rate: float, start_year: int=1) -> float:
    """Explicit survival-weighted QALYs; utility may be below zero, not above one."""
    s=np.asarray(survival,dtype=float);u=np.asarray(utilities,dtype=float)
    r=_finite(rate)
    if s.ndim!=1 or s.shape!=u.shape or not len(s) or not np.isfinite(s).all() or not np.isfinite(u).all():
        raise ValueError('Matched finite annual sequences required')
    if np.any((s<0)|(s>1)) or np.any(u>1) or type(start_year) is not int or start_year<0:
        raise ValueError('Invalid survival, utility or time origin')
    return float(np.sum(s*u/(1+r)**np.arange(start_year,start_year+len(s))))


def dalys(*,yll: float,prevalent_years: float,disability_weight: float) -> float:
    """YLL + YLD. Disability weights are NOT converted to QALY utilities."""
    return _finite(yll)+_finite(prevalent_years)*_finite(disability_weight,0,1)
