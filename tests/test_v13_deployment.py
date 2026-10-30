"""Site eligibility, shared hub accounting and mixed deployment decisions."""

from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, cast

import numpy as np
import pytest

from src import audit_v7, deployment
from src.activity import ActivitySpec
from src.configuration import load_configuration
from src.equipment import OwnedAsset
from src.pathways_v6 import PathwaySpec, compare_v6
from src.portfolios_v7 import portfolio
from src.statewide import Parameters, Site

if TYPE_CHECKING:
    from collections.abc import Callable

# src signatures use bare containers; these aliases restate the shapes the tests assert.
Draws = tuple[dict[str, np.ndarray], dict[str, np.ndarray]]
evaluate_policy = cast("Callable[..., dict[str, np.ndarray]]", deployment.evaluate_policy)
_compare_v6 = cast("Callable[..., dict[str, dict[str, np.ndarray]]]", compare_v6)
evaluate_policies = cast("Callable[..., dict[str, dict[str, np.ndarray]]]", deployment.evaluate_policies)
policy_cash_budget = cast("Callable[..., list[dict[str, float]]]", deployment.policy_cash_budget)
sample_v7 = cast("Callable[..., Draws]", audit_v7.sample_v7)


def env(sites: list[Site] | None = None, strategy: str = "panda", *, conditional: bool = True):
    sites = sites or portfolio("pilot")
    records = deployment.eligibility_catalogue(sites, allow_hypothetical=conditional)
    p = deployment.DeploymentPolicy("test", tuple((s.name, strategy) for s in sites), conditional)
    return sites, records, p


def test_reported_current_operation_not_approval_everywhere() -> None:
    s, e, p = env(portfolio("chhhs"), conditional=False)
    with pytest.raises(ValueError, match="eligib"):
        deployment.validate_policy(s, p, e)
    keep = deployment.policy_catalogue(s)[1]
    deployment.validate_policy(s, keep, e)
    assert dict(keep.assignments)["Atherton"] == "panda"
    assert dict(keep.assignments)["Cairns"] == "telephone"


def test_kit_is_conditional_not_strict_eligible() -> None:
    s, e, p = env(strategy="obsbot")
    deployment.validate_policy(s, p, e)
    with pytest.raises(ValueError, match="eligibility not established"):
        deployment.validate_policy(s, replace(p, conditional=False), e)


@pytest.mark.parametrize(
    "assignments", [(), (("Atherton", "panda"),), (("Atherton", "panda"),) * 3, (("invented", "panda"),)]
)
def test_bad_assignment_scope(assignments: tuple[object, ...]) -> None:
    s, e, p = env()
    with pytest.raises(ValueError, match="assign"):
        deployment.validate_policy(s, replace(p, assignments=assignments), e)


def test_unknown_and_duplicate_eligibility() -> None:
    s, e, p = env()
    with pytest.raises(ValueError, match="Duplicate eligibility"):
        deployment.validate_policy(s, p, (*e, e[0]))
    with pytest.raises(ValueError, match="Invalid eligibility record"):
        _ = deployment.Eligibility("Atherton", "obsbot", "approved", "unverified")


def test_uniform_policy_is_exact_reference_without_retention() -> None:
    s, e, p = env()
    result = evaluate_policy(s, p, e, Parameters(), PathwaySpec(), (), retain=False)
    ref = compare_v6(s)["panda"]
    for k in ref:
        np.testing.assert_allclose(result[k], ref[k], atol=1e-7)


def test_mixed_clinical_mass_and_retained_capital() -> None:
    s, e, p = env(portfolio("chhhs"))
    assets = load_configuration(Path.cwd()).owned_assets
    p = deployment.policy_catalogue(s)[3]  # retain Panda + new kit
    r = evaluate_policy(s, p, e, Parameters(), PathwaySpec(), assets)
    assert r["incremental_purchase_capital"][0] == 7 * 4500
    assert r["contacts"][0] >= r["episodes"][0]
    eventual = float(cast("float", r["eventual_transfers"][0]))
    local = float(cast("float", r["final_local"][0]))
    assert eventual + local == pytest.approx(cast("float", r["episodes"][0]))
    table = policy_cash_budget(s, p, e, Parameters(), PathwaySpec(), assets)
    assert table[0]["capital"] == 7 * 4500
    assert table[2]["capital"] == 30000
    assert table[5]["capital"] == 7 * 4500


