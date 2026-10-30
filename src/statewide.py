"""HISTORICAL V2-V5 kernel, retained for reproducibility only.

Active evaluation: src.pathways_v6.compare_v6. Do not use evaluate/psa here
for current decisions: this historical implementation contains the superseded
site-count hub charge and net-transfer rescue approximation.

This is not a clinical prediction tool. All current effect and cost projections
are conditional on explicitly labelled, mostly non-local priors.
"""

from __future__ import annotations

import csv
import json
import math
from dataclasses import asdict, dataclass
from numbers import Real
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]

# Calendar-year guard bounds for a birth-year record.
_MIN_YEAR = 1900
_MAX_YEAR = 2100
# Acuity strata and the two sampled non-critical strata in the transfer vector.
_STRATA = 3
_SAMPLED_STRATA = 2
# Allowed scenario bound for the analyst air-mode shift.
_MODE_SHIFT_BOUND = 0.6
# Birth-count cut-offs classifying a site group.
_READINESS_BIRTHS = 20
_REGIONAL_PROXY_BIRTHS = 1000
# Hub capacity charges apply only above this site count.
_HUB_SITE_THRESHOLD = 3
# Draw-count guard bounds.
_MIN_DRAWS = 2
_MAX_DRAWS = 1_000_000


@dataclass(frozen=True)
class Site:
    """One collapsed birth-centre record; geography and group are analyst priors."""

    name: str
    births: int
    year: int
    group: str
    geography: str
    pilot: bool = False

    def __post_init__(self) -> None:
        """Reject malformed site records before they enter economic calculations.

        Raises:
            ValueError: If any site field is missing or outside its allowed set.
        """
        if not isinstance(self.name, str) or not self.name.strip():
            msg = "Site name must be non-empty"
            raise ValueError(msg)
        if type(self.births) is not int or self.births < 0:
            msg = "Births must be a non-negative integer"
            raise ValueError(msg)
        if type(self.year) is not int or not _MIN_YEAR <= self.year <= _MAX_YEAR:
            msg = "Birth year must be an integer in [1900, 2100]"
            raise ValueError(msg)
        if self.group not in {"hub", "scn", "readiness", "regional_proxy", "rural_proxy"}:
            msg = "Unknown site group"
            raise ValueError(msg)
        if self.geography not in {"metro", "regional", "remote"}:
            msg = "Unknown site geography"
            raise ValueError(msg)
        if type(self.pilot) is not bool:
            msg = "Pilot status must be boolean"
            raise ValueError(msg)


