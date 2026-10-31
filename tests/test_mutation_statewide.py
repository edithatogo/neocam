"""Mutation-burndown tests for the historical statewide kernel.

These tests pin exact observable values for ``src.statewide`` so that arithmetic,
comparison, boolean and boundary mutations change a value the public API returns.
They do not modify the module under test and add no suppression pragmas.
"""

from __future__ import annotations

import dataclasses
import math
from typing import TYPE_CHECKING, NotRequired, TypedDict, cast

import numpy as np
import pytest

from src import statewide
from src.statewide import Parameters, Site

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

_REL = 1e-9


class _EvaluateResult(TypedDict):
    """Numeric kernel plus the textual interpretation of the historical scenario."""

    consultations: float
    avoided_transfers: float
    programme_cost: float
    gross_resource_benefit: float
    family_benefit: float
    cash_running_cost: float
    net_saving: float
    societal_net_saving: float
    site_count: int
    births_2022: int
    interpretation: str


class _PsaSummary(TypedDict):
    """Scalar PSA envelope."""

    iterations: int
    seed: int
    effect_mode: str
    mean: float
    median: float
    lower: float
    upper: float
    probability_cost_saving: float
    mcse_probability: float
    mean_avoided_transfers: float
    mean_consultations: float
    mean_programme_cost: float
    annual_cost_only_evpi: float
    interpretation: str


class _PsaResult(TypedDict):
    """PSA envelope: shared draw arrays plus the summary."""

    summary: _PsaSummary
    draws: dict[str, np.ndarray]


class _SiteArgs(TypedDict):
    """Site field overrides used to drive malformed-record cases."""

    name: str
    births: int
    year: int
    group: str
    geography: str
    pilot: NotRequired[bool]


class _ParametersArgs(TypedDict, total=False):
    """Parameter overrides used to drive malformed-parameter cases."""

    equipment_cost: float
    life_years: float
    discount: float
    check_minutes: float
    loaded_hour: float
    support: float
    training: float
    workflow_per_call: float
    calls_per_pilot_site: float
    birth_growth: float
    state_uptake: float
    reliability: float
    odds_ratio: float
    case_mix: tuple[float, float, float]
    baseline_transfer: tuple[float, float, float]
    rescue_rate: float
    rescue_premium: float
    road_cost: float
    air_multiplier: float
    marginal_fraction: float
    downstream_delta: float
    family_delta: float
    hub_annual_cost: float
    capacity_threshold: float
    capacity_step_cost: float
    mode_air_shift: float
    include_capital: bool


# Driver returns bare containers; restate the asserted shapes.
evaluate = cast("Callable[..., _EvaluateResult]", statewide.evaluate)
psa = cast("Callable[..., _PsaResult]", statewide.psa)

# Eight collapsed records covering every dispatch factor, all three geographies,
# a pilot site, and more sites than the hub threshold so the capacity charge fires.
_SITES8 = [
    Site("Alpha", 100, 2022, "rural_proxy", "metro"),
    Site("Beta", 100, 2022, "rural_proxy", "regional"),
    Site("Gamma", 100, 2022, "rural_proxy", "remote"),
    Site("Delta", 100, 2022, "scn", "metro"),
    Site("Epsilon", 100, 2022, "hub", "metro"),
    Site("Zeta", 100, 2022, "readiness", "regional"),
    Site("Eta", 100, 2022, "regional_proxy", "remote"),
    Site("Theta", 100, 2022, "rural_proxy", "metro", pilot=True),
]
# Exactly the hub site-count threshold: no capacity charge at three sites.
_SITES3 = [
    Site("Alpha", 100, 2022, "rural_proxy", "metro"),
    Site("Gamma", 100, 2022, "rural_proxy", "remote"),
    Site("Theta", 100, 2022, "rural_proxy", "metro", pilot=True),
]

