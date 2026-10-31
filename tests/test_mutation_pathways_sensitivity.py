"""Behavioural tests targeting surviving mutants in pathways_v6 and sensitivity.

Every assertion is an observable public-API property that a mutant would change;
none of these tests read private state or suppress mutation.
"""

from __future__ import annotations

from typing import cast

import numpy as np
import pytest

from src import sensitivity
from src.activity import ActivitySpec
from src.pathways_v6 import (
    NEP26,
    WEIGHTS,
    PathwaySpec,
    cash_budget,
    compare_v6,
    hospital_cost,
    hub_cost,
    path_probabilities,
    sample_v6,
)
from src.statewide import (
    Parameters,
    Site,
    _base_arrays,  # pyright: ignore[reportPrivateUsage] -- private draw helper is the in-repo surface under test
    index_air_cost,
    load_sites,
    select_sites,
)
from src.strategies import KEYS, compare

BAD_BOOL = cast("float", bool(1))


@pytest.fixture(scope="module")
def pilot() -> list[Site]:
    """Return the pilot portfolio for deterministic comparisons."""
    return select_sites(load_sites(), "pilot")


def _regional(name: str = "alt", births: int = 1000) -> Site:
    return Site(name, births, 2022, "rural_proxy", "regional")


# --------------------------------------------------------------------------- #
# PathwaySpec validation
# --------------------------------------------------------------------------- #


def test_pathway_spec_is_frozen_and_hashable() -> None:
    assert isinstance(hash(PathwaySpec()), int)


def test_pathway_spec_probability_fields_accept_exactly_one() -> None:
    assert PathwaySpec(phone_delay_share=1.0).phone_delay_share == pytest.approx(1.0)
    assert PathwaySpec(video_delay_share=1.0).video_delay_share == pytest.approx(1.0)
    assert PathwaySpec(extra_rescue=1.0).extra_rescue == pytest.approx(1.0)
    assert PathwaySpec(hospital_marginal_fraction=1.0).hospital_marginal_fraction == pytest.approx(1.0)
    for bad in (2.0, 1.0000001):
        with pytest.raises(ValueError, match="must be a probability"):
            _ = PathwaySpec(phone_delay_share=bad)
    with pytest.raises(ValueError, match="must be a probability"):
        _ = PathwaySpec(hospital_marginal_fraction=2.0)


def test_pathway_spec_rejects_negative_nonfinite_and_boolean() -> None:
    with pytest.raises(ValueError, match="must be finite non-negative numeric"):
        _ = PathwaySpec(extra_rescue=-0.5)
    with pytest.raises(ValueError, match="must be finite non-negative numeric"):
        _ = PathwaySpec(phone_delay_share=float("nan"))
    with pytest.raises(ValueError, match="must be finite non-negative numeric"):
        _ = PathwaySpec(hub_block_hours=float("inf"))
    with pytest.raises(ValueError, match="must be finite non-negative numeric"):
        _ = PathwaySpec(extra_rescue=BAD_BOOL)


def test_pathway_spec_hub_block_hours_and_endpoint_boundaries() -> None:
    assert PathwaySpec(hub_block_hours=1.0).hub_block_hours == pytest.approx(1.0)
    assert PathwaySpec(endpoint="initial").endpoint == "initial"
    with pytest.raises(ValueError, match="hub_block_hours must be positive"):
        _ = PathwaySpec(hub_block_hours=0)
    with pytest.raises(ValueError, match="endpoint must be eventual or initial"):
        _ = PathwaySpec(endpoint="neither")


# --------------------------------------------------------------------------- #
# path_probabilities exact partition
# --------------------------------------------------------------------------- #


def test_path_probabilities_eventual_exact() -> None:
    t = np.array([[0.2, 0.6, 0.98]])
    a = path_probabilities(t, np.array([2.0]), np.array([0.9]), 0.1, 0.3, extra_rescue=0.05)
    np.testing.assert_allclose(a["phone_immediate"], [[0.18, 0.54, 0.882]])
    np.testing.assert_allclose(a["phone_rescue"], [[0.02, 0.06, 0.098]])
    np.testing.assert_allclose(a["phone_local"], [[0.8, 0.4, 0.02]])
    np.testing.assert_allclose(a["video_immediate"], [[0.228, 0.5265, 0.7056]])
    np.testing.assert_allclose(a["video_rescue"], [[0.122, 0.21975, 0.2753]])
    np.testing.assert_allclose(a["video_local"], [[0.65, 0.25375, 0.0191]])
    np.testing.assert_allclose(a["phone_initial_local"], a["phone_rescue"] + a["phone_local"])
    np.testing.assert_allclose(a["video_initial_local"], a["video_rescue"] + a["video_local"])
    np.testing.assert_allclose(a["phone_conditional_rescue"], [[0.024390243902, 0.130434782609, 0.830508474576]])
    np.testing.assert_allclose(a["video_conditional_rescue"], [[0.158031088083, 0.464097148891, 0.935122282609]])


