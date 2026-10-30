"""Real entrypoint for refinements: resolved inputs, eligibility and safe exports."""

import csv
import json
import shutil
import subprocess  # ruff: ignore[suspicious-subprocess-import] -- fixed argv of the local driver, never shell input
import sys
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict, cast

import pytest

from quality import artifacts
from quality.artifacts import calculation_inputs
from scripts import analyse_refinements
from src.deployment import policy_catalogue
from src.portfolios_v7 import portfolio

if TYPE_CHECKING:
    from collections.abc import Callable

ROOT = Path(__file__).resolve().parents[1]


class RefinementRun(TypedDict):
    """Recorded refinement run metadata read from results.json."""

    draws: int
    independent_validation: bool
    max_cohort_residual: float
    all_finite: bool


class RunControls(TypedDict):
    """The ``run`` table of a resolved reference configuration."""

    run: dict[str, object]


class ReviewPacket(TypedDict):
    """Recorded external-review packet."""

    reviews: list[dict[str, object]]


# The driver declares bare dicts; restate the asserted shapes.
load_refinements = cast("Callable[..., dict[str, object]]", analyse_refinements.load_refinements)
snapshot_identity = cast("Callable[..., str]", analyse_refinements.snapshot_identity)


def test_catalogue_deduplicates_identical_pilot_policies() -> None:
    policies = policy_catalogue(portfolio("pilot"))
    assert len({p.assignments for p in policies}) == len(policies)
    assert len(policies) == 2


def test_refinement_schema_is_strict(tmp_path: Path) -> None:
    data = cast("dict[str, object]", json.loads((ROOT / "config/refinements.json").read_text()))
    p = tmp_path / "refinements.json"
    _ = p.write_text(json.dumps(data))
    assert load_refinements(p)["schema_version"] == 1
    data["unexpected"] = 1
    _ = p.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="Refinements requires exactly"):
        _ = load_refinements(p)


def test_real_refinement_pipeline(tmp_path: Path) -> None:
    assert (ROOT / "scripts/analyse_refinements.py").exists()
    for folder in ("src", "scripts", "quality", "config", "data"):
        _ = shutil.copytree(ROOT / folder, tmp_path / folder, ignore=shutil.ignore_patterns("__pycache__"))
    f = tmp_path / "config/reference.json"
    data = cast("RunControls", json.loads(f.read_text()))
    data["run"].update(draws=32, portfolios=["pilot", "chhhs"])
    _ = f.write_text(json.dumps(data))
    result = subprocess.run(
        [sys.executable, "-m", "scripts.analyse_refinements", "--output", "outputs/check"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    folder = tmp_path / "outputs/check"
    metadata = cast("RefinementRun", json.loads((folder / "results.json").read_text()))
    assert metadata["draws"] == 32
    assert metadata["independent_validation"] is False
    assert metadata["max_cohort_residual"] < 1e-7
    assert metadata["all_finite"] is True

    def rows(name: str) -> list[dict[str, str]]:
        with (folder / name).open(encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f))

    table = rows("policy_deterministic.csv")
    row = next(
        r
        for r in table
        if r["portfolio"] == "chhhs"
        and r["policy"] == "retain_pilot_expand_obsbot"
        and r["activity_id"] == "contacts_1"
    )
    assert float(row["initial_purchase_capital"]) == pytest.approx(31500)
    assert row["conditional_policy"] == "True"
    reported = rows("policy_rankings.csv")
    assert all(
        r["policy"] in {"telephone", "retain_pilot_only"} for r in reported if r["decision_set"] == "reported_operation"
    )
    assert all(0 <= float(r["probability_optimal"]) <= 1 for r in reported)
    checks = cast("ReviewPacket", json.loads((folder / "review_packet.json").read_text()))
    assert all(r["status"] == "pending" for r in checks["reviews"])
    snapshot = cast("dict[str, object]", json.loads((folder / "resolved_inputs.json").read_text()))
    assert "refinements_sha256" in snapshot
    # Shared reference is not overwritten or compared as an empirical observation.
    assert (folder / "policy_predictive.csv").exists()
    assert (folder / "policy_budget.csv").exists()
    assert (folder / "eligibility.csv").exists()
    assert (folder / "policy_assignments.csv").exists()
    refusal = subprocess.run(
        [sys.executable, "-m", "scripts.analyse_refinements", "--output", "outputs/check"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert refusal.returncode != 0


def test_new_driver_enters_artifact_dependency_manifest(tmp_path: Path) -> None:
    (tmp_path / "scripts").mkdir()
    p = tmp_path / "scripts/analyse_refinements.py"
    _ = p.write_text("#one")
    first = calculation_inputs(tmp_path)
    assert "scripts/analyse_refinements.py" in first
    _ = p.write_text("#two")
    assert calculation_inputs(tmp_path) != first


def test_review_snapshot_changes_when_model_source_changes(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    p = tmp_path / "src/model.py"
    _ = p.write_text("x=1")
    first = snapshot_identity(tmp_path, {"reference": "a"})
    _ = p.write_text("x=2")
    assert snapshot_identity(tmp_path, {"reference": "a"}) != first


def test_artifact_cli_checks_declared_supplement_not_old_hardcoded_release(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "config").mkdir()
    _ = (tmp_path / "config/assurance.json").write_text(
        json.dumps({
            "evidence_version": "v13",
            "current_output": "outputs/primary",
            "additional_outputs": ["outputs/supplement"],
        })
    )
    for name in ("primary", "supplement"):
        d = tmp_path / "outputs" / name
        d.mkdir(parents=True)
        _ = (d / "result.txt").write_text("value")
        _ = artifacts.seal(tmp_path, d)
    monkeypatch.setattr(artifacts, "__file__", str(tmp_path / "quality/artifacts.py"))
    monkeypatch.setattr(sys, "argv", ["artifacts", "verify"])
    assert artifacts.main() == 0
    _ = (tmp_path / "outputs/supplement/result.txt").write_text("changed")
    assert artifacts.main() == 1


def test_contact_config_must_reject_duplicate_semantic_scenarios(tmp_path: Path) -> None:
    d = cast("dict[str, object]", json.loads((ROOT / "config/refinements.json").read_text()))
    scenarios = cast("list[dict[str, object]]", d["activity_scenarios"])
    scenarios.append(dict(scenarios[0], id="another"))
    p = tmp_path / "c.json"
    _ = p.write_text(json.dumps(d))
    with pytest.raises(ValueError, match="Duplicate semantic activity scenario"):
        _ = load_refinements(p)