_EVAL8 = {
    "consultations": 46.83641975308642,
    "avoided_transfers": 2.896688862965827,
    "programme_cost": 93484.04866507626,
    "gross_resource_benefit": 22471.300143227112,
    "family_benefit": 4345.033294448741,
    "cash_running_cost": 75006.06481481482,
    "net_saving": -71012.74852184915,
    "societal_net_saving": -66667.7152274004,
}
_EVAL8_SHIFT = {
    "consultations": 46.83641975308642,
    "avoided_transfers": 2.896688862965827,
    "gross_resource_benefit": 54774.86999251139,
    "net_saving": -38709.17867256487,
    "societal_net_saving": -34364.14537811613,
}
_EVAL8_CAP10 = {
    "programme_cost": 213484.04866507626,
    "cash_running_cost": 195006.0648148148,
    "net_saving": -191012.74852184916,
}
_EVAL8_DISCOUNT0_PROGRAMME = 91006.0648148148
_EVAL8_NO_CAPITAL_PROGRAMME = 75006.06481481482

# Every non-default scaling parameter so each sampled multiplier is not 1.0.
_BIG = Parameters(
    calls_per_pilot_site=25.0,
    reliability=0.5,
    rescue_rate=0.025,
    rescue_premium=20000.0,
    road_cost=8000.0,
    air_multiplier=2.0,
    marginal_fraction=0.25,
    downstream_delta=4000.0,
    family_delta=3000.0,
    equipment_cost=20000.0,
    life_years=10.0,
    check_minutes=20.0,
    support=600.0,
    training=800.0,
    workflow_per_call=150.0,
    birth_growth=2.0,
)

_SAMPLED = {
    "air_anchor": [
        70563.74216844338,
        63963.078233182234,
        36318.05564273813,
        55016.29463720625,
        18375.771248206187,
        37645.821820127596,
    ],
    "air_multiplier": [2.0, 2.0, 2.0, 2.0, 2.0, 2.0],
    "baseline_transfer": [
        [0.2518846781561147, 0.7964354486758536, 0.98],
        [0.3278565655273754, 0.5678389674856272, 0.98],
        [0.35307829953936465, 0.6389962366011234, 0.98],
        [0.3635148860611484, 0.6214163312485955, 0.98],
        [0.3930275366952856, 0.6357241596752918, 0.98],
        [0.288162903999144, 0.6509917808197466, 0.98],
    ],
    "case_mix": [
        [0.4129509361322157, 0.537072918213494, 0.049976145654290316],
        [0.3933068985616488, 0.5407753377109971, 0.06591776372735425],
        [0.3394971108182976, 0.3411236220958759, 0.3193792670858265],
        [0.33063051077924116, 0.6224296234743255, 0.04693986574643331],
        [0.3289923016350321, 0.41742398261777963, 0.25358371574718824],
        [0.2862976212592177, 0.5697824110931854, 0.1439199676475969],
    ],
    "birth_growth": [
        2.0435905957436566,
        2.001664241737941,
        2.225994083710741,
        2.300256198200513,
        2.1531609697384315,
        2.193463814125804,
    ],
    "calls_per_pilot_site": [
        23.371468689363507,
        23.979688051278345,
        26.816962593156767,
        25.97665978788131,
        24.422157565046213,
        24.079300968710108,
    ],
    "capacity_step_cost": [30000.0] * 6,
    "capacity_threshold": [500.0] * 6,
    "check_minutes": [
        28.110803922362898,
        21.248732705802045,
        24.89895967769209,
        13.624064618716929,
        18.11896619817683,
        17.81975794342433,
    ],
    "discount": [0.05] * 6,
    "downstream_delta": [
        1106.5546397390222,
        3151.9930444814236,
        385.2981768557561,
        8440.445526257168,
        -638.4150759158624,
        4801.118891195201,
    ],
    "equipment_cost": [
        29667.397569827743,
        22027.327010671004,
        20124.087767945326,
        20613.373242615395,
        23474.769193925746,
        18594.958158385085,
    ],
    "family_delta": [
        2064.6284304391265,
        1878.264577942032,
        1995.060781419051,
        5781.477779321567,
        3503.201697114082,
        2860.3517070492126,
    ],
    "hub_annual_cost": [60000.0] * 6,
    "life_years": [
        11.218467692332244,
        12.071415912946847,
        9.899255907588678,
        9.740822176864256,
        8.14001699633523,
        9.678009280726894,
    ],
    "loaded_hour": [85.0] * 6,
    "marginal_fraction": [
        0.46653225418044847,
        0.3838525489847974,
        0.38253892172961784,
        0.1566960199912806,
        0.3186629140774731,
        0.3478522854678713,
    ],
    "mode_air_shift": [
        -0.12038266452453983,
        0.11785308940300598,
        -0.10306658539867677,
        0.029921832800463122,
        -0.08462399711359872,
        0.019662030046938398,
    ],
    "odds_ratio": [
        0.4096523922786708,
        0.8889618469217084,
        0.7959031759002733,
        0.3271909245290548,
        1.7071311562250848,
        1.005093525944731,
    ],
    "reliability": [
        0.5169798413925111,
        0.5109087285233189,
        0.5058747778347855,
        0.5009305057847673,
        0.523405324488634,
        0.5077049986813107,
    ],
    "rescue_premium": [
        33486.446106289404,
        18124.129361119543,
        31862.33700407334,
        20428.33749506817,
        36409.89204203979,
        32104.684963348536,
    ],
    "rescue_rate": [
        0.000715398963282697,
        0.03164474774827264,
        0.019504837888623932,
        0.026350146228963457,
        0.00848213275143799,
        0.071770880881821,
    ],
    "road_cost": [
        8065.818505640845,
        5633.68408386364,
        11228.813178912547,
        4270.003354561808,
        6111.040000444929,
        15210.316102064535,
    ],
    "state_uptake": [0.8] * 6,
    "support": [
        1770.4042863253965,
        231.21387994436844,
        508.31308847948145,
        194.11100108588062,
        995.3601166267131,
        1014.5443597175014,
    ],
    "training": [
        882.1843607643048,
        419.06157273172556,
        989.7648294986287,
        675.5563022103183,
        979.4611265485721,
        914.1642382894288,
    ],
    "workflow_per_call": [
        107.7359395226008,
        244.7140377315253,
        203.31344120504497,
        157.50367151188013,
        144.85675316624545,
        75.6610470858974,
    ],
}

