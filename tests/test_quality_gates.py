"""Reject false-positive mutation reports and preserve complete tool coverage."""

from __future__ import annotations

import hashlib
import io
import tarfile
from typing import TYPE_CHECKING, cast

import pytest

from quality.bootstrap import unpack_binary
from quality.checks import mutation_errors
from quality.cli import gates_for_profile

if TYPE_CHECKING:
    from pathlib import Path


def mutation_report(
    zapped: int = 90, survived: int = 10, timeout: int = 0, error: int = 0, pardoned: int = 0
) -> dict[str, object]:
    total = zapped + survived + timeout + error + pardoned
    return {
        "summary": {
            "total": total,
            "zapped": zapped,
            "survived": survived,
            "timeout": timeout,
            "error": error,
            "pardoned": pardoned,
            "percentage": 100 * zapped / max(total, 1),
        }
    }


def test_mutation_target_met() -> None:
    assert mutation_errors(mutation_report()) == []


@pytest.mark.parametrize(
    "data",
    [
        mutation_report(80, 20),
        mutation_report(0, 0),
        mutation_report(90, 9, 1),
        mutation_report(90, 9, 0, 1),
        mutation_report(90, 9, 0, 0, 1),
        {},
        {"summary": {"percentage": 100}},
        mutation_report(-1, 0),
    ],
)
def test_unreliable_mutation_result_cannot_pass(data: object) -> None:
    assert mutation_errors(data)


def test_lying_mutation_percentage_cannot_pass() -> None:
    data = mutation_report(10, 90)
    summary = cast("dict[str, object]", data["summary"])
    summary["percentage"] = 100
    assert mutation_errors(data)


def test_all_requested_tool_gates_are_mandatory() -> None:
    names = {gate.name for gate in gates_for_profile("full")}
    assert {
        "ruff_lint",
        "ruff_format",
        "ty",
        "basedpyright",
        "hypothesis",
        "gremlins",
        "mutation_score",
        "scalene",
        "scalene_output",
        "gitleaks_history",
        "gitleaks_tree",
        "vale",
        "dependency_lock",
        "locked_versions",
        "pip_audit",
        "sbom",
        "conductor_checkout",
        "polars_consistency",
        "pytest",
        "coverage",
        "coverage_threshold",
        "inputs",
        "context",
    } <= names


def test_quick_is_a_strict_subset_not_a_release_shortcut() -> None:
    quick = {gate.name for gate in gates_for_profile("quick")}
    full = {gate.name for gate in gates_for_profile("full")}
    assert quick < full
    assert quick == {"pytest", "inputs", "context"}


def test_unknown_profile_rejected() -> None:
    with pytest.raises(ValueError, match="Unknown assurance profile"):
        _ = gates_for_profile("ci")


def binary_tar(name: str = "vale", payload: bytes = b"binary") -> bytes:
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w:gz") as archive:
        info = tarfile.TarInfo(name)
        info.size = len(payload)
        archive.addfile(info, io.BytesIO(payload))
    return stream.getvalue()


def test_pinned_binary_bytes_extract_without_executing(tmp_path: Path) -> None:
    payload = binary_tar()
    path = unpack_binary(payload, hashlib.sha256(payload).hexdigest(), "vale", tmp_path)
    assert path.read_bytes() == b"binary"


def test_checksum_mismatch_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="checksum"):
        _ = unpack_binary(binary_tar(), "0" * 64, "vale", tmp_path)


def test_archive_traversal_rejected(tmp_path: Path) -> None:
    payload = binary_tar("../vale")
    with pytest.raises(ValueError, match="Archive must contain one exact regular executable"):
        _ = unpack_binary(payload, hashlib.sha256(payload).hexdigest(), "vale", tmp_path)
    assert not (tmp_path.parent / "vale").exists()


def test_archive_missing_executable_rejected(tmp_path: Path) -> None:
    payload = binary_tar("not-vale")
    with pytest.raises(ValueError, match="Archive must contain one exact regular executable"):
        _ = unpack_binary(payload, hashlib.sha256(payload).hexdigest(), "vale", tmp_path)


def test_mismatched_mutation_counts_rejected() -> None:
    data = mutation_report()
    summary = cast("dict[str, object]", data["summary"])
    summary["total"] = 101
    assert mutation_errors(data)


def test_unknown_native_tool_rejected(tmp_path: Path) -> None:
    payload = binary_tar()
    with pytest.raises(ValueError, match="Unknown native tool"):
        _ = unpack_binary(payload, hashlib.sha256(payload).hexdigest(), "arbitrary", tmp_path)
