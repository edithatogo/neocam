"""Generate contact/episode and eligible deployment comparisons from declared inputs."""
from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import re
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.activity import ActivitySpec
from src.audit_v7 import sample_v7
from src.configuration import exact_keys, load_configuration, strict_json
from src.deployment import eligibility_catalogue, evaluate_policy, policy_cash_budget, policy_catalogue
from src.pathways_v6 import compare_v6
from src.perspectives_v7 import optimal_probabilities
from src.portfolios_v7 import portfolio
from src.statewide import _base_arrays

REVIEW_ROLES = ('neonatal_retrieval', 'health_economics', 'technical', 'consumer_rural')


def load_refinements(path: Path) -> dict:
    """Validate researcher scenarios before generating any output files."""
    data = strict_json(path)
    exact_keys(data, {'schema_version', 'activity_scenarios', 'effect_modes', 'budget_years', 'assumption_label'}, 'Refinements')
    if type(data['schema_version']) is not int or data['schema_version'] != 1:
        raise ValueError('Unknown refinements schema')
    rows = data['activity_scenarios']
    if not isinstance(rows, list) or not rows:
        raise ValueError('Nonempty activity scenarios required')
    seen = set()
    semantics = set()
    for row in rows:
        exact_keys(row, {'id', 'activity_basis', 'contacts_per_episode'}, 'Activity scenario')
        identity = row['id']
        if not isinstance(identity, str) or not re.fullmatch(r'[a-z0-9_]+', identity) or identity in seen:
            raise ValueError('Unique safe activity identifiers required')
        seen.add(identity)
        activity = ActivitySpec(row['activity_basis'], row['contacts_per_episode'])
        signature = (activity.activity_basis, activity.contacts_per_episode)
        if signature in semantics:
            raise ValueError('Duplicate semantic activity scenario')
        semantics.add(signature)
    modes = data['effect_modes']
    if (not isinstance(modes, list) or not modes or any(not isinstance(x, str) for x in modes)
            or len(set(modes)) != len(modes) or set(modes)-{'attenuated', 'null', 'skeptical', 'published'}):
        raise ValueError('Invalid or duplicate effect modes')
    if type(data['budget_years']) is not int or not 1 <= data['budget_years'] <= 100:
        raise ValueError('Budget years must be in 1..100')
    if not isinstance(data['assumption_label'], str) or not data['assumption_label'].strip():
        raise ValueError('Assumption disclosure is required')
    return data


def summary(values: np.ndarray) -> dict:
    """Summarise paired researcher-prior draws, not fitted clinical predictions."""
    low, median, high = np.quantile(values, [.025, .5, .975])
    return {'mean': float(values.mean()), 'lower': float(low), 'median': float(median), 'upper': float(high)}


def write_csv(output: Path, name: str, rows: list[dict]) -> None:
    if not rows:
        raise ValueError(f'Empty output scope: {name}')
    with (output/name).open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def pending_reviews(snapshot: str) -> dict:
    """Empty external review requests, never simulated or auto-approved signatures."""
    questions = {
        'neonatal_retrieval': 'Do episode counts, transfer timing, local capability and appropriate escalation look plausible? More transfers can mean better recognition; identify potential unsafe retention.',
        'health_economics': 'Are incremental workload, avoidable resources, shared capacity and site-estate capital/replacement coherent? Are fixed-contact versus fixed-episode interpretations appropriate?',
        'technical': 'Recalculate a small independent case without importing model helpers; check shared priors, population and cost identities against exact source and inputs.',
        'consumer_rural': 'Assess separation, access, family burden, cultural safety and whether the bounded family-cost account misses material consequences.',
    }
    return {'snapshot_sha256': snapshot, 'independent_validation': False,
            'review_type': 'external review requested, not executed',
            'reviews': [{'role': role, 'identity': '', 'independent': False, 'status': 'pending',
                         'conflicts': '', 'date': '', 'snapshot_sha256': snapshot, 'finding_summary': '',
                         'findings': [], 'evidence': [], 'question': questions[role]} for role in REVIEW_ROLES]}


