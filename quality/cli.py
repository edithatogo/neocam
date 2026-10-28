"""One explicit assurance command for a solo developer and hosted CI.

Quick checks are never a substitute for full acceptance. No profile publishes a
release or assumes that a local run is a hosted GitHub Actions result.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import importlib.metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys

from quality.assurance import Gate, Receipt, input_fingerprint, run_gate, validate_receipts

ROOT = Path(__file__).resolve().parents[1]


def _native(name: str) -> str:
    local = ROOT / '.tools/bin' / name
    return str(local) if local.exists() else (shutil.which(name) or name)


def gates_for_profile(profile: str) -> list[Gate]:
    """Declare every gate once; covered execution supplies test and coverage evidence without a second suite."""
    python = sys.executable
    gates = [
        Gate('pytest', (python, '-m', 'pytest', '-q'), 180),
        Gate('inputs', (python, '-m', 'quality.checks', 'inputs')),
        Gate('context', (python, '-m', 'quality.checks', 'context')),
    ]
    if profile == 'quick':
        return gates
    if profile not in {'pr', 'full'}:
        raise ValueError('Unknown assurance profile')
    gates[0] = Gate('pytest', (python, '-m', 'coverage', 'run', '-m', 'pytest', '-q'), 180, 'coverage')
    gates.extend([
        Gate('source_integrity', (python, '-m', 'quality.source_archive'), 60),
        Gate('coverage', (python, '-m', 'coverage', 'json', '-o', 'verification/v7/coverage.json'), 60, 'coverage'),
        Gate('coverage_threshold', (python, '-m', 'coverage', 'report', '--fail-under=90'), 60, 'coverage'),
        Gate('core_coverage', (python, '-m', 'coverage', 'report', '--include=src/pathways_v6.py,src/perspectives_v7.py,src/portfolios_v7.py,src/audit_v7.py', '--fail-under=95'), 60, 'coverage'),
        Gate('ruff_lint', (python, '-m', 'ruff', 'check', 'src', 'scripts', 'quality', 'tests'), 180, 'ruff'),
        Gate('ruff_format', (python, '-m', 'ruff', 'format', '--check', 'src', 'scripts', 'quality', 'tests'), 180, 'ruff'),
        Gate('ty', (python, '-m', 'ty', 'check'), 180, 'ty'),
        Gate('basedpyright', (python, '-m', 'basedpyright'), 180, 'basedpyright'),
        Gate('hypothesis', (python, '-m', 'pytest', 'quality/hypothesis_properties.py', '-q'), 180, 'hypothesis'),
        Gate('gremlins', (python, '-m', 'pytest', 'tests', 'quality/hypothesis_properties.py', '--gremlins', '--gremlin-workers=2', '--gremlin-clear-cache', '--gremlin-report=json', '--gremlin-report=html', '--strict-pardons'), 1800, 'pytest_gremlins'),
        Gate('mutation_score', (python, '-m', 'quality.checks', 'mutation'), allow_unavailable=True),
        Gate('scalene', (python, '-m', 'scalene', 'run', '-o', 'verification/v7/scalene.json', 'quality/profile_workload.py'), 180, 'scalene'),
        Gate('scalene_output', (python, '-m', 'quality.checks', 'scalene_output'), allow_unavailable=True),
        Gate('gitleaks_history', (_native('gitleaks'), 'git', '--log-opts=--all', '--redact=100', '--report-format=json', '--report-path=verification/v7/gitleaks-history.json', '.'), 180),
        Gate('gitleaks_tree', (_native('gitleaks'), 'dir', '--redact=100', '--report-format=json', '--report-path=verification/v7/gitleaks-tree.json', '.'), 180),
        Gate('vale', (_native('vale'), '--minAlertLevel=warning', 'README.md', 'AGENTS.md', 'GEMINI.md', 'conductor/runbook.md', 'conductor/decisions-v3.md'), 120),
        Gate('dependency_consistency', ('uv', 'lock', '--check', '--offline'), 30),
        Gate('dependency_lock', (python, '-m', 'quality.checks', 'lock'), allow_unavailable=True),
        Gate('native_versions', (python, '-m', 'quality.checks', 'native_versions'), allow_unavailable=True),
        Gate('locked_versions', (python, '-m', 'quality.checks', 'versions'), allow_unavailable=True),
        Gate('pip_audit', (python, '-m', 'pip_audit', '--local', '--format=json', '--output=verification/v7/pip-audit.json'), 300, 'pip_audit'),
        Gate('sbom', (python, '-m', 'pip_audit', '--local', '--format=cyclonedx-json', '--output=verification/v7/sbom.json'), 300, 'pip_audit'),
        Gate('conductor_checkout', (python, '-m', 'quality.checks', 'submodule'), allow_unavailable=True),
        Gate('polars_consistency', (python, '-m', 'quality.polars_probe'), 60, 'polars'),
    ])
    gates.extend([
        Gate('actionlint', (_native('actionlint'), '-color'), 60),
        Gate('zizmor', (_native('zizmor'), '--offline', '--persona=pedantic', '.github/workflows'), 60),
        Gate('prek_config', (_native('prek'), 'validate-config', '.pre-commit-config.yaml'), 60),
    ])
    if profile == 'pr':
        deep = {'gremlins', 'mutation_score', 'scalene', 'scalene_output', 'gitleaks_history'}
        gates = [gate for gate in gates if gate.name not in deep]
    return gates


def main() -> int:
    """Collect all gate results, then return nonzero for any blocker or failure."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=('quick', 'pr', 'full'), default='quick')
    args = parser.parse_args()
    directory = ROOT / 'verification/v7' / args.profile
    directory.mkdir(parents=True, exist_ok=True)
    if args.profile in {'pr', 'full'}:
        # Prevent an old report from satisfying a newly failed execution gate.
        for stale in ('coverage/gremlins/gremlins.json', 'verification/v7/scalene.json', '.coverage'):
            (ROOT / stale).unlink(missing_ok=True)
    fingerprint = input_fingerprint(ROOT)
    receipts: list[Receipt] = []
    for gate in gates_for_profile(args.profile):
        receipt = run_gate(gate, ROOT, fingerprint, directory)
        receipts.append(receipt)
        print(f'{receipt.status.upper():7} {gate.name}: {receipt.reason}', flush=True)
    current = input_fingerprint(ROOT)
    problems = validate_receipts(receipts, {gate.name for gate in gates_for_profile(args.profile)}, current, ROOT)
    if fingerprint != current:
        problems.append('Inputs changed during verification')
    versions: dict[str, str | None] = {}
    for name in ('numpy', 'polars', 'scipy', 'scikit-learn', 'pytest', 'coverage', 'ruff', 'ty', 'basedpyright', 'hypothesis', 'pytest-gremlins', 'scalene', 'pip-audit', 'uv', 'prek', 'zizmor', 'pytest-xdist', 'pytest-testmon'):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    commit = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True, capture_output=True, check=False).stdout.strip()
    report = {
        'generated_at': datetime.now(timezone.utc).isoformat(), 'profile': args.profile,
        'source_commit_at_execution': commit, 'input_fingerprint': fingerprint,
        'complete_within_profile': not problems,
        'full_local_assurance': args.profile == 'full' and not problems,
        'release_ready': False, 'hosted_assurance': 'Not independently verified by this local runner',
        'environment': {'python': sys.version, 'executable': sys.executable, 'packages': versions},
        'receipts': [asdict(receipt) for receipt in receipts], 'problems': problems,
        'review': 'Author review; not an independent review',
        'evidence_reuse': 'pytest and coverage derive from one covered suite in PR/full profiles',
        'required_gates': [g.name for g in gates_for_profile(args.profile)],
    }
    (directory / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return int(bool(problems))


if __name__ == '__main__':
    raise SystemExit(main())
