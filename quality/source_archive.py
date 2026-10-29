"""Verify stored source bytes without promoting extracts to original documents."""
from __future__ import annotations
import hashlib
from pathlib import Path
from typing import Any


def verify_manifest(root: Path, manifest: dict[str, Any]) -> list[str]:
    """Return bounded errors for escapes, missing bytes, digest and representation gaps."""
    errors: list[str] = []
    root = root.resolve()
    files = manifest.get('files', [])
    if not isinstance(files, list) or not files:
        return ['Stored-source verification requires a nonempty file scope']
    seen: set[str] = set()
    for item in files:
        name = item.get('path', '')
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
                    if item.get('representation') == 'original public bytes'}
        if not expected or not expected.issubset(acquired):
            errors.append('Original public-source completeness is unsupported')
    return errors


if __name__ == '__main__':
    import json
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root/'sources/manifest.json').read_text())
    errors = verify_manifest(root, manifest)
    report = {'stored_file_integrity_passed': not errors, 'errors': errors,
              'public_original_archival_completeness': manifest.get('original_public_downloads_complete', False),
              'stored_files': len(manifest.get('files', []))}
    output=root/'verification/v7/source_archive.json'
    output.parent.mkdir(exist_ok=True,parents=True)
    output.write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
    raise SystemExit(bool(errors))