def snapshot_identity(root: Path, declared: dict) -> str:
    """Bind external-review requests to numerical/report source and resolved inputs."""
    from quality.artifacts import calculation_inputs
    identity = {'declared_inputs': declared, 'calculation_inputs': calculation_inputs(root)}
    return hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()


def main(config_path: Path | None = None, refinements_path: Path | None = None,
         output_dir: Path | None = None) -> dict:
    """Run paired policy analysis; all approvals, health effects and gaps stay explicit."""
    config = load_configuration(ROOT, config_path)
    ref_path = (refinements_path or ROOT/'config/refinements.json').resolve()
    if not ref_path.is_relative_to(ROOT):
        raise ValueError('Refinement configuration must be inside repository')
    refinements = load_refinements(ref_path)
    p, s, n = config.parameters, config.pathways, config.draws
    output = (output_dir or ROOT/'outputs/v13-refinements').resolve()
    if not output.is_relative_to(ROOT/'outputs') or output == ROOT/'outputs':
        raise ValueError('New output must be a subdirectory of repository outputs')
    if output.exists():
        raise FileExistsError('Refusing to overwrite an existing analysis directory')
    output.mkdir(parents=True)
    snapshot = config.snapshot()
    snapshot['refinements_sha256'] = hashlib.sha256(ref_path.read_bytes()).hexdigest()
    snapshot['refinements'] = refinements
    snapshot_digest = snapshot_identity(ROOT, snapshot)
    snapshot['analysis_snapshot_sha256'] = snapshot_digest
    (output/'resolved_inputs.json').write_text(json.dumps(snapshot, indent=2)+'\n')
    deterministic, results, rankings, predictive, budgets, assignments, eligibility_rows = [], [], [], [], [], [], []
    checks = []
    for network in config.portfolios:
        sites = portfolio(network)
        policies = policy_catalogue(sites)
        eligibility = eligibility_catalogue(sites, allow_hypothetical=True)
        eligibility_rows.extend({'portfolio': network, **asdict(record)} for record in eligibility)
        for policy in policies:
            assignments.extend({'portfolio': network, 'policy': policy.name, 'conditional_policy': policy.conditional,
                                'site': site, 'strategy': technology} for site, technology in policy.assignments)
        for row in refinements['activity_scenarios']:
            activity = ActivitySpec(row['activity_basis'], row['contacts_per_episode'])
            for policy in policies:
                arm = evaluate_policy(sites, policy, eligibility, p, s, config.owned_assets, activity=activity)
                deterministic.append({'portfolio': network, 'activity_id': row['id'], 'activity_basis': activity.activity_basis,
                    'contacts_per_episode': activity.contacts_per_episode, 'policy': policy.name, 'conditional_policy': policy.conditional,
                    **{k: float(arm[k][0]) for k in ('episodes', 'contacts', 'eventual_transfers', 'delayed_rescues',
                        'final_local', 'avoided_transfers', 'net_saving', 'programme_cost', 'hub_hours', 'hub_cash_cost')},
                    'initial_purchase_capital': float(arm['incremental_purchase_capital'][0])})
                for budget in policy_cash_budget(sites, policy, eligibility, p, s, config.owned_assets,
                                                activity=activity, years=refinements['budget_years']):
                    budgets.append({'portfolio': network, 'activity_id': row['id'], 'policy': policy.name, **budget})
            for effect in refinements['effect_modes']:
                x, e = sample_v7(p, s, n=n, seed=config.seed, effect_mode=effect)
                evaluated = [evaluate_policy(sites, policy, eligibility, p, s, config.owned_assets,
                             inputs=x, structural_draws=e, activity=activity) for policy in policies]
                for policy, arm in zip(policies, evaluated, strict=True):
                    base = {'portfolio': network, 'activity_id': row['id'], 'activity_basis': activity.activity_basis,
                            'contacts_per_episode': activity.contacts_per_episode, 'effect_mode': effect,
                            'policy': policy.name, 'conditional_policy': policy.conditional}
                    for metric, label in (('net_saving', 'health_system'), ('net_with_family_extension', 'societal_bounded')):
                        results.append({**base, 'perspective': label, **summary(arm[metric]),
                                        'probability_resource_saving': float(np.mean(arm[metric] > 0))})
                    for metric in ('episodes', 'contacts', 'immediate_transfers', 'delayed_rescues',
                                   'final_local', 'eventual_transfers', 'hub_hours', 'hospital_benchmark_cost'):
                        predictive.append({**base, 'metric': metric, **summary(arm[metric])})
                    mass = np.max(np.abs(arm['eventual_transfers']+arm['final_local']-arm['episodes']))
                    checks.append({'portfolio': network, 'activity_id': row['id'], 'effect_mode': effect,
                        'policy': policy.name, 'cohort_residual': float(mass),
                        'all_finite': all(np.isfinite(a).all() for a in arm.values()),
                        'clinical_validation': False})
                for decision_set in ('reported_operation', 'conditional_expansion'):
                    selected = [i for i, policy in enumerate(policies) if decision_set == 'conditional_expansion' or not policy.conditional]
                    for metric, view in (('net_saving', 'health_system'), ('net_with_family_extension', 'societal_bounded')):
                        matrix = np.column_stack([evaluated[i][metric] for i in selected])
                        probs = optimal_probabilities(matrix)
                        for j, i in enumerate(selected):
                            rankings.append({'portfolio': network, 'activity_id': row['id'], 'effect_mode': effect,
                                'decision_set': decision_set, 'perspective': view, 'policy': policies[i].name,
                                'expected_net_value': float(matrix[:, j].mean()), 'probability_optimal': float(probs[j]),
                                'expected_regret': float((matrix.max(axis=1)-matrix[:, j]).mean()),
                                'status': 'cost-only conditional decision, not procurement or clinical recommendation'})
    for name, rows in [('policy_deterministic.csv', deterministic), ('policy_psa.csv', results),
                       ('policy_rankings.csv', rankings), ('policy_predictive.csv', predictive),
                       ('policy_budget.csv', budgets), ('policy_assignments.csv', assignments),
                       ('eligibility.csv', eligibility_rows), ('checks.csv', checks)]:
        write_csv(output, name, rows)
    (output/'review_packet.json').write_text(json.dumps(pending_reviews(snapshot_digest), indent=2)+'\n')
    metadata = {'version': '13.0.0', 'draws': n, 'seed': config.seed, 'portfolios': list(config.portfolios),
                'independent_validation': False, 'clinical_appropriateness_estimated': False,
                'snapshot_sha256': snapshot_digest, 'max_cohort_residual': max(r['cohort_residual'] for r in checks),
                'all_finite': all(r['all_finite'] for r in checks),
                'counts': {'paired_policy_scenarios': len(checks), 'psa_result_rows': len(results),
                           'ranking_rows': len(rankings), 'predictive_rows': len(predictive), 'budget_rows': len(budgets)},
                'assumptions': refinements['assumption_label'],
                'scope': 'Health-system and bounded family resources; arbitrary mixed-policy provider/fiscal allocation is not inferred. Original six-perspective reference retained separately.',
                'clinical_unit': 'episode; consultations is legacy episode alias, contacts are separate workload events; not unique infants over repeated admissions',
                'reliability': 'episode-level video delivery; repeated contacts are not independent opportunities for success',
                'cost_equivalence': 'Reference assumes equal video effect/reliability by technology; lower costs alone can dominate under that assumption.'}
    (output/'results.json').write_text(json.dumps(metadata, indent=2)+'\n')
    print(json.dumps(metadata, indent=2))
    return metadata


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT/'config/reference.json')
    parser.add_argument('--refinements', type=Path, default=ROOT/'config/refinements.json')
    parser.add_argument('--output', type=Path, default=ROOT/'outputs/v13-refinements')
    args = parser.parse_args()
    main(args.config, args.refinements, args.output)