_EFFECT_ODDS = {
    "published": [0.5475909348576214, 0.6530918701832579, 1.034721246222698, 0.6880384482111835, 0.583549816823978],
    "null": [1.0] * 5,
    "skeptical": [1.1026079923715988, 1.2564759420073375, 1.7673762678610725, 1.3059876544331992, 1.155848156740514],
    "attenuated": [0.7712283499050525, 0.8901319969585317, 1.2944770631499791, 0.9287052046870503, 0.812197962749085],
}

_BASE_KEYS = {
    "air_anchor",
    "air_multiplier",
    "baseline_transfer",
    "birth_growth",
    "calls_per_pilot_site",
    "capacity_step_cost",
    "capacity_threshold",
    "case_mix",
    "check_minutes",
    "discount",
    "downstream_delta",
    "equipment_cost",
    "family_delta",
    "hub_annual_cost",
    "life_years",
    "loaded_hour",
    "marginal_fraction",
    "mode_air_shift",
    "odds_ratio",
    "reliability",
    "rescue_premium",
    "rescue_rate",
    "road_cost",
    "state_uptake",
    "support",
    "training",
    "workflow_per_call",
}


def _close(actual: float, expected: float) -> bool:
    return math.isclose(actual, expected, rel_tol=_REL, abs_tol=1e-12)


def test_site_and_parameters_are_immutable() -> None:
    site = Site("Alpha", 10, 2022, "rural_proxy", "metro")
    with pytest.raises(dataclasses.FrozenInstanceError):
        # The assignment is the assertion that the record is frozen.
        site.births = 11  # pyright: ignore[reportAttributeAccessIssue]  # ty: ignore[invalid-assignment]

    params = Parameters()
    with pytest.raises(dataclasses.FrozenInstanceError):
        # The assignment is the assertion that the record is frozen.
        params.equipment_cost = 1.0  # pyright: ignore[reportAttributeAccessIssue]  # ty: ignore[invalid-assignment]


def test_new_site_is_not_a_pilot_site_by_default() -> None:
    assert Site("Alpha", 10, 2022, "rural_proxy", "metro").pilot is False
    assert Site("Alpha", 10, 2022, "rural_proxy", "metro", pilot=True).pilot is True


