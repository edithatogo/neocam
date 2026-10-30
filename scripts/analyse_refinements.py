# ruff: ignore[implicit-namespace-package] -- scripts/ is a namespace package run via python -m
"""Generate contact/episode and eligible deployment comparisons from declared inputs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict, cast

import numpy as np

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import audit_v7  # ruff: ignore[module-import-not-at-top-of-file] -- import needs ROOT on sys.path
from src.activity import ActivitySpec  # ruff: ignore[module-import-not-at-top-of-file] -- import needs ROOT on sys.path
from src.configuration import (  # ruff: ignore[module-import-not-at-top-of-file] -- import needs ROOT on sys.path
    exact_keys,
    load_configuration,
    strict_json,
)
from src.deployment import (  # ruff: ignore[module-import-not-at-top-of-file] -- import needs ROOT on sys.path
    eligibility_catalogue,
    evaluate_policies,
    evaluate_policy,
    policy_cash_budget,
    policy_catalogue,
)
from src.perspectives_v7 import (  # ruff: ignore[module-import-not-at-top-of-file] -- import needs ROOT on sys.path
    optimal_probabilities,
)
from src.portfolios_v7 import portfolio  # ruff: ignore[module-import-not-at-top-of-file] -- import needs ROOT on sys.path

# The numerical kernels are untyped in the model package; bind precise call shapes here.
sample_v7 = cast("Callable[..., tuple[dict[str, np.ndarray], dict[str, np.ndarray]]]", audit_v7.sample_v7)

REVIEW_ROLES = ("neonatal_retrieval", "health_economics", "technical", "consumer_rural")
MAX_BUDGET_YEARS = 100  # upper bound on the declared cash-budget horizon


class ActivityScenario(TypedDict):
    """One declared contact-versus-episode activity scenario."""

    id: str
    activity_basis: str
    contacts_per_episode: float


class Refinements(TypedDict):
    """The validated config/refinements.json document."""

    schema_version: int
    activity_scenarios: list[ActivityScenario]
    effect_modes: list[str]
    budget_years: int
    assumption_label: str


class CheckRecord(TypedDict):
    """One paired-policy cohort-conservation check row."""

    portfolio: str
    activity_id: str
    effect_mode: str
    policy: str
    cohort_residual: float
    all_finite: bool
    clinical_validation: bool


class ReviewPacket(TypedDict):
    """The empty external-review request template bound to a snapshot digest."""

    snapshot_sha256: str
    independent_validation: bool
    review_type: str
    reviews: list[dict[str, object]]


def load_refinements(path: Path) -> Refinements:
    """Validate researcher scenarios before generating any output files.

    Returns:
        The validated refinements mapping.

    Raises:
        ValueError: If a scenario, mode, schema version or budget year is invalid.
    """
    data = strict_json(path)
    exact_keys(
        data,
        {"schema_version", "activity_scenarios", "effect_modes", "budget_years", "assumption_label"},
        "Refinements",
    )
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        msg = "Unknown refinements schema"
        raise ValueError(msg)
    rows = data["activity_scenarios"]
    if not isinstance(rows, list) or not rows:
        msg = "Nonempty activity scenarios required"
        raise ValueError(msg)
    scenarios = cast("list[dict[str, object]]", rows)
    seen: set[str] = set()
    semantics: set[tuple[str, float]] = set()
    for row in scenarios:
        exact_keys(row, {"id", "activity_basis", "contacts_per_episode"}, "Activity scenario")
        identity = row["id"]
        if not isinstance(identity, str) or not re.fullmatch(r"[a-z0-9_]+", identity) or identity in seen:
            msg = "Unique safe activity identifiers required"
            raise ValueError(msg)
        seen.add(identity)
        activity = ActivitySpec(cast("str", row["activity_basis"]), cast("float", row["contacts_per_episode"]))
        signature = (activity.activity_basis, activity.contacts_per_episode)
        if signature in semantics:
            msg = "Duplicate semantic activity scenario"
            raise ValueError(msg)
        semantics.add(signature)
    modes = data["effect_modes"]
    mode_values = cast("list[object]", modes)
    if (
        not isinstance(modes, list)
        or not modes
        or any(not isinstance(x, str) for x in mode_values)
        or len(set(mode_values)) != len(mode_values)
        or set(mode_values) - {"attenuated", "null", "skeptical", "published"}
    ):
        msg = "Invalid or duplicate effect modes"
        raise ValueError(msg)
    if type(data["budget_years"]) is not int or not 1 <= data["budget_years"] <= MAX_BUDGET_YEARS:
        msg = "Budget years must be in 1..100"
        raise ValueError(msg)
    if not isinstance(data["assumption_label"], str) or not data["assumption_label"].strip():
        msg = "Assumption disclosure is required"
        raise ValueError(msg)
    return cast("Refinements", cast("object", data))


def summary(values: np.ndarray) -> dict[str, float]:
    """Summarise paired researcher-prior draws, not fitted clinical predictions.

    Returns:
        Mean and 2.5/50/97.5 percentile bounds as plain floats.
    """
    q = np.quantile(values, [0.025, 0.5, 0.975])
    return {
        "mean": float(values.mean()),
        "lower": float(cast("float", q[0])),
        "median": float(cast("float", q[1])),
        "upper": float(cast("float", q[2])),
    }


def write_csv(output: Path, name: str, rows: Sequence[Mapping[str, object]]) -> None:
    """Write one CSV table under the output directory.

    Raises:
        ValueError: If there are no rows for the named output.
    """
    if not rows:
        msg = f"Empty output scope: {name}"
        raise ValueError(msg)
    with (output / name).open("w", newline="", encoding="utf-8") as stream:
        writer: csv.DictWriter[str] = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def pending_reviews(snapshot: str) -> ReviewPacket:
    """Empty external review requests, never simulated or auto-approved signatures.

    Returns:
        The review packet template bound to the given snapshot digest.
    """
    questions = {
        "neonatal_retrieval": (
            "Do episode counts, transfer timing, local capability and appropriate escalation look plausible? "
            "More transfers can mean better recognition; identify potential unsafe retention."
        ),
        "health_economics": (
            "Are incremental workload, avoidable resources, shared capacity and site-estate "
            "capital/replacement coherent? Are fixed-contact versus fixed-episode interpretations appropriate?"
        ),
        "technical": (
            "Recalculate a small independent case without importing model helpers; check shared priors, "
            "population and cost identities against exact source and inputs."
        ),
        "consumer_rural": (
            "Assess separation, access, family burden, cultural safety and whether the bounded family-cost "
            "account misses material consequences."
        ),
    }
    reviews: list[dict[str, object]] = [
        {
            "role": role,
            "identity": "",
            "independent": False,
            "status": "pending",
            "conflicts": "",
            "date": "",
            "snapshot_sha256": snapshot,
            "finding_summary": "",
            "findings": [],
            "evidence": [],
            "question": questions[role],
        }
        for role in REVIEW_ROLES
    ]
    return {
        "snapshot_sha256": snapshot,
        "independent_validation": False,
        "review_type": "external review requested, not executed",
        "reviews": reviews,
    }


def snapshot_identity(root: Path, declared: Mapping[str, object]) -> str:
    """Bind external-review requests to numerical/report source and resolved inputs.

    Returns:
        SHA-256 digest of the declared and calculated inputs.
    """
    from quality.artifacts import calculation_inputs  # ruff: ignore[import-outside-top-level] -- deferred so the module imports without the artifacts dependency

    identity = {"declared_inputs": declared, "calculation_inputs": calculation_inputs(root)}
    return hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()


def main(  # ruff: ignore[complex-structure, too-many-branches, too-many-locals, too-many-statements] -- one linear reproducible paired-policy pipeline
    config_path: Path | None = None, refinements_path: Path | None = None, output_dir: Path | None = None
) -> dict[str, object]:
    """Run paired policy analysis; all approvals, health effects and gaps stay explicit.

    Returns:
        The written results metadata mapping.

    Raises:
        ValueError: If configuration paths or the output directory are invalid.
        FileExistsError: If the target output directory already exists.
    """
    config = load_configuration(ROOT, config_path)
    ref_path = (refinements_path or ROOT / "config/refinements.json").resolve()
    if not ref_path.is_relative_to(ROOT):
        msg = "Refinement configuration must be inside repository"
        raise ValueError(msg)
    refinements = load_refinements(ref_path)
    p, s, n = config.parameters, config.pathways, config.draws
    output = (output_dir or ROOT / "outputs/v13-refinements").resolve()
    if not output.is_relative_to(ROOT / "outputs") or output == ROOT / "outputs":
        msg = "New output must be a subdirectory of repository outputs"
        raise ValueError(msg)
    if output.exists():
        msg = "Refusing to overwrite an existing analysis directory"
        raise FileExistsError(msg)
    output.mkdir(parents=True)
    snapshot: dict[str, object] = config.snapshot()
    snapshot["refinements_sha256"] = hashlib.sha256(ref_path.read_bytes()).hexdigest()
    snapshot["refinements"] = refinements
    snapshot_digest = snapshot_identity(ROOT, snapshot)
    snapshot["analysis_snapshot_sha256"] = snapshot_digest
    _ = (output / "resolved_inputs.json").write_text(json.dumps(snapshot, indent=2) + "\n")
    deterministic: list[dict[str, object]] = []
    results: list[dict[str, object]] = []
    rankings: list[dict[str, object]] = []
    predictive: list[dict[str, object]] = []
    budgets: list[dict[str, object]] = []
    assignments: list[dict[str, object]] = []
    eligibility_rows: list[dict[str, object]] = []
    checks: list[CheckRecord] = []
    sampled = {mode: sample_v7(p, s, n=n, seed=config.seed, effect_mode=mode) for mode in refinements["effect_modes"]}
    for network in config.portfolios:  # ruff: ignore[too-many-nested-blocks] -- paired policy/contact/scenario nesting is deliberate
        print(f"Analysing {network}: paired policy/contact scenarios", flush=True)  # ruff: ignore[print] -- CLI progress goes to stdout
        sites = portfolio(network)
        policies = policy_catalogue(sites)
        eligibility = eligibility_catalogue(sites, allow_hypothetical=True)
        eligibility_rows.extend({"portfolio": network, **asdict(record)} for record in eligibility)
        for policy in policies:
            assignments.extend(
                {
                    "portfolio": network,
                    "policy": policy.name,
                    "conditional_policy": policy.conditional,
                    "site": site,
                    "strategy": technology,
                }
                for site, technology in policy.assignments
            )
        for row in refinements["activity_scenarios"]:
            activity = ActivitySpec(row["activity_basis"], row["contacts_per_episode"])
            for policy in policies:
                arm = evaluate_policy(sites, policy, eligibility, p, s, config.owned_assets, activity=activity)
                deterministic.append({
                    "portfolio": network,
                    "activity_id": row["id"],
                    "activity_basis": activity.activity_basis,
                    "contacts_per_episode": activity.contacts_per_episode,
                    "policy": policy.name,
                    "conditional_policy": policy.conditional,
                    **{
                        k: float(cast("float", arm[k][0]))
                        for k in (
                            "episodes",
                            "contacts",
                            "eventual_transfers",
                            "delayed_rescues",
                            "final_local",
                            "avoided_transfers",
                            "net_saving",
                            "programme_cost",
                            "hub_hours",
                            "hub_cash_cost",
                        )
                    },
                    "initial_purchase_capital": float(cast("float", arm["incremental_purchase_capital"][0])),
                })
                budgets.extend(
                    {"portfolio": network, "activity_id": row["id"], "policy": policy.name, **budget}
                    for budget in policy_cash_budget(
                        sites,
                        policy,
                        eligibility,
                        p,
                        s,
                        config.owned_assets,
                        activity=activity,
                        years=refinements["budget_years"],
                    )
                )
            for effect in refinements["effect_modes"]:
                x, e = sampled[effect]
                calculated = evaluate_policies(
                    sites,
                    policies,
                    eligibility,
                    p,
                    s,
                    config.owned_assets,
                    inputs=x,
                    structural_draws=e,
                    activity=activity,
                )
                evaluated = [calculated[policy.name] for policy in policies]
                for policy, arm in zip(policies, evaluated, strict=True):
                    base: dict[str, object] = {
                        "portfolio": network,
                        "activity_id": row["id"],
                        "activity_basis": activity.activity_basis,
                        "contacts_per_episode": activity.contacts_per_episode,
                        "effect_mode": effect,
                        "policy": policy.name,
                        "conditional_policy": policy.conditional,
                    }
                    for metric, label in (
                        ("net_saving", "health_system"),
                        ("net_with_family_extension", "societal_bounded"),
                    ):
                        results.append({
                            **base,
                            "perspective": label,
                            **summary(arm[metric]),
                            "probability_resource_saving": float(cast("float", np.mean(arm[metric] > 0))),
                        })
                    predictive.extend(
                        {**base, "metric": metric, **summary(arm[metric])}
                        for metric in (
                            "episodes",
                            "contacts",
                            "immediate_transfers",
                            "delayed_rescues",
                            "final_local",
                            "eventual_transfers",
                            "hub_hours",
                            "hospital_benchmark_cost",
                        )
                    )
                    mass = cast(
                        "float",
                        np.max(np.abs(arm["eventual_transfers"] + arm["final_local"] - arm["episodes"])),
                    )
                    checks.append({
                        "portfolio": network,
                        "activity_id": row["id"],
                        "effect_mode": effect,
                        "policy": policy.name,
                        "cohort_residual": float(mass),
                        "all_finite": all(np.isfinite(a).all() for a in arm.values()),
                        "clinical_validation": False,
                    })
                for decision_set in ("reported_operation", "conditional_expansion"):
                    selected = [
                        i
                        for i, policy in enumerate(policies)
                        if decision_set == "conditional_expansion" or not policy.conditional
                    ]
                    for metric, view in (
                        ("net_saving", "health_system"),
                        ("net_with_family_extension", "societal_bounded"),
                    ):
                        matrix = np.column_stack([evaluated[i][metric] for i in selected])
                        probs = optimal_probabilities(matrix)
                        for j, i in enumerate(selected):
                            rankings.append({
                                "portfolio": network,
                                "activity_id": row["id"],
                                "effect_mode": effect,
                                "decision_set": decision_set,
                                "perspective": view,
                                "policy": policies[i].name,
                                "expected_net_value": float(cast("float", matrix[:, j].mean())),
                                "probability_optimal": float(cast("float", probs[j])),
                                "expected_regret": float(cast("float", (matrix.max(axis=1) - matrix[:, j]).mean())),
                                "status": "cost-only conditional decision, not procurement or clinical recommendation",
                            })
    for name, rows in [
        ("policy_deterministic.csv", deterministic),
        ("policy_psa.csv", results),
        ("policy_rankings.csv", rankings),
        ("policy_predictive.csv", predictive),
        ("policy_budget.csv", budgets),
        ("policy_assignments.csv", assignments),
        ("eligibility.csv", eligibility_rows),
        ("checks.csv", checks),
    ]:
        write_csv(output, name, rows)
    _ = (output / "review_packet.json").write_text(json.dumps(pending_reviews(snapshot_digest), indent=2) + "\n")
    metadata: dict[str, object] = {
        "version": "13.0.0",
        "draws": n,
        "seed": config.seed,
        "portfolios": list(config.portfolios),
        "independent_validation": False,
        "clinical_appropriateness_estimated": False,
        "snapshot_sha256": snapshot_digest,
        "max_cohort_residual": max(r["cohort_residual"] for r in checks),
        "all_finite": all(r["all_finite"] for r in checks),
        "counts": {
            "paired_policy_scenarios": len(checks),
            "psa_result_rows": len(results),
            "ranking_rows": len(rankings),
            "predictive_rows": len(predictive),
            "budget_rows": len(budgets),
        },
        "assumptions": refinements["assumption_label"],
        "scope": (
            "Health-system and bounded family resources; arbitrary mixed-policy provider/fiscal allocation is "
            "not inferred. Original six-perspective reference retained separately."
        ),
        "clinical_unit": (
            "episode; consultations is legacy episode alias, contacts are separate workload events; not unique "
            "infants over repeated admissions"
        ),
        "reliability": "episode-level video delivery; repeated contacts are not independent opportunities for success",
        "cost_equivalence": (
            "Reference assumes equal video effect/reliability by technology; lower costs alone can dominate "
            "under that assumption."
        ),
    }
    _ = (output / "results.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(metadata, indent=2))  # ruff: ignore[print] -- CLI results report goes to stdout
    return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument("--config", type=Path, default=ROOT / "config/reference.json")
    _ = parser.add_argument("--refinements", type=Path, default=ROOT / "config/refinements.json")
    _ = parser.add_argument("--output", type=Path, default=ROOT / "outputs/v13-refinements")
    args = parser.parse_args()
    _ = main(cast("Path | None", args.config), cast("Path | None", args.refinements), cast("Path | None", args.output))
