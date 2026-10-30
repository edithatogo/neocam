"""Review-record integrity cannot manufacture independent clinical validation."""

from typing import TYPE_CHECKING, TypedDict, cast

import pytest

from quality.clinical_review import review_errors
from scripts import analyse_refinements

if TYPE_CHECKING:
    from collections.abc import Callable

SNAPSHOT = "a" * 64


class Packet(TypedDict):
    """External review packet template returned by the refinement driver."""

    reviews: list[dict[str, object]]
    review_type: str


pending_reviews = cast("Callable[..., Packet]", analyse_refinements.pending_reviews)


def packet() -> Packet:
    p = pending_reviews(SNAPSHOT)
    for i, r in enumerate(p["reviews"]):
        r.update(
            identity=f"Reviewer {i + 1}",
            independent=True,
            status="approved",
            conflicts="None declared",
            date="2026-10-29",
            finding_summary="Assessed declared scope; no unresolved material issues.",
            evidence=["Documented report locator"],
        )
    p["review_type"] = "external reviewer attestation"
    return p


def test_pending_is_not_validation() -> None:
    assert review_errors(pending_reviews(SNAPSHOT), SNAPSHOT)


def test_valid_attestation_schema_only_not_identity_proof() -> None:
    assert review_errors(packet(), SNAPSHOT) == []


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("identity", ""),
        ("independent", False),
        ("independent", 1),
        ("status", "pending"),
        ("conflicts", ""),
        ("date", "bad"),
        ("finding_summary", ""),
        ("evidence", []),
        ("snapshot_sha256", "b" * 64),
        ("role", "invented"),
    ],
)
def test_missing_or_false_attestation_fails(field: str, value: object) -> None:
    p = packet()
    p["reviews"][0][field] = value
    assert review_errors(p, SNAPSHOT)


def test_duplicate_role_and_empty_scope_fail() -> None:
    p = packet()
    p["reviews"][1] = p["reviews"][0].copy()
    assert review_errors(p, SNAPSHOT)
    assert review_errors({"reviews": []}, SNAPSHOT)


def test_simulated_or_stale_record_fails() -> None:
    p = packet()
    p["review_type"] = "simulated author roles"
    assert review_errors(p, SNAPSHOT)
    assert review_errors(packet(), "b" * 64)
    assert review_errors(packet(), "")


def test_approved_record_with_unresolved_finding_fails() -> None:
    p = packet()
    findings: list[dict[str, object]] = [
        {
            "severity": "high",
            "description": "Unknown outcome definition",
            "status": "open",
            "resolution": "",
            "evidence": [],
        }
    ]
    p["reviews"][0]["findings"] = findings
    assert review_errors(p, SNAPSHOT)
    findings[0].update(status="resolved", resolution="Definition reconciled", evidence=["Evidence locator"])
    assert review_errors(p, SNAPSHOT) == []


@pytest.mark.parametrize("bad", [None, [], {"reviews": None}, {"reviews": [None]}, "a"])
def test_malformed_review_fails_without_crash(bad: object) -> None:
    assert review_errors(bad, SNAPSHOT)


@pytest.mark.parametrize("finding", [None, {"severity": "high"}, {"severity": [], "status": "resolved"}])
def test_malformed_findings_fail_without_exception(finding: object) -> None:
    p = packet()
    p["reviews"][0]["findings"] = [finding]
    assert review_errors(p, SNAPSHOT)