def test_site_accepts_boundary_records() -> None:
    low = Site("Alpha", 0, 1900, "readiness", "regional")
    high = Site("Beta", 5, 2100, "regional_proxy", "remote")
    assert low.births == 0
    assert low.year == 1900
    assert high.year == 2100


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"name": ""}, "non-empty"),
        ({"name": "Alpha", "births": -1}, "non-negative integer"),
        ({"name": "Alpha", "births": 1.5}, "non-negative integer"),
        ({"name": "Alpha", "year": 1899}, "Birth year"),
        ({"name": "Alpha", "year": 2101}, "Birth year"),
        ({"name": "Alpha", "year": 2022.0}, "Birth year"),
        ({"name": "Alpha", "group": "bogus"}, "Unknown site group"),
        ({"name": "Alpha", "geography": "bogus"}, "Unknown site geography"),
        ({"name": "Alpha", "pilot": 1}, "Pilot status"),
    ],
)
def test_site_rejects_malformed_records(kwargs: dict[str, object], message: str) -> None:
    base: dict[str, object] = {"name": "Alpha", "births": 5, "year": 2022, "group": "rural_proxy", "geography": "metro"}
    merged = {**base, **kwargs}
    with pytest.raises(ValueError, match=message):
        _ = Site(**cast("_SiteArgs", cast("object", merged)))


def test_parameters_accept_boundary_probabilities() -> None:
    assert Parameters(state_uptake=0).state_uptake == 0
    assert Parameters(state_uptake=1, reliability=1, rescue_rate=1, marginal_fraction=1).reliability == 1
    assert Parameters(case_mix=(1.0, 0.0, 0.0)).case_mix == (1.0, 0.0, 0.0)
    assert Parameters(baseline_transfer=(0.0, 0.5, 1.0)).baseline_transfer == (0.0, 0.5, 1.0)
    assert _close(Parameters(mode_air_shift=0.6).mode_air_shift, 0.6)
    assert _close(Parameters(mode_air_shift=-0.6).mode_air_shift, -0.6)
    assert Parameters(capacity_threshold=1).capacity_threshold == 1
    assert Parameters(equipment_cost=0).equipment_cost == 0
    assert Parameters(include_capital=False).include_capital is False
    assert Parameters(case_mix=cast("tuple[float, float, float]", cast("object", [0.5, 0.5, 0.0]))).case_mix == (
        0.5,
        0.5,
        0.0,
    )


@pytest.mark.parametrize(
    ("kwargs", "error", "message"),
    [
        ({"case_mix": 0.5}, TypeError, "three-value sequence"),
        ({"case_mix": (True, 0.0, 0.0)}, ValueError, "not boolean"),
        ({"case_mix": (0.5, 0.5, float("nan"))}, ValueError, "non-negative"),
        ({"case_mix": (-1.0, 1.0, 1.0)}, ValueError, "non-negative"),
        ({"case_mix": (0.5, 0.5)}, ValueError, "three non-negative"),
        ({"case_mix": (0.5, 0.5, 0.5)}, ValueError, "sum to one"),
        ({"baseline_transfer": (0.5, 0.5, 1.5)}, ValueError, "three probabilities"),
        ({"baseline_transfer": (-0.5, 0.75, 0.75)}, ValueError, "three probabilities"),
        ({"baseline_transfer": (0.5, 0.5)}, ValueError, "three probabilities"),
        ({"state_uptake": True}, ValueError, "not boolean"),
        ({"state_uptake": 1.5}, ValueError, r"must be in \[0,1\]"),
        ({"state_uptake": -0.1}, ValueError, r"must be in \[0,1\]"),
        ({"life_years": 0}, ValueError, "must be positive"),
        ({"capacity_threshold": 0}, ValueError, "must be positive"),
        ({"equipment_cost": -0.5}, ValueError, "cannot be negative"),
        ({"equipment_cost": float("nan")}, ValueError, "finite numeric"),
        ({"mode_air_shift": 0.61}, ValueError, "outside scenario bounds"),
        ({"include_capital": 1}, ValueError, "include_capital must be boolean"),
    ],
)
def test_parameters_reject_malformed_values(kwargs: dict[str, object], error: type[Exception], message: str) -> None:
    with pytest.raises(error, match=message):
        _ = Parameters(**cast("_ParametersArgs", cast("object", kwargs)))


def test_evaluate_pins_every_kernel_output() -> None:
    result = evaluate(_SITES8)
    values = cast("dict[str, float]", cast("object", result))
    for key, expected in _EVAL8.items():
        assert _close(values[key], expected), key
    assert result["site_count"] == 8
    assert result["births_2022"] == 800
    assert result["interpretation"] == "conditional scenario, not observed savings"


