"""Bind current scientific outputs to actual bytes and calculation dependencies."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

MANIFEST = 'release_manifest.json'
SOURCE_DIRECTORIES = ('src', 'data', 'config')
SOURCE_FILES = ('scripts/analyse_refinements.py', 'scripts/plot_refinements.py', 'quality/clinical_review.py', 'scripts/reproduce.py', 'scripts/analyse_v7.py', 'scripts/build_current_report.py',
                'scripts/plot_current.py', 'quality/artifacts.py', 'assets/Briefing_note.docx',
                'assets/chhhs-powerpoint-template.pptx', 'assets/chhhs-content-v2-background.png')


def digest_file(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def inventory(root: Path, paths: list[Path]) -> dict[str, str]:
    root = root.resolve()
    result = {}
    for path in sorted(set(paths)):
        actual = path.resolve()
        if not actual.is_relative_to(root) or path.is_symlink():
            raise ValueError('Manifest path escapes its root or is a symlink')
        if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
            result[path.relative_to(root).as_posix()] = digest_file(path)
    return result


def calculation_inputs(root: Path) -> dict[str, str]:
    paths = [root / name for name in SOURCE_FILES if (root / name).is_file()]
    for name in SOURCE_DIRECTORIES:
        paths.extend((root / name).rglob('*'))
    return inventory(root, [p for p in paths if p.is_file()])


def output_inventory(output: Path) -> dict[str, str]:
    return inventory(output, [p for p in output.rglob('*')
                              if p.is_file() and p.name not in {MANIFEST, MANIFEST + '.tmp'}])


def seal(root: Path, output: Path) -> dict:
    """Seal a generated set; self-digest is excluded, and time does not affect bytes."""
    root, output = root.resolve(), output.resolve()
    if not output.is_relative_to(root / 'outputs'):
        raise ValueError('Release output must be inside repository outputs')
    artifacts = output_inventory(output)
    if not artifacts:
        raise ValueError('Cannot seal an empty artifact set')
    commit = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=root, capture_output=True,
                            text=True, timeout=10, check=False).stdout.strip()
    report = {'schema_version': 1, 'source_commit_at_generation': commit or None,
              'analysis_inputs': calculation_inputs(root), 'artifacts': artifacts,
              'interpretation': 'Byte/provenance check, not clinical or independent validation'}
    target = output / MANIFEST
    temporary = target.with_name(MANIFEST + '.tmp')
    temporary.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    temporary.replace(target)
    return report


def verify(root: Path, output: Path) -> list[str]:
    """Reject changed dependencies, missing/extra files and unsafe manifest entries."""
    root, output = root.resolve(), output.resolve()
    if not output.is_relative_to(root / 'outputs'):
        return ['Release output outside repository outputs']
    try:
        report = json.loads((output / MANIFEST).read_text(encoding='utf-8'))
        if not isinstance(report, dict) or report.get('schema_version') != 1:
            return ['Invalid release manifest']
        artifacts = report.get('artifacts')
        if not isinstance(artifacts, dict) or not artifacts:
            return ['Empty/invalid artifact scope']
        for name, digest in artifacts.items():
            target = output / name
            if (Path(name).is_absolute() or not target.resolve().is_relative_to(output)
                    or not isinstance(digest, str) or len(digest) != 64):
                return ['Unsafe artifact path or invalid digest']
        errors = []
        if artifacts != output_inventory(output):
            errors.append('Artifact files or inventory changed')
        if report.get('analysis_inputs') != calculation_inputs(root):
            errors.append('Calculation dependencies changed')
        return errors
    except (OSError, ValueError, TypeError):
        return ['Manifest unavailable or invalid; no release verification']


def artifact_dependency_fingerprint(root: Path) -> str:
    """Bind generated files read by regression tests separately from execution inputs.

    This intentionally includes all retained outputs, not just current tables.
    Verification logs remain outside this scope and cannot change their own digest.
    """
    files = inventory(root, [p for p in (root / 'outputs').rglob('*') if p.is_file()])
    return hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('seal', 'verify'))
    parser.add_argument('--output', type=Path, default=None)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.output is not None:
        paths = [args.output]
    else:
        from src.configuration import strict_json
        try:
            config = strict_json(root / 'config/assurance.json')
            paths = [config['current_output'], *config.get('additional_outputs', [])]
            if (not paths or any(not isinstance(p, str) or not p for p in paths)
                    or len(set(paths)) != len(paths)):
                raise ValueError('Unique nonempty output scopes required')
        except (OSError, ValueError, KeyError, TypeError) as error:
            print(json.dumps({'errors': ['Invalid current-artifact configuration', str(error)]}))
            return 1
    outputs = [(root / path).resolve() for path in paths]
    if any(not output.is_relative_to(root / 'outputs') or output == root / 'outputs' for output in outputs):
        parser.error('Release outputs must be repository output subdirectories')
    if args.action == 'seal':
        print(json.dumps([seal(root, output) for output in outputs], indent=2))
        return 0
    reports = [{'scope': str(output.relative_to(root)), 'errors': verify(root, output)} for output in outputs]
    errors = [error for report in reports for error in report['errors']]
    print(json.dumps({'reports': reports, 'errors': errors}, indent=2))
    return int(bool(errors))


if __name__ == '__main__':
    raise SystemExit(main())
