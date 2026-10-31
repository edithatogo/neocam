"""The incremental test path overrides the coverage core only in its child env."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from quality import feedback

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def test_incremental_tests_force_ctrace_core(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Sysmon disables testmon's dynamic contexts, so the child must select ctrace."""
    monkeypatch.setenv("COVERAGE_CORE", "sysmon")
    plan = feedback.prepare(tmp_path, "tests", available=True, environment={})
    env = feedback.child_environment(plan)
    assert env is not None
    assert env["COVERAGE_CORE"] == "ctrace"
    assert set(os.environ) <= set(env)  # the ambient environment is inherited unchanged


def test_mutation_and_unavailable_tests_inherit_ambient_environment(tmp_path: Path) -> None:
    """Only a real incremental test run overrides the core; every other path inherits."""
    mutation = feedback.prepare(tmp_path, "mutation", available=True, environment={})
    assert feedback.child_environment(mutation) is None
    fallback = feedback.prepare(tmp_path, "tests", available=False, environment={})
    assert feedback.child_environment(fallback) is None
