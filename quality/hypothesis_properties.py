"""Generative invariants, explicitly required by the full assurance profile.

Missing Hypothesis is an unavailable gate, not a successful skipped test suite.
"""
from dataclasses import replace
import math

from hypothesis import given, settings, strategies as st
import numpy as np

from src.statewide import Parameters, Site, annuity, evaluate, funding_ledger, psa

settings.register_profile('panda_ci', max_examples=150, deadline=None, derandomize=True)
settings.load_profile('panda_ci')
SITE = Site('Audit site', 100, 2022, 'rural_proxy', 'regional', True)
FINITE_MONEY = st.floats(min_value=0, max_value=1_000_000, allow_nan=False, allow_infinity=False)
PROBABILITY = st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False)


@given(FINITE_MONEY, st.floats(min_value=1, max_value=100, allow_nan=False, allow_infinity=False))
def test_zero_discount_annuity(capital: float, years: float) -> None:
    assert math.isclose(annuity(capital, years, 0), capital / years)


@given(FINITE_MONEY, st.floats(min_value=1e-20, max_value=1e-12, allow_nan=False, allow_infinity=False))
def test_tiny_discount_is_continuous(capital: float, rate: float) -> None:
    assert math.isclose(annuity(capital, 5, rate), capital / 5, rel_tol=1e-10, abs_tol=1e-10)


@given(FINITE_MONEY, PROBABILITY)
def test_zero_effect_has_no_transfer_benefit(cost: float, reliability: float) -> None:
    result = evaluate([SITE], Parameters(odds_ratio=1, equipment_cost=cost, reliability=reliability))
    assert result['avoided_transfers'] == 0
    assert result['gross_resource_benefit'] == 0
    assert result['net_saving'] <= 0


@given(st.floats(min_value=.01, max_value=10, allow_nan=False, allow_infinity=False), PROBABILITY)
def test_transfer_change_bounded_by_consultations(effect: float, reliability: float) -> None:
    result = evaluate([SITE], Parameters(odds_ratio=effect, reliability=reliability))
    assert abs(result['avoided_transfers']) <= result['consultations']


@given(FINITE_MONEY)
def test_capital_exclusion_is_exact(cost: float) -> None:
    params = Parameters(equipment_cost=cost)
    full = evaluate([SITE], params)
    cash = evaluate([SITE], replace(params, include_capital=False))
    assert math.isclose(full['programme_cost'] - cash['programme_cost'], annuity(cost, 5, .05), rel_tol=1e-9, abs_tol=1e-8)


@given(st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False), FINITE_MONEY)
def test_missing_qep_stays_missing(weight: float, price: float) -> None:
    assert funding_ledger(weight, weight, price, None)['queensland_benchmark'] is None


@given(st.integers(min_value=0, max_value=2**31 - 1))
@settings(max_examples=25)
def test_psa_seed_reproduces(seed: int) -> None:
    first = psa([SITE], 50, seed)
    second = psa([SITE], 50, seed)
    assert first['summary'] == second['summary']
    assert np.array_equal(first['draws']['net_saving'], second['draws']['net_saving'])


@given(st.integers(min_value=0, max_value=2**31 - 1))
@settings(max_examples=25)
def test_shared_draws_do_not_diversify_away_systematic_uncertainty(seed: int) -> None:
    other = replace(SITE, name='Second audit site')
    one = psa([SITE], 50, seed)['draws']['net_saving']
    two = psa([SITE, other], 50, seed)['draws']['net_saving']
    assert np.allclose(two, 2 * one)
