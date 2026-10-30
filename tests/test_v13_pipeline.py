"""Real entrypoint for refinements: resolved inputs, eligibility and safe exports."""

import csv
import json
import shutil
import subprocess  # ruff: ignore[suspicious-subprocess-import] -- fixed argv of the local driver, never shell input
import sys
from pathlib import Path

import pytest

from quality import artifacts
from quality.artifacts import calculation_inputs
from scripts.analyse_refinements import load_refinements, snapshot_identity
from src.deployment import policy_catalogue
from src.portfolios_v7 import portfolio

ROOT = Path(__file__).resolve().parents[1]


def test_catalogue_deduplicates_identical_pilot_policies():
    policies = policy_catalogue(portfolio("pilot"))
    assert len({p.assignments for p in policies}) == len(policies)
    assert len(policies) == 2


def test_refinement_schema_is_strict(tmp_path):
    data = json.loads((ROOT / "config/refinements.json").read_text())
    p = tmp_path / "refinements.json"
    p.write_text(json.dumps(data))
    assert load_refinements(p)["schema_version"] == 1
    data["unexpected"] = 1
    p.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="Refinements requires exactly"):
        load_refinements(p)


def test_real_refinement_pipeline(tmp_path):
    assert (ROOT / "scripts/analyse_refinements.py").exists()
    for folder in ("src", "scripts", "quality", "config", "data"):
        shutil.copytree(ROOT / folder, tmp_path / folder, ignore=shutil.ignore_patterns("__pycache__"))
    f = tmp_path / "config/reference.json"
    data = json.loads(f.read_text())
    data["run"].update(draws=32, portfolios=["pilot", "chhhs"])
    f.write_text(json.dumps(data))
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
    metadata = json.loads((folder / "results.json").read_text())
    assert metadata["draws"] == 32
    assert metadata["independent_validation"] is False
    assert metadata["max_cohort_residual"] < 1e-7
    assert metadata["all_finite"] is True

    def rows(name):
        with (folder / name).open() as f:
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
    checks = json.loads((folder / "review_packet.json").read_text())
    assert all(r["status"] == "pending" for r in checks["reviews"])
    snapshot = json.loads((folder / "resolved_inputs.json").read_text())
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


def test_new_driver_enters_artifact_dependency_manifest(tmp_path):
    (tmp_path / "scripts").mkdir()
    p = tmp_path / "scripts/analyse_refinements.py"
    p.write_text("#one")
    first = calculation_inputs(tmp_path)
    assert "scripts/analyse_refinements.py" in first
    p.write_text("#two")
    assert calculation_inputs(tmp_path) != first


def test_review_snapshot_changes_when_model_source_changes(tmp_path):
    (tmp_path / "src").mkdir()
    p = tmp_path / "src/model.py"
    p.write_text("x=1")
    first = snapshot_identity(tmp_path, {"reference": "a"})
    p.write_text("x=2")
    assert snapshot_identity(tmp_path, {"reference": "a"}) != first


def test_artifact_cli_checks_declared_supplement_not_old_hardcoded_release(tmp_path, monkeypatch):
    (tmp_path / "config").mkdir()
    (tmp_path / "config/assurance.json").write_text(
        json.dumps({
            "evidence_version": "v13",
            "current_output": "outputs/primary",
            "additional_outputs": ["outputs/supplement"],
        })
    )
    for name in ("primary", "supplement"):
        d = tmp_path / "outputs" / name
        d.mkdir(parents=True)
        (d / "result.txt").write_text("value")
        artifacts.seal(tmp_path, d)
    monkeypatch.setattr(artifacts, "__file__", str(tmp_path / "quality/artifacts.py"))
    monkeypatch.setattr(sys, "argv", ["artifacts", "verify"])
    assert artifacts.main() == 0
    (tmp_path / "outputs/supplement/result.txt").write_text("changed")
    assert artifacts.main() == 1


def test_contact_config_must_reject_duplicate_semantic_scenarios(tmp_path):
    d = json.loads((ROOT / "config/refinements.json").read_text())
    dup = dict(d["activity_scenarios"][0], id="another")
    d["activity_scenarios"].append(dup)
    p = tmp_path / "c.json"
    p.write_text(json.dumps(d))
    with pytest.raises(ValueError, match="Duplicate semantic activity scenario"):
        load_refinements(p)