def test_path_probabilities_initial_exact() -> None:
    t = np.array([[0.2, 0.6, 0.98]])
    a = path_probabilities(t, np.array([2.0]), np.array([0.9]), 0.1, 0.3, extra_rescue=0.05, endpoint="initial")
    np.testing.assert_allclose(a["phone_immediate"], [[0.2, 0.6, 0.98]])
    np.testing.assert_allclose(a["phone_rescue"], [[0.08, 0.04, 0.002]])
    np.testing.assert_allclose(a["phone_local"], [[0.72, 0.36, 0.018]])
    np.testing.assert_allclose(a["video_immediate"], [[0.32, 0.735, 0.98]])
    np.testing.assert_allclose(a["video_rescue"], [[0.209, 0.079375, 0.00623]])
    np.testing.assert_allclose(a["video_local"], [[0.471, 0.185625, 0.01377]])
    np.testing.assert_allclose(a["video_conditional_rescue"], [[0.307352941176, 0.299528301887, 0.3115]])


def test_path_probabilities_zero_initial_local_is_zero() -> None:
    t = np.array([[1.0, 1.0, 1.0]])
    a = path_probabilities(t, np.array([2.0]), np.array([0.9]), 0.0, 0.0)
    np.testing.assert_allclose(a["phone_initial_local"], 0.0)
    np.testing.assert_allclose(a["video_initial_local"], 0.0)
    np.testing.assert_allclose(a["phone_conditional_rescue"], 0.0)
    np.testing.assert_allclose(a["video_conditional_rescue"], 0.0)


def test_path_probabilities_zero_transfer_stratum_accepted() -> None:
    t = np.array([[0.0, 0.6, 0.98]])
    a = path_probabilities(t, np.array([1.0]), np.array([1.0]), 1.0, 1.0, extra_rescue=1.0)
    assert a["video_local"].shape == (1, 3)
    assert path_probabilities(
        t, cast("np.ndarray", cast("object", 1.0)), cast("np.ndarray", cast("object", 0.9)), 0.05, 0.05
    )["video_immediate"].shape == (1, 3)


def test_path_probabilities_rejects_invalid_inputs() -> None:
    t = np.array([[0.2, 0.6, 0.98]])
    with pytest.raises(ValueError, match="Invalid reliability"):
        _ = path_probabilities(t, np.array([1.0]), np.array([1.5]), 0.05, 0.05)
    with pytest.raises(ValueError, match="Invalid extra rescue"):
        _ = path_probabilities(t, np.array([1.0]), np.array([0.9]), 0.05, 0.05, extra_rescue=1.5)
    with pytest.raises(ValueError, match="Invalid baseline transfer"):
        _ = path_probabilities(np.array([[np.nan, 0.6, 0.98]]), np.array([1.0]), np.array([0.9]), 0.05, 0.05)
    with pytest.raises(ValueError, match="Invalid baseline transfer"):
        _ = path_probabilities(np.array([[True, False, True]]), np.array([1.0]), np.array([0.9]), 0.05, 0.05)
    with pytest.raises(ValueError, match="odds ratio must be positive"):
        _ = path_probabilities(t, np.array([0.0]), np.array([0.9]), 0.05, 0.05)
    with pytest.raises(ValueError, match="baseline_transfer must have shape"):
        _ = path_probabilities(np.array([0.2, 0.6, 0.98]), np.array([1.0]), np.array([0.9]), 0.05, 0.05)
    with pytest.raises(ValueError, match="baseline_transfer must have shape"):
        _ = path_probabilities(np.zeros((0, 3)), np.array([1.0]), np.array([0.9]), 0.05, 0.05)


def test_path_probabilities_column_shape_validation() -> None:
    t = np.array([[0.2, 0.6, 0.98]])
    with pytest.raises(ValueError, match="odds ratio requires one value per draw"):
        _ = path_probabilities(t, np.array([[1.0]]), np.array([0.9]), 0.05, 0.05)
    with pytest.raises(ValueError, match="odds ratio requires one value per draw"):
        _ = path_probabilities(t, np.array([1.0, 2.0]), np.array([0.9]), 0.05, 0.05)
    with pytest.raises(ValueError, match="reliability requires one value per draw"):
        _ = path_probabilities(t, np.array([1.0]), np.array([0.9, 0.8]), 0.05, 0.05)


# --------------------------------------------------------------------------- #
# hub_cost and hospital_cost
# --------------------------------------------------------------------------- #


