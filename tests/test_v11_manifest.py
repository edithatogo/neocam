"""The source audit must fail closed on adversarial metadata and JSON shapes."""

import hashlib
import json
import subprocess  # ruff: ignore[suspicious-subprocess-import] -- fixed local CLI argv, never shell input
import sys
from pathlib import Path

import pytest

from quality.source_archive import verify_manifest


def fixture(root: Path) -> dict[str, object]:
    _ = (root / "sample.txt").write_bytes(b"x")
    return {
        "path": "sample.txt",
        "bytes": 1,
        "sha256": hashlib.sha256(b"x").hexdigest(),
        "representation": "original public bytes",
        "source_id": "S1",
    }


@pytest.mark.parametrize("value", [None, [None], [[]], ["S1", "S1"], "S1"])
def test_invalid_original_source_scope_is_an_error(tmp_path: Path, value: object) -> None:
    item = fixture(tmp_path)
    errors = verify_manifest(
        tmp_path, {"files": [item], "original_public_downloads_complete": True, "expected_original_source_ids": value}
    )
    assert errors


def test_boolean_byte_count_is_not_an_integer_size(tmp_path: Path) -> None:
    item = fixture(tmp_path)
    item["bytes"] = True
    assert verify_manifest(tmp_path, {"files": [item]})


def test_original_source_id_must_be_a_string(tmp_path: Path) -> None:
    item = fixture(tmp_path)
    item["source_id"] = []
    assert verify_manifest(
        tmp_path, {"files": [item], "original_public_downloads_complete": True, "expected_original_source_ids": ["S1"]}
    )


def test_duplicate_canonical_paths_rejected(tmp_path: Path) -> None:
    item = fixture(tmp_path)
    alias = dict(item, path="./sample.txt")
    assert verify_manifest(tmp_path, {"files": [item, alias]})


@pytest.mark.parametrize("manifest", [[], None, {"files": None}, {"files": []}])
def test_cli_retains_a_failed_report_for_malformed_manifest(tmp_path: Path, manifest: object) -> None:
    (tmp_path / "quality").mkdir()
    (tmp_path / "sources").mkdir()
    source = Path("quality/source_archive.py").read_text(encoding="utf-8")
    _ = (tmp_path / "quality/source_archive.py").write_text(source)
    _ = (tmp_path / "sources/manifest.json").write_text(json.dumps(manifest))
    result = subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true] -- fixed local CLI argv, no shell
        [
            sys.executable,
            str(tmp_path / "quality/source_archive.py"),
            "--output",
            "verification/v11/source_archive.json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    report_path = tmp_path / "verification/v11/source_archive.json"
    assert report_path.is_file()
    assert json.loads(report_path.read_text())["stored_file_integrity_passed"] is False
    assert "Traceback" not in result.stderr
