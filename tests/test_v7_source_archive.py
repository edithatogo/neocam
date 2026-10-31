"""Source-byte claims must follow hashes, paths and actual representations."""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

from quality import source_archive
from quality.assurance import input_fingerprint
from quality.cli import gates_for_profile

if TYPE_CHECKING:
    from pathlib import Path


def test_hash_mismatch_is_not_an_original_file(tmp_path: Path) -> None:
    p = tmp_path / "sources"
    p.mkdir()
    _ = (p / "a.txt").write_text("actual")
    m = {
        "files": [{"path": "sources/a.txt", "sha256": "0" * 64, "bytes": 6}],
        "original_public_downloads_complete": False,
    }
    assert source_archive.verify_manifest(tmp_path, m)


def test_path_escape_rejected(tmp_path: Path) -> None:
    m = {"files": [{"path": "../outside", "sha256": "0" * 64, "bytes": 0}]}
    assert source_archive.verify_manifest(tmp_path, m)


def test_empty_archive_cannot_claim_all_public_originals(tmp_path: Path) -> None:
    assert source_archive.verify_manifest(tmp_path, {"files": [], "original_public_downloads_complete": True})


def test_actual_bytes_pass_but_do_not_imply_original_completeness(tmp_path: Path) -> None:
    p = tmp_path / "sources"
    p.mkdir()
    _ = (p / "a.txt").write_text("actual")
    m = {
        "files": [{"path": "sources/a.txt", "sha256": hashlib.sha256(b"actual").hexdigest(), "bytes": 6}],
        "original_public_downloads_complete": False,
    }
    assert source_archive.verify_manifest(tmp_path, m) == []


def test_source_change_invalidates_assurance_fingerprint(tmp_path: Path) -> None:
    folder = tmp_path / "sources"
    folder.mkdir()
    path = folder / "evidence.csv"
    _ = path.write_text("a,1")
    before = input_fingerprint(tmp_path)
    _ = path.write_text("a,2")
    assert before != input_fingerprint(tmp_path)


def test_full_acceptance_requires_source_byte_integrity_gate() -> None:
    gates = {g.name: g for g in gates_for_profile("full")}
    assert "source_integrity" in gates
    assert "quality.source_archive" in gates["source_integrity"].command
