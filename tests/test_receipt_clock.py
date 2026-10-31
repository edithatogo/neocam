"""Freeze the clock so receipt timestamps are asserted exactly, not merely present.

The assurance receipt is the only place this repository reads wall-clock time
(``datetime.now(UTC)`` in ``quality.cli``); ``quality.assurance`` durations use
``time.monotonic`` and review dates are parsed from ISO strings, neither of which
depend on the current instant. Before this test the stamps could only be checked
for shape, never for value.
"""

from __future__ import annotations

import json
import sys
from typing import TYPE_CHECKING, cast

import time_machine

from quality import cli
from quality.assurance import Gate

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

FROZEN = "2026-03-01T00:00:00+00:00"


def test_receipt_timestamps_are_the_frozen_utc_instant(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """A travel target makes generated_at and updated_at exact, timezone-aware stamps."""
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["cli", "--profile", "quick"])

    def gates(_profile: str) -> list[Gate]:
        return [Gate("probe", (sys.executable, "-c", "pass"))]

    monkeypatch.setattr(cli, "gates_for_profile", gates)
    with time_machine.travel(FROZEN, tick=False):
        assert cli.main() == 0
    report = cast("dict[str, object]", json.loads((tmp_path / "verification/v7/quick/receipt.json").read_text()))
    assert report["generated_at"] == FROZEN
    assert report["updated_at"] == FROZEN
    assert report["complete_within_profile"] is True
