"""Five complete service configurations using the existing exact cohort kernel.

All economic outcomes are incremental to telephone-supported care. Reference
video effects are identical by assumption, not demonstrated device equivalence.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from numbers import Real
from typing import Any

import numpy as np

from src.statewide import Parameters, Site, _base_arrays, _kernel, sample_inputs


@dataclass(frozen=True)
class Strategy:
    """A complete installed configuration, never a camera-only retail price."""

    key: str
    label: str
    installed_cost: float
    source: str
    documented_local_service: bool


STRATEGIES = (
    Strategy(
        "telephone", "Telephone advice", 0, "Common existing care; incremental zero", documented_local_service=True
    ),
    Strategy(
        "mobile",
        "Mobile teleconference",
        45000,
        "ELC 21 Oct 2026, printed p210; indicative",
        documented_local_service=False,
    ),
    Strategy(
        "panda",
        "Panda Vision",
        10000,
        "ELC printed p209-210 and user; invoices unverified",
        documented_local_service=True,
    ),
    Strategy("fixed", "Ceiling/wall PTZ", 47000, "ELC printed p210; indicative", documented_local_service=False),
    Strategy(
        "obsbot",
        "Tablet + OBSBOT kit",
        4500,
        "Analyst complete-kit assumption; no supplier quote",
        documented_local_service=False,
    ),
)
KEYS = tuple(s.key for s in STRATEGIES)
# Joint outcome matrices are draw-by-strategy.
_MATRIX_NDIM = 2
_OVERRIDE_RANGES = {
    "installed_cost": (0, np.inf),
    "capital_share": (0, 1),
    "reliability": (0, 1),
    "workflow_per_call": (0, np.inf),
    "life_years": (np.finfo(float).tiny, np.inf),
}


def _validate_overrides(overrides: dict[str, dict[str, Any]], n: int) -> None:
    for key, fields in overrides.items():
        if key not in KEYS or key == "telephone":
            msg = "Overrides require a named video strategy"
            raise ValueError(msg)
        for name, value in fields.items():
            if name not in _OVERRIDE_RANGES or isinstance(value, (bool, np.bool_)):
                msg = f"Invalid strategy override: {name}"
                raise ValueError(msg)
            if not isinstance(value, (Real, np.ndarray)):
                msg = "Override must be numeric scalar or draw array"
                raise TypeError(msg)
            a = np.asarray(value)
            if a.dtype.kind not in "iuf" or a.ndim > 1 or (a.ndim == 1 and a.shape != (n,)):
                msg = "Override draw array has wrong type or shape"
                raise ValueError(msg)
            low, high = _OVERRIDE_RANGES[name]
            if not np.all(np.isfinite(a)) or np.any(a < low) or np.any(a > high):
                msg = f"Override {name} outside allowed range"
                raise ValueError(msg)


def compare_inputs(
    sites: list[Site],
    parameters: Parameters,
    inputs: dict[str, np.ndarray],
    *,
    sunk: tuple[str, ...] = (),
    overrides: dict[str, dict[str, Any]] | None = None,
) -> dict[str, dict[str, np.ndarray]]:
    """Evaluate every strategy on the SAME draw, retaining systematic correlations.

    Returns:
        Per-strategy result dictionaries on the shared draws.

    Raises:
        ValueError: If sites, sunk strategies or overrides are invalid.
    """
    if not sites:
        msg = "At least one site is required"
        raise ValueError(msg)
    if len({s.name for s in sites}) != len(sites):
        msg = "Repeated sites would double count activity"
        raise ValueError(msg)
    if any(k not in KEYS[1:] for k in sunk) or len(set(sunk)) != len(sunk):
        msg = "Invalid sunk strategy list"
        raise ValueError(msg)
    n = len(inputs["odds_ratio"])
    overrides = overrides or {}
    _validate_overrides(overrides, n)
    result = {}
    reference = _kernel(sites, parameters, inputs)
    for strategy in STRATEGIES:
        if strategy.key == "telephone":
            result[strategy.key] = {name: np.zeros(n) for name in reference}
            result[strategy.key]["consultations"] = reference["consultations"].copy()
            for name in ("full_purchase_capital", "attributed_capital", "incremental_purchase_capital"):
                result[strategy.key][name] = np.zeros(n)
            continue
        # Each strategy shares the sampled procurement-cost multiplier. No fake
        # independent draws make expensive devices appear cheaper by chance.
        x = {name: value.copy() for name, value in inputs.items()}
        x["equipment_cost"] *= strategy.installed_cost / 10000
        fields = overrides.get(strategy.key, {})
        for name, value in fields.items():
            if name == "capital_share":
                continue
            target = "equipment_cost" if name == "installed_cost" else name
            x[target] = np.broadcast_to(np.asarray(value, dtype=float), (n,)).copy()
        purchase = x["equipment_cost"].copy() * len(sites)
        x["equipment_cost"] *= fields.get("capital_share", 1.0)
        p = replace(parameters, include_capital=parameters.include_capital and strategy.key not in sunk)
        out = _kernel(sites, p, x)
        out["full_purchase_capital"] = purchase
        out["attributed_capital"] = len(sites) * x["equipment_cost"]
        out["incremental_purchase_capital"] = np.zeros(n) if strategy.key in sunk else purchase.copy()
        result[strategy.key] = out
    return result


def compare(
    sites: list[Site],
    parameters: Parameters | None = None,
    *,
    sunk: tuple[str, ...] = (),
    overrides: dict[str, dict[str, Any]] | None = None,
) -> dict[str, dict[str, float]]:
    """Return exact deterministic annual incremental resource results."""
    p = parameters or Parameters()
    draws = compare_inputs(sites, p, _base_arrays(p, 1), sunk=sunk, overrides=overrides)
    return {key: {name: float(a[0]) for name, a in values.items()} for key, values in draws.items()}


def summarise(
    draws: dict[str, dict[str, np.ndarray]], *, eligible: tuple[str, ...] = KEYS, metric: str = "net_saving"
) -> dict[str, Any]:
    """Summarise joint choices; expected value, probability best and regret differ.

    Returns:
        Per-strategy summaries, pairwise comparisons and the cost-only EVPI.

    Raises:
        ValueError: If the eligible set or draw matrix is invalid.
    """
    if not eligible or len(set(eligible)) != len(eligible) or any(k not in KEYS for k in eligible):
        msg = "Eligible set must contain unique known strategies"
        raise ValueError(msg)
    matrix = np.column_stack([draws[k][metric] for k in eligible])
    if matrix.ndim != _MATRIX_NDIM or matrix.shape[0] < 1 or not np.all(np.isfinite(matrix)):
        msg = "Finite non-empty draw matrix required"
        raise ValueError(msg)
    best = matrix.max(axis=1)
    # Fractional credit avoids arm-order bias in genuinely tied decisions.
    tied = np.isclose(matrix, best[:, None], rtol=1e-12, atol=1e-8)
    shares = tied / tied.sum(axis=1, keepdims=True)
    summary = {}
    for j, k in enumerate(eligible):
        a = matrix[:, j]
        q = np.quantile(a, [0.025, 0.5, 0.975])
        prob = float(np.mean(a > 0))
        summary[k] = {
            "mean": float(a.mean()),
            "lower": float(q[0]),
            "median": float(q[1]),
            "upper": float(q[2]),
            "p_saving_vs_telephone": prob,
            "p_optimal": float(shares[:, j].mean()),
            "expected_regret": float((best - a).mean()),
            "mean_programme_cost": float(draws[k]["programme_cost"].mean()),
            "mean_avoided_transfers": float(draws[k]["avoided_transfers"].mean()),
        }
    evpi = float(best.mean() - np.max(matrix.mean(axis=0)))
    pairwise = []
    for j, a in enumerate(eligible):
        for z in range(j + 1, len(eligible)):
            b = eligible[z]
            d = matrix[:, j] - matrix[:, z]
            q = np.quantile(d, [0.025, 0.5, 0.975])
            pairwise.append({
                "a": a,
                "b": b,
                "mean_incremental_saving_a_vs_b": float(d.mean()),
                "p_a_more_saving": float(np.mean(d > 0)),
                "lower": float(q[0]),
                "upper": float(q[2]),
            })
    return {
        "summary": summary,
        "cost_only_evpi": max(0, evpi),
        "pairwise": pairwise,
        "eligible": list(eligible),
        "preferred_expected_value": eligible[int(np.argmax(matrix.mean(axis=0)))],
        "metric": metric,
        "interpretation": "Conditional resource-cost choice; no proven clinical-equivalence or procurement claim",
    }


def compare_psa(  # ruff: ignore[too-many-arguments] -- published PSA API
    sites: list[Site],
    n: int = 20000,
    seed: int = 20261028,
    parameters: Parameters | None = None,
    effect_mode: str = "attenuated",
    *,
    sunk: tuple[str, ...] = (),
    overrides: dict[str, dict[str, Any]] | None = None,
    eligible: tuple[str, ...] = KEYS,
) -> dict[str, Any]:
    """Joint PSA with paired rather than independently sampled comparators.

    Returns:
        The summarised PSA together with the draws and input arrays.
    """
    p = parameters or Parameters()
    x = sample_inputs(p, n=n, seed=seed, effect_mode=effect_mode)
    draws = compare_inputs(sites, p, x, sunk=sunk, overrides=overrides)
    return {
        **summarise(draws, eligible=eligible),
        "draws": draws,
        "inputs": x,
        "seed": seed,
        "iterations": n,
        "effect_mode": effect_mode,
    }
