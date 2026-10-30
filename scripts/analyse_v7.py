# ruff: ignore[implicit-namespace-package] -- scripts/ is a namespace package run via python -m
"""Regional/perspective analysis from the exact model; no learned decisions."""

from __future__ import annotations

import csv
import itertools
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict, Unpack, cast

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import audit_v7, equipment, perspectives_v7, portfolios_v7  # ruff: ignore[module-import-not-at-top-of-file] -- import needs ROOT on sys.path
from src.audit_v7 import (  # ruff: ignore[module-import-not-at-top-of-file] -- import needs ROOT on sys.path
    discounted_health_years,
    required_health_gain,
)
from src.configuration import (  # ruff: ignore[module-import-not-at-top-of-file] -- import needs ROOT on sys.path
    load_configuration,
)
from src.equipment import (  # ruff: ignore[module-import-not-at-top-of-file] -- import needs ROOT on sys.path
    apply_retention,
)
from src.pathways_v6 import (  # ruff: ignore[module-import-not-at-top-of-file] -- import needs ROOT on sys.path
    PathwaySpec,
    compare_v6,
)
from src.perspectives_v7 import (  # ruff: ignore[module-import-not-at-top-of-file] -- import needs ROOT on sys.path
    optimal_probabilities,
    reconcile_ledger,
)
from src.portfolios_v7 import (  # ruff: ignore[module-import-not-at-top-of-file] -- import needs ROOT on sys.path
    CHHHS,
    TCHHS,
    portfolio,
)
from src.statewide import (  # ruff: ignore[module-import-not-at-top-of-file] -- import needs ROOT on sys.path
    Parameters,
    Site,
    _base_arrays,  # ruff: ignore[import-private-name] -- internal base-array builder  # pyright: ignore[reportPrivateUsage]
)
from src.strategies import KEYS  # ruff: ignore[module-import-not-at-top-of-file] -- import needs ROOT on sys.path

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

    from src.activity import ActivitySpec
    from src.equipment import OwnedAsset

# The numerical kernels are untyped in the model package; bind precise call shapes here.
sample_v7 = cast("Callable[..., tuple[dict[str, np.ndarray], dict[str, np.ndarray]]]", audit_v7.sample_v7)
mixed_cash_budget = cast("Callable[..., list[dict[str, object]]]", equipment.mixed_cash_budget)
perspective_regret = cast("Callable[..., dict[str, object]]", perspectives_v7.perspective_regret)
consultation_overrides = cast("Callable[..., dict[str, np.ndarray]]", portfolios_v7.consultation_overrides)
regional_roster = portfolios_v7.regional_roster

OutcomeArrays = dict[str, np.ndarray]
OutcomeTable = dict[str, OutcomeArrays]


OUT = ROOT / "outputs/v12"
PERSPECTIVES = ("health_system", "societal_bounded", "provider_chhhs", "patient_family", "state", "commonwealth")


class CompareOptions(TypedDict, total=False):
    """Optional kernel overrides forwarded to the v6 comparison."""

    inputs: dict[str, np.ndarray] | None
    structural_draws: dict[str, np.ndarray] | None
    site_calls: dict[str, np.ndarray] | None
    overrides: dict[str, dict[str, object]] | None
    activity: ActivitySpec | None


class ScenarioOptions(TypedDict, total=False):
    """Declared structural scenario overrides for one perspective pass."""

    reopened: bool
    readiness_calls: float
    cairns_hub_only: bool
    receiver_share: float
    retrieval_chhhs_share: float
    subsidy_fraction: float
    family_travel_share: float
    funding_response: float
    sunk: tuple[str, ...]
    overrides: dict[str, dict[str, object]]


class CheckRecord(TypedDict):
    """One paired-scenario reconciliation and cohort-error check row."""

    portfolio: str
    scenario: str
    max_perspective_reconciliation_error: float
    max_cohort_error: float


def write(name: str, rows: Sequence[Mapping[str, object]]) -> None:
    """Write one CSV table when there are rows to record."""
    if rows:
        with (OUT / name).open("w", newline="") as f:
            w: csv.DictWriter[str] = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)


