"""New acceptance must not overwrite earlier evidence or omit the active model."""

import tomllib
from pathlib import Path
from typing import cast

from quality.cli import gates_for_profile

ROOT = Path(__file__).resolve().parents[1]


def test_receipts_and_core_gate_target_current_model() -> None:
    gates = gates_for_profile("full")
    commands = [" ".join(g.command) for g in gates]
    assert not any("verification/v5/" in c for c in commands)
    assert any("verification/v7/scalene.json" in c for c in commands)
    assert "src/pathways_v6.py" in " ".join(next(g for g in gates if g.name == "core_coverage").command)


def test_current_type_mutation_profile_scope() -> None:
    cfg = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert "src/pathways_v6.py" in cfg["tool"]["pytest-gremlins"]["paths"]
    ty_include = cast("list[str]", cfg["tool"]["ty"]["src"]["include"])
    pyright_include = cast("list[str]", cfg["tool"]["basedpyright"]["include"])
    for c in [ty_include, pyright_include]:
        assert "scripts/analyse_v6.py" in c
    assert "compare_v6" in (ROOT / "quality/profile_workload.py").read_text()