@dataclass(frozen=True)
class Parameters:
    """Historical v2-v5 kernel parameters; retained for reproducibility only."""

    equipment_cost: float = 10_000.0
    life_years: float = 5.0
    discount: float = 0.05
    check_minutes: float = 10.0
    loaded_hour: float = 85.0
    support: float = 300.0
    training: float = 400.0
    workflow_per_call: float = 75.0
    calls_per_pilot_site: float = 12.5
    birth_growth: float = 1.0
    state_uptake: float = 0.8
    reliability: float = 0.95
    odds_ratio: float = math.sqrt(0.48)
    case_mix: tuple[float, float, float] = (0.35, 0.50, 0.15)
    baseline_transfer: tuple[float, float, float] = (0.30, 0.65, 0.98)
    rescue_rate: float = 0.05
    rescue_premium: float = 10_000.0
    road_cost: float = 4_000.0
    air_multiplier: float = 1.0
    marginal_fraction: float = 0.50
    downstream_delta: float = 2_000.0
    family_delta: float = 1_500.0
    hub_annual_cost: float = 60_000.0
    capacity_threshold: float = 500.0
    capacity_step_cost: float = 30_000.0
    mode_air_shift: float = 0.0
    include_capital: bool = True

    def __post_init__(self) -> None:  # ruff: ignore[complex-structure, too-many-branches] -- one ordered field-validation pass
        """Validate every declared historical parameter before use.

        Raises:
            TypeError: If a case-mix or transfer sequence has the wrong type.
            ValueError: If any declared value is out of its allowed range.
        """
        if type(self.include_capital) is not bool:
            msg = "include_capital must be boolean"
            raise ValueError(msg)
        for name in ("case_mix", "baseline_transfer"):
            values = getattr(self, name)
            if not isinstance(values, (list, tuple)):
                msg = f"{name} must be a three-value sequence"
                raise TypeError(msg)
            if any((not isinstance(value, Real) or isinstance(value, bool)) for value in values):
                msg = f"{name} values must be numeric, not boolean"
                raise ValueError(msg)
            object.__setattr__(self, name, tuple(values))
        for key, value in asdict(self).items():
            if key in {"case_mix", "baseline_transfer", "include_capital"}:
                continue
            if not isinstance(value, Real) or isinstance(value, bool) or not math.isfinite(value):
                msg = f"{key} must be finite numeric, not boolean"
                raise ValueError(msg)
        for key in ("state_uptake", "reliability", "rescue_rate", "marginal_fraction"):
            if not 0 <= getattr(self, key) <= 1:
                msg = f"{key} must be in [0,1]"
                raise ValueError(msg)
        for key in ("life_years", "odds_ratio", "birth_growth", "capacity_threshold"):
            if getattr(self, key) <= 0:
                msg = f"{key} must be positive"
                raise ValueError(msg)
        for key in (
            "equipment_cost",
            "check_minutes",
            "loaded_hour",
            "support",
            "training",
            "workflow_per_call",
            "calls_per_pilot_site",
            "road_cost",
            "air_multiplier",
            "hub_annual_cost",
            "rescue_premium",
            "capacity_step_cost",
            "discount",
        ):
            if getattr(self, key) < 0:
                msg = f"{key} cannot be negative"
                raise ValueError(msg)
        if len(self.case_mix) != _STRATA or not all(math.isfinite(v) and v >= 0 for v in self.case_mix):
            msg = "case_mix must contain three non-negative finite shares"
            raise ValueError(msg)
        if not math.isclose(sum(self.case_mix), 1.0):
            msg = "case_mix must sum to one"
            raise ValueError(msg)
        if len(self.baseline_transfer) != _STRATA or not all(0 <= v <= 1 for v in self.baseline_transfer):
            msg = "baseline_transfer must contain three probabilities"
            raise ValueError(msg)
        if not -_MODE_SHIFT_BOUND <= self.mode_air_shift <= _MODE_SHIFT_BOUND:
            msg = "mode_air_shift outside scenario bounds"
            raise ValueError(msg)


def load_sites(  # ruff: ignore[complex-structure, too-many-branches] -- one ordered table-reading pass
    path: Path | None = None,
) -> list[Site]:
    """Collapse co-located birth-centre rows; retain every published public birth.

    Returns:
        The collapsed public birth-centre records.

    Raises:
        ValueError: If the birth table is malformed, duplicated or of mixed years.
    """
    cfg = json.loads((ROOT / "data/site_classification.json").read_text())
    totals: dict[str, int] = {}
    years: set[int] = set()
    seen: set[str] = set()
    source = path or ROOT / "data/births_queensland_2022.csv"
    with source.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        columns = set(reader.fieldnames or [])
        if not {"facility", "births", "year"}.issubset(columns):
            msg = "Birth table requires facility, births and year columns"
            raise ValueError(msg)
        for row in reader:
            original_name = row["facility"].strip()
            if not original_name:
                msg = "Birth facility must be non-empty"
                raise ValueError(msg)
            if original_name in seen:
                msg = "duplicate birth facility row"
                raise ValueError(msg)
            seen.add(original_name)
            if "sector" in columns and row["sector"] != "public":
                msg = "Birth table must contain public-sector rows only"
                raise ValueError(msg)
            count, year = int(row["births"]), int(row["year"])
            if count < 0:
                msg = "negative birth count"
                raise ValueError(msg)
            years.add(year)
            name = cfg["aliases"].get(original_name, original_name)
            totals[name] = totals.get(name, 0) + count
    if not totals:
        msg = "Birth table is empty"
        raise ValueError(msg)
    if len(years) != 1:
        msg = "Birth table must contain one year only"
        raise ValueError(msg)
    birth_year = years.pop()
    sites = []
    for name, births in sorted(totals.items()):
        if name in cfg["nicu_anznn_2023"]:
            group = "hub"
        elif name in cfg["scn_anznn_2023"]:
            group = "scn"
        elif births < _READINESS_BIRTHS:
            group = "readiness"
        elif births >= _REGIONAL_PROXY_BIRTHS:
            group = "regional_proxy"
        else:
            group = "rural_proxy"
        geography = (
            "remote"
            if name in cfg["geographic_remote_proxy"]
            else "metro"
            if name in cfg["geographic_metro_proxy"]
            else "regional"
        )
        sites.append(Site(name, births, birth_year, group, geography, name in cfg["pilot_sites"]))
    return sites


