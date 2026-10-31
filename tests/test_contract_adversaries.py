"""Exercise malformed evidence and boundary cases rather than only happy paths."""

from __future__ import annotations

import csv
import json
import math
import shutil
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, cast

import pytest

from quality.contracts import _same_value, audit_inputs, validate_lock  # pyright: ignore[reportPrivateUsage] -- the private comparator is the in-repo surface under test
from src.panda_model import ModelInputs, clinical_extension, odds_to_probability, weighted_transfer_cost
from src.statewide import Parameters, Site, load_sites, survival_extension

if TYPE_CHECKING:
    from collections.abc import Callable

# Heterogeneous per-case constructors are validated by the model itself.
_parameters = cast("Callable[..., object]", Parameters)
_site = cast("Callable[..., object]", Site)

ROOT = Path(__file__).resolve().parents[1]


def evidence_copy(tmp_path: Path):
    _ = shutil.copytree(ROOT / "data", tmp_path / "data")
    _ = shutil.copytree(ROOT / "evidence", tmp_path / "evidence")
    return tmp_path


def update_csv(path: Path, mutate: Callable[[list[dict[str, str]]], None]) -> None:
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames or []
        rows = list(reader)
    mutate(rows)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


@pytest.mark.parametrize(
    ("field", "value"),
    [("base_value", "999"), ("uncertainty", ""), ("interpretation", ""), ("source_ids", "UNKNOWN_EVIDENCE")],
)
def test_parameter_register_corruption_rejected(tmp_path: Path, field: str, value: str) -> None:
    root = evidence_copy(tmp_path)
    update_csv(root / "evidence/parameter_register.csv", lambda rows: rows[0].update({field: value}))
    assert audit_inputs(root)["errors"]


def test_duplicate_parameter_rejected(tmp_path: Path) -> None:
    root = evidence_copy(tmp_path)
    update_csv(root / "evidence/parameter_register.csv", lambda rows: rows.append(rows[0].copy()))
    assert audit_inputs(root)["errors"]


@pytest.mark.parametrize("field", ["url", "limitations"])
def test_source_disclosure_cannot_be_missing(tmp_path: Path, field: str) -> None:
    root = evidence_copy(tmp_path)
    update_csv(root / "evidence/sources.csv", lambda rows: rows[0].update({field: ""}))
    assert audit_inputs(root)["errors"]


def test_duplicate_source_rejected(tmp_path: Path) -> None:
    root = evidence_copy(tmp_path)
    update_csv(root / "evidence/sources.csv", lambda rows: rows.append(rows[0].copy()))
    assert audit_inputs(root)["errors"]


@pytest.mark.parametrize("field", ["public_births", "raw_public_rows", "total", "year"])
def test_bad_denominator_metadata_rejected(tmp_path: Path, field: str) -> None:
    root = evidence_copy(tmp_path)
    path = root / "data/population_totals.json"
    data = cast("dict[str, int]", json.loads(path.read_text()))
    data[field] += 1
    _ = path.write_text(json.dumps(data))
    assert audit_inputs(root)["errors"]


def test_missing_parameter_not_silently_defaulted_in_audit(tmp_path: Path) -> None:
    root = evidence_copy(tmp_path)
    path = root / "data/parameters.json"
    data = cast("dict[str, object]", json.loads(path.read_text()))
    _ = data.pop("equipment_cost")
    _ = path.write_text(json.dumps(data))
    assert audit_inputs(root)["errors"]


@pytest.mark.parametrize(
    "text",
    [
        "[invalid",
        "package=[1]",
        '[[package]]\nname="a"\nsource="wrong"',
        '[[package]]\nname="a"\nsource={registry="x"}\nsdist={hash="bad"}',
        '[[package]]\nname="a"\nsource={registry="x"}\nwheels=[3]',
    ],
)
def test_malformed_lock_fail_closed(tmp_path: Path, text: str) -> None:
    path = tmp_path / "uv.lock"
    _ = path.write_text(text)
    assert validate_lock(path)


