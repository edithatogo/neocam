"""Reproducible analysis entry point: no network or private patient data needed."""
from __future__ import annotations
import argparse
import csv
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.statewide import Parameters, Site, load_sites, select_sites, evaluate, psa, index_air_cost, survival_extension, budget_impact


def save_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run(outdir: Path, iterations: int = 20000, seed: int = 20261027) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    p = Parameters(**json.loads((ROOT / 'data/parameters.json').read_text()))
    sites = load_sites()
    selections = {name: select_sites(sites, name) for name in ('pilot', 'spokes', 'rural', 'readiness', 'all_public')}
    deterministic = {name: evaluate(selected, p) for name, selected in selections.items()}
    scenarios = []
    variants = [
        ('Base attenuated effect', {}), ('No incremental video effect', {'odds_ratio': 1}),
        ('Published OR without attenuation', {'odds_ratio': .48}), ('Increased transfers OR1.1', {'odds_ratio': 1.1}),
        ('Full allocated retrieval value', {'marginal_fraction': 1}), ('25% avoidable retrieval resources', {'marginal_fraction': .25}),
        ('No downstream hospital savings', {'downstream_delta': 0}), ('More local hospital cost', {'downstream_delta': -4000}),
        ('Continuation: exclude sunk equipment', {'include_capital': False}), ('Tablet component estimate4500', {'equipment_cost': 4500}),
        ('Commercial cart45000', {'equipment_cost': 45000}), ('10calls/pilot site', {'calls_per_pilot_site': 10}),
        ('15calls/pilot site', {'calls_per_pilot_site': 15}), ('Technical reliability70%', {'reliability': .7}),
        ('Delayed rescue20%', {'rescue_rate': .2}), ('Air-heavy geography', {'mode_air_shift': .25}),
        ('Road-heavy geography', {'mode_air_shift': -.25}), ('Critical casemix50%', {'case_mix': (.2,.3,.5)}),
        ('No avoidable critical-case transfers', {'case_mix': (0,0,1)}),
        ('State uptake40%', {'state_uptake': .4}), ('State uptake100%', {'state_uptake': 1}),
        ('Birth volumes-20%', {'birth_growth': .8}), ('Birth volumes+20%', {'birth_growth': 1.2}),
        ('High shared hub cost', {'hub_annual_cost': 150000, 'capacity_step_cost': 60000}),
        ('No new shared hub cost', {'hub_annual_cost': 0, 'capacity_step_cost': 0}),
        ('Discount0%', {'discount': 0}), ('Discount3%', {'discount': .03}),
        ('Air cost +30% versus CPI', {'air_multiplier': 1.3}),
        ('2018 assumed air-price year', {'air_multiplier': index_air_cost(113.3)/index_air_cost()}),
    ]
    for portfolio in ('pilot','spokes'):
        for label, changes in variants:
            scenarios.append({'portfolio': portfolio, 'scenario': label, **evaluate(selections[portfolio], replace(p, **changes))})
    # Reopening is an explicitly separate hybrid-year scenario, not inserted into 2022 totals.
    weipa = Site('Weipa (2025 reopening scenario)', 32, 2025, 'rural_proxy', 'remote')
    reopening = evaluate(selections['spokes'] + [weipa], p)
    psas = {}
    for portfolio in ('pilot', 'spokes'):
        for mode in ('attenuated','null','published','skeptical'):
            result = psa(selections[portfolio], n=iterations, seed=seed, parameters=p, effect_mode=mode)
            key = portfolio + '_' + mode
            psas[key] = result['summary']
            if mode == 'attenuated':
                draws = result['draws']
                names = list(draws)
                np.savetxt(outdir / f'{key}_draws.csv', np.column_stack([draws[k] for k in names]),
                           delimiter=',', header=','.join(names), comments='', fmt='%.10g')
                # Partial rank correlations are not causal sensitivity estimates; Spearman ranks prioritise drivers only.
                ranking = []
                ranks_net = np.argsort(np.argsort(draws['net_saving']))
                for variable in ('effect_or','marginal_fraction','air_anchor','downstream_delta','calls_per_pilot_site'):
                    ranks = np.argsort(np.argsort(draws[variable]))
                    ranking.append({'portfolio': portfolio, 'parameter': variable,
                                    'spearman_rank_correlation': float(np.corrcoef(ranks, ranks_net)[0,1])})
                save_csv(outdir / f'{portfolio}_sensitivity_ranks.csv', ranking)
                # Annual patient-count variation conditional on each parameter draw, with monotone paired transfer changes.
                rng = np.random.default_rng(seed + 99)
                observed_calls = rng.poisson(draws['consultations'])
                probability_change = np.clip(np.abs(draws['avoided_transfers']) / np.maximum(draws['consultations'], 1e-12), 0, 1)
                changed = rng.binomial(observed_calls, probability_change) * np.sign(draws['avoided_transfers'])
                per_change = np.divide(draws['gross_resource_benefit'], draws['avoided_transfers'],
                                       out=np.zeros(iterations), where=draws['avoided_transfers'] != 0)
                realised_net = changed * per_change - draws['programme_cost']
                qq = np.quantile(realised_net,[.025,.5,.975])
                psas[key]['annual_realisation_interval'] = [float(v) for v in qq]
                psas[key]['annual_realisation_interpretation'] = 'Extra stochastic year-to-year variation; paired monotone-transfer approximation, not additional evidence'
    site_rows = []
    for site in sites:
        r = evaluate([site], p)
        site_rows.append({**asdict(site), 'projected_calls': r['consultations'], 'allocated_programme_cost': r['programme_cost'],
                          'net_saving_before_shared_hub_cost': r['net_saving'],
                          'primary_spoke_portfolio': site.group not in {'hub','readiness'},
                          'current_capability_verified': False})
    save_csv(outdir / 'site_projection.csv', site_rows)
    save_csv(outdir / 'scenario_results.csv', scenarios)
    frontier = []
    for gain in (0,.001,.005,.01):
        for morbidity in (.1,.35,.7):
            for discount in (0,.03,.05):
                r = survival_extension(37.5,gain,morbidity,discount=discount)
                for wtp in (0,50000,100000):
                    frontier.append({'survival_gain': gain, 'major_share': morbidity, 'discount': discount, 'wtp': wtp, **r,
                                     'total_nmb_including_acute_base': deterministic['pilot']['net_saving'] + wtp*r['qalys'] - r['costs']})
    save_csv(outdir / 'survival_morbidity_frontier.csv', frontier)
    for name in ('pilot','spokes'):
        save_csv(outdir / f'{name}_five_year_budget.csv', budget_impact(selections[name],5,True,p))
    # QEP/QWAU unknown: this is an explicitly hypothetical normalisation grid, never actual QLD payment.
    funding = []
    for localisation in (.9,1,1.1):
        for price_ratio in (.9,1,1.1):
            funding.append({'nwau':1,'assumed_qwau_per_nwau':localisation,'nep':7418,'assumed_qep_to_nep_ratio':price_ratio,
                            'national_benchmark':7418,'hypothetical_queensland_benchmark':7418*localisation*price_ratio,
                            'status':'sensitivity only; QEP and localisation unverified'})
    save_csv(outdir / 'funding_sensitivity.csv', funding)
    input_hashes = {str(f.relative_to(ROOT)): hashlib.sha256(f.read_bytes()).hexdigest()
                    for folder in ('data','evidence') for f in sorted((ROOT/folder).glob('*')) if f.is_file()}
    output = {'version':'2.0.0-preliminary','as_of':'2026-10-27','price_basis':'June2026 cost point / FY2026-27 NEP; source-specific exceptions explicit',
              'assumptions':asdict(p),'indexed_air_anchor': index_air_cost(), 'deterministic':deterministic,
              'psa':psas,'scenario_count':len(scenarios),'clinical_scenario_count':len(frontier),
              'reopening_weipa_2025_scenario':reopening, 'input_sha256':input_hashes,
              'scope_limits':['2022 historic public birth roster; not all 2026 operating sites','private births aggregate13741; no site-level private expansion cost',
                              'ANZNN membership is not current CSCF accreditation','effect and price uncertainty are assumptions, not local posterior estimates',
                              'unknown QEP is not imputed as NEP','no calibrated mortality effect','hosted CI and latest dependency install not verified here']}
    (outdir/'results_v2.json').write_text(json.dumps(output,indent=2)+'\n')
    return output


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, default=ROOT/'outputs/v2')
    parser.add_argument('--iterations', type=int, default=20000)
    parser.add_argument('--seed', type=int, default=20261027)
    args=parser.parse_args()
    result=run(args.out,args.iterations,args.seed)
    for name in ('pilot','spokes'):
        print(name,result['deterministic'][name])
        print(name+'_PSA',result['psa'][name+'_attenuated'])