def select_sites(sites: list[Site], portfolio: str) -> list[Site]:
    """Select the named portfolio from the collapsed site list.

    Returns:
        The sites belonging to the requested portfolio.

    Raises:
        ValueError: If the portfolio name is unknown.
    """
    if portfolio == "pilot":
        return [s for s in sites if s.pilot]
    if portfolio == "spokes":
        return [s for s in sites if s.group not in {"hub", "readiness"}]
    if portfolio == "rural":
        return [s for s in sites if s.group == "rural_proxy"]
    if portfolio == "readiness":
        return [s for s in sites if s.group == "readiness"]
    if portfolio == "all_public":
        return list(sites)
    msg = f"Unknown portfolio: {portfolio}"
    raise ValueError(msg)


def index_air_cost(base_cpi: float = 115.125, target_cpi: float = 102.03) -> float:
    """AUD18670, assumed calendar2019 prices -> June2026 point prices.

    Convert old2011-12-base annual average to Sep-month2025 base first.
    Rounded published conversion causes minor arithmetic imprecision.

    Returns:
        The point-price air transport anchor.

    Raises:
        ValueError: If either CPI input is non-finite or non-positive.
    """
    if not math.isfinite(base_cpi) or not math.isfinite(target_cpi) or min(base_cpi, target_cpi) <= 0:
        msg = "CPI inputs must be finite and positive"
        raise ValueError(msg)
    return 18_670.0 * target_cpi / (base_cpi * (99.73 / 143.6))


def annuity(capital: float, years: float, rate: float) -> float:
    """Return the annualised capital charge, reducing to straight-line at zero rate.

    Raises:
        ValueError: If the inputs are non-finite, the life is non-positive or costs are negative.
    """
    if not all(math.isfinite(x) for x in (capital, years, rate)) or years <= 0 or min(capital, rate) < 0:
        msg = "Invalid annuity input"
        raise ValueError(msg)
    return capital / years if rate == 0 else capital * rate / -math.expm1(-years * math.log1p(rate))


def funding_ledger(nwau: float, qwau: float | None, nep: float, qep: float | None) -> dict[str, float | None]:
    """Return national and (where available) Queensland benchmark funding.

    Raises:
        ValueError: If a supplied funding input is negative or non-finite.
    """
    for value in (nwau, qwau, nep, qep):
        if value is not None and (not math.isfinite(value) or value < 0):
            msg = "Funding inputs must be non-negative and finite or missing"
            raise ValueError(msg)
    return {
        "national_benchmark": nwau * nep,
        "queensland_benchmark": None if qwau is None or qep is None else qwau * qep,
    }


def mchs_support(year: int) -> str:
    """Return the historical support label for the requested reporting year."""
    return "historical_interface_only" if year in {2024, 2025} else "official_GEN_WAU_export_required"


def _odds(p: np.ndarray, odds_ratio: np.ndarray) -> np.ndarray:
    return odds_ratio * p / (1 - p + odds_ratio * p)


def _base_arrays(p: Parameters, n: int) -> dict[str, np.ndarray]:
    values = {
        k: np.full(n, v, dtype=float)
        for k, v in asdict(p).items()
        if isinstance(v, (float, int)) and not isinstance(v, bool)
    }
    values["case_mix"] = np.tile(p.case_mix, (n, 1))
    values["baseline_transfer"] = np.tile(p.baseline_transfer, (n, 1))
    values["air_anchor"] = np.full(n, index_air_cost() * p.air_multiplier)
    return values


def _site_modes(site: Site, shift: np.ndarray) -> np.ndarray:
    # Analyst geographic priors. NOT actual facility-specific dispatch proportions.
    base = {"metro": (0.85, 0.10, 0.05), "regional": (0.60, 0.25, 0.15), "remote": (0.15, 0.35, 0.50)}[site.geography]
    road = np.clip(base[0] - shift, 0.02, 0.98)
    rotary = (1 - road) * base[1] / (base[1] + base[2])
    return np.column_stack((road, rotary, 1 - road - rotary))


