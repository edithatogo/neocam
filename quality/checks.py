"""Individual verification commands shared by the local and hosted harness."""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import tomllib

from quality.contracts import audit_inputs, forbidden_packages, validate_lock

ROOT = Path(__file__).resolve().parents[1]


def mutation_errors(data: object) -> list[str]:
    """Check the documented Gremlins summary; do not credit timeouts as kills."""
    if not isinstance(data, dict) or not isinstance(data.get('summary'), dict):
        return ['Missing mutation summary']
    summary = data['summary']
    counts = ('total', 'zapped', 'survived', 'timeout', 'error', 'pardoned')
    if any(type(summary.get(key)) is not int or summary[key] < 0 for key in counts):
        return ['Invalid mutation counts']
    total = summary['total']
    if total == 0:
        return ['No mutants exercised']
    errors: list[str] = []
    if sum(summary[key] for key in counts[1:]) != total:
        errors.append('Mutation counts do not reconcile')
    if summary['timeout'] or summary['error'] or summary['pardoned']:
        errors.append('Mutation timeouts/errors/pardons require investigation')
    score = 100 * summary['zapped'] / total
    supplied = summary.get('percentage')
    if not isinstance(supplied, (int, float)) or not math.isfinite(supplied) or not math.isclose(supplied, score, abs_tol=.02):
        errors.append('Reported mutation percentage does not match counts')
    if score < 90:
        errors.append(f'Mutation score below 90%: {score:.2f}%')
    return errors


def context_errors(root: Path) -> list[str]:
    """Check authoritative context is small, reachable and consistent with tracks."""
    errors: list[str] = []
    for name in ('AGENTS.md', 'GEMINI.md'):
        path = root / name
        if not path.exists() or 'conductor/runbook.md' not in path.read_text(encoding='utf-8'):
            errors.append(f'Missing context entrypoint: {name}')
        elif path.stat().st_size > 6000:
            errors.append(f'Entrypoint exceeds 6 KB budget: {name}')
    state = json.loads((root / 'conductor/current-state.json').read_text(encoding='utf-8'))
    if state.get('release_ready') is not False:
        errors.append('Working draft must not assert release readiness')
    for track in state.get('active_tracks', []):
        for name in ('spec.md', 'plan.md', 'metadata.json'):
            if not (root / 'conductor/tracks' / track / name).is_file():
                errors.append(f'Missing track artifact: {track}/{name}')
    for name in ('conductor/runbook.md', 'conductor/tracks.md', 'conductor/decisions-v3.md'):
        if not (root / name).is_file():
            errors.append(f'Missing context: {name}')
    for workflow in (root / '.github/workflows').glob('*.yml'):
        text = workflow.read_text(encoding='utf-8')
        for pin in re.findall(r'uses:\s*([^\s]+)', text):
            if not pin.startswith('./') and not re.fullmatch(r'[^@]+@[a-f0-9]{40}', pin):
                errors.append(f'Mutable action reference: {workflow.name}: {pin}')
        if 'pull_request_target' in text or 'continue-on-error: true' in text:
            errors.append(f'Unsafe CI bypass in {workflow.name}')
    return errors


def version_errors(root: Path) -> list[str]:
    """Require an isolated environment and all declared direct assurance pins."""
    cfg = tomllib.loads((root / 'pyproject.toml').read_text(encoding='utf-8'))
    declarations = cfg['project']['dependencies'] + cfg['project']['optional-dependencies']['tabular']
    declarations += cfg['dependency-groups']['test']
    declarations += [value for value in cfg['dependency-groups']['assurance'] if isinstance(value, str)]
    project_environment = Path(sys.prefix).resolve() == (root / '.venv').resolve()
    errors = [] if project_environment else ['The project .venv is required; the shared host environment is not certified']
    for declaration in sorted(set(declarations)):
        name, expected = declaration.split('==', maxsplit=1)
        try:
            installed = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            errors.append(f'Missing {declaration}')
        else:
            if installed != expected:
                errors.append(f'{name}: installed {installed}; required {expected}')
    if project_environment:
        names = [dist.metadata['Name'] for dist in importlib.metadata.distributions() if dist.metadata['Name']]
        errors.extend(f'Prohibited installed dependency: {name}' for name in forbidden_packages(names))
    return errors


def native_version_errors(root: Path) -> list[str]:
    """Require pinned native releases; PATH tools cannot silently override them."""
    manifest = json.loads((root / 'quality/native-tools.json').read_text(encoding='utf-8'))
    errors: list[str] = []
    for name, entries in manifest.items():
        local = root / '.tools/bin' / name
        executable = str(local) if local.is_file() else name
        flag = 'version' if name == 'gitleaks' else '-version' if name == 'actionlint' else '--version'
        try:
            result = subprocess.run([executable, flag], cwd=root, capture_output=True,
                                    text=True, timeout=10, check=False)
        except (OSError, subprocess.TimeoutExpired) as error:
            errors.append(f'{name}: unavailable: {error}')
            continue
        pattern = rf'(?<![\d.]){re.escape(entries["version"])}(?![\d.])'
        if result.returncode or not re.search(pattern, result.stdout + result.stderr):
            errors.append(f'{name}: expected {entries["version"]}; version command did not verify it')
    return errors


def main() -> int:
    """Run a named check; EX_UNAVAILABLE explicitly distinguishes prerequisites."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('check', choices=('inputs', 'context', 'lock', 'versions', 'submodule', 'mutation', 'scalene_output', 'native_versions'))
    args = parser.parse_args()
    if args.check == 'inputs':
        report = audit_inputs(ROOT)
        print(json.dumps(report, indent=2))
        return int(bool(report['errors']))
    if args.check == 'context':
        errors = context_errors(ROOT)
    elif args.check == 'lock':
        errors = validate_lock(ROOT / 'uv.lock')
        if not (ROOT / 'uv.lock').exists():
            print('\n'.join(errors))
            return 69
    elif args.check == 'versions':
        errors = version_errors(ROOT)
        if errors:
            print('\n'.join(errors))
            return 69
    elif args.check == 'native_versions':
        errors = native_version_errors(ROOT)
        if errors:
            print('\n'.join(errors))
            return 69
    elif args.check == 'submodule':
        result = subprocess.run(['git', 'submodule', 'status'], cwd=ROOT, capture_output=True, text=True, check=False)
        print(result.stdout, result.stderr)
        if result.returncode or not (ROOT / 'extensions/conductor/README.md').exists():
            print('Conductor checkout unavailable; a gitlink alone is not a checkout')
            return 69
        errors = [] if result.stdout.strip() and not result.stdout.startswith(('-', '+', 'U')) else ['Submodule differs from pinned revision']
    elif args.check == 'mutation':
        path = ROOT / 'coverage/gremlins/gremlins.json'
        if not path.exists():
            print('No fresh Gremlins report; execution gate must pass first')
            return 69
        errors = mutation_errors(json.loads(path.read_text(encoding='utf-8')))
    else:
        path = ROOT / 'verification/v4/scalene.json'
        if not path.exists():
            print('No Scalene profile was produced')
            return 69
        data = json.loads(path.read_text(encoding='utf-8'))
        errors = [] if isinstance(data, dict) and data.get('files') else ['Scalene profile contains no files']
    print(json.dumps({'check': args.check, 'errors': errors}, indent=2))
    return int(bool(errors))


if __name__ == '__main__':
    raise SystemExit(main())
