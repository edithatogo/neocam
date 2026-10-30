"""Explicit mixed-site policies; eligibility assumptions are not device approvals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from src.equipment import OwnedAsset, apply_retention, mixed_cash_budget, validate_estate
from src.pathways_v6 import PathwaySpec, compare_v6, hub_cost
from src.strategies import KEYS

if TYPE_CHECKING:
    from src.activity import ActivitySpec
    from src.statewide import Parameters, Site

PILOT_NAMES = frozenset({"Atherton", "Mareeba", "Innisfail"})
ELIGIBILITY_STATES = frozenset({"reported_operation", "verified_eligible", "hypothetical", "unknown"})
# A policy assignment row is a (site, strategy) pair.
_ASSIGNMENT_WIDTH = 2
# Guard bound for the annual cash-budget horizon in years.
_MAX_BUDGET_YEARS = 100


@dataclass(frozen=True)
class Eligibility:
    """A site/strategy decision-set record, not certification from this software."""

    site: str
    strategy: str
    status: str
    evidence: str

    def __post_init__(self) -> None:
        """Reject malformed eligibility records before they are used.

        Raises:
            ValueError: If the site, strategy, status or evidence is invalid.
        """
        invalid_site = not isinstance(self.site, str) or not self.site.strip()
        invalid_evidence = not isinstance(self.evidence, str) or not self.evidence.strip()
        if invalid_site or self.strategy not in KEYS or self.status not in ELIGIBILITY_STATES or invalid_evidence:
            msg = "Invalid eligibility record"
            raise ValueError(msg)


@dataclass(frozen=True)
class DeploymentPolicy:
    """Exactly one configuration per site; no unrestricted combinatorial optimiser."""

    name: str
    assignments: tuple[tuple[str, str], ...]
    conditional: bool = False

    def __post_init__(self) -> None:
        """Freeze and validate the policy identity and site assignments.

        Raises:
            ValueError: If the name, conditional flag or assignments are invalid.
        """
        if not isinstance(self.name, str) or not self.name.strip() or type(self.conditional) is not bool:
            msg = "Invalid deployment policy identity"
            raise ValueError(msg)
        # Freeze caller-owned lists. Validate row shape before conversion.
        if not isinstance(self.assignments, (tuple, list)) or not self.assignments:
            msg = "Nonempty assignments required"
            raise ValueError(msg)
        for row in self.assignments:
            if (
                not isinstance(row, (tuple, list))
                or len(row) != _ASSIGNMENT_WIDTH
                or any(not isinstance(v, str) or not v.strip() for v in row)
                or row[1] not in KEYS
            ):
                msg = "Invalid policy assignment"
                raise ValueError(msg)
        object.__setattr__(self, "assignments", tuple(tuple(row) for row in self.assignments))


def eligibility_catalogue(sites: list[Site], *, allow_hypothetical: bool = False) -> tuple[Eligibility, ...]:
    """Preserve reported pilot operation; do not generalise it to new sites/devices.

    Returns:
        One eligibility record per site and strategy.

    Raises:
        ValueError: If the hypothetical-permission flag is not boolean.
    """
    if type(allow_hypothetical) is not bool:
        msg = "Hypothetical permission must be boolean"
        raise ValueError(msg)
    records = []
    for site in sites:
        for key in KEYS:
            if key == "telephone":
                status, source = "reported_operation", "Existing specialist telephone pathway; usual care"
            elif site.name in PILOT_NAMES and key == "panda":
                status, source = (
                    "reported_operation",
                    "ELC2026 item2.1.7; reported operation, not approval certification",
                )
            elif allow_hypothetical:
                status, source = (
                    "hypothetical",
                    "Analyst scenario: site suitability, credentials, connectivity and approval unverified",
                )
            else:
                status, source = "unknown", "No verified site-specific eligibility evidence supplied"
            records.append(Eligibility(site.name, key, status, source))
    return tuple(records)


def validate_policy(sites: list[Site], policy: DeploymentPolicy, eligibility: tuple[Eligibility, ...]) -> None:
    """Reject incomplete scopes, duplicate records and ineligible strategy choices.

    Raises:
        ValueError: If the scope, policy or eligibility records are inconsistent.
    """
    if not sites or len({s.name for s in sites}) != len(sites) or not isinstance(policy, DeploymentPolicy):
        msg = "Unique nonempty site scope and typed policy required"
        raise ValueError(msg)
    names = {s.name for s in sites}
    if any(not isinstance(e, Eligibility) or e.site not in names for e in eligibility):
        msg = "Unknown site or malformed eligibility"
        raise ValueError(msg)
    records = {(e.site, e.strategy): e for e in eligibility}
    if len(records) != len(eligibility):
        msg = "Duplicate eligibility"
        raise ValueError(msg)
    chosen = dict(policy.assignments)
    if len(chosen) != len(policy.assignments) or set(chosen) != names:
        msg = "Policy must assign every site exactly once"
        raise ValueError(msg)
    for site, strategy in chosen.items():
        record = records.get((site, strategy))
        allowed = {"reported_operation", "verified_eligible"}
        if policy.conditional:
            allowed.add("hypothetical")
        if record is None or record.status not in allowed:
            msg = f"Policy eligibility not established: {site}/{strategy}"
            raise ValueError(msg)


def policy_catalogue(sites: list[Site]) -> tuple[DeploymentPolicy, ...]:
    """Two reported-operation policies plus four conditional expansion scenarios.

    Returns:
        The distinct deployment policies.
    """
    all_phone = tuple((s.name, "telephone") for s in sites)
    result = [
        DeploymentPolicy("telephone", all_phone),
        DeploymentPolicy(
            "retain_pilot_only", tuple((s.name, "panda" if s.name in PILOT_NAMES else "telephone") for s in sites)
        ),
    ]
    result.extend(
        DeploymentPolicy(
            f"retain_pilot_expand_{new}",
            tuple((s.name, "panda" if s.name in PILOT_NAMES else new) for s in sites),
            conditional=True,
        )
        for new in ("panda", "obsbot", "mobile", "fixed")
    )
    unique = []
    seen = set()
    for policy in result:
        if policy.assignments not in seen:
            unique.append(policy)
            seen.add(policy.assignments)
    return tuple(unique)


def _groups(sites: list[Site], policy: DeploymentPolicy) -> dict[str, list[Site]]:
    chosen = dict(policy.assignments)
    return {key: [s for s in sites if chosen[s.name] == key] for key in KEYS if key in chosen.values()}


def evaluate_policies(  # ruff: ignore[too-many-arguments, too-many-positional-arguments] -- published evaluation API
    sites: list[Site],
    policies: tuple[DeploymentPolicy, ...],
    eligibility: tuple[Eligibility, ...],
    parameters: Parameters,
    spec: PathwaySpec,
    assets: tuple[OwnedAsset, ...],
    *,
    inputs: dict | None = None,
    structural_draws: dict | None = None,
    activity: ActivitySpec | None = None,
    retain: bool = True,
    site_calls: dict | None = None,
) -> dict[str, dict[str, np.ndarray]]:
    """Evaluate each distinct group once within this call, on the same input draws.

    No persistent cache or reused acceptance evidence is involved. Outputs are
    copied before retention/aggregation; a subsequent call always computes afresh.

    Returns:
        Per-policy result dictionaries on the shared draws.

    Raises:
        ValueError: If the policies, retention flag or site override is invalid.
    """
    if not policies or any(not isinstance(p, DeploymentPolicy) for p in policies):
        msg = "Nonempty typed policies required"
        raise ValueError(msg)
    if len({p.name for p in policies}) != len(policies):
        msg = "Duplicate policy identifiers"
        raise ValueError(msg)
    for policy in policies:
        validate_policy(sites, policy, eligibility)
    validate_estate(assets)
    if type(retain) is not bool:
        msg = "Retention must be boolean"
        raise ValueError(msg)
    site_calls = {} if site_calls is None else site_calls
    if set(site_calls) - {s.name for s in sites}:
        msg = "Unknown site in activity override"
        raise ValueError(msg)
    calculated = {}
    answers = {}
    for policy in policies:
        selected = []
        for key, group in _groups(sites, policy).items():
            identity = tuple(s.name for s in group)
            if identity not in calculated:
                calculated[identity] = compare_v6(
                    group,
                    parameters,
                    spec,
                    inputs=inputs,
                    structural_draws=structural_draws,
                    activity=activity,
                    site_calls={k: v for k, v in site_calls.items() if k in identity},
                )
            arm = {name: value.copy() for name, value in calculated[identity][key].items()}
            if retain and key != "telephone":
                apply_retention({key: arm}, group, assets, (key,))
            selected.append(arm)
        out = {name: sum((r[name] for r in selected), np.zeros_like(selected[0][name])) for name in selected[0]}
        out["conditional_rescue_risk"] = np.divide(
            out["delayed_rescues"],
            out["initially_local"],
            out=np.zeros_like(out["episodes"]),
            where=out["initially_local"] > 0,
        )
        # Spare capacity belongs to the whole network, not each technology group.
        hub = hub_cost(out["hub_hours"], np.full_like(out["hub_hours"], 60.0), spec)
        out["hub_cash_cost"] = hub["cash_capacity"]
        out["hub_capacity_blocks"] = hub["capacity_blocks"]
        out["cash_running_cost"] = out["local_ready_cost"] + out["local_workflow_cost"] + out["hub_cash_cost"]
        answers[policy.name] = out
    return answers


def evaluate_policy(  # ruff: ignore[too-many-arguments, too-many-positional-arguments] -- published evaluation API
    sites: list[Site],
    policy: DeploymentPolicy,
    eligibility: tuple[Eligibility, ...],
    parameters: Parameters,
    spec: PathwaySpec,
    assets: tuple[OwnedAsset, ...],
    *,
    inputs: dict | None = None,
    structural_draws: dict | None = None,
    activity: ActivitySpec | None = None,
    retain: bool = True,
    site_calls: dict | None = None,
) -> dict[str, np.ndarray]:
    """Evaluate one policy, retaining the same public typed interface and safeguards.

    Returns:
        The selected policy's result dictionary.
    """
    results = evaluate_policies(
        sites,
        (policy,),
        eligibility,
        parameters,
        spec,
        assets,
        inputs=inputs,
        structural_draws=structural_draws,
        activity=activity,
        retain=retain,
        site_calls=site_calls,
    )
    return results[policy.name]


def policy_cash_budget(  # ruff: ignore[too-many-arguments, too-many-positional-arguments] -- published budgeting API
    sites: list[Site],
    policy: DeploymentPolicy,
    eligibility: tuple[Eligibility, ...],
    parameters: Parameters,
    spec: PathwaySpec,
    assets: tuple[OwnedAsset, ...],
    *,
    activity: ActivitySpec | None = None,
    retain: bool = True,
    years: int = 7,
    site_calls: dict | None = None,
) -> list[dict]:
    """Combine site-estate purchases with one portfolio-level annual hub capacity bill.

    Returns:
        The annual capital and running-cash schedule.

    Raises:
        ValueError: If the budget horizon is not an integer in range.
    """
    result = evaluate_policy(
        sites, policy, eligibility, parameters, spec, assets, activity=activity, retain=retain, site_calls=site_calls
    )
    if type(years) is not int or not 1 <= years <= _MAX_BUDGET_YEARS:
        msg = "Budget years must be an integer in 1..100"
        raise ValueError(msg)
    tables = []
    for key, group in _groups(sites, policy).items():
        names = {s.name for s in group}
        tables.append(
            mixed_cash_budget(
                group,
                key,
                assets,
                parameters,
                spec,
                retain=retain,
                years=years,
                activity=activity,
                site_calls={k: v for k, v in (site_calls or {}).items() if k in names},
            )
        )
    rows = []
    for i in range(years):
        capital = sum(t[i]["capital"] for t in tables)
        running = float(result["cash_running_cost"][0])
        rows.append({
            "year": i + 1,
            "capital": capital,
            "purchases": sum(t[i]["purchases"] for t in tables),
            "new_installations": sum(t[i]["new_installations"] for t in tables),
            "cash_running": running,
            "hub_cash_capacity": float(result["hub_cash_cost"][0]),
            "cash_expenditure": capital + running,
        })
    return rows
