"""Regression tests for plugin identity and version-isolated evidence."""

import itertools
import json
import subprocess  # ruff: ignore[suspicious-subprocess-import] -- fixed local CLI argv, never shell input
import sys
from pathlib import Path

from quality.feedback import prepare


def test_testmon_loads_actual_upstream_plugin_module(tmp_path: Path) -> None:
    """pytest-testmon 2.2.0 declares testmon.pytest_testmon, not testmon."""
    plan = prepare(tmp_path, "tests", available=True, environment={})
    assert ("-p", "testmon.pytest_testmon") in tuple(itertools.pairwise(plan.command))


def test_source_integrity_accepts_evidence_version_and_preserves_history(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    (root / "quality").mkdir(parents=True)
    (root / "sources").mkdir()
    (root / "verification/v7").mkdir(parents=True)
    source = Path("quality/source_archive.py").read_text(encoding="utf-8")
    _ = (root / "quality/source_archive.py").write_text(source)
    historic = root / "verification/v7/source_archive.json"
    _ = historic.write_text("historical evidence\n")
    _ = (root / "sources/manifest.json").write_text(json.dumps({"files": []}))
    result = subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true] -- fixed local CLI argv, no shell
        [sys.executable, str(root / "quality/source_archive.py"), "--output", "verification/v10/source_archive.json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0  # An empty source scope remains a failure.
    assert historic.read_text() == "historical evidence\n"
    assert (root / "verification/v10/source_archive.json").exists()


def test_source_integrity_rejects_unsafe_evidence_version(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    (root / "quality").mkdir(parents=True)
    _ = (root / "quality/source_archive.py").write_text(Path("quality/source_archive.py").read_text(encoding="utf-8"))
    (root / "sources").mkdir()
    _ = (root / "sources/manifest.json").write_text(json.dumps({"files": []}))
    result = subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true] -- fixed local CLI argv, no shell
        [sys.executable, str(root / "quality/source_archive.py"), "--output", "../escape"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert not (tmp_path / "escape").exists()
