"""Compatibility entrypoint; the authoritative executable harness is quality.cli.

The legacy status predicate is retained for regression tests only. It cannot
validate fingerprints or logs and is not a release-authorisation interface.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from quality.cli import gates_for_profile, main

RELEASE_GATES = frozenset({gate.name for gate in gates_for_profile('full')} | {'hosted_GitHub_Actions'})


def release_assurance_complete(gates: list[dict], scope: str) -> bool:
    """Check legacy status completeness only; full acceptance also validates logs."""
    statuses = {gate['gate']: gate['status'] for gate in gates}
    return (scope == 'release' and len(statuses) == len(gates)
            and RELEASE_GATES.issubset(statuses)
            and all(gate['status'] == 'passed' for gate in gates))


if __name__ == '__main__':
    raise SystemExit(main())