def test_hub_cost_exact_and_capacity_boundaries() -> None:
    spec = PathwaySpec(hub_spare_hours=20.0, hub_block_hours=10.0, hub_block_cost=2000.0, hub_hourly_rate=200.0)
    a = hub_cost(np.array([80.0, 80.04, 180.0]), np.array([15.0, 15.0, 15.0]), spec)
    np.testing.assert_allclose(a["hours"], [20.0, 20.01, 45.0])
    np.testing.assert_allclose(a["economic"], [4000.0, 4002.0, 9000.0])
    np.testing.assert_allclose(a["cash_capacity"], [0.0, 2000.0, 6000.0])
    np.testing.assert_allclose(a["capacity_blocks"], [0.0, 1.0, 3.0])


def test_hospital_cost_exact_partition() -> None:
    val = hospital_cost(
        np.array([0.4]),
        np.array([0.1]),
        np.array([0.5]),
        np.array([100.0]),
        np.array([1000.0]),
        np.array([200.0]),
        np.array([50.0]),
    )
    np.testing.assert_allclose(val, [655.0])


# --------------------------------------------------------------------------- #
# _activity and compare_v6 wiring
# --------------------------------------------------------------------------- #


def test_activity_episode_counts_by_group_and_geography() -> None:
    out = compare_v6([_regional()])["panda"]
    assert cast("float", out["episodes"][0]) == pytest.approx(1000.0 * (3 * 12.5 / 486) * 0.8)
    remote = compare_v6([Site("rem", 1000, 2022, "rural_proxy", "remote")])["panda"]
    assert cast("float", remote["episodes"][0]) == pytest.approx(1000.0 * (3 * 12.5 / 486) * 1.25 * 0.8)
    scn = compare_v6([Site("s", 1000, 2022, "scn", "regional")])["panda"]
    assert cast("float", scn["episodes"][0]) == pytest.approx(1000.0 * (3 * 12.5 / 486) * 0.5 * 0.8)
    grown = compare_v6([_regional()], Parameters(birth_growth=0.9))["panda"]
    assert cast("float", grown["episodes"][0]) == pytest.approx(1000.0 * (3 * 12.5 / 486) * 0.9 * 0.8)


def test_compare_v6_delay_share_wiring_matches_path_probabilities() -> None:
    p = Parameters()
    site = _regional()
    spec = PathwaySpec(phone_delay_share=0.5, video_delay_share=0.5)
    out = compare_v6([site], p, spec)["panda"]
    paths = path_probabilities(
        np.array([p.baseline_transfer]), np.array([p.odds_ratio]), np.array([p.reliability]), 0.5, 0.5
    )
    weights = cast("float", out["episodes"][0]) * np.array(p.case_mix)
    assert cast("float", out["delayed_rescues"][0]) == pytest.approx(
        cast("float", (weights * paths["video_rescue"]).sum())
    )
    assert cast("float", out["immediate_transfers"][0]) == pytest.approx(
        cast("float", (weights * paths["video_immediate"]).sum())
    )


def test_compare_v6_benchmark_wiring_exact() -> None:
    p = Parameters()
    site = _regional()
    spec = PathwaySpec(phone_delay_share=0.5, video_delay_share=0.5)
    out = compare_v6([site], p, spec)["panda"]
    paths = path_probabilities(
        np.array([p.baseline_transfer]), np.array([p.odds_ratio]), np.array([p.reliability]), 0.5, 0.5
    )
    weights = cast("float", out["episodes"][0]) * np.array(p.case_mix)
    origin = NEP26 * np.array([WEIGHTS["P60B"], WEIGHTS["P60B"], WEIGHTS["P60A"]])
    receiver = NEP26 * np.array([WEIGHTS["P68D"], WEIGHTS["P68B"], WEIGHTS["P06B"]])
    im, re, lo = paths["video_immediate"], paths["video_rescue"], paths["video_local"]
    assert cast("float", out["final_local"][0]) == pytest.approx(cast("float", (weights * lo).sum()))
    assert cast("float", out["origin_benchmark_cost"][0]) == pytest.approx(
        cast("float", (weights * (im + re) * origin).sum())
    )
    assert cast("float", out["receiving_benchmark_cost"][0]) == pytest.approx(
        cast("float", (weights * (im + re) * receiver).sum())
    )
    assert cast("float", out["local_benchmark_cost"][0]) == pytest.approx(
        cast("float", (weights * lo * receiver).sum())
    )
    benchmark = hospital_cost(im, re, lo, origin, receiver, receiver, np.full(3, 2000.0))
    assert cast("float", out["hospital_benchmark_cost"][0]) == pytest.approx(cast("float", (weights * benchmark).sum()))


