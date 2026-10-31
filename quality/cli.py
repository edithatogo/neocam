"""One explicit assurance command for a solo developer and hosted CI.

Quick checks are never a substitute for full acceptance. No profile publishes a
release or assumes that a local run is a hosted GitHub Actions result.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import re
import shutil
import subprocess  # ruff: ignore[suspicious-subprocess-import] -- records the local commit for the receipt
import sys
import uuid
from dataclasses import asdict, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol, cast

from quality.artifacts import artifact_dependency_fingerprint
from quality.assurance import Gate, Receipt, input_fingerprint, run_gate, validate_receipts

ROOT = Path(__file__).resolve().parents[1]


class _CliArgs(Protocol):
    """The parsed CLI attributes for the assurance runner."""

    profile: str
    evidence_version: str


def _native(name: str) -> str:
    local = ROOT / ".tools/bin" / name
    return str(local) if local.exists() else (shutil.which(name) or str(local))


def gates_for_profile(profile: str) -> list[Gate]:
    """Declare every gate once; covered execution supplies test and coverage evidence without a second suite.

    Returns:
        list[Gate]: The ordered gates for the requested profile.

    Raises:
        ValueError: If the profile is not a known assurance profile.
    """
    python = sys.executable
    gates = [
        Gate("pytest", (python, "-m", "pytest", "-q"), 180),
        Gate("inputs", (python, "-m", "quality.checks", "inputs")),
        Gate("context", (python, "-m", "quality.checks", "context")),
    ]
    if profile == "quick":
        return gates
    if profile not in {"pr", "full"}:
        msg = "Unknown assurance profile"
        raise ValueError(msg)
    gates[0] = Gate("pytest", (python, "-m", "coverage", "run", "-m", "pytest", "-q"), 180, "coverage")
    gates.extend([
        Gate("current_release", (python, "-m", "quality.artifacts", "verify"), 60),
        Gate(
            "source_integrity",
            (python, "-m", "quality.source_archive", "--output", "verification/v7/source_archive.json"),
            60,
        ),
        Gate("coverage", (python, "-m", "coverage", "json", "-o", "verification/v7/coverage.json"), 60, "coverage"),
        Gate("coverage_threshold", (python, "-m", "coverage", "report", "--fail-under=90"), 60, "coverage"),
        Gate(
            "core_coverage",
            (
                python,
                "-m",
                "coverage",
                "report",
                "--include=src/activity.py,src/deployment.py,src/configuration.py,src/equipment.py,src/pathways_v6.py,src/perspectives_v7.py,src/portfolios_v7.py,src/audit_v7.py",
                "--fail-under=95",
            ),
            60,
            "coverage",
        ),
        Gate("ruff_lint", (python, "-m", "ruff", "check", "src", "scripts", "quality", "tests"), 180, "ruff"),
        Gate(
            "ruff_format",
            (python, "-m", "ruff", "format", "--check", "src", "scripts", "quality", "tests"),
            180,
            "ruff",
        ),
        Gate("ty", (python, "-m", "ty", "check", "--error-on-warning"), 180, "ty"),
        Gate("basedpyright", (python, "-m", "basedpyright"), 180, "basedpyright"),
        Gate("hypothesis", (python, "-m", "pytest", "quality/hypothesis_properties.py", "-q"), 180, "hypothesis"),
        Gate(
            "gremlins",
            (
                python,
                "-m",
                "pytest",
                "-p",
                "gremlins",
                "tests",
                "quality/hypothesis_properties.py",
                "--gremlins",
                # One worker: mutants are applied by rewriting the source file, so two
                # workers mutating the same file race on it. The full run measured
                # 1,240 zapped / 5 survived / 5 Error at two workers, then 1 Error after
                # an explicit basetemp removed the tmpdir race; the survivor was an
                # identity mutant (`<= to <=`) with no failing test and no killing test,
                # while the same identity mutant elsewhere was classified as survived.
                # The mutation gate requires zero errors, timeouts and pardons, and the
                # sequential run stays well inside the gate's budget.
                "--gremlin-workers=1",
                "--gremlin-clear-cache",
                "--gremlin-report=json",
                "--gremlin-report=html",
                "--strict-pardons",
                # An explicit basetemp stops pytest pruning its numbered temporary
                # directories. That pruning is what raced between the two mutation
                # workers on Python 3.15 (an unclosed-scandir ResourceWarning escalated
                # by filterwarnings=error, plus an rm_rf race), and the mutation gate
                # treats any error as a failure regardless of score: 5 of 1,250 mutants
                # reported Error with no failing test and no killing test before this.
                "--basetemp=coverage/gremlins/tmp",
            ),
            1800,
            "pytest_gremlins",
        ),
        Gate("mutation_score", (python, "-m", "quality.checks", "mutation"), allow_unavailable=True),
        Gate(
            "scalene",
            (python, "-m", "scalene", "run", "-o", "verification/v7/scalene.json", "quality/profile_workload.py"),
            180,
            "scalene",
        ),
        Gate("scalene_output", (python, "-m", "quality.checks", "scalene_output"), allow_unavailable=True),
        Gate(
            "gitleaks_history",
            (
                _native("gitleaks"),
                "git",
                "--log-opts=--all",
                "--redact=100",
                "--report-format=json",
                "--report-path=verification/v7/gitleaks-history.json",
                ".",
            ),
            180,
        ),
        Gate(
            "gitleaks_tree",
            (
                _native("gitleaks"),
                "dir",
                "--redact=100",
                "--report-format=json",
                "--report-path=verification/v7/gitleaks-tree.json",
                ".",
            ),
            180,
        ),
        Gate(
            "vale",
            (
                _native("vale"),
                "--minAlertLevel=warning",
                "README.md",
                "AGENTS.md",
                "GEMINI.md",
                "conductor/runbook.md",
                "conductor/decisions-v3.md",
            ),
            120,
        ),
        Gate(
            "privacy",
            (python, "-m", "quality.privacy", "--output", "verification/v7/privacy.json"),
            120,
        ),
        Gate("dependency_consistency", ("uv", "lock", "--check", "--offline"), 30),
        Gate("dependency_lock", (python, "-m", "quality.checks", "lock"), allow_unavailable=True),
        Gate("native_versions", (python, "-m", "quality.checks", "native_versions"), allow_unavailable=True),
        Gate("locked_versions", (python, "-m", "quality.checks", "versions"), allow_unavailable=True),
        Gate(
            "pip_audit",
            (python, "-m", "pip_audit", "--local", "--format=json", "--output=verification/v7/pip-audit.json"),
            300,
            "pip_audit",
        ),
        Gate(
            "sbom",
            (python, "-m", "pip_audit", "--local", "--format=cyclonedx-json", "--output=verification/v7/sbom.json"),
            300,
            "pip_audit",
        ),
        Gate("conductor_checkout", (python, "-m", "quality.checks", "submodule"), allow_unavailable=True),
        Gate("polars_consistency", (python, "-m", "quality.polars_probe"), 60, "polars"),
    ])
    gates.extend([
        Gate("actionlint", (_native("actionlint"), "-color"), 60),
        Gate("zizmor", (_native("zizmor"), "--offline", "--persona=pedantic", ".github/workflows"), 60),
        Gate("prek_config", (_native("prek"), "validate-config", ".pre-commit-config.yaml"), 60),
    ])
    if profile == "pr":
        deep = {"gremlins", "mutation_score", "scalene", "scalene_output", "gitleaks_history"}
        gates = [gate for gate in gates if gate.name not in deep]
    return gates


def _build_parser() -> argparse.ArgumentParser:
    """Declare the assurance runner flags once, with a typed namespace contract.

    Returns:
        argparse.ArgumentParser: The configured argument parser.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument("--profile", choices=("quick", "pr", "full"), default="quick")
    _ = parser.add_argument(
        "--evidence-version",
        default="v7",
        help="Versioned evidence directory, for example v8; older evidence is preserved.",
    )
    return parser


