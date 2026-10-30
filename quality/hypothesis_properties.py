"""Generative contracts for the active pathway and perspective model.

Missing Hypothesis remains blocked, not a successful skipped test suite. Historical
examples remain covered by ordinary regressions; these properties target current code.
"""

from dataclasses import replace
from typing import TYPE_CHECKING, cast

import numpy as np
from hypothesis import given, settings
from hypothesis import strategies as st

from scripts import analyse_v7
from src import audit_v7, deployment
from src.activity import ActivitySpec
from src.deployment import DeploymentPolicy, eligibility_catalogue
from src.pathways_v6 import PathwaySpec, compare_v6
from src.statewide import (
    Parameters,
    Site,
    _base_arrays,  # ruff: ignore[import-private-name] -- property test reuses the internal base-array builder  # pyright: ignore[reportPrivateUsage]
)

if TYPE_CHECKING:
    from collections.abc import Callable

# The numerical kernels below are untyped in the model package; bind precise call shapes here.
perspective_balances = cast(
    "Callable[..., tuple[object, dict[str, dict[str, np.ndarray]], object]]", analyse_v7.evaluate_perspectives
)
sampled_draws = cast("Callable[..., tuple[dict[str, np.ndarray], dict[str, np.ndarray]]]", audit_v7.sample_v7)
policy_outcomes = cast("Callable[..., dict[str, np.ndarray]]", deployment.evaluate_policy)

settings.register_profile("panda_ci", max_examples=100, deadline=None, derandomize=True)
settings.load_profile("panda_ci")
SITE = Site("Atherton", 157, 2022, "rural_proxy", "regional", pilot=True)
PROBABILITY = st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False)
MONEY = st.floats(min_value=0, max_value=1000000, allow_nan=False, allow_infinity=False)


@given(PROBABILITY, MONEY)
def test_null_all_effects_equal_has_no_resource_benefit(reliability: float, cost: float) -> None:
    """A unit odds ratio leaves no gross resource benefit or net saving."""
    p = Parameters(odds_ratio=1, reliability=reliability, equipment_cost=cost)
    result = compare_v6([SITE], p, PathwaySpec())
    for arm in result.values():
        np.testing.assert_allclose(arm["gross_resource_benefit"], 0, atol=1e-7)
        assert arm["net_saving"][0] <= 1e-7


@given(PROBABILITY, PROBABILITY, st.floats(min_value=0.01, max_value=10, allow_nan=False, allow_infinity=False))
def test_disjoint_paths_conserve_population(reliability: float, rescue: float, odds: float) -> None:
    """Immediate transfers, rescues and final local care sum to consultations."""
    p = Parameters(reliability=reliability, odds_ratio=odds)
    result = compare_v6([SITE], p, PathwaySpec(extra_rescue=rescue))
    for arm in result.values():
        np.testing.assert_allclose(
            arm["immediate_transfers"] + arm["delayed_rescues"] + arm["final_local"], arm["consultations"], atol=1e-8
        )


@given(PROBABILITY, PROBABILITY)
def test_perspective_transfers_do_not_create_social_resources(subsidy: float, funding: float) -> None:
    """Perspective transfers reallocate the bounded societal total, never add to it."""
    p = Parameters()
    s = PathwaySpec()
    x = _base_arrays(p, 1)
    _, ledger, _ = perspective_balances([SITE], p, s, x, {}, subsidy_fraction=subsidy, funding_response=funding)
    for arm in ledger.values():
        np.testing.assert_allclose(
            arm["state"] + arm["commonwealth"] + arm["patient_family"], arm["societal_bounded"], atol=1e-7
        )


@given(st.integers(min_value=0, max_value=2**31 - 1))
@settings(max_examples=25)
def test_active_shared_psa_draws_remain_paired(seed: int) -> None:
    """Adding a second site doubles additive hourly value on the same draws."""
    p = Parameters()
    s = PathwaySpec()
    x, e = sampled_draws(p, s, 80, seed)
    a = compare_v6([SITE], p, s, inputs=x, structural_draws=e)
    b = compare_v6([SITE, replace(SITE, name="Mareeba")], p, s, inputs=x, structural_draws=e)
    # Economic hourly value is additive; cash capacity steps intentionally are not.
    for key in a:
        np.testing.assert_allclose(b[key]["net_saving"], 2 * a[key]["net_saving"], atol=1e-7)


@given(st.integers(min_value=0, max_value=2**31 - 1))
@settings(max_examples=25)
def test_current_sampler_seed_reproducibility(seed: int) -> None:
    """Repeated draws from one seed reproduce the same clinical and economic arrays."""
    a, b = sampled_draws(n=50, seed=seed)
    c, d = sampled_draws(n=50, seed=seed)
    for key in a:
        np.testing.assert_array_equal(a[key], c[key])
    for key in b:
        np.testing.assert_array_equal(b[key], d[key])


# Active v13 properties. These are required but not claimed executed without Hypothesis.
@given(st.floats(min_value=1, max_value=5, allow_nan=False, allow_infinity=False))
def test_repeat_contacts_do_not_multiply_clinical_episodes(ratio: float) -> None:
    """Contact multiplicity scales workload hours but never clinical episodes."""
    a = compare_v6([SITE])["panda"]
    b = compare_v6([SITE], activity=ActivitySpec("episodes", ratio))["panda"]
    np.testing.assert_allclose(a["eventual_transfers"], b["eventual_transfers"])
    np.testing.assert_allclose(a["hub_hours"] * ratio, b["hub_hours"])


@given(st.floats(min_value=1, max_value=5, allow_nan=False, allow_infinity=False), PROBABILITY)
def test_policy_and_contact_population_conservation(ratio: float, reliability: float) -> None:
    """A mixed deployment policy conserves episodes and scales contacts with them."""
    sites = [SITE, replace(SITE, name="Mareeba")]
    policy = DeploymentPolicy("mixed", (("Atherton", "panda"), ("Mareeba", "telephone")))
    result = policy_outcomes(
        sites,
        policy,
        eligibility_catalogue(sites),
        Parameters(reliability=reliability),
        PathwaySpec(),
        (),
        activity=ActivitySpec("contacts", ratio),
    )
    np.testing.assert_allclose(result["eventual_transfers"] + result["final_local"], result["episodes"], atol=1e-8)
    np.testing.assert_allclose(result["contacts"], ratio * result["episodes"], atol=1e-8)