def test_compare_v6_structural_multiplier_scaling() -> None:
    site = _regional()
    base = compare_v6([site], structural_draws={"hospital_multiplier": np.array([1.0])})["panda"]
    doubled = compare_v6([site], structural_draws={"hospital_multiplier": np.array([2.0])})["panda"]
    for key in ("origin_benchmark_cost", "receiving_benchmark_cost", "local_benchmark_cost"):
        assert cast("float", doubled[key][0]) == pytest.approx(2.0 * cast("float", base[key][0]))
    local3 = compare_v6([site], structural_draws={"local_multiplier": np.array([3.0])})["panda"]
    assert cast("float", local3["local_benchmark_cost"][0]) == pytest.approx(
        3.0 * cast("float", base["local_benchmark_cost"][0])
    )


def test_conditional_rescue_risk_boundaries() -> None:
    site = _regional()
    x = _base_arrays(Parameters(), 1)
    x["baseline_transfer"] = np.array([[1.0, 1.0, 1.0]])
    saturated = compare_v6([site], inputs=x, spec=PathwaySpec(phone_delay_share=0.0, video_delay_share=0.0))["panda"]
    assert cast("float", saturated["immediate_transfers"][0]) > 0
    assert cast("float", saturated["conditional_rescue_risk"][0]) == pytest.approx(0.0)
    tiny = compare_v6([Site("t", 1, 2022, "rural_proxy", "regional")])["panda"]
    assert cast("float", tiny["conditional_rescue_risk"][0]) == pytest.approx(
        cast("float", tiny["delayed_rescues"][0]) / cast("float", tiny["initially_local"][0])
    )


def test_transport_cost_uses_site_modes_and_marginal_fraction() -> None:
    p = Parameters()
    site = _regional()
    out = compare_v6([site], p)["telephone"]
    air = index_air_cost() * p.air_multiplier
    transport = 0.60 * p.road_cost + 0.25 * air * 1.15 + 0.15 * air * 0.85
    exposure = cast("float", out["episodes"][0]) * transport * p.marginal_fraction
    expected = cast("float", (np.array(p.case_mix) * np.array(p.baseline_transfer)).sum()) * exposure
    assert cast("float", out["transport_resource_cost"][0]) == pytest.approx(expected)


def test_compare_v6_cost_identities(pilot: list[Site]) -> None:
    out = compare_v6(pilot)["panda"]
    base = compare_v6(pilot)["telephone"]
    assert cast("float", out["hospital_resource_cost"][0]) == pytest.approx(
        cast("float", out["hospital_benchmark_cost"][0]) * 0.5
    )
    assert cast("float", out["care_resource_cost"][0]) == pytest.approx(
        cast("float", out["transport_resource_cost"][0])
        + cast("float", out["hospital_resource_cost"][0])
        + cast("float", out["rescue_extra_resource_cost"][0])
    )
    assert cast("float", out["eventual_transfers"][0]) == pytest.approx(
        cast("float", out["immediate_transfers"][0]) + cast("float", out["delayed_rescues"][0])
    )
    assert cast("float", out["initially_local"][0]) == pytest.approx(
        cast("float", out["episodes"][0]) - cast("float", out["immediate_transfers"][0])
    )
    assert cast("float", out["net_saving"][0]) == pytest.approx(
        cast("float", out["gross_resource_benefit"][0]) - cast("float", out["programme_cost"][0])
    )
    assert cast("float", out["pre_rescue_benchmark_cost"][0]) == pytest.approx(
        cast("float", out["delayed_rescues"][0]) * 2000.0
    )
    assert cast("float", out["rescue_extra_resource_cost"][0]) == pytest.approx(0.0)
    for key in (
        "avoided_transfers",
        "hospital_resource_benefit",
        "transport_resource_benefit",
        "gross_resource_benefit",
    ):
        assert cast("float", base[key][0]) == pytest.approx(0.0)
    assert cast("float", out["gross_resource_benefit"][0]) == pytest.approx(
        cast("float", base["care_resource_cost"][0]) - cast("float", out["care_resource_cost"][0])
    )
    assert cast("float", out["family_cost_extension"][0]) == pytest.approx(
        cast("float", out["avoided_transfers"][0]) * 1500.0
    )
    assert cast("float", out["net_with_family_extension"][0]) == pytest.approx(
        cast("float", out["net_saving"][0]) + cast("float", out["family_cost_extension"][0])
    )


