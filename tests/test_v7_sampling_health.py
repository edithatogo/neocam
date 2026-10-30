"""Bounded distributions and non-interchangeable health metrics."""

from dataclasses import replace
from typing import TYPE_CHECKING, cast

import numpy as np
import pytest

from src import audit_v7
from src.audit_v7 import discounted_health_years
from src.statewide import Parameters

if TYPE_CHECKING:
    from collections.abc import Callable

# The audited sampler declares a bare tuple; restate the asserted draw shapes.
Draws = tuple[dict[str, np.ndarray], dict[str, np.ndarray]]
sample_v7 = cast("Callable[..., Draws]", audit_v7.sample_v7)


def test_beta_preserves_mean_without_clipped_boundary_mass() -> None:
    x = audit_v7.beta_mean(np.random.default_rng(1), 0.8, 20, 100000)
    assert x.mean() == pytest.approx(0.8, abs=0.004)
    assert np.all((x > 0) & (x < 1))


def test_beta_degenerate_boundaries() -> None:
    for p in [0.0, 1.0]:
        assert np.all(np.equal(audit_v7.beta_mean(np.random.default_rng(1), p, 20, 5), p))


@pytest.mark.parametrize(
    ("p", "k", "message"),
    [
        (-0.1, 20, "Invalid finite numeric input"),
        (1.1, 20, "Invalid finite numeric input"),
        (0.5, 0, "Positive precision and size required"),
        (0.5, np.nan, "Invalid finite numeric input"),
    ],
)
def test_beta_rejects_invalid(p: float, k: float, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        _ = audit_v7.beta_mean(np.random.default_rng(1), p, k, 3)


def test_reference_draws_are_compared_with_explicit_tolerance() -> None:
    """Representation error near a reference default must not force a re-draw."""
    base, _ = sample_v7(n=256, seed=5)
    nudged, _ = sample_v7(replace(Parameters(), reliability=0.95 + 1e-12), n=256, seed=5)
    np.testing.assert_allclose(nudged["reliability"], base["reliability"], rtol=1e-9, atol=0)


def test_non_reference_reliability_is_still_redrawn() -> None:
    """A genuinely different reliability must still re-draw the beta mean."""
    base, _ = sample_v7(n=256, seed=5)
    changed, _ = sample_v7(replace(Parameters(), reliability=0.5), n=256, seed=5)
    assert not np.allclose(changed["reliability"], base["reliability"])


def test_qaly_threshold_not_effect_estimate() -> None:
    m = audit_v7
    assert m.required_health_gain(10000, 50000) == pytest.approx(0.2)
    assert m.required_health_gain(-10000, 50000) == 0
    assert m.discounted_health_years(np.array([1.0, 1.0]), np.array([0.5, 0.5]), 0) == 1


def test_survival_and_disability_are_separate_inputs() -> None:
    m = audit_v7
    assert m.dalys(yll=5, prevalent_years=10, disability_weight=0.2) == 7
    with pytest.raises(ValueError, match="Invalid finite numeric input"):
        _ = m.dalys(yll=-1, prevalent_years=10, disability_weight=0.2)


def test_age_eleven_bridge_is_discounted_from_birth() -> None:
    early = discounted_health_years(np.array([1.0] * 5), np.array([0.13] * 5), 0.05, start_year=1)
    later = discounted_health_years(np.array([1.0] * 5), np.array([0.13] * 5), 0.05, start_year=11)
    assert later == pytest.approx(early / (1.05**10))
