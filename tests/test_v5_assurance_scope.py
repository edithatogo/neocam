"""New scientific modules and receipts must enter the existing assurance scope."""

import importlib.metadata
import tomllib
from pathlib import Path
from typing import cast

import pytest

from quality import checks
from quality.cli import gates_for_profile

ROOT = Path(__file__).resolve().parents[1]


def test_current_receipts_do_not_overwrite_previous_version() -> None:
    commands = [" ".join(g.command) for g in gates_for_profile("full")]
    assert not any("verification/v4/" in c for c in commands)
    assert any("verification/v7/scalene.json" in c for c in commands)


def test_new_numerical_modules_are_mutation_targets() -> None:
    cfg = tomllib.loads((ROOT / "pyproject.toml").read_text())
    paths = cast("list[str]", cfg["tool"]["pytest-gremlins"]["paths"])
    assert {"src/strategies.py", "src/sensitivity.py"} <= set(paths)


def test_analysis_script_is_in_both_typecheck_scopes() -> None:
    cfg = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert "scripts/analyse_v5.py" in cfg["tool"]["ty"]["src"]["include"]
    assert "scripts/analyse_v5.py" in cfg["tool"]["basedpyright"]["include"]


def test_lock_validation_does_not_try_network_resolution() -> None:
    gate = next(g for g in gates_for_profile("full") if g.name == "dependency_consistency")
    assert "--offline" in gate.command


def test_version_gate_covers_optional_research_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    queried: list[str] = []

    def installed(name: str) -> str:
        queried.append(name)
        return "0.0.0"

    monkeypatch.setattr(importlib.metadata, "version", installed)
    _ = checks.version_errors(ROOT)
    assert {"scipy", "scikit-learn"} <= set(queried)


def test_full_ci_installs_research_extra_for_analysis_reproduction() -> None:
    text = (ROOT / ".github/workflows/ci.yml").read_text()
    assert "--group assurance --extra tabular --extra research" in text
