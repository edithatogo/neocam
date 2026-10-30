"""Legacy single-site panda model retained for historical reproduction."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class ModelInputs:
    """Declared legacy model inputs; every value is an assumption, not an observation."""

    sites: int = 3
    consultations_per_site: float = 12.5
    equipment_cost_per_site: float = 10_000.0
    equipment_life_years: float = 5.0
    weekly_check_minutes: float = 10.0
    loaded_staff_cost_per_hour: float = 85.0
    annual_support_per_site: float = 300.0
    incremental_video_cost_per_consult: float = 75.0
    road_share: float = 25 / 45
    rotary_share: float = 9 / 45
    fixed_share: float = 11 / 45
    road_cost: float = 4_000.0
    rotary_cost: float = 25_000.0
    fixed_cost: float = 18_000.0
    downstream_cost_difference: float = 4_000.0
    family_cost_per_transfer: float = 1_500.0
    usual_transfer_probability: float = 0.65
    video_transfer_odds_ratio: float = 0.70
    nep_2026_27: float = 7_418.0
    wtp_per_qaly: float = 50_000.0


def odds_to_probability(p0: float, odds_ratio: float) -> float:
    """Convert a baseline probability to a post-odds-ratio probability.

    Returns:
        The converted probability, unchanged at the degenerate endpoints.

    Raises:
        ValueError: If the baseline probability or odds ratio is out of range.
    """
    if not 0 <= p0 <= 1:
        msg = "p0 must be between zero and one"
        raise ValueError(msg)
    if odds_ratio <= 0:
        msg = "odds_ratio must be positive"
        raise ValueError(msg)
    if p0 in {0.0, 1.0}:
        return p0
    return (odds_ratio * p0) / (1 - p0 + odds_ratio * p0)


def annual_programme_cost(x: ModelInputs) -> dict[str, float]:
    """Return the legacy annual programme cost components."""
    consultations = x.sites * x.consultations_per_site
    annualised_equipment = x.sites * x.equipment_cost_per_site / x.equipment_life_years
    checks = x.sites * 52 * (x.weekly_check_minutes / 60) * x.loaded_staff_cost_per_hour
    support = x.sites * x.annual_support_per_site
    consult = consultations * x.incremental_video_cost_per_consult
    cash_continuation = checks + support + consult
    return {
        "consultations": consultations,
        "annualised_equipment": annualised_equipment,
        "checks": checks,
        "support": support,
        "incremental_video_workflow": consult,
        "cash_continuation": cash_continuation,
        "total_economic": annualised_equipment + cash_continuation,
    }


def weighted_transfer_cost(x: ModelInputs) -> float:
    """Return the transport-weighted transfer cost under the declared mode shares.

    Raises:
        ValueError: If the declared transport shares do not sum to one.
    """
    shares = x.road_share + x.rotary_share + x.fixed_share
    if not math.isclose(shares, 1.0, abs_tol=1e-9):
        msg = "transport shares must sum to one"
        raise ValueError(msg)
    return (
        x.road_share * x.road_cost
        + x.rotary_share * x.rotary_cost
        + x.fixed_share * x.fixed_cost
        + x.downstream_cost_difference
    )


def deterministic_scenario(
    x: ModelInputs,
    transfer_reduction_abs: float | None = None,
    consultations_per_site: float | None = None,
    include_annualised_capital: bool = True,  # ruff: ignore[boolean-default-value-positional-argument, boolean-type-hint-positional-argument] -- published flag
) -> dict[str, float]:
    """Evaluate the legacy deterministic net-saving scenario.

    Returns:
        The legacy deterministic cost and saving components.
    """
    cps = x.consultations_per_site if consultations_per_site is None else consultations_per_site
    xx = ModelInputs(**{**asdict(x), "consultations_per_site": cps})
    p_video = odds_to_probability(xx.usual_transfer_probability, xx.video_transfer_odds_ratio)
    effect = xx.usual_transfer_probability - p_video if transfer_reduction_abs is None else transfer_reduction_abs
    consultations = xx.sites * cps
    avoided = consultations * effect
    gross_system = avoided * weighted_transfer_cost(xx)
    gross_societal = gross_system + avoided * xx.family_cost_per_transfer
    programme = annual_programme_cost(xx)
    cost = programme["total_economic"] if include_annualised_capital else programme["cash_continuation"]
    return {
        "consultations": consultations,
        "transfer_reduction_abs": effect,
        "avoided_transfers": avoided,
        "weighted_transfer_cost": weighted_transfer_cost(xx),
        "programme_cost": cost,
        "net_saving_health_system": gross_system - cost,
        "net_saving_societal": gross_societal - cost,
        "break_even_effect": cost / (consultations * weighted_transfer_cost(xx)),
    }


def clinical_extension(  # ruff: ignore[too-many-arguments, too-many-positional-arguments] -- published model API
    consultations: float,
    probability_incremental_survival: float,
    major_morbidity_share_among_survivors: float = 0.35,
    qalys_without_major_morbidity: float = 25.0,
    qalys_with_major_morbidity: float = 8.0,
    lifetime_cost_without_major_morbidity: float = 50_000.0,
    lifetime_cost_with_major_morbidity: float = 500_000.0,
    wtp_per_qaly: float = 50_000.0,
) -> dict[str, float]:
    """Return the exploratory survival, QALY and lifetime-cost extension.

    Returns:
        The assumed survivor counts, incremental QALYs and net monetary benefit.
    """
    extra_survivors = consultations * probability_incremental_survival
    major = extra_survivors * major_morbidity_share_among_survivors
    no_major = extra_survivors - major
    qalys = major * qalys_with_major_morbidity + no_major * qalys_without_major_morbidity
    costs = major * lifetime_cost_with_major_morbidity + no_major * lifetime_cost_without_major_morbidity
    return {
        "extra_survivors": extra_survivors,
        "extra_survivors_major_morbidity": major,
        "extra_survivors_without_major_morbidity": no_major,
        "incremental_qalys": qalys,
        "incremental_lifetime_costs": costs,
        "net_monetary_benefit": qalys * wtp_per_qaly - costs,
    }


def _lognormal(rng: np.random.Generator, median: float, gsd: float, n: int) -> np.ndarray:
    return rng.lognormal(np.log(median), np.log(gsd), n)


def run_psa(  # ruff: ignore[too-many-locals] -- one linear paired-sampling routine
    n: int = 20_000,
    seed: int = 20261027,
) -> dict[str, Any]:
    """Run the legacy probabilistic scenario and return its summary and histogram.

    Returns:
        The PSA summary and histogram records.
    """
    rng = np.random.default_rng(seed)
    sites = 3
    consultations = sites * rng.triangular(10.0, 12.5, 15.0, n)
    mean, sd = 0.65, 0.15
    concentration = mean * (1 - mean) / (sd**2) - 1
    p0 = rng.beta(mean * concentration, (1 - mean) * concentration, n)
    odds_ratio = np.exp(rng.normal(np.log(0.70), 0.35, n))
    p1 = odds_ratio * p0 / (1 - p0 + odds_ratio * p0)
    effect = p0 - p1

    mode = rng.dirichlet([25.0, 9.0, 11.0], n)
    road_cost = _lognormal(rng, 4_000.0, 1.5, n)
    rotary_cost = _lognormal(rng, 25_000.0, 1.5, n)
    fixed_cost = _lognormal(rng, 18_000.0, 1.5, n)
    downstream = rng.triangular(0.0, 4_000.0, 12_000.0, n)
    transfer_cost = mode[:, 0] * road_cost + mode[:, 1] * rotary_cost + mode[:, 2] * fixed_cost + downstream

    equipment = sites * rng.triangular(9_000.0, 10_000.0, 12_000.0, n) / rng.triangular(3.0, 5.0, 7.0, n)
    checks = sites * 52 * (rng.triangular(5.0, 10.0, 20.0, n) / 60) * rng.triangular(70.0, 85.0, 110.0, n)
    support = sites * rng.triangular(0.0, 300.0, 1_000.0, n)
    workflow = consultations * rng.triangular(25.0, 75.0, 175.0, n)
    programme_cost = equipment + checks + support + workflow

    avoided = consultations * effect
    net = avoided * transfer_cost - programme_cost
    family = avoided * rng.triangular(500.0, 1_500.0, 4_000.0, n)
    societal_net = net + family

    q = np.quantile(net, [0.025, 0.5, 0.975])
    eq = np.quantile(effect, [0.025, 0.5, 0.975])
    bins = np.linspace(float(np.quantile(net, 0.005)), float(np.quantile(net, 0.995)), 21)
    counts, edges = np.histogram(net, bins=bins)
    histogram = [
        {"midpoint": float((edges[i] + edges[i + 1]) / 2), "count": int(counts[i])} for i in range(len(counts))
    ]
    summary = {
        "iterations": int(n),
        "mean_net_saving": float(np.mean(net)),
        "median_net_saving": float(q[1]),
        "net_saving_p025": float(q[0]),
        "net_saving_p975": float(q[2]),
        "probability_cost_saving": float(np.mean(net > 0)),
        "mean_societal_net_saving": float(np.mean(societal_net)),
        "mean_avoided_transfers": float(np.mean(avoided)),
        "mean_programme_cost": float(np.mean(programme_cost)),
        "mean_transfer_cost": float(np.mean(transfer_cost)),
        "transfer_effect_mean": float(np.mean(effect)),
        "transfer_effect_p025": float(eq[0]),
        "transfer_effect_median": float(eq[1]),
        "transfer_effect_p975": float(eq[2]),
    }
    return {"summary": summary, "histogram": histogram}