def test_hub_capacity_not_summed_per_group_or_site() -> None:
    sites = [Site("S1", 0, 2022, "readiness", "regional"), Site("S2", 0, 2022, "readiness", "regional")]
    s, e, p = env(sites)
    p = replace(p, assignments=(("S1", "panda"), ("S2", "obsbot")))
    calls = {"S1": np.array([300.0]), "S2": np.array([300.0])}
    result = evaluate_policy(s, p, e, Parameters(), PathwaySpec(), (), site_calls=calls)
    assert result["hub_hours"][0] == 150
    assert result["hub_cash_cost"][0] == 40000
    assert result["hub_capacity_blocks"][0] == 1
    assert result["cash_running_cost"][0] == pytest.approx(
        cast("float", result["local_ready_cost"][0]) + cast("float", result["local_workflow_cost"][0]) + 40000
    )
    budget = policy_cash_budget(s, p, e, Parameters(), PathwaySpec(), (), site_calls=calls)
    assert budget[0]["hub_cash_capacity"] == 40000


def test_single_contact_vs_repeated_clinical_cases() -> None:
    s, e, p = env()
    r = evaluate_policy(s, p, e, Parameters(), PathwaySpec(), (), activity=ActivitySpec("contacts", 2))
    assert r["episodes"][0] == pytest.approx(18.75)
    assert r["contacts"][0] == pytest.approx(37.5)
    assert r["hub_hours"][0] == pytest.approx(9.375)


def test_shared_draws_and_input_immutability() -> None:
    s, e, p = env()
    x, z = sample_v7(n=128, seed=99)
    original = {k: v.copy() for k, v in x.items()}
    r = evaluate_policy(s, p, e, Parameters(), PathwaySpec(), (), inputs=x, structural_draws=z, retain=False)
    direct = compare_v6(s, inputs=x, structural_draws=z)["panda"]
    for k in r:
        np.testing.assert_allclose(r[k], direct[k], atol=1e-7)
    for k in x:
        np.testing.assert_array_equal(x[k], original[k])


def test_more_transfers_remain_signed_not_clipped() -> None:
    s, e, p = env()
    r = evaluate_policy(s, p, e, Parameters(odds_ratio=1.4), PathwaySpec(), ())
    assert r["avoided_transfers"][0] < 0
    assert r["net_saving"][0] < 0


def test_null_policy_phone_and_expired_assets() -> None:
    s, e, p = env(strategy="telephone")
    r = evaluate_policy(s, p, e, Parameters(), PathwaySpec(), ())
    assert r["programme_cost"][0] == 0
    assert r["net_saving"][0] == 0
    p = replace(p, assignments=tuple((site.name, "panda") for site in s))
    expired = (OwnedAsset("Atherton", "panda", 0),)
    r = evaluate_policy(s, p, e, Parameters(), PathwaySpec(), expired)
    assert r["incremental_purchase_capital"][0] == 30000


def test_policy_scope_and_life_validation() -> None:
    s, e, p = env()
    with pytest.raises(ValueError, match="Budget years"):
        _ = policy_cash_budget(s, p, e, Parameters(), PathwaySpec(), (), years=True)
    with pytest.raises(ValueError, match="Retention must be boolean"):
        _ = evaluate_policy(s, p, e, Parameters(), PathwaySpec(), (), retain="false")


def test_multiple_policies_reuse_only_identical_ephemeral_groups(monkeypatch: pytest.MonkeyPatch) -> None:
    s, e, _p = env(portfolio("chhhs"))
    policies = deployment.policy_catalogue(s)
    seen: list[tuple[str, ...]] = []

    def recorded(sites: list[Site], *args: object, **kwargs: object) -> dict[str, dict[str, np.ndarray]]:
        seen.append(tuple(site.name for site in sites))
        # Transparent forwarding double: the wrapped kernel revalidates every argument.
        return _compare_v6(sites, *args, **kwargs)

    monkeypatch.setattr(deployment, "compare_v6", recorded)
    result = evaluate_policies(s, policies, e, Parameters(), PathwaySpec(), ())
    assert len(result) == 6
    assert len(seen) == len(set(seen)) == 3
    # No persisted cache: a new call with new parameters must evaluate afresh.
    changed = evaluate_policies(s, policies, e, Parameters(odds_ratio=1), PathwaySpec(), ())
    assert len(seen) == 6
    assert (
        changed["retain_pilot_expand_obsbot"]["net_saving"][0] != result["retain_pilot_expand_obsbot"]["net_saving"][0]
    )


def test_policy_results_do_not_share_mutable_arrays() -> None:
    s, e, _p = env(portfolio("chhhs"))
    result = evaluate_policies(s, deployment.policy_catalogue(s), e, Parameters(), PathwaySpec(), ())
    first = result["retain_pilot_only"]["episodes"]
    second = result["telephone"]["episodes"]
    assert not np.shares_memory(first, second)
