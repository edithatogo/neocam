"""Individual verification commands shared by the local and hosted harness."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import math
import re
import subprocess  # ruff: ignore[suspicious-subprocess-import] -- checks probe pinned native tools
import sys
import tomllib
from pathlib import Path
from typing import Protocol, cast

from quality.contracts import audit_inputs, forbidden_packages, validate_lock

ROOT = Path(__file__).resolve().parents[1]
# Mutation score floor for the documented Gremlins summary.
MIN_MUTATION_SCORE = 90
# Context entrypoints must stay small so agents read the runbook, not a monolith.
MAX_ENTRYPOINT_BYTES = 6000


class _CheckArgs(Protocol):
    """The parsed CLI attributes for the named-check dispatcher."""

    check: str
    evidence_version: str


def _string_list(value: object) -> list[str]:
    """Return the value as a list of nonblank strings, or an empty list.

    Returns:
        list[str]: The validated string list, otherwise empty.
    """
    if not isinstance(value, list):
        return []
    items = cast("list[object]", value)
    return [item for item in items if isinstance(item, str) and item]


def _nonnegative_int(value: object) -> bool:
    """Return whether a value is a genuine non-negative integer.

    Returns:
        bool: True when the value is an ``int`` and not negative.
    """
    return type(value) is int and value >= 0


def mutation_errors(data: object) -> list[str]:
    """Check the documented Gremlins summary; do not credit timeouts as kills.

    Returns:
        list[str]: Mutation-report errors; empty when the summary reconciles.
    """
    if not isinstance(data, dict):
        return ["Missing mutation summary"]
    summary = cast("dict[str, object]", data).get("summary")
    if not isinstance(summary, dict):
        return ["Missing mutation summary"]
    counts = ("total", "zapped", "survived", "timeout", "error", "pardoned")
    fields = cast("dict[str, object]", summary)
    if any(not _nonnegative_int(fields.get(key)) for key in counts):
        return ["Invalid mutation counts"]
    values = {key: cast("int", fields[key]) for key in counts}
    total = values["total"]
    if total == 0:
        return ["No mutants exercised"]
    errors: list[str] = []
    if sum(values[key] for key in counts[1:]) != total:
        errors.append("Mutation counts do not reconcile")
    if values["timeout"] or values["error"] or values["pardoned"]:
        errors.append("Mutation timeouts/errors/pardons require investigation")
    score = 100 * values["zapped"] / total
    supplied = fields.get("percentage")
    if (
        not isinstance(supplied, (int, float))
        or not math.isfinite(supplied)
        or not math.isclose(supplied, score, abs_tol=0.02)
    ):
        errors.append("Reported mutation percentage does not match counts")
    if score < MIN_MUTATION_SCORE:
        errors.append(f"Mutation score below {MIN_MUTATION_SCORE}%: {score:.2f}%")
    return errors


def workflow_errors(root: Path) -> list[str]:
    """Reject mutable action pins and CI bypasses in workflow files.

    Returns:
        list[str]: Unsafe-workflow errors; empty when every workflow is pinned.
    """
    errors: list[str] = []
    for workflow in (root / ".github/workflows").glob("*.yml"):
        text = workflow.read_text(encoding="utf-8")
        errors.extend(
            f"Mutable action reference: {workflow.name}: {pin}"
            for pin in cast("list[str]", re.findall(r"uses:\s*([^\s]+)", text))
            if not pin.startswith("./") and not re.fullmatch(r"[^@]+@[a-f0-9]{40}", pin)
        )
        if "pull_request_target" in text or "continue-on-error: true" in text:
            errors.append(f"Unsafe CI bypass in {workflow.name}")
    return errors


def context_errors(root: Path) -> list[str]:
    """Check authoritative context is small, reachable and consistent with tracks.

    Returns:
        list[str]: Context errors; empty when the documentation hub is consistent.
    """
    errors: list[str] = []
    for name in ("AGENTS.md", "GEMINI.md"):
        path = root / name
        if not path.exists() or "conductor/runbook.md" not in path.read_text(encoding="utf-8"):
            errors.append(f"Missing context entrypoint: {name}")
        elif path.stat().st_size > MAX_ENTRYPOINT_BYTES:
            errors.append(f"Entrypoint exceeds 6 KB budget: {name}")
    state = cast("dict[str, object]", json.loads((root / "conductor/current-state.json").read_text(encoding="utf-8")))
    if state.get("release_ready") is not False:
        errors.append("Working draft must not assert release readiness")
    errors.extend(
        f"Missing track artifact: {track}/{name}"
        for track in _string_list(state.get("active_tracks", []))
        for name in ("spec.md", "plan.md", "metadata.json")
        if not (root / "conductor/tracks" / track / name).is_file()
    )
    errors.extend(
        f"Missing context: {name}"
        for name in ("conductor/runbook.md", "conductor/tracks.md", "conductor/decisions-v3.md")
        if not (root / name).is_file()
    )
    errors.extend(workflow_errors(root))
    return errors


def version_errors(root: Path) -> list[str]:
    """Require an isolated environment and all declared direct assurance pins.

    Returns:
        list[str]: Environment and pin errors; empty when all pins are satisfied.
    """
    cfg = cast("dict[str, object]", tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8")))
    project = cast("dict[str, object]", cfg["project"])
    declarations = list(cast("list[str]", project["dependencies"]))
    for group in cast("dict[str, list[str]]", project["optional-dependencies"]).values():
        declarations += group
    groups = cast("dict[str, object]", cfg["dependency-groups"])
    declarations += cast("list[str]", groups["test"])
    declarations += [value for value in cast("list[object]", groups["assurance"]) if isinstance(value, str)]
    project_environment = Path(sys.prefix).resolve() == (root / ".venv").resolve()
    errors = (
        [] if project_environment else ["The project .venv is required; the shared host environment is not certified"]
    )
    for declaration in sorted(set(declarations)):
        name, expected = declaration.split("==", maxsplit=1)
        try:
            installed = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            errors.append(f"Missing {declaration}")
        else:
            if installed != expected:
                errors.append(f"{name}: installed {installed}; required {expected}")
    if project_environment:
        names = [dist.metadata["Name"] for dist in importlib.metadata.distributions() if dist.metadata["Name"]]
        errors.extend(f"Prohibited installed dependency: {name}" for name in forbidden_packages(names))
    return errors


def native_version_errors(root: Path) -> list[str]:
    """Require pinned native releases; PATH tools cannot silently override them.

    Returns:
        list[str]: Native-version errors; empty when every pinned release verifies.
    """
    manifest = cast("dict[str, object]", json.loads((root / "quality/native-tools.json").read_text(encoding="utf-8")))
    errors: list[str] = []
    for name, entries in manifest.items():
        record = cast("dict[str, object]", entries) if isinstance(entries, dict) else {}
        local = root / ".tools/bin" / name
        executable = str(local) if local.is_file() else name
        flag = "version" if name == "gitleaks" else "-version" if name == "actionlint" else "--version"
        try:
            result = subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true] -- fixed executable and flag, no shell
                [executable, flag], cwd=root, capture_output=True, text=True, timeout=10, check=False
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            errors.append(f"{name}: unavailable: {error}")
            continue
        version = cast("str", record["version"])
        pattern = rf"(?<![\d.]){re.escape(version)}(?![\d.])"
        if result.returncode or not re.search(pattern, result.stdout + result.stderr):
            errors.append(f"{name}: expected {version}; version command did not verify it")
    return errors


def main() -> int:  # ruff: ignore[complex-structure, too-many-return-statements, too-many-branches] -- explicit per-check dispatch keeps each exit-code contract visible
    """Run a named check; EX_UNAVAILABLE explicitly distinguishes prerequisites.

    Returns:
        int: 0 when the named check passes, 1 on failure, 69 when unavailable.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument(
        "check",
        choices=("inputs", "context", "lock", "versions", "submodule", "mutation", "scalene_output", "native_versions"),
    )
    _ = parser.add_argument("--evidence-version", default="v7")
    args = cast("_CheckArgs", cast("object", parser.parse_args()))
    if not re.fullmatch(r"v[1-9][0-9]*", args.evidence_version):
        parser.error("Invalid evidence version")
    if args.check == "inputs":
        report = audit_inputs(ROOT)
        print(json.dumps(report, indent=2))  # ruff: ignore[print] -- CLI check report goes to stdout
        return int(bool(report["errors"]))
    errors: list[str]
    if args.check == "context":
        errors = context_errors(ROOT)
    elif args.check == "lock":
        errors = validate_lock(ROOT / "uv.lock")
        if not (ROOT / "uv.lock").exists():
            print("\n".join(errors))  # ruff: ignore[print] -- CLI check report goes to stdout
            return 69
    elif args.check == "versions":
        errors = version_errors(ROOT)
        if errors:
            print("\n".join(errors))  # ruff: ignore[print] -- CLI check report goes to stdout
            return 69
    elif args.check == "native_versions":
        errors = native_version_errors(ROOT)
        if errors:
            print("\n".join(errors))  # ruff: ignore[print] -- CLI check report goes to stdout
            return 69
    elif args.check == "submodule":
        result = subprocess.run(
            ["git", "submodule", "status"],  # ruff: ignore[start-process-with-partial-path] -- fixed git subcommand, not user input
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        print(result.stdout, result.stderr)  # ruff: ignore[print] -- CLI check report goes to stdout
        if result.returncode or not (ROOT / "extensions/conductor/README.md").exists():
            print("Conductor checkout unavailable; a gitlink alone is not a checkout")  # ruff: ignore[print] -- CLI check report goes to stdout
            return 69
        errors = (
            []
            if result.stdout.strip() and not result.stdout.startswith(("-", "+", "U"))
            else ["Submodule differs from pinned revision"]
        )
    elif args.check == "mutation":
        path = ROOT / "coverage/gremlins/gremlins.json"
        if not path.exists():
            print("No fresh Gremlins report; execution gate must pass first")  # ruff: ignore[print] -- CLI check report goes to stdout
            return 69
        errors = mutation_errors(cast("object", json.loads(path.read_text(encoding="utf-8"))))
    else:
        path = ROOT / "verification" / args.evidence_version / "scalene.json"
        if not path.exists():
            print("No Scalene profile was produced")  # ruff: ignore[print] -- CLI check report goes to stdout
            return 69
        data: object = cast("object", json.loads(path.read_text(encoding="utf-8")))
        if isinstance(data, dict) and cast("dict[str, object]", data).get("files"):
            errors = []
        else:
            errors = ["Scalene profile contains no files"]
    print(json.dumps({"check": args.check, "errors": errors}, indent=2))  # ruff: ignore[print] -- CLI check report goes to stdout
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