def test_sdist_hash_is_supported(tmp_path: Path) -> None:
    path = tmp_path / "uv.lock"
    _ = path.write_text('[[package]]\nname="a"\nsource={registry="x"}\nsdist={hash="sha256:' + "a" * 64 + '"}')
    assert validate_lock(path) == []


def test_value_comparison_distinguishes_strings_and_booleans() -> None:
    assert _same_value("label", "label")
    assert not _same_value(first=True, second=1)
    assert not _same_value([1], [1, 2])


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"name": ""}, "Site name must be non-empty"),
        ({"births": 1.2}, "Births must be a non-negative integer"),
        ({"year": 1800}, r"Birth year must be an integer in \[1900, 2100\]"),
        ({"group": "unknown"}, "Unknown site group"),
        ({"geography": "unknown"}, "Unknown site geography"),
        ({"pilot": 1}, "Pilot status must be boolean"),
    ],
)
def test_site_boundary_validation(change: dict[str, object], message: str) -> None:
    values = {"name": "Test", "births": 1, "year": 2022, "group": "rural_proxy", "geography": "regional"}
    with pytest.raises(ValueError, match=message):
        _ = _site(**(values | change))


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"case_mix": (True, 0, 0)}, "case_mix values must be numeric, not boolean"),
        ({"life_years": 0}, "life_years must be positive"),
        ({"support": -1}, "support cannot be negative"),
        ({"case_mix": (0.5, 0.5)}, "case_mix must contain three non-negative finite shares"),
        ({"case_mix": (0.3, 0.3, 0.3)}, "case_mix must sum to one"),
        ({"baseline_transfer": (0.3, 0.6, 2)}, "baseline_transfer must contain three probabilities"),
        ({"mode_air_shift": 0.7}, "mode_air_shift outside scenario bounds"),
    ],
)
def test_parameter_boundary_validation(change: dict[str, object], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        _ = _parameters(**change)


def test_parameter_sequence_type_error() -> None:
    with pytest.raises(TypeError):
        _ = _parameters(case_mix="bad")


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("wrong,column\nA,1\n", "Birth table requires facility, births and year columns"),
        ("facility,births,year,sector\nA,1,2022,private\n", "Birth table must contain public-sector rows only"),
        ("facility,births,year\nA,-1,2022\n", "negative birth count"),
    ],
)
def test_malformed_birth_rows_fail(tmp_path: Path, text: str, message: str) -> None:
    path = tmp_path / "births.csv"
    _ = path.write_text(text)
    with pytest.raises(ValueError, match=message):
        _ = load_sites(path)


def test_survival_cost_cannot_be_negative() -> None:
    with pytest.raises(ValueError, match="Negative annual cost"):
        _ = survival_extension(1, 0.1, 0.5, annual_cost_major=-1)


@pytest.mark.parametrize(
    ("probability", "odds", "message"),
    [(-0.1, 1, "p0 must be between zero and one"), (0.5, 0, "odds_ratio must be positive")],
)
def test_legacy_probability_error_paths(probability: float, odds: int, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        _ = odds_to_probability(probability, odds)


@pytest.mark.parametrize("probability", [0, 1])
def test_legacy_probability_endpoints(probability: int) -> None:
    assert odds_to_probability(probability, 0.5) == probability


def test_legacy_transport_rejects_non_normalized_mix() -> None:
    with pytest.raises(ValueError, match="transport shares must sum to one"):
        _ = weighted_transfer_cost(replace(ModelInputs(), road_share=1))


def test_legacy_survival_arithmetic() -> None:
    result = clinical_extension(100, 0.01, 0.1)
    assert result["extra_survivors"] == 1
    assert math.isclose(result["incremental_qalys"], 23.3)
    assert result["incremental_lifetime_costs"] == 95000