def test_evaluate_applies_mode_shift_and_air_multiplier() -> None:
    result = evaluate(_SITES8, Parameters(mode_air_shift=0.3, air_multiplier=2.0))
    values = cast("dict[str, float]", cast("object", result))
    for key, expected in _EVAL8_SHIFT.items():
        assert _close(values[key], expected), key


def test_evaluate_applies_birth_growth_to_non_pilot_volume() -> None:
    result = evaluate(_SITES8, Parameters(birth_growth=2.0))
    assert _close(result["consultations"], 81.17283950617283)
    assert _close(result["avoided_transfers"], 5.020291077166474)


def test_evaluate_charges_hub_capacity_above_threshold() -> None:
    result = evaluate(_SITES8, Parameters(capacity_threshold=10.0))
    values = cast("dict[str, float]", cast("object", result))
    for key, expected in _EVAL8_CAP10.items():
        assert _close(values[key], expected), key


def test_evaluate_without_hub_charge_at_three_sites() -> None:
    result = evaluate(_SITES3)
    assert _close(result["programme_cost"], 13218.410610514711)
    assert _close(result["net_saving"], -1491.1270368806872)
    assert result["site_count"] == 3


def test_evaluate_zero_and_sunk_capital_paths() -> None:
    zero_rate = evaluate(_SITES8, Parameters(discount=0.0))
    assert _close(zero_rate["programme_cost"], _EVAL8_DISCOUNT0_PROGRAMME)
    sunk = evaluate(_SITES8, Parameters(include_capital=False))
    assert _close(sunk["programme_cost"], _EVAL8_NO_CAPITAL_PROGRAMME)


def test_evaluate_defaults_parameters_when_omitted() -> None:
    assert evaluate(_SITES3)["site_count"] == 3


def test_base_arrays_key_set_and_values() -> None:
    values = statewide._base_arrays(Parameters(), 2)  # pyright: ignore[reportPrivateUsage] -- in-repo kernel surface
    assert set(values) == _BASE_KEYS
    assert "include_capital" not in values
    assert np.allclose(values["case_mix"], np.tile(Parameters().case_mix, (2, 1)))
    assert np.allclose(values["air_anchor"], statewide.index_air_cost())


def test_odds_transformation_exact_value() -> None:
    out = statewide._odds(np.array([0.2, 0.5]), np.array([0.5, 2.0]))  # pyright: ignore[reportPrivateUsage]
    assert np.allclose(out, [0.1111111111111111, 0.6666666666666666])


def test_index_air_cost_exact_values_and_guards() -> None:
    assert _close(statewide.index_air_cost(), 23824.90525591736)
    assert _close(statewide.index_air_cost(2.0, 3.0), 40324.05494836057)
    assert _close(statewide.index_air_cost(0.5, 1.0), 53765.40659781409)
    for bad in (0, -1, float("nan"), float("inf")):
        with pytest.raises(ValueError, match="CPI inputs"):
            _ = statewide.index_air_cost(base_cpi=bad)
        with pytest.raises(ValueError, match="CPI inputs"):
            _ = statewide.index_air_cost(target_cpi=bad)


def test_annuity_exact_values_and_guards() -> None:
    assert _close(statewide.annuity(10000, 5, 0.05), 2309.7479812826814)
    assert statewide.annuity(10000, 5, 0) == 2000
    assert statewide.annuity(0, 5, 0.05) == 0
    assert _close(statewide.annuity(10000, 0.5, 0.05), 20746.950765959595)
    for args in ((-0.5, 5, 0.05), (1, -1, 0.05), (1, 5, -0.5), (1, 0, 0.05)):
        with pytest.raises(ValueError, match="Invalid annuity input"):
            _ = statewide.annuity(*args)


def test_funding_ledger_values_and_guards() -> None:
    ledger = statewide.funding_ledger(2, 3, 7418, 7000)
    assert ledger["national_benchmark"] == 14836
    assert ledger["queensland_benchmark"] == 21000
    zeros = statewide.funding_ledger(0, 0, 0, 0)
    assert zeros["national_benchmark"] == 0
    assert zeros["queensland_benchmark"] == 0
    assert _close(cast("float", statewide.funding_ledger(0.5, None, 0.5, None)["national_benchmark"]), 0.25)
    assert statewide.funding_ledger(2, 2.1, 7418, None)["queensland_benchmark"] is None
    for bad in (-0.5, float("nan"), float("inf")):
        with pytest.raises(ValueError, match="Funding inputs"):
            _ = statewide.funding_ledger(bad, None, 1, None)