def compare_regional(
    sites: list[Site],
    p: Parameters,
    s: PathwaySpec,
    *,
    sunk: tuple[str, ...] = (),
    owned_assets: tuple[OwnedAsset, ...] | None = None,
    **kwargs: Unpack[CompareOptions],
) -> OutcomeTable:
    """Retain known Panda pilot installations, not hypothetical equipment everywhere.

    Returns:
        The compared strategy outcomes for the given regional sites.
    """
    if owned_assets is not None:
        result = compare_v6(sites, p, s, **kwargs)
        apply_retention(result, sites, owned_assets, sunk)
        return result
    other_sunk = tuple(k for k in sunk if k != "panda")
    result = compare_v6(sites, p, s, sunk=other_sunk, **kwargs)
    if "panda" in sunk:
        fraction = sum(site.pilot for site in sites) / len(sites)
        item = result["panda"]
        avoided = item["capital_annualised"] * fraction
        # ruff: ignore[non-augmented-assignment] -- rebinding, not +=, avoids mutating a possibly shared draw array
        item["capital_annualised"] = item["capital_annualised"] - avoided
        # ruff: ignore[non-augmented-assignment] -- rebinding, not +=, avoids mutating a possibly shared draw array
        item["programme_cost"] = item["programme_cost"] - avoided
        item["incremental_purchase_capital"] = item["full_purchase_capital"] * (1 - fraction)
        # ruff: ignore[non-augmented-assignment] -- rebinding, not +=, avoids mutating a possibly shared draw array
        item["net_saving"] = item["net_saving"] + avoided
        # ruff: ignore[non-augmented-assignment] -- rebinding, not +=, avoids mutating a possibly shared draw array
        item["net_with_family_extension"] = item["net_with_family_extension"] + avoided
    return result


