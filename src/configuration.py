"""Resolve complete declared model inputs before execution; no silent defaults."""
from __future__ import annotations

from dataclasses import asdict, dataclass, fields
import hashlib
import json
from pathlib import Path

from src.equipment import OwnedAsset, validate_estate
from src.pathways_v6 import PathwaySpec
from src.statewide import Parameters


def strict_json(path: Path) -> dict:
    """Reject duplicate JSON keys and nonstandard nonfinite numbers."""
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f'Duplicate configuration key: {key}')
            result[key] = value
        return result
    def nonfinite(value):
        raise ValueError(f'Nonfinite JSON value: {value}')
    result = json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=pairs, parse_constant=nonfinite)
    if not isinstance(result, dict):
        raise ValueError('Configuration document must be an object')
    return result


def exact_keys(value: dict, expected: set[str], label: str) -> None:
    if not isinstance(value, dict) or set(value) != expected:
        raise ValueError(f'{label} requires exactly {sorted(expected)}')


@dataclass(frozen=True)
class ResolvedConfiguration:
    """Validated inputs plus a digest of the actual source files used."""

    parameters: Parameters
    pathways: PathwaySpec
    owned_assets: tuple[OwnedAsset, ...]
    draws: int
    seed: int
    portfolios: tuple[str, ...]
    source_hashes: dict[str, str]
    digest: str

    def snapshot(self) -> dict:
        return {'parameters': asdict(self.parameters), 'pathways': asdict(self.pathways),
                'owned_assets': [asdict(a) for a in self.owned_assets],
                'run': {'draws': self.draws, 'seed': self.seed, 'portfolios': self.portfolios},
                'source_hashes': self.source_hashes, 'configuration_sha256': self.digest}


def load_configuration(root: Path, path: Path | None = None) -> ResolvedConfiguration:
    """Load the authoritative run recipe with repository-bounded source paths."""
    root = root.resolve()
    path = (path or root / 'config/reference.json').resolve()
    if not path.is_relative_to(root):
        raise ValueError('Run configuration must remain inside the repository')
    recipe = strict_json(path)
    exact_keys(recipe, {'schema_version', 'parameters', 'pathways', 'equipment_estate', 'run'}, 'Run recipe')
    if type(recipe['schema_version']) is not int or recipe['schema_version'] != 1:
        raise ValueError('Unsupported run-configuration schema')
    sources = [path]
    docs = {}
    for key in ('parameters', 'pathways', 'equipment_estate'):
        value = recipe[key]
        if not isinstance(value, str) or Path(value).is_absolute():
            raise ValueError('Source paths must be repository-relative strings')
        target = (root / value).resolve()
        if not target.is_relative_to(root) or not target.is_file():
            raise ValueError(f'Invalid configuration source: {key}')
        sources.append(target)
        docs[key] = strict_json(target)
    exact_keys(docs['parameters'], {f.name for f in fields(Parameters)}, 'Parameters')
    exact_keys(docs['pathways'], {f.name for f in fields(PathwaySpec)}, 'Pathways')
    exact_keys(docs['equipment_estate'], {'owned_assets', 'remaining_life_basis'}, 'Equipment estate')
    if not isinstance(docs['equipment_estate']['owned_assets'], list):
        raise ValueError('Owned assets must be a list')
    owned = []
    for item in docs['equipment_estate']['owned_assets']:
        exact_keys(item, {'site', 'strategy', 'remaining_life_years'}, 'Owned asset')
        owned.append(OwnedAsset(**item))
    assets = tuple(owned)
    validate_estate(assets)
    run = recipe['run']
    exact_keys(run, {'draws', 'seed', 'portfolios'}, 'Run controls')
    if type(run['draws']) is not int or not 2 <= run['draws'] <= 1_000_000:
        raise ValueError('Draw count must be an integer in 2..1000000')
    if type(run['seed']) is not int or run['seed'] < 0:
        raise ValueError('Seed must be a nonnegative integer')
    networks = run['portfolios']
    if (not isinstance(networks, list) or not networks or any(not isinstance(k, str) for k in networks)
            or len(set(networks)) != len(networks) or set(networks) - {'pilot', 'chhhs', 'chhhs_tchhs', 'spokes'}):
        raise ValueError('Unknown, empty or repeated portfolio')
    p, s = Parameters(**docs['parameters']), PathwaySpec(**docs['pathways'])
    if any(a.remaining_life_years > p.life_years for a in assets):
        raise ValueError('Remaining asset life exceeds equipment life')
    hashes = {f.relative_to(root).as_posix(): hashlib.sha256(f.read_bytes()).hexdigest() for f in sources}
    digest = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()
    return ResolvedConfiguration(p, s, assets, run['draws'], run['seed'], tuple(networks), hashes, digest)
