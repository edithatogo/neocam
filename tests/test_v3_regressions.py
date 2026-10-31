"""Reproduce model-integrity defects without changing economic assumptions."""

from __future__ import annotations

import csv
import math
from typing import TYPE_CHECKING, TypedDict, cast

import numpy as np
import pytest

from scripts.verify import RELEASE_GATES, release_assurance_complete
from src.statewide import Parameters, Site, annuity, evaluate, load_sites, psa

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

# Deliberately invalid values must be validated by the model itself.
_parameters = cast("Callable[..., object]", Parameters)
_psa_call = cast("Callable[..., object]", psa)


class PriorPsa(TypedDict):
    """Reference-kernel PSA envelope: one draw array per field."""

    draws: dict[str, np.ndarray]


def _prior_psa(raw: object) -> PriorPsa:
    """Narrow the loosely typed reference PSA envelope.

    Returns:
        The envelope typed as the shape these tests assert.
    """
    return cast("PriorPsa", raw)


def write_births(path: Path, rows: list[tuple[str, str, str]]) -> Path:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["facility", "births", "year", "sector"])
        for name, count, year in rows:
            writer.writerow([name, count, year, "public"])
    return path


def test_birth_year_is_preserved(tmp_path: Path) -> None:
    path = write_births(tmp_path / "births.csv", [("Atherton", "157", "2023")])
    assert load_sites(path)[0].year == 2023


def test_duplicate_facility_row_rejected(tmp_path: Path) -> None:
    path = write_births(tmp_path / "births.csv", [("Atherton", "157", "2022")] * 2)
    with pytest.raises(ValueError, match="duplicate"):
        _ = load_sites(path)


def test_mixed_birth_years_rejected(tmp_path: Path) -> None:
    path = write_births(tmp_path / "births.csv", [("Atherton", "157", "2022"), ("Mareeba", "134", "2023")])
    with pytest.raises(ValueError, match="year"):
        _ = load_sites(path)


def test_blank_facility_rejected(tmp_path: Path) -> None:
    path = write_births(tmp_path / "births.csv", [("", "1", "2022")])
    with pytest.raises(ValueError, match="facility"):
        _ = load_sites(path)


def test_empty_birth_file_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="empty"):
        _ = load_sites(write_births(tmp_path / "births.csv", []))


def test_site_rejects_negative_births() -> None:
    with pytest.raises(ValueError, match="Births must be a non-negative integer"):
        _ = Site("Invalid", -1, 2022, "rural_proxy", "regional")


def test_boolean_not_accepted_as_monetary_input() -> None:
    with pytest.raises(ValueError, match="equipment_cost must be finite numeric, not boolean"):
        _ = Parameters(equipment_cost=True)


def test_capital_flag_must_be_boolean() -> None:
    with pytest.raises(ValueError, match="include_capital must be boolean"):
        # Deliberately invalid flag type must fail closed at runtime.
        _ = _parameters(include_capital="false")


def test_frozen_parameters_do_not_retain_mutable_casemix() -> None:
    shares = [0.35, 0.5, 0.15]
    # The model accepts any finite sequence and freezes its own tuple copy.
    inputs = cast("Parameters", _parameters(case_mix=shares))
    shares[0] = 1
    assert tuple(inputs.case_mix) == (0.35, 0.5, 0.15)


def test_annuity_near_zero_discount_is_stable() -> None:
    assert math.isclose(annuity(10000, 5, 1e-18), 2000, rel_tol=1e-12)


def test_evaluate_near_zero_discount_is_finite() -> None:
    site = Site("Test", 100, 2022, "rural_proxy", "regional", pilot=True)
    answer = evaluate([site], Parameters(discount=1e-18))
    assert math.isfinite(cast("float", answer["programme_cost"]))


def test_psa_uses_supplied_attenuated_effect() -> None:
    site = Site("Test", 100, 2022, "rural_proxy", "regional", pilot=True)
    a = _prior_psa(psa([site], 1000, 7, Parameters(), "attenuated"))
    b = _prior_psa(psa([site], 1000, 7, Parameters(odds_ratio=1), "attenuated"))
    assert not np.array_equal(a["draws"]["effect_or"], b["draws"]["effect_or"])
    assert np.allclose(b["draws"]["effect_or"] / a["draws"]["effect_or"], 1 / math.sqrt(0.48))


def test_psa_iterations_must_be_integer() -> None:
    with pytest.raises(ValueError, match="integer"):
        # Deliberately non-integer iterations must fail closed at runtime.
        _ = _psa_call([], n=2.5)


def test_conflicting_duplicate_release_receipts_rejected() -> None:
    gates = [{"gate": name, "status": "passed"} for name in RELEASE_GATES]
    gates.insert(0, {"gate": "pytest", "status": "failed"})
    assert not release_assurance_complete(gates, "release")


def test_extra_failed_gate_cannot_be_ignored_for_release() -> None:
    gates = [{"gate": name, "status": "passed"} for name in RELEASE_GATES]
    gates.append({"gate": "gitleaks", "status": "failed"})
    assert not release_assurance_complete(gates, "release")