def test_mchs_support_labels() -> None:
    assert statewide.mchs_support(2024) == "historical_interface_only"
    assert statewide.mchs_support(2025) == "historical_interface_only"
    assert statewide.mchs_support(2026) == "official_GEN_WAU_export_required"


def test_sample_inputs_pins_every_draw() -> None:
    draws = statewide.sample_inputs(_BIG, n=6, seed=12345)
    for key, expected in _SAMPLED.items():
        assert np.allclose(np.asarray(draws[key], dtype=float), np.asarray(expected, dtype=float)), key


def test_sample_inputs_effect_structures() -> None:
    for mode, expected in _EFFECT_ODDS.items():
        draws = statewide.sample_inputs(_BIG, n=5, seed=4242, effect_mode=mode)
        assert np.allclose(np.asarray(draws["odds_ratio"], dtype=float), np.asarray(expected)), mode


def test_sample_inputs_baseline_transfer_boundaries_and_case_mix_zeros() -> None:
    p = dataclasses.replace(_BIG, baseline_transfer=(0.0, 0.5, 1.0), case_mix=(0.5, 0.5, 0.0))
    draws = statewide.sample_inputs(p, n=6, seed=12345)
    baseline = np.asarray(draws["baseline_transfer"], dtype=float)
    assert np.allclose(baseline[:, 0], 0.0)
    assert np.allclose(baseline[:, 2], 1.0)
    assert np.allclose(
        baseline[:, 1],
        [
            0.4748501575109527,
            0.5159536694882538,
            0.530095445316995,
            0.6023608127027306,
            0.5668111833036489,
            0.5416712961678207,
        ],
    )
    case_mix = np.asarray(draws["case_mix"], dtype=float)
    assert np.allclose(case_mix[:, 2], 0.0)
    assert np.allclose(
        case_mix[:, 0],
        [
            0.6584388136625959,
            0.42948214897404074,
            0.48381444527372386,
            0.47085036586940016,
            0.4933274219434572,
            0.5025933225595147,
        ],
    )


def test_sample_inputs_sampled_stratum_at_probability_one() -> None:
    p = dataclasses.replace(_BIG, baseline_transfer=(1.0, 0.0, 0.5), case_mix=(0.5, 0.5, 0.0))
    draws = statewide.sample_inputs(p, n=6, seed=12345)
    baseline = np.asarray(draws["baseline_transfer"], dtype=float)
    assert np.allclose(baseline[:, 0], 1.0)
    assert np.allclose(baseline[:, 1], 0.0)
    assert np.allclose(baseline[:, 2], 0.5)
    case_mix = np.asarray(draws["case_mix"], dtype=float)
    assert np.allclose(case_mix[:, 2], 0.0)
    assert np.allclose(
        case_mix[:, 0],
        [
            0.4748501575109527,
            0.5159536694882538,
            0.530095445316995,
            0.6023608127027306,
            0.5668111833036489,
            0.5416712961678208,
        ],
    )


def test_sample_inputs_defaults_and_draw_guard() -> None:
    assert set(statewide.sample_inputs()) == _BASE_KEYS
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(statewide, "_MIN_DRAWS", 3)
    monkeypatch.setattr(statewide, "_MAX_DRAWS", 6)
    try:
        assert len(statewide.sample_inputs(n=3)["odds_ratio"]) == 3
        assert len(statewide.sample_inputs(n=6)["odds_ratio"]) == 6
        for bad in (2, 7):
            with pytest.raises(ValueError, match="n must be between 2 and 1000000"):
                _ = statewide.sample_inputs(n=bad)
        with pytest.raises(ValueError, match="n must be an integer"):
            _ = statewide.sample_inputs(n=cast("int", cast("object", 3.0)))  # runtime rejects a non-integer n
        with pytest.raises(ValueError, match="Unsupported effect model"):
            _ = statewide.sample_inputs(n=3, effect_mode="magic")
    finally:
        monkeypatch.undo()


