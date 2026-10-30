"""Report benchmark measurements without passing missing or failing runs."""

import subprocess  # ruff: ignore[suspicious-subprocess-import] -- the benchmark harness invokes fixed local argv
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict, cast

import pytest

from quality import benchmark

if TYPE_CHECKING:
    import io
    from collections.abc import Callable


class Summary(TypedDict):
    """Benchmark summary returned by the published helper."""

    median_seconds: dict[str, float]
    speedup: float


# The published helpers declare bare dicts; restate the asserted shapes.
summarise = cast("Callable[..., Summary]", benchmark.summarise)
timed = cast("Callable[..., dict[str, object]]", benchmark.timed)


def test_only_successful_equivalent_samples_can_be_compared() -> None:
    rows = [
        {"variant": "old", "duration_seconds": 4, "returncode": 0, "passed": 10},
        {"variant": "old", "duration_seconds": 6, "returncode": 0, "passed": 10},
        {"variant": "new", "duration_seconds": 2, "returncode": 0, "passed": 10},
        {"variant": "new", "duration_seconds": 3, "returncode": 0, "passed": 10},
    ]
    out = summarise(rows)
    assert out["median_seconds"]["old"] == 5
    assert out["median_seconds"]["new"] == pytest.approx(2.5)
    assert out["speedup"] == 2


def test_failing_samples_are_not_silently_dropped() -> None:
    with pytest.raises(ValueError, match="All timed samples must pass"):
        _ = summarise([{"variant": "old", "duration_seconds": 4, "returncode": 1, "passed": 10}])


def test_different_test_counts_rejected() -> None:
    rows = [
        {"variant": "old", "duration_seconds": 4, "returncode": 0, "passed": 10},
        {"variant": "new", "duration_seconds": 2, "returncode": 0, "passed": 9},
    ]
    with pytest.raises(ValueError, match="Benchmarked suites are not equivalent"):
        _ = summarise(rows)


def test_benchmark_streams_logs_and_accepts_relative_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    m = benchmark
    monkeypatch.setattr(m, "ROOT", tmp_path)

    class Completed:
        returncode: int = 0

    def run(_command: list[str], **kwargs: object) -> Completed:
        assert not kwargs.get("capture_output")
        stdout = cast("io.TextIOBase", kwargs["stdout"])
        _ = stdout.write("10 passed in 0.1s\n")
        stdout.flush()
        return Completed()

    monkeypatch.setattr(subprocess, "run", run)
    row = timed([("pytest",)], Path("result.txt"))
    assert row["returncode"] == 0
    assert row["passed"] == 10
    assert (tmp_path / "result.txt").exists()


def test_benchmark_empty_command_list_is_invalid(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="At least one benchmark command is required"):
        _ = timed([], tmp_path / "result.txt")
