"""Run the actual analysis CLI using a modified declared scenario."""

import csv
import json
import os
import shutil
import subprocess  # ruff: ignore[suspicious-subprocess-import] -- fixed local CLI argv, never shell input
import sys
from pathlib import Path
from typing import TypedDict, cast

import pytest

ROOT = Path(__file__).resolve().parents[1]


class ConfigDocument(TypedDict):
    """The declared-input documents this test rewrites."""

    run: dict[str, object]
    equipment_cost: float


class ResolvedInputs(TypedDict):
    """Resolved-input record emitted by the driver."""

    parameters: dict[str, float]


def test_real_entrypoint_consumes_configuration_and_preserves_old_outputs(tmp_path: Path) -> None:
    def trace(stage: str) -> None:
        with (tmp_path / "trace.txt").open("a") as f:
            _ = f.write(stage + "\n")

    trace("started")
    for name in ("src", "scripts", "config", "data"):
        _ = shutil.copytree(ROOT / name, tmp_path / name, ignore=shutil.ignore_patterns("__pycache__"))
    p = tmp_path / "data/parameters.json"
    d = cast("ConfigDocument", json.loads(p.read_text()))
    d["equipment_cost"] = 20000
    _ = p.write_text(json.dumps(d))
    f = tmp_path / "config/reference.json"
    d = cast("ConfigDocument", json.loads(f.read_text()))
    d["run"]["draws"] = 32
    d["run"]["portfolios"] = ["pilot"]
    _ = f.write_text(json.dumps(d))
    trace("before first subprocess")
    result = subprocess.run(
        [sys.executable, "-m", "scripts.analyse_v7", "--config", "config/reference.json", "--output", "outputs/check"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=90,
        env=os.environ.copy(),
        check=False,
    )
    trace("first returned " + str(result.returncode))
    assert result.returncode == 0, result.stderr
    target = tmp_path / "outputs/check"
    assert target.is_dir(), "Driver did not honour the output argument"
    with (target / "deterministic.csv").open() as stream:
        values = list(csv.DictReader(stream))
    assert next(r for r in values if r["strategy"] == "panda")["sites"] == "3"
    inputs = cast("ResolvedInputs", json.loads((target / "resolved_inputs.json").read_text()))
    assert inputs["parameters"]["equipment_cost"] == 20000
    assert json.loads((target / "results.json").read_text())["draws"] == 32
    with (target / "utility_bridge_scenarios.csv").open() as stream:
        utility = list(csv.DictReader(stream))
    r = next(
        r
        for r in utility
        if float(r["utility_difference"]) == pytest.approx(0.13)
        and int(r["duration_years_assumed"]) == 1
        and float(r["discount_rate"]) == pytest.approx(0.05)
        and float(r["fraction_consultations_improved_assumed"]) == pytest.approx(0.001)
    )
    assert float(r["qalys_per_1000_consultations"]) == pytest.approx(0.13 / 1.05**11)
    assert (target / "mixed_estate_budget.csv").exists()
    assert (target / "prior_predictive.csv").exists()
    trace("before overwrite refusal")
    rerun = subprocess.run(
        [sys.executable, "-m", "scripts.analyse_v7", "--output", "outputs/check"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    trace("second returned " + str(rerun.returncode))
    assert rerun.returncode != 0, "Existing release was silently overwritten"
