"""Repeated contacts do not multiply infants or clinical outcome opportunities."""

from pathlib import Path
from typing import TYPE_CHECKING, cast

import numpy as np
import pytest

from scripts import analyse_v7
from src import equipment
from src.activity import ActivitySpec
from src.configuration import load_configuration
from src.pathways_v6 import PathwaySpec, compare_v6
from src.statewide import Parameters, _base_arrays, load_sites, select_sites  # pyright: ignore[reportPrivateUsage] -- private kernel helper is the in-repo surface under test

if TYPE_CHECKING:
    from collections.abc import Callable

# Driver/kernel signatures declare bare containers; restate the asserted shapes.
Perspectives = tuple[dict[str, dict[str, np.ndarray]], dict[str, dict[str, np.ndarray]], dict[str, object]]
evaluate_perspectives = cast("Callable[..., Perspectives]", analyse_v7.evaluate_perspectives)
mixed_cash_budget = cast("Callable[..., list[dict[str, float]]]", equipment.mixed_cash_budget)
# Deliberately invalid values must be validated by the model itself.
_activity_spec = cast("Callable[..., ActivitySpec]", ActivitySpec)
_compare_v6 = cast("Callable[..., dict[str, dict[str, np.ndarray]]]", compare_v6)


@pytest.mark.parametrize(("basis", "episodes", "contacts"), [("contacts", 18.75, 37.5), ("episodes", 37.5, 75)])
def test_forecast_exposures(basis: str, episodes: float, contacts: float) -> None:
    e, c = ActivitySpec(basis, 2).exposures(np.array([37.5]))
    assert e[0] == episodes
    assert c[0] == contacts


@pytest.mark.parametrize("ratio", [True, False, 0, 0.9, float("nan"), float("inf"), "2"])
def test_invalid_ratio(ratio: object) -> None:
    with pytest.raises(ValueError, match="Contacts per episode must be finite numeric"):
        # Deliberately invalid ratios must fail closed at runtime.
        _ = _activity_spec("contacts", ratio)


def test_invalid_basis() -> None:
    with pytest.raises(ValueError, match="Activity basis must be contacts or episodes"):
        _ = ActivitySpec("infants", 1)


@pytest.mark.parametrize(
    "forecast", [np.array([True]), np.array([-1]), np.array([np.nan]), np.array([]), np.array([[2]])]
)
def test_invalid_exposure(forecast: np.ndarray) -> None:
    with pytest.raises(ValueError, match="Forecast requires finite nonnegative one-dimensional"):
        _ = ActivitySpec().exposures(forecast)


def test_default_is_reference_equivalent() -> None:
    sites = select_sites(load_sites(), "pilot")
    a = compare_v6(sites)
    b = compare_v6(sites, activity=ActivitySpec("contacts", 1))
    for k in a:
        for name in a[k]:
            np.testing.assert_array_equal(a[k][name], b[k][name])
    assert a["panda"]["contacts"][0] == pytest.approx(37.5)
    assert a["panda"]["episodes"][0] == pytest.approx(37.5)


def test_fixed_episode_clinical_outcomes_unchanged_and_workload_doubled() -> None:
    sites = select_sites(load_sites(), "pilot")
    a = compare_v6(sites)
    b = compare_v6(sites, activity=ActivitySpec("episodes", 2))
    for k in a:
        for field in (
            "eventual_transfers",
            "delayed_rescues",
            "final_local",
            "care_resource_cost",
            "avoided_transfers",
        ):
            np.testing.assert_allclose(a[k][field], b[k][field])
    assert b["panda"]["hub_hours"][0] == 2 * a["panda"]["hub_hours"][0]
    assert b["panda"]["local_workflow_cost"][0] == 2 * a["panda"]["local_workflow_cost"][0]
    assert b["panda"]["contacts"][0] == 75


def test_fixed_contacts_outcomes_halved_not_time() -> None:
    sites = select_sites(load_sites(), "pilot")
    a = compare_v6(sites)
    b = compare_v6(sites, activity=ActivitySpec("contacts", 2))
    for k in a:
        for field in (
            "eventual_transfers",
            "delayed_rescues",
            "final_local",
            "care_resource_cost",
            "avoided_transfers",
        ):
            np.testing.assert_allclose(0.5 * a[k][field], b[k][field])
    assert b["panda"]["hub_hours"][0] == a["panda"]["hub_hours"][0]
    assert b["panda"]["capital_annualised"][0] == a["panda"]["capital_annualised"][0]


def test_contact_effect_does_not_exponentiate_reliability() -> None:
    sites = select_sites(load_sites(), "pilot")
    p = Parameters(reliability=0.5)
    a = compare_v6(sites, p)
    b = compare_v6(sites, p, activity=ActivitySpec("episodes", 3))
    np.testing.assert_allclose(a["panda"]["avoided_transfers"], b["panda"]["avoided_transfers"])


def test_perspective_and_budget_use_activity() -> None:
    p = Parameters()
    s = PathwaySpec()
    sites = select_sites(load_sites(), "pilot")
    x = _base_arrays(p, 1)
    _, ledgers, _ = evaluate_perspectives(sites, p, s, x, {}, activity=ActivitySpec("contacts", 2))
    for ledger in ledgers.values():
        np.testing.assert_allclose(
            ledger["state"] + ledger["commonwealth"] + ledger["patient_family"], ledger["societal_bounded"]
        )
    cfg = load_configuration(Path.cwd())
    first = mixed_cash_budget(sites, "panda", cfg.owned_assets, p, s, activity=ActivitySpec("episodes", 2))
    base = mixed_cash_budget(sites, "panda", cfg.owned_assets, p, s)
    assert first[0]["cash_running"] > base[0]["cash_running"]
    assert first[0]["capital"] == base[0]["capital"]


@pytest.mark.parametrize("bad", [False, {}, [], 0, "contacts"])
def test_falsey_untyped_activity_is_not_silently_defaulted(bad: object) -> None:
    with pytest.raises(TypeError):
        # Deliberately untyped activity must be rejected at runtime.
        _ = _compare_v6(select_sites(load_sites(), "pilot"), activity=bad)


def test_contact_overflow_rejected() -> None:
    with pytest.raises(ValueError, match="Contact exposure overflow"):
        _ = ActivitySpec("episodes", 1e308).exposures(np.array([1e308]))