def evaluate_perspectives(  # ruff: ignore[too-many-arguments, too-many-locals] -- one explicit per-perspective accounting pass
    sites: list[Site],
    p: Parameters,
    s: PathwaySpec,
    x: OutcomeArrays,
    e: OutcomeArrays,
    *,
    reopened: bool = False,
    readiness_calls: float = 0.0,
    cairns_hub_only: bool = False,
    receiver_share: float = 0.5,
    retrieval_chhhs_share: float = 1.0,
    subsidy_fraction: float = 0.5,
    family_travel_share: float = 0.4,
    funding_response: float = 0.0,
    sunk: tuple[str, ...] = (),
    overrides: dict[str, dict[str, object]] | None = None,
    owned_assets: tuple[OwnedAsset, ...] | None = None,
    activity: ActivitySpec | None = None,
) -> tuple[OutcomeTable, OutcomeTable, OutcomeTable]:
    """Evaluate every strategy under each declared regional perspective.

    Returns:
        The raw strategy outcomes, the reconciled ledgers and the family components.

    Raises:
        ValueError: If a perspective fraction is not a finite value in 0..1.
    """
    for v in (receiver_share, retrieval_chhhs_share, subsidy_fraction, family_travel_share, funding_response):
        if isinstance(v, bool) or not np.isfinite(v) or not 0 <= v <= 1:
            msg = "Invalid perspective fraction"
            raise ValueError(msg)
    calls = consultation_overrides(
        sites, x, reopened=reopened, readiness_calls=readiness_calls, cairns_hub_only=cairns_hub_only
    )
    r = compare_regional(
        sites,
        p,
        s,
        inputs=x,
        structural_draws=e,
        site_calls=calls,
        sunk=sunk,
        overrides=overrides,
        owned_assets=owned_assets,
        activity=activity,
    )
    local_sites = [z for z in sites if z.name in CHHHS]
    local = (
        r
        if local_sites == sites
        else compare_regional(
            local_sites,
            p,
            s,
            inputs=x,
            structural_draws=e,
            site_calls={k: v for k, v in calls.items() if k in CHHHS},
            sunk=sunk,
            overrides=overrides,
            owned_assets=owned_assets,
            activity=activity,
        )
        if local_sites
        else None
    )
    # Receiving resources allocated to CHHHS must come from the explicitly
    # modelled regional catchment, not every origin in a statewide portfolio.
    catchment_sites = [z for z in sites if z.name in CHHHS + TCHHS]
    catchment = (
        r
        if catchment_sites == sites
        else compare_regional(
            catchment_sites,
            p,
            s,
            inputs=x,
            structural_draws=e,
            site_calls={k: v for k, v in calls.items() if k in CHHHS + TCHHS},
            sunk=sunk,
            overrides=overrides,
            owned_assets=owned_assets,
            activity=activity,
        )
        if catchment_sites
        else None
    )
    base = r["telephone"]
    n = len(x["odds_ratio"])
    hf = e.get("hospital_fraction", np.full(n, s.hospital_marginal_fraction))
    ledgers: OutcomeTable = {}
    components: OutcomeTable = {}
    for key, a in r.items():
        health = -a["net_saving"]
        family = -a["avoided_transfers"] * x["family_delta"]
        subsidy = family * family_travel_share * subsidy_fraction
        # No actual statutory payment is inferred: response0 is fixed-funding,
        # response.405 is a deliberately uncapped illustrative benchmark scenario.
        cth = (a["hospital_benchmark_cost"] - base["hospital_benchmark_cost"]) * funding_response
        provider = np.zeros(n)
        if local is not None:
            la, lb = local[key], local["telephone"]
            localcare = (
                sum(
                    la[f] - lb[f]
                    for f in ("origin_benchmark_cost", "local_benchmark_cost", "pre_rescue_benchmark_cost")
                )
                * hf
            )
            receiver = (
                (catchment[key]["receiving_benchmark_cost"] - catchment["telephone"]["receiving_benchmark_cost"])
                * hf
                * receiver_share
                if catchment is not None
                else np.zeros(n)
            )
            provider = (
                localcare
                + receiver
                + (la["transport_resource_cost"] - lb["transport_resource_cost"]) * retrieval_chhhs_share
            )
            provider += la["capital_annualised"] + la["local_ready_cost"] + la["local_workflow_cost"]
        ledgers[key] = reconcile_ledger(
            health_cost=health, family_gross=family, family_subsidy=subsidy, commonwealth=cth, provider_cost=provider
        )
        components[key] = {
            "family_out_of_pocket": family * family_travel_share - subsidy,
            "family_time_value": family * (1 - family_travel_share),
            "commonwealth_funding_transfer": cth,
            "patient_subsidy_transfer": subsidy,
        }
    return r, ledgers, components


def summary(a: np.ndarray) -> dict[str, float]:
    """Summarise one paired draw array as mean and quantile bounds.

    Returns:
        Mean and 2.5/50/97.5 percentile bounds as plain floats.
    """
    q = np.quantile(a, [0.025, 0.5, 0.975])
    return {
        "mean": float(a.mean()),
        "lower": float(cast("float", q[0])),
        "median": float(cast("float", q[1])),
        "upper": float(cast("float", q[2])),
    }


def utility_bridge_scenarios() -> list[dict[str, object]]:
    """Illustrative improvements from age 11, discounted back to birth.

    Utility contrasts are observational, not effects of video on prematurity.
    Durations and improved fractions remain assumptions. No effect is credited
    before the age at which the source measured the utility contrast.

    Returns:
        One row per utility, duration, discount-rate and improved-fraction combination.
    """
    rows: list[dict[str, object]] = []
    for u, label in (
        (0.13, "EPICure2 adjusted UK HUI2 SI decrement"),
        (0.28, "EPICure2 adjusted Canadian HUI3 decrement"),
    ):
        for duration, rate, improved in itertools.product((1, 5, 10), (0.0, 0.03, 0.05), (0.001, 0.005, 0.01)):
            per = discounted_health_years(np.ones(duration), np.full(duration, u), rate, start_year=11)
            rows.append({
                "utility_difference": u,
                "source_metric": label,
                "duration_years_assumed": duration,
                "start_age_years": 11,
                "discount_rate": rate,
                "fraction_consultations_improved_assumed": improved,
                "qalys_per_1000_consultations": 1000 * improved * per,
                "warning": (
                    "illustrative disability-improvement bridge from age11; does not mean video prevents prematurity"
                ),
            })
    return rows


