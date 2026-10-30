# ruff: ignore[implicit-namespace-package] -- scripts/ is a namespace package run via python -m
"""Reproducible v6 pathway analyses. No learned surrogate or new patient data."""

from __future__ import annotations

import csv
import itertools
import json
import sys
from dataclasses import asdict, replace
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict, cast

import numpy as np

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.pathways_v6 import (  # ruff: ignore[module-import-not-at-top-of-file] -- import requires ROOT on sys.path
    NEP26,
    WEIGHTS,
    PathwaySpec,
    cash_budget,
    compare_v6,
    hub_cost,
    sample_v6,
)
from src.statewide import (  # ruff: ignore[module-import-not-at-top-of-file] -- import requires ROOT on sys.path
    Parameters,
    evaluate,
    load_sites,
    select_sites,
)
from src.strategies import (  # ruff: ignore[module-import-not-at-top-of-file] -- import requires ROOT on sys.path
    KEYS,
    summarise,
)

OUT = ROOT / "outputs/v6"
OUT.mkdir(exist_ok=True, parents=True)
PILOT_SITE_LIMIT = 3  # a hub charge applies once the portfolio exceeds the three-site pilot


class SummaryRow(TypedDict):
    """One strategy's paired-draw summary inside a PSA scenario."""

    mean: float
    lower: float
    median: float
    upper: float
    p_saving_vs_telephone: float
    p_optimal: float
    expected_regret: float
    mean_programme_cost: float
    mean_avoided_transfers: float


class PairwiseRow(TypedDict):
    """One strategy-pair comparison row inside a PSA scenario."""

    a: str
    b: str
    mean_incremental_saving_a_vs_b: float
    p_a_more_saving: float
    lower: float
    upper: float


class ConservationRecord(TypedDict):
    """One cohort-conservation check row."""

    portfolio: str
    scenario: str
    max_cohort_residual: float
    finite: bool


class AnalysisMetadata(TypedDict):
    """The results_v6.json document assembled by this driver."""

    version: str
    seed: int
    draws: int
    clinical_evidence: str
    primary_endpoint: str
    hospital_prices: str
    independent_subagent_panel: str
    parameters: dict[str, object]
    pathway_spec: dict[str, object]
    deterministic: dict[str, dict[str, dict[str, float]]]
    psa: dict[str, dict[str, object]]
    analysis_counts: dict[str, int]
    checks: dict[str, object]


def write(name: str, rows: Sequence[Mapping[str, object]]) -> None:
    """Write one CSV table when there are rows to record."""
    if rows:
        with (OUT / name).open("w", newline="") as f:
            w: csv.DictWriter[str] = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)


def floats(d: Mapping[str, np.ndarray]) -> dict[str, float]:
    """Take the first element of each value array as a plain float.

    Returns:
        Mapping of each key to its first element as a float.
    """
    return {k: float(cast("float", v[0])) for k, v in d.items()}


