"""Contracts for perspective accounting and fixed-decision regret."""

from typing import TYPE_CHECKING, TypedDict, cast

import numpy as np
import pytest

from src import perspectives_v7

if TYPE_CHECKING:
    from collections.abc import Callable


class Regret(TypedDict):
    """Fixed-decision regret record returned by the kernel."""

    value: float
    choose_indices: list[int]
    target_indices: list[int]


# The published helpers declare bare dicts; restate the asserted shapes.
perspective_regret = cast("Callable[..., Regret]", perspectives_v7.perspective_regret)
reconcile_ledger = cast("Callable[..., dict[str, np.ndarray]]", perspectives_v7.reconcile_ledger)


def test_vop_uses_fixed_expected_decision_not_oracle() -> None:
    # A wins expected under p; B wins expected under q. Fixed regret=1, oracle=5.
    p = np.array([[9.0, 0.0], [1.0, 0.0]])
    q = np.array([[0.0, 10.0], [8.0, 0.0]])
    r = perspective_regret(p, q)
    assert r["value"] == pytest.approx(1.0)
    assert r["choose_indices"] == [0]
    assert r["target_indices"] == [1]


def test_vop_diagonal_and_ties() -> None:
    a = np.array([[1.0, 1.0], [3.0, 3.0]])
    assert perspective_regret(a, a)["value"] == pytest.approx(0.0)
    assert np.allclose(perspectives_v7.optimal_probabilities(a), [0.5, 0.5])


def test_ledger_subsidy_does_not_change_societal_resources() -> None:
    c = {
        "health_cost": np.array([100.0]),
        "family_gross": np.array([40.0]),
        "family_subsidy": np.array([20.0]),
        "commonwealth": np.array([30.0]),
        "provider_cost": np.array([70.0]),
    }
    a = reconcile_ledger(**c)
    assert a["societal"] == pytest.approx([140.0])
    assert a["patient_family"] == pytest.approx([20.0])
    assert a["state"] == pytest.approx([90.0])
    assert a["state"] + a["commonwealth"] + a["patient_family"] == pytest.approx(a["societal"])
    c["family_subsidy"] = np.array([0.0])
    b = reconcile_ledger(**c)
    assert np.array_equal(a["societal"], b["societal"])


def test_ledger_signed_incremental_costs_reconcile() -> None:
    a = reconcile_ledger(
        health_cost=np.array([-100.0, 0.0]),
        family_gross=np.array([-40.0, 0.0]),
        family_subsidy=np.array([-20.0, 0.0]),
        commonwealth=np.array([-30.0, 0.0]),
        provider_cost=np.array([10.0, 0.0]),
    )
    assert np.allclose(a["state"] + a["commonwealth"] + a["patient_family"], a["societal"])
    assert np.allclose(a["provider_chhhs"], [10, 0])


@pytest.mark.parametrize(
    ("a", "b", "message"),
    [
        (np.array([1]), np.array([1]), "Require finite draw by strategy matrix"),
        (np.ones((2, 2)), np.ones((3, 2)), "Paired perspectives must have equal shapes"),
        (np.array([[np.nan]]), np.array([[0.0]]), "Require finite draw by strategy matrix"),
    ],
)
def test_vop_rejects_invalid(a: np.ndarray, b: np.ndarray, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        _ = perspective_regret(a, b)
