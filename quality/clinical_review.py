"""Validate external-review records; schema validity is not proof of reviewer identity."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path

ROLES = frozenset({"neonatal_retrieval", "health_economics", "technical", "consumer_rural"})
SEVERITIES = frozenset({"critical", "high", "medium", "low"})


def _text(value: object) -> bool:
    """Return whether a value is non-placeholder prose.

    Returns:
        bool: True when the value is a nonempty string that is not a placeholder.
    """
    return (
        isinstance(value, str)
        and bool(value.strip())
        and value.strip().lower() not in {"tbd", "pending", "unknown", "placeholder"}
    )


def _evidence(value: object) -> bool:
    """Return whether a value is a nonempty list of prose evidence items.

    Returns:
        bool: True when the value is a nonempty list of valid text items.
    """
    return isinstance(value, list) and bool(value) and all(_text(item) for item in value)


def _finding_errors(index: int, finding: object) -> list[str]:
    """Return the errors for one review finding record.

    Returns:
        list[str]: Errors for the finding; empty when it is resolved and documented.
    """
    if not isinstance(finding, dict):
        return [f"Review {index} contains a malformed finding"]
    severity = finding.get("severity")
    valid_severity = isinstance(severity, str) and severity in SEVERITIES
    if (
        valid_severity
        and _text(finding.get("description"))
        and finding.get("status") == "resolved"
        and _text(finding.get("resolution"))
        and _evidence(finding.get("evidence"))
    ):
        return []
    return [f"Review {index} contains an unresolved or undocumented finding"]


def _record_errors(index: int, record: object, expected_snapshot: str) -> tuple[list[str], str | None]:
    """Return the attestation errors and known role for one review record.

    Returns:
        tuple[list[str], str | None]: Errors for the record and its validated role.
    """
    if not isinstance(record, dict):
        return [f"Malformed review record {index}"], None
    errors: list[str] = []
    role = record.get("role")
    known_role = role if isinstance(role, str) and role in ROLES else None
    if known_role is None:
        errors.append(f"Unknown role at record {index}")
    errors.extend(
        f"Review {index} lacks {field}"
        for field in ("identity", "conflicts", "finding_summary")
        if not _text(record.get(field))
    )
    if record.get("independent") is not True or record.get("status") != "approved":
        errors.append(f"Review {index} has no independent completed attestation")
    if record.get("snapshot_sha256") != expected_snapshot:
        errors.append(f"Review {index} has a stale or absent snapshot")
    try:
        date.fromisoformat(record.get("date", ""))
    except (TypeError, ValueError):
        errors.append(f"Review {index} lacks a valid date")
    if not _evidence(record.get("evidence")):
        errors.append(f"Review {index} lacks supporting report evidence")
    findings = record.get("findings")
    if not isinstance(findings, list):
        return [*errors, f"Review {index} findings malformed"], known_role
    for finding in findings:
        errors.extend(_finding_errors(index, finding))
    return errors, known_role


def review_errors(packet: object, expected_snapshot: str) -> list[str]:
    """Check complete, snapshot-matched attestation fields without inventing sign-off.

    Approval requires an actual independently authored report outside this schema.
    This function cannot authenticate identities or adjudicate clinical adequacy.

    Returns:
        list[str]: Attestation errors; empty when the review packet is complete.
    """
    errors = []
    if not isinstance(expected_snapshot, str) or not re.fullmatch(r"[a-f0-9]{64}", expected_snapshot):
        return ["Expected exact analysis snapshot digest is required"]
    if not isinstance(packet, dict):
        return ["Review packet must be an object"]
    if packet.get("snapshot_sha256") != expected_snapshot:
        errors.append("Review packet does not match analysis snapshot")
    if packet.get("review_type") != "external reviewer attestation":
        errors.append("External reviewer attestation is not recorded")
    rows = packet.get("reviews")
    if not isinstance(rows, list) or not rows:
        return [*errors, "Review scope is empty or malformed"]
    roles = []
    for index, record in enumerate(rows):
        record_errors, role = _record_errors(index, record, expected_snapshot)
        errors.extend(record_errors)
        if role is not None:
            roles.append(role)
    if set(roles) != ROLES or len(roles) != len(ROLES):
        errors.append("All four distinct review roles are required")
    return errors


def main() -> int:
    """Validate one review packet against an exact analysis snapshot digest.

    Returns:
        int: 0 when the attestation contract holds, otherwise 1.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path)
    parser.add_argument("--snapshot", required=True)
    args = parser.parse_args()
    try:
        packet = json.loads(args.packet.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        packet = None
    errors = review_errors(packet, args.snapshot)
    print(  # ruff: ignore[print] -- CLI review report goes to stdout
        json.dumps(
            {
                "errors": errors,
                "record_contract_passed": not errors,
                "identity_authenticated": False,
                "scope": "Attestation schema only; cannot certify reviewer independence or clinical validity",
            },
            indent=2,
        )
    )
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
