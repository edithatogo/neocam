"""Measure duplicate-work removal on the same suite; optional plugins are explicit."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import statistics
import subprocess  # ruff: ignore[suspicious-subprocess-import] -- benchmark times fixed local pytest commands
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, TypedDict, cast

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
# A benchmark needs at least a pair of timed samples to compare variants.
MIN_REPEATS = 2


class _Sample(TypedDict):
    """One timed sample, as recorded in the benchmark report."""

    variant: str
    duration_seconds: float
    returncode: int
    passed: int


class _BenchmarkSummary(TypedDict):
    """The compared median timings and derived speedup for one benchmark."""

    median_seconds: dict[str, float]
    speedup: float
    reduction_fraction: float
    tests_per_run: int
    scope: str


class _BenchmarkArgs(Protocol):
    """The parsed CLI attributes for the benchmark runner."""

    repeats: int


def summarise(rows: Sequence[Mapping[str, object]]) -> _BenchmarkSummary:
    """Reject failed/non-equivalent samples instead of cherry-picking timings.

    Returns:
        _BenchmarkSummary: Median durations per variant, speedup and reduction fraction.

    Raises:
        ValueError: If any sample failed, variants disagree on pass counts, or
            either the baseline or the new implementation is missing.
    """
    samples = [cast("_Sample", cast("object", row)) for row in rows]
    if not samples or any(sample["returncode"] != 0 for sample in samples):
        msg = "All timed samples must pass"
        raise ValueError(msg)
    if len({sample["passed"] for sample in samples}) != 1:
        msg = "Benchmarked suites are not equivalent"
        raise ValueError(msg)
    names = {sample["variant"] for sample in samples}
    groups = {name: [sample["duration_seconds"] for sample in samples if sample["variant"] == name] for name in names}
    if not {"old", "new"} <= groups.keys():
        msg = "Both baseline and new implementation are required"
        raise ValueError(msg)
    med = {name: statistics.median(values) for name, values in groups.items()}
    return {
        "median_seconds": med,
        "speedup": med["old"] / med["new"],
        "reduction_fraction": 1 - med["new"] / med["old"],
        "tests_per_run": samples[0]["passed"],
        "scope": "Same available host; no claim about full online CI",
    }


def timed(commands: list[tuple[str, ...]], log: Path) -> dict[str, object]:
    """Time serial commands and require matching positive passed-test counts.

    Returns:
        dict[str, object]: Duration, exit code, final passed count and repo-relative log path.

    Raises:
        ValueError: If no benchmark command was supplied.
    """
    if not commands:
        msg = "At least one benchmark command is required"
        raise ValueError(msg)
    log = log if log.is_absolute() else ROOT / log
    log.parent.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    counts: list[int] = []
    exitcode = 0
    with log.open("w", encoding="utf-8") as stream:
        for command in commands:
            _ = stream.write("COMMAND: " + repr(command) + "\n")
            stream.flush()
            offset = stream.tell()
            try:
                result = subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true] -- commands are fixed local test invocations
                    command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, text=True, check=False, timeout=180
                )
                code = result.returncode
            except subprocess.TimeoutExpired:
                _ = stream.write("\nBENCHMARK TIMEOUT; this is not a timing sample\n")
                code = 124
            stream.flush()
            with log.open(encoding="utf-8") as readback:
                _ = readback.seek(offset)
                output = readback.read()
            found = re.search(r"(\d+) passed", output)
            counts.append(int(found.group(1)) if found else 0)
            if code or not found:
                exitcode = code or 1
                break
    if len(set(counts)) != 1:
        exitcode = 1
    return {
        "duration_seconds": time.perf_counter() - start,
        "returncode": exitcode,
        "passed": counts[-1],
        "log": str(log.relative_to(ROOT)),
    }


def main() -> int:
    """Run alternating baseline/new samples, write a report and return success.

    Returns:
        int: 0 once the report has been written.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument("--repeats", type=int, default=3)
    args = cast("_BenchmarkArgs", cast("object", parser.parse_args()))
    if args.repeats < MIN_REPEATS:
        parser.error("At least two repetitions are required")
    out = ROOT / "verification/v4/benchmarks"
    out.mkdir(parents=True, exist_ok=True)
    plain = (sys.executable, "-m", "pytest", "-q")
    covered = (sys.executable, "-m", "coverage", "run", "-m", "pytest", "-q")
    samples: list[dict[str, object]] = []
    # Alternate order to reduce systematic warm-up/order bias.
    for i in range(args.repeats):
        variants = ("old", "new") if i % 2 == 0 else ("new", "old")
        for variant in variants:
            result = timed([plain, covered] if variant == "old" else [covered], out / f"{variant}_{i}.txt")
            samples.append({"variant": variant, "repeat": i, **result})
            print(variant, i, round(cast("float", result["duration_seconds"]), 3), result["returncode"], flush=True)  # ruff: ignore[print] -- live benchmark progress goes to stdout
    optional: dict[str, str] = {}
    for package in ("xdist", "testmon"):
        optional[package] = (
            "available; not yet benchmark-qualified"
            if importlib.util.find_spec(package)
            else "blocked: package unavailable"
        )
    report: dict[str, object] = {
        "samples": samples,
        "optional": optional,
        "summary": summarise(samples),
        "python": sys.version,
    }
    _ = (out / "results.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["summary"], indent=2))  # ruff: ignore[print] -- benchmark summary is this CLI's stdout output
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
