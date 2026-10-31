"""Explicit data, provenance and dependency checks, with no network requirement."""

from __future__ import annotations

import ast
import csv
import json
import math
import re
import tomllib
from dataclasses import asdict

# starmap removed: RUF058 requires map() for pairwise application
from typing import TYPE_CHECKING, TypedDict, cast

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from pathlib import Path

BANNED = frozenset({"pandas", "xarray", "pandas-stubs", "xarray-stubs"})


class _PopulationTotals(TypedDict):
    """The fixed whole-population total schema reconciled by the input audit."""

    public_births: int
    private_births_aggregate_only: int
    home_freebirths: int
    born_before_arrival: int
    total: int
    raw_public_rows: int
    year: int


def forbidden_imports(source: str) -> list[str]:
    r"""Detect prohibited imports, including literal dynamic imports, not prose.

    Examples:
        >>> forbidden_imports("import numpy\nfrom pandas import DataFrame\n")
        ['pandas']
        >>> forbidden_imports('import importlib; importlib.import_module("xarray")\n')
        ['xarray']
        >>> forbidden_imports("# pandas and xarray are only mentioned as prose\nimport numpy\n")
        []

    Returns:
        list[str]: Sorted root package names of prohibited imports.
    """
    found: set[str] = set()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module is not None and node.module:
            names = [node.module]
        elif isinstance(node, ast.Call) and node.args:
            literal = node.args[0]
            func = node.func
            dynamic = (isinstance(func, ast.Name) and func.id == "__import__") or (
                isinstance(func, ast.Attribute) and func.attr == "import_module"
            )
            if dynamic and isinstance(literal, ast.Constant) and isinstance(literal.value, str):
                names = [literal.value]
        found.update(name for name in names if name.split(".")[0] in {"pandas", "xarray"})
    return sorted(found)


def forbidden_packages(names: list[str]) -> list[str]:
    """Check canonical package names in direct or resolved dependency records.

    Examples:
        >>> forbidden_packages(["Pandas", "numpy"])
        ['pandas']
        >>> forbidden_packages(["pandas_stubs", "polars"])
        ['pandas-stubs']

    Returns:
        list[str]: Sorted canonical names that are prohibited.
    """
    canonical = {re.sub(r"[-_.]+", "-", name.lower()) for name in names}
    return sorted(canonical & BANNED)


def _valid_artifact_hash(artifact: object) -> bool:
    """Return whether one registry artifact carries a valid SHA-256 digest.

    Returns:
        bool: True when the artifact is a record with a well-formed hash.
    """
    if not isinstance(artifact, dict):
        return False
    record = cast("dict[str, object]", artifact)
    return bool(re.fullmatch(r"sha256:[a-f0-9]{64}", str(record.get("hash", ""))))


def _package_hash_errors(package: dict[str, object]) -> list[str]:
    """Return artifact-hash errors for one registry package record.

    Returns:
        list[str]: Hash errors for the package; empty when all hashes are valid.
    """
    name = package["name"]
    source = package.get("source", {})
    if not isinstance(source, dict):
        return [f"Invalid source: {name}"]
    if "registry" not in cast("dict[str, object]", source):
        return []
    artifacts: list[object] = []
    wheels = package.get("wheels")
    if isinstance(wheels, list):
        artifacts.extend(cast("list[object]", wheels))
    if "sdist" in package:
        artifacts.append(package["sdist"])
    if not artifacts:
        return [f"No registry artifact hashes: {name}"]
    return [f"Invalid artifact hash: {name}" for artifact in artifacts if not _valid_artifact_hash(artifact)]


def validate_lock(path: Path) -> list[str]:
    """A missing or unhashed registry graph is not a reproducibility lock.

    Returns:
        list[str]: Lock errors; empty when a complete hashed graph is present.
    """
    if not path.is_file():
        return ["Dependency lock unavailable; resolve and review uv.lock before full acceptance"]
    try:
        content = cast("dict[str, object]", tomllib.loads(path.read_text(encoding="utf-8")))
    except tomllib.TOMLDecodeError, UnicodeError:
        return ["Invalid dependency lock"]
    packages = content.get("package", [])
    if not isinstance(packages, list) or not packages:
        return ["Empty package graph"]
    errors: list[str] = []
    names: list[str] = []
    for package in cast("list[object]", packages):
        if not isinstance(package, dict):
            errors.append("Malformed package record")
            continue
        record = cast("dict[str, object]", package)
        name = record.get("name")
        if not isinstance(name, str):
            errors.append("Malformed package record")
            continue
        names.append(name)
        errors.extend(_package_hash_errors(record))
    errors.extend(f"Prohibited dependency: {name}" for name in forbidden_packages(names))
    return errors


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _as_sequence(value: object) -> Sequence[object] | None:
    """Return the value as an object sequence, or None when it is not one.

    Returns:
        Sequence[object] | None: The list/tuple element view, otherwise None.
    """
    return cast("Sequence[object]", value) if isinstance(value, (list, tuple)) else None


