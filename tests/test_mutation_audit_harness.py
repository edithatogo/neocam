"""Behavioural mutation-kill tests for the audited kernel, configuration and harness.

Each assertion is chosen so a specific operator mutation (comparison, arithmetic,
boolean, boundary, return) in ``src/audit_v7.py``, ``src/perspectives_v7.py``,
``src/configuration.py``, ``src/equipment.py``, ``quality/assurance.py``,
``quality/contracts.py`` or ``src/activity.py`` produces a different observable
result through the public surface. Inputs are deterministic and network-free.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import re
import shutil
import sys
from dataclasses import asdict, replace
from pathlib import Path
from typing import TYPE_CHECKING, cast

import numpy as np
import pytest

from quality import contracts
from quality.assurance import Gate, Receipt, input_fingerprint, receipt_errors, run_gate, validate_receipts
from quality.contracts import forbidden_imports, forbidden_packages, validate_lock
from src import audit_v7
from src.activity import ActivitySpec
from src.audit_v7 import beta_mean, dalys, discounted_health_years, required_health_gain, sample_v7
from src.configuration import ResolvedConfiguration, exact_keys, load_configuration, strict_json
from src.equipment import OwnedAsset, apply_retention, mixed_cash_budget, retained_sites, validate_estate
from src.pathways_v6 import PathwaySpec, sample_v6
from src.perspectives_v7 import optimal_probabilities, perspective_regret, reconcile_ledger
from src.portfolios_v7 import portfolio
from src.statewide import Parameters, Site

if TYPE_CHECKING:
    from collections.abc import Callable

ROOT = Path(__file__).resolve().parents[1]
# Deliberately invalid values are validated by the runtime under test.
_spec = cast("Callable[..., ActivitySpec]", ActivitySpec)
_beta = cast("Callable[..., np.ndarray]", beta_mean)
# The private comparator helpers are the in-repo surface these mutation tests pin.
_as_sequence = contracts._as_sequence  # pyright: ignore[reportPrivateUsage]
_package_hash_errors = contracts._package_hash_errors  # pyright: ignore[reportPrivateUsage]
_register_errors = contracts._register_errors  # pyright: ignore[reportPrivateUsage]
_rows = contracts._rows  # pyright: ignore[reportPrivateUsage]
_same_value = contracts._same_value  # pyright: ignore[reportPrivateUsage]
_valid_artifact_hash = contracts._valid_artifact_hash  # pyright: ignore[reportPrivateUsage]


# --------------------------------------------------------------------------- activity


def test_activity_spec_is_frozen() -> None:
    spec = ActivitySpec()
    with pytest.raises(dataclasses.FrozenInstanceError):
        # The assignment is the assertion that the record is frozen.
        spec.activity_basis = "episodes"  # pyright: ignore[reportAttributeAccessIssue]  # ty: ignore[invalid-assignment]


@pytest.mark.parametrize(("basis", "episodes", "contacts"), [("contacts", 18.75, 37.5), ("episodes", 37.5, 75.0)])
def test_exposures_basis_arithmetic(basis: str, episodes: float, contacts: float) -> None:
    e, c = ActivitySpec(basis, 2.0).exposures(np.array([37.5]))
    assert e[0] == pytest.approx(episodes)
    assert c[0] == pytest.approx(contacts)


def test_exposures_does_not_alias_the_forecast() -> None:
    forecast = np.array([3.0, 4.0])
    episodes, contacts = ActivitySpec("contacts", 2.0).exposures(forecast)
    forecast[0] = 99.0
    assert contacts[0] == pytest.approx(3.0)
    assert episodes[0] == pytest.approx(1.5)


@pytest.mark.parametrize("ratio", [True, False, 0, 0.9, float("nan"), float("inf"), "2"])
def test_invalid_contact_ratio(ratio: object) -> None:
    with pytest.raises(ValueError, match="Contacts per episode must be finite numeric"):
        _ = _spec("contacts", ratio)


@pytest.mark.parametrize("forecast", [np.array([True]), np.array([-1]), np.array([np.nan]), np.array([])])
def test_invalid_forecast_rejected(forecast: np.ndarray) -> None:
    with pytest.raises(ValueError, match="Forecast requires finite nonnegative one-dimensional"):
        _ = ActivitySpec().exposures(forecast)


def test_valid_ratio_and_forecast_boundary() -> None:
    e, _ = ActivitySpec("contacts", 1).exposures(np.array([0.0, 0.5]))
    assert list(e) == [0.0, 0.5]


def test_contact_overflow_rejected() -> None:
    with pytest.raises(ValueError, match="Contact exposure overflow"):
        _ = ActivitySpec("episodes", 1e308).exposures(np.array([1e308]))


# --------------------------------------------------------------------------- audit_v7


def test_beta_mean_accepts_boundary_means() -> None:
    assert np.array_equal(beta_mean(np.random.default_rng(1), 0.0, 20, 4), np.zeros(4))
    assert np.array_equal(beta_mean(np.random.default_rng(1), 1.0, 20, 4), np.ones(4))


@pytest.mark.parametrize("mean", [True, "x", np.nan, 2.0, -0.1, 1.1])
def test_beta_mean_rejects_nonfinite_or_out_of_range_mean(mean: object) -> None:
    with pytest.raises(ValueError, match="Invalid finite numeric input"):
        _ = _beta(np.random.default_rng(1), mean, 20, 4)


@pytest.mark.parametrize("size", [0, -1])
def test_beta_mean_rejects_empty_size(size: int) -> None:
    with pytest.raises(ValueError, match="Positive precision and size required"):
        _ = beta_mean(np.random.default_rng(1), 0.5, 20, size)


@pytest.mark.parametrize("concentration", [0])
def test_beta_mean_rejects_nonpositive_precision(concentration: float) -> None:
    with pytest.raises(ValueError, match="Positive precision and size required"):
        _ = beta_mean(np.random.default_rng(1), 0.5, concentration, 4)


def test_beta_mean_valid_uses_mean_preserving_parameterisation() -> None:
    draws = beta_mean(np.random.default_rng(3), 0.8, 20, 200000)
    assert draws.shape == (200000,)
    assert draws.mean() == pytest.approx(0.8, abs=0.004)
    assert np.all((draws > 0) & (draws < 1))


def test_beta_mean_boundary_sizes() -> None:
    assert beta_mean(np.random.default_rng(2), 0.5, 20, 1).shape == (1,)
    assert beta_mean(np.random.default_rng(2), 0.5, 1, 4).shape == (4,)


def test_required_health_gain_threshold() -> None:
    assert required_health_gain(10000.0, 50000.0) == pytest.approx(0.2)
    assert required_health_gain(100.0, 1.0) == pytest.approx(100.0)
    assert required_health_gain(-10000.0, 50000.0) == pytest.approx(0.0)


@pytest.mark.parametrize("value", [0.0])
def test_required_health_gain_rejects_nonpositive_value(value: float) -> None:
    with pytest.raises(ValueError, match="Positive value per health-year required"):
        _ = required_health_gain(100.0, value)


def test_discounted_health_years_discounts_from_origin() -> None:
    value = discounted_health_years(np.array([1.0, 1.0]), np.array([0.5, 0.5]), 0.05, start_year=1)
    assert value == pytest.approx(0.5 / 1.05 + 0.5 / 1.05**2)
    shifted = discounted_health_years(np.array([1.0, 1.0]), np.array([0.5, 0.5]), 0.05, start_year=2)
    assert shifted == pytest.approx(value / 1.05)


def test_discounted_health_years_zero_rate_and_origin() -> None:
    assert discounted_health_years(np.array([1.0]), np.array([0.25]), 0.0, start_year=0) == pytest.approx(0.25)


def test_discounted_health_years_accepts_open_unit_interval() -> None:
    value = discounted_health_years(np.array([0.0, 0.5]), np.array([1.0, 1.0]), 0.0, start_year=0)
    assert value == pytest.approx(0.5)


@pytest.mark.parametrize(
    ("survival", "utilities", "rate", "start_year", "message"),
    [
        (np.array([[1.0], [1.0]]), np.array([[0.5], [0.5]]), 0.05, 1, "Matched finite annual sequences required"),
        (np.array([1.0, 1.0]), np.array([0.5]), 0.05, 1, "Matched finite annual sequences required"),
        (np.array([]), np.array([]), 0.05, 1, "Matched finite annual sequences required"),
        (np.array([np.inf]), np.array([0.5]), 0.05, 1, "Matched finite annual sequences required"),
        (np.array([1.0]), np.array([np.nan]), 0.05, 1, "Matched finite annual sequences required"),
        (np.array([1.5]), np.array([0.5]), 0.05, 1, "Invalid survival, utility or time origin"),
        (np.array([-0.5]), np.array([0.5]), 0.05, 1, "Invalid survival, utility or time origin"),
        (np.array([1.0]), np.array([1.5]), 0.05, 1, "Invalid survival, utility or time origin"),
        (np.array([1.0]), np.array([0.5]), 0.05, 1.0, "Invalid survival, utility or time origin"),
        (np.array([1.0]), np.array([0.5]), 0.05, -1, "Invalid survival, utility or time origin"),
    ],
)
def test_discounted_health_years_rejects_invalid(
    survival: np.ndarray, utilities: np.ndarray, rate: float, start_year: object, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        _ = discounted_health_years(survival, utilities, rate, start_year=cast("int", start_year))


def test_discounted_health_years_rejects_nonfinite_rate() -> None:
    with pytest.raises(ValueError, match="Invalid finite numeric input"):
        _ = discounted_health_years(np.array([1.0]), np.array([0.5]), float("nan"))


def test_dalys_sums_yll_and_yld() -> None:
    assert dalys(yll=5.0, prevalent_years=10.0, disability_weight=0.2) == pytest.approx(7.0)


@pytest.mark.parametrize(
    ("yll", "weight"),
    [(-1.0, 0.2), (5.0, 1.5)],
)
def test_dalys_rejects_out_of_range_inputs(yll: float, weight: float) -> None:
    with pytest.raises(ValueError, match="Invalid finite numeric input"):
        _ = dalys(yll=yll, prevalent_years=10.0, disability_weight=weight)


def test_sample_v7_preserves_reference_draws() -> None:
    x, e = sample_v7(n=32, seed=11)
    reference_x, reference_e = sample_v6(Parameters(), PathwaySpec(), 32, 11, "attenuated")
    np.testing.assert_array_equal(x["reliability"], reference_x["reliability"])
    np.testing.assert_array_equal(x["marginal_fraction"], reference_x["marginal_fraction"])
    np.testing.assert_array_equal(e["hospital_fraction"], reference_e["hospital_fraction"])
    np.testing.assert_array_equal(e["delay_share"], reference_e["delay_share"])


def test_sample_v7_redraws_non_reference_parameters() -> None:
    default_x, default_e = sample_v7(n=32, seed=11)
    changed_x, _ = sample_v7(p=replace(Parameters(), reliability=0.5), n=32, seed=11)
    assert not np.allclose(changed_x["reliability"], default_x["reliability"])
    _, changed_e = sample_v7(spec=replace(PathwaySpec(), phone_delay_share=0.5), n=32, seed=11)
    assert not np.allclose(changed_e["delay_share"], default_e["delay_share"])


def test_sample_v7_uses_the_declared_stream_offset() -> None:
    x, _ = sample_v7(p=Parameters(reliability=0.5), n=64, seed=7)
    expected = audit_v7.beta_mean(np.random.default_rng(7 + 71000), 0.5, 20, 64)
    np.testing.assert_allclose(x["reliability"], expected)


# --------------------------------------------------------------------------- perspectives_v7


def test_optimal_probabilities_single_row_and_ties() -> None:
    assert np.allclose(optimal_probabilities(np.array([[0.0, 1.0]])), [0.0, 1.0])
    assert np.allclose(optimal_probabilities(np.array([[1.0, 1.0], [3.0, 3.0]])), [0.5, 0.5])


def test_optimal_probabilities_non_square_matrix() -> None:
    winners = optimal_probabilities(np.array([[1.0, 5.0, 5.0], [2.0, 2.0, 2.0]]))
    np.testing.assert_allclose(winners, [1 / 6, 5 / 12, 5 / 12])


def test_optimal_probabilities_rejects_bad_shape() -> None:
    with pytest.raises(ValueError, match="Require finite draw by strategy matrix"):
        _ = optimal_probabilities(np.array([1.0, 2.0]))
    with pytest.raises(ValueError, match="Require finite draw by strategy matrix"):
        _ = optimal_probabilities(np.zeros((0, 2)))
    with pytest.raises(ValueError, match="Require finite draw by strategy matrix"):
        _ = optimal_probabilities(np.array([[np.nan, 0.0]]))


def _regret_case(choose: np.ndarray, evaluate: np.ndarray) -> dict[str, object]:
    return perspective_regret(choose, evaluate)


def test_perspective_regret_value_and_bounds() -> None:
    result = _regret_case(np.array([[9.0, 0.0], [1.0, 0.0]]), np.array([[0.0, 10.0], [8.0, 0.0]]))
    assert result["value"] == pytest.approx(1.0)
    assert result["choose_indices"] == [0]
    assert result["target_indices"] == [1]
    assert result["source_tied"] is False
    assert result["target_tied"] is False
    assert result["minimum_tie_regret"] == pytest.approx(1.0)
    assert result["maximum_tie_regret"] == pytest.approx(1.0)


def test_perspective_regret_ties_are_disclosed() -> None:
    tied = _regret_case(np.array([[1.0, 1.0], [1.0, 1.0]]), np.array([[2.0, 2.0], [2.0, 2.0]]))
    assert tied["source_tied"] is True
    assert tied["target_tied"] is True
    assert tied["value"] == pytest.approx(0.0)


def test_perspective_regret_rejects_mismatched_shapes() -> None:
    with pytest.raises(ValueError, match="Paired perspectives must have equal shapes"):
        _ = perspective_regret(np.ones((2, 2)), np.ones((3, 2)))


def test_reconcile_ledger_reconciles_signed_amounts() -> None:
    result = reconcile_ledger(
        health_cost=np.array([100.0]),
        family_gross=np.array([40.0]),
        family_subsidy=np.array([20.0]),
        commonwealth=np.array([30.0]),
        provider_cost=np.array([70.0]),
    )
    assert result["health_system"] == pytest.approx([100.0])
    assert result["societal_bounded"] == pytest.approx([140.0])
    assert result["societal"] == pytest.approx([140.0])
    assert result["patient_family"] == pytest.approx([20.0])
    assert result["commonwealth"] == pytest.approx([30.0])
    assert result["state"] == pytest.approx([90.0])
    assert result["provider_chhhs"] == pytest.approx([70.0])


def test_reconcile_ledger_rejects_unpaired_inputs() -> None:
    with pytest.raises(ValueError, match="Ledger inputs must be paired finite arrays of equal shape"):
        _ = reconcile_ledger(
            health_cost=np.array([1.0, 2.0]),
            family_gross=np.array([1.0, 2.0, 3.0]),
            family_subsidy=np.array([1.0, 2.0]),
            commonwealth=np.array([1.0, 2.0]),
            provider_cost=np.array([1.0, 2.0]),
        )
    with pytest.raises(ValueError, match="Ledger inputs must be paired finite arrays of equal shape"):
        _ = reconcile_ledger(
            health_cost=np.array([np.nan]),
            family_gross=np.array([1.0]),
            family_subsidy=np.array([1.0]),
            commonwealth=np.array([1.0]),
            provider_cost=np.array([1.0]),
        )


# --------------------------------------------------------------------------- equipment


def _site(name: str, births: int = 100) -> Site:
    return Site(name, births, 2022, "rural_proxy", "regional", pilot=True)


def test_owned_asset_is_frozen() -> None:
    asset = OwnedAsset("Atherton", "panda", 2)
    with pytest.raises(dataclasses.FrozenInstanceError):
        # The assignment is the assertion that the record is frozen.
        asset.site = "Mareeba"  # pyright: ignore[reportAttributeAccessIssue]  # ty: ignore[invalid-assignment]


@pytest.mark.parametrize(
    ("site", "strategy", "remaining"),
    [("", "panda", 2), ("   ", "panda", 2), ("Atherton", "telephone", 2), ("Atherton", "unknown", 2)],
)
def test_invalid_asset_identity_rejected(site: str, strategy: str, remaining: int) -> None:
    with pytest.raises(ValueError, match="Invalid asset site or configuration"):
        _ = OwnedAsset(site, strategy, remaining)


@pytest.mark.parametrize("remaining", [-1, 51, True, 1.5])
def test_invalid_remaining_life_rejected(remaining: object) -> None:
    with pytest.raises(ValueError, match="Remaining life must be an integer between zero and fifty years"):
        _ = cast("Callable[..., OwnedAsset]", OwnedAsset)("Atherton", "panda", remaining)


@pytest.mark.parametrize("remaining", [0, 50])
def test_valid_remaining_life_boundaries(remaining: int) -> None:
    assert OwnedAsset("Atherton", "panda", remaining).remaining_life_years == remaining


def test_duplicate_estate_sites_rejected() -> None:
    asset = OwnedAsset("Atherton", "panda", 2)
    with pytest.raises(ValueError, match="Duplicate site in equipment estate"):
        validate_estate((asset, asset))
    validate_estate((asset, OwnedAsset("Mareeba", "panda", 2)))


def test_retained_sites_requires_name_strategy_and_live_life() -> None:
    sites = [_site("Atherton"), _site("Mareeba"), _site("Innisfail")]
    assets = (
        OwnedAsset("Atherton", "panda", 2),
        OwnedAsset("Mareeba", "obsbot", 2),
        OwnedAsset("Innisfail", "panda", 0),
        OwnedAsset("Unknown", "panda", 2),
    )
    assert retained_sites(sites, "panda", assets) == {"Atherton"}


def test_retained_sites_includes_one_year_remaining() -> None:
    sites = [_site("Atherton")]
    assert retained_sites(sites, "panda", (OwnedAsset("Atherton", "panda", 1),)) == {"Atherton"}


def _retention_result() -> dict[str, dict[str, np.ndarray]]:
    return {
        "panda": {
            "capital_annualised": np.array([100.0]),
            "programme_cost": np.array([1000.0]),
            "full_purchase_capital": np.array([400.0]),
            "net_saving": np.array([0.0]),
            "net_with_family_extension": np.array([0.0]),
        }
    }


def test_apply_retention_scales_known_retained_share() -> None:
    sites = [_site("A"), _site("B"), _site("C"), _site("D")]
    assets = (OwnedAsset("A", "panda", 2), OwnedAsset("B", "panda", 2))
    result = _retention_result()
    apply_retention(result, sites, assets, ("panda",))
    item = result["panda"]
    assert item["capital_annualised"][0] == pytest.approx(50.0)
    assert item["programme_cost"][0] == pytest.approx(950.0)
    assert item["incremental_purchase_capital"][0] == pytest.approx(200.0)
    assert item["net_saving"][0] == pytest.approx(50.0)


def test_apply_retention_rejects_invalid_portfolio() -> None:
    with pytest.raises(ValueError, match="Invalid retained portfolio or strategies"):
        apply_retention({}, [], (), ())
    with pytest.raises(ValueError, match="Invalid retained portfolio or strategies"):
        apply_retention({}, [], cast("tuple[OwnedAsset, ...]", ("panda",)), ())
    with pytest.raises(ValueError, match="Invalid retained portfolio or strategies"):
        apply_retention(_retention_result(), [_site("A")], (), ("panda", "panda"))


def test_mixed_cash_budget_retention_default_is_true() -> None:
    estate = load_configuration(ROOT).owned_assets
    sites = portfolio("chhhs")
    default = mixed_cash_budget(sites, "panda", estate, Parameters(), PathwaySpec())
    retained = mixed_cash_budget(sites, "panda", estate, Parameters(), PathwaySpec(), retain=True)
    fresh = mixed_cash_budget(sites, "panda", estate, Parameters(), PathwaySpec(), retain=False)
    assert [r["capital"] for r in default] == [r["capital"] for r in retained]
    assert default[0]["capital"] != fresh[0]["capital"]


def test_mixed_cash_budget_purchase_schedule() -> None:
    estate = load_configuration(ROOT).owned_assets
    rows = mixed_cash_budget(portfolio("chhhs"), "panda", estate, Parameters(), PathwaySpec())
    assert rows[0]["capital"] == pytest.approx(70000.0)
    assert rows[2]["capital"] == pytest.approx(30000.0)
    assert rows[5]["capital"] == pytest.approx(70000.0)
    assert rows[0]["new_installations"] == 7
    assert rows[1]["new_installations"] == 0
    assert [r["year"] for r in rows] == [1, 2, 3, 4, 5, 6, 7]
    assert rows[0]["purchases"] == 7
    for row in rows:
        assert row["cash_expenditure"] == pytest.approx(row["capital"] + row["cash_running"])


def test_mixed_cash_budget_new_installations_use_unowned_sites() -> None:
    estate = load_configuration(ROOT).owned_assets
    rows = mixed_cash_budget(portfolio("pilot"), "obsbot", estate, Parameters(), PathwaySpec())
    assert rows[0]["new_installations"] == 3
    assert rows[1]["new_installations"] == 0
    assert rows[0]["capital"] == pytest.approx(13500.0)


def test_mixed_cash_budget_telephone_has_no_purchases_or_installations() -> None:
    estate = load_configuration(ROOT).owned_assets
    rows = mixed_cash_budget(portfolio("pilot"), "telephone", estate, Parameters(), PathwaySpec())
    for row in rows:
        assert row["purchases"] == 0
        assert row["new_installations"] == 0


def test_mixed_cash_budget_replacement_cycle_and_purchase_counting() -> None:
    sites = [_site("Alpha")]
    assets = (OwnedAsset("Alpha", "panda", 5),)
    rows = mixed_cash_budget(sites, "panda", assets, Parameters(life_years=5.0), PathwaySpec())
    assert rows[0]["capital"] == pytest.approx(0.0)
    assert rows[5]["capital"] == pytest.approx(10000.0)
    assert rows[6]["capital"] == pytest.approx(0.0)
    assert rows[0]["purchases"] == 0


def test_mixed_cash_budget_allows_remaining_equal_to_life() -> None:
    sites = [_site("Alpha")]
    rows = mixed_cash_budget(
        sites, "panda", (OwnedAsset("Alpha", "panda", 5),), Parameters(life_years=5.0), PathwaySpec()
    )
    assert rows[0]["year"] == 1


@pytest.mark.parametrize(
    ("years", "retain", "life", "message"),
    [
        (0, True, 5.0, "Positive integer years and boolean retention required"),
        (True, True, 5.0, "Positive integer years and boolean retention required"),
        (7, "true", 5.0, "Positive integer years and boolean retention required"),
        (7, True, 2.5, "An explicit integer replacement interval is required"),
        (7, True, 1.0, "Remaining life exceeds configured equipment life"),
    ],
)
def test_mixed_cash_budget_contract(years: object, retain: object, life: float, message: str) -> None:
    estate = load_configuration(ROOT).owned_assets
    with pytest.raises(ValueError, match=message):
        _ = mixed_cash_budget(
            portfolio("pilot"),
            "panda",
            estate,
            Parameters(life_years=life),
            PathwaySpec(),
            years=cast("int", years),
            retain=cast("bool", retain),
        )


def test_mixed_cash_budget_single_year_and_unknown_strategy() -> None:
    sites = [_site("Alpha")]
    rows = mixed_cash_budget(sites, "panda", (), Parameters(), PathwaySpec(), years=1)
    assert len(rows) == 1
    with pytest.raises(ValueError, match="Unknown strategy"):
        _ = mixed_cash_budget(sites, "invalid", (), Parameters(), PathwaySpec())


# --------------------------------------------------------------------------- configuration


def _parameters_document() -> dict[str, object]:
    return cast("dict[str, object]", asdict(Parameters()))


def _pathways_document() -> dict[str, object]:
    return cast("dict[str, object]", asdict(PathwaySpec()))


def _recipe(draws: int = 2, seed: int = 0, portfolios: list[str] | None = None) -> dict[str, object]:
    return {
        "schema_version": 1,
        "parameters": "data/parameters.json",
        "pathways": "config/pathways.json",
        "equipment_estate": "config/equipment_estate.json",
        "run": {"draws": draws, "seed": seed, "portfolios": portfolios or ["pilot"]},
    }


def _write_root(root: Path) -> Path:
    (root / "config").mkdir(parents=True)
    (root / "data").mkdir(parents=True)
    _ = (root / "config/reference.json").write_text(json.dumps(_recipe()), encoding="utf-8")
    _ = (root / "data/parameters.json").write_text(json.dumps(_parameters_document()), encoding="utf-8")
    _ = (root / "config/pathways.json").write_text(json.dumps(_pathways_document()), encoding="utf-8")
    _ = (root / "config/equipment_estate.json").write_text(
        json.dumps({
            "owned_assets": [{"site": "Atherton", "strategy": "panda", "remaining_life_years": 2}],
            "remaining_life_basis": "x",
        }),
        encoding="utf-8",
    )
    _ = (root / "data/births_queensland_2022.csv").write_text(
        "facility,births,year\nAtherton,157,2022\nInnisfail,195,2022\nMareeba,134,2022\n", encoding="utf-8"
    )
    return root


def _root(tmp_path: Path) -> Path:
    return _write_root(tmp_path)


def test_strict_json_returns_object_and_rejects_arrays(tmp_path: Path) -> None:
    good = tmp_path / "good.json"
    _ = good.write_text('{"a": 1, "b": [2]}', encoding="utf-8")
    assert strict_json(good) == {"a": 1, "b": [2]}
    bad = tmp_path / "bad.json"
    _ = bad.write_text("[1, 2]", encoding="utf-8")
    with pytest.raises(TypeError, match="Configuration document must be an object"):
        _ = strict_json(bad)


def test_strict_json_rejects_duplicate_and_nonfinite(tmp_path: Path) -> None:
    duplicate = tmp_path / "dup.json"
    _ = duplicate.write_text('{"a": 1, "a": 2}', encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate configuration key: a"):
        _ = strict_json(duplicate)
    nonfinite = tmp_path / "nf.json"
    _ = nonfinite.write_text('{"a": NaN}', encoding="utf-8")
    with pytest.raises(ValueError, match="Nonfinite JSON value"):
        _ = strict_json(nonfinite)


def test_exact_keys_contract() -> None:
    exact_keys({"a": 1}, {"a"}, "Doc")
    with pytest.raises(ValueError, match="Doc requires exactly"):
        exact_keys({"a": 1, "b": 2}, {"a"}, "Doc")
    with pytest.raises(ValueError, match="Doc requires exactly"):
        exact_keys(["a"], {"a"}, "Doc")
    with pytest.raises(ValueError, match="Doc requires exactly"):
        exact_keys(5, {"a"}, "Doc")


def test_resolved_configuration_is_frozen_and_snapshots() -> None:
    configuration_value = ResolvedConfiguration(Parameters(), PathwaySpec(), (), 2, 0, ("pilot",), {}, "digest")
    with pytest.raises(dataclasses.FrozenInstanceError):
        # The assignment is the assertion that the record is frozen.
        configuration_value.draws = 5  # pyright: ignore[reportAttributeAccessIssue]  # ty: ignore[invalid-assignment]
    snapshot = configuration_value.snapshot()
    assert snapshot["run"] == {"draws": 2, "seed": 0, "portfolios": ("pilot",)}
    assert snapshot["configuration_sha256"] == "digest"


def test_load_configuration_resolves_declared_inputs(tmp_path: Path) -> None:
    root = _root(tmp_path)
    resolved = load_configuration(root)
    assert resolved.draws == 2
    assert resolved.seed == 0
    assert resolved.portfolios == ("pilot",)
    assert asdict(resolved.parameters) == asdict(Parameters())
    assert resolved.owned_assets[0].site == "Atherton"
    hashes = {
        rel: hashlib.sha256((root / rel).read_bytes()).hexdigest()
        for rel in (
            "config/equipment_estate.json",
            "config/pathways.json",
            "config/reference.json",
            "data/parameters.json",
        )
    }
    assert resolved.source_hashes == hashes
    assert resolved.digest == hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()


def test_load_configuration_uses_the_explicit_path(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _ = (root / "config/alternate.json").write_text(json.dumps(_recipe(draws=3)), encoding="utf-8")
    resolved = load_configuration(root, root / "config/alternate.json")
    assert resolved.draws == 3


def test_load_configuration_rejects_escape_and_outside_path(tmp_path: Path) -> None:
    root = _root(tmp_path)
    with pytest.raises(ValueError, match="Run configuration must remain inside the repository"):
        _ = load_configuration(root, tmp_path.parent / "elsewhere.json")
    recipe = _recipe()
    recipe["parameters"] = "../escape.json"
    _ = (root / "config/reference.json").write_text(json.dumps(recipe), encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid configuration source"):
        _ = load_configuration(root)


def test_load_configuration_rejects_non_string_and_directory_sources(tmp_path: Path) -> None:
    root = _root(tmp_path)
    recipe = _recipe()
    recipe["parameters"] = 123
    _ = (root / "config/reference.json").write_text(json.dumps(recipe), encoding="utf-8")
    with pytest.raises(ValueError, match="Source paths must be repository-relative strings"):
        _ = load_configuration(root)
    recipe["parameters"] = "config"
    _ = (root / "config/reference.json").write_text(json.dumps(recipe), encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid configuration source"):
        _ = load_configuration(root)


@pytest.mark.parametrize("schema", [0, 2, True, "1"])
def test_load_configuration_rejects_bad_schema(tmp_path: Path, schema: object) -> None:
    root = _root(tmp_path)
    recipe = _recipe()
    recipe["schema_version"] = schema
    _ = (root / "config/reference.json").write_text(json.dumps(recipe), encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported run-configuration schema"):
        _ = load_configuration(root)


def test_load_configuration_rejects_non_list_assets(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _ = (root / "config/equipment_estate.json").write_text(
        json.dumps({"owned_assets": 5, "remaining_life_basis": "x"}), encoding="utf-8"
    )
    with pytest.raises(TypeError, match="Owned assets must be a list"):
        _ = load_configuration(root)


@pytest.mark.parametrize("draws", [1, 1000001, 5.0, True])
def test_load_configuration_rejects_bad_draws(tmp_path: Path, draws: object) -> None:
    root = _root(tmp_path)
    _ = (root / "config/reference.json").write_text(json.dumps(_recipe(draws=cast("int", draws))), encoding="utf-8")
    with pytest.raises(ValueError, match=re.escape("Draw count must be an integer in 2..1000000")):
        _ = load_configuration(root)


def test_load_configuration_accepts_draw_bounds(tmp_path: Path) -> None:
    root = _root(tmp_path)
    for draws in (2, 1_000_000):
        _ = (root / "config/reference.json").write_text(json.dumps(_recipe(draws=draws)), encoding="utf-8")
        assert load_configuration(root).draws == draws


@pytest.mark.parametrize("seed", [-1, True, 1.5])
def test_load_configuration_rejects_bad_seed(tmp_path: Path, seed: object) -> None:
    root = _root(tmp_path)
    _ = (root / "config/reference.json").write_text(json.dumps(_recipe(seed=cast("int", seed))), encoding="utf-8")
    with pytest.raises(ValueError, match="Seed must be a nonnegative integer"):
        _ = load_configuration(root)


def test_load_configuration_accepts_zero_seed(tmp_path: Path) -> None:
    root = _root(tmp_path)
    assert load_configuration(root).seed == 0


@pytest.mark.parametrize("portfolios", [[], ["bad"], ["pilot", "pilot"], ["pilot", "bad"], [1]])
def test_load_configuration_rejects_bad_portfolios(tmp_path: Path, portfolios: list[object]) -> None:
    root = _root(tmp_path)
    recipe = _recipe()
    recipe["run"] = {"draws": 2, "seed": 0, "portfolios": portfolios}
    _ = (root / "config/reference.json").write_text(json.dumps(recipe), encoding="utf-8")
    with pytest.raises(ValueError, match="Unknown, empty or repeated portfolio"):
        _ = load_configuration(root)


def test_load_configuration_rejects_unknown_site(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _ = (root / "config/equipment_estate.json").write_text(
        json.dumps({
            "owned_assets": [{"site": "Nowhere", "strategy": "panda", "remaining_life_years": 2}],
            "remaining_life_basis": "x",
        }),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Unknown site in owned equipment estate"):
        _ = load_configuration(root)


def test_load_configuration_rejects_remaining_life_beyond_equipment(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _ = (root / "config/equipment_estate.json").write_text(
        json.dumps({
            "owned_assets": [{"site": "Atherton", "strategy": "panda", "remaining_life_years": 6}],
            "remaining_life_basis": "x",
        }),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Remaining asset life exceeds equipment life"):
        _ = load_configuration(root)


def test_load_configuration_allows_remaining_life_equal_to_equipment(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _ = (root / "config/equipment_estate.json").write_text(
        json.dumps({
            "owned_assets": [{"site": "Atherton", "strategy": "panda", "remaining_life_years": 5}],
            "remaining_life_basis": "x",
        }),
        encoding="utf-8",
    )
    assert load_configuration(root).owned_assets[0].remaining_life_years == 5


def test_default_repository_configuration_loads() -> None:
    resolved = load_configuration(ROOT)
    assert resolved.draws == 20000
    assert len(resolved.owned_assets) == 3


# --------------------------------------------------------------------------- quality.assurance


def _receipt(tmp_path: Path, **fields: object) -> Receipt:
    gate = str(fields.get("gate", "probe"))
    status = str(fields.get("status", "passed"))
    returncode = cast("int | None", fields.get("returncode", 0))
    fingerprint = str(fields.get("fingerprint", "fp"))
    duration = float(cast("float", fields.get("duration", 0.1)))
    log = str(fields.get("log", "log.txt"))
    log_sha256 = cast("str | None", fields.get("log_sha256"))
    path = tmp_path / log
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text("ok\n", encoding="utf-8")
    digest = log_sha256 if log_sha256 is not None else hashlib.sha256(path.read_bytes()).hexdigest()
    return Receipt(gate, status, returncode, fingerprint, ("cmd",), duration, log, digest)


def test_gate_and_receipt_are_frozen(tmp_path: Path) -> None:
    gate = Gate("probe", (sys.executable, "-c", "pass"))
    with pytest.raises(dataclasses.FrozenInstanceError):
        # The assignment is the assertion that the record is frozen.
        gate.name = "other"  # pyright: ignore[reportAttributeAccessIssue]  # ty: ignore[invalid-assignment]
    receipt = _receipt(tmp_path)
    with pytest.raises(dataclasses.FrozenInstanceError):
        # The assignment is the assertion that the record is frozen.
        receipt.status = "failed"  # pyright: ignore[reportAttributeAccessIssue]  # ty: ignore[invalid-assignment]


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"name": "../unsafe", "command": ("x",)}, "Gate name must be a lowercase identifier"),
        ({"name": "ok", "command": ()}, "Command must contain nonempty string arguments"),
        ({"name": "ok", "command": ("",)}, "Command must contain nonempty string arguments"),
        ({"name": "ok", "command": ("x",), "timeout": 0}, "Gate timeout must be positive and finite"),
        ({"name": "ok", "command": ("x",), "timeout": -1}, "Gate timeout must be positive and finite"),
        ({"name": "ok", "command": ("x",), "timeout": float("inf")}, "Gate timeout must be positive and finite"),
    ],
)
def test_invalid_gate_specifications(kwargs: dict[str, object], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        _ = cast("Callable[..., Gate]", Gate)(**kwargs)


def test_real_gate_run_records_reason_and_duration(tmp_path: Path) -> None:
    receipt = run_gate(Gate("probe", (sys.executable, "-c", "print('ran')")), tmp_path, "fp", tmp_path / "logs")
    assert receipt.status == "passed"
    assert receipt.returncode == 0
    assert not receipt.reason
    assert 0 <= receipt.duration_seconds < 5
    assert (tmp_path / receipt.log).read_text(encoding="utf-8") == "ran\n"
    assert validate_receipts([receipt], {"probe"}, "fp", tmp_path) == []


def test_missing_executable_names_the_tool(tmp_path: Path) -> None:
    receipt = run_gate(Gate("probe", ("/certainly-not-installed/panda-tool",)), tmp_path, "fp", tmp_path / "logs")
    assert receipt.status == "blocked"
    assert "/certainly-not-installed/panda-tool" in receipt.reason


def test_missing_python_tool_reports_module(tmp_path: Path) -> None:
    receipt = run_gate(
        Gate("probe", (sys.executable, "-c", "print('ran')"), module="nonexistent_pkg.sub"),
        tmp_path,
        "fp",
        tmp_path / "logs",
    )
    assert receipt.status == "blocked"
    assert receipt.reason == "Required Python tool is unavailable: nonexistent_pkg.sub"


def test_timeout_retains_partial_output(tmp_path: Path) -> None:
    script = "import sys,time;print('OUTPART',flush=True);print('ERRPART',file=sys.stderr,flush=True);time.sleep(5)"
    receipt = run_gate(Gate("probe", (sys.executable, "-c", script), timeout=1.0), tmp_path, "fp", tmp_path / "logs")
    assert receipt.status == "failed"
    assert "timeout" in receipt.reason.lower()
    log = (tmp_path / receipt.log).read_text(encoding="utf-8")
    assert "OUTPART" in log
    assert "ERRPART" in log


def test_exit_69_allow_unavailable_blocks_but_default_fails(tmp_path: Path) -> None:
    allowed = run_gate(
        Gate("probe", (sys.executable, "-c", "raise SystemExit(69)"), allow_unavailable=True),
        tmp_path,
        "fp",
        tmp_path / "logs",
    )
    assert allowed.status == "blocked"
    blocked = run_gate(Gate("probe", (sys.executable, "-c", "raise SystemExit(69)")), tmp_path, "fp", tmp_path / "logs")
    assert blocked.status == "failed"


def test_gate_runs_without_shell_interpolation(tmp_path: Path) -> None:
    receipt = run_gate(
        Gate("probe", (sys.executable, "-c", "print('safe')", "$(touch compromised)")),
        tmp_path,
        "fp",
        tmp_path / "logs",
    )
    assert receipt.status == "passed"
    assert (tmp_path / receipt.log).read_text(encoding="utf-8") == "safe\n"
    assert not (tmp_path / "compromised").exists()


def test_nested_log_directory_and_reuse(tmp_path: Path) -> None:
    log_dir = tmp_path / "deep/nested/logs"
    first = run_gate(Gate("probe", (sys.executable, "-c", "pass")), tmp_path, "fp", log_dir)
    second = run_gate(Gate("probe", (sys.executable, "-c", "pass")), tmp_path, "fp", log_dir)
    assert first.status == "passed"
    assert second.status == "passed"


def test_permission_denied_is_failed_receipt(tmp_path: Path) -> None:
    executable = tmp_path / "not-executable"
    _ = executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o600)
    receipt = run_gate(Gate("probe", (str(executable),)), tmp_path, "fp", tmp_path / "logs")
    assert receipt.status == "failed"
    assert "permission" in receipt.reason.lower()


def test_external_log_directory_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Log directory must be inside the project"):
        _ = run_gate(Gate("probe", (sys.executable, "-c", "pass")), tmp_path, "fp", tmp_path.parent / "outside")


def test_receipt_errors_accepts_intact_receipt(tmp_path: Path) -> None:
    receipt = _receipt(tmp_path, duration=0.0)
    assert receipt_errors(receipt, tmp_path, "fp") == []


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"status": "failed"}, "Gate not passed: probe"),
        ({"returncode": 1}, "Gate not passed: probe"),
        ({"fingerprint": "stale"}, "Stale inputs: probe"),
        ({"duration": float("inf")}, "Invalid duration: probe"),
        ({"duration": -1.0}, "Invalid duration: probe"),
        ({"log_sha256": "0" * 64}, "Altered log: probe"),
        ({"log": "../outside.txt"}, "Unsafe log path: probe"),
    ],
)
def test_receipt_errors_detects_inconsistency(tmp_path: Path, overrides: dict[str, object], message: str) -> None:
    receipt = _receipt(tmp_path, **overrides)
    errors = receipt_errors(receipt, tmp_path, "fp")
    assert message in errors


def test_receipt_errors_flags_missing_log(tmp_path: Path) -> None:
    receipt = _receipt(tmp_path)
    (tmp_path / receipt.log).unlink()
    assert "Missing log: probe" in receipt_errors(receipt, tmp_path, "fp")


def test_validate_receipts_full_contract(tmp_path: Path) -> None:
    assert validate_receipts([], set(), "fp", tmp_path)
    receipt = _receipt(tmp_path)
    assert validate_receipts([receipt], {"probe"}, "fp", tmp_path) == []
    assert validate_receipts([receipt, receipt], {"probe"}, "fp", tmp_path)
    assert validate_receipts([receipt], {"probe", "other"}, "fp", tmp_path)
    assert validate_receipts([_receipt(tmp_path, gate="unexpected")], {"probe"}, "fp", tmp_path)
    failed_with_zero_code = _receipt(tmp_path, status="failed", returncode=0)
    assert validate_receipts([failed_with_zero_code], {"probe"}, "fp", tmp_path) == ["Gate not passed: probe"]


def test_input_fingerprint_excludes_pyc_and_pycache(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    _ = (tmp_path / "src/a.py").write_text("A = 1\n", encoding="utf-8")
    baseline = input_fingerprint(tmp_path)
    _ = (tmp_path / "src/junk.pyc").write_bytes(b"junk")
    (tmp_path / "src/__pycache__").mkdir()
    _ = (tmp_path / "src/__pycache__/gen.py").write_text("G = 1\n", encoding="utf-8")
    assert input_fingerprint(tmp_path) == baseline


def test_input_fingerprint_changes_with_source(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    source = tmp_path / "src/a.py"
    _ = source.write_text("A = 1\n", encoding="utf-8")
    before = input_fingerprint(tmp_path)
    _ = source.write_text("A = 2\n", encoding="utf-8")
    assert input_fingerprint(tmp_path) != before


def test_input_fingerprint_hashes_declared_input_files(tmp_path: Path) -> None:
    declared = tmp_path / "pyproject.toml"
    _ = declared.write_text("value = 1\n", encoding="utf-8")
    digest = input_fingerprint(tmp_path)
    assert len(digest) == 64
    _ = declared.write_text("value = 2\n", encoding="utf-8")
    assert input_fingerprint(tmp_path) != digest


# --------------------------------------------------------------------------- quality.contracts


@pytest.mark.parametrize(
    "source",
    [
        "import pandas as pd",
        "from xarray import Dataset",
        'importlib.import_module("pandas")',
        '__import__("xarray")',
    ],
)
def test_forbidden_imports_detected(source: str) -> None:
    assert forbidden_imports(source)


@pytest.mark.parametrize(
    "source",
    [
        "import polars as pl",
        "import numpy as np",
        'foo("pandas")',
        'obj.attr("pandas")',
        "__import__(42)",
        "text = 'import pandas'",
    ],
)
def test_non_dynamic_imports_are_not_flagged(source: str) -> None:
    assert forbidden_imports(source) == []


@pytest.mark.parametrize("names", [["Pandas"], ["XARRAY"], ["numpy", "pandas"], ["pandas_stubs"]])
def test_forbidden_packages_detected(names: list[str]) -> None:
    assert forbidden_packages(names)


def test_forbidden_packages_allows_numerics() -> None:
    assert forbidden_packages(["polars", "numpy"]) == []


def test_rows_reads_csv(tmp_path: Path) -> None:
    path = tmp_path / "rows.csv"
    _ = path.write_text("a,b\n1,2\n3,4\n", encoding="utf-8")
    assert _rows(path) == [{"a": "1", "b": "2"}, {"a": "3", "b": "4"}]


def test_as_sequence_distinguishes_sequences() -> None:
    assert _as_sequence([1, 2]) == [1, 2]
    assert _as_sequence((1, 2)) == (1, 2)
    assert _as_sequence(5) is None


def test_same_value_reconciles_nested_and_scalar() -> None:
    assert _same_value([1.0, 2.0], (1.0, 2.0)) is True
    assert _same_value([1.0], [1.0, 2.0]) is False
    assert _same_value([1.0], None) is False
    assert _same_value(first=True, second=1) is False
    assert _same_value(first=True, second=False) is False
    assert _same_value(1, "1") is False
    assert _same_value(1.0, 1.0) is True
    assert _same_value("a", "b") is False
    assert _same_value("a", "a") is True


def test_valid_artifact_hash_contract() -> None:
    assert _valid_artifact_hash({"hash": "sha256:" + "a" * 64}) is True
    assert _valid_artifact_hash({"hash": "bad"}) is False
    assert _valid_artifact_hash(42) is False


def test_package_hash_errors_contract() -> None:
    assert _package_hash_errors({"name": "p", "source": 5}) == ["Invalid source: p"]
    assert _package_hash_errors({"name": "p", "source": {"index": "x"}}) == []
    assert _package_hash_errors({"name": "p", "source": {"registry": "https://x"}, "wheels": []}) == [
        "No registry artifact hashes: p"
    ]
    valid = "sha256:" + "b" * 64
    assert _package_hash_errors({"name": "p", "source": {"registry": "x"}, "wheels": [{"hash": valid}]}) == []
    assert _package_hash_errors({
        "name": "p",
        "source": {"registry": "x"},
        "wheels": [{"hash": "bad"}, 42],
    }) == ["Invalid artifact hash: p", "Invalid artifact hash: p"]


def test_register_errors_reconciles_rows() -> None:
    params: dict[str, object] = {"a": 1, "b": [1, 2]}
    known = {"S1"}
    matching = [
        {"parameter": "a", "base_value": "1", "uncertainty": "u", "interpretation": "i", "source_ids": "S1"},
        {"parameter": "b", "base_value": "[1, 2]", "uncertainty": "u", "interpretation": "i", "source_ids": "S1"},
    ]
    assert _register_errors(matching, params, known) == []
    incomplete = [{"parameter": "a", "base_value": "1", "uncertainty": "", "interpretation": "i", "source_ids": "S1"}]
    assert _register_errors(incomplete, params, known) == ["Incomplete assumption disclosure: a"]
    unresolved = [{"parameter": "a", "base_value": "1", "uncertainty": "u", "interpretation": "i", "source_ids": "S9"}]
    assert _register_errors(unresolved, params, known) == ["Unresolved evidence: a: S9"]
    unknown_name = [
        {"parameter": "z", "base_value": "9", "uncertainty": "u", "interpretation": "i", "source_ids": "S1"}
    ]
    assert _register_errors(unknown_name, params, known) == []


def test_validate_lock_accepts_complete_hashed_graph(tmp_path: Path) -> None:
    path = tmp_path / "uv.lock"
    valid = "sha256:" + "c" * 64
    header = 'version=1\n[[package]]\nname="numpy"\nversion="2.5.4"\nsource={registry="https://pypi.org/simple"}\n'
    wheels = f'wheels=[{{url="https://files.pythonhosted.org/n.whl",hash="{valid}"}}]\n'
    _ = path.write_text(header + wheels, encoding="utf-8")
    assert validate_lock(path) == []


def test_validate_lock_accepts_packages_without_registry(tmp_path: Path) -> None:
    path = tmp_path / "uv.lock"
    _ = path.write_text('version=1\n[[package]]\nname="numpy"\nversion="2.5.4"\n', encoding="utf-8")
    assert validate_lock(path) == []


def test_validate_lock_reports_missing_invalid_and_empty(tmp_path: Path) -> None:
    assert validate_lock(tmp_path / "missing.lock")
    invalid = tmp_path / "bad.lock"
    _ = invalid.write_text("not toml = =", encoding="utf-8")
    assert validate_lock(invalid)
    empty = tmp_path / "empty.lock"
    _ = empty.write_text("version=1\n", encoding="utf-8")
    assert validate_lock(empty) == ["Empty package graph"]
    stringy = tmp_path / "str.lock"
    _ = stringy.write_text('version=1\npackage="x"\n', encoding="utf-8")
    assert validate_lock(stringy) == ["Empty package graph"]


def test_validate_lock_flags_unhashed_and_prohibited(tmp_path: Path) -> None:
    unhashed = tmp_path / "unhashed.lock"
    _ = unhashed.write_text(
        'version=1\n[[package]]\nname="numpy"\nversion="2.5.4"\nsource={registry="https://x"}\n', encoding="utf-8"
    )
    assert validate_lock(unhashed) == ["No registry artifact hashes: numpy"]
    malformed_hash = tmp_path / "malformed.lock"
    header = 'version=1\n[[package]]\nname="numpy"\nversion="2.5.4"\nsource={registry="https://x"}\n'
    body = 'wheels=[{url="u",hash="bad"}]\n'
    _ = malformed_hash.write_text(header + body, encoding="utf-8")
    assert validate_lock(malformed_hash) == ["Invalid artifact hash: numpy"]
    banned = tmp_path / "banned.lock"
    _ = banned.write_text('version=1\n[[package]]\nname="pandas"\nversion="1"\n', encoding="utf-8")
    assert validate_lock(banned) == ["Prohibited dependency: pandas"]


def test_validate_lock_flags_malformed_records(tmp_path: Path) -> None:
    non_record = tmp_path / "nonrecord.lock"
    _ = non_record.write_text("version=1\npackage=[1]\n", encoding="utf-8")
    assert validate_lock(non_record) == ["Malformed package record"]
    nameless = tmp_path / "nameless.lock"
    _ = nameless.write_text("version=1\n[[package]]\nname=5\n", encoding="utf-8")
    assert validate_lock(nameless) == ["Malformed package record"]


def _audit_root(tmp_path: Path) -> Path:
    for rel in (
        "data/parameters.json",
        "data/population_totals.json",
        "data/births_queensland_2022.csv",
        "evidence/parameter_register.csv",
        "evidence/sources.csv",
        "evidence/literature_parameter_map.csv",
    ):
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        _ = shutil.copy(ROOT / rel, target)
    return tmp_path


def test_audit_inputs_accepts_current_repository() -> None:
    report = contracts.audit_inputs(ROOT)
    assert report["errors"] == []
    assert report["parameters_checked"] == 27
    assert report["public_births"] == 46711


def test_audit_inputs_detects_parameter_and_register_mismatch(tmp_path: Path) -> None:
    root = _audit_root(tmp_path)
    register = root / "evidence/parameter_register.csv"
    lines = register.read_text(encoding="utf-8").splitlines()
    _ = register.write_text("\n".join([lines[0], lines[1], lines[1], *lines[2:]]) + "\n", encoding="utf-8")
    assert "Parameter register incomplete or duplicated" in cast("list[str]", contracts.audit_inputs(root)["errors"])


def test_audit_inputs_detects_missing_register_parameter(tmp_path: Path) -> None:
    root = _audit_root(tmp_path)
    register = root / "evidence/parameter_register.csv"
    lines = register.read_text(encoding="utf-8").splitlines()
    _ = register.write_text("\n".join([lines[0], *lines[2:]]) + "\n", encoding="utf-8")
    assert "Parameter register incomplete or duplicated" in cast("list[str]", contracts.audit_inputs(root)["errors"])


def test_audit_inputs_detects_value_mismatch_and_missing_disclosure(tmp_path: Path) -> None:
    root = _audit_root(tmp_path)
    register = root / "evidence/parameter_register.csv"
    lines = register.read_text(encoding="utf-8").splitlines()
    lines[1] = lines[1].replace("10000.0", "99999.0")
    _ = register.write_text("\n".join(lines) + "\n", encoding="utf-8")
    errors = cast("list[str]", contracts.audit_inputs(root)["errors"])
    assert any(e.startswith("Parameter register mismatch:") for e in errors)


def test_audit_inputs_detects_unresolved_source(tmp_path: Path) -> None:
    root = _audit_root(tmp_path)
    register = root / "evidence/parameter_register.csv"
    lines = register.read_text(encoding="utf-8").splitlines()
    lines[1] = lines[1].replace("ELC2026;USER2026", "MISSING2026")
    _ = register.write_text("\n".join(lines) + "\n", encoding="utf-8")
    errors = cast("list[str]", contracts.audit_inputs(root)["errors"])
    assert any(e.startswith("Unresolved evidence:") for e in errors)


def test_audit_inputs_detects_duplicate_source_and_missing_evidence(tmp_path: Path) -> None:
    root = _audit_root(tmp_path)
    sources = root / "evidence/sources.csv"
    lines = sources.read_text(encoding="utf-8").splitlines()
    _ = sources.write_text("\n".join([lines[0], lines[1], lines[1], *lines[2:]]) + "\n", encoding="utf-8")
    errors = cast("list[str]", contracts.audit_inputs(root)["errors"])
    assert "Duplicate source/study identifier" in errors
    locator = root / "evidence/literature_parameter_map.csv"
    lit = locator.read_text(encoding="utf-8").splitlines()
    lit[1] = lit[1].replace("https://pubmed.ncbi.nlm.nih.gov/23148301/", "")
    _ = locator.write_text("\n".join(lit) + "\n", encoding="utf-8")
    errors = cast("list[str]", contracts.audit_inputs(root)["errors"])
    assert "Evidence lacks locator or limitation" in errors


def test_audit_inputs_detects_birth_total_and_year_mismatch(tmp_path: Path) -> None:
    root = _audit_root(tmp_path)
    totals_path = root / "data/population_totals.json"
    totals = cast("dict[str, object]", json.loads(totals_path.read_text(encoding="utf-8")))
    totals["public_births"] = 1
    _ = totals_path.write_text(json.dumps(totals), encoding="utf-8")
    errors = cast("list[str]", contracts.audit_inputs(root)["errors"])
    assert "Birth totals or source row counts do not reconcile" in errors
    totals["public_births"] = 46711
    totals["raw_public_rows"] = 1
    _ = totals_path.write_text(json.dumps(totals), encoding="utf-8")
    errors = cast("list[str]", contracts.audit_inputs(root)["errors"])
    assert "Birth totals or source row counts do not reconcile" in errors
    totals["raw_public_rows"] = 72
    totals["total"] = 1
    _ = totals_path.write_text(json.dumps(totals), encoding="utf-8")
    errors = cast("list[str]", contracts.audit_inputs(root)["errors"])
    assert "Whole-population totals do not reconcile" in errors
    totals["total"] = 61404
    totals["year"] = 1999
    _ = totals_path.write_text(json.dumps(totals), encoding="utf-8")
    errors = cast("list[str]", contracts.audit_inputs(root)["errors"])
    assert "Birth year does not reconcile" in errors
