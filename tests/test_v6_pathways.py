"""Executable requirements for the explicit v6 kernel (written before implementation)."""

from dataclasses import replace

import numpy as np
import pytest

from src.pathways_v6 import PathwaySpec, cash_budget, compare_v6, hospital_cost, hub_cost, path_probabilities
from src.statewide import Parameters, Site, load_sites, select_sites


def test_final_endpoint_conserved_and_no_double_rescue_penalty():
    t = np.array([[0.3, 0.65, 0.98]])
    a = path_probabilities(t, np.array([0.5]), np.array([1.0]), 0.1, 0.1)
    target = 0.5 * t / (1 - t + 0.5 * t)
    target[:, 2] = t[:, 2]
    np.testing.assert_allclose(a["video_immediate"] + a["video_rescue"], target)
    np.testing.assert_allclose(a["video_immediate"] + a["video_rescue"] + a["video_local"], 1)
    np.testing.assert_allclose(a["phone_immediate"] + a["phone_rescue"] + a["phone_local"], 1)
    np.testing.assert_allclose(a["video_initial_local"], a["video_rescue"] + a["video_local"])


def test_no_video_returns_phone_even_with_extra_rescue_assumption():
    a = path_probabilities(
        np.array([[0.3, 0.65, 0.98]]), np.array([0.48]), np.array([0.0]), 0.05, 0.2, extra_rescue=0.2
    )
    for suffix in ("immediate", "rescue", "local"):
        np.testing.assert_allclose(a["phone_" + suffix], a["video_" + suffix])


def test_rescue_share_changes_timing_not_final_endpoint():
    t = np.array([[0.3, 0.65, 0.98]])
    a = path_probabilities(t, np.array([1.0]), np.array([1.0]), 0.05, 0.25)
    np.testing.assert_allclose(a["video_immediate"] + a["video_rescue"], t)
    assert np.all(a["video_rescue"] > a["phone_rescue"])


def test_extra_rescue_only_moves_local_to_rescue_on_successful_video():
    t = np.array([[0.3, 0.65, 0.98]])
    a = path_probabilities(t, np.array([1.0]), np.array([1.0]), 0.05, 0.05, extra_rescue=0.1)
    np.testing.assert_allclose(a["video_rescue"] - a["phone_rescue"], (1 - t) * 0.1)
    np.testing.assert_allclose(a["video_immediate"] + a["video_rescue"] + a["video_local"], 1)


@pytest.mark.parametrize("prob", [-0.1, 1.1, float("nan")])
def test_invalid_path_inputs_rejected(prob):
    with pytest.raises(ValueError, match="Invalid baseline transfer"):
        path_probabilities(np.array([[prob, 0.65, 0.98]]), np.array([0.5]), np.array([1.0]), 0.05, 0.05)


def test_hub_cost_depends_on_hours_not_sites():
    spec = PathwaySpec()
    a = hub_cost(np.array([100.0]), np.array([15.0]), spec)
    b = hub_cost(np.array([100.0]), np.array([15.0]), spec)
    assert a["hours"][0] == 25
    assert a["economic"][0] == 5000
    assert a["cash_capacity"][0] == b["cash_capacity"][0]


def test_hub_zero_and_capacity_boundary():
    spec = replace(PathwaySpec(), hub_spare_hours=20, hub_block_hours=10, hub_block_cost=2000)
    a = hub_cost(np.array([0.0, 80.0, 80.04]), np.array([15.0, 15.0, 15.0]), spec)
    np.testing.assert_allclose(a["cash_capacity"], [0, 0, 2000])
    np.testing.assert_allclose(a["economic"], [0, 4000, 4002])


def test_hospital_cost_counts_receiving_once():
    # 0.4 immediate, 0.1 rescue, 0.5 local. Origin=100, receiver=1000,
    # local=200, extra pre-rescue=50 => 655 before any rescue morbidity premium.
    val = hospital_cost(
        np.array([0.4]),
        np.array([0.1]),
        np.array([0.5]),
        np.array([100.0]),
        np.array([1000.0]),
        np.array([200.0]),
        np.array([50.0]),
    )
    np.testing.assert_allclose(val, 655)


def test_null_effect_has_zero_clinical_resource_benefit():
    sites = select_sites(load_sites(), "pilot")
    out = compare_v6(sites, parameters=replace(Parameters(), odds_ratio=1.0))
    for a in out.values():
        assert abs(a["avoided_transfers"][0]) < 1e-10
        assert abs(a["gross_resource_benefit"][0]) < 1e-8
        assert a["net_saving"][0] <= 0


def test_fourth_zero_activity_site_does_not_trigger_hub_charge():
    base = select_sites(load_sites(), "pilot")
    zero = Site("zero", 0, 2022, "readiness", "remote")
    a = compare_v6(base)["panda"]
    b = compare_v6([*base, zero])["panda"]
    np.testing.assert_allclose(a["hub_resource_cost"], b["hub_resource_cost"])
    np.testing.assert_allclose(a["hub_cash_cost"], b["hub_cash_cost"])


def test_telephone_reports_absolute_care_not_zero_patients():
    a = compare_v6(select_sites(load_sites(), "pilot"))["telephone"]
    assert a["immediate_transfers"][0] > 0
    assert a["hospital_benchmark_cost"][0] > 0
    assert a["programme_cost"][0] == 0
    assert a["net_saving"][0] == 0


def test_cash_existing_remaining_life_not_perpetually_free():
    rows = cash_budget(select_sites(load_sites(), "pilot"), strategy="panda", years=7, incumbent=True, remaining_life=2)
    assert rows[0]["capital"] == 0
    assert rows[1]["capital"] == 0
    assert rows[2]["capital"] == 30000


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("hub_hourly_rate", -1, "hub_hourly_rate must be finite non-negative numeric"),
        ("phone_delay_share", 1.1, "phone_delay_share must be a probability"),
        ("hospital_marginal_fraction", float("nan"), "hospital_marginal_fraction must be finite non-negative numeric"),
        ("hub_block_hours", 0, "hub_block_hours must be positive"),
    ],
)
def test_spec_invalid(field, value, message):
    with pytest.raises(ValueError, match=message):
        replace(PathwaySpec(), **{field: value})
