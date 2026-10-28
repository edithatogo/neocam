"""Portable evidence-consistency check; no external packages or hosted-CI claim."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


def audit(report: dict, root: Path, required: set[str], fingerprint: str) -> list[str]:
    """Require independently supplied scope and fingerprints, not self-reported green."""
    errors = []
    if not required or any(not isinstance(name, str) or not name.strip() for name in required):
        errors.append('An independent non-empty required gate set is mandatory')
    if not isinstance(fingerprint, str) or not fingerprint.strip():
        errors.append('An independently supplied non-empty fingerprint is mandatory')
    if 'input_fingerprint' in report and report['input_fingerprint'] != fingerprint:
        errors.append('Top-level fingerprint conflicts with expected state')
    if report.get('profile') != 'full' or report.get('full_local_assurance') is not True:
        errors.append('Not a complete full-local receipt')
    if report.get('cache_reused'):
        errors.append('Incremental evidence cannot certify fresh acceptance')
    receipts = report.get('receipts', [])
    names = [item.get('gate') for item in receipts]
    if len(names) != len(set(names)):
        errors.append('Duplicate gate receipts')
    if required - set(names):
        errors.append('Required gates missing')
    for item in receipts:
        name = item.get('gate', '<missing>')
        if item.get('status') != 'passed' or item.get('returncode') != 0:
            errors.append(f'Not passed: {name}')
        if item.get('fingerprint') != fingerprint:
            errors.append(f'Stale fingerprint: {name}')
        duration = item.get('duration_seconds')
        if type(duration) not in (int,float) or not math.isfinite(duration) or duration < 0:
            errors.append(f'Invalid duration: {name}')
        path = (root / str(item.get('log',''))).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file():
            errors.append(f'Invalid log path: {name}')
        elif hashlib.sha256(path.read_bytes()).hexdigest() != item.get('log_sha256'):
            errors.append(f'Log digest mismatch: {name}')
    return errors


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('receipt',type=Path)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--required',required=True)
    parser.add_argument('--fingerprint',required=True)
    args=parser.parse_args()
    report=json.loads(args.receipt.read_text(encoding='utf-8'))
    errors=audit(report,args.root,set(args.required.split(',')),args.fingerprint)
    print(json.dumps({'errors':errors,'hosted_ci_verified':False},indent=2))
    return int(bool(errors))


if __name__ == '__main__':
    raise SystemExit(main())
