"""Independent scalar arithmetic cross-checks, not independent clinical review."""

import ast
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, cast

import numpy as np
import pytest

from src.pathways_v6 import PathwaySpec, cash_budget, compare_v6, path_probabilities, sample_v6
from src.statewide import Parameters, Site, _base_arrays, load_sites, select_sites  # pyright: ignore[reportPrivateUsage] -- private kernel helper is the published in-repo surface under test
from src.strategies import KEYS

if TYPE_CHECKING:
    from collections.abc import Callable

# Heterogeneous failure-injection keywords are validated by the kernel itself.
_compare_v6 = cast("Callable[..., dict[str, dict[str, np.ndarray]]]", compare_v6)


def scalar_case(p: Parameters, s: PathwaySpec) -> tuple[float, float, list[float]]:
    """Hand-expressed one-pilot-site calculation; no new-kernel helper calls.

    Returns:
        Tuple of net saving, avoided transfers and per-arm care resource cost.
    """
    price = 7418
    origin = [0.8224 * price, 0.8224 * price, 1.6530 * price]
    receiving = [0.6454 * price, 1.4581 * price, 7.1826 * price]
    transport = (
        0.6 * p.road_cost
        + 0.25 * (18670 * 102.03 / (115.125 * (99.73 / 143.6))) * p.air_multiplier * 1.15
        + 0.15 * (18670 * 102.03 / (115.125 * (99.73 / 143.6))) * p.air_multiplier * 0.85
    ) * p.marginal_fraction
    care = [0.0, 0.0]
    transfers = [0.0, 0.0]
    for k, share in enumerate(p.case_mix):
        t = p.baseline_transfer[k]
        target = p.odds_ratio * t / (1 - t + p.odds_ratio * t) if k < 2 else t
        for arm in (0, 1):
            success = p.reliability if arm else 0
            immediate = (1 - success) * t * (1 - s.phone_delay_share) + success * target * (1 - s.video_delay_share)
            rescue = (1 - success) * t * s.phone_delay_share + success * (
                target * s.video_delay_share + (1 - target) * s.extra_rescue
            )
            local = (1 - success) * (1 - t) + success * (1 - target) * (1 - s.extra_rescue)
            population = p.calls_per_pilot_site * share
            hosp = (
                (immediate + rescue) * (origin[k] + receiving[k]) * s.hospital_resource_multiplier
                + local * receiving[k] * s.hospital_resource_multiplier * s.local_care_multiplier
                + rescue * s.extra_pre_rescue_cost
            ) * s.hospital_marginal_fraction
            care[arm] += population * (hosp + (immediate + rescue) * transport + rescue * s.rescue_receiving_premium)
            transfers[arm] += population * (immediate + rescue)
    annual = (
        p.equipment_cost / p.life_years
        if p.discount == 0
        else p.equipment_cost * p.discount / (1 - (1 + p.discount) ** (-p.life_years))
    )
    if not p.include_capital:
        annual = 0
    return (
        cast(
            "float",
            care[0]
            - care[1]
            - annual
            - (52 * p.check_minutes / 60 * p.loaded_hour + p.support + p.training)
            - (
                p.calls_per_pilot_site
                * (p.workflow_per_call / 75)
                * (s.local_coordination_per_call + s.hub_minutes_per_call * s.hub_hourly_rate / 60)
            ),
        ),
        transfers[0] - transfers[1],
        care,
    )


@pytest.mark.parametrize("seed", range(20))
def test_random_scalar_oracle(seed: int) -> None:
    rng = np.random.default_rng(seed)
    p = replace(
        Parameters(),
        odds_ratio=float(rng.uniform(0.3, 1.4)),
        reliability=float(rng.uniform(0, 1)),
        calls_per_pilot_site=float(rng.uniform(1, 100)),
        discount=float(rng.uniform(0, 0.1)),
        case_mix=tuple(rng.dirichlet([2, 4, 1])),
        baseline_transfer=tuple(rng.uniform(0.1, 0.99, 3)),
        workflow_per_call=float(rng.uniform(0, 175)),
    )
    s = replace(
        PathwaySpec(),
        phone_delay_share=float(rng.uniform(0, 0.2)),
        video_delay_share=float(rng.uniform(0, 0.3)),
        extra_rescue=float(rng.uniform(0, 0.1)),
        local_care_multiplier=float(rng.uniform(0.5, 2)),
        hospital_marginal_fraction=float(rng.uniform(0, 1)),
        hub_minutes_per_call=float(rng.uniform(0, 45)),
    )
    exact = compare_v6([Site("Synthetic", 100, 2022, "rural_proxy", "regional", pilot=True)], p, s)
    net, avoid, care = scalar_case(p, s)
    assert exact["panda"]["net_saving"][0] == pytest.approx(net, rel=1e-10, abs=1e-7)
    assert exact["panda"]["avoided_transfers"][0] == pytest.approx(avoid, abs=1e-10)
    assert exact["telephone"]["care_resource_cost"][0] == pytest.approx(care[0], abs=1e-7)
    assert exact["panda"]["care_resource_cost"][0] == pytest.approx(care[1], abs=1e-7)