def _kernel(  # ruff: ignore[too-many-locals] -- published historical kernel kept linear
    sites: list[Site],
    p: Parameters,
    x: dict[str, np.ndarray],
) -> dict[str, np.ndarray]:
    """Evaluate the historical per-site kernel on the shared draws.

    Returns:
        The historical per-site kernel result arrays.
    """
    n = len(x["odds_ratio"])
    out = {
        k: np.zeros(n)
        for k in (
            "consultations",
            "avoided_transfers",
            "programme_cost",
            "gross_resource_benefit",
            "family_benefit",
            "cash_running_cost",
        )
    }
    for site in sites:
        if site.pilot:
            calls = x["calls_per_pilot_site"]
        else:
            factor = {"hub": 0.0, "scn": 0.5, "regional_proxy": 0.65, "rural_proxy": 1.0, "readiness": 1.0}[site.group]
            geographic = 1.25 if site.geography == "remote" else 1.0
            calls = (
                site.births
                * (3 * x["calls_per_pilot_site"] / 486)
                * factor
                * geographic
                * x["birth_growth"]
                * x["state_uptake"]
            )
        # Critical cases remain transfers; possible survival benefits are separate.
        p0 = x["baseline_transfer"]
        p1 = p0.copy()
        p1[:, :2] = _odds(p0[:, :2], x["odds_ratio"][:, None])
        effect = np.sum(x["case_mix"] * (p0 - p1), axis=1) * x["reliability"]
        apparent_avoided = calls * effect
        rescue = np.maximum(apparent_avoided, 0) * x["rescue_rate"]
        avoided = apparent_avoided - rescue
        modes = _site_modes(site, x["mode_air_shift"])
        # Both air modes share the source anchor, with assumed mode multipliers.
        allocated_transport = (
            modes[:, 0] * x["road_cost"] + modes[:, 1] * x["air_anchor"] * 1.2 + modes[:, 2] * x["air_anchor"] * 0.9
        )
        marginal_transport = allocated_transport * x["marginal_fraction"]
        benefit = avoided * (marginal_transport + x["downstream_delta"]) - rescue * x["rescue_premium"]
        rate = x["discount"]
        annual_capital = np.divide(x["equipment_cost"], x["life_years"])
        positive = rate > 0
        annual_capital[positive] = (
            x["equipment_cost"][positive]
            * rate[positive]
            / -np.expm1(-x["life_years"][positive] * np.log1p(rate[positive]))
        )
        cash = (
            52 * x["check_minutes"] / 60 * x["loaded_hour"]
            + x["support"]
            + x["training"]
            + calls * x["workflow_per_call"]
        )
        out["consultations"] += calls
        out["avoided_transfers"] += avoided
        out["programme_cost"] += cash + (annual_capital if p.include_capital else 0)
        out["cash_running_cost"] += cash
        out["gross_resource_benefit"] += benefit
        out["family_benefit"] += avoided * x["family_delta"]
    if len(sites) > _HUB_SITE_THRESHOLD:
        extra_capacity = np.maximum(
            0, np.ceil((out["consultations"] - x["capacity_threshold"]) / x["capacity_threshold"])
        )
        hub = x["hub_annual_cost"] + extra_capacity * x["capacity_step_cost"]
        out["programme_cost"] += hub
        out["cash_running_cost"] += hub
    out["net_saving"] = out["gross_resource_benefit"] - out["programme_cost"]
    out["societal_net_saving"] = out["net_saving"] + out["family_benefit"]
    return out


def evaluate(sites: list[Site], parameters: Parameters | None = None) -> dict[str, Any]:
    """Evaluate the historical deterministic single-draw scenario.

    Returns:
        The historical deterministic scalar result dictionary.
    """
    p = parameters or Parameters()
    results = _kernel(sites, p, _base_arrays(p, 1))
    result: dict[str, Any] = {k: float(v[0]) for k, v in results.items()}
    result.update({
        "site_count": len(sites),
        "births_2022": sum(s.births for s in sites),
        "interpretation": "conditional scenario, not observed savings",
    })
    return result


