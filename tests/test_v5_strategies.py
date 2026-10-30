"""Behavioural contracts for distinct five-option investment decisions."""

from dataclasses import replace
from typing import TYPE_CHECKING, TypedDict, cast

import numpy as np
import pytest

from src import statewide, strategies
from src.statewide import Parameters, load_sites, select_sites

if TYPE_CHECKING:
    from collections.abc import Callable


class PriorPsa(TypedDict):
    """Reference-kernel PSA envelope: one draw array per field."""

    draws: dict[str, np.ndarray]


class ComparePsa(TypedDict):
    """Joint strategy PSA envelope: draws nested by strategy."""

    draws: dict[str, dict[str, np.ndarray]]
    summary: dict[str, dict[str, float]]
    cost_only_evpi: float


def _prior_psa(raw: object) -> PriorPsa:
    """Narrow the loosely typed reference PSA envelope.

    Returns:
        The envelope typed as the shape these tests assert.
    """
    return cast("PriorPsa", raw)


# src declares bare Any/dict containers; restate the asserted shapes.
evaluate = cast("Callable[..., dict[str, float]]", statewide.evaluate)
psa = cast("Callable[..., object]", statewide.psa)
compare_psa = cast("Callable[..., ComparePsa]", strategies.compare_psa)


def test_five_distinct_complete_configurations() -> None:
    m = strategies
    assert [a.key for a in m.STRATEGIES] == ["telephone", "mobile", "panda", "fixed", "obsbot"]
    assert [a.installed_cost for a in m.STRATEGIES] == [0, 45000, 10000, 47000, 4500]
    assert not m.STRATEGIES[-1].documented_local_service


def test_telephone_is_incremental_zero_not_no_consultation() -> None:
    m = strategies
    s = select_sites(load_sites(), "pilot")
    r = m.compare(s)
    for field in ["programme_cost", "net_saving", "avoided_transfers", "societal_net_saving"]:
        assert r["telephone"][field] == pytest.approx(0)
    assert r["telephone"]["consultations"] == pytest.approx(37.5)


def test_panda_exactly_reproduces_existing_reference() -> None:
    m = strategies
    s = select_sites(load_sites(), "pilot")
    old = evaluate(s)
    new = m.compare(s)["panda"]
    for k in ["programme_cost", "net_saving", "avoided_transfers", "societal_net_saving", "cash_running_cost"]:
        assert new[k] == pytest.approx(old[k], rel=1e-12)


def test_equal_video_effects_and_cost_order() -> None:
    r = strategies.compare(select_sites(load_sites(), "pilot"))
    assert len({round(r[k]["avoided_transfers"], 12) for k in ("mobile", "panda", "fixed", "obsbot")}) == 1
    assert r["obsbot"]["net_saving"] > r["panda"]["net_saving"] > r["mobile"]["net_saving"] > r["fixed"]["net_saving"]


def test_psa_preserves_previous_panda_draws() -> None:
    s = select_sites(load_sites(), "pilot")
    old = _prior_psa(psa(s, n=256, seed=811))["draws"]
    new = compare_psa(s, n=256, seed=811)["draws"]["panda"]
    for k in ("programme_cost", "net_saving", "avoided_transfers"):
        np.testing.assert_allclose(new[k], old[k], rtol=1e-12)


def test_psa_shared_effects_not_independent_unpaired_draws() -> None:
    r = compare_psa(select_sites(load_sites(), "pilot"), n=256, seed=811)
    np.testing.assert_array_equal(r["draws"]["obsbot"]["avoided_transfers"], r["draws"]["panda"]["avoided_transfers"])
    assert sum(v["p_optimal"] for v in r["summary"].values()) == pytest.approx(1)
    assert r["cost_only_evpi"] >= 0


def test_sunk_panda_capital_does_not_make_new_obsbot_free() -> None:
    m = strategies
    s = select_sites(load_sites(), "pilot")
    green = m.compare(s)
    incumbent = m.compare(s, sunk=("panda",))
    assert incumbent["panda"]["programme_cost"] == pytest.approx(green["panda"]["cash_running_cost"])
    assert incumbent["obsbot"]["programme_cost"] == pytest.approx(green["obsbot"]["programme_cost"])
    assert incumbent["panda"]["net_saving"] > incumbent["obsbot"]["net_saving"]


def test_no_video_benefit_costs_still_positive() -> None:
    r = strategies.compare(select_sites(load_sites(), "pilot"), parameters=replace(Parameters(), odds_ratio=1))
    assert r["telephone"]["net_saving"] == 0
    assert all(r[k]["net_saving"] < 0 for k in ("mobile", "panda", "fixed", "obsbot"))


