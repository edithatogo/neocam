"""Validate external-review records; schema validity is not proof of reviewer identity."""
from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import re

ROLES = frozenset({'neonatal_retrieval', 'health_economics', 'technical', 'consumer_rural'})


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and value.strip().lower() not in {'tbd', 'pending', 'unknown', 'placeholder'}


def _evidence(value: object) -> bool:
    return isinstance(value, list) and bool(value) and all(_text(item) for item in value)


def review_errors(packet: object, expected_snapshot: str) -> list[str]:
    """Check complete, snapshot-matched attestation fields without inventing sign-off.

    Approval requires an actual independently authored report outside this schema.
    This function cannot authenticate identities or adjudicate clinical adequacy.
    """
    errors = []
    if not isinstance(expected_snapshot, str) or not re.fullmatch(r'[a-f0-9]{64}', expected_snapshot):
        return ['Expected exact analysis snapshot digest is required']
    if not isinstance(packet, dict):
        return ['Review packet must be an object']
    if packet.get('snapshot_sha256') != expected_snapshot:
        errors.append('Review packet does not match analysis snapshot')
    if packet.get('review_type') != 'external reviewer attestation':
        errors.append('External reviewer attestation is not recorded')
    rows = packet.get('reviews')
    if not isinstance(rows, list) or not rows:
        return errors + ['Review scope is empty or malformed']
    roles = []
    for index, record in enumerate(rows):
        if not isinstance(record, dict):
            errors.append(f'Malformed review record {index}')
            continue
        role = record.get('role')
        if not isinstance(role, str) or role not in ROLES:
            errors.append(f'Unknown role at record {index}')
        else:
            roles.append(role)
        for field in ('identity', 'conflicts', 'finding_summary'):
            if not _text(record.get(field)):
                errors.append(f'Review {index} lacks {field}')
        if record.get('independent') is not True or record.get('status') != 'approved':
            errors.append(f'Review {index} has no independent completed attestation')
        if record.get('snapshot_sha256') != expected_snapshot:
            errors.append(f'Review {index} has a stale or absent snapshot')
        try:
            date.fromisoformat(record.get('date', ''))
        except (TypeError, ValueError):
            errors.append(f'Review {index} lacks a valid date')
        if not _evidence(record.get('evidence')):
            errors.append(f'Review {index} lacks supporting report evidence')
        findings = record.get('findings')
        if not isinstance(findings, list):
            errors.append(f'Review {index} findings malformed')
            continue
        for finding in findings:
            if not isinstance(finding, dict):
                errors.append(f'Review {index} contains a malformed finding')
                continue
            if (finding.get('severity') not in ('critical', 'high', 'medium', 'low')
                    or not _text(finding.get('description'))
                    or finding.get('status') != 'resolved'
                    or not _text(finding.get('resolution')) or not _evidence(finding.get('evidence'))):
                errors.append(f'Review {index} contains an unresolved or undocumented finding')
    if set(roles) != ROLES or len(roles) != len(ROLES):
        errors.append('All four distinct review roles are required')
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('packet', type=Path)
    parser.add_argument('--snapshot', required=True)
    args = parser.parse_args()
    try:
        packet = json.loads(args.packet.read_text(encoding='utf-8'))
    except (ValueError, OSError):
        packet = None
    errors = review_errors(packet, args.snapshot)
    print(json.dumps({'errors': errors, 'record_contract_passed': not errors,
                      'identity_authenticated': False,
                      'scope': 'Attestation schema only; cannot certify reviewer independence or clinical validity'}, indent=2))
    return int(bool(errors))


if __name__ == '__main__':
    raise SystemExit(main())