def test_psa_summary_consistent_with_draws() -> None:
    result = psa(_SITES3, n=60, seed=7)
    summary = result["summary"]
    draws = result["draws"]
    net = np.asarray(draws["net_saving"], dtype=float)
    prob = float(np.mean(net > 0))
    assert 0.0 < prob < 1.0
    assert _close(summary["probability_cost_saving"], prob)
    assert _close(summary["mcse_probability"], math.sqrt(prob * (1 - prob) / 60))
    evpi = float(np.mean(np.maximum(net, 0)) - max(np.mean(net), 0))
    assert _close(summary["annual_cost_only_evpi"], max(evpi, 0))
    assert summary["iterations"] == 60
    assert summary["interpretation"] == "conditional researcher-prior PSA; not an empirical posterior"


def test_psa_zero_saving_scenario() -> None:
    summary = psa([], n=5, seed=1)["summary"]
    assert _close(summary["probability_cost_saving"], 0.0)
    assert _close(summary["annual_cost_only_evpi"], 0.0)
    assert _close(summary["mcse_probability"], 0.0)


def test_psa_net_draws_straddling_zero() -> None:
    parameters = Parameters(
        support=0.0,
        training=0.0,
        check_minutes=0.0,
        equipment_cost=0.0,
        workflow_per_call=0.0,
        hub_annual_cost=0.0,
        capacity_step_cost=0.0,
        marginal_fraction=0.0,
        downstream_delta=0.0,
        rescue_rate=0.0,
    )
    result = psa([Site("Alpha", 1, 2022, "rural_proxy", "metro")], n=64, seed=1, parameters=parameters)
    summary = result["summary"]
    net = np.asarray(result["draws"]["net_saving"], dtype=float)
    assert np.any((net > 0) & (net <= 1))
    assert np.any(net > 1)
    prob = float(np.mean(net > 0))
    assert _close(summary["probability_cost_saving"], prob)
    assert _close(summary["mcse_probability"], math.sqrt(prob * (1 - prob) / 64))
    evpi = float(np.mean(np.maximum(net, 0)) - max(np.mean(net), 0))
    assert evpi > 0
    assert _close(summary["annual_cost_only_evpi"], evpi)


def test_psa_defaults_parameters_when_omitted() -> None:
    result = psa(_SITES3, n=4)
    assert result["summary"]["iterations"] == 4


def test_survival_extension_exact_values() -> None:
    result = statewide.survival_extension(
        10.0,
        0.25,
        0.4,
        discount=0.1,
        years=3,
        utility_no_major=0.8,
        utility_major=0.5,
        annual_cost_no_major=1000,
        annual_cost_major=20000,
    )
    assert _close(result["extra_survivors"], 2.5)
    assert _close(result["major_morbidity_survivors"], 1.0)
    assert _close(result["qalys"], 4.227648384673178)
    assert _close(result["costs"], 53467.31780616077)


def test_survival_extension_boundaries_and_guards() -> None:
    assert _close(statewide.survival_extension(0, 0.0, 0.0)["extra_survivors"], 0.0)
    assert _close(
        statewide.survival_extension(0.5, 1.0, 1.0, discount=0.0, years=1, utility_no_major=1.0, utility_major=1.0)[
            "extra_survivors"
        ],
        0.5,
    )
    assert _close(statewide.survival_extension(10, 0.5, 0.5, annual_cost_no_major=0, annual_cost_major=0)["costs"], 0.0)
    for args, kwargs, message in (
        ((-1, 0.1, 0.5), {}, "Invalid survival scenario"),
        ((10, 0.1, 0.5), {"years": 0}, "Invalid survival scenario"),
        ((10, 0.1, 0.5), {"discount": -1}, "Invalid survival scenario"),
        ((10, -0.5, 0.5), {}, "Probabilities and utilities"),
        ((10, 0.1, 1.5), {}, "Probabilities and utilities"),
        ((10, 0.1, 0.5), {"annual_cost_no_major": -1}, "Negative annual cost"),
    ):
        with pytest.raises(ValueError, match=message):
            _ = statewide.survival_extension(*args, **kwargs)


