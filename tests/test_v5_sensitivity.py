"""Bounded sensitivity designs and exact decision reconstruction."""

from typing import TYPE_CHECKING, TypedDict, cast

import numpy as np
import pytest

from src import sensitivity
from src.statewide import load_sites, select_sites
from src.strategies import KEYS, compare, compare_psa, summarise

if TYPE_CHECKING:
    from collections.abc import Callable


class Summary(TypedDict):
    """Summary envelope returned by the published decision helpers."""

    summary: dict[str, dict[str, float]]
    cost_only_evpi: float
    preferred_expected_value: str


# src signatures declare bare containers; these restate the shapes these tests assert.
one_way = cast("Callable[..., list[dict[str, object]]]", sensitivity.one_way)
two_way = cast("Callable[..., list[dict[str, object]]]", sensitivity.two_way)
k_way = cast("Callable[..., list[dict[str, object]]]", sensitivity.k_way)


def _summary(raw: object) -> Summary:
    """Narrow a loosely typed summary envelope.

    Returns:
        The summary dict typed as the shape these tests assert.
    """
    return cast("Summary", raw)


def test_reference_design_matches_all_five_exact_strategies() -> None:
    m = sensitivity
    sites = select_sites(load_sites(), "pilot")
    out = m.evaluate_design(sites, m.reference_design()[None, :])
    ref = compare(sites)
    for j, k in enumerate(KEYS):
        assert out[0, j] == pytest.approx(ref[k]["net_saving"], rel=1e-12)


def test_design_validation() -> None:
    m = sensitivity
    sites = select_sites(load_sites(), "pilot")
    r = m.reference_design()
    for bad in [r, np.zeros((1, 2)), np.full((1, len(r)), np.nan), np.full((1, len(r)), np.inf)]:
        with pytest.raises(ValueError, match="Expected finite n-by-d nonempty design"):
            _ = m.evaluate_design(sites, bad)


def test_unit_transform_roundtrip_and_bounds() -> None:
    m = sensitivity
    u = np.vstack([np.zeros(len(m.VARIABLES)), np.ones(len(m.VARIABLES)), np.full(len(m.VARIABLES), 0.5)])
    d = m.from_unit(u)
    assert d.shape == u.shape
    np.testing.assert_allclose(cast("np.ndarray", d[0]), [v.low for v in m.VARIABLES])
    np.testing.assert_allclose(cast("np.ndarray", d[1]), [v.high for v in m.VARIABLES])
    with pytest.raises(ValueError, match=r"Expected a finite n-by-d design within \[0,1\]"):
        _ = m.from_unit(np.full(u.shape, 1.1))


def test_one_way_and_two_way_inventory() -> None:
    m = sensitivity
    s = select_sites(load_sites(), "pilot")
    one = one_way(s, points=3)
    assert len(one) == len(m.VARIABLES) * 3 * 5
    two = two_way(s, "calls_per_site", "odds_ratio", points=3)
    assert len(two) == 9
    assert all(row["best"] in KEYS for row in two)


def test_joint_grid_size_and_duplicate_dimensions() -> None:
    s = select_sites(load_sites(), "pilot")
    rows = k_way(s, ["odds_ratio", "calls_per_site", "marginal_fraction"], levels=3)
    assert len(rows) == 27
    with pytest.raises(ValueError, match="Unique known coordinates required"):
        _ = k_way(s, ["odds_ratio", "odds_ratio"], levels=3)


def test_kway_full_grid_not_conditional_probability() -> None:
    rows = k_way(select_sites(load_sites(), "pilot"), ["odds_ratio", "calls_per_site"], levels=3)
    assert all(r["design_kind"] == "deterministic_cartesian_not_probability" for r in rows)


def test_zero_benefit_telephone_wins_regardless_of_device() -> None:
    m = sensitivity
    s = select_sites(load_sites(), "pilot")
    d = m.reference_design()
    d[0] = 1
    a = m.evaluate_design(s, d[None, :])
    assert np.argmax(cast("np.ndarray", a[0])) == 0


