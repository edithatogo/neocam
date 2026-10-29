"""Audit generated analysis and quantify simulation error without changing the model."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PROTECTED = (
    'data/parameters.json', 'data/births_queensland_2022.csv',
    'data/site_classification.json', 'data/population_totals.json',
    'evidence/sources.csv', 'evidence/parameter_register.csv',
    'evidence/literature_parameter_map.csv', 'evidence/search_log.md',
    'evidence/transport_mode_comparison.csv',
)


def prefix_diagnostics(draws: np.ndarray, sizes: tuple[int, ...]) -> list[dict]:
    """Compute nested-prefix diagnostics, not independent scientific replications."""
    if draws.ndim != 1 or len(draws) == 0 or not np.isfinite(draws).all():
        raise ValueError('Finite nonempty one-dimensional draws are required')
    if any(type(n) is not int or n < 1 or n > len(draws) for n in sizes):
        raise ValueError('Prefix sizes must be positive integers within the draw count')
    result = []
    for n in sizes:
        values = draws[:n]
        probability = float(np.mean(values > 0))
        result.append({'draws': n, 'p_saving': probability,
                       'mcse_probability': float(np.sqrt(probability * (1-probability)/n)),
                       'mean_net_saving': float(np.mean(values)),
                       'mcse_mean': float(np.std(values, ddof=1)/np.sqrt(n)) if n > 1 else None})
    return result


def audit_outputs(root: Path = ROOT) -> dict:
    """Compare actual regenerated results against the preserved prior release."""
    now = json.loads((root/'outputs/v4/results_v2.json').read_text())
    before = json.loads((root/'outputs/v2/results_v2.json').read_text())
    same = now['assumptions'] == before['assumptions']
    for section in ('deterministic', 'psa'):
        for key, row in before[section].items():
            for field, value in row.items():
                if isinstance(value, (int, float)):
                    same = same and bool(np.isclose(now[section][key][field], value, rtol=1e-12, atol=1e-8))
    row_counts = {}
    for filename, label in [('scenario_results.csv','scenario_rows'),
                            ('survival_morbidity_frontier.csv','clinical_frontier_rows'),
                            ('site_projection.csv','site_rows')]:
        with (root/'outputs/v4'/filename).open(newline='') as stream:
            row_counts[label] = sum(1 for _ in csv.DictReader(stream))
    hashes = {}
    expected = json.loads((root/"evidence/protected_inputs_v4.json").read_text())["sha256"]
    unchanged = True
    for path in PROTECTED:
        current = (root/path).read_bytes()
        unchanged = unchanged and hashlib.sha256(current).hexdigest() == expected[path]
        hashes[path] = hashlib.sha256(current).hexdigest()
    # Compare retained 20,000-draw tables, not merely headline summaries.
    for portfolio in ('pilot','spokes'):
        name = f'{portfolio}_attenuated_draws.csv'
        a = np.loadtxt(root/'outputs/v4'/name,delimiter=',',skiprows=1)
        b = np.loadtxt(root/'outputs/v2'/name,delimiter=',',skiprows=1)
        same = same and bool(np.allclose(a,b,rtol=1e-9,atol=1e-6))
    return {**row_counts,'psa_structures':len(now['psa']),
            'economic_defaults_unchanged':bool(same),'protected_inputs_unchanged':bool(unchanged),
            'protected_input_hashes':hashes,
            'interpretation':'Numerical/provenance checks; not empirical validation of assumed effects/costs.'}