def sample_inputs(
    parameters: Parameters | None = None, n: int = 20_000, seed: int = 20261027, effect_mode: str = "attenuated"
) -> dict[str, np.ndarray]:
    """Sample the unchanged v2/v4 common parameter distribution for paired strategies.

    Returns:
        The shared paired-draw input arrays.

    Raises:
        ValueError: If the draw count or effect mode is invalid.
    """
    if type(n) is not int:
        msg = "n must be an integer"
        raise ValueError(msg)
    if n < _MIN_DRAWS or n > _MAX_DRAWS:
        msg = "n must be between 2 and 1000000"
        raise ValueError(msg)
    if effect_mode not in {"attenuated", "published", "null", "skeptical"}:
        msg = "Unsupported effect model"
        raise ValueError(msg)
    p = parameters or Parameters()
    rng = np.random.default_rng(seed)
    x = _base_arrays(p, n)
    x["calls_per_pilot_site"] = rng.triangular(10, 12.5, 15, n) * (p.calls_per_pilot_site / 12.5)
    se = (math.log(0.90) - math.log(0.26)) / (2 * 1.96)
    if effect_mode == "null":
        x["odds_ratio"] = np.ones(n)
    else:
        attenuation = 1 if effect_mode == "published" else 0.5 if effect_mode == "attenuated" else 0
        # .35 is an analyst transportability SD; not a fitted meta-analytic variance.
        centre = math.log(p.odds_ratio) if effect_mode == "attenuated" else attenuation * math.log(0.48)
        x["odds_ratio"] = np.exp(rng.normal(centre, math.sqrt((attenuation * se) ** 2 + 0.35**2), n))
    x["baseline_transfer"] = np.column_stack([
        rng.beta(prob * 20, (1 - prob) * 20, n) if 0 < prob < 1 and j < _SAMPLED_STRATA else np.full(n, prob)
        for j, prob in enumerate(p.baseline_transfer)
    ])
    shares = np.asarray(p.case_mix)
    active = shares > 0
    x["case_mix"] = np.zeros((n, 3))
    x["case_mix"][:, active] = rng.dirichlet(shares[active] * 20, n)
    x["reliability"] = rng.beta(19, 1, n) * (p.reliability / 0.95)
    x["reliability"] = np.clip(x["reliability"], 0, 1)
    x["rescue_rate"] = np.clip(rng.beta(1, 19, n) * (p.rescue_rate / 0.05), 0, 1)
    x["rescue_premium"] = rng.triangular(0, 10000, 30000, n) * p.rescue_premium / 10000
    x["air_anchor"] = rng.lognormal(math.log(index_air_cost()), 0.35, n) * p.air_multiplier
    x["road_cost"] = rng.triangular(2000, 4000, 8000, n) * p.road_cost / 4000
    x["marginal_fraction"] = np.clip(rng.beta(2, 2, n) * p.marginal_fraction / 0.5, 0, 1)
    # Retained babies may increase local costs: negative differences are permitted.
    x["downstream_delta"] = rng.triangular(-4000, 2000, 10000, n) + (p.downstream_delta - 2000)
    x["family_delta"] = rng.triangular(0, 1500, 4000, n) * p.family_delta / 1500
    x["equipment_cost"] = rng.triangular(8000, 10000, 15000, n) * p.equipment_cost / 10000
    x["life_years"] = rng.triangular(3, 5, 7, n) * p.life_years / 5
    x["check_minutes"] = rng.triangular(5, 10, 20, n) * p.check_minutes / 10
    x["support"] = rng.triangular(0, 300, 1000, n) * p.support / 300
    x["training"] = rng.triangular(100, 400, 1200, n) * p.training / 400
    x["workflow_per_call"] = rng.triangular(0, 75, 175, n) * p.workflow_per_call / 75
    x["birth_growth"] = rng.triangular(0.8, 1, 1.2, n) * p.birth_growth
    x["mode_air_shift"] = np.clip(rng.normal(p.mode_air_shift, 0.10, n), -0.6, 0.6)
    return x