def test_compare_v6_programme_and_cash_identities(pilot: list[Site]) -> None:
    out = compare_v6(pilot)["panda"]
    assert cast("float", out["programme_cost"][0]) == pytest.approx(
        cast("float", out["capital_annualised"][0])
        + cast("float", out["local_ready_cost"][0])
        + cast("float", out["local_workflow_cost"][0])
        + cast("float", out["hub_resource_cost"][0])
    )
    assert cast("float", out["cash_running_cost"][0]) == pytest.approx(
        cast("float", out["local_ready_cost"][0])
        + cast("float", out["local_workflow_cost"][0])
        + cast("float", out["hub_cash_cost"][0])
    )
    assert cast("float", out["local_ready_cost"][0]) == pytest.approx(
        len(pilot) * (52 * 10.0 / 60 * 85.0 + 300.0 + 400.0)
    )
    assert cast("float", out["local_workflow_cost"][0]) == pytest.approx(cast("float", out["contacts"][0]) * 25.0)
    assert cast("float", out["hub_hours"][0]) == pytest.approx(cast("float", out["contacts"][0]) * 15.0 / 60)
    assert cast("float", out["hospital_price_equivalent_units"][0]) == pytest.approx(
        cast("float", out["hospital_benchmark_cost"][0]) / NEP26
    )
    assert cast("float", out["conditional_rescue_risk"][0]) == pytest.approx(
        cast("float", out["delayed_rescues"][0]) / cast("float", out["initially_local"][0])
    )


def test_compare_v6_rescue_premium_scales_delayed_rescues() -> None:
    out = compare_v6([_regional()], spec=PathwaySpec(rescue_receiving_premium=100.0))["panda"]
    assert cast("float", out["rescue_extra_resource_cost"][0]) == pytest.approx(
        cast("float", out["delayed_rescues"][0]) * 100.0
    )
    assert cast("float", out["care_resource_cost"][0]) == pytest.approx(
        cast("float", out["transport_resource_cost"][0])
        + cast("float", out["hospital_resource_cost"][0])
        + cast("float", out["rescue_extra_resource_cost"][0])
    )


def test_local_workflow_cost_uses_workflow_scale(pilot: list[Site]) -> None:
    out = compare_v6(pilot, overrides={"panda": {"workflow_per_call": 150.0}})["panda"]
    assert cast("float", out["local_workflow_cost"][0]) == pytest.approx(cast("float", out["contacts"][0]) * 25.0 * 2.0)
    assert cast("float", out["hub_hours"][0]) == pytest.approx(cast("float", out["contacts"][0]) * 2.0 * 15.0 / 60)


def test_cash_running_cost_includes_nonzero_hub_cash(pilot: list[Site]) -> None:
    spec = PathwaySpec(hub_spare_hours=0.1, hub_block_hours=1.0)
    out = compare_v6(pilot, spec=spec)["panda"]
    assert cast("float", out["hub_cash_cost"][0]) > 0
    assert cast("float", out["cash_running_cost"][0]) == pytest.approx(
        cast("float", out["local_ready_cost"][0])
        + cast("float", out["local_workflow_cost"][0])
        + cast("float", out["hub_cash_cost"][0])
    )


def test_compare_v6_capital_attribution_flags_and_sunk() -> None:
    sites = [_regional("a", 500), _regional("b", 500)]
    out = compare_v6(sites, overrides={"panda": {"capital_share": 0.5}})["panda"]
    assert cast("float", out["full_purchase_capital"][0]) == pytest.approx(2 * 10000.0)
    assert cast("float", out["attributed_capital"][0]) == pytest.approx(2 * 10000.0 * 0.5)
    assert cast("float", out["capital_annualised"][0]) > 0
    sunk = compare_v6(sites, sunk=("panda",))["panda"]
    assert cast("float", sunk["incremental_purchase_capital"][0]) == pytest.approx(0.0)
    assert cast("float", sunk["capital_annualised"][0]) == pytest.approx(0.0)
    off = compare_v6(sites, Parameters(include_capital=False))["panda"]
    assert cast("float", off["capital_annualised"][0]) == pytest.approx(0.0)


def test_annuity_zero_and_positive_rate() -> None:
    sites = [_regional("a", 500)]
    zero = compare_v6(sites, Parameters(discount=0.0))["panda"]
    assert cast("float", zero["capital_annualised"][0]) == pytest.approx(
        cast("float", zero["attributed_capital"][0]) / 5.0
    )
    positive = compare_v6(sites, Parameters(discount=0.05))["panda"]
    expected = 10000.0 * 0.05 / (1.0 - 1.05**-5)
    assert cast("float", positive["capital_annualised"][0]) == pytest.approx(expected)