def test_shared_cart_can_win_when_neonatal_capital_allocation_is_small() -> None:
    m = sensitivity
    d = m.reference_design()
    d[m.NAMES.index("mobile_capital_share")] = 0.05
    a = m.evaluate_design(select_sites(load_sites(), "pilot"), d[None, :])
    assert KEYS[int(np.argmax(cast("np.ndarray", a[0])))] == "mobile"


def test_constant_ties_fractionally_assigned() -> None:
    draws = {
        k: {"net_saving": np.zeros(3), "programme_cost": np.zeros(3), "avoided_transfers": np.zeros(3)} for k in KEYS
    }
    r = _summary(summarise(draws))
    assert all(v["p_optimal"] == pytest.approx(0.2) for v in r["summary"].values())
    assert r["cost_only_evpi"] == 0


def test_expected_regret_identity() -> None:
    r = _summary(compare_psa(select_sites(load_sites(), "pilot"), n=128, seed=9))
    best = r["preferred_expected_value"]
    assert r["summary"][best]["expected_regret"] == pytest.approx(r["cost_only_evpi"])


def test_decision_metrics_measure_cost_of_wrong_choice() -> None:
    m = sensitivity
    truth = np.array([[0, 5, 4, 3, 2], [0, 1, 4, 3, 2]], dtype=float)
    pred = np.array([[0, 9, 1, 2, 3], [0, 1, 1, 9, 2]], dtype=float)
    r = m.decision_quality(pred, truth)
    assert r["accuracy"] == pytest.approx(0.5)
    assert r["mean_regret"] == pytest.approx(0.5)
    assert r["max_regret"] == 1
    assert r["near_optimal_100"] == 1


def test_decision_metrics_reject_misalignment() -> None:
    with pytest.raises(ValueError, match="Aligned finite n-by-five prediction and exact outcomes required"):
        _ = sensitivity.decision_quality(np.zeros((2, 5)), np.zeros((3, 5)))


@pytest.mark.parametrize("n", [1, 102, True, 2.5])
def test_invalid_grid_resolutions(n: object) -> None:
    with pytest.raises(ValueError, match="Grid resolution must be an integer between 2 and 101"):
        _ = one_way(select_sites(load_sites(), "pilot"), points=n)


def test_bad_axes_and_excessive_grid() -> None:
    m = sensitivity
    s = select_sites(load_sites(), "pilot")
    for axes in [("odds_ratio", "odds_ratio"), ("bad", "life_years")]:
        with pytest.raises(ValueError, match="Two distinct known coordinates required"):
            _ = two_way(s, *axes)
    for axes in [[], ["bad"]]:
        with pytest.raises(ValueError, match="Unique known coordinates required"):
            _ = k_way(s, axes)
    with pytest.raises(ValueError, match="Cartesian grid exceeds 100000-point guardrail"):
        _ = k_way(s, list(m.NAMES), levels=3)


def test_wrong_outcome_or_unbounded_design_rejected() -> None:
    m = sensitivity
    s = select_sites(load_sites(), "pilot")
    d = m.reference_design()[None, :]
    with pytest.raises(ValueError, match="Unsupported sensitivity outcome"):
        _ = m.evaluate_design(s, d, metric="unavailable")
    d[0, 0] = 50
    with pytest.raises(ValueError, match="Outside prespecified deterministic range"):
        _ = m.evaluate_design(s, d)


def test_sensitivity_societal_and_sunk_paths() -> None:
    m = sensitivity
    s = select_sites(load_sites(), "pilot")
    d = m.reference_design()[None, :]
    a = m.evaluate_design(s, d, sunk=("panda",), metric="societal_net_saving")
    b = compare(s, sunk=("panda",))
    for j, key in enumerate(KEYS):
        assert a[0, j] == pytest.approx(b[key]["societal_net_saving"])
