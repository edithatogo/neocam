"""Online CI-only generative checks; absence is a blocked gate, not a pass."""
import numpy as np
from hypothesis import given, settings, strategies as st
from src.statewide import _odds, annuity

@given(st.floats(min_value=0, max_value=1), st.floats(min_value=.001, max_value=1000))
@settings(max_examples=1000, derandomize=True)
def test_odds_probability_is_bounded(p, odds):
    result=_odds(np.array([p]),np.array([odds]))[0]
    assert 0 <= result <= 1

@given(st.floats(min_value=0, max_value=100000), st.floats(min_value=1, max_value=30))
@settings(max_examples=500, derandomize=True)
def test_capital_with_discount_not_lower_than_straight_line(capital, years):
    assert annuity(capital,years,.05) >= annuity(capital,years,0) - 1e-7
