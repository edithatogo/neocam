"""Active-kernel contracts supplement, but do not pretend to execute, Hypothesis."""

from pathlib import Path

import numpy as np

from scripts.analyse_v7 import evaluate_perspectives
from src.audit_v7 import sample_v7
from src.pathways_v6 import PathwaySpec, compare_v6
from src.portfolios_v7 import portfolio
from src.statewide import Parameters


def test_generative_scope_is_active_model():
    text = Path("quality/hypothesis_properties.py").read_text(encoding="utf-8")
    assert "compare_v6" in text
    assert "sample_v7" in text
    assert "evaluate_perspectives" in text


def test_active_null_and_mass_conservation_across_seeds():
    sites = portfolio("pilot")
    p = Parameters(odds_ratio=1)
    s = PathwaySpec()
    for seed in range(8):
        x, e = sample_v7(p, s, 96, seed, "null")
        r, ledgers, _ = evaluate_perspectives(sites, p, s, x, e)
        for key, a in r.items():
            np.testing.assert_allclose(a["gross_resource_benefit"], 0, atol=1e-7)
            np.testing.assert_allclose(
                a["immediate_transfers"] + a["delayed_rescues"] + a["final_local"], a["consultations"], atol=1e-9
            )
            np.testing.assert_allclose(
                ledgers[key]["state"] + ledgers[key]["commonwealth"] + ledgers[key]["patient_family"],
                ledgers[key]["societal_bounded"],
                atol=1e-7,
            )


def test_critical_cases_receive_no_unsupported_avoidance_credit():
    p = Parameters(case_mix=(0, 0, 1))
    s = PathwaySpec()
    x, e = sample_v7(p, s, 100, 31)
    r = compare_v6(portfolio("pilot"), p, s, inputs=x, structural_draws=e)
    for arm in r.values():
        np.testing.assert_allclose(arm["avoided_transfers"], 0, atol=1e-9)


def test_additional_contact_question_is_explicit_not_fitted():
    path = Path("conductor/validation-v12.md")
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "contacts per infant" in text
    assert "not executed" in text
