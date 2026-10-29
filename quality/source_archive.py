"""Verify stored source bytes without promoting extracts to original documents."""
from __future__ import annotations
import hashlib
from pathlib import Path
from typing import Any


def verify_manifest(root: Path, manifest: dict[str, Any]) -> list[str]:
    """Return bounded errors for escapes, missing bytes, digest and representation gaps."""
    errors: list[str] = []
    root = root.resolve()
    if not isinstance(manifest, dict):
        return ['Source manifest must be an object']
    files = manifest.get('files', [])
    if not isinstance(files, list) or not files:
        return ['Stored-source verification requires a nonempty file scope']
    seen: set[str] = set()
    for index, item in enumerate(files):
        if not isinstance(item, dict):
            errors.append(f'Invalid source record: {index}')
            continue
        name = item.get('path', '')
        if not isinstance(name, str):
            errors.append(f'Invalid source path type: {index}')
            continue
        path = (root / name).resolve()
        if not name or path == root or root not in path.parents or name in seen:
            errors.append(f'Unsafe or duplicate source path: {name}')
            continue
        seen.add(name)
        if not path.is_file():
            errors.append(f'Missing source bytes: {name}')
            continue
        if path.stat().st_size != item.get('bytes'):
            errors.append(f'Source size mismatch: {name}')
        if hashlib.sha256(path.read_bytes()).hexdigest() != item.get('sha256'):
            errors.append(f'Source digest mismatch: {name}')
    if manifest.get('original_public_downloads_complete'):
        expected = set(manifest.get('expected_original_source_ids', []))
        acquired = {item.get('source_id') for item in files
                    if isinstance(item, dict) and item.get('representation') == 'original public bytes'}
        if not expected or not expected.issubset(acquired):
            errors.append('Original public-source completeness is unsupported')
    return errors


if __name__ == '__main__':
    import argparse
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='verification/v7/source_archive.json')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root/'sources/manifest.json').read_text())
    errors = verify_manifest(root, manifest)
    report = {'stored_file_integrity_passed': not errors, 'errors': errors,
              'public_original_archival_completeness': manifest.get('original_public_downloads_complete', False),
              'stored_files': len(manifest.get('files', []))}
    output=(root/args.output).resolve()
    if not output.is_relative_to((root/'verification').resolve()):
        parser.error('Source report must remain within the verification directory')
    output.parent.mkdir(exist_ok=True,parents=True)
    output.write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
    raise SystemExit(bool(errors))
