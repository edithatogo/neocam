"""Bind current scientific outputs to actual bytes and calculation dependencies."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess  # ruff: ignore[suspicious-subprocess-import] -- sealing records the local git commit
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, TypedDict, cast

if TYPE_CHECKING:
    from collections.abc import Callable

MANIFEST = "release_manifest.json"
# Length of a lowercase SHA-256 hex digest.
SHA256_HEX_LENGTH = 64
SOURCE_DIRECTORIES = ("src", "data", "config")
SOURCE_FILES = (
    "scripts/analyse_refinements.py",
    "scripts/plot_refinements.py",
    "quality/clinical_review.py",
    "scripts/reproduce.py",
    "scripts/analyse_v7.py",
    "scripts/build_current_report.py",
    "scripts/plot_current.py",
    "quality/artifacts.py",
    "assets/Briefing_note.docx",
    "assets/chhhs-powerpoint-template.pptx",
    "assets/chhhs-content-v2-background.png",
)


class _ArtifactArgs(Protocol):
    """The parsed CLI attributes for the seal/verify dispatcher."""

    action: str
    output: Path | None


class _ScopeReport(TypedDict):
    """One verified output scope and its errors."""

    scope: str
    errors: list[str]


def digest_file(path: Path) -> str:
    """Return the SHA-256 hex digest of a file's bytes.

    Returns:
        str: Lowercase hex SHA-256 digest.
    """
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def inventory(root: Path, paths: list[Path]) -> dict[str, str]:
    """Map each in-scope regular file to its digest, rejecting escapes.

    Returns:
        dict[str, str]: Root-relative POSIX paths mapped to SHA-256 digests.

    Raises:
        ValueError: If a manifest path escapes `root` or is a symlink.
    """
    root = root.resolve()
    result: dict[str, str] = {}
    for path in sorted(set(paths)):
        actual = path.resolve()
        if not actual.is_relative_to(root) or path.is_symlink():
            msg = "Manifest path escapes its root or is a symlink"
            raise ValueError(msg)
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
            result[path.relative_to(root).as_posix()] = digest_file(path)
    return result


def _generated(path: Path) -> bool:
    """True for local build artefacts, which a fresh clone does not contain.

    Returns:
        bool: Whether the path is ignored/derived rather than a calculation input.
    """
    return (
        any(part in {"__pycache__", ".mypy_cache", ".ruff_cache", ".pytest_cache"} for part in path.parts)
        or any(part.endswith(".egg-info") for part in path.parts)
        or path.suffix in {".pyc", ".pyo"}
    )


def calculation_inputs(root: Path) -> dict[str, str]:
    """Digest every source, data, config and script file feeding calculations.

    Derived local artefacts (byte-compiled caches, egg-info metadata) are excluded: they
    are not calculation inputs, and pinning them made the sealed digest depend on whatever
    build junk happened to sit in the working tree, so the same commit failed this gate on
    a fresh clone.

    Returns:
        dict[str, str]: Root-relative paths mapped to digests for existing inputs.
    """
    paths = [root / name for name in SOURCE_FILES if (root / name).is_file()]
    for name in SOURCE_DIRECTORIES:
        paths.extend((root / name).rglob("*"))
    return inventory(root, [p for p in paths if p.is_file() and not _generated(p)])


def output_inventory(output: Path) -> dict[str, str]:
    """Digest the produced files in an output directory, excluding the manifest.

    Returns:
        dict[str, str]: Output-relative paths mapped to digests.
    """
    return inventory(
        output, [p for p in output.rglob("*") if p.is_file() and p.name not in {MANIFEST, MANIFEST + ".tmp"}]
    )


def seal(root: Path, output: Path) -> dict[str, object]:
    """Seal a generated set; self-digest is excluded, and time does not affect bytes.

    Returns:
        dict[str, object]: The release manifest written beside the sealed artifacts.

    Raises:
        ValueError: If the output escapes `outputs` or has no artifacts.
    """
    root, output = root.resolve(), output.resolve()
    if not output.is_relative_to(root / "outputs"):
        msg = "Release output must be inside repository outputs"
        raise ValueError(msg)
    artifacts = output_inventory(output)
    if not artifacts:
        msg = "Cannot seal an empty artifact set"
        raise ValueError(msg)
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],  # ruff: ignore[start-process-with-partial-path] -- fixed git command, not user input
        cwd=root,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    ).stdout.strip()
    report: dict[str, object] = {
        "schema_version": 1,
        "source_commit_at_generation": commit or None,
        "analysis_inputs": calculation_inputs(root),
        "artifacts": artifacts,
        "interpretation": "Byte/provenance check, not clinical or independent validation",
    }
    target = output / MANIFEST
    temporary = target.with_name(MANIFEST + ".tmp")
    _ = temporary.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _ = temporary.replace(target)
    return report


def manifest_errors(report: object, output: Path, root: Path) -> list[str]:
    """Validate a parsed release manifest against its artifacts and dependencies.

    Returns:
        list[str]: Human-readable errors; empty when the manifest is consistent.
    """
    if not isinstance(report, dict):
        return ["Invalid release manifest"]
    record = cast("dict[str, object]", report)
    if record.get("schema_version") != 1:
        return ["Invalid release manifest"]
    artifacts = record.get("artifacts")
    if not isinstance(artifacts, dict) or not artifacts:
        return ["Empty/invalid artifact scope"]
    entries = cast("dict[str, object]", artifacts)
    for name, digest in entries.items():
        target = output / name
        if (
            Path(name).is_absolute()
            or not target.resolve().is_relative_to(output)
            or not isinstance(digest, str)
            or len(digest) != SHA256_HEX_LENGTH
        ):
            return ["Unsafe artifact path or invalid digest"]
    errors: list[str] = []
    if entries != output_inventory(output):
        errors.append("Artifact files or inventory changed")
    if record.get("analysis_inputs") != calculation_inputs(root):
        errors.append("Calculation dependencies changed")
    return errors


def verify(root: Path, output: Path) -> list[str]:
    """Reject changed dependencies, missing/extra files and unsafe manifest entries.

    Returns:
        list[str]: Validation errors; empty when the release verifies.
    """
    root, output = root.resolve(), output.resolve()
    if not output.is_relative_to(root / "outputs"):
        return ["Release output outside repository outputs"]
    try:
        report: object = cast("object", json.loads((output / MANIFEST).read_text(encoding="utf-8")))
        errors = manifest_errors(report, output, root)
    except OSError, ValueError, TypeError:
        return ["Manifest unavailable or invalid; no release verification"]
    return errors


def artifact_dependency_fingerprint(root: Path) -> str:
    """Bind generated files read by regression tests separately from execution inputs.

    This intentionally includes all retained outputs, not just current tables.
    Verification logs remain outside this scope and cannot change their own digest.

    Returns:
        str: SHA-256 of the sorted retained-output inventory.
    """
    files = inventory(root, [p for p in (root / "outputs").rglob("*") if p.is_file()])
    return hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()


def configured_outputs(config: dict[str, object]) -> list[str]:
    """Return the unique, non-empty output scopes named by a sealed configuration.

    Returns:
        list[str]: The current and additional configured output scopes.

    Raises:
        ValueError: If scopes are missing, empty or duplicated.
    """
    current = config["current_output"]
    additional = config.get("additional_outputs", [])
    values: list[object] = [current]
    if isinstance(additional, list):
        values.extend(cast("list[object]", additional))
    if not values or any(not isinstance(p, str) or not p for p in values) or len(set(values)) != len(values):
        msg = "Unique nonempty output scopes required"
        raise ValueError(msg)
    return [p for p in values if isinstance(p, str)]


def main() -> int:
    """Seal or verify the release output sets named by CLI flags or configuration.

    Returns:
        int: 0 when every requested action succeeds, otherwise 1.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument("action", choices=("seal", "verify"))
    _ = parser.add_argument("--output", type=Path, default=None)
    args = cast("_ArtifactArgs", cast("object", parser.parse_args()))
    root = Path(__file__).resolve().parents[1]
    if args.output is not None:
        paths = [args.output]
    else:
        from src import configuration  # ruff: ignore[import-outside-top-level] -- deferred so the module imports without src on the path

        try:
            loader = cast("Callable[[Path], dict[str, object]]", configuration.strict_json)
            config = loader(root / "config/assurance.json")
            paths = configured_outputs(config)
        except (OSError, ValueError, KeyError, TypeError) as error:
            print(json.dumps({"errors": ["Invalid current-artifact configuration", str(error)]}))  # ruff: ignore[print] -- CLI error report goes to stdout
            return 1
    outputs = [(root / path).resolve() for path in paths]
    if any(not output.is_relative_to(root / "outputs") or output == root / "outputs" for output in outputs):
        parser.error("Release outputs must be repository output subdirectories")
    if args.action == "seal":
        print(json.dumps([seal(root, output) for output in outputs], indent=2))  # ruff: ignore[print] -- CLI seal report goes to stdout
        return 0
    reports: list[_ScopeReport] = [
        {"scope": str(output.relative_to(root)), "errors": verify(root, output)} for output in outputs
    ]
    errors = [error for report in reports for error in report["errors"]]
    print(json.dumps({"reports": reports, "errors": errors}, indent=2))  # ruff: ignore[print] -- CLI verify report goes to stdout
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
