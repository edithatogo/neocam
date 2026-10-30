"""Explicit annual care pathways and incremental video-workload costs.

This is an early cost-consequence model, not a clinical prediction model. The
national-price episode prototypes below are pricing scenarios, not clinical DRG
assignments or validated NWAU calculations. Historical v5 results remain in their
original modules; this module does not call the legacy site-count cost kernel.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from numbers import Real
from typing import Any

import numpy as np

from src.activity import ActivitySpec
from src.statewide import Parameters, Site, _base_arrays, _site_modes, sample_inputs
from src.strategies import KEYS, STRATEGIES, _validate_overrides

NEP26 = 7418.0
# NEP Determination 2026-27, Appendix H, PDF pp82-83. Text-extracted rows.
WEIGHTS = {"P68D": 0.6454, "P68B": 1.4581, "P60B": 0.8224, "P60A": 1.6530, "P06B": 7.1826}
# A baseline-transfer array is draw-by-stratum over the three acuity strata.
_TRANSFER_NDIM = 2
_TRANSFER_STRATA = 3


@dataclass(frozen=True)
class PathwaySpec:
    """All new assumptions are explicit and separate from historical parameters."""

    phone_delay_share: float = 0.05
    video_delay_share: float = 0.05
    extra_rescue: float = 0.0
    endpoint: str = "eventual"
    local_coordination_per_call: float = 25.0
    hub_minutes_per_call: float = 15.0
    hub_hourly_rate: float = 200.0
    hub_spare_hours: float = 100.0
    hub_block_hours: float = 200.0
    hub_block_cost: float = 40000.0
    hospital_marginal_fraction: float = 0.5
    hospital_resource_multiplier: float = 1.0
    local_care_multiplier: float = 1.0
    extra_pre_rescue_cost: float = 2000.0
    rescue_receiving_premium: float = 0.0

    def __post_init__(self) -> None:
        """Reject malformed pathway assumptions before they enter the kernel.

        Raises:
            ValueError: If any declared assumption is negative or out of range.
        """
        for name, value in asdict(self).items():
            if name == "endpoint":
                continue
            if isinstance(value, bool) or not isinstance(value, Real) or not np.isfinite(value) or value < 0:
                msg = f"{name} must be finite non-negative numeric"
                raise ValueError(msg)
        for name in ("phone_delay_share", "video_delay_share", "extra_rescue", "hospital_marginal_fraction"):
            if getattr(self, name) > 1:
                msg = f"{name} must be a probability"
                raise ValueError(msg)
        if self.hub_block_hours <= 0:
            msg = "hub_block_hours must be positive"
            raise ValueError(msg)
        if self.endpoint not in {"eventual", "initial"}:
            msg = "endpoint must be eventual or initial"
            raise ValueError(msg)


def _array(value: float | np.ndarray, name: str, lower: float = 0.0, upper: float = np.inf) -> np.ndarray:
    """Validate finite numeric arrays without accepting booleans as numbers.

    Returns:
        The validated array cast to float.

    Raises:
        ValueError: If the values are non-numeric, non-finite or out of range.
    """
    a = np.asarray(value)
    if a.dtype.kind not in "iuf" or not np.all(np.isfinite(a)) or np.any(a < lower) or np.any(a > upper):
        msg = f"Invalid {name}"
        raise ValueError(msg)
    return a.astype(float, copy=False)


def _column(value: float | np.ndarray, n: int, name: str, upper: float = np.inf) -> np.ndarray:
    a = _array(value, name, upper=upper)
    if a.ndim > 1 or (a.ndim == 1 and a.shape != (n,)):
        msg = f"{name} requires one value per draw"
        raise ValueError(msg)
    return np.broadcast_to(a, (n,))[:, None]


def path_probabilities(  # ruff: ignore[too-many-arguments, too-many-locals] -- published path-partition API
    t0: np.ndarray,
    odds_ratio: np.ndarray,
    reliability: np.ndarray,
    phone_share: float | np.ndarray,
    video_share: float | np.ndarray,
    *,
    extra_rescue: float | np.ndarray = 0.0,
    endpoint: str = "eventual",
) -> dict[str, np.ndarray]:
    """Partition each arm into mutually exclusive immediate, rescue and local paths.

    Primary: the OR changes eventual transfer. The delay share partitions that
    endpoint; it does NOT impose a second transfer penalty. Alternative 'initial'
    interprets the baseline/OR as initial decisions and shares as conditional
    rescue risks. These structures deliberately do not have identical baselines.
    Extra rescue is a separate, explicitly hypothetical shift from video-local
    to delayed transfer. Failed video always follows the telephone branch.

    Returns:
        The immediate, rescue and local path probabilities per arm.

    Raises:
        ValueError: If the baseline, odds ratio, reliability or shares are invalid.
    """
    t = _array(t0, "baseline transfer", upper=1.0)
    if t.ndim != _TRANSFER_NDIM or t.shape[1] != _TRANSFER_STRATA or not len(t):
        msg = "baseline_transfer must have shape (draws, 3)"
        raise ValueError(msg)
    n = len(t)
    odds = _column(odds_ratio, n, "odds ratio")
    if np.any(odds <= 0):
        msg = "odds ratio must be positive"
        raise ValueError(msg)
    r = _column(reliability, n, "reliability", 1.0)
    dp = _column(phone_share, n, "phone delay share", 1.0)
    dv = _column(video_share, n, "video delay share", 1.0)
    extra = _column(extra_rescue, n, "extra rescue", 1.0)
    target = odds * t / (1 - t + odds * t)
    target[:, 2] = t[:, 2]  # No unsupported avoidance credit in critical cases.
    if endpoint == "eventual":
        pi, pr, pl = t * (1 - dp), t * dp, 1 - t
        vi, vr, vl = target * (1 - dv), target * dv, 1 - target
    elif endpoint == "initial":
        pi, pr, pl = t, (1 - t) * dp, (1 - t) * (1 - dp)
        vi, vr, vl = target, (1 - target) * dv, (1 - target) * (1 - dv)
    else:
        msg = "unknown transfer endpoint"
        raise ValueError(msg)
    added = vl * extra
    vr, vl = vr + added, vl - added
    result = {
        "phone_immediate": pi,
        "phone_rescue": pr,
        "phone_local": pl,
        "video_immediate": r * vi + (1 - r) * pi,
        "video_rescue": r * vr + (1 - r) * pr,
        "video_local": r * vl + (1 - r) * pl,
    }
    result["phone_initial_local"] = 1 - pi
    result["video_initial_local"] = 1 - result["video_immediate"]
    for arm in ("phone", "video"):
        initial_local = result[arm + "_initial_local"]
        result[arm + "_conditional_rescue"] = np.divide(
            result[arm + "_rescue"], initial_local, out=np.zeros_like(initial_local), where=initial_local > 0
        )
    return result


def hub_cost(calls: np.ndarray, minutes: np.ndarray, spec: PathwaySpec) -> dict[str, np.ndarray]:
    """Value incremental time; separately price additional paid capacity blocks.

    Returns:
        The hub hours, economic time value and paid capacity blocks.
    """
    hours = _array(calls, "calls") * _array(minutes, "minutes") / 60
    excess = np.maximum(0.0, hours - spec.hub_spare_hours)
    blocks = np.ceil(excess / spec.hub_block_hours)
    return {
        "hours": hours,
        "economic": hours * spec.hub_hourly_rate,
        "cash_capacity": blocks * spec.hub_block_cost,
        "capacity_blocks": blocks,
    }


def hospital_cost(  # ruff: ignore[too-many-arguments, too-many-positional-arguments] -- published cost API
    immediate: np.ndarray,
    rescue: np.ndarray,
    local: np.ndarray,
    origin: np.ndarray,
    receiving: np.ndarray,
    local_episode: np.ndarray,
    extra_pre_rescue: np.ndarray,
) -> np.ndarray:
    """Price disjoint care components; receiving care is never counted twice.

    Returns:
        The per-draw priced hospital resource cost.
    """
    for a in (immediate, rescue, local, origin, receiving, local_episode, extra_pre_rescue):
        _array(a, "hospital component")
    return (immediate + rescue) * (origin + receiving) + local * local_episode + rescue * extra_pre_rescue


def _activity(site: Site, x: dict[str, np.ndarray]) -> np.ndarray:
    if site.pilot:
        return x["calls_per_pilot_site"].copy()
    factor = {"hub": 0.0, "scn": 0.5, "regional_proxy": 0.65, "rural_proxy": 1.0, "readiness": 1.0}[site.group]
    geo = 1.25 if site.geography == "remote" else 1.0
    return site.births * (3 * x["calls_per_pilot_site"] / 486) * factor * geo * x["birth_growth"] * x["state_uptake"]


def _annuity_vector(capital: np.ndarray, life: np.ndarray, rate: np.ndarray) -> np.ndarray:
    result = capital / life
    positive = rate > 0
    result[positive] = capital[positive] * rate[positive] / -np.expm1(-life[positive] * np.log1p(rate[positive]))
    return result


def compare_v6(  # ruff: ignore[complex-structure, too-many-arguments, too-many-branches, too-many-locals, too-many-statements] -- published kernel kept linear
    sites: list[Site],
    parameters: Parameters | None = None,
    spec: PathwaySpec | None = None,
    *,
    inputs: dict[str, np.ndarray] | None = None,
    sunk: tuple[str, ...] = (),
    overrides: dict[str, dict[str, Any]] | None = None,
    structural_draws: dict[str, np.ndarray] | None = None,
    site_calls: dict[str, np.ndarray] | None = None,
    activity: ActivitySpec | None = None,
) -> dict[str, dict[str, np.ndarray]]:
    """Calculate absolute pathways and paired incremental outcomes for all arms.

    Returns:
        Per-strategy absolute pathways and paired incremental outcomes.

    Raises:
        TypeError: If the activity specification is not an ``ActivitySpec``.
        ValueError: If sites, inputs, draws, overrides or sunk strategies are invalid.
    """
    if not sites or len({s.name for s in sites}) != len(sites):
        msg = "non-empty unique sites required"
        raise ValueError(msg)
    if any(k not in KEYS[1:] for k in sunk) or len(set(sunk)) != len(sunk):
        msg = "invalid sunk strategies"
        raise ValueError(msg)
    p, s = parameters or Parameters(), spec or PathwaySpec()
    activity = ActivitySpec() if activity is None else activity
    if not isinstance(activity, ActivitySpec):
        msg = "Activity requires ActivitySpec"
        raise TypeError(msg)
    x = inputs if inputs is not None else _base_arrays(p, 1)
    n = len(x["odds_ratio"])
    for name, value in x.items():
        if name not in {"downstream_delta", "mode_air_shift"}:
            _array(value, name)
        if np.asarray(value).shape != ((n, 3) if name in {"case_mix", "baseline_transfer"} else (n,)):
            msg = f"bad input shape: {name}"
            raise ValueError(msg)
    if not np.allclose(x["case_mix"].sum(axis=1), 1):
        msg = "case-mix rows must sum to one"
        raise ValueError(msg)
    if np.any(x["life_years"] <= 0):
        msg = "positive equipment life required"
        raise ValueError(msg)
    overrides = overrides or {}
    _validate_overrides(overrides, n)
    structural_draws = structural_draws or {}
    allowed = {"delay_share", "hospital_fraction", "hospital_multiplier", "local_multiplier", "pre_rescue"}
    if set(structural_draws) - allowed:
        msg = "unknown structural draw"
        raise ValueError(msg)

    def draw(name: str, default: float, upper: float = np.inf) -> np.ndarray:
        return _column(structural_draws.get(name, default), n, name, upper)[:, 0]

    # A common delay share preserves equal timing in the reference PSA; unequal
    # shares are explicit structural scenarios, not hidden independent draws.
    dp = draw("delay_share", s.phone_delay_share, 1.0)
    dv = np.clip(dp + s.video_delay_share - s.phone_delay_share, 0, 1)
    hf = draw("hospital_fraction", s.hospital_marginal_fraction, 1.0)
    hm = draw("hospital_multiplier", s.hospital_resource_multiplier)
    lm = draw("local_multiplier", s.local_care_multiplier)
    pre = draw("pre_rescue", s.extra_pre_rescue_cost)
    origin = NEP26 * np.array([WEIGHTS["P60B"], WEIGHTS["P60B"], WEIGHTS["P60A"]])[None, :] * hm[:, None]
    receiver = NEP26 * np.array([WEIGHTS["P68D"], WEIGHTS["P68B"], WEIGHTS["P06B"]])[None, :] * hm[:, None]
    local = receiver * lm[:, None]
    # All current sites share stratum probabilities and hospital prototypes.
    # Aggregate exposure once; geography still weights the transport cost by site.
    site_calls = site_calls or {}
    if set(site_calls) - {site.name for site in sites}:
        msg = "Unknown site in activity override"
        raise ValueError(msg)
    total_calls = np.zeros(n)  # Historical name; clinical episodes, not repeat contacts.
    total_contacts = np.zeros(n)
    transport_exposure = np.zeros(n)
    for site in sites:
        calls = _column(site_calls[site.name], n, "site calls")[:, 0] if site.name in site_calls else _activity(site, x)
        calls, contacts = activity.exposures(calls)
        total_contacts += contacts
        transport = np.sum(
            _site_modes(site, x["mode_air_shift"])
            * np.column_stack([x["road_cost"], x["air_anchor"] * 1.15, x["air_anchor"] * 0.85]),
            axis=1,
        )
        total_calls += calls
        transport_exposure += calls * transport * x["marginal_fraction"]
    cohort_weights = total_calls[:, None] * x["case_mix"]
    all_results: dict[str, dict[str, np.ndarray]] = {}
    for strategy in STRATEGIES:
        key, video = strategy.key, strategy.key != "telephone"
        fields = overrides.get(key, {})
        rel = np.broadcast_to(np.asarray(fields.get("reliability", x["reliability"])), (n,)) if video else np.zeros(n)
        paths = path_probabilities(
            x["baseline_transfer"], x["odds_ratio"], rel, dp, dv, extra_rescue=s.extra_rescue, endpoint=s.endpoint
        )
        arm = "video" if video else "phone"
        im, re, lo = (paths[arm + "_" + k] for k in ("immediate", "rescue", "local"))
        names = (
            "consultations",
            "immediate_transfers",
            "delayed_rescues",
            "initially_local",
            "final_local",
            "transport_resource_cost",
            "hospital_benchmark_cost",
            "hospital_resource_cost",
            "origin_benchmark_cost",
            "receiving_benchmark_cost",
            "local_benchmark_cost",
            "pre_rescue_benchmark_cost",
            "rescue_extra_resource_cost",
        )
        out = {k: np.zeros(n) for k in names}
        weights = cohort_weights
        out["consultations"] = total_calls.copy()  # Compatibility alias for episodes.
        out["episodes"] = total_calls.copy()
        out["contacts"] = total_contacts.copy()
        out["immediate_transfers"] = (weights * im).sum(axis=1)
        out["delayed_rescues"] = (weights * re).sum(axis=1)
        out["initially_local"] = (weights * (1 - im)).sum(axis=1)
        out["final_local"] = (weights * lo).sum(axis=1)
        out["transport_resource_cost"] = (x["case_mix"] * (im + re)).sum(axis=1) * transport_exposure
        out["origin_benchmark_cost"] = (weights * (im + re) * origin).sum(axis=1)
        out["receiving_benchmark_cost"] = (weights * (im + re) * receiver).sum(axis=1)
        out["local_benchmark_cost"] = (weights * lo * local).sum(axis=1)
        out["pre_rescue_benchmark_cost"] = (weights * re * pre[:, None]).sum(axis=1)
        out["hospital_benchmark_cost"] = (
            weights * hospital_cost(im, re, lo, origin, receiver, local, pre[:, None])
        ).sum(axis=1)
        out["rescue_extra_resource_cost"] = (weights * re).sum(axis=1) * s.rescue_receiving_premium
        out["hospital_resource_cost"] = out["hospital_benchmark_cost"] * hf
        out["care_resource_cost"] = (
            out["transport_resource_cost"] + out["hospital_resource_cost"] + out["rescue_extra_resource_cost"]
        )
        out["eventual_transfers"] = out["immediate_transfers"] + out["delayed_rescues"]
        out["conditional_rescue_risk"] = np.divide(
            out["delayed_rescues"], out["initially_local"], out=np.zeros(n), where=out["initially_local"] > 0
        )
        out["hospital_price_equivalent_units"] = out["hospital_benchmark_cost"] / NEP26
        zero_names = (
            "capital_annualised",
            "local_ready_cost",
            "local_workflow_cost",
            "hub_hours",
            "hub_resource_cost",
            "hub_cash_cost",
            "hub_capacity_blocks",
            "programme_cost",
            "cash_running_cost",
            "full_purchase_capital",
            "attributed_capital",
            "incremental_purchase_capital",
        )
        out.update({k: np.zeros(n) for k in zero_names})
        if video:
            workflow = np.broadcast_to(np.asarray(fields.get("workflow_per_call", x["workflow_per_call"])), (n,))
            scale = workflow / 75.0  # Explicit split of historical staff allowance, not an extra charge.
            hub = hub_cost(out["contacts"], scale * s.hub_minutes_per_call, s)
            out["hub_hours"], out["hub_resource_cost"], out["hub_cash_cost"] = (
                hub["hours"],
                hub["economic"],
                hub["cash_capacity"],
            )
            out["hub_capacity_blocks"] = hub["capacity_blocks"]
            out["local_workflow_cost"] = out["contacts"] * s.local_coordination_per_call * scale
            out["local_ready_cost"] = len(sites) * (
                52 * x["check_minutes"] / 60 * x["loaded_hour"] + x["support"] + x["training"]
            )
            capital = np.broadcast_to(
                np.asarray(fields.get("installed_cost", x["equipment_cost"] * strategy.installed_cost / 10000)), (n,)
            ).copy() * len(sites)
            life = np.broadcast_to(np.asarray(fields.get("life_years", x["life_years"])), (n,))
            out["full_purchase_capital"] = capital
            out["attributed_capital"] = capital * fields.get("capital_share", 1.0)
            out["incremental_purchase_capital"] = capital.copy() if key not in sunk else np.zeros(n)
            if p.include_capital and key not in sunk:
                out["capital_annualised"] = _annuity_vector(out["attributed_capital"], life, x["discount"])
            out["programme_cost"] = (
                out["capital_annualised"]
                + out["local_ready_cost"]
                + out["local_workflow_cost"]
                + out["hub_resource_cost"]
            )
            # Cash blocks and hourly opportunity cost are alternative ledgers; never summed.
            out["cash_running_cost"] = out["local_ready_cost"] + out["local_workflow_cost"] + out["hub_cash_cost"]
        all_results[key] = out
    base = all_results["telephone"]
    for out in all_results.values():
        out["avoided_transfers"] = base["eventual_transfers"] - out["eventual_transfers"]
        out["hospital_resource_benefit"] = base["hospital_resource_cost"] - out["hospital_resource_cost"]
        out["transport_resource_benefit"] = base["transport_resource_cost"] - out["transport_resource_cost"]
        out["gross_resource_benefit"] = base["care_resource_cost"] - out["care_resource_cost"]
        out["net_saving"] = out["gross_resource_benefit"] - out["programme_cost"]
        out["family_cost_extension"] = out["avoided_transfers"] * x["family_delta"]
        out["net_with_family_extension"] = out["net_saving"] + out["family_cost_extension"]
    return all_results


def sample_v6(
    parameters: Parameters | None = None,
    spec: PathwaySpec | None = None,
    n: int = 20000,
    seed: int = 20261028,
    effect_mode: str = "attenuated",
) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    """Retain shared evidence draws; add labelled analyst structural distributions.

    Returns:
        Paired population input and structural effect draw dictionaries.
    """
    p, s = parameters or Parameters(), spec or PathwaySpec()
    x = sample_inputs(p, n, seed, effect_mode)
    rng = np.random.default_rng(seed + 61000)
    extras = {
        "delay_share": np.clip(rng.beta(1, 19, n) * (s.phone_delay_share / 0.05), 0, 1),
        "hospital_fraction": np.clip(rng.beta(2, 2, n) * (s.hospital_marginal_fraction / 0.5), 0, 1),
        "hospital_multiplier": rng.lognormal(-0.5 * 0.25**2, 0.25, n) * s.hospital_resource_multiplier,
        "local_multiplier": rng.triangular(0.7, 1.0, 1.8, n) * s.local_care_multiplier,
        "pre_rescue": rng.triangular(0, 2000, 6000, n) * (s.extra_pre_rescue_cost / 2000),
    }
    return x, extras


def cash_budget(  # ruff: ignore[too-many-arguments, too-many-positional-arguments] -- published cash-budget API
    sites: list[Site],
    strategy: str = "panda",
    years: int = 7,
    incumbent: bool = False,  # ruff: ignore[boolean-default-value-positional-argument, boolean-type-hint-positional-argument] -- published flag
    remaining_life: int = 2,
    parameters: Parameters | None = None,
    spec: PathwaySpec | None = None,
) -> list[dict[str, float]]:
    """Undiscounted constant-price cash purchases and replacement, no assumed savings.

    Returns:
        One constant-price annual cash record per year.

    Raises:
        ValueError: If the strategy, horizon or replacement interval is invalid.
    """
    p = parameters or Parameters()
    if (
        strategy not in KEYS
        or type(years) is not int
        or years < 1
        or type(remaining_life) is not int
        or remaining_life < 0
    ):
        msg = "Invalid cash-budget specification"
        raise ValueError(msg)
    # Annual budgets require an explicit integer replacement interval, not silent rounding.
    if not float(p.life_years).is_integer() or remaining_life > p.life_years:
        msg = "Integer equipment life and feasible remaining life required"
        raise ValueError(msg)
    out = compare_v6(sites, p, spec, sunk=(strategy,) if incumbent and strategy != "telephone" else ())[strategy]
    life = int(p.life_years)
    first = remaining_life if incumbent else 0
    rows = []
    for y in range(years):
        capital = float(out["full_purchase_capital"][0]) if y >= first and (y - first) % life == 0 else 0.0
        cash = float(out["cash_running_cost"][0])
        rows.append({
            "year": y + 1,
            "capital": capital,
            "cash_running": cash,
            "hub_cash_capacity": float(out["hub_cash_cost"][0]),
            "cash_expenditure": capital + cash,
        })
    return rows