def main() -> None:  # ruff: ignore[complex-structure, too-many-branches, too-many-locals, too-many-statements] -- one linear reproducible pipeline
    """Run the v6 deterministic, PSA, sensitivity and conservation analyses."""
    p = Parameters()
    s = PathwaySpec()
    all_sites = load_sites()
    portfolios = {k: select_sites(all_sites, k) for k in ["pilot", "spokes"]}
    metadata: AnalysisMetadata = {
        "version": "6.0.0",
        "seed": 20261028,
        "draws": 20000,
        "clinical_evidence": "Full-text completion is partial; no updated empirical OR",
        "primary_endpoint": "eventual transfer; delayed timing partition is assumed",
        "hospital_prices": "Unadjusted NEP episode prototypes; not actual clinical DRGs or marginal cash prices",
        "independent_subagent_panel": "not run; no available runner",
        "parameters": asdict(p),
        "pathway_spec": asdict(s),
        "deterministic": {},
        "psa": {},
        "analysis_counts": {},
        "checks": {},
    }
    deterministic: list[dict[str, object]] = []
    bridge: list[dict[str, object]] = []
    pathway_counts: list[dict[str, object]] = []
    budget: list[dict[str, object]] = []
    psa_rows: list[dict[str, object]] = []
    pairs: list[dict[str, object]] = []
    conservation: list[ConservationRecord] = []
    for portfolio, sites in portfolios.items():
        d = compare_v6(sites, p, s)
        metadata["deterministic"][portfolio] = {k: floats(v) for k, v in d.items()}
        for k, a in d.items():
            row: dict[str, object] = {"portfolio": portfolio, "strategy": k, **floats(a)}
            deterministic.append(row)
            pathway_counts.append({
                z: row[z]
                for z in [
                    "portfolio",
                    "strategy",
                    "consultations",
                    "immediate_transfers",
                    "initially_local",
                    "delayed_rescues",
                    "final_local",
                    "eventual_transfers",
                    "conditional_rescue_risk",
                    "avoided_transfers",
                ]
            })
        old = evaluate(sites, p)
        old_consultations = cast("float", old["consultations"])
        old_net_saving = cast("float", old["net_saving"])
        old_hub = (
            0
            if len(sites) <= PILOT_SITE_LIMIT
            else p.hub_annual_cost
            + max(0, cast("float", np.ceil((old_consultations - p.capacity_threshold) / p.capacity_threshold)))
            * p.capacity_step_cost
        )
        bridge.append({
            "portfolio": portfolio,
            "v5_net_saving": old_net_saving,
            "remove_site_count_hub_charge": float(old_hub),
            "after_hub_only_repair": old_net_saving + old_hub,
            "joint_pathway_and_hospital_pricing_change": float(cast("float", d["panda"]["net_saving"][0]))
            - old_net_saving
            - old_hub,
            "v6_net_saving": float(cast("float", d["panda"]["net_saving"][0])),
        })
        for arm, inc in [("panda", False), ("panda", True), ("obsbot", False), ("mobile", True), ("fixed", True)]:
            budget.extend(
                {"portfolio": portfolio, "strategy": arm, "incumbent": inc, **r}
                for r in cash_budget(sites, arm, years=7, incumbent=inc, parameters=p, spec=s)
            )
        structures = [
            ("reference", "attenuated", s, ()),
            ("null", "null", s, ()),
            ("skeptical", "skeptical", s, ()),
            ("published_effect", "published", s, ()),
            ("retain_panda", "attenuated", s, ("panda",)),
            ("prototype_uncertain", "attenuated", s, ()),
            ("initial_decision_endpoint", "attenuated", replace(s, endpoint="initial"), ()),
            ("video_delays_more", "attenuated", replace(s, video_delay_share=0.20), ()),
            ("excess_rescue_2pct_retained", "attenuated", replace(s, extra_rescue=0.02), ()),
            ("no_hospital_offset", "attenuated", replace(s, hospital_marginal_fraction=0), ()),
            ("higher_local_burden", "attenuated", replace(s, local_care_multiplier=1.5), ()),
        ]
        for name, mode, ss, sunk in structures:
            x, e = sample_v6(p, ss, n=20000, seed=20261028, effect_mode=mode)
            overrides = {}
            if name == "prototype_uncertain":
                rng = np.random.default_rng(62026)
                overrides = {
                    "obsbot": {
                        "installed_cost": rng.triangular(2500, 4500, 10000, 20000) * x["equipment_cost"] / 10000,
                        "reliability": x["reliability"] * rng.triangular(0.65, 0.95, 1.0, 20000),
                    }
                }
            r = compare_v6(sites, p, ss, inputs=x, structural_draws=e, sunk=sunk, overrides=overrides)
            summ = summarise(r)
            metadata["psa"][portfolio + "_" + name] = summ
            summary_rows = cast("dict[str, SummaryRow]", summ["summary"])
            pairwise_rows = cast("list[PairwiseRow]", summ["pairwise"])
            for k, a in summary_rows.items():
                psa_rows.append({"portfolio": portfolio, "scenario": name, "strategy": k, **a})
            pairs.extend({"portfolio": portfolio, "scenario": name, **pr} for pr in pairwise_rows)
            errs = [
                float(
                    cast(
                        "float",
                        np.max(
                            np.abs(
                                a["immediate_transfers"] + a["delayed_rescues"] + a["final_local"] - a["consultations"]
                            )
                        ),
                    )
                )
                for a in r.values()
            ]
            conservation.append({
                "portfolio": portfolio,
                "scenario": name,
                "max_cohort_residual": max(errs),
                "finite": all(np.all(np.isfinite(v)) for a in r.values() for v in a.values()),
            })
            if name in {"reference", "prototype_uncertain"}:
                np.savez_compressed(
                    OUT / (portfolio + "_" + name + "_draws.npz"),
                    allow_pickle=True,
                    **{k + "_net": a["net_saving"] for k, a in r.items()},
                    panda_rescue=r["panda"]["delayed_rescues"],
                    panda_hours=r["panda"]["hub_hours"],
                )
    # Decision-relevant deterministic sensitivity: no frequencies represented as priors.
    axes = [
        ("odds_ratio", 0.35, 1.30, "p"),
        ("calls_per_pilot_site", 5, 25, "p"),
        ("marginal_fraction", 0.1, 1.0, "p"),
        ("life_years", 3, 7, "p"),
        ("hub_minutes_per_call", 0, 60, "s"),
        ("hub_hourly_rate", 100, 350, "s"),
        ("video_delay_share", 0, 0.3, "s"),
        ("extra_rescue", 0, 0.1, "s"),
        ("hospital_marginal_fraction", 0, 1, "s"),
        ("local_care_multiplier", 0.7, 2, "s"),
        ("extra_pre_rescue_cost", 0, 10000, "s"),
        ("rescue_receiving_premium", 0, 30000, "s"),
    ]
    one: list[dict[str, object]] = []
    for portfolio, sites in portfolios.items():
        for name, lo, hi, kind in axes:
            for v in np.linspace(lo, hi, 21):
                pp = replace(p, **{name: float(v)}) if kind == "p" else p
                ss = replace(s, **{name: float(v)}) if kind == "s" else s
                r = compare_v6(sites, pp, ss)
                winner = max(KEYS, key=lambda k: cast("float", r[k]["net_saving"][0]))
                for k, a in r.items():
                    one.append({
                        "portfolio": portfolio,
                        "parameter": name,
                        "value": float(v),
                        "strategy": k,
                        "net_saving": float(cast("float", a["net_saving"][0])),
                        "winner": winner,
                    })
    two: list[dict[str, object]] = []
    grids = [
        (
            "effect_local_burden",
            "odds_ratio",
            np.linspace(0.35, 1.3, 21),
            "local_care_multiplier",
            np.linspace(0.7, 2, 21),
        ),
        ("effect_rescue", "odds_ratio", np.linspace(0.35, 1.3, 21), "extra_rescue", np.linspace(0, 0.1, 21)),
        (
            "activity_hubtime",
            "calls_per_pilot_site",
            np.linspace(5, 25, 21),
            "hub_minutes_per_call",
            np.linspace(0, 60, 21),
        ),
    ]
    for portfolio, sites in portfolios.items():
        for name, xname, xs, yname, ys in grids:
            for xx, yy in itertools.product(xs, ys):
                rr = compare_v6(sites, replace(p, **{xname: float(xx)}), replace(s, **{yname: float(yy)}))
                winner = max(KEYS, key=lambda k: cast("float", rr[k]["net_saving"][0]))
                two.append({
                    "portfolio": portfolio,
                    "grid": name,
                    "x_name": xname,
                    "x_value": float(xx),
                    "y_name": yname,
                    "y_value": float(yy),
                    "winner": winner,
                    **{k + "_net": float(cast("float", a["net_saving"][0])) for k, a in rr.items()},
                })
    joint: list[dict[str, object]] = []
    for effect, burden, rescue, minutes in itertools.product(
        np.linspace(0.4, 1.2, 5), np.linspace(0.7, 1.8, 5), np.linspace(0, 0.1, 5), np.linspace(0, 45, 5)
    ):
        r = compare_v6(
            portfolios["pilot"],
            replace(p, odds_ratio=float(effect)),
            replace(
                s, local_care_multiplier=float(burden), extra_rescue=float(rescue), hub_minutes_per_call=float(minutes)
            ),
        )
        winner = max(KEYS, key=lambda k: cast("float", r[k]["net_saving"][0]))
        joint.append({
            "effect": float(effect),
            "local_burden": float(burden),
            "excess_rescue": float(rescue),
            "hub_minutes": float(minutes),
            "winner": winner,
            **{k + "_net": float(cast("float", a["net_saving"][0])) for k, a in r.items()},
        })
    threshold: list[dict[str, object]] = []
    for calls in [0, 12.5, 37.5, 100, 399.9, 400, 400.1, 800, 1114.543, 1200]:
        h = hub_cost(np.array([calls]), np.array([15.0]), s)
        threshold.append({
            "consultations": calls,
            "sites": "not used",
            **{k: float(cast("float", v[0])) for k, v in h.items()},
        })
    checks: dict[str, object] = {
        "max_mass_residual": max(c["max_cohort_residual"] for c in conservation),
        "all_outputs_finite": all(c["finite"] for c in conservation),
    }
    for name, rows in [
        ("deterministic.csv", deterministic),
        ("pathways.csv", pathway_counts),
        ("v5_v6_bridge.csv", bridge),
        ("budget.csv", budget),
        ("psa_summary.csv", psa_rows),
        ("pairwise.csv", pairs),
        ("conservation.csv", conservation),
        ("one_way.csv", one),
        ("two_way.csv", two),
        ("four_way.csv", joint),
        ("hub_thresholds.csv", threshold),
    ]:
        write(name, rows)
    write(
        "hospital_prototypes.csv",
        [
            {
                "drg": k,
                "unadjusted_weight": v,
                "nep26": NEP26,
                "episode_price": v * NEP26,
                "mapping_status": "Illustrative episode prototype; not patient-level grouping",
                "source": "IHACPA NEP Determination 2026-27 Appendix A, PDF pp82-83",
            }
            for k, v in WEIGHTS.items()
        ],
    )
    metadata["analysis_counts"] = {
        "psa_structures": len(metadata["psa"]),
        "draws_each": 20000,
        "one_way_arm_rows": len(one),
        "two_way_points": len(two),
        "four_way_points": len(joint),
        "budget_rows": len(budget),
    }
    metadata["checks"] = checks
    _ = (OUT / "results_v6.json").write_text(json.dumps(metadata, indent=2))
    print(  # ruff: ignore[print] -- CLI analysis summary goes to stdout
        json.dumps({"counts": metadata["analysis_counts"], "checks": checks, "bridge": bridge}, indent=2)
    )


if __name__ == "__main__":
    main()
