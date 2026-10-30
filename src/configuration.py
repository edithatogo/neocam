"""Resolve complete declared model inputs before execution; no silent defaults."""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import NoReturn

from src.equipment import OwnedAsset, validate_estate
from src.pathways_v6 import PathwaySpec
from src.portfolios_v7 import CHHHS, TCHHS
from src.statewide import Parameters

# Draw-count guard bounds; documented in the run-recipe contract.
_MIN_DRAWS = 2
_MAX_DRAWS = 1_000_000


def strict_json(path: Path) -> dict:
    """Reject duplicate JSON keys and nonstandard nonfinite numbers.

    Returns:
        The parsed JSON object.

    Raises:
        TypeError: If the document root is not a JSON object.
    """

    def pairs(items: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in items:
            if key in result:
                msg = f"Duplicate configuration key: {key}"
                raise ValueError(msg)
            result[key] = value
        return result

    def nonfinite(value: str) -> NoReturn:
        msg = f"Nonfinite JSON value: {value}"
        raise ValueError(msg)

    result = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs, parse_constant=nonfinite)
    if not isinstance(result, dict):
        msg = "Configuration document must be an object"
        raise TypeError(msg)
    return result


def exact_keys(value: dict, expected: set[str], label: str) -> None:
    """Require exactly the declared keys on a configuration document.

    Raises:
        ValueError: If the value is not an object or its keys differ.
    """
    if not isinstance(value, dict) or set(value) != expected:
        msg = f"{label} requires exactly {sorted(expected)}"
        raise ValueError(msg)


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
        """Return the resolved inputs and their source digest as plain data."""
        return {
            "parameters": asdict(self.parameters),
            "pathways": asdict(self.pathways),
            "owned_assets": [asdict(a) for a in self.owned_assets],
            "run": {"draws": self.draws, "seed": self.seed, "portfolios": self.portfolios},
            "source_hashes": self.source_hashes,
            "configuration_sha256": self.digest,
        }


def load_configuration(  # ruff: ignore[complex-structure, too-many-locals, too-many-statements] -- one ordered contract-verification pass
    root: Path,
    path: Path | None = None,
) -> ResolvedConfiguration:
    """Load the authoritative run recipe with repository-bounded source paths.

    Returns:
        The validated parameters, pathways, estate and run controls.

    Raises:
        TypeError: If a document or owned-asset collection has the wrong type.
        ValueError: If any declared value, key or source path is invalid.
    """
    root = root.resolve()
    path = (path or root / "config/reference.json").resolve()
    if not path.is_relative_to(root):
        msg = "Run configuration must remain inside the repository"
        raise ValueError(msg)
    recipe = strict_json(path)
    exact_keys(recipe, {"schema_version", "parameters", "pathways", "equipment_estate", "run"}, "Run recipe")
    if type(recipe["schema_version"]) is not int or recipe["schema_version"] != 1:
        msg = "Unsupported run-configuration schema"
        raise ValueError(msg)
    sources = [path]
    docs = {}
    for key in ("parameters", "pathways", "equipment_estate"):
        value = recipe[key]
        if not isinstance(value, str) or Path(value).is_absolute():
            msg = "Source paths must be repository-relative strings"
            raise ValueError(msg)
        target = (root / value).resolve()
        if not target.is_relative_to(root) or not target.is_file():
            msg = f"Invalid configuration source: {key}"
            raise ValueError(msg)
        sources.append(target)
        docs[key] = strict_json(target)
    exact_keys(docs["parameters"], {f.name for f in fields(Parameters)}, "Parameters")
    exact_keys(docs["pathways"], {f.name for f in fields(PathwaySpec)}, "Pathways")
    exact_keys(docs["equipment_estate"], {"owned_assets", "remaining_life_basis"}, "Equipment estate")
    if not isinstance(docs["equipment_estate"]["owned_assets"], list):
        msg = "Owned assets must be a list"
        raise TypeError(msg)
    owned = []
    for item in docs["equipment_estate"]["owned_assets"]:
        exact_keys(item, {"site", "strategy", "remaining_life_years"}, "Owned asset")
        owned.append(OwnedAsset(**item))
    assets = tuple(owned)
    validate_estate(assets)
    with (root / "data/births_queensland_2022.csv").open(encoding="utf-8", newline="") as stream:
        known_sites = {row["facility"] for row in csv.DictReader(stream)} | set(CHHHS) | set(TCHHS)
    if any(asset.site not in known_sites for asset in assets):
        msg = "Unknown site in owned equipment estate"
        raise ValueError(msg)
    run = recipe["run"]
    exact_keys(run, {"draws", "seed", "portfolios"}, "Run controls")
    if type(run["draws"]) is not int or not _MIN_DRAWS <= run["draws"] <= _MAX_DRAWS:
        msg = "Draw count must be an integer in 2..1000000"
        raise ValueError(msg)
    if type(run["seed"]) is not int or run["seed"] < 0:
        msg = "Seed must be a nonnegative integer"
        raise ValueError(msg)
    networks = run["portfolios"]
    if (
        not isinstance(networks, list)
        or not networks
        or any(not isinstance(k, str) for k in networks)
        or len(set(networks)) != len(networks)
        or set(networks) - {"pilot", "chhhs", "chhhs_tchhs", "spokes"}
    ):
        msg = "Unknown, empty or repeated portfolio"
        raise ValueError(msg)
    p, s = Parameters(**docs["parameters"]), PathwaySpec(**docs["pathways"])
    if any(a.remaining_life_years > p.life_years for a in assets):
        msg = "Remaining asset life exceeds equipment life"
        raise ValueError(msg)
    hashes = {f.relative_to(root).as_posix(): hashlib.sha256(f.read_bytes()).hexdigest() for f in sources}
    digest = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()
    return ResolvedConfiguration(p, s, assets, run["draws"], run["seed"], tuple(networks), hashes, digest)
