"""Guard local incremental feedback; it never supplies acceptance evidence."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import platform
import subprocess  # ruff: ignore[suspicious-subprocess-import] -- runs the guarded local feedback plan
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol, cast

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {
    ".git",
    ".venv",
    ".tools",
    "outputs",
    "verification",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".hypothesis",
    ".gremlins_cache",
    ".feedback-cache",
    "coverage",
    "htmlcov",
    "extensions",
    ".uv-cache",
}


@dataclass(frozen=True)
class FeedbackPlan:
    """An explicitly local execution plan, with its cache-invalidating context."""

    mode: str
    command: tuple[str, ...]
    key: str
    cache_reused: bool
    reason: str
    can_seal: bool


class _FeedbackArgs(Protocol):
    """The parsed CLI attributes for the local feedback runner."""

    mode: str


def environment_versions() -> dict[str, str]:
    """Include interpreter, OS and the actual installed distribution versions.

    Returns:
        dict[str, str]: Installed distribution versions keyed by name, plus
            ``__python__`` and ``__platform__`` entries.
    """
    versions: dict[str, str] = {}
    for dist in importlib.metadata.distributions():
        name = dist.metadata.get("Name")
        if name is not None and name:
            versions[name] = dist.version
    versions["__python__"] = sys.version
    versions["__platform__"] = platform.platform()
    return versions


def cache_key(root: Path, mode: str, environment: dict[str, str]) -> str:
    """Testmon owns source-code dependencies; we own static/config dependencies.

    Mutation caching is more conservative: all source files enter the key. File
    deletion changes the path inventory. Output, receipt and cache files do not.

    Returns:
        str: The hex cache key over environment, mode and inventory bytes.

    Raises:
        ValueError: If the feedback mode is not `tests` or `mutation`.
    """
    if mode not in {"tests", "mutation"}:
        msg = "Unknown local feedback mode"
        raise ValueError(msg)
    digest = hashlib.sha256(json.dumps(environment, sort_keys=True).encode())
    digest.update(mode.encode())
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if set(rel.parts) & EXCLUDED or not path.is_file():
            continue
        if rel.name.startswith((".testmondata", ".coverage")) or path.suffix == ".pyc":
            continue
        if mode == "tests" and rel.parts[0] == "src" and path.suffix == ".py":
            # Source edits are tracked by testmon; additions/deletions still change inventory.
            digest.update(rel.as_posix().encode() + b"\0")
            continue
        digest.update(rel.as_posix().encode() + b"\0" + path.read_bytes() + b"\0")
    return digest.hexdigest()


def prepare(root: Path, mode: str, *, available: bool, environment: dict[str, str]) -> FeedbackPlan:
    """Invalidate unknown/stale local state before an optional plugin is run.

    Returns:
        FeedbackPlan: The guarded local command, cache key and seal decision.

    Raises:
        ModuleNotFoundError: If mutation feedback is requested without gremlins.
    """
    key = cache_key(root, mode, environment)
    state_file = root / ".feedback-cache" / f"{mode}.json"
    try:
        previous: object = cast("object", json.loads(state_file.read_text(encoding="utf-8")))
    except OSError, ValueError:
        previous = {}
    state = cast("dict[str, object]", previous) if isinstance(previous, dict) else {}
    reused = state.get("key") == key and state.get("returncode") == 0
    # Consume the old seal before starting: interruption must not preserve success.
    state_file.unlink(missing_ok=True)
    if mode == "tests":
        if not available:
            return FeedbackPlan(
                mode,
                (sys.executable, "-m", "pytest", "-q"),
                key,
                cache_reused=False,
                reason="testmon unavailable: run full ordinary suite; local feedback only",
                can_seal=False,
            )
        if not reused:
            for name in (".testmondata", ".testmondata-wal", ".testmondata-shm"):
                (root / name).unlink(missing_ok=True)
        command = (sys.executable, "-m", "pytest", "-p", "testmon.pytest_testmon", "-q", "--testmon")
    else:
        if not available:
            msg = "pytest-gremlins unavailable; mutation feedback is blocked"
            raise ModuleNotFoundError(msg)
        command = (
            sys.executable,
            "-m",
            "pytest",
            "-p",
            "gremlins",
            "tests",
            "quality/hypothesis_properties.py",
            "--gremlins",
            "--gremlin-workers=2",
            "--gremlin-cache",
            "--gremlin-report=json",
            "--strict-pardons",
        )
        if not reused:
            command += ("--gremlin-clear-cache",)
    return FeedbackPlan(
        mode,
        command,
        key,
        cache_reused=reused,
        reason="Valid local cache reused" if reused else "Cold cache or changed inputs: rebuild local evidence",
        can_seal=True,
    )


def complete(root: Path, plan: FeedbackPlan, returncode: int) -> None:
    """Seal only a real successful run; failure invalidates the old seal."""
    state_file = root / ".feedback-cache" / f"{plan.mode}.json"
    state_file.unlink(missing_ok=True)
    if returncode == 0 and plan.can_seal:
        state_file.parent.mkdir(parents=True, exist_ok=True)
        _ = state_file.write_text(
            json.dumps({"key": plan.key, "returncode": 0, "scope": "local-only; not acceptance"}) + "\n",
            encoding="utf-8",
        )


def main() -> int:
    """Execute guarded feedback; do not upgrade local results to full assurance.

    Returns:
        int: The guarded command's exit code, or 69 when a plugin is unavailable.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument("--mode", choices=("tests", "mutation"), default="tests")
    args = cast("_FeedbackArgs", cast("object", parser.parse_args()))
    module = "testmon" if args.mode == "tests" else "pytest_gremlins"
    env = environment_versions()
    try:
        plan = prepare(ROOT, args.mode, available=importlib.util.find_spec(module) is not None, environment=env)
    except ModuleNotFoundError as error:
        print(f"BLOCKED: {error}")  # ruff: ignore[print] -- CLI blocked notice goes to stdout
        return 69
    print(json.dumps(asdict(plan), indent=2), flush=True)  # ruff: ignore[print] -- CLI plan report goes to stdout
    result = subprocess.run(plan.command, cwd=ROOT, check=False)  # ruff: ignore[subprocess-without-shell-equals-true] -- fixed plan command, no shell
    # A file/environment change during the run invalidates the seal too.
    stable = cache_key(ROOT, args.mode, environment_versions()) == plan.key
    complete(ROOT, plan, result.returncode if stable else 1)
    return result.returncode if stable else 1


if __name__ == "__main__":
    raise SystemExit(main())