@pytest.mark.parametrize("endpoint", ["eventual", "initial"])
@pytest.mark.parametrize("reliability", [0, 1, 0.35])
def test_population_conservation_in_each_draw(endpoint: str, reliability: float) -> None:
    p = Parameters(reliability=reliability)
    s = replace(PathwaySpec(), endpoint=endpoint)
    x, e = sample_v6(p, s, n=600, seed=600)
    out = compare_v6(select_sites(load_sites(), "spokes"), p, s, inputs=x, structural_draws=e)
    for arm in out.values():
        np.testing.assert_allclose(
            arm["immediate_transfers"] + arm["delayed_rescues"] + arm["final_local"], arm["consultations"], atol=1e-9
        )
        np.testing.assert_allclose(arm["initially_local"], arm["delayed_rescues"] + arm["final_local"], atol=1e-9)
        np.testing.assert_allclose(
            arm["hospital_benchmark_cost"],
            sum(
                arm[k]
                for k in [
                    "origin_benchmark_cost",
                    "receiving_benchmark_cost",
                    "local_benchmark_cost",
                    "pre_rescue_benchmark_cost",
                ]
            ),
            atol=1e-8,
        )


def test_hub_cash_change_cannot_change_resource_result() -> None:
    sites = select_sites(load_sites(), "spokes")
    a = compare_v6(sites, spec=PathwaySpec())["panda"]
    b = compare_v6(sites, spec=replace(PathwaySpec(), hub_spare_hours=0, hub_block_cost=900000))["panda"]
    np.testing.assert_allclose(a["net_saving"], b["net_saving"])
    assert b["cash_running_cost"][0] > a["cash_running_cost"][0]


def test_increasing_hub_workload_has_proportionate_cost() -> None:
    sites = select_sites(load_sites(), "pilot")
    a = compare_v6(sites)["panda"]
    b = compare_v6(sites, spec=replace(PathwaySpec(), hub_minutes_per_call=30))["panda"]
    assert b["programme_cost"][0] - a["programme_cost"][0] == pytest.approx(37.5 * 15 / 60 * 200)


def test_eventual_effect_no_double_counting_rescue() -> None:
    p = Parameters(odds_ratio=0.5, reliability=1)
    a = compare_v6(select_sites(load_sites(), "pilot"), p)["panda"]
    b = compare_v6(select_sites(load_sites(), "pilot"), p, replace(PathwaySpec(), video_delay_share=0.5))["panda"]
    np.testing.assert_allclose(a["avoided_transfers"], b["avoided_transfers"])
    assert b["net_saving"][0] < a["net_saving"][0]


def test_sample_reproducibility_and_null_resource_benefit() -> None:
    p = Parameters(odds_ratio=1)
    x, e = sample_v6(p, n=500, seed=601, effect_mode="null")
    y, f = sample_v6(p, n=500, seed=601, effect_mode="null")
    for k in x:
        np.testing.assert_array_equal(x[k], y[k])
    for k in e:
        np.testing.assert_array_equal(e[k], f[k])
    out = compare_v6(select_sites(load_sites(), "pilot"), p, inputs=x, structural_draws=e)
    for a in out.values():
        np.testing.assert_allclose(a["gross_resource_benefit"], 0, atol=1e-8)


def test_absolutely_no_activity_no_hub_but_readiness() -> None:
    a = compare_v6([Site("Zero", 0, 2022, "readiness", "remote")])["panda"]
    assert a["hub_resource_cost"][0] == a["hub_cash_cost"][0] == 0
    assert a["programme_cost"][0] > 0


def test_all_critical_has_no_transfer_avoidance() -> None:
    out = compare_v6(select_sites(load_sites(), "pilot"), Parameters(case_mix=(0, 0, 1)))
    for a in out.values():
        assert a["avoided_transfers"][0] == pytest.approx(0)