def test_compare_v6_validation(pilot: list[Site]) -> None:
    site = _regional()
    with pytest.raises(ValueError, match="non-empty unique sites required"):
        _ = compare_v6([])
    with pytest.raises(ValueError, match="non-empty unique sites required"):
        _ = compare_v6([site, site])
    with pytest.raises(ValueError, match="invalid sunk strategies"):
        _ = compare_v6([site], sunk=("bogus",))
    with pytest.raises(ValueError, match="invalid sunk strategies"):
        _ = compare_v6([site], sunk=("panda", "panda"))
    with pytest.raises(TypeError, match="Activity requires ActivitySpec"):
        _ = compare_v6([site], activity=cast("ActivitySpec", object()))
    with pytest.raises(ValueError, match="unknown structural draw"):
        _ = compare_v6([site], structural_draws={"nope": np.ones(1)})
    assert compare_v6([site], activity=ActivitySpec())["panda"]["episodes"][0] > 0
    assert compare_v6([site], structural_draws={"delay_share": np.array([0.1])})["panda"]["episodes"][0] > 0
    assert compare_v6(pilot, Parameters(life_years=1.0))["panda"]["episodes"][0] > 0
    zero_life = _base_arrays(Parameters(), 1)
    zero_life["life_years"] = np.array([0.0])
    with pytest.raises(ValueError, match="positive equipment life required"):
        _ = compare_v6(pilot, inputs=zero_life)


# --------------------------------------------------------------------------- #
# cash_budget
# --------------------------------------------------------------------------- #


def test_cash_budget_validation(pilot: list[Site]) -> None:
    for years in (0, -1, cast("int", bool(1)), cast("int", cast("object", 2.5))):
        with pytest.raises(ValueError, match="Invalid cash-budget specification"):
            _ = cash_budget(pilot, years=years)
    with pytest.raises(ValueError, match="Invalid cash-budget specification"):
        _ = cash_budget(pilot, strategy="bogus")
    with pytest.raises(ValueError, match="Invalid cash-budget specification"):
        _ = cash_budget(pilot, remaining_life=-1)
    with pytest.raises(ValueError, match="Integer equipment life and feasible remaining life required"):
        _ = cash_budget(pilot, parameters=Parameters(life_years=5.5))
    with pytest.raises(ValueError, match="Integer equipment life and feasible remaining life required"):
        _ = cash_budget(pilot, remaining_life=6)
    assert len(cash_budget(pilot, remaining_life=5)) == 7
    assert len(cash_budget(pilot, years=1)) == 1
    assert len(cash_budget(pilot, remaining_life=0)) == 7
    assert len(cash_budget(pilot, strategy="telephone", incumbent=True)) == 7


def test_cash_budget_schedule(pilot: list[Site]) -> None:
    rows = cash_budget(pilot, strategy="panda", years=3)
    assert [r["year"] for r in rows] == [1, 2, 3]
    assert rows[0]["capital"] == pytest.approx(30000.0)
    assert rows[1]["capital"] == pytest.approx(0.0)
    for row in rows:
        assert row["cash_expenditure"] == pytest.approx(row["capital"] + row["cash_running"])
    incumbent = cash_budget(pilot, strategy="panda", years=7, incumbent=True, remaining_life=2)
    assert [r["capital"] for r in incumbent] == [0.0, 0.0, 30000.0, 0.0, 0.0, 0.0, 0.0]
    assert [r["year"] for r in incumbent] == [1, 2, 3, 4, 5, 6, 7]


# --------------------------------------------------------------------------- #
# sample_v6 structural draws
# --------------------------------------------------------------------------- #


def test_sample_v6_default_shapes() -> None:
    x, extras = sample_v6(n=4, seed=1)
    assert x["odds_ratio"].shape == (4,)
    assert extras["delay_share"].shape == (4,)


def test_sample_v6_uses_supplied_parameters() -> None:
    x, _ = sample_v6(Parameters(state_uptake=0.5), n=3, seed=7)
    np.testing.assert_allclose(x["state_uptake"], 0.5)


def test_sample_v6_structural_draws_deterministic() -> None:
    spec = PathwaySpec(
        phone_delay_share=0.1,
        hospital_marginal_fraction=0.25,
        hospital_resource_multiplier=2.0,
        local_care_multiplier=2.0,
        extra_pre_rescue_cost=4000.0,
    )
    _, extras = sample_v6(spec=spec, n=5, seed=12345)
    np.testing.assert_allclose(
        extras["delay_share"], [0.010381099601, 0.235709816682, 0.132686678444, 0.138529992873, 0.000944282935]
    )
    np.testing.assert_allclose(
        extras["hospital_fraction"], [0.297495022993, 0.351659809914, 0.325387190808, 0.151627907215, 0.266915124355]
    )
    np.testing.assert_allclose(
        extras["hospital_multiplier"], [1.963153059565, 2.20311380633, 1.752458464541, 2.22612642746, 2.098111171489]
    )
    np.testing.assert_allclose(
        extras["local_multiplier"], [1.897796273289, 1.600911090122, 2.196380560849, 1.844315475799, 1.806449925968]
    )
    np.testing.assert_allclose(
        extras["pre_rescue"],
        [4167.755846618106, 5609.474119465573, 5213.593826030897, 4410.376506854544, 6630.922984337998],
    )