def test_budget_impact_schedule_and_guards() -> None:
    records = statewide.budget_impact(_SITES3, 6)
    cash_running = evaluate(_SITES3)["cash_running_cost"]
    capital = 30000.0
    assert [r["year"] for r in records] == [1, 2, 3, 4, 5, 6]
    assert [r["capital"] for r in records] == [capital, 0.0, 0.0, 0.0, 0.0, capital]
    for record in records:
        assert _close(record["cash_expenditure"], record["capital"] + cash_running)
        gross = evaluate(_SITES3)["gross_resource_benefit"]
        assert _close(record["resource_net_saving_excluding_funding"], gross - record["cash_expenditure"])
    continued = statewide.budget_impact(_SITES3, 6, replacement=False)
    assert sum(r["capital"] for r in continued) == 0
    short_life = statewide.budget_impact(_SITES3, 4, parameters=Parameters(life_years=0.5))
    assert [r["capital"] for r in short_life] == [capital, capital, capital, capital]
    assert len(statewide.budget_impact(_SITES3, 1)) == 1
    with pytest.raises(ValueError, match="years must be positive"):
        _ = statewide.budget_impact(_SITES3, 0)


def _write_births(tmp_path: Path, rows: list[tuple[str, int, int, str]]) -> Path:
    path = tmp_path / "births.csv"
    body = "facility,births,year,sector\n" + "".join(f"{f},{b},{y},{s}\n" for f, b, y, s in rows)
    _ = path.write_text(body, encoding="utf-8")
    return path


def test_load_sites_classifies_by_volume_thresholds(tmp_path: Path) -> None:
    path = _write_births(
        tmp_path,
        [
            ("Alpha", 0, 2022, "public"),
            ("Beta", 19, 2022, "public"),
            ("Gamma", 20, 2022, "public"),
            ("Delta", 999, 2022, "public"),
            ("Epsilon", 1000, 2022, "public"),
        ],
    )
    groups = {s.name: s.group for s in statewide.load_sites(path)}
    assert groups == {
        "Alpha": "readiness",
        "Beta": "readiness",
        "Gamma": "rural_proxy",
        "Delta": "rural_proxy",
        "Epsilon": "regional_proxy",
    }


def test_load_sites_applies_alias_and_geography(tmp_path: Path) -> None:
    path = _write_births(
        tmp_path,
        [
            ("Cairns Hospital Birthing Centre", 50, 2022, "public"),
            ("Ipswich", 300, 2022, "public"),
            ("Mount Isa", 50, 2022, "public"),
        ],
    )
    sites = {s.name: s for s in statewide.load_sites(path)}
    assert sites["Cairns"].group == "scn"
    assert sites["Cairns"].geography == "regional"
    assert sites["Ipswich"].geography == "metro"
    assert sites["Mount Isa"].geography == "remote"


def test_load_sites_rejects_negative_counts(tmp_path: Path) -> None:
    path = _write_births(tmp_path, [("Alpha", -1, 2022, "public")])
    with pytest.raises(ValueError, match="negative birth count"):
        _ = statewide.load_sites(path)


def test_load_sites_rejects_duplicates_mixed_years_and_missing_columns(tmp_path: Path) -> None:
    duplicate = _write_births(tmp_path, [("Alpha", 5, 2022, "public"), ("Alpha", 6, 2022, "public")])
    with pytest.raises(ValueError, match="duplicate birth facility row"):
        _ = statewide.load_sites(duplicate)
    mixed = _write_births(tmp_path, [("Alpha", 5, 2022, "public"), ("Beta", 6, 2023, "public")])
    with pytest.raises(ValueError, match="one year only"):
        _ = statewide.load_sites(mixed)
    missing = tmp_path / "missing.csv"
    _ = missing.write_text("facility,births\nAlpha,5\n", encoding="utf-8")
    with pytest.raises(ValueError, match="requires facility, births and year columns"):
        _ = statewide.load_sites(missing)


def test_load_sites_default_table_totals() -> None:
    sites = statewide.load_sites()
    assert len(sites) == 65
    assert sum(s.births for s in sites) == 46711


def test_select_sites_portfolios() -> None:
    sites = statewide.load_sites()
    assert {s.name for s in statewide.select_sites(sites, "pilot")} == {"Atherton", "Mareeba", "Innisfail"}
    assert all(s.group not in {"hub", "readiness"} for s in statewide.select_sites(sites, "spokes"))
    assert all(s.group == "rural_proxy" for s in statewide.select_sites(sites, "rural"))
    assert all(s.group == "readiness" for s in statewide.select_sites(sites, "readiness"))
    assert statewide.select_sites(sites, "all_public") == sites
    with pytest.raises(ValueError, match="Unknown portfolio"):
        _ = statewide.select_sites(sites, "unknown")
