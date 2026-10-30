"""Exact deterministic sensitivity surfaces: design frequencies are not probabilities."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product

import numpy as np

from src.statewide import Parameters, Site, _base_arrays
from src.strategies import KEYS, compare_inputs


@dataclass(frozen=True)
class Variable:
    """A prespecified sensitivity coordinate, not an empirically fitted distribution."""

    name: str
    label: str
    low: float
    high: float
    reference: float
    rationale: str


VARIABLES = (
    Variable(
        "odds_ratio",
        "Video transfer odds ratio",
        0.35,
        1.3,
        float(np.sqrt(0.48)),
        "Common clinical-effect uncertainty, including no effect/increased transfer",
    ),
    Variable(
        "calls_per_site",
        "Calls per pilot site/year",
        5,
        25,
        12.5,
        "Wider deterministic utilisation stress test than 10-15 forecast",
    ),
    Variable(
        "marginal_fraction", "Avoidable retrieval fraction", 0.1, 1, 0.5, "Resource fraction, not full reported tariff"
    ),
    Variable(
        "downstream_delta",
        "Hospital cost difference, AUD",
        -4000,
        10000,
        2000,
        "Additional local care may exceed receiving-hospital offset",
    ),
    Variable("life_years", "Equipment life, years", 3, 7, 5, "Existing equipment-life range"),
    Variable(
        "critical_share",
        "Critical case share",
        0.05,
        0.40,
        0.15,
        "Critical transfer unchanged; low/moderate remainder shares preserved",
    ),
    Variable(
        "common_reliability",
        "Established-video usable connection",
        0.8,
        1,
        0.95,
        "Technical delivery assumption, not comparative clinical efficacy",
    ),
    Variable("workflow_per_call", "Extra video workflow, AUD/call", 0, 175, 75, "Increment above telephone workload"),
    Variable(
        "obsbot_installed_cost",
        "Complete OBSBOT kit, AUD/site",
        2500,
        10000,
        4500,
        "Unquoted complete-system range; includes tablet/mount/integration",
    ),
    Variable(
        "obsbot_reliability",
        "Tablet/OBSBOT usable connection",
        0.7,
        1,
        0.95,
        "Hypothetical alternative; not measured quality",
    ),
    Variable(
        "mobile_capital_share",
        "Mobile neonatal capital attribution",
        0.05,
        1,
        1,
        "Cross-use allocation only; does not reduce full procurement cash",
    ),
    Variable(
        "fixed_capital_share",
        "Fixed PTZ neonatal capital attribution",
        0.05,
        1,
        1,
        "Cross-use allocation only; may be infeasible at some sites",
    ),
)
NAMES = tuple(v.name for v in VARIABLES)
# Sensitivity designs are draw-by-coordinate matrices.
_MATRIX_NDIM = 2
# Guard bounds for a one-dimensional grid resolution.
_MIN_GRID_POINTS = 2
_MAX_GRID_POINTS = 101
# Guard bound for a full Cartesian design.
_MAX_CARTESIAN_POINTS = 100000
# Decision-quality near-optimality tolerances, in outcome units (AUD).
_NEAR_OPTIMAL_ABS_100 = 100
_NEAR_OPTIMAL_ABS_1000 = 1000


def reference_design() -> np.ndarray:
    """Return the deterministic reference point in named coordinate order."""
    return np.array([v.reference for v in VARIABLES])


def from_unit(unit: np.ndarray) -> np.ndarray:
    """Map independent unit design coordinates to prespecified ranges.

    Returns:
        The design mapped to the prespecified coordinate ranges.

    Raises:
        ValueError: If the unit design is not finite, two-dimensional and in [0,1].
    """
    u = np.asarray(unit, dtype=float)
    if (
        u.ndim != _MATRIX_NDIM
        or u.shape[1] != len(VARIABLES)
        or not np.all(np.isfinite(u))
        or np.any((u < 0) | (u > 1))
    ):
        msg = "Expected a finite n-by-d design within [0,1]"
        raise ValueError(msg)
    low = np.array([v.low for v in VARIABLES])
    high = np.array([v.high for v in VARIABLES])
    return low + u * (high - low)


def evaluate_design(
    sites: list[Site], design: np.ndarray, *, sunk: tuple[str, ...] = (), metric: str = "net_saving"
) -> np.ndarray:
    """Evaluate exact five-arm outcomes for a bounded multivariable design.

    Returns:
        The five-arm outcome matrix for each design row and strategy.

    Raises:
        ValueError: If the design or the requested outcome metric is invalid.
    """
    d = np.asarray(design, dtype=float)
    if d.ndim != _MATRIX_NDIM or d.shape[0] < 1 or d.shape[1] != len(VARIABLES) or not np.all(np.isfinite(d)):
        msg = "Expected finite n-by-d nonempty design"
        raise ValueError(msg)
    low = np.array([v.low for v in VARIABLES])
    high = np.array([v.high for v in VARIABLES])
    if np.any(d < low - 1e-10) or np.any(d > high + 1e-10):
        msg = "Outside prespecified deterministic range"
        raise ValueError(msg)
    if metric not in {"net_saving", "societal_net_saving", "programme_cost", "avoided_transfers"}:
        msg = "Unsupported sensitivity outcome"
        raise ValueError(msg)
    p = Parameters()
    x = _base_arrays(p, len(d))
    v = {name: d[:, i] for i, name in enumerate(NAMES)}
    mapping = {
        "odds_ratio": "odds_ratio",
        "calls_per_site": "calls_per_pilot_site",
        "marginal_fraction": "marginal_fraction",
        "downstream_delta": "downstream_delta",
        "life_years": "life_years",
        "common_reliability": "reliability",
        "workflow_per_call": "workflow_per_call",
    }
    for name, target in mapping.items():
        x[target] = v[name].copy()
    remainder = 1 - v["critical_share"]
    x["case_mix"] = np.column_stack((remainder * 7 / 17, remainder * 10 / 17, v["critical_share"]))
    overrides = {
        "obsbot": {"installed_cost": v["obsbot_installed_cost"], "reliability": v["obsbot_reliability"]},
        "mobile": {"capital_share": v["mobile_capital_share"]},
        "fixed": {"capital_share": v["fixed_capital_share"]},
    }
    out = compare_inputs(sites, p, x, sunk=sunk, overrides=overrides)
    return np.column_stack([out[k][metric] for k in KEYS])


def _check_points(points: int) -> None:
    if type(points) is not int or not _MIN_GRID_POINTS <= points <= _MAX_GRID_POINTS:
        msg = "Grid resolution must be an integer between 2 and 101"
        raise ValueError(msg)


def one_way(sites: list[Site], points: int = 21, *, sunk: tuple[str, ...] = ()) -> list[dict]:
    """Full curves around a fixed reference; not jointly sampled priors.

    Returns:
        One row per parameter, grid point and strategy.
    """
    _check_points(points)
    rows = []
    for j, var in enumerate(VARIABLES):
        d = np.tile(reference_design(), (points, 1))
        d[:, j] = np.linspace(var.low, var.high, points)
        y = evaluate_design(sites, d, sunk=sunk)
        for i, values in enumerate(y):
            best = KEYS[int(np.argmax(values))]
            for z, key in enumerate(KEYS):
                rows.append({
                    "parameter": var.name,
                    "value": float(d[i, j]),
                    "strategy": key,
                    "net_saving": float(values[z]),
                    "best": best,
                })
    return rows


def _design_rows(design: np.ndarray, outcome: np.ndarray, axes: list[str], kind: str) -> list[dict]:
    rows = []
    for i, values in enumerate(outcome):
        order = np.argsort(values)
        rows.append({
            **{name: float(design[i, NAMES.index(name)]) for name in axes},
            **{key: float(values[j]) for j, key in enumerate(KEYS)},
            "best": KEYS[int(order[-1])],
            "runner_up": KEYS[int(order[-2])],
            "margin": float(values[order[-1]] - values[order[-2]]),
            "design_kind": kind,
        })
    return rows


def two_way(sites: list[Site], x_name: str, y_name: str, points: int = 31, *, sunk: tuple[str, ...] = ()) -> list[dict]:
    """Evaluate all pairs on a complete named two-dimensional grid.

    Returns:
        One row per grid point with the best and runner-up strategies.

    Raises:
        ValueError: If the two coordinate names are not distinct and known.
    """
    _check_points(points)
    if x_name == y_name or x_name not in NAMES or y_name not in NAMES:
        msg = "Two distinct known coordinates required"
        raise ValueError(msg)
    a, b = [NAMES.index(name) for name in (x_name, y_name)]
    va, vb = VARIABLES[a], VARIABLES[b]
    d = np.tile(reference_design(), (points**2, 1))
    d[:, [a, b]] = np.array(list(product(np.linspace(va.low, va.high, points), np.linspace(vb.low, vb.high, points))))
    return _design_rows(d, evaluate_design(sites, d, sunk=sunk), [x_name, y_name], "deterministic_grid_not_probability")


def k_way(sites: list[Site], axes: list[str], levels: int = 5, *, sunk: tuple[str, ...] = ()) -> list[dict]:
    """Exact bounded Cartesian design in selected high-value dimensions.

    Returns:
        One row per Cartesian grid point with the best and runner-up strategies.

    Raises:
        ValueError: If axes are unknown or the grid exceeds the point guardrail.
    """
    _check_points(levels)
    if not axes or len(set(axes)) != len(axes) or any(name not in NAMES for name in axes):
        msg = "Unique known coordinates required"
        raise ValueError(msg)
    if levels ** len(axes) > _MAX_CARTESIAN_POINTS:
        msg = "Cartesian grid exceeds 100000-point guardrail"
        raise ValueError(msg)
    indexes = [NAMES.index(name) for name in axes]
    d = np.tile(reference_design(), (levels ** len(axes), 1))
    d[:, indexes] = np.array(
        list(product(*[np.linspace(VARIABLES[i].low, VARIABLES[i].high, levels) for i in indexes]))
    )
    return _design_rows(d, evaluate_design(sites, d, sunk=sunk), axes, "deterministic_cartesian_not_probability")


def decision_quality(predicted: np.ndarray, truth: np.ndarray) -> dict[str, float]:
    """Evaluate surrogate choices against exact outcomes, including decision regret.

    Returns:
        Accuracy, mean and tail regret against the exact outcomes.

    Raises:
        ValueError: If the aligned prediction and outcome matrices are invalid.
    """
    p = np.asarray(predicted, dtype=float)
    t = np.asarray(truth, dtype=float)
    misaligned = p.ndim != _MATRIX_NDIM or p.shape != t.shape or len(p) < 1 or p.shape[1] != len(KEYS)
    if misaligned or not np.all(np.isfinite(p)) or not np.all(np.isfinite(t)):
        msg = "Aligned finite n-by-five prediction and exact outcomes required"
        raise ValueError(msg)
    choice = np.argmax(p, axis=1)
    actual = np.argmax(t, axis=1)
    regret = t.max(axis=1) - t[np.arange(len(t)), choice]
    return {
        "accuracy": float(np.mean(choice == actual)),
        "mean_regret": float(regret.mean()),
        "max_regret": float(regret.max()),
        "regret_95th": float(np.quantile(regret, 0.95)),
        "near_optimal_100": float(np.mean(regret <= _NEAR_OPTIMAL_ABS_100)),
        "near_optimal_1000": float(np.mean(regret <= _NEAR_OPTIMAL_ABS_1000)),
    }