# --------------------------------------------------------------------------- #
# sensitivity
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="module")
def design_axes() -> tuple[int, np.ndarray, np.ndarray]:
    low = np.array([v.low for v in sensitivity.VARIABLES])
    high = np.array([v.high for v in sensitivity.VARIABLES])
    return len(sensitivity.VARIABLES), low, high


def test_variable_catalog_frozen_and_reference() -> None:
    assert isinstance(hash(sensitivity.VARIABLES[0]), int)
    ref = sensitivity.reference_design()
    assert isinstance(ref, np.ndarray)
    np.testing.assert_allclose(ref, [v.reference for v in sensitivity.VARIABLES])


def test_from_unit_endpoints_and_rejection(design_axes: tuple[int, np.ndarray, np.ndarray]) -> None:
    d, low, high = design_axes
    np.testing.assert_allclose(sensitivity.from_unit(np.zeros((1, d))), low[None, :])
    np.testing.assert_allclose(sensitivity.from_unit(np.ones((1, d))), high[None, :])
    np.testing.assert_allclose(sensitivity.from_unit(np.full((1, d), 0.5)), (low + 0.5 * (high - low))[None, :])
    for bad in (np.zeros(d), np.full((1, d), -0.1), np.full((1, d), 1.5), np.full((1, d), np.nan)):
        with pytest.raises(ValueError, match=r"Expected a finite n-by-d design within \[0,1\]"):
            _ = sensitivity.from_unit(bad)


def test_evaluate_design_validation(pilot: list[Site], design_axes: tuple[int, np.ndarray, np.ndarray]) -> None:
    d, _low, _high = design_axes
    reference = sensitivity.reference_design()
    assert sensitivity.evaluate_design(pilot, reference[None, :]).shape == (1, len(KEYS))
    assert sensitivity.evaluate_design(pilot, np.vstack([reference, reference])).shape == (2, len(KEYS))
    bad_designs = [reference, np.zeros((0, d)), np.zeros((1, d + 1)), np.full((1, d), np.nan), np.full((1, d), np.inf)]
    for bad in bad_designs:
        with pytest.raises(ValueError, match="Expected finite n-by-d nonempty design"):
            _ = sensitivity.evaluate_design(pilot, bad)
    below = reference.copy()
    below[0] = -1.0
    with pytest.raises(ValueError, match="Outside prespecified deterministic range"):
        _ = sensitivity.evaluate_design(pilot, below[None, :])
    above = reference.copy()
    above[0] = 50.0
    with pytest.raises(ValueError, match="Outside prespecified deterministic range"):
        _ = sensitivity.evaluate_design(pilot, above[None, :])


def test_evaluate_design_range_boundaries(pilot: list[Site], design_axes: tuple[int, np.ndarray, np.ndarray]) -> None:
    d, low, high = design_axes
    assert low.size == d
    reference = sensitivity.reference_design()
    at_low = reference.copy()
    at_low[0] = cast("float", low[0])
    at_high = reference.copy()
    at_high[0] = cast("float", high[0])
    just_below = reference.copy()
    just_below[0] = cast("float", low[0]) - 1e-10
    just_above = reference.copy()
    just_above[0] = cast("float", high[0]) + 1e-10
    assert sensitivity.evaluate_design(pilot, np.vstack([at_low, at_high, just_below, just_above])).shape == (
        4,
        len(KEYS),
    )


def test_evaluate_design_critical_share_scales_non_critical_effect(pilot: list[Site]) -> None:
    index = sensitivity.NAMES.index("critical_share")
    low_share = sensitivity.reference_design()
    low_share[index] = 0.05
    high_share = sensitivity.reference_design()
    high_share[index] = 0.40
    low_value = cast("float", sensitivity.evaluate_design(pilot, low_share[None, :], metric="avoided_transfers")[0, 2])
    high_value = cast(
        "float", sensitivity.evaluate_design(pilot, high_share[None, :], metric="avoided_transfers")[0, 2]
    )
    assert low_value / high_value == pytest.approx(0.95 / 0.60)


def test_one_way_inventory(pilot: list[Site]) -> None:
    rows = sensitivity.one_way(pilot, points=3)
    assert len(rows) == len(sensitivity.VARIABLES) * 3 * len(KEYS)
    assert {r["parameter"] for r in rows} == set(sensitivity.NAMES)
    assert all(r["strategy"] in KEYS for r in rows)
    assert all(r["best"] in KEYS for r in rows)


