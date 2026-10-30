"""Reject false-positive mutation reports and preserve complete tool coverage."""

import hashlib
import io
import tarfile

import pytest

from quality.bootstrap import unpack_binary
from quality.checks import mutation_errors
from quality.cli import gates_for_profile


def mutation_report(zapped=90, survived=10, timeout=0, error=0, pardoned=0):
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


def test_mutation_target_met():
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
def test_unreliable_mutation_result_cannot_pass(data):
    assert mutation_errors(data)


def test_lying_mutation_percentage_cannot_pass():
    data = mutation_report(10, 90)
    data["summary"]["percentage"] = 100
    assert mutation_errors(data)


def test_all_requested_tool_gates_are_mandatory():
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


def test_quick_is_a_strict_subset_not_a_release_shortcut():
    quick = {gate.name for gate in gates_for_profile("quick")}
    full = {gate.name for gate in gates_for_profile("full")}
    assert quick < full
    assert quick == {"pytest", "inputs", "context"}


def test_unknown_profile_rejected():
    with pytest.raises(ValueError, match="Unknown assurance profile"):
        gates_for_profile("ci")


def binary_tar(name="vale", payload=b"binary"):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w:gz") as archive:
        info = tarfile.TarInfo(name)
        info.size = len(payload)
        archive.addfile(info, io.BytesIO(payload))
    return stream.getvalue()


def test_pinned_binary_bytes_extract_without_executing(tmp_path):
    payload = binary_tar()
    path = unpack_binary(payload, hashlib.sha256(payload).hexdigest(), "vale", tmp_path)
    assert path.read_bytes() == b"binary"


def test_checksum_mismatch_rejected(tmp_path):
    with pytest.raises(ValueError, match="checksum"):
        unpack_binary(binary_tar(), "0" * 64, "vale", tmp_path)


def test_archive_traversal_rejected(tmp_path):
    payload = binary_tar("../vale")
    with pytest.raises(ValueError, match="Archive must contain one exact regular executable"):
        unpack_binary(payload, hashlib.sha256(payload).hexdigest(), "vale", tmp_path)
    assert not (tmp_path.parent / "vale").exists()


def test_archive_missing_executable_rejected(tmp_path):
    payload = binary_tar("not-vale")
    with pytest.raises(ValueError, match="Archive must contain one exact regular executable"):
        unpack_binary(payload, hashlib.sha256(payload).hexdigest(), "vale", tmp_path)


def test_mismatched_mutation_counts_rejected():
    data = mutation_report()
    data["summary"]["total"] = 101
    assert mutation_errors(data)


def test_unknown_native_tool_rejected(tmp_path):
    payload = binary_tar()
    with pytest.raises(ValueError, match="Unknown native tool"):
        unpack_binary(payload, hashlib.sha256(payload).hexdigest(), "arbitrary", tmp_path)
