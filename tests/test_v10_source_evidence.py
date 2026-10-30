"""Fail-closed source evidence and non-overwriting report contracts."""

import json
import subprocess  # ruff: ignore[suspicious-subprocess-import] -- fixed local CLI argv, never shell input
import sys
from pathlib import Path

import pytest

from quality.cli import gates_for_profile
from quality.source_archive import verify_manifest


@pytest.mark.parametrize("files", [[None], ["not a record"], [42]])
def test_manifest_rows_fail_closed_without_crashing(tmp_path: Path, files: list[object]) -> None:
    assert verify_manifest(tmp_path, {"files": files})


def test_non_string_manifest_path_is_a_validation_error(tmp_path: Path) -> None:
    assert verify_manifest(tmp_path, {"files": [{"path": 17}]})


def test_source_gate_declares_versioned_output() -> None:
    command = next(g.command for g in gates_for_profile("full") if g.name == "source_integrity")
    assert "--output" in command
    assert command[command.index("--output") + 1] == "verification/v7/source_archive.json"


def test_source_cli_accepts_nondefault_report_and_preserves_old_report(tmp_path: Path) -> None:
    source = Path("quality/source_archive.py").read_text(encoding="utf-8")
    project = tmp_path / "project"
    (project / "quality").mkdir(parents=True)
    (project / "sources").mkdir()
    (project / "verification/v7").mkdir(parents=True)
    _ = (project / "quality/source_archive.py").write_text(source)
    _ = (project / "sources/manifest.json").write_text(json.dumps({"files": []}))
    old = project / "verification/v7/source_archive.json"
    _ = old.write_text("historical evidence")
    result = subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true] -- fixed local CLI argv, no shell
        [
            sys.executable,
            str(project / "quality/source_archive.py"),
            "--output",
            "verification/v10/source_archive.json",
        ],
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert old.read_text() == "historical evidence"
    new = project / "verification/v10/source_archive.json"
    assert new.is_file()
    assert json.loads(new.read_text())["stored_file_integrity_passed"] is False
