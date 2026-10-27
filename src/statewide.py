"""Panda Vision v2: auditable, assumption-based cohort evaluation.

This is not a clinical prediction tool. All current effect and cost projections
are conditional on explicitly labelled, mostly non-local priors.
"""
from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Site:
    name: str
    births: int
    year: int
    group: str
    geography: str
    pilot: bool = False


@dataclass(frozen=True)
class Parameters:
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

    def __post_init__(self) -> None:
        for key, value in asdict(self).items():
            if isinstance(value, (float, int)) and not isinstance(value, bool):
                if not math.isfinite(value):
                    raise ValueError(f'{key} must be finite')
        for key in ('state_uptake', 'reliability', 'rescue_rate', 'marginal_fraction'):
            if not 0 <= getattr(self, key) <= 1:
                raise ValueError(f'{key} must be in [0,1]')
        for key in ('life_years', 'odds_ratio', 'birth_growth', 'capacity_threshold'):
            if getattr(self, key) <= 0:
                raise ValueError(f'{key} must be positive')
        for key in ('equipment_cost', 'check_minutes', 'loaded_hour', 'support',
                    'training', 'workflow_per_call', 'calls_per_pilot_site',
                    'road_cost', 'air_multiplier', 'hub_annual_cost', 'rescue_premium',
                    'capacity_step_cost', 'discount'):
            if getattr(self, key) < 0:
                raise ValueError(f'{key} cannot be negative')
        if len(self.case_mix) != 3 or not all(math.isfinite(v) and v >= 0 for v in self.case_mix):
            raise ValueError('case_mix must contain three non-negative finite shares')
        if not math.isclose(sum(self.case_mix), 1.0):
            raise ValueError('case_mix must sum to one')
        if len(self.baseline_transfer) != 3 or not all(0 <= v <= 1 for v in self.baseline_transfer):
            raise ValueError('baseline_transfer must contain three probabilities')
        if not -0.6 <= self.mode_air_shift <= 0.6:
            raise ValueError('mode_air_shift outside scenario bounds')


def load_sites(path: Path | None = None) -> list[Site]:
    """Collapse co-located birth-centre rows; retain every published public birth."""
    cfg = json.loads((ROOT / 'data/site_classification.json').read_text())
    totals: dict[str, int] = {}
    with (path or ROOT / 'data/births_queensland_2022.csv').open(newline='') as f:
        for row in csv.DictReader(f):
            name = cfg['aliases'].get(row['facility'], row['facility'])
            count = int(row['births'])
            if count < 0:
                raise ValueError('negative birth count')
            totals[name] = totals.get(name, 0) + count
    sites = []
    for name, births in sorted(totals.items()):
        if name in cfg['nicu_anznn_2023']:
            group = 'hub'
        elif name in cfg['scn_anznn_2023']:
            group = 'scn'
        elif births < 20:
            group = 'readiness'
        elif births >= 1000:
            group = 'regional_proxy'
        else:
            group = 'rural_proxy'
        geography = ('remote' if name in cfg['geographic_remote_proxy'] else
                     'metro' if name in cfg['geographic_metro_proxy'] else 'regional')
        sites.append(Site(name, births, 2022, group, geography, name in cfg['pilot_sites']))
    return sites


def select_sites(sites: list[Site], portfolio: str) -> list[Site]:
    if portfolio == 'pilot':
        return [s for s in sites if s.pilot]
    if portfolio == 'spokes':
        return [s for s in sites if s.group not in {'hub', 'readiness'}]
    if portfolio == 'rural':
        return [s for s in sites if s.group == 'rural_proxy']
    if portfolio == 'readiness':
        return [s for s in sites if s.group == 'readiness']
    if portfolio == 'all_public':
        return list(sites)
    raise ValueError(f'Unknown portfolio: {portfolio}')


def index_air_cost(base_cpi: float = 115.125, target_cpi: float = 102.03) -> float:
    """AUD18670, assumed calendar2019 prices -> June2026 point prices.

    Convert old2011-12-base annual average to Sep-month2025 base first.
    Rounded published conversion causes minor arithmetic imprecision.
    """
    if not math.isfinite(base_cpi) or not math.isfinite(target_cpi) or min(base_cpi, target_cpi) <= 0:
        raise ValueError('CPI inputs must be finite and positive')
    return 18_670.0 * target_cpi / (base_cpi * (99.73 / 143.6))


