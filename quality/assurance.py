"""Run checks without a shell and bind their evidence to the inspected inputs.

This module is intentionally standard-library-only. A missing development tool
is a blocker; a failing program or timed-out check is a failure, not a waiver.
"""

from __future__ import annotations

import hashlib
import importlib.util
import math
import re
import subprocess  # ruff: ignore[suspicious-subprocess-import] -- gates deliberately run pinned native tools without a shell
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

# EX_UNAVAILABLE is used only by our explicit preflight check scripts.
EX_UNAVAILABLE = 69

INPUT_DIRS = (
    "src",
    "scripts",
    "quality",
    "tests",
    "data",
    "config",
    "evidence",
    "sources",
    "conductor",
    ".github",
    ".vale",
    ".agents",
)
INPUT_FILES = (
    ".gitmodules",
    "pyproject.toml",
    "uv.lock",
    ".vale.ini",
    ".gitleaks.toml",
    "AGENTS.md",
    "GEMINI.md",
    "README.md",
    ".pre-commit-config.yaml",
    "renovate.json",
)


@dataclass(frozen=True)
class Gate:
    """One executable check, with an optional explicit Python-tool prerequisite."""

    name: str
    command: tuple[str, ...]
    timeout: float = 60
    module: str | None = None
    allow_unavailable: bool = False

    def __post_init__(self) -> None:
        """Reject unsafe log names and invalid command/timeout definitions.

        Raises:
            ValueError: If the gate name, command or timeout is invalid.
        """
        if not re.fullmatch(r"[a-z][a-z0-9_]*", self.name):
            msg = "Gate name must be a lowercase identifier"
            raise ValueError(msg)
        if not self.command or not all(isinstance(part, str) and part for part in self.command):
            msg = "Command must contain nonempty string arguments"
            raise ValueError(msg)
        if not math.isfinite(self.timeout) or self.timeout <= 0:
            msg = "Gate timeout must be positive and finite"
            raise ValueError(msg)


@dataclass(frozen=True)
class Receipt:
    """A check result; the log digest is an integrity check, not a signature."""

    gate: str
    status: str
    returncode: int | None
    fingerprint: str
    command: tuple[str, ...]
    duration_seconds: float
    log: str
    log_sha256: str
    reason: str = ""


def execute_gate(gate: Gate, root: Path) -> tuple[int, str]:
    """Run one gate command without a shell and capture its combined output.

    Returns:
        tuple[int, str]: The exit code and the combined standard output and error.
    """
    result = subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true] -- fixed tuple commands, shell explicitly disabled
        gate.command,
        cwd=root,
        capture_output=True,
        text=True,
        timeout=gate.timeout,
        check=False,
        shell=False,
        encoding="utf-8",
        errors="replace",
    )
    return result.returncode, result.stdout + result.stderr


def run_gate(gate: Gate, root: Path, fingerprint: str, log_dir: Path) -> Receipt:
    """Execute one check and retain evidence even when it fails or is unavailable.

    Returns:
        Receipt: The recorded status, output digest and command evidence.

    Raises:
        ValueError: If the log directory escapes the project root.
    """
    root = root.resolve()
    log_dir = log_dir.resolve()
    if not log_dir.is_relative_to(root):
        msg = "Log directory must be inside the project"
        raise ValueError(msg)
    log_dir.mkdir(parents=True, exist_ok=True)
    log = log_dir / f"{gate.name}.txt"
    started = time.monotonic()
    status, reason, output = "failed", "", ""
    returncode: int | None = None
    missing = False
    if gate.module is not None:
        try:
            missing = importlib.util.find_spec(gate.module) is None
        except (ImportError, ValueError, AttributeError):
            missing = True
    if missing:
        status, reason = "blocked", f"Required Python tool is unavailable: {gate.module}"
        output = reason + "\n"
    else:
        try:
            returncode, output = execute_gate(gate, root)
        except FileNotFoundError as error:
            status, reason = "blocked", f"Executable unavailable: {error.filename}"
            output = reason + "\n"
        except OSError as error:
            status = "failed"
            reason = f"Executable launch failed: {type(error).__name__}: {error}"
            output = reason + "\n"
        except subprocess.TimeoutExpired as error:
            status, reason = "failed", f"Check timeout after {gate.timeout:g} seconds"
            fragments = (error.stdout or b"", error.stderr or b"")
            output = "".join(part.decode(errors="replace") if isinstance(part, bytes) else part for part in fragments)
            output += "\n" + reason + "\n"
        else:
            status = (
                "passed"
                if returncode == 0
                else "blocked"
                if returncode == EX_UNAVAILABLE and gate.allow_unavailable
                else "failed"
            )
            if returncode != 0:
                reason = f"Command exited {returncode}"
    log.write_text(output, encoding="utf-8")
    return Receipt(
        gate.name,
        status,
        returncode,
        fingerprint,
        gate.command,
        time.monotonic() - started,
        str(log.relative_to(root)),
        hashlib.sha256(log.read_bytes()).hexdigest(),
        reason,
    )


def receipt_errors(receipt: Receipt, root: Path, fingerprint: str) -> list[str]:
    """Return the consistency errors for one receipt against required evidence.

    Returns:
        list[str]: Errors for the receipt; empty when it is current and intact.
    """
    errors: list[str] = []
    if receipt.status != "passed" or receipt.returncode != 0:
        errors.append(f"Gate not passed: {receipt.gate}")
    if receipt.fingerprint != fingerprint:
        errors.append(f"Stale inputs: {receipt.gate}")
    if not math.isfinite(receipt.duration_seconds) or receipt.duration_seconds < 0:
        errors.append(f"Invalid duration: {receipt.gate}")
    path = (root / receipt.log).resolve()
    if not path.is_relative_to(root.resolve()):
        errors.append(f"Unsafe log path: {receipt.gate}")
    elif not path.is_file():
        errors.append(f"Missing log: {receipt.gate}")
    elif hashlib.sha256(path.read_bytes()).hexdigest() != receipt.log_sha256:
        errors.append(f"Altered log: {receipt.gate}")
    return errors


def validate_receipts(receipts: list[Receipt], required: set[str], fingerprint: str, root: Path) -> list[str]:
    """Reject incomplete, stale, conflicting, failed or altered result sets.

    Returns:
        list[str]: Validation errors; empty when the receipt set is acceptable.
    """
    names = [receipt.gate for receipt in receipts]
    errors: list[str] = []
    if not required:
        errors.append("Acceptance scope must be nonempty")
    if len(names) != len(set(names)):
        errors.append("Duplicate gate receipts")
    errors.extend(f"Unexpected gate: {name}" for name in sorted(set(names) - required))
    errors.extend(f"Missing gate: {name}" for name in sorted(required - set(names)))
    for receipt in receipts:
        errors.extend(receipt_errors(receipt, root, fingerprint))
    return errors


def input_fingerprint(root: Path) -> str:
    """Hash code, tests, inputs, dependency policy and context; exclude output logs.

    Returns:
        str: The hex SHA-256 digest over the sorted fingerprint inputs.
    """
    files = {root / name for name in INPUT_FILES if (root / name).is_file()}
    for name in INPUT_DIRS:
        directory = root / name
        if directory.is_dir():
            files.update(
                path
                for path in directory.rglob("*")
                if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
            )
    digest = hashlib.sha256()
    for path in sorted(files):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()
