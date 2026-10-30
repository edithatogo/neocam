"""Verify stored source bytes without promoting extracts to original documents."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


def _bytes_errors(path: Path, name: str, item: dict) -> list[str]:
    """Return size and digest errors for one stored source file.

    Returns:
        list[str]: Size and digest errors; empty when stored bytes match metadata.
    """
    try:
        size = path.stat().st_size
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
    except OSError:
        return [f"Cannot read source bytes: {name}"]
    errors: list[str] = []
    if size != item.get("bytes"):
        errors.append(f"Source size mismatch: {name}")
    if digest != item.get("sha256"):
        errors.append(f"Source digest mismatch: {name}")
    return errors


def _original_id_errors(name: str, source_id: object, original_ids: set[str]) -> list[str]:
    """Record or reject the identifier of one original public-source record.

    Returns:
        list[str]: Errors for the identifier; empty when it is accepted.
    """
    if not isinstance(source_id, str) or not source_id.strip():
        return [f"Invalid original source identifier: {name}"]
    original_ids.add(source_id)
    return []


def _metadata_errors(path: Path, name: str, item: dict, original_ids: set[str]) -> list[str]:
    """Check byte count, digest format, representation and stored bytes.

    Returns:
        list[str]: Metadata and byte errors; empty when the record is consistent.
    """
    errors: list[str] = []
    if type(item.get("bytes")) is not int or item["bytes"] < 0:
        errors.append(f"Invalid source byte count: {name}")
    if not isinstance(item.get("sha256"), str) or not re.fullmatch(r"[a-f0-9]{64}", item["sha256"]):
        errors.append(f"Invalid source digest: {name}")
    if item.get("representation") == "original public bytes":
        errors.extend(_original_id_errors(name, item.get("source_id"), original_ids))
    if not path.is_file():
        return [*errors, f"Missing source bytes: {name}"]
    errors.extend(_bytes_errors(path, name, item))
    return errors


def _record_errors(root: Path, index: int, item: object, seen: set[Path], original_ids: set[str]) -> list[str]:
    """Validate one stored-source record, then check its metadata and bytes.

    Returns:
        list[str]: Errors for the record; empty when its metadata and bytes hold.
    """
    if not isinstance(item, dict):
        return [f"Invalid source record: {index}"]
    name = item.get("path", "")
    if not isinstance(name, str):
        return [f"Invalid source path type: {index}"]
    try:
        path = (root / name).resolve()
    except (OSError, ValueError, RuntimeError):
        return [f"Invalid source path: {index}"]
    if not name or Path(name).is_absolute() or path == root or root not in path.parents or path in seen:
        return [f"Unsafe or duplicate source path: {name}"]
    seen.add(path)
    return _metadata_errors(path, name, item, original_ids)


def _completeness_errors(manifest: dict, original_ids: set[str]) -> list[str]:
    """Check declared original-source completeness against recorded identifiers.

    Returns:
        list[str]: Completeness errors; empty when the declared claim is supported.
    """
    if manifest.get("original_public_downloads_complete") is not True:
        return []
    expected = manifest.get("expected_original_source_ids")
    valid = (
        isinstance(expected, list)
        and bool(expected)
        and all(isinstance(item, str) and item.strip() for item in expected)
    )
    if not valid or len(set(expected)) != len(expected):
        return ["Expected original-source identifiers must be a nonempty unique string list"]
    if not set(expected).issubset(original_ids):
        return ["Original public-source completeness is unsupported"]
    return []


def verify_manifest(root: Path, manifest: object) -> list[str]:
    """Return errors for malformed metadata, duplicate paths and missing bytes.

    Returns:
        list[str]: Manifest errors; empty when stored bytes match their metadata.
    """
    errors: list[str] = []
    root = root.resolve()
    if not isinstance(manifest, dict):
        return ["Source manifest must be an object"]
    files = manifest.get("files", [])
    if not isinstance(files, list) or not files:
        return ["Stored-source verification requires a nonempty file scope"]
    if type(manifest.get("original_public_downloads_complete", False)) is not bool:
        errors.append("Original-source completeness must be a boolean")
    seen: set[Path] = set()
    original_ids: set[str] = set()
    for index, item in enumerate(files):
        errors.extend(_record_errors(root, index, item, seen, original_ids))
    errors.extend(_completeness_errors(manifest, original_ids))
    return errors


def main() -> int:
    """Emit a failure report even when the manifest itself cannot be interpreted.

    Returns:
        int: 0 when stored-byte verification passes, otherwise 1.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="verification/v7/source_archive.json")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = (root / args.output).resolve()
    if not output.is_relative_to((root / "verification").resolve()):
        parser.error("Source report must remain within the verification directory")
    try:
        manifest = json.loads((root / "sources/manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        manifest = None
        errors = ["Source manifest unavailable or invalid JSON"]
    else:
        errors = verify_manifest(root, manifest)
    mapping = manifest if isinstance(manifest, dict) else {}
    records = mapping.get("files")
    report = {
        "stored_file_integrity_passed": not errors,
        "errors": errors,
        "public_original_archival_completeness": (
            not errors and mapping.get("original_public_downloads_complete") is True
        ),
        "stored_files": len(records) if isinstance(records, list) else 0,
    }
    output.parent.mkdir(exist_ok=True, parents=True)
    temporary = output.with_name(output.name + ".tmp")
    temporary.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output)
    print(json.dumps(report, indent=2))  # ruff: ignore[print] -- CLI verification report goes to stdout
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
