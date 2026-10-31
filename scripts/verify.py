# ruff: ignore[implicit-namespace-package] -- standalone compatibility entrypoint, not a package module
"""Compatibility entrypoint; the authoritative executable harness is quality.cli.

The legacy status predicate is retained for regression tests only. It cannot
validate fingerprints or logs and is not a release-authorisation interface.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from quality.cli import gates_for_profile, main  # ruff: ignore[module-import-not-at-top-of-file] -- import requires ROOT on sys.path

RELEASE_GATES = frozenset({gate.name for gate in gates_for_profile("full")} | {"hosted_GitHub_Actions"})


def release_assurance_complete(gates: Sequence[Mapping[str, object]], scope: str) -> bool:
    """Check legacy status completeness only; full acceptance also validates logs.

    Returns:
        True when every recorded gate is present and passed for the release scope.
    """
    statuses = {gate["gate"]: gate["status"] for gate in gates}
    return (
        scope == "release"
        and len(statuses) == len(gates)
        and RELEASE_GATES.issubset(statuses)
        and all(gate["status"] == "passed" for gate in gates)
    )


if __name__ == "__main__":
    raise SystemExit(main())