def psa(
    sites: list[Site],
    n: int = 20_000,
    seed: int = 20261027,
    parameters: Parameters | None = None,
    effect_mode: str = "attenuated",
) -> dict[str, Any]:
    """Common state-wide draws preserve systematic uncertainty at all scales.

    Returns:
        The PSA summary and the shared draw arrays.
    """
    p = parameters or Parameters()
    x = sample_inputs(p, n=n, seed=seed, effect_mode=effect_mode)
    draws = _kernel(sites, p, x)
    draws["effect_or"] = x["odds_ratio"]
    draws["marginal_fraction"] = x["marginal_fraction"]
    draws["air_anchor"] = x["air_anchor"]
    draws["downstream_delta"] = x["downstream_delta"]
    draws["calls_per_pilot_site"] = x["calls_per_pilot_site"]
    q = np.quantile(draws["net_saving"], [0.025, 0.5, 0.975])
    prob = float(np.mean(draws["net_saving"] > 0))
    # Cost-only EVPI is not a valuation of the unquantified clinical consequences.
    evpi = float(np.mean(np.maximum(draws["net_saving"], 0)) - max(np.mean(draws["net_saving"]), 0))
    return {
        "summary": {
            "iterations": n,
            "seed": seed,
            "effect_mode": effect_mode,
            "mean": float(np.mean(draws["net_saving"])),
            "median": float(q[1]),
            "lower": float(q[0]),
            "upper": float(q[2]),
            "probability_cost_saving": prob,
            "mcse_probability": math.sqrt(prob * (1 - prob) / n),
            "mean_avoided_transfers": float(np.mean(draws["avoided_transfers"])),
            "mean_consultations": float(np.mean(draws["consultations"])),
            "mean_programme_cost": float(np.mean(draws["programme_cost"])),
            "annual_cost_only_evpi": max(evpi, 0),
            "interpretation": "conditional researcher-prior PSA; not an empirical posterior",
        },
        "draws": draws,
    }


def survival_extension(  # ruff: ignore[too-many-arguments, too-many-positional-arguments] -- published exploratory API
    consultations: float,
    survival_gain: float,
    major_share: float,
    discount: float = 0.05,
    years: int = 40,
    utility_no_major: float = 0.9,
    utility_major: float = 0.5,
    annual_cost_no_major: float = 1000,
    annual_cost_major: float = 20000,
) -> dict[str, float]:
    """Exploratory survival/morbidity frontier; all effects/utilities/costs assumed.

    Forty-year constant survival is a scenario, not a fitted survival model.
    No value judgement about disability or lifetime clinical benefit is implied.

    Returns:
        The assumed survivor counts, QALYs and lifetime costs.

    Raises:
        ValueError: If a probability, utility, cost or horizon is invalid.
    """
    vals = (
        consultations,
        survival_gain,
        major_share,
        discount,
        utility_no_major,
        utility_major,
        annual_cost_no_major,
        annual_cost_major,
    )
    if not all(math.isfinite(v) for v in vals) or consultations < 0 or years <= 0 or discount < 0:
        msg = "Invalid survival scenario"
        raise ValueError(msg)
    if not all(0 <= v <= 1 for v in (survival_gain, major_share, utility_no_major, utility_major)):
        msg = "Probabilities and utilities must lie in [0,1]"
        raise ValueError(msg)
    if min(annual_cost_no_major, annual_cost_major) < 0:
        msg = "Negative annual cost"
        raise ValueError(msg)
    pv = sum((1 + discount) ** -y for y in range(1, years + 1))
    extra = consultations * survival_gain
    major = extra * major_share
    qalys = pv * (major * utility_major + (extra - major) * utility_no_major)
    costs = pv * (major * annual_cost_major + (extra - major) * annual_cost_no_major)
    return {"extra_survivors": extra, "major_morbidity_survivors": major, "qalys": qalys, "costs": costs}


def budget_impact(
    sites: list[Site],
    years: int = 5,
    replacement: bool = True,  # ruff: ignore[boolean-default-value-positional-argument, boolean-type-hint-positional-argument] -- published flag
    parameters: Parameters | None = None,
) -> list[dict[str, float]]:
    """Return the historical annual budget-impact cash schedule.

    Raises:
        ValueError: If the horizon is not positive.
    """
    if years < 1:
        msg = "years must be positive"
        raise ValueError(msg)
    p = parameters or Parameters()
    r = evaluate(sites, p)
    records = []
    for year in range(1, years + 1):
        capital = len(sites) * p.equipment_cost if replacement and (year - 1) % max(1, round(p.life_years)) == 0 else 0
        cash = capital + r["cash_running_cost"]
        records.append({
            "year": year,
            "cash_expenditure": cash,
            "capital": capital,
            "resource_net_saving_excluding_funding": r["gross_resource_benefit"] - cash,
        })
    return records
