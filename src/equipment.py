"""A single explicit ownership estate for retention and constant-price cash budgets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from src.pathways_v6 import PathwaySpec, compare_v6
from src.strategies import KEYS

if TYPE_CHECKING:
    from src.activity import ActivitySpec
    from src.statewide import Parameters, Site

# Remaining installed life is bounded by a fifty-year guard horizon.
_MAX_REMAINING_LIFE_YEARS = 50


@dataclass(frozen=True)
class OwnedAsset:
    """One current installation; remaining life is an assumption, not measured age."""

    site: str
    strategy: str
    remaining_life_years: int

    def __post_init__(self) -> None:
        """Reject malformed asset records before they enter the estate.

        Raises:
            ValueError: If the site, strategy or remaining life is invalid.
        """
        if not isinstance(self.site, str) or not self.site.strip() or self.strategy not in KEYS[1:]:
            msg = "Invalid asset site or configuration"
            raise ValueError(msg)
        if (
            type(self.remaining_life_years) is not int
            or not 0 <= self.remaining_life_years <= _MAX_REMAINING_LIFE_YEARS
        ):
            msg = "Remaining life must be an integer between zero and fifty years"
            raise ValueError(msg)


def validate_estate(assets: tuple[OwnedAsset, ...]) -> None:
    """Reject contradictory ownership records rather than double-count assets.

    Raises:
        ValueError: If a record is untyped or a site is duplicated.
    """
    if any(not isinstance(a, OwnedAsset) for a in assets):
        msg = "Estate requires OwnedAsset records"
        raise ValueError(msg)
    if len({a.site for a in assets}) != len(assets):
        msg = "Duplicate site in equipment estate"
        raise ValueError(msg)


def retained_sites(sites: list[Site], strategy: str, assets: tuple[OwnedAsset, ...]) -> set[str]:
    """Only a compatible existing installation can offset new procurement.

    Returns:
        The set of site names retained for the given strategy.
    """
    validate_estate(assets)
    names = {s.name for s in sites}
    return {a.site for a in assets if a.site in names and a.strategy == strategy and a.remaining_life_years > 0}


def apply_retention(
    result: dict[str, dict[str, Any]], sites: list[Site], assets: tuple[OwnedAsset, ...], strategies: tuple[str, ...]
) -> None:
    """Apply the same known retained-site count used by the purchase schedule.

    Current configuration costs/lives are common across sites. Annualised economic
    comparison excludes existing sunk purchases; future replacement is disclosed
    separately by the cash schedule. No claim that retained equipment is costless.

    Raises:
        ValueError: If the portfolio or strategy list is invalid.
    """
    if not sites or len(set(strategies)) != len(strategies) or any(k not in KEYS[1:] for k in strategies):
        msg = "Invalid retained portfolio or strategies"
        raise ValueError(msg)
    for key in strategies:
        fraction = len(retained_sites(sites, key, assets)) / len(sites)
        item = result[key]
        avoided = item["capital_annualised"] * fraction
        item["capital_annualised"] -= avoided
        item["programme_cost"] -= avoided
        item["incremental_purchase_capital"] = item["full_purchase_capital"] * (1 - fraction)
        item["net_saving"] += avoided
        item["net_with_family_extension"] += avoided


def mixed_cash_budget(  # ruff: ignore[too-many-arguments] -- published budgeting API
    sites: list[Site],
    strategy: str,
    assets: tuple[OwnedAsset, ...],
    parameters: Parameters,
    spec: PathwaySpec,
    *,
    retain: bool = True,
    years: int = 7,
    site_calls: dict | None = None,
    activity: ActivitySpec | None = None,
) -> list[dict]:
    """Schedule new and replacement purchases, without double-counting hub costs.

    Year 1 is the current year; remaining life 2 means replacement at start of
    year 3. Undiscounted constant-price budgets, not allocated savings or revenue.

    Returns:
        One annual purchase and running-cash record per year.

    Raises:
        ValueError: If the estate, years, retention flag or strategy is invalid.
    """
    validate_estate(assets)
    if type(years) is not int or years < 1 or type(retain) is not bool:
        msg = "Positive integer years and boolean retention required"
        raise ValueError(msg)
    life = parameters.life_years
    if not float(life).is_integer():
        msg = "An explicit integer replacement interval is required"
        raise ValueError(msg)
    life = int(life)
    if any(a.remaining_life_years > life for a in assets):
        msg = "Remaining life exceeds configured equipment life"
        raise ValueError(msg)
    if strategy not in KEYS:
        msg = "Unknown strategy"
        raise ValueError(msg)
    out = compare_v6(sites, parameters, spec, site_calls=site_calls, activity=activity)[strategy]
    unit_cost = float(out["full_purchase_capital"][0]) / len(sites)
    owned = {a.site: a for a in assets if a.strategy == strategy} if retain else {}
    first = {s.name: owned[s.name].remaining_life_years if s.name in owned else 0 for s in sites}
    rows = []
    for index in range(years):
        count = sum(index >= start and (index - start) % life == 0 for start in first.values())
        capital = count * unit_cost
        running = float(out["cash_running_cost"][0])
        rows.append({
            "year": index + 1,
            "capital": capital,
            "purchases": count if strategy != "telephone" else 0,
            "new_installations": sum(start == 0 for start in first.values())
            if index == 0 and strategy != "telephone"
            else 0,
            "cash_running": running,
            "hub_cash_capacity": float(out["hub_cash_cost"][0]),
            "cash_expenditure": capital + running,
        })
    return rows
