"""Portable skill evidence contracts: these are not independent agent tests."""

import hashlib
import importlib.util
from pathlib import Path
from typing import Protocol, cast

import pytest


class EvidenceChecker(Protocol):
    """The portable evidence checker loaded from the skill payload."""

    def audit(self, report: object, root: Path, required: set[str], fingerprint: str) -> list[str]:
        """Return attestation errors for a claimed receipt scope."""
        ...


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents/skills/maintaining-lean-ci"


def checker() -> EvidenceChecker:
    """Load the vendored portable evidence checker from its file path.

    Returns:
        The executed checker typed as the audit surface these tests use.
    """
    p = SKILL / "scripts/audit_evidence.py"
    assert p.exists(), "Portable evidence checker has not been created"
    spec = importlib.util.spec_from_file_location("portable_audit", p)
    assert spec is not None
    assert spec.loader is not None
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    # exec_module yields ModuleType; the audited surface is asserted by these tests.
    return cast("EvidenceChecker", cast("object", m))


def receipt(root: Path) -> dict[str, object]:
    _ = (root / "run.txt").write_text("254 passed")
    return {
        "profile": "full",
        "full_local_assurance": True,
        "receipts": [
            {
                "gate": "tests",
                "status": "passed",
                "returncode": 0,
                "fingerprint": "abc",
                "duration_seconds": 1,
                "log": "run.txt",
                "log_sha256": hashlib.sha256(b"254 passed").hexdigest(),
            }
        ],
    }


def test_skill_trigger_and_size() -> None:
    path = SKILL / "SKILL.md"
    assert path.exists()
    text = path.read_text()
    assert "description: Use when" in text
    assert len(text.split()) < 750
    assert "testmon" in text
    assert "Polars" in text
    assert "independent agent" in text


def test_valid_full_receipt_is_scoped_not_hosted_assurance(tmp_path: Path) -> None:
    assert checker().audit(receipt(tmp_path), tmp_path, {"tests"}, "abc") == []


@pytest.mark.parametrize("change", [{"profile": "quick"}, {"full_local_assurance": False}, {"cache_reused": True}])
def test_partial_or_cached_evidence_cannot_certify_acceptance(tmp_path: Path, change: dict[str, object]) -> None:
    r = receipt(tmp_path)
    r.update(change)
    assert checker().audit(r, tmp_path, {"tests"}, "abc")


def test_missing_gate_not_overridden_by_claimed_green(tmp_path: Path) -> None:
    r = receipt(tmp_path)
    r["release_ready"] = True
    assert checker().audit(r, tmp_path, {"tests", "mutation"}, "abc")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("status", "blocked"),
        ("returncode", 5),
        ("fingerprint", "stale"),
        ("log_sha256", "0" * 64),
        ("log", "../outside"),
        ("duration_seconds", -1),
    ],
)
def test_adversarial_evidence_rejected(tmp_path: Path, field: str, value: object) -> None:
    r = receipt(tmp_path)
    receipts = cast("list[dict[str, object]]", r["receipts"])
    receipts[0][field] = value
    assert checker().audit(r, tmp_path, {"tests"}, "abc")


def test_duplicate_gate_rejected(tmp_path: Path) -> None:
    r = receipt(tmp_path)
    r["receipts"] = cast("list[dict[str, object]]", r["receipts"]) * 2
    assert checker().audit(r, tmp_path, {"tests"}, "abc")


def test_required_scope_cannot_be_empty(tmp_path: Path) -> None:
    assert checker().audit(receipt(tmp_path), tmp_path, set(), "abc")


def test_conflicting_top_level_fingerprint_rejected(tmp_path: Path) -> None:
    r = receipt(tmp_path)
    r["input_fingerprint"] = "wrong"
    assert checker().audit(r, tmp_path, {"tests"}, "abc")


def test_expected_fingerprint_cannot_be_empty(tmp_path: Path) -> None:
    r = receipt(tmp_path)
    receipts = cast("list[dict[str, object]]", r["receipts"])
    receipts[0]["fingerprint"] = ""
    assert checker().audit(r, tmp_path, {"tests"}, "")
