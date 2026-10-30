"""Resolve complete declared model inputs before execution; no silent defaults."""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import NoReturn, TypedDict, cast

from src.equipment import OwnedAsset, validate_estate
from src.pathways_v6 import PathwaySpec
from src.portfolios_v7 import CHHHS, TCHHS
from src.statewide import Parameters

# Draw-count guard bounds; documented in the run-recipe contract.
_MIN_DRAWS = 2
_MAX_DRAWS = 1_000_000


class _OwnedAssetDocument(TypedDict):
    """Declared shape of one owned-asset record in the equipment-estate source."""

    site: str
    strategy: str
    remaining_life_years: int


class _ParametersDocument(TypedDict):
    """Declared shape of the parameter source document accepted by ``Parameters``."""

    equipment_cost: float
    life_years: float
    discount: float
    check_minutes: float
    loaded_hour: float
    support: float
    training: float
    workflow_per_call: float
    calls_per_pilot_site: float
    birth_growth: float
    state_uptake: float
    reliability: float
    odds_ratio: float
    case_mix: tuple[float, float, float]
    baseline_transfer: tuple[float, float, float]
    rescue_rate: float
    rescue_premium: float
    road_cost: float
    air_multiplier: float
    marginal_fraction: float
    downstream_delta: float
    family_delta: float
    hub_annual_cost: float
    capacity_threshold: float
    capacity_step_cost: float
    mode_air_shift: float
    include_capital: bool


class _PathwaySpecDocument(TypedDict):
    """Declared shape of the pathway source document accepted by ``PathwaySpec``."""

    phone_delay_share: float
    video_delay_share: float
    extra_rescue: float
    endpoint: str
    local_coordination_per_call: float
    hub_minutes_per_call: float
    hub_hourly_rate: float
    hub_spare_hours: float
    hub_block_hours: float
    hub_block_cost: float
    hospital_marginal_fraction: float
    hospital_resource_multiplier: float
    local_care_multiplier: float
    extra_pre_rescue_cost: float
    rescue_receiving_premium: float


def strict_json(path: Path) -> dict[str, object]:
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

    parsed = cast(
        "object", json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs, parse_constant=nonfinite)
    )
    if not isinstance(parsed, dict):
        msg = "Configuration document must be an object"
        raise TypeError(msg)
    return cast("dict[str, object]", parsed)


def exact_keys(value: object, expected: set[str], label: str) -> None:
    """Require exactly the declared keys on a configuration document.

    Raises:
        ValueError: If the value is not an object or its keys differ.
    """
    if not isinstance(value, dict) or set(cast("dict[str, object]", value)) != expected:
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

    def snapshot(self) -> dict[str, object]:
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
    docs: dict[str, dict[str, object]] = {}
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
    owned_raw = docs["equipment_estate"]["owned_assets"]
    if not isinstance(owned_raw, list):
        msg = "Owned assets must be a list"
        raise TypeError(msg)
    owned: list[OwnedAsset] = []
    for item in cast("list[object]", owned_raw):
        exact_keys(item, {"site", "strategy", "remaining_life_years"}, "Owned asset")
        owned.append(OwnedAsset(**cast("_OwnedAssetDocument", item)))
    assets = tuple(owned)
    validate_estate(assets)
    with (root / "data/births_queensland_2022.csv").open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        known_sites = {row["facility"] for row in reader} | set(CHHHS) | set(TCHHS)
    if any(asset.site not in known_sites for asset in assets):
        msg = "Unknown site in owned equipment estate"
        raise ValueError(msg)
    run = cast("dict[str, object]", recipe["run"])
    exact_keys(run, {"draws", "seed", "portfolios"}, "Run controls")
    draws_raw = run["draws"]
    if type(draws_raw) is not int or not _MIN_DRAWS <= draws_raw <= _MAX_DRAWS:
        msg = "Draw count must be an integer in 2..1000000"
        raise ValueError(msg)
    seed_raw = run["seed"]
    if type(seed_raw) is not int or seed_raw < 0:
        msg = "Seed must be a nonnegative integer"
        raise ValueError(msg)
    portfolios_raw = run["portfolios"]
    portfolios = cast("list[object]", portfolios_raw) if isinstance(portfolios_raw, list) else None
    if (
        portfolios is None
        or not portfolios
        or any(not isinstance(k, str) for k in portfolios)
        or len(set(portfolios)) != len(portfolios)
        or set(portfolios) - {"pilot", "chhhs", "chhhs_tchhs", "spokes"}
    ):
        msg = "Unknown, empty or repeated portfolio"
        raise ValueError(msg)
    p = Parameters(**cast("_ParametersDocument", cast("object", docs["parameters"])))
    s = PathwaySpec(**cast("_PathwaySpecDocument", cast("object", docs["pathways"])))
    if any(a.remaining_life_years > p.life_years for a in assets):
        msg = "Remaining asset life exceeds equipment life"
        raise ValueError(msg)
    hashes = {f.relative_to(root).as_posix(): hashlib.sha256(f.read_bytes()).hexdigest() for f in sources}
    digest = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()
    return ResolvedConfiguration(
        p,
        s,
        assets,
        draws_raw,
        seed_raw,
        tuple(k for k in portfolios if isinstance(k, str)),
        hashes,
        digest,
    )