def annuity(capital: float, years: float, rate: float) -> float:
    if not all(math.isfinite(x) for x in (capital, years, rate)) or years <= 0 or min(capital, rate) < 0:
        raise ValueError('Invalid annuity input')
    return capital / years if rate == 0 else capital * rate / (1 - (1 + rate) ** -years)


def funding_ledger(nwau: float, qwau: float | None, nep: float, qep: float | None) -> dict[str, float | None]:
    for value in (nwau, qwau, nep, qep):
        if value is not None and (not math.isfinite(value) or value < 0):
            raise ValueError('Funding inputs must be non-negative and finite or missing')
    return {'national_benchmark': nwau * nep,
            'queensland_benchmark': None if qwau is None or qep is None else qwau * qep}


def mchs_support(year: int) -> str:
    return 'historical_interface_only' if year in (2024, 2025) else 'official_GEN_WAU_export_required'


def _odds(p: np.ndarray, odds_ratio: np.ndarray) -> np.ndarray:
    return odds_ratio * p / (1 - p + odds_ratio * p)


def _base_arrays(p: Parameters, n: int) -> dict[str, np.ndarray]:
    values = {k: np.full(n, v, dtype=float) for k, v in asdict(p).items()
              if isinstance(v, (float, int)) and not isinstance(v, bool)}
    values['case_mix'] = np.tile(p.case_mix, (n, 1))
    values['baseline_transfer'] = np.tile(p.baseline_transfer, (n, 1))
    values['air_anchor'] = np.full(n, index_air_cost() * p.air_multiplier)
    return values


def _site_modes(site: Site, shift: np.ndarray) -> np.ndarray:
    # Analyst geographic priors. NOT actual facility-specific dispatch proportions.
    base = {'metro': (.85, .10, .05), 'regional': (.60, .25, .15),
            'remote': (.15, .35, .50)}[site.geography]
    road = np.clip(base[0] - shift, .02, .98)
    rotary = (1 - road) * base[1] / (base[1] + base[2])
    return np.column_stack((road, rotary, 1 - road - rotary))


