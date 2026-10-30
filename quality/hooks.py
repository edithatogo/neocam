# Copyright (c) 2026 Panda Vision contributors
"""Thin changed-file hook commands; tool configuration remains in canonical files."""

from __future__ import annotations

import argparse
import subprocess  # ruff: ignore[suspicious-subprocess-import] -- hooks deliberately delegate to pinned native tools
import sys
from pathlib import Path

from quality.cli import _native


def hook_commands(kind: str, files: list[str]) -> list[tuple[str, ...]]:
    """Allow only repository-relative filenames and a fixed set of hook commands.

    Returns:
        list[tuple[str, ...]]: One fixed, argument-injected command tuple per check.

    Raises:
        ValueError: A filename leaves the repository or the hook kind is unknown.
    """
    if any(Path(p).is_absolute() or ".." in Path(p).parts for p in files):
        msg = "Hook filenames must remain inside the repository"
        raise ValueError(msg)
    if kind == "python":
        return (
            [
                (sys.executable, "-m", "ruff", "check", "--", *files),
                (sys.executable, "-m", "ruff", "format", "--check", "--", *files),
            ]
            if files
            else []
        )
    if kind == "prose":
        return [(_native("vale"), "--minAlertLevel=warning", "--", *files)] if files else []
    if kind == "workflow":
        return (
            [
                (_native("actionlint"), "-color", "--", *files),
                (_native("zizmor"), "--offline", "--persona=pedantic", "--", *files),
            ]
            if files
            else []
        )
    if kind == "secrets":
        return [(_native("gitleaks"), "git", "--staged", "--redact=100", ".")]
    if kind == "secrets-history":
        return [(_native("gitleaks"), "git", "--no-banner", "--redact=100", "--log-opts=--all", ".")]
    msg = "Unknown hook kind"
    raise ValueError(msg)


def main() -> int:
    """Run the fixed hook commands for one requested kind and pass through exit codes.

    Returns:
        int: The last failing command's exit code, or 0 when all commands passed.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=("python", "prose", "workflow", "secrets", "secrets-history"))
    parser.add_argument("files", nargs="*")
    args = parser.parse_args()
    for command in hook_commands(args.kind, args.files):
        try:
            result = subprocess.run(command, check=False)  # ruff: ignore[subprocess-without-shell-equals-true] -- command tuples are fixed here
        except FileNotFoundError as error:
            print(f"BLOCKED: {error.filename} is not installed", file=sys.stderr)  # ruff: ignore[print] -- hook output must reach stderr directly
            return 69
        if result.returncode:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
