"""Explicit data, provenance and dependency checks, with no network requirement."""
from __future__ import annotations

import ast
import csv
from dataclasses import asdict
import json
import math
from pathlib import Path
import re
import tomllib

BANNED = frozenset({'pandas', 'xarray', 'pandas-stubs', 'xarray-stubs'})


def forbidden_imports(source: str) -> list[str]:
    """Detect prohibited imports, including literal dynamic imports, not prose."""
    found: set[str] = set()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module]
        elif isinstance(node, ast.Call) and node.args:
            literal = node.args[0]
            func = node.func
            dynamic = ((isinstance(func, ast.Name) and func.id == '__import__')
                       or (isinstance(func, ast.Attribute) and func.attr == 'import_module'))
            if dynamic and isinstance(literal, ast.Constant) and isinstance(literal.value, str):
                names = [literal.value]
        found.update(name for name in names if name.split('.')[0] in {'pandas', 'xarray'})
    return sorted(found)


def forbidden_packages(names: list[str]) -> list[str]:
    """Check canonical package names in direct or resolved dependency records."""
    canonical = {re.sub(r'[-_.]+', '-', name.lower()) for name in names}
    return sorted(canonical & BANNED)


def validate_lock(path: Path) -> list[str]:
    """A missing or unhashed registry graph is not a reproducibility lock."""
    if not path.is_file():
        return ['Dependency lock unavailable; resolve and review uv.lock before full acceptance']
    try:
        content = tomllib.loads(path.read_text(encoding='utf-8'))
    except (tomllib.TOMLDecodeError, UnicodeError):
        return ['Invalid dependency lock']
    packages = content.get('package', [])
    if not isinstance(packages, list) or not packages:
        return ['Empty package graph']
    errors: list[str] = []
    names: list[str] = []
    for package in packages:
        if not isinstance(package, dict) or not isinstance(package.get('name'), str):
            errors.append('Malformed package record')
            continue
        name = package['name']
        names.append(name)
        source = package.get('source', {})
        if not isinstance(source, dict):
            errors.append(f'Invalid source: {name}')
            continue
        if 'registry' in source:
            artifacts = [*package.get('wheels', [])]
            if 'sdist' in package:
                artifacts.append(package['sdist'])
            if not artifacts:
                errors.append(f'No registry artifact hashes: {name}')
            for artifact in artifacts:
                if not isinstance(artifact, dict) or not re.fullmatch(r'sha256:[a-f0-9]{64}', str(artifact.get('hash', ''))):
                    errors.append(f'Invalid artifact hash: {name}')
    errors.extend(f'Prohibited dependency: {name}' for name in forbidden_packages(names))
    return errors


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def _same_value(first: object, second: object) -> bool:
    if isinstance(first, (list, tuple)) and isinstance(second, (list, tuple)):
        return len(first) == len(second) and all(_same_value(a, b) for a, b in zip(first, second, strict=True))
    if isinstance(first, bool) or isinstance(second, bool):
        return type(first) is type(second) and first == second
    if isinstance(first, (int, float)) and isinstance(second, (int, float)):
        return math.isclose(first, second, rel_tol=1e-12, abs_tol=1e-12)
    return first == second


def audit_inputs(root: Path) -> dict[str, object]:
    """Check completeness and reconciliation, not empirical truth of assumptions."""
    from src.statewide import Parameters, load_sites

    errors: list[str] = []
    supplied = json.loads((root / 'data/parameters.json').read_text(encoding='utf-8'))
    defaults = asdict(Parameters())
    if set(supplied) != set(defaults):
        errors.append('Parameter JSON and model schema differ')
    params = asdict(Parameters(**supplied))
    register = _rows(root / 'evidence/parameter_register.csv')
    names = [row['parameter'] for row in register]
    if len(names) != len(set(names)) or set(names) != set(params):
        errors.append('Parameter register incomplete or duplicated')
    sources = _rows(root / 'evidence/sources.csv')
    literature = _rows(root / 'evidence/literature_parameter_map.csv')
    ids = [row['source_id'] for row in sources] + [row['study_id'] for row in literature]
    if len(ids) != len(set(ids)):
        errors.append('Duplicate source/study identifier')
    known = set(ids) | {'ASSUMPTION', 'DECISION'}
    for row in register:
        name = row['parameter']
        if name in params and not _same_value(json.loads(row['base_value']), params[name]):
            errors.append(f'Parameter register mismatch: {name}')
        if not row['uncertainty'] or not row['interpretation']:
            errors.append(f'Incomplete assumption disclosure: {name}')
        for token in row['source_ids'].split(';'):
            if token not in known:
                errors.append(f'Unresolved evidence: {name}: {token}')
    for row in [*sources, *literature]:
        if not row['url'] or not row['limitations']:
            errors.append('Evidence lacks locator or limitation')
    totals = json.loads((root / 'data/population_totals.json').read_text(encoding='utf-8'))
    rows = _rows(root / 'data/births_queensland_2022.csv')
    sites = load_sites(root / 'data/births_queensland_2022.csv')
    count = sum(site.births for site in sites)
    if count != totals['public_births'] or len(rows) != totals['raw_public_rows']:
        errors.append('Birth totals or source row counts do not reconcile')
    if sum(totals[key] for key in ('public_births', 'private_births_aggregate_only', 'home_freebirths', 'born_before_arrival')) != totals['total']:
        errors.append('Whole-population totals do not reconcile')
    if {site.year for site in sites} != {totals['year']}:
        errors.append('Birth year does not reconcile')
    for folder in ('src', 'scripts', 'quality'):
        for file in (root / folder).rglob('*.py'):
            errors.extend(f'{file.relative_to(root)}: prohibited import {name}'
                          for name in forbidden_imports(file.read_text(encoding='utf-8')))
    return {
        'errors': errors, 'parameters_checked': len(register), 'public_births': count,
        'raw_public_rows': len(rows), 'aliased_sites': len(sites), 'sources': len(sources),
        'studies': len(literature),
        'source_validation': 'Schema, arithmetic and provenance links checked; estimated inputs remain assumptions',
    }
