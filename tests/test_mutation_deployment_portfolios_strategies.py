"""Mutation-killing behaviour for deployment, portfolios_v7 and strategies.

Each test targets a surviving mutant reported in
``verification/v13/burndown/mutation-survivors.md`` and is written against the
public API so the assertion fails when the mutation changes behaviour.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import cast

import numpy as np
import pytest

from src import deployment, portfolios_v7, strategies
from src.equipment import OwnedAsset
from src.pathways_v6 import PathwaySpec, _activity  # pyright: ignore[reportPrivateUsage] -- private kernel helper under test
from src.statewide import Parameters, Site, _base_arrays, load_sites, select_sites  # pyright: ignore[reportPrivateUsage]

# --- shared deterministic fixtures -------------------------------------------------


def pilot_sites() -> list[Site]:
    """Three declared pilot sites, matching deployment.PILOT_NAMES.

    Returns:
        The three pilot site records.
    """
    return [
        Site("Atherton", 100, 2022, "regional_proxy", "regional", pilot=True),
        Site("Mareeba", 100, 2022, "regional_proxy", "regional", pilot=True),
        Site("Innisfail", 100, 2022, "regional_proxy", "regional", pilot=True),
    ]


def eligibility_for(sites: list[Site]) -> tuple[deployment.Eligibility, ...]:
    """Hypothetical-permitted catalogue for every site and strategy.

    Returns:
        Eligibility records for every site and strategy pairing.
    """
    return deployment.eligibility_catalogue(sites, allow_hypothetical=True)


def panda_policy(sites: list[Site]) -> deployment.DeploymentPolicy:
    """One conditional policy assigning every site to Panda.

    Returns:
        A conditional policy assigning each site to Panda.
    """
    return deployment.DeploymentPolicy("panda_only", tuple((s.name, "panda") for s in sites), conditional=True)


# --- deployment.Eligibility / DeploymentPolicy validation --------------------------


def test_eligibility_rejects_blank_site() -> None:
    """Line 41: invalid_site must stay an OR, not collapse to AND."""
    with pytest.raises(ValueError, match="Invalid eligibility record"):
        _ = deployment.Eligibility("", "panda", "hypothetical", "src")
    with pytest.raises(ValueError, match="Invalid eligibility record"):
        _ = deployment.Eligibility("   ", "panda", "hypothetical", "src")


def test_eligibility_rejects_blank_evidence() -> None:
    """Line 42: invalid_evidence must stay an OR, not collapse to AND."""
    with pytest.raises(ValueError, match="Invalid eligibility record"):
        _ = deployment.Eligibility("Atherton", "panda", "hypothetical", "")
    with pytest.raises(ValueError, match="Invalid eligibility record"):
        _ = deployment.Eligibility("Atherton", "panda", "hypothetical", "  ")


def test_records_are_frozen() -> None:
    """Lines 26 and 48: the frozen dataclasses must reject attribute writes."""
    record = deployment.Eligibility("Atherton", "panda", "hypothetical", "src")
    with pytest.raises(FrozenInstanceError):
        record.site = "Other"  # pyright: ignore[reportAttributeAccessIssue]  # ty: ignore[invalid-assignment]
    policy = deployment.DeploymentPolicy("n", (("Atherton", "panda"),))
    with pytest.raises(FrozenInstanceError):
        policy.name = "other"  # pyright: ignore[reportAttributeAccessIssue]  # ty: ignore[invalid-assignment]


def test_policy_conditional_defaults_to_strict() -> None:
    """Line 54: conditional must default to False, not True."""
    policy = deployment.DeploymentPolicy("n", (("Atherton", "panda"),))
    assert policy.conditional is False


def test_policy_rejects_blank_name() -> None:
    """Line 62: the identity guard must catch a blank name via OR."""
    with pytest.raises(ValueError, match="Invalid deployment policy identity"):
        _ = deployment.DeploymentPolicy("", (("Atherton", "panda"),))
    with pytest.raises(ValueError, match="Invalid deployment policy identity"):
        _ = deployment.DeploymentPolicy("n", (("Atherton", "panda"),), conditional=cast("bool", cast("object", 1)))


def test_policy_rejects_empty_assignments() -> None:
    """Line 66: empty assignments must be rejected via OR."""
    with pytest.raises(ValueError, match="Nonempty assignments required"):
        _ = deployment.DeploymentPolicy("n", ())


@pytest.mark.parametrize(
    "bad_row",
    [5, ["Atherton"], ("", "panda"), ("Atherton", "invented")],
    ids=["non-sequence", "short-list", "blank-element", "unknown-strategy"],
)
def test_policy_rejects_bad_assignment_rows(bad_row: object) -> None:
    """Lines 71 and 73: row shape and element guards must stay OR-chained."""
    with pytest.raises(ValueError, match="Invalid policy assignment"):
        _ = deployment.DeploymentPolicy("n", (cast("tuple[str, str]", bad_row),))


def test_eligibility_catalogue_requires_explicit_hypothetical_permission() -> None:
    """Lines 81 and 98: hypothetical permission is explicit and pilot Panda is reported."""
    atherton = Site("Atherton", 100, 2022, "regional_proxy", "regional", pilot=True)
    tully = Site("Tully", 50, 2022, "readiness", "regional")
    sites = [atherton, tully]
    strict = {(r.site, r.strategy): r.status for r in deployment.eligibility_catalogue(sites)}
    assert strict["Atherton", "panda"] == "reported_operation"
    assert strict["Atherton", "obsbot"] == "unknown"
    assert strict["Tully", "obsbot"] == "unknown"
    allowed = {(r.site, r.strategy): r.status for r in eligibility_for(sites)}
    assert allowed["Atherton", "panda"] == "reported_operation"
    assert allowed["Atherton", "obsbot"] == "hypothetical"
    assert allowed["Tully", "panda"] == "hypothetical"


# --- deployment.validate_policy ----------------------------------------------------


def test_validate_policy_rejects_empty_scope() -> None:
    """Line 120: an empty site scope must be rejected via OR."""
    sites = [Site("Atherton", 100, 2022, "regional_proxy", "regional")]
    eligibility = eligibility_for(sites)
    policy = deployment.DeploymentPolicy("n", (("Atherton", "panda"),), conditional=True)
    with pytest.raises(ValueError, match="Unique nonempty site scope"):
        deployment.validate_policy([], policy, eligibility)


def test_validate_policy_rejects_record_for_unknown_site() -> None:
    """Line 124: a valid record for an unknown site must be rejected via OR."""
    sites = [Site("Atherton", 100, 2022, "regional_proxy", "regional")]
    eligibility = (deployment.Eligibility("Elsewhere", "panda", "hypothetical", "src"),)
    policy = deployment.DeploymentPolicy("n", (("Atherton", "panda"),), conditional=True)
    with pytest.raises(ValueError, match="Unknown site or malformed eligibility"):
        deployment.validate_policy(sites, policy, eligibility)


# --- deployment.evaluate_policies --------------------------------------------------


def test_evaluate_policies_requires_nonempty_policies() -> None:
    """Line 205: an empty policy tuple must be rejected via OR."""
    sites = pilot_sites()
    eligibility = eligibility_for(sites)
    with pytest.raises(ValueError, match="Nonempty typed policies required"):
        _ = deployment.evaluate_policies(sites, (), eligibility, Parameters(), PathwaySpec(), ())


def test_evaluate_policies_default_applies_retention() -> None:
    """Line 191: retain must default to True, so owned assets offset procurement."""
    sites = pilot_sites()
    eligibility = eligibility_for(sites)
    policy = panda_policy(sites)
    assets = (OwnedAsset("Atherton", "panda", 5),)
    gross_policies = deployment.evaluate_policies(
        sites, (policy,), eligibility, Parameters(), PathwaySpec(), assets, retain=False
    )
    kept_policies = deployment.evaluate_policies(sites, (policy,), eligibility, Parameters(), PathwaySpec(), assets)
    gross = cast("float", gross_policies[policy.name]["incremental_purchase_capital"][0])
    kept = cast("float", kept_policies[policy.name]["incremental_purchase_capital"][0])
    assert gross == pytest.approx(30000.0)
    assert kept == pytest.approx(gross * 2 / 3)
    assert kept < gross


def test_conditional_rescue_risk_is_zero_with_no_initially_local(monkeypatch: pytest.MonkeyPatch) -> None:
    """Line 248: the divide mask is strictly > 0, not >= 0 or shifted."""
    sites = pilot_sites()[:1]
    eligibility = eligibility_for(sites)
    policy = panda_policy(sites)

    def fake_compare_v6(*_args: object, **_kwargs: object) -> dict[str, dict[str, np.ndarray]]:
        zeros = np.zeros(2)
        return {
            "panda": {
                "delayed_rescues": np.array([5.0, 5.0]),
                "initially_local": np.array([0.0, 1.0]),
                "episodes": zeros.copy(),
                "hub_hours": zeros.copy(),
                "local_ready_cost": zeros.copy(),
                "local_workflow_cost": zeros.copy(),
            }
        }

    monkeypatch.setattr(deployment, "compare_v6", fake_compare_v6)
    out = deployment.evaluate_policies(sites, (policy,), eligibility, Parameters(), PathwaySpec(), (), retain=False)
    np.testing.assert_allclose(out[policy.name]["conditional_rescue_risk"], np.array([0.0, 5.0]))


# --- deployment.policy_cash_budget -------------------------------------------------


def test_cash_budget_years_bounds() -> None:
    """Line 318: the 1..100 horizon guard keeps both inclusive bounds."""
    sites = pilot_sites()
    eligibility = eligibility_for(sites)
    policy = panda_policy(sites)
    assert len(deployment.policy_cash_budget(sites, policy, eligibility, Parameters(), PathwaySpec(), (), years=1)) == 1
    assert (
        len(deployment.policy_cash_budget(sites, policy, eligibility, Parameters(), PathwaySpec(), (), years=100))
        == 100
    )
    for bad in (0, 101, True):
        with pytest.raises(ValueError, match=r"Budget years must be an integer in 1\.\.100"):
            _ = deployment.policy_cash_budget(sites, policy, eligibility, Parameters(), PathwaySpec(), (), years=bad)


def test_cash_budget_rows_are_one_based_and_sum_cash() -> None:
    """Lines 342 and 348: year index is i + 1 and expenditure sums capital + cash."""
    sites = pilot_sites()
    eligibility = eligibility_for(sites)
    policy = panda_policy(sites)
    rows = deployment.policy_cash_budget(sites, policy, eligibility, Parameters(), PathwaySpec(), (), years=3)
    assert [row["year"] for row in rows] == [1, 2, 3]
    assert rows[0]["capital"] > 0
    for row in rows:
        assert row["cash_running"] > 0
        assert row["cash_expenditure"] == pytest.approx(row["capital"] + row["cash_running"])


# --- portfolios_v7.regional_roster -------------------------------------------------


def test_regional_roster_roles_and_statuses_use_exact_names() -> None:
    """Lines 33, 44 and 46: exact equality drives role and status selection."""
    rows = {str(r["name"]): r for r in portfolios_v7.regional_roster()}
    assert rows["Cairns"]["role"] == "birth/referral"
    assert rows["Atherton"]["role"] == "birthing"
    assert rows["Tully"]["role"] == "readiness scenario"
    assert rows["Weipa"]["current_status"] == "birthing resumed May 2024"
    assert rows["Atherton"]["current_status"] == "current service directory"
    assert rows["Tully"]["current_status"] == "not asserted to have planned birthing"


# --- portfolios_v7.consultation_overrides ------------------------------------------


def consultation_inputs(*, calls: float = 12.5, uptake: float = 0.8) -> dict[str, np.ndarray]:
    """One-draw input bundle carrying the fields the override branch reads.

    Returns:
        One-draw arrays for the parameters the override branch reads.
    """
    return {
        "odds_ratio": np.array([1.0]),
        "calls_per_pilot_site": np.array([calls]),
        "state_uptake": np.array([uptake]),
        "birth_growth": np.array([1.0]),
    }


def test_consultation_guard_rejects_nonfinite_and_negative_activity() -> None:
    """Lines 104, 105 and 107: the nonnegative-finite guard uses OR and < 0."""
    sites = [Site("Tully", 50, 2022, "readiness", "regional")]
    inputs = consultation_inputs()
    for bad in (np.inf, -1.0, -0.5):
        with pytest.raises(ValueError, match="Nonnegative finite activity required"):
            _ = portfolios_v7.consultation_overrides(sites, inputs, readiness_calls=bad)
        with pytest.raises(ValueError, match="Nonnegative finite activity required"):
            _ = portfolios_v7.consultation_overrides(sites, inputs, cooktown_annual_births=bad)
    # Zero and small positive values are finite and non-negative: no rejection.
    assert portfolios_v7.consultation_overrides(sites, inputs, readiness_calls=0.0)
    assert portfolios_v7.consultation_overrides(sites, inputs, readiness_calls=0.5)
    assert portfolios_v7.consultation_overrides(sites, inputs, cooktown_annual_births=0.0)
    assert portfolios_v7.consultation_overrides(sites, inputs, cooktown_annual_births=0.5)


def test_consultation_defaults_are_strict_scenarios() -> None:
    """Lines 86 and 88: reopened and cairns_hub_only must default to False."""
    inputs = consultation_inputs()
    cairns = Site("Cairns", 100, 2022, "readiness", "regional")
    hub_default = portfolios_v7.consultation_overrides([cairns], inputs)
    assert hub_default["Cairns"][0] == pytest.approx(cast("float", _activity(cairns, inputs)[0]))
    # A readiness site outside the reopened set must not take the 32-birth path.
    weipa = Site("Weipa", 100, 2022, "readiness", "remote")
    base = portfolios_v7.consultation_overrides([weipa], inputs)
    assert base["Weipa"][0] == pytest.approx(cast("float", _activity(weipa, inputs)[0]))


def test_consultation_cairns_hub_branch_is_exact() -> None:
    """Lines 114 and 116: the hub guard is an AND and the exact Cairns name."""
    inputs = consultation_inputs()
    cairns = Site("Cairns", 100, 2022, "readiness", "regional")
    hub = portfolios_v7.consultation_overrides([cairns], inputs, cairns_hub_only=True)
    np.testing.assert_array_equal(hub["Cairns"], np.zeros(1))
    strict = portfolios_v7.consultation_overrides([cairns], inputs, cairns_hub_only=False)
    assert strict["Cairns"][0] == pytest.approx(cast("float", _activity(cairns, inputs)[0]))
    reopened = portfolios_v7.consultation_overrides([cairns], inputs, reopened=True)
    assert reopened["Cairns"][0] == pytest.approx(cast("float", _activity(cairns, inputs)[0]))


def test_consultation_reopened_births_formula() -> None:
    """Lines 117 and 118: Weipa uses 32 births, Cooktown the assumed count."""
    inputs = consultation_inputs(calls=12.5, uptake=0.8)
    weipa = Site("Weipa", 100, 2022, "readiness", "remote")
    cooktown = Site("Cooktown", 100, 2022, "readiness", "remote")
    out = portfolios_v7.consultation_overrides([weipa, cooktown], inputs, reopened=True, cooktown_annual_births=50.0)
    factor = 3 * 12.5 / 486
    assert out["Weipa"][0] == pytest.approx(32.0 * factor * 1.25 * 0.8)
    assert out["Cooktown"][0] == pytest.approx(50.0 * factor * 1.25 * 0.8)


def test_consultation_readiness_branch_is_exact() -> None:
    """Lines 119 and 120: readiness membership and the exact addition/product."""
    inputs = consultation_inputs(calls=25.0, uptake=0.8)
    tully = Site("Tully", 50, 2022, "readiness", "regional")
    out = portfolios_v7.consultation_overrides([tully], inputs, readiness_calls=5.0)
    expected = cast("float", _activity(tully, inputs)[0]) + 5.0 * (25.0 / 12.5)
    assert out["Tully"][0] == pytest.approx(expected)


# --- strategies.Strategy / STRATEGIES ---------------------------------------------


def test_strategy_records_are_frozen() -> None:
    """Line 19: the Strategy dataclass must remain frozen."""
    strategy = strategies.STRATEGIES[0]
    with pytest.raises(FrozenInstanceError):
        strategy.label = "x"  # pyright: ignore[reportAttributeAccessIssue]  # ty: ignore[invalid-assignment]


def test_documented_local_service_flags() -> None:
    """Lines 32, 39 and 48: the documented-service flags must keep their values."""
    flags = {s.key: s.documented_local_service for s in strategies.STRATEGIES}
    assert flags["telephone"] is True
    assert flags["panda"] is True
    assert flags["mobile"] is False
    assert flags["fixed"] is False
    assert flags["obsbot"] is False


# --- strategies.summarise ----------------------------------------------------------


def sum_draws(values: dict[str, list[float]]) -> dict[str, dict[str, np.ndarray]]:
    """Build the draw mapping summarise expects for one metric.

    Returns:
        Per-strategy one-draw arrays for each summarised metric.
    """
    return {
        key: {
            "net_saving": np.array(v, dtype=float),
            "programme_cost": np.array(v, dtype=float),
            "avoided_transfers": np.array(v, dtype=float),
        }
        for key, v in values.items()
    }


def test_summarise_accepts_single_draw() -> None:
    """Line 177: a one-draw matrix is finite and non-empty, so it must pass."""
    out = strategies.summarise(sum_draws({"panda": [1.0]}), eligible=("panda",))
    summary = cast("dict[str, dict[str, float]]", out["summary"])
    assert summary["panda"]["mean"] == pytest.approx(1.0)


def test_summarise_rejects_empty_draws() -> None:
    """Line 177: an empty draw matrix must be rejected."""
    with pytest.raises(ValueError, match="Finite non-empty draw matrix required"):
        _ = strategies.summarise(sum_draws({"panda": []}), eligible=("panda",))


def test_summarise_p_saving_is_strictly_positive() -> None:
    """Line 188: a zero draw is not a saving, so p_saving counts strict > 0."""
    out = strategies.summarise(sum_draws({"panda": [0.0, 1.0]}), eligible=("panda",))
    summary = cast("dict[str, dict[str, float]]", out["summary"])
    assert summary["panda"]["p_saving_vs_telephone"] == pytest.approx(0.5)


def test_summarise_pairwise_uses_forward_pairs_and_difference() -> None:
    """Lines 203 and 205: pairs start at j + 1 and compare a minus b."""
    draws = sum_draws({"panda": [5.0, 2.0], "mobile": [2.0, 2.0], "fixed": [1.0, 1.0]})
    out = strategies.summarise(draws, eligible=("panda", "mobile", "fixed"))
    pairs = cast("list[dict[str, object]]", out["pairwise"])
    assert len(pairs) == 3
    first = pairs[0]
    assert first["a"] == "panda"
    assert first["b"] == "mobile"
    assert first["mean_incremental_saving_a_vs_b"] == pytest.approx(1.5)


def test_summarise_p_a_more_saving_is_strictly_positive() -> None:
    """Line 211: p_a_more_saving counts strict > 0 on the paired difference."""
    draws = sum_draws({"panda": [0.0, 1.0], "mobile": [0.0, 0.0]})
    out = strategies.summarise(draws, eligible=("panda", "mobile"))
    pair = cast("list[dict[str, object]]", out["pairwise"])[0]
    assert pair["p_a_more_saving"] == pytest.approx(0.5)
    assert pair["mean_incremental_saving_a_vs_b"] == pytest.approx(0.5)


# --- deployment: policy catalogue, eligibility status and running-cost sum ----------


def test_validate_policy_requires_every_site_assigned() -> None:
    """Line 132: the scope guard keeps both OR checks."""
    sites = [Site("A", 10, 2022, "readiness", "regional"), Site("B", 10, 2022, "readiness", "regional")]
    eligibility = eligibility_for(sites)
    policy = deployment.DeploymentPolicy("n", (("A", "panda"),), conditional=True)
    with pytest.raises(ValueError, match="Policy must assign every site exactly once"):
        deployment.validate_policy(sites, policy, eligibility)


def test_validate_policy_rejects_ineligible_status() -> None:
    """Line 140: a present-but-ineligible record is still rejected via OR."""
    sites = [Site("Tully", 10, 2022, "readiness", "regional")]
    eligibility = deployment.eligibility_catalogue(sites)
    policy = deployment.DeploymentPolicy("n", (("Tully", "panda"),))
    with pytest.raises(ValueError, match="Policy eligibility not established"):
        deployment.validate_policy(sites, policy, eligibility)


def test_policy_catalogue_lists_distinct_policies_and_expands_conditionally() -> None:
    """Lines 162 and 172: six distinct policies, expansions conditional."""
    sites = [*pilot_sites(), Site("Tully", 10, 2022, "readiness", "regional")]
    policies = deployment.policy_catalogue(sites)
    assert len(policies) == 6
    expand = [p for p in policies if p.name.startswith("retain_pilot_expand")]
    assert len(expand) == 4
    assert all(p.conditional for p in expand)
    tully = [Site("Tully", 10, 2022, "readiness", "regional")]
    tully_policies = {p.name: p for p in deployment.policy_catalogue(tully)}
    eligibility = eligibility_for(tully)
    for name in ("retain_pilot_expand_panda", "retain_pilot_expand_obsbot"):
        deployment.validate_policy(tully, tully_policies[name], eligibility)


def test_evaluate_policies_running_cost_is_the_sum_of_components() -> None:
    """Line 254: cash_running_cost adds local ready, workflow and hub cash."""
    sites = pilot_sites()
    eligibility = eligibility_for(sites)
    policy = panda_policy(sites)
    calls = {s.name: np.array([300.0]) for s in sites}
    row = deployment.evaluate_policies(
        sites, (policy,), eligibility, Parameters(), PathwaySpec(), (), site_calls=calls
    )[policy.name]
    assert row["local_ready_cost"][0] > 0
    assert row["local_workflow_cost"][0] > 0
    assert row["hub_cash_cost"][0] > 0
    assert row["cash_running_cost"][0] == pytest.approx(
        cast("float", row["local_ready_cost"][0])
        + cast("float", row["local_workflow_cost"][0])
        + cast("float", row["hub_cash_cost"][0])
    )


def test_evaluate_policy_default_applies_retention() -> None:
    """Line 270: evaluate_policy retain defaults to True."""
    sites = pilot_sites()
    eligibility = eligibility_for(sites)
    policy = panda_policy(sites)
    assets = (OwnedAsset("Atherton", "panda", 5),)
    gross_row = deployment.evaluate_policy(
        sites, policy, eligibility, Parameters(), PathwaySpec(), assets, retain=False
    )
    kept_row = deployment.evaluate_policy(sites, policy, eligibility, Parameters(), PathwaySpec(), assets)
    gross = cast("float", gross_row["incremental_purchase_capital"][0])
    kept = cast("float", kept_row["incremental_purchase_capital"][0])
    assert kept == pytest.approx(gross * 2 / 3)


def test_cash_budget_default_applies_retention() -> None:
    """Line 303: policy_cash_budget retain defaults to True."""
    sites = pilot_sites()
    eligibility = eligibility_for(sites)
    policy = panda_policy(sites)
    assets = (OwnedAsset("Atherton", "panda", 5),)
    default = deployment.policy_cash_budget(sites, policy, eligibility, Parameters(), PathwaySpec(), assets, years=1)
    gross = deployment.policy_cash_budget(
        sites, policy, eligibility, Parameters(), PathwaySpec(), assets, retain=False, years=1
    )
    assert default[0]["capital"] == pytest.approx(20000.0)
    assert gross[0]["capital"] == pytest.approx(30000.0)


# --- portfolios_v7.portfolio -------------------------------------------------------


def test_portfolio_selection_and_composition() -> None:
    """Lines 70, 71 and 77: named portfolios return the expected site sets."""
    pilot = portfolios_v7.portfolio("pilot")
    assert pilot
    assert all(isinstance(s, Site) for s in pilot)
    assert len(portfolios_v7.portfolio("chhhs")) == 10
    assert len(portfolios_v7.portfolio("chhhs_tchhs")) == 14
    with pytest.raises(ValueError, match="Unknown portfolio"):
        _ = portfolios_v7.portfolio("bogus")


# --- strategies.compare_inputs / compare -------------------------------------------


PILOT = select_sites(load_sites(), "pilot")


def base_inputs(n: int = 1) -> dict[str, np.ndarray]:
    """Deterministic one-draw input bundle from the reference kernel.

    Returns:
        The reference kernel's base draw arrays for ``n`` draws.
    """
    return _base_arrays(Parameters(), n)


def test_compare_returns_every_strategy_and_zero_phone() -> None:
    """Lines 107, 117, 122, 131, 138, 143, 146 and 159."""
    result = strategies.compare(PILOT)
    assert set(result) == set(strategies.KEYS)
    assert result["telephone"]["programme_cost"] == 0
    assert result["telephone"]["net_saving"] == 0
    assert result["panda"]["full_purchase_capital"] == pytest.approx(30000.0)
    assert result["panda"]["attributed_capital"] == pytest.approx(30000.0)
    assert result["obsbot"]["full_purchase_capital"] == pytest.approx(13500.0)


def test_compare_rejects_duplicate_sites() -> None:
    """Line 110: repeated site names are rejected."""
    with pytest.raises(ValueError, match="Repeated sites would double count activity"):
        _ = strategies.compare([*PILOT, PILOT[0]])


@pytest.mark.parametrize("sunk", [("unknown",), ("panda", "panda"), ("telephone",)])
def test_compare_rejects_bad_sunk(sunk: tuple[str, ...]) -> None:
    """Line 113: sunk strategies must be known, distinct and video-only."""
    with pytest.raises(ValueError, match="Invalid sunk strategy list"):
        _ = strategies.compare(PILOT, sunk=sunk)


def test_compare_installed_cost_override_is_applied() -> None:
    """Lines 134 and 136: the installed cost override rewrites equipment cost."""
    result = strategies.compare(PILOT, overrides={"obsbot": {"installed_cost": 12345}})
    assert result["obsbot"]["full_purchase_capital"] == pytest.approx(12345.0 * len(PILOT))


def test_compare_sunk_strategy_excludes_capital() -> None:
    """Line 140: sunk strategies carry no annualised capital."""
    result = strategies.compare(PILOT, sunk=("panda",))
    assert result["panda"]["programme_cost"] == pytest.approx(result["panda"]["cash_running_cost"])


# --- strategies override validation ------------------------------------------------


def test_compare_rejects_telephone_or_unknown_override_key() -> None:
    """Line 71: overrides must name a known video strategy."""
    for name in ("telephone", "unknown"):
        with pytest.raises(ValueError, match="Overrides require a named video strategy"):
            _ = strategies.compare(PILOT, overrides={name: {"installed_cost": 5}})


@pytest.mark.parametrize("override", [{"bogus": 1}, {"reliability": True}], ids=["unknown-name", "boolean-value"])
def test_compare_rejects_unknown_name_or_boolean_value(override: dict[str, object]) -> None:
    """Line 75: unknown field names and boolean values are rejected."""
    with pytest.raises(ValueError, match="Invalid strategy override"):
        _ = strategies.compare(PILOT, overrides={"obsbot": override})


def test_compare_rejects_non_numeric_override() -> None:
    """Line 78: non-numeric override values raise TypeError."""
    with pytest.raises(TypeError):
        _ = strategies.compare(PILOT, overrides={"obsbot": {"reliability": "0.8"}})


@pytest.mark.parametrize("bad", [np.array([0.8, 0.9]), np.array([[0.8]]), np.array([True])])
def test_compare_rejects_wrong_shape_or_type(bad: np.ndarray) -> None:
    """Line 82: wrong length, wrong dimension and boolean arrays are rejected."""
    with pytest.raises(ValueError, match="Override draw array has wrong type or shape"):
        _ = strategies.compare(PILOT, overrides={"obsbot": {"reliability": bad}})


def test_compare_accepts_valid_override_draws() -> None:
    """Line 82: a correctly shaped numeric draw array is accepted."""
    result = strategies.compare_inputs(
        PILOT, Parameters(), base_inputs(1), overrides={"obsbot": {"reliability": np.array([0.8])}}
    )
    assert result["obsbot"]["avoided_transfers"].shape == (1,)


@pytest.mark.parametrize("good", [0.0, 1.0])
def test_compare_accepts_boundary_reliability(good: float) -> None:
    """Line 86: the allowed range is closed at both ends."""
    result = strategies.compare_inputs(PILOT, Parameters(), base_inputs(1), overrides={"obsbot": {"reliability": good}})
    assert result["obsbot"]["avoided_transfers"].shape == (1,)


@pytest.mark.parametrize("bad", [np.nan, np.inf, -0.1, 1.1])
def test_compare_rejects_nonfinite_or_out_of_range_reliability(bad: float) -> None:
    """Line 86: non-finite and out-of-range values are rejected."""
    with pytest.raises(ValueError, match="Override reliability outside allowed range"):
        _ = strategies.compare(PILOT, overrides={"obsbot": {"reliability": bad}})


# --- strategies.summarise guards and statistics ------------------------------------


def test_summarise_rejects_empty_eligible_set() -> None:
    """Line 173: an empty eligible set is rejected."""
    with pytest.raises(ValueError, match="Eligible set must contain unique known strategies"):
        _ = strategies.summarise(sum_draws({"panda": [1.0]}), eligible=())


def test_summarise_p_optimal_fractional_credit_sums_to_one() -> None:
    """Line 183: tied draws split credit, so p_optimal sums to one."""
    out = strategies.summarise(
        sum_draws({"panda": [3.0], "mobile": [3.0], "fixed": [3.0]}), eligible=("panda", "mobile", "fixed")
    )
    summary = cast("dict[str, dict[str, float]]", out["summary"])
    assert sum(summary[key]["p_optimal"] for key in summary) == pytest.approx(1.0)


def test_summarise_expected_regret_is_best_minus_value() -> None:
    """Line 196: expected regret subtracts the arm value from the best."""
    out = strategies.summarise(sum_draws({"panda": [5.0], "mobile": [2.0]}), eligible=("panda", "mobile"))
    summary = cast("dict[str, dict[str, float]]", out["summary"])
    assert summary["panda"]["expected_regret"] == pytest.approx(0.0)
    assert summary["mobile"]["expected_regret"] == pytest.approx(3.0)


def test_summarise_cost_only_evpi_is_best_minus_expected_choice() -> None:
    """Line 200: EVPI is the mean best value minus the best mean value."""
    out = strategies.summarise(sum_draws({"panda": [5.0, 1.0], "mobile": [2.0, 4.0]}), eligible=("panda", "mobile"))
    assert out["cost_only_evpi"] == pytest.approx(1.5)


# --- strategies.compare_psa --------------------------------------------------------


def test_compare_psa_defaults_and_envelope() -> None:
    """Lines 242 and 245: compare_psa defaults parameters and returns an envelope."""
    out = strategies.compare_psa(PILOT, n=8, seed=7)
    assert "summary" in out
    assert out["iterations"] == 8
    assert set(cast("dict[str, np.ndarray]", out["draws"])) == set(strategies.KEYS)
