"""Verify stored source bytes without promoting extracts to original documents."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any


def verify_manifest(root: Path, manifest: Any) -> list[str]:
    """Return errors for malformed metadata, duplicate paths and missing bytes."""
    errors: list[str] = []
    root = root.resolve()
    if not isinstance(manifest, dict):
        return ['Source manifest must be an object']
    files = manifest.get('files', [])
    if not isinstance(files, list) or not files:
        return ['Stored-source verification requires a nonempty file scope']
    if type(manifest.get('original_public_downloads_complete', False)) is not bool:
        errors.append('Original-source completeness must be a boolean')
    seen: set[Path] = set()
    original_ids: set[str] = set()
    for index, item in enumerate(files):
        if not isinstance(item, dict):
            errors.append(f'Invalid source record: {index}')
            continue
        name = item.get('path', '')
        if not isinstance(name, str):
            errors.append(f'Invalid source path type: {index}')
            continue
        try:
            path = (root / name).resolve()
        except (OSError, ValueError, RuntimeError):
            errors.append(f'Invalid source path: {index}')
            continue
        if (not name or Path(name).is_absolute() or path == root
                or root not in path.parents or path in seen):
            errors.append(f'Unsafe or duplicate source path: {name}')
            continue
        seen.add(path)
        if type(item.get('bytes')) is not int or item['bytes'] < 0:
            errors.append(f'Invalid source byte count: {name}')
        if not isinstance(item.get('sha256'), str) or not re.fullmatch(r'[a-f0-9]{64}', item['sha256']):
            errors.append(f'Invalid source digest: {name}')
        if item.get('representation') == 'original public bytes':
            source_id = item.get('source_id')
            if not isinstance(source_id, str) or not source_id.strip():
                errors.append(f'Invalid original source identifier: {name}')
            else:
                original_ids.add(source_id)
        if not path.is_file():
            errors.append(f'Missing source bytes: {name}')
            continue
        try:
            if path.stat().st_size != item.get('bytes'):
                errors.append(f'Source size mismatch: {name}')
            with path.open('rb') as stream:
                digest = hashlib.file_digest(stream, 'sha256').hexdigest()
            if digest != item.get('sha256'):
                errors.append(f'Source digest mismatch: {name}')
        except OSError:
            errors.append(f'Cannot read source bytes: {name}')
    if manifest.get('original_public_downloads_complete') is True:
        expected = manifest.get('expected_original_source_ids')
        valid = (isinstance(expected, list) and bool(expected)
                 and all(isinstance(item, str) and item.strip() for item in expected))
        if not valid or len(set(expected)) != len(expected):
            errors.append('Expected original-source identifiers must be a nonempty unique string list')
        elif not set(expected).issubset(original_ids):
            errors.append('Original public-source completeness is unsupported')
    return errors


def main() -> int:
    """Emit a failure report even when the manifest itself cannot be interpreted."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='verification/v7/source_archive.json')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = (root / args.output).resolve()
    if not output.is_relative_to((root / 'verification').resolve()):
        parser.error('Source report must remain within the verification directory')
    try:
        manifest = json.loads((root / 'sources/manifest.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        manifest = None
        errors = ['Source manifest unavailable or invalid JSON']
    else:
        errors = verify_manifest(root, manifest)
    mapping = manifest if isinstance(manifest, dict) else {}
    records = mapping.get('files')
    report = {
        'stored_file_integrity_passed': not errors,
        'errors': errors,
        'public_original_archival_completeness': (
            not errors and mapping.get('original_public_downloads_complete') is True),
        'stored_files': len(records) if isinstance(records, list) else 0,
    }
    output.parent.mkdir(exist_ok=True, parents=True)
    temporary = output.with_name(output.name + '.tmp')
    temporary.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    temporary.replace(output)
    print(json.dumps(report, indent=2))
    return int(bool(errors))


if __name__ == '__main__':
    raise SystemExit(main())
