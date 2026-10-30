"""Explicit mixed-site policies; eligibility assumptions are not device approvals."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.activity import ActivitySpec
from src.equipment import OwnedAsset, apply_retention, mixed_cash_budget, validate_estate
from src.pathways_v6 import PathwaySpec, compare_v6, hub_cost
from src.statewide import Parameters, Site
from src.strategies import KEYS

PILOT_NAMES = frozenset({'Atherton', 'Mareeba', 'Innisfail'})
ELIGIBILITY_STATES = frozenset({'reported_operation', 'verified_eligible', 'hypothetical', 'unknown'})


@dataclass(frozen=True)
class Eligibility:
    """A site/strategy decision-set record, not certification from this software."""

    site: str
    strategy: str
    status: str
    evidence: str

    def __post_init__(self) -> None:
        if (not isinstance(self.site, str) or not self.site.strip() or self.strategy not in KEYS
                or self.status not in ELIGIBILITY_STATES
                or not isinstance(self.evidence, str) or not self.evidence.strip()):
            raise ValueError('Invalid eligibility record')


@dataclass(frozen=True)
class DeploymentPolicy:
    """Exactly one configuration per site; no unrestricted combinatorial optimiser."""

    name: str
    assignments: tuple[tuple[str, str], ...]
    conditional: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip() or type(self.conditional) is not bool:
            raise ValueError('Invalid deployment policy identity')
        # Freeze caller-owned lists. Validate row shape before conversion.
        if not isinstance(self.assignments, (tuple, list)) or not self.assignments:
            raise ValueError('Nonempty assignments required')
        for row in self.assignments:
            if (not isinstance(row, (tuple, list)) or len(row) != 2
                    or any(not isinstance(v, str) or not v.strip() for v in row)
                    or row[1] not in KEYS):
                raise ValueError('Invalid policy assignment')
        object.__setattr__(self, 'assignments', tuple(tuple(row) for row in self.assignments))


def eligibility_catalogue(sites: list[Site], *, allow_hypothetical: bool = False) -> tuple[Eligibility, ...]:
    """Preserve reported pilot operation; do not generalise it to new sites/devices."""
    if type(allow_hypothetical) is not bool:
        raise ValueError('Hypothetical permission must be boolean')
    records = []
    for site in sites:
        for key in KEYS:
            if key == 'telephone':
                status, source = 'reported_operation', 'Existing specialist telephone pathway; usual care'
            elif site.name in PILOT_NAMES and key == 'panda':
                status, source = 'reported_operation', 'ELC2026 item2.1.7; reported operation, not approval certification'
            elif allow_hypothetical:
                status, source = 'hypothetical', 'Analyst scenario: site suitability, credentials, connectivity and approval unverified'
            else:
                status, source = 'unknown', 'No verified site-specific eligibility evidence supplied'
            records.append(Eligibility(site.name, key, status, source))
    return tuple(records)


def validate_policy(sites: list[Site], policy: DeploymentPolicy,
                    eligibility: tuple[Eligibility, ...]) -> None:
    """Reject incomplete scopes, duplicate records and ineligible strategy choices."""
    if not sites or len({s.name for s in sites}) != len(sites) or not isinstance(policy, DeploymentPolicy):
        raise ValueError('Unique nonempty site scope and typed policy required')
    names = {s.name for s in sites}
    if any(not isinstance(e, Eligibility) or e.site not in names for e in eligibility):
        raise ValueError('Unknown site or malformed eligibility')
    records = {(e.site, e.strategy): e for e in eligibility}
    if len(records) != len(eligibility):
        raise ValueError('Duplicate eligibility')
    chosen = dict(policy.assignments)
    if len(chosen) != len(policy.assignments) or set(chosen) != names:
        raise ValueError('Policy must assign every site exactly once')
    for site, strategy in chosen.items():
        record = records.get((site, strategy))
        allowed = {'reported_operation', 'verified_eligible'}
        if policy.conditional:
            allowed.add('hypothetical')
        if record is None or record.status not in allowed:
            raise ValueError(f'Policy eligibility not established: {site}/{strategy}')


def policy_catalogue(sites: list[Site]) -> tuple[DeploymentPolicy, ...]:
    """Two reported-operation policies plus four conditional expansion scenarios."""
    all_phone = tuple((s.name, 'telephone') for s in sites)
    result = [DeploymentPolicy('telephone', all_phone),
              DeploymentPolicy('retain_pilot_only', tuple((s.name, 'panda' if s.name in PILOT_NAMES else 'telephone') for s in sites))]
    for new in ('panda', 'obsbot', 'mobile', 'fixed'):
        result.append(DeploymentPolicy(f'retain_pilot_expand_{new}',
            tuple((s.name, 'panda' if s.name in PILOT_NAMES else new) for s in sites), True))
    return tuple(result)


def _groups(sites: list[Site], policy: DeploymentPolicy) -> dict[str, list[Site]]:
    chosen = dict(policy.assignments)
    return {key: [s for s in sites if chosen[s.name] == key] for key in KEYS
            if key in chosen.values()}


def evaluate_policy(sites: list[Site], policy: DeploymentPolicy, eligibility: tuple[Eligibility, ...],
                    parameters: Parameters, spec: PathwaySpec, assets: tuple[OwnedAsset, ...], *,
                    inputs: dict | None = None, structural_draws: dict | None = None,
                    activity: ActivitySpec | None = None, retain: bool = True,
                    site_calls: dict | None = None) -> dict[str, np.ndarray]:
    """Sum paired exact group outcomes; apply shared paid hub capacity only once.

    These are health-system and bounded family-resource results. Provider fiscal
    allocation and policy-specific safety effects are not invented. Grouping only
    avoids redundant calculation; it does not redraw clinical/systematic priors.
    """
    validate_policy(sites, policy, eligibility)
    validate_estate(assets)
    if type(retain) is not bool:
        raise ValueError('Retention must be boolean')
    site_calls = {} if site_calls is None else site_calls
    if set(site_calls) - {s.name for s in sites}:
        raise ValueError('Unknown site in activity override')
    selected = []
    for key, group in _groups(sites, policy).items():
        names = {s.name for s in group}
        result = compare_v6(group, parameters, spec, inputs=inputs, structural_draws=structural_draws,
                            activity=activity, site_calls={k: v for k, v in site_calls.items() if k in names})
        if retain and key != 'telephone':
            apply_retention(result, group, assets, (key,))
        selected.append(result[key])
    out = {name: sum((r[name] for r in selected), np.zeros_like(selected[0][name]))
           for name in selected[0]}
    out['conditional_rescue_risk'] = np.divide(out['delayed_rescues'], out['initially_local'],
        out=np.zeros_like(out['episodes']), where=out['initially_local'] > 0)
    # Convert the summed hours through the existing capacity function, exactly once.
    hub = hub_cost(out['hub_hours'], np.full_like(out['hub_hours'], 60.), spec)
    out['hub_cash_cost'] = hub['cash_capacity']
    out['hub_capacity_blocks'] = hub['capacity_blocks']
    out['cash_running_cost'] = out['local_ready_cost'] + out['local_workflow_cost'] + out['hub_cash_cost']
    return out


def policy_cash_budget(sites: list[Site], policy: DeploymentPolicy, eligibility: tuple[Eligibility, ...],
                       parameters: Parameters, spec: PathwaySpec, assets: tuple[OwnedAsset, ...], *,
                       activity: ActivitySpec | None = None, retain: bool = True, years: int = 7,
                       site_calls: dict | None = None) -> list[dict]:
    """Combine site-estate purchases with one portfolio-level annual hub capacity bill."""
    result = evaluate_policy(sites, policy, eligibility, parameters, spec, assets,
                             activity=activity, retain=retain, site_calls=site_calls)
    if type(years) is not int or not 1 <= years <= 100:
        raise ValueError('Budget years must be an integer in 1..100')
    tables = []
    for key, group in _groups(sites, policy).items():
        names = {s.name for s in group}
        tables.append(mixed_cash_budget(group, key, assets, parameters, spec, retain=retain,
            years=years, activity=activity,
            site_calls={k: v for k, v in (site_calls or {}).items() if k in names}))
    rows = []
    for i in range(years):
        capital = sum(t[i]['capital'] for t in tables)
        running = float(result['cash_running_cost'][0])
        rows.append({'year': i+1, 'capital': capital,
                     'purchases': sum(t[i]['purchases'] for t in tables),
                     'new_installations': sum(t[i]['new_installations'] for t in tables),
                     'cash_running': running, 'hub_cash_capacity': float(result['hub_cash_cost'][0]),
                     'cash_expenditure': capital+running})
    return rows
