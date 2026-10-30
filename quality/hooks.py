"""Thin changed-file hook commands; tool configuration remains in canonical files."""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

from quality.cli import _native


def hook_commands(kind: str, files: list[str]) -> list[tuple[str, ...]]:
    """Allow only repository-relative filenames and a fixed set of hook commands."""
    if any(Path(p).is_absolute() or '..' in Path(p).parts for p in files):
        raise ValueError('Hook filenames must remain inside the repository')
    if kind == 'python':
        return [(sys.executable, '-m', 'ruff', 'check', '--', *files),
                (sys.executable, '-m', 'ruff', 'format', '--check', '--', *files)] if files else []
    if kind == 'prose':
        return [(_native('vale'), '--minAlertLevel=warning', '--', *files)] if files else []
    if kind == 'workflow':
        return [(_native('actionlint'), '-color', '--', *files),
                (_native('zizmor'), '--offline', '--persona=pedantic', '--', *files)] if files else []
    if kind == 'secrets':
        return [(_native('gitleaks'), 'git', '--staged', '--redact=100', '.')]
    raise ValueError('Unknown hook kind')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kind', choices=('python','prose','workflow','secrets'))
    parser.add_argument('files', nargs='*')
    args = parser.parse_args()
    for command in hook_commands(args.kind,args.files):
        try:
            result = subprocess.run(command,check=False)
        except FileNotFoundError as error:
            print(f'BLOCKED: {error.filename} is not installed',file=sys.stderr)
            return 69
        if result.returncode:
            return result.returncode
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