def main(  # ruff: ignore[complex-structure, too-many-branches, too-many-locals, too-many-statements] -- one linear reproducible regional pipeline
    config_path: Path | None = None, output_dir: Path | None = None
) -> None:
    """Run the regional and perspective analyses and write the output tables.

    Raises:
        FileExistsError: If the target output directory already exists.
    """
    global OUT  # ruff: ignore[global-statement] -- per-invocation output path
    config = load_configuration(ROOT, config_path)
    p, s, n, seed = config.parameters, config.pathways, config.draws, config.seed
    OUT = Path(output_dir or ROOT / "outputs/v12").resolve()  # pyright: ignore[reportConstantRedefinition] -- per-invocation output path
    if OUT.exists() and any(OUT.iterdir()):
        msg = "Refusing to overwrite an existing analysis directory"
        raise FileExistsError(msg)
    OUT.mkdir(parents=True, exist_ok=True)
    _ = (OUT / "resolved_inputs.json").write_text(json.dumps(config.snapshot(), indent=2) + "\n")
    inventories = regional_roster()
    write("regional_roster.csv", inventories)
    deterministic: list[dict[str, object]] = []
    summaries: list[dict[str, object]] = []
    regrets: list[dict[str, object]] = []
    checks: list[CheckRecord] = []
    scenarios: list[dict[str, object]] = []
    thresholds: list[dict[str, object]] = []
    vop_draws: dict[str, dict[str, np.ndarray]] = {}
    allocation_sensitivity: list[dict[str, object]] = []
    predictive: list[dict[str, object]] = []
    budgets: list[dict[str, object]] = []
    networks = {name: portfolio(name) for name in config.portfolios}
    x0 = _base_arrays(p, 1)
    for name, sites in networks.items():
        raw, ledger, _parts = evaluate_perspectives(sites, p, s, x0, {}, owned_assets=config.owned_assets)
        for key, a in raw.items():
            deterministic.append({
                "portfolio": name,
                "sites": len(sites),
                "strategy": key,
                "historical_reported_births": sum(z.births for z in sites),
                **{
                    k: float(cast("float", a[k][0]))
                    for k in (
                        "consultations",
                        "immediate_transfers",
                        "delayed_rescues",
                        "final_local",
                        "programme_cost",
                        "net_saving",
                        "hub_hours",
                    )
                },
                **{z + "_net": float(cast("float", -ledger[key][z][0])) for z in PERSPECTIVES},
            })
        configurations: list[tuple[str, ScenarioOptions]] = [
            ("reference", {}),
            ("null_effect", {}),
            ("skeptical_effect", {}),
            ("published_effect", {}),
            ("reopened", {"reopened": True}),
            ("readiness_1_call", {"readiness_calls": 1.0}),
            ("cairns_referral_only", {"cairns_hub_only": True}),
            ("retain_panda", {"sunk": ("panda",)}),
            ("prototype_uncertain", {}),
            ("provider_local_only", {"receiver_share": 0.0, "retrieval_chhhs_share": 0.0}),
            ("uncapped_funding_response_0405", {"funding_response": 0.405}),
        ]
        for scenario, kwargs in configurations:
            mode = {"null_effect": "null", "skeptical_effect": "skeptical", "published_effect": "published"}.get(
                scenario, "attenuated"
            )
            x, e = sample_v7(p, s, n, seed, mode)
            if scenario == "prototype_uncertain":
                rng = np.random.default_rng(62026)
                kwargs["overrides"] = {
                    "obsbot": {
                        "installed_cost": rng.triangular(2500, 4500, 10000, n) * x["equipment_cost"] / 10000,
                        "reliability": x["reliability"] * rng.triangular(0.65, 0.95, 1.0, n),
                    }
                }
            rr, ll, _cc = evaluate_perspectives(sites, p, s, x, e, owned_assets=config.owned_assets, **kwargs)
            values = {view: np.column_stack([-ll[k][view] for k in KEYS]) for view in PERSPECTIVES}
            for view, matrix in values.items():
                probs = optimal_probabilities(matrix)
                for j, key in enumerate(KEYS):
                    summaries.append({
                        "portfolio": name,
                        "scenario": scenario,
                        "perspective": view,
                        "strategy": key,
                        **summary(matrix[:, j]),
                        "probability_positive": float(cast("float", np.mean(matrix[:, j] > 0))),
                        "probability_optimal": float(cast("float", probs[j])),
                        "unit": "AUD per network-year",
                    })
            for src, dst in itertools.product(PERSPECTIVES, repeat=2):
                v = perspective_regret(values[src], values[dst])
                chosen = cast("list[int]", v["choose_indices"])
                targeted = cast("list[int]", v["target_indices"])
                v["choose_indices"] = "|".join(KEYS[i] for i in chosen)
                v["target_indices"] = "|".join(KEYS[i] for i in targeted)
                regrets.append({
                    "portfolio": name,
                    "scenario": scenario,
                    "choose_under": src,
                    "evaluate_under": dst,
                    **v,
                })
            if scenario == "reference":
                for key, arm in rr.items():
                    predictive.extend(
                        {
                            "portfolio": name,
                            "strategy": key,
                            "metric": metric,
                            **summary(arm[metric]),
                            "interpretation": "Prior predictive, not fitted local outcomes",
                        }
                        for metric in (
                            "consultations",
                            "immediate_transfers",
                            "delayed_rescues",
                            "final_local",
                            "eventual_transfers",
                            "hub_hours",
                            "hospital_benchmark_cost",
                        )
                    )
            residual = max(
                float(
                    cast(
                        "float",
                        np.max(np.abs(a["state"] + a["commonwealth"] + a["patient_family"] - a["societal_bounded"])),
                    )
                )
                for a in ll.values()
            )
            mass = max(
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
                for a in rr.values()
            )
            checks.append({
                "portfolio": name,
                "scenario": scenario,
                "max_perspective_reconciliation_error": residual,
                "max_cohort_error": mass,
            })
            if scenario in {"reference", "prototype_uncertain"}:
                np.savez_compressed(OUT / (name + "_" + scenario + "_perspectives.npz"), allow_pickle=True, **values)
                vop_draws[name + "_" + scenario] = values
            for key, a in rr.items():
                scenarios.append({
                    "portfolio": name,
                    "scenario": scenario,
                    "strategy": key,
                    **summary(a["net_saving"]),
                    "mean_consultations": float(a["consultations"].mean()),
                    "mean_avoided_transfers": float(a["avoided_transfers"].mean()),
                })
        # No-effect health-gain threshold; no QALY is credited in reference analysis.
        pn = replace(p, odds_ratio=1.0)
        nr = compare_v6(sites, pn, s)
        for key in KEYS[1:]:
            cost = float(cast("float", -nr[key]["net_saving"][0]))
            calls = float(cast("float", nr[key]["consultations"][0]))
            for lam in (30000.0, 50000.0, 100000.0):
                required = required_health_gain(cost, lam)
                thresholds.append({
                    "portfolio": name,
                    "strategy": key,
                    "additional_annual_cost_no_transfer_effect": cost,
                    "scenario_value_per_qaly": lam,
                    "required_qalys_per_network_year": required,
                    "required_qaly_days_per_consultation": required * 365.25 / calls if calls else None,
                    "status": "threshold, not estimated video benefit; not an official Australian threshold",
                })
    for name, sites in networks.items():
        for strategy in KEYS:
            for retain in (False, True):
                budgets.extend(
                    {"portfolio": name, "strategy": strategy, "retain_known_estate": retain, **row}
                    for row in mixed_cash_budget(sites, strategy, config.owned_assets, p, s, retain=retain)
                )
    write("mixed_estate_budget.csv", budgets)
    write("prior_predictive.csv", predictive)
    # Exact two-way allocation surface: no need to rerun clinical outcomes.
    for name in (key for key in config.portfolios if key != "spokes"):
        rr, ll, _cc = evaluate_perspectives(networks[name], p, s, x0, {}, owned_assets=config.owned_assets)
        # Receiver share changes provider accounting only; reimbursement changes
        # fiscal/patient accounts only, leaving societal resources invariant.
        for share in np.linspace(0, 1, 11):
            for subsidy in np.linspace(0, 1, 11):
                _, ledger_alloc, _ = evaluate_perspectives(
                    networks[name],
                    p,
                    s,
                    x0,
                    {},
                    receiver_share=float(share),
                    subsidy_fraction=float(subsidy),
                    owned_assets=config.owned_assets,
                )
                for view in ("health_system", "societal_bounded", "provider_chhhs", "patient_family"):
                    m = np.array([-ledger_alloc[k][view][0] for k in KEYS])
                    chosen = np.flatnonzero(np.isclose(m, cast("float", m.max()), rtol=0, atol=1e-9))
                    allocation_sensitivity.append({
                        "portfolio": name,
                        "receiver_share": float(share),
                        "subsidy_share_of_travel": float(subsidy),
                        "perspective": view,
                        "expected_best": "|".join(KEYS[j] for j in chosen),
                        "maximum_net_value": float(cast("float", m.max())),
                    })
    # The kit is a conceptual comparator, not an approved current procurement option.
    eligibility: list[dict[str, object]] = []
    for network in networks:
        data = cast("Mapping[str, np.ndarray]", np.load(OUT / (network + "_reference_perspectives.npz")))
        for view in PERSPECTIVES:
            matrix = data[view][:, :4]
            probs = optimal_probabilities(matrix)
            for j, key in enumerate(KEYS[:4]):
                eligibility.append({
                    "portfolio": network,
                    "perspective": view,
                    "strategy": key,
                    **summary(matrix[:, j]),
                    "probability_optimal": float(cast("float", probs[j])),
                    "decision_set": "four established categories; local technical suitability still required",
                })
    write("established_options.csv", eligibility)
    # Age-11 observational utilities are not credited before their evidence age.
    health = utility_bridge_scenarios()
    for name, rows in [
        ("deterministic.csv", deterministic),
        ("psa_perspectives.csv", summaries),
        ("value_of_perspective.csv", regrets),
        ("reconciliation.csv", checks),
        ("structural_scenarios.csv", scenarios),
        ("health_thresholds.csv", thresholds),
        ("allocation_two_way.csv", allocation_sensitivity),
        ("utility_bridge_scenarios.csv", health),
    ]:
        write(name, rows)
    metadata: dict[str, object] = {
        "version": "12.0.0",
        "draws": n,
        "seed": seed,
        "portfolios": {k: len(v) for k, v in networks.items()},
        "perspectives": PERSPECTIVES,
        "simulated_review": "role-based author self-review, not independent agents",
        "counts": {
            "paired_psa_structures": len(checks),
            "psa_result_rows": len(summaries),
            "vop_directional_rows": len(regrets),
            "two_way_allocation_rows": len(allocation_sensitivity),
            "qaly_thresholds": len(thresholds),
            "utility_bridge_scenarios": len(health),
            "prior_predictive_rows": len(predictive),
            "mixed_estate_budget_rows": len(budgets),
        },
        "max_mass_error": max(c["max_cohort_error"] for c in checks),
        "max_ledger_error": max(c["max_perspective_reconciliation_error"] for c in checks),
        "funding": (
            "Fixed fiscal response reference; .405 is an uncapped illustrative benchmark response, not a "
            "Queensland entitlement calculator"
        ),
        "societal_scope": (
            "Health resources plus existing family travel/time aggregate only; wider education/carer/environment "
            "effects unquantified"
        ),
        "source_vop_commit": "ad84d3090a2d97f2805a86e94a7b9614a3d1ab14",
        "fit": "No local empirical fitting; labelled transported and researcher priors",
    }
    _ = (OUT / "results.json").write_text(json.dumps(metadata, indent=2))
    print(json.dumps(metadata, indent=2))  # ruff: ignore[print] -- CLI results report goes to stdout


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument("--config", type=Path, default=ROOT / "config/reference.json")
    _ = parser.add_argument("--output", type=Path, default=ROOT / "outputs/v12")
    args = parser.parse_args()
    main(cast("Path | None", args.config), cast("Path | None", args.output))