def test_one_way_rejects_invalid_grid_resolutions(pilot: list[Site]) -> None:
    for bad in (1, 102, cast("int", bool(1)), cast("int", cast("object", 2.5))):
        with pytest.raises(ValueError, match="Grid resolution must be an integer between 2 and 101"):
            _ = sensitivity.one_way(pilot, points=bad)
    assert len(sensitivity.one_way(pilot, points=2)) == len(sensitivity.VARIABLES) * 2 * len(KEYS)


def test_reference_design_matches_deterministic_compare(pilot: list[Site]) -> None:
    out = sensitivity.evaluate_design(pilot, sensitivity.reference_design()[None, :])
    reference = compare(pilot)
    for j, key in enumerate(KEYS):
        assert out[0, j] == pytest.approx(reference[key]["net_saving"])


def test_two_way_validation_rows_and_margin(pilot: list[Site]) -> None:
    for other in ("odds_ratio", "nope"):
        with pytest.raises(ValueError, match="Two distinct known coordinates required"):
            _ = sensitivity.two_way(pilot, "odds_ratio", other)
    rows = sensitivity.two_way(pilot, "odds_ratio", "life_years", points=3)
    assert len(rows) == 9
    assert all(r["design_kind"] == "deterministic_grid_not_probability" for r in rows)
    for row in rows:
        values = sorted(float(cast("float", row[k])) for k in KEYS)
        assert float(cast("float", row["margin"])) == pytest.approx(values[-1] - values[-2])


def test_k_way_validation_grid_and_guard(pilot: list[Site], monkeypatch: pytest.MonkeyPatch) -> None:
    for axes in ([], ["odds_ratio", "odds_ratio"], ["nope"]):
        with pytest.raises(ValueError, match="Unique known coordinates required"):
            _ = sensitivity.k_way(pilot, axes)
    rows = sensitivity.k_way(pilot, ["odds_ratio", "life_years"], levels=3)
    assert len(rows) == 9
    assert all(r["design_kind"] == "deterministic_cartesian_not_probability" for r in rows)
    monkeypatch.setattr(sensitivity, "_MAX_CARTESIAN_POINTS", 8)
    assert len(sensitivity.k_way(pilot, ["odds_ratio", "life_years"], levels=2)) == 4
    with pytest.raises(ValueError, match="Cartesian grid exceeds 100000-point guardrail"):
        _ = sensitivity.k_way(pilot, ["odds_ratio", "life_years"], levels=3)
    monkeypatch.setattr(sensitivity, "_MAX_CARTESIAN_POINTS", 9)
    assert len(sensitivity.k_way(pilot, ["odds_ratio", "life_years"], levels=3)) == 9


def test_decision_quality_regret_metrics() -> None:
    truth = np.array([
        [1.0, 5.0, 4.0, 3.0, 2.0],
        [1.0, 4.0, 3.0, 9.0, 2.0],
        [10.0, 1.0, 1.0, 1.0, 1.0],
        [0.0, 5.0, 2.0, 3.0, 105.0],
        [0.0, 5.0, 2.0, 3.0, 1005.0],
    ])
    predicted = np.tile(np.array([0.0, 9.0, 1.0, 2.0, 3.0]), (5, 1))
    r = sensitivity.decision_quality(predicted, truth)
    assert r["accuracy"] == pytest.approx(0.2)
    assert r["mean_regret"] == pytest.approx(222.8)
    assert r["max_regret"] == pytest.approx(1000.0)
    assert r["near_optimal_100"] == pytest.approx(0.8)
    assert r["near_optimal_1000"] == pytest.approx(1.0)


def test_decision_quality_validation() -> None:
    good = np.array([[1.0, 2.0, 3.0, 4.0, 5.0], [2.0, 1.0, 3.0, 4.0, 5.0]])
    assert sensitivity.decision_quality(good, good)["accuracy"] == pytest.approx(1.0)
    single = np.array([[1.0, 2.0, 3.0, 4.0, 5.0]])
    assert sensitivity.decision_quality(single, single)["accuracy"] == pytest.approx(1.0)
    bad_pairs = [np.zeros(5), np.zeros((0, 5)), np.zeros((1, 6)), np.full((1, 5), np.inf), np.full((1, 5), np.nan)]
    for bad in bad_pairs:
        with pytest.raises(ValueError, match="Aligned finite n-by-five prediction and exact outcomes required"):
            _ = sensitivity.decision_quality(bad, bad)
    with pytest.raises(ValueError, match="Aligned finite n-by-five prediction and exact outcomes required"):
        _ = sensitivity.decision_quality(np.zeros((2, 5)), np.zeros((3, 5)))