def _kernel(sites: list[Site], p: Parameters, x: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    n = len(x['odds_ratio'])
    out = {k: np.zeros(n) for k in ('consultations', 'avoided_transfers', 'programme_cost',
                                   'gross_resource_benefit', 'family_benefit', 'cash_running_cost')}
    for site in sites:
        if site.pilot:
            calls = x['calls_per_pilot_site']
        else:
            factor = {'hub': .0, 'scn': .5, 'regional_proxy': .65,
                      'rural_proxy': 1.0, 'readiness': 1.0}[site.group]
            geographic = 1.25 if site.geography == 'remote' else 1.0
            calls = (site.births * (3 * x['calls_per_pilot_site'] / 486) * factor * geographic
                     * x['birth_growth'] * x['state_uptake'])
        # Critical cases remain transfers; possible survival benefits are separate.
        p0 = x['baseline_transfer']
        p1 = p0.copy()
        p1[:, :2] = _odds(p0[:, :2], x['odds_ratio'][:, None])
        effect = np.sum(x['case_mix'] * (p0 - p1), axis=1) * x['reliability']
        apparent_avoided = calls * effect
        rescue = np.maximum(apparent_avoided, 0) * x['rescue_rate']
        avoided = apparent_avoided - rescue
        modes = _site_modes(site, x['mode_air_shift'])
        # Both air modes share the source anchor, with assumed mode multipliers.
        allocated_transport = (modes[:, 0] * x['road_cost'] + modes[:, 1] * x['air_anchor'] * 1.2
                               + modes[:, 2] * x['air_anchor'] * .9)
        marginal_transport = allocated_transport * x['marginal_fraction']
        benefit = avoided * (marginal_transport + x['downstream_delta']) - rescue * x['rescue_premium']
        rate = x['discount']
        annual_capital = np.divide(x['equipment_cost'], x['life_years'])
        positive = rate > 0
        annual_capital[positive] = (x['equipment_cost'][positive] * rate[positive]
                                   / (1 - (1 + rate[positive]) ** -x['life_years'][positive]))
        cash = (52 * x['check_minutes'] / 60 * x['loaded_hour'] + x['support']
                + x['training'] + calls * x['workflow_per_call'])
        out['consultations'] += calls
        out['avoided_transfers'] += avoided
        out['programme_cost'] += cash + (annual_capital if p.include_capital else 0)
        out['cash_running_cost'] += cash
        out['gross_resource_benefit'] += benefit
        out['family_benefit'] += avoided * x['family_delta']
    if len(sites) > 3:
        extra_capacity = np.maximum(0, np.ceil((out['consultations'] - x['capacity_threshold'])
                                              / x['capacity_threshold']))
        hub = x['hub_annual_cost'] + extra_capacity * x['capacity_step_cost']
        out['programme_cost'] += hub
        out['cash_running_cost'] += hub
    out['net_saving'] = out['gross_resource_benefit'] - out['programme_cost']
    out['societal_net_saving'] = out['net_saving'] + out['family_benefit']
    return out


def evaluate(sites: list[Site], parameters: Parameters | None = None) -> dict[str, Any]:
    p = parameters or Parameters()
    results = _kernel(sites, p, _base_arrays(p, 1))
    result: dict[str, Any] = {k: float(v[0]) for k, v in results.items()}
    result.update({'site_count': len(sites), 'births_2022': sum(s.births for s in sites),
                   'interpretation': 'conditional scenario, not observed savings'})
    return result


def psa(sites: list[Site], n: int = 20_000, seed: int = 20261027,
        parameters: Parameters | None = None, effect_mode: str = 'attenuated') -> dict[str, Any]:
    """Common state-wide draws preserve systematic uncertainty at all scales."""
    if n < 2 or n > 1_000_000:
        raise ValueError('n must be between 2 and 1000000')
    if effect_mode not in {'attenuated', 'published', 'null', 'skeptical'}:
        raise ValueError('Unsupported effect model')
    p = parameters or Parameters()
    rng = np.random.default_rng(seed)
    x = _base_arrays(p, n)
    x['calls_per_pilot_site'] = rng.triangular(10, 12.5, 15, n) * (p.calls_per_pilot_site / 12.5)
    se = (math.log(.90) - math.log(.26)) / (2 * 1.96)
    if effect_mode == 'null':
        x['odds_ratio'] = np.ones(n)
    else:
        attenuation = 1 if effect_mode == 'published' else .5 if effect_mode == 'attenuated' else 0
        # .35 is an analyst transportability SD; not a fitted meta-analytic variance.
        x['odds_ratio'] = np.exp(rng.normal(attenuation * math.log(.48),
                                            math.sqrt((attenuation * se)**2 + .35**2), n))
    x['baseline_transfer'] = np.column_stack([
        rng.beta(prob * 20, (1 - prob) * 20, n) if 0 < prob < 1 and j < 2
        else np.full(n, prob) for j, prob in enumerate(p.baseline_transfer)])
    shares = np.asarray(p.case_mix)
    active = shares > 0
    x['case_mix'] = np.zeros((n, 3))
    x['case_mix'][:, active] = rng.dirichlet(shares[active] * 20, n)
    x['reliability'] = rng.beta(19, 1, n) * (p.reliability / .95)
    x['reliability'] = np.clip(x['reliability'], 0, 1)
    x['rescue_rate'] = np.clip(rng.beta(1, 19, n) * (p.rescue_rate / .05), 0, 1)
    x['rescue_premium'] = rng.triangular(0, 10000, 30000, n) * p.rescue_premium / 10000
    x['air_anchor'] = rng.lognormal(math.log(index_air_cost()), .35, n) * p.air_multiplier
    x['road_cost'] = rng.triangular(2000, 4000, 8000, n) * p.road_cost / 4000
    x['marginal_fraction'] = np.clip(rng.beta(2, 2, n) * p.marginal_fraction / .5, 0, 1)
    # Retained babies may increase local costs: negative differences are permitted.
    x['downstream_delta'] = rng.triangular(-4000, 2000, 10000, n) + (p.downstream_delta - 2000)
    x['family_delta'] = rng.triangular(0, 1500, 4000, n) * p.family_delta / 1500
    x['equipment_cost'] = rng.triangular(8000, 10000, 15000, n) * p.equipment_cost / 10000
    x['life_years'] = rng.triangular(3, 5, 7, n) * p.life_years / 5
    x['check_minutes'] = rng.triangular(5, 10, 20, n) * p.check_minutes / 10
    x['support'] = rng.triangular(0, 300, 1000, n) * p.support / 300
    x['training'] = rng.triangular(100, 400, 1200, n) * p.training / 400
    x['workflow_per_call'] = rng.triangular(0, 75, 175, n) * p.workflow_per_call / 75
    x['birth_growth'] = rng.triangular(.8, 1, 1.2, n) * p.birth_growth
    x['mode_air_shift'] = np.clip(rng.normal(p.mode_air_shift, .10, n), -.6, .6)
    draws = _kernel(sites, p, x)
    draws['effect_or'] = x['odds_ratio']
    draws['marginal_fraction'] = x['marginal_fraction']
    draws['air_anchor'] = x['air_anchor']
    draws['downstream_delta'] = x['downstream_delta']
    draws['calls_per_pilot_site'] = x['calls_per_pilot_site']
    q = np.quantile(draws['net_saving'], [.025, .5, .975])
    prob = float(np.mean(draws['net_saving'] > 0))
    # Cost-only EVPI is not a valuation of the unquantified clinical consequences.
    evpi = float(np.mean(np.maximum(draws['net_saving'], 0)) - max(np.mean(draws['net_saving']), 0))
    return {'summary': {'iterations': n, 'seed': seed, 'effect_mode': effect_mode,
                        'mean': float(np.mean(draws['net_saving'])), 'median': float(q[1]),
                        'lower': float(q[0]), 'upper': float(q[2]), 'probability_cost_saving': prob,
                        'mcse_probability': math.sqrt(prob * (1 - prob) / n),
                        'mean_avoided_transfers': float(np.mean(draws['avoided_transfers'])),
                        'mean_consultations': float(np.mean(draws['consultations'])),
                        'mean_programme_cost': float(np.mean(draws['programme_cost'])),
                        'annual_cost_only_evpi': max(evpi, 0),
                        'interpretation': 'conditional researcher-prior PSA; not an empirical posterior'},
            'draws': draws}


def survival_extension(consultations: float, survival_gain: float, major_share: float,
                       discount: float = .05, years: int = 40,
                       utility_no_major: float = .9, utility_major: float = .5,
                       annual_cost_no_major: float = 1000, annual_cost_major: float = 20000) -> dict[str, float]:
    """Exploratory survival/morbidity frontier; all effects/utilities/costs assumed.

    Forty-year constant survival is a scenario, not a fitted survival model.
    No value judgement about disability or lifetime clinical benefit is implied.
    """
    vals = (consultations, survival_gain, major_share, discount, utility_no_major,
            utility_major, annual_cost_no_major, annual_cost_major)
    if not all(math.isfinite(v) for v in vals) or consultations < 0 or years <= 0 or discount < 0:
        raise ValueError('Invalid survival scenario')
    if not all(0 <= v <= 1 for v in (survival_gain, major_share, utility_no_major, utility_major)):
        raise ValueError('Probabilities and utilities must lie in [0,1]')
    if min(annual_cost_no_major, annual_cost_major) < 0:
        raise ValueError('Negative annual cost')
    pv = sum((1 + discount) ** -y for y in range(1, years + 1))
    extra = consultations * survival_gain
    major = extra * major_share
    qalys = pv * (major * utility_major + (extra - major) * utility_no_major)
    costs = pv * (major * annual_cost_major + (extra - major) * annual_cost_no_major)
    return {'extra_survivors': extra, 'major_morbidity_survivors': major, 'qalys': qalys, 'costs': costs}


def budget_impact(sites: list[Site], years: int = 5, replacement: bool = True,
                  parameters: Parameters | None = None) -> list[dict[str, float]]:
    if years < 1:
        raise ValueError('years must be positive')
    p = parameters or Parameters()
    r = evaluate(sites, p)
    records = []
    for year in range(1, years + 1):
        capital = len(sites) * p.equipment_cost if replacement and (year - 1) % max(1, round(p.life_years)) == 0 else 0
        cash = capital + r['cash_running_cost']
        records.append({'year': year, 'cash_expenditure': cash, 'capital': capital,
                        'resource_net_saving_excluding_funding': r['gross_resource_benefit'] - cash})
    return records