def test_budget_shared_attribution_not_discount_cash() -> None:
    sites = select_sites(load_sites(), "pilot")
    full = compare_v6(sites)["mobile"]
    shared = compare_v6(sites, overrides={"mobile": {"capital_share": 0.1}})["mobile"]
    np.testing.assert_array_equal(full["full_purchase_capital"], shared["full_purchase_capital"])
    shared_capital = cast("float", shared["capital_annualised"][0])
    full_capital = cast("float", full["capital_annualised"][0])
    assert shared_capital == pytest.approx(full_capital / 10)


@pytest.mark.parametrize(
    ("years", "remaining", "message"),
    [
        (0, 2, "Invalid cash-budget specification"),
        (3, -1, "Invalid cash-budget specification"),
        (3, 6, "Integer equipment life and feasible remaining life required"),
    ],
)
def test_invalid_budget(years: int, remaining: int, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        _ = cash_budget(select_sites(load_sites(), "pilot"), years=years, remaining_life=remaining)


def test_no_dataframe_imports_in_new_kernel() -> None:
    tree = ast.parse(Path("src/pathways_v6.py").read_text(encoding="utf-8"))
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            assert all(x.name.split(".")[0] not in {"pandas", "xarray"} for x in n.names)
        if isinstance(n, ast.ImportFrom):
            assert (n.module or "").split(".")[0] not in {"pandas", "xarray"}


def test_aggregation_matches_separate_site_care() -> None:
    sites = [*select_sites(load_sites(), "pilot"), Site("Remote synthetic", 40, 2022, "rural_proxy", "remote")]
    p = Parameters()
    x, e = sample_v6(p, n=150, seed=976)
    together = compare_v6(sites, p, inputs=x, structural_draws=e)
    separate = [compare_v6([site], p, inputs=x, structural_draws=e) for site in sites]
    for key in KEYS:
        for metric in [
            "consultations",
            "care_resource_cost",
            "transport_resource_cost",
            "hospital_benchmark_cost",
            "hub_resource_cost",
            "programme_cost",
            "net_saving",
        ]:
            np.testing.assert_allclose(together[key][metric], sum(item[key][metric] for item in separate), atol=1e-7)


@pytest.mark.parametrize(
    ("t", "odds", "ep", "message"),
    [
        (
            np.array([0.3, 0.65, 0.98]),
            np.array([0.5]),
            "eventual",
            "baseline_transfer must have shape",
        ),
        (np.array([[0.3, 0.65, 0.98]]), np.array([0.0]), "eventual", "odds ratio must be positive"),
        (
            np.array([[0.3, 0.65, 0.98]]),
            np.array([0.5, 0.6]),
            "eventual",
            "odds ratio requires one value per draw",
        ),
        (np.array([[0.3, 0.65, 0.98]]), np.array([0.5]), "unknown", "unknown transfer endpoint"),
    ],
)
def test_bad_path_shapes_and_endpoint(t: np.ndarray, odds: np.ndarray, ep: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        _ = path_probabilities(t, odds, np.array([1.0]), 0.05, 0.05, endpoint=ep)


def test_spec_rejects_unknown_endpoint() -> None:
    with pytest.raises(ValueError, match="endpoint must be eventual or initial"):
        _ = replace(PathwaySpec(), endpoint="unknown")


@pytest.mark.parametrize(
    ("failure", "message"),
    [
        ("empty", "non-empty unique sites required"),
        ("duplicate", "non-empty unique sites required"),
        ("sunk", "invalid sunk strategies"),
        ("shape", "bad input shape: road_cost"),
        ("mix", "case-mix rows must sum to one"),
        ("life", "positive equipment life required"),
        ("structural", "unknown structural draw"),
    ],
)
def test_bad_comparison_contract(failure: str, message: str) -> None:
    sites = select_sites(load_sites(), "pilot")
    x = _base_arrays(Parameters(), 1)
    kwargs: dict[str, object] = {}
    if failure == "empty":
        sites = []
    elif failure == "duplicate":
        sites = [*sites, *sites]
    elif failure == "sunk":
        kwargs["sunk"] = ("telephone",)
    elif failure == "shape":
        x["road_cost"] = np.array([4.0, 5.0])
    elif failure == "mix":
        x["case_mix"] = np.array([[0.1, 0.1, 0.1]])
    elif failure == "life":
        x["life_years"] = np.array([0.0])
    elif failure == "structural":
        kwargs["structural_draws"] = {"unknown": np.array([1.0])}
    with pytest.raises(ValueError, match=message):
        _ = _compare_v6(sites, inputs=x, **kwargs)