def test_unusable_video_falls_back_to_phone_not_free_service() -> None:
    m = strategies
    s = select_sites(load_sites(), "pilot")
    r = m.compare(s, overrides={"obsbot": {"reliability": 0}})
    assert r["obsbot"]["avoided_transfers"] == 0
    assert r["obsbot"]["programme_cost"] > 0


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"bogus": 1}, "Invalid strategy override: bogus"),
        ({"reliability": 1.1}, "Override reliability outside allowed range"),
        ({"capital_share": -1}, "Override capital_share outside allowed range"),
        ({"installed_cost": -5}, "Override installed_cost outside allowed range"),
        ({"workflow_per_call": True}, "Invalid strategy override: workflow_per_call"),
    ],
)
def test_invalid_strategy_overrides_rejected(override: dict[str, object], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        _ = strategies.compare(select_sites(load_sites(), "pilot"), overrides={"obsbot": override})


def test_shared_capital_allocation_does_not_reduce_full_purchase_cost() -> None:
    m = strategies
    r = m.compare(select_sites(load_sites(), "pilot"), overrides={"mobile": {"capital_share": 0.1}})
    assert r["mobile"]["full_purchase_capital"] == 135000
    assert r["mobile"]["attributed_capital"] == 13500


def test_unknown_sunk_strategy_rejected() -> None:
    with pytest.raises(ValueError, match="Invalid sunk strategy list"):
        _ = strategies.compare(select_sites(load_sites(), "pilot"), sunk=("unknown",))


def test_empty_sites_rejected() -> None:
    with pytest.raises(ValueError, match="At least one site is required"):
        _ = strategies.compare([])


def test_source_documentation_is_not_clinical_validation() -> None:
    assert strategies.STRATEGIES[2].documented_local_service
    assert not strategies.STRATEGIES[-1].documented_local_service


def test_duplicate_sites_rejected() -> None:
    s = select_sites(load_sites(), "pilot")
    with pytest.raises(ValueError, match="Repeated sites would double count activity"):
        _ = strategies.compare(s + s[:1])


@pytest.mark.parametrize("sunk", [("panda", "panda"), ("telephone",)])
def test_bad_sunk_set_rejected(sunk: tuple[str, ...]) -> None:
    with pytest.raises(ValueError, match="Invalid sunk strategy list"):
        _ = strategies.compare(select_sites(load_sites(), "pilot"), sunk=sunk)


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"reliability": np.array([True])}, "Override draw array has wrong type or shape"),
        ({"reliability": np.array([0.8, 0.9])}, "Override draw array has wrong type or shape"),
        ({"reliability": np.array([[0.8]])}, "Override draw array has wrong type or shape"),
        ({"installed_cost": np.nan}, "Override installed_cost outside allowed range"),
        ({"installed_cost": np.inf}, "Override installed_cost outside allowed range"),
        ({"life_years": 0}, "Override life_years outside allowed range"),
    ],
)
def test_nonfinite_or_wrong_shape_override_rejected(override: dict[str, object], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        _ = strategies.compare(select_sites(load_sites(), "pilot"), overrides={"obsbot": override})


def test_non_numeric_override_type_rejected() -> None:
    with pytest.raises(TypeError):
        _ = strategies.compare(select_sites(load_sites(), "pilot"), overrides={"obsbot": {"reliability": "0.8"}})


@pytest.mark.parametrize("eligible", [(), ("panda", "panda"), ("bogus",)])
def test_invalid_eligibility_rejected(eligible: tuple[str, ...]) -> None:
    with pytest.raises(ValueError, match="Eligible set must contain unique known strategies"):
        _ = strategies.summarise({}, eligible=eligible)


def test_nonfinite_or_empty_summary_rejected() -> None:
    for a in (np.array([]), np.array([np.nan])):
        with pytest.raises(ValueError, match="Finite non-empty draw matrix required"):
            _ = strategies.summarise({"panda": {"net_saving": a}}, eligible=("panda",))


def test_invalid_override_strategy_rejected() -> None:
    for name in ("telephone", "unknown"):
        with pytest.raises(ValueError, match="Overrides require a named video strategy"):
            _ = strategies.compare(select_sites(load_sites(), "pilot"), overrides={name: {"installed_cost": 5}})


def test_disabling_capital_is_not_a_false_free_procurement_claim() -> None:
    s = select_sites(load_sites(), "pilot")
    p = replace(Parameters(), include_capital=False)
    r = strategies.compare(s, parameters=p)
    assert r["mobile"]["programme_cost"] == pytest.approx(r["mobile"]["cash_running_cost"])
    assert r["mobile"]["incremental_purchase_capital"] == 135000