def _same_value(first: object, second: object) -> bool:
    left, right = _as_sequence(first), _as_sequence(second)
    if left is not None and right is not None:
        # RUF058 requires map() instead of starmap over zip, and RUF... requires explicit
        # strict=; Python 3.14+ map supports strict, so pairwise application stays checked.
        return len(left) == len(right) and all(map(_same_value, left, right, strict=True))
    if isinstance(first, bool) or isinstance(second, bool):
        return type(first) is type(second) and first == second
    if isinstance(first, (int, float)) and isinstance(second, (int, float)):
        return math.isclose(first, second, rel_tol=1e-12, abs_tol=1e-12)
    return first == second


def _register_errors(register: list[dict[str, str]], params: dict[str, object], known: set[str]) -> list[str]:
    """Return reconciliation errors for the parameter-evidence register.

    Returns:
        list[str]: Register errors; empty when every row reconciles and resolves.
    """
    errors: list[str] = []
    for row in register:
        name = row["parameter"]
        if name in params and not _same_value(cast("object", json.loads(row["base_value"])), params[name]):
            errors.append(f"Parameter register mismatch: {name}")
        if not row["uncertainty"] or not row["interpretation"]:
            errors.append(f"Incomplete assumption disclosure: {name}")
        errors.extend(
            f"Unresolved evidence: {name}: {token}" for token in row["source_ids"].split(";") if token not in known
        )
    return errors


def audit_inputs(root: Path) -> dict[str, object]:
    """Check completeness and reconciliation, not empirical truth of assumptions.

    Returns:
        dict[str, object]: Reconciliation errors and counted input totals.
    """
    from src.statewide import Parameters, load_sites  # ruff: ignore[import-outside-top-level] -- deferred so the module imports without src on the path

    errors: list[str] = []
    supplied = cast("dict[str, object]", json.loads((root / "data/parameters.json").read_text(encoding="utf-8")))
    defaults = cast("dict[str, object]", asdict(Parameters()))
    if set(supplied) != set(defaults):
        errors.append("Parameter JSON and model schema differ")
    # The constructor call is a dynamic seam: the exact-key check above guarantees the mapping shape.
    params = cast("dict[str, object]", asdict(cast("Callable[..., Parameters]", Parameters)(**supplied)))
    register = _rows(root / "evidence/parameter_register.csv")
    names = [row["parameter"] for row in register]
    if len(names) != len(set(names)) or set(names) != set(params):
        errors.append("Parameter register incomplete or duplicated")
    sources = _rows(root / "evidence/sources.csv")
    literature = _rows(root / "evidence/literature_parameter_map.csv")
    ids = [row["source_id"] for row in sources] + [row["study_id"] for row in literature]
    if len(ids) != len(set(ids)):
        errors.append("Duplicate source/study identifier")
    known = set(ids) | {"ASSUMPTION", "DECISION"}
    errors.extend(_register_errors(register, params, known))
    errors.extend(
        "Evidence lacks locator or limitation"
        for row in [*sources, *literature]
        if not row["url"] or not row["limitations"]
    )
    totals = cast("_PopulationTotals", json.loads((root / "data/population_totals.json").read_text(encoding="utf-8")))
    rows = _rows(root / "data/births_queensland_2022.csv")
    sites = load_sites(root / "data/births_queensland_2022.csv")
    count = sum(site.births for site in sites)
    if count != totals["public_births"] or len(rows) != totals["raw_public_rows"]:
        errors.append("Birth totals or source row counts do not reconcile")
    if (
        sum(
            totals[key]
            for key in ("public_births", "private_births_aggregate_only", "home_freebirths", "born_before_arrival")
        )
        != totals["total"]
    ):
        errors.append("Whole-population totals do not reconcile")
    if {site.year for site in sites} != {totals["year"]}:
        errors.append("Birth year does not reconcile")
    for folder in ("src", "scripts", "quality"):
        for file in (root / folder).rglob("*.py"):
            errors.extend(
                f"{file.relative_to(root)}: prohibited import {name}"
                for name in forbidden_imports(file.read_text(encoding="utf-8"))
            )
    return {
        "errors": errors,
        "parameters_checked": len(register),
        "public_births": count,
        "raw_public_rows": len(rows),
        "aliased_sites": len(sites),
        "sources": len(sources),
        "studies": len(literature),
        "source_validation": "Schema, arithmetic and provenance links checked; estimated inputs remain assumptions",
    }