def main() -> int:
    """Execute all declared gates and atomically checkpoint evidence after each gate.

    Returns:
        int: 0 when every gate passed with current inputs, otherwise 1.
    """
    parser = _build_parser()
    args = cast("_CliArgs", cast("object", parser.parse_args()))
    if not re.fullmatch(r"v[1-9][0-9]*", args.evidence_version):
        parser.error("--evidence-version must be v followed by a positive integer")
    evidence_root = f"verification/{args.evidence_version}"
    directory = ROOT / evidence_root / args.profile
    directory.mkdir(parents=True, exist_ok=True)
    gates = [
        replace(g, command=tuple(s.replace("verification/v7/", evidence_root + "/") for s in g.command))
        for g in gates_for_profile(args.profile)
    ]
    gates = [
        replace(g, command=(*g.command, "--evidence-version", args.evidence_version))
        if g.name == "scalene_output"
        else g
        for g in gates
    ]
    if args.profile in {"pr", "full"}:
        for stale in ("coverage/gremlins/gremlins.json", f"{evidence_root}/scalene.json", ".coverage"):
            (ROOT / stale).unlink(missing_ok=True)
    fingerprint = input_fingerprint(ROOT)
    artifacts_before = artifact_dependency_fingerprint(ROOT)
    receipts: list[Receipt] = []
    versions: dict[str, str | None] = {}
    for name in (
        "numpy",
        "polars",
        "scipy",
        "scikit-learn",
        "pytest",
        "coverage",
        "ruff",
        "ty",
        "basedpyright",
        "hypothesis",
        "pytest-gremlins",
        "scalene",
        "pip-audit",
        "uv",
        "prek",
        "zizmor",
        "pytest-xdist",
        "pytest-testmon",
    ):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],  # ruff: ignore[start-process-with-partial-path] -- fixed git command, not user input
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=10,
        check=False,
    ).stdout.strip()
    report: dict[str, object] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "run_id": str(uuid.uuid4()),
        "profile": args.profile,
        "source_commit_at_execution": commit,
        "input_fingerprint": fingerprint,
        "artifact_dependency_fingerprint": artifacts_before,
        "run_finished": False,
        "active_gate": None,
        "complete_within_profile": False,
        "full_local_assurance": False,
        "release_ready": False,
        "hosted_assurance": "Not independently verified by this local runner",
        "environment": {
            "python": sys.version,
            "executable": sys.executable,
            "packages": versions,
            "pytest_plugin_autoload": os.environ.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD"),
            "notebook_startup_flag": os.environ.get("OAI_IS_JUPYTER_KERNEL"),
        },
        "receipts": [],
        "problems": ["Execution has not completed"],
        "review": "Author review; not an independent review",
        "evidence_reuse": "pytest and coverage derive from one covered suite in PR/full profiles",
        "required_gates": [g.name for g in gates],
    }

    def checkpoint() -> None:
        """Never leave a truncated JSON receipt after a failed/interrupted write."""
        report["updated_at"] = datetime.now(UTC).isoformat()
        report["receipts"] = [asdict(receipt) for receipt in receipts]
        temporary = directory / "receipt.json.tmp"
        _ = temporary.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        _ = temporary.replace(directory / "receipt.json")

    checkpoint()
    for gate in gates:
        report["active_gate"] = gate.name
        checkpoint()
        print(f"START   {gate.name}", flush=True)  # ruff: ignore[print] -- live CLI progress goes to stdout
        receipt = run_gate(gate, ROOT, fingerprint, directory)
        receipts.append(receipt)
        checkpoint()
        print(f"{receipt.status.upper():7} {gate.name}: {receipt.reason}", flush=True)  # ruff: ignore[print] -- live CLI progress goes to stdout
    current = input_fingerprint(ROOT)
    problems = validate_receipts(receipts, {g.name for g in gates}, current, ROOT)
    artifacts_after = artifact_dependency_fingerprint(ROOT)
    report["artifact_dependency_fingerprint_end"] = artifacts_after
    if artifacts_before != artifacts_after:
        problems.append("Generated artifacts changed during verification")
    if fingerprint != current:
        problems.append("Inputs changed during verification")
    report.update(
        run_finished=True,
        active_gate=None,
        problems=problems,
        complete_within_profile=not problems,
        full_local_assurance=args.profile == "full" and not problems,
    )
    checkpoint()
    return int(bool(problems))


if __name__ == "__main__":
    raise SystemExit(main())
