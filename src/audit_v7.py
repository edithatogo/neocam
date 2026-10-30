"""Auditable probability and health-metric helpers; no clinical effect is inferred."""

from __future__ import annotations

import math
from numbers import Real

import numpy as np

from src.pathways_v6 import PathwaySpec, sample_v6
from src.statewide import Parameters

# Reference defaults are compared with an explicit relative tolerance: binary
# representation error in an otherwise-reference value must not trigger a
# spurious re-draw of the sampled beta mean.
_REFERENCE_REL_TOL = 1e-9


def _finite(value: float, lower: float = 0.0, upper: float = float("inf")) -> float:
    if isinstance(value, bool) or not isinstance(value, Real) or not np.isfinite(value) or not lower <= value <= upper:
        msg = "Invalid finite numeric input"
        raise ValueError(msg)
    return float(value)


def beta_mean(rng: np.random.Generator, mean: float, concentration: float, n: int) -> np.ndarray:
    """Parameterise beta by mean and assumed precision; never scale then clip.

    Returns:
        The ``n`` sampled values carrying the requested mean and concentration.

    Raises:
        ValueError: If the mean, concentration or draw count is invalid.
    """
    m = _finite(mean, 0, 1)
    k = _finite(concentration)
    if k <= 0 or type(n) is not int or n < 1:
        msg = "Positive precision and size required"
        raise ValueError(msg)
    if m in {0, 1}:
        return np.full(n, m)
    return rng.beta(m * k, (1 - m) * k, n)


def sample_v7(
    p: Parameters | None = None,
    spec: PathwaySpec | None = None,
    n: int = 20000,
    seed: int = 20261028,
    effect_mode: str = "attenuated",
) -> tuple[dict, dict]:
    """Preserve reference v6 draws; repair non-reference beta mean changes.

    No data are fitted. Beta concentration20 and all transported clinical-effect
    assumptions are researcher priors. A zero mean is a degenerate distribution.

    Returns:
        The population and structural-effect draw dictionaries.
    """
    p = p or Parameters()
    s = spec or PathwaySpec()
    reference_p, reference_s = Parameters(), PathwaySpec()
    x, e = sample_v6(p, s, n, seed, effect_mode)
    rng = np.random.default_rng(seed + 71000)
    if not math.isclose(p.reliability, reference_p.reliability, rel_tol=_REFERENCE_REL_TOL):
        x["reliability"] = beta_mean(rng, p.reliability, 20, n)
    if not math.isclose(p.marginal_fraction, reference_p.marginal_fraction, rel_tol=_REFERENCE_REL_TOL):
        x["marginal_fraction"] = beta_mean(rng, p.marginal_fraction, 4, n)
    if not math.isclose(
        s.hospital_marginal_fraction, reference_s.hospital_marginal_fraction, rel_tol=_REFERENCE_REL_TOL
    ):
        e["hospital_fraction"] = beta_mean(rng, s.hospital_marginal_fraction, 4, n)
    if not math.isclose(s.phone_delay_share, reference_s.phone_delay_share, rel_tol=_REFERENCE_REL_TOL):
        e["delay_share"] = beta_mean(rng, s.phone_delay_share, 20, n)
    return x, e


def required_health_gain(incremental_cost: float, value_per_health_year: float) -> float:
    """Threshold only; money per specified health metric is a scenario, not policy.

    Returns:
        The non-negative incremental cost per health year.

    Raises:
        ValueError: If the value per health-year is not positive.
    """
    c = _finite(incremental_cost, -float("inf"))
    v = _finite(value_per_health_year)
    if v <= 0:
        msg = "Positive value per health-year required"
        raise ValueError(msg)
    return max(0.0, c / v)


def discounted_health_years(survival: np.ndarray, utilities: np.ndarray, rate: float, start_year: int = 1) -> float:
    """Explicit survival-weighted QALYs; utility may be below zero, not above one.

    Returns:
        The discounted sum of survival-weighted utilities.

    Raises:
        ValueError: If the sequences are unmatched or the rate or origin is invalid.
    """
    s = np.asarray(survival, dtype=float)
    u = np.asarray(utilities, dtype=float)
    r = _finite(rate)
    if s.ndim != 1 or s.shape != u.shape or not len(s) or not np.isfinite(s).all() or not np.isfinite(u).all():
        msg = "Matched finite annual sequences required"
        raise ValueError(msg)
    if np.any((s < 0) | (s > 1)) or np.any(u > 1) or type(start_year) is not int or start_year < 0:
        msg = "Invalid survival, utility or time origin"
        raise ValueError(msg)
    return float(np.sum(s * u / (1 + r) ** np.arange(start_year, start_year + len(s))))


def dalys(*, yll: float, prevalent_years: float, disability_weight: float) -> float:
    """YLL + YLD. Disability weights are NOT converted to QALY utilities.

    Returns:
        The summed years of life lost and years lived with disability.
    """
    return _finite(yll) + _finite(prevalent_years) * _finite(disability_weight, 0, 1)
