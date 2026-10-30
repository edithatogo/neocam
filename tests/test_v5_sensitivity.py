"""Bounded sensitivity designs and exact decision reconstruction."""

import importlib

import numpy as np
import pytest

from src.statewide import load_sites, select_sites
from src.strategies import KEYS, compare, compare_psa, summarise


def api():
    return importlib.import_module("src.sensitivity")


def test_reference_design_matches_all_five_exact_strategies():
    m = api()
    sites = select_sites(load_sites(), "pilot")
    out = m.evaluate_design(sites, m.reference_design()[None, :])
    ref = compare(sites)
    for j, k in enumerate(KEYS):
        assert out[0, j] == pytest.approx(ref[k]["net_saving"], rel=1e-12)


def test_design_validation():
    m = api()
    sites = select_sites(load_sites(), "pilot")
    r = m.reference_design()
    for bad in [r, np.zeros((1, 2)), np.full((1, len(r)), np.nan), np.full((1, len(r)), np.inf)]:
        with pytest.raises(ValueError, match="Expected finite n-by-d nonempty design"):
            m.evaluate_design(sites, bad)


def test_unit_transform_roundtrip_and_bounds():
    m = api()
    u = np.vstack([np.zeros(len(m.VARIABLES)), np.ones(len(m.VARIABLES)), np.full(len(m.VARIABLES), 0.5)])
    d = m.from_unit(u)
    assert d.shape == u.shape
    np.testing.assert_allclose(d[0], [v.low for v in m.VARIABLES])
    np.testing.assert_allclose(d[1], [v.high for v in m.VARIABLES])
    with pytest.raises(ValueError, match=r"Expected a finite n-by-d design within \[0,1\]"):
        m.from_unit(np.full(u.shape, 1.1))


def test_one_way_and_two_way_inventory():
    m = api()
    s = select_sites(load_sites(), "pilot")
    one = m.one_way(s, points=3)
    assert len(one) == len(m.VARIABLES) * 3 * 5
    two = m.two_way(s, "calls_per_site", "odds_ratio", points=3)
    assert len(two) == 9
    assert all(row["best"] in KEYS for row in two)


def test_joint_grid_size_and_duplicate_dimensions():
    m = api()
    s = select_sites(load_sites(), "pilot")
    rows = m.k_way(s, ["odds_ratio", "calls_per_site", "marginal_fraction"], levels=3)
    assert len(rows) == 27
    with pytest.raises(ValueError, match="Unique known coordinates required"):
        m.k_way(s, ["odds_ratio", "odds_ratio"], levels=3)


def test_kway_full_grid_not_conditional_probability():
    rows = api().k_way(select_sites(load_sites(), "pilot"), ["odds_ratio", "calls_per_site"], levels=3)
    assert all(r["design_kind"] == "deterministic_cartesian_not_probability" for r in rows)


def test_zero_benefit_telephone_wins_regardless_of_device():
    m = api()
    s = select_sites(load_sites(), "pilot")
    d = m.reference_design()
    d[0] = 1
    a = m.evaluate_design(s, d[None, :])
    assert np.argmax(a[0]) == 0


def test_shared_cart_can_win_when_neonatal_capital_allocation_is_small():
    m = api()
    d = m.reference_design()
    d[m.NAMES.index("mobile_capital_share")] = 0.05
    a = m.evaluate_design(select_sites(load_sites(), "pilot"), d[None, :])
    assert KEYS[int(np.argmax(a[0]))] == "mobile"


def test_constant_ties_fractionally_assigned():
    draws = {
        k: {"net_saving": np.zeros(3), "programme_cost": np.zeros(3), "avoided_transfers": np.zeros(3)} for k in KEYS
    }
    r = summarise(draws)
    assert all(v["p_optimal"] == pytest.approx(0.2) for v in r["summary"].values())
    assert r["cost_only_evpi"] == 0


def test_expected_regret_identity():
    r = compare_psa(select_sites(load_sites(), "pilot"), n=128, seed=9)
    best = r["preferred_expected_value"]
    assert r["summary"][best]["expected_regret"] == pytest.approx(r["cost_only_evpi"])


def test_decision_metrics_measure_cost_of_wrong_choice():
    m = api()
    truth = np.array([[0, 5, 4, 3, 2], [0, 1, 4, 3, 2]], dtype=float)
    pred = np.array([[0, 9, 1, 2, 3], [0, 1, 1, 9, 2]], dtype=float)
    r = m.decision_quality(pred, truth)
    assert r["accuracy"] == pytest.approx(0.5)
    assert r["mean_regret"] == pytest.approx(0.5)
    assert r["max_regret"] == 1
    assert r["near_optimal_100"] == 1


def test_decision_metrics_reject_misalignment():
    with pytest.raises(ValueError, match="Aligned finite n-by-five prediction and exact outcomes required"):
        api().decision_quality(np.zeros((2, 5)), np.zeros((3, 5)))


@pytest.mark.parametrize("n", [1, 102, True, 2.5])
def test_invalid_grid_resolutions(n):
    with pytest.raises(ValueError, match="Grid resolution must be an integer between 2 and 101"):
        api().one_way(select_sites(load_sites(), "pilot"), points=n)


def test_bad_axes_and_excessive_grid():
    m = api()
    s = select_sites(load_sites(), "pilot")
    for axes in [("odds_ratio", "odds_ratio"), ("bad", "life_years")]:
        with pytest.raises(ValueError, match="Two distinct known coordinates required"):
            m.two_way(s, *axes)
    for axes in [[], ["bad"]]:
        with pytest.raises(ValueError, match="Unique known coordinates required"):
            m.k_way(s, axes)
    with pytest.raises(ValueError, match="Cartesian grid exceeds 100000-point guardrail"):
        m.k_way(s, list(m.NAMES), levels=3)


def test_wrong_outcome_or_unbounded_design_rejected():
    m = api()
    s = select_sites(load_sites(), "pilot")
    d = m.reference_design()[None, :]
    with pytest.raises(ValueError, match="Unsupported sensitivity outcome"):
        m.evaluate_design(s, d, metric="unavailable")
    d[0, 0] = 50
    with pytest.raises(ValueError, match="Outside prespecified deterministic range"):
        m.evaluate_design(s, d)


def test_sensitivity_societal_and_sunk_paths():
    m = api()
    s = select_sites(load_sites(), "pilot")
    d = m.reference_design()[None, :]
    a = m.evaluate_design(s, d, sunk=("panda",), metric="societal_net_saving")
    b = compare(s, sunk=("panda",))
    for j, key in enumerate(KEYS):
        assert a[0, j] == pytest.approx(b[key]["societal_net_saving"])
