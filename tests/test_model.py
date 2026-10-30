import math
from typing import TYPE_CHECKING, TypedDict, cast

import pytest

from src.panda_model import ModelInputs, annual_programme_cost, deterministic_scenario, odds_to_probability, run_psa

if TYPE_CHECKING:
    from collections.abc import Callable


class PsaResult(TypedDict):
    """PSA envelope returned by the published reference sampler."""

    summary: dict[str, float]
    histogram: list[object]


# src declares a bare object-valued dict; restate the asserted shape.
_psa = cast("Callable[..., PsaResult]", run_psa)


def test_odds_ratio_transformation() -> None:
    p = odds_to_probability(0.65, 0.70)
    assert 0 < p < 0.65
    assert math.isclose(p, 0.5652173913, rel_tol=1e-8)


def test_annual_programme_cost_uses_three_sites_and_per_site_volume() -> None:
    x = ModelInputs()
    result = annual_programme_cost(x)
    assert result["consultations"] == pytest.approx(37.5)
    assert math.isclose(result["annualised_equipment"], 6000.0)
    assert result["total_economic"] > result["cash_continuation"]


def test_deterministic_scenario_zero_effect_is_cost_increasing() -> None:
    x = ModelInputs()
    result = deterministic_scenario(x, transfer_reduction_abs=0.0)
    assert result["avoided_transfers"] == 0
    assert result["net_saving_health_system"] < 0


def test_transport_mix_sums_to_one() -> None:
    x = ModelInputs()
    assert math.isclose(x.road_share + x.rotary_share + x.fixed_share, 1.0)


def test_psa_is_reproducible_and_allows_harm() -> None:
    a = _psa(5000, seed=20261027)
    b = _psa(5000, seed=20261027)
    assert a["summary"] == b["summary"]
    assert a["summary"]["probability_cost_saving"] > 0
    assert a["summary"]["probability_cost_saving"] < 1
    assert a["summary"]["transfer_effect_p025"] < 0
    assert len(a["histogram"]) == 20
