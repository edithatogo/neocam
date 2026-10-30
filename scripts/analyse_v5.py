# ruff: ignore[implicit-namespace-package] -- scripts/ is a namespace package run via python -m
"""Paired five-strategy analysis; machine learning explains, never replaces, the exact model."""

from __future__ import annotations

import csv
import hashlib
import importlib
import importlib.metadata
import json
import operator
import os
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, TypedDict, cast

for env in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    _ = os.environ.setdefault(env, "1")
import numpy as np  # ruff: ignore[module-import-not-at-top-of-file] -- thread caps must be set before numpy loads

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.sensitivity import (  # ruff: ignore[module-import-not-at-top-of-file] -- import needs ROOT on sys.path
    NAMES,
    VARIABLES,
    decision_quality,
    evaluate_design,
    from_unit,
    k_way,
    one_way,
    two_way,
)
from src.statewide import (  # ruff: ignore[module-import-not-at-top-of-file] -- import needs ROOT on sys.path
    Parameters,
    Site,
    load_sites,
    sample_inputs,
    select_sites,
)
from src.strategies import (  # ruff: ignore[module-import-not-at-top-of-file] -- import needs ROOT on sys.path
    KEYS,
    compare,
    compare_inputs,
    compare_psa,
    summarise,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

    from numpy.typing import NDArray

OUT = ROOT / "outputs/v5"


def _cell(matrix: NDArray[np.float64], i: int, j: int | np.intp) -> float:
    """Return one scalar cell of a two-dimensional array."""
    return float(cast("float", matrix[i, j]))


def _row(matrix: NDArray[np.float64], i: int) -> NDArray[np.float64]:
    """Return one row of a two-dimensional array."""
    return cast("NDArray[np.float64]", matrix[i])


class _Importance(TypedDict):
    """One predictive-importance row; not a causal or EVPPI estimate."""

    parameter: str
    increase_in_mean_regret: float
    sd_across_permutations: float
    repeats: int
    scope: str


class _SummaryResult(TypedDict):
    """The document returned by :func:`src.strategies.summarise`."""

    summary: dict[str, dict[str, float]]
    pairwise: list[dict[str, object]]
    preferred_expected_value: str


class _PsaResult(TypedDict):
    """The document returned by :func:`src.strategies.compare_psa`."""

    summary: dict[str, dict[str, float]]
    pairwise: list[dict[str, object]]
    preferred_expected_value: str
    draws: dict[str, dict[str, NDArray[np.float64]]]
    inputs: dict[str, NDArray[np.float64]]
    without_proposed_obsbot: dict[str, object]
    societal: dict[str, object]


class _V4Results(TypedDict):
    """The retained historical v4 results read for the parity guard."""

    psa: dict[str, dict[str, float]]


class _Clusterer(Protocol):
    """Fitted clusterer surface used by the input-cluster analysis."""

    def fit(self, x: NDArray[np.float64]) -> _Clusterer: ...
    def predict(self, x: NDArray[np.float64]) -> NDArray[np.intp]: ...


class _Reducer(Protocol):
    """Fitted decomposition surface used for the two-component projection."""

    explained_variance_ratio_: NDArray[np.float64]

    def fit(self, x: NDArray[np.float64]) -> _Reducer: ...
    def transform(self, x: NDArray[np.float64]) -> NDArray[np.float64]: ...


class _Regressor(Protocol):
    """Fitted regressor surface used by the surrogate emulator."""

    def fit(self, x: NDArray[np.float64], y: NDArray[np.float64]) -> _Regressor: ...
    def predict(self, x: NDArray[np.float64]) -> NDArray[np.float64]: ...


class _Classifier(Protocol):
    """Fitted classifier surface used by the surrogate choice model."""

    def fit(self, x: NDArray[np.float64], y: NDArray[np.intp]) -> _Classifier: ...
    def predict(self, x: NDArray[np.float64]) -> NDArray[np.intp]: ...


class _Tree(Protocol):
    """Fitted decision-tree surface used for the shallow readable rules."""

    def fit(self, x: NDArray[np.float64], y: NDArray[np.intp]) -> _Tree: ...
    def predict(self, x: NDArray[np.float64]) -> NDArray[np.intp]: ...


class _SobolEngine(Protocol):
    """Untyped scipy Sobol engine, reduced to the one method used here."""

    def random_base2(self, m: int) -> NDArray[np.float64]: ...


class _SobolIndices(Protocol):
    """Untyped scipy Sobol' result, reduced to the arrays used here."""

    first_order: NDArray[np.float64]
    total_order: NDArray[np.float64]


class _QmcModule(Protocol):
    """Typed facade over the untyped ``scipy.stats.qmc`` module."""

    Sobol: Callable[..., _SobolEngine]


class _StatsModule(Protocol):
    """Typed facade over the untyped parts of ``scipy.stats``."""

    uniform: Callable[..., object]

    def sobol_indices(
        self,
        *,
        func: Callable[[NDArray[np.float64]], NDArray[np.float64]],
        n: int,
        dists: Sequence[object],
        rng: np.random.Generator,
    ) -> _SobolIndices: ...


class _ClusterModule(Protocol):
    """Typed facade over the untyped ``sklearn.cluster`` module."""

    KMeans: Callable[..., _Clusterer]


class _DecompositionModule(Protocol):
    """Typed facade over the untyped ``sklearn.decomposition`` module."""

    PCA: Callable[..., _Reducer]


class _EnsembleModule(Protocol):
    """Typed facade over the untyped ``sklearn.ensemble`` module."""

    ExtraTreesRegressor: Callable[..., _Regressor]
    HistGradientBoostingClassifier: Callable[..., _Classifier]


class _MetricsModule(Protocol):
    """Typed facade over the untyped ``sklearn.metrics`` module."""

    def adjusted_rand_score(self, labels_true: NDArray[np.intp], labels_pred: NDArray[np.intp]) -> float: ...
    def balanced_accuracy_score(self, y_true: NDArray[np.intp], y_pred: NDArray[np.intp]) -> float: ...

    def confusion_matrix(
        self, y_true: NDArray[np.intp], y_pred: NDArray[np.intp], *, labels: NDArray[np.int64]
    ) -> NDArray[np.int64]: ...

    def mean_absolute_error(
        self, y_true: NDArray[np.float64], y_pred: NDArray[np.float64], *, multioutput: str
    ) -> NDArray[np.float64]: ...

    def r2_score(
        self, y_true: NDArray[np.float64], y_pred: NDArray[np.float64], *, multioutput: str
    ) -> NDArray[np.float64]: ...

    def silhouette_score(
        self, x: NDArray[np.float64], labels: NDArray[np.intp], *, sample_size: int, random_state: int
    ) -> float: ...


class _TreeModule(Protocol):
    """Typed facade over the untyped ``sklearn.tree`` module."""

    DecisionTreeClassifier: Callable[..., _Tree]

    def export_text(self, decision_tree: _Tree, *, feature_names: Sequence[str]) -> str: ...


def _optional_module[T](_protocol: type[T], name: str) -> T:
    """Import an untyped optional dependency and present it as a typed facade.

    Returns:
        The imported module, presented as the requested facade type.
    """
    return cast("T", cast("object", importlib.import_module(name)))


def save_csv(name: str, rows: Sequence[Mapping[str, object]]) -> None:
    """Write one publication CSV table.

    Raises:
        ValueError: If there are no rows for the named table.
    """
    if not rows:
        msg = "Empty publication table"
        raise ValueError(msg)
    with (OUT / name).open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def write_manifest(directory: Path, root: Path = ROOT) -> None:
    """Write deterministic digests without a recursively changing self-digest."""
    manifest = {
        str(f.relative_to(root)): hashlib.sha256(f.read_bytes()).hexdigest()
        for f in sorted(directory.glob("*"))
        if f.is_file() and f.name != "analysis_manifest.json"
    }
    _ = (directory / "analysis_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


def main() -> None:  # ruff: ignore[complex-structure, too-many-branches, too-many-locals, too-many-statements] -- one linear reproducible analysis pipeline
    """Run the paired PSA, sensitivity, learning and parity analyses and write outputs.

    Raises:
        AssertionError: If the protected v4 Panda PSA parity check fails.
    """
    start = time.monotonic()
    OUT.mkdir(exist_ok=True, parents=True)
    sites = load_sites()
    pilot = select_sites(sites, "pilot")
    state = select_sites(sites, "spokes")
    p = Parameters()
    seed = 20261027
    n = 20000
    decisions: list[tuple[str, list[Site], tuple[str, ...], dict[str, dict[str, object]]]] = [
        ("pilot_new", pilot, (), {}),
        ("state_new", state, (), {}),
        ("pilot_retain_panda", pilot, ("panda",), {}),
        ("pilot_existing_mobile", pilot, ("mobile",), {}),
        ("pilot_existing_fixed", pilot, ("fixed",), {}),
        ("pilot_shared_mobile", pilot, (), {"mobile": {"capital_share": 0.1}}),
        ("pilot_shared_fixed", pilot, (), {"fixed": {"capital_share": 0.1}}),
        ("pilot_obsbot_7500", pilot, (), {"obsbot": {"installed_cost": 7500}}),
        ("pilot_obsbot_reliability80", pilot, (), {"obsbot": {"reliability": 0.8}}),
    ]
    deterministic: list[dict[str, object]] = []
    psa_results: dict[str, Mapping[str, object]] = {}
    psa_table: list[dict[str, object]] = []
    pairwise: list[dict[str, object]] = []
    savez = cast("Callable[..., None]", np.savez_compressed)
    for name, s, sunk, overrides in decisions:
        for key, values in compare(s, sunk=sunk, overrides=overrides).items():
            deterministic.append({"decision": name, "strategy": key, **values})
        r = cast("_PsaResult", cast("object", compare_psa(s, n=n, seed=seed, sunk=sunk, overrides=overrides)))
        r["without_proposed_obsbot"] = summarise(r["draws"], eligible=KEYS[:-1])
        r["societal"] = summarise(r["draws"], metric="societal_net_saving")
        psa_results[name] = {k: v for k, v in r.items() if k not in {"inputs", "draws"}}
        for key, v in r["summary"].items():
            psa_table.append({"decision": name, "effect": "attenuated", "strategy": key, **v})
        pairwise.extend({"decision": name, **row} for row in r["pairwise"])
        if name in {"pilot_new", "state_new", "pilot_retain_panda"}:
            savez(
                OUT / f"{name}_joint_draws.npz",
                **{f"{key}__{metric}": a for key, v in r["draws"].items() for metric, a in v.items()},
                **{f"input__{key}": a for key, a in r["inputs"].items()},
            )
        print("PSA", name, r["preferred_expected_value"], flush=True)  # ruff: ignore[print] -- CLI progress goes to stdout
    for portfolio, s in [("pilot", pilot), ("state", state)]:
        for mode in ["published", "null", "skeptical"]:
            r = cast("_PsaResult", cast("object", compare_psa(s, n=n, seed=seed, effect_mode=mode)))
            name = f"{portfolio}_{mode}"
            psa_results[name] = {k: v for k, v in r.items() if k not in {"inputs", "draws"}}
            for key, v in r["summary"].items():
                psa_table.append({"decision": name, "effect": mode, "strategy": key, **v})
    x = sample_inputs(p, n=n, seed=seed)
    relative = np.random.default_rng(seed + 1).triangular(0.65, 0.95, 1, n)
    d = compare_inputs(pilot, p, x, overrides={"obsbot": {"reliability": x["reliability"] * relative}})
    r = cast("_SummaryResult", cast("object", summarise(d)))
    psa_results["pilot_prototype_reliability_uncertain"] = r
    for key, v in r["summary"].items():
        psa_table.append({
            "decision": "pilot_prototype_reliability_uncertain",
            "effect": "attenuated",
            "strategy": key,
            **v,
        })
    # Separate structural sensitivity: prototype cost and delivery uncertainty.
    # These are analyst priors, not new supplier or patient observations.
    kit_cost = np.random.default_rng(seed + 2).triangular(2500, 4500, 10000, n) * x["equipment_cost"] / 10000
    for portfolio, s in [("pilot", pilot), ("state", state)]:
        name = f"{portfolio}_prototype_cost_and_reliability_uncertain"
        d = compare_inputs(
            s, p, x, overrides={"obsbot": {"installed_cost": kit_cost, "reliability": x["reliability"] * relative}}
        )
        r = cast("_SummaryResult", cast("object", summarise(d)))
        psa_results[name] = r
        for key, v in r["summary"].items():
            psa_table.append({"decision": name, "effect": "attenuated", "strategy": key, **v})
    save_csv("deterministic_strategies.csv", deterministic)
    save_csv("psa_strategy_summary.csv", psa_table)
    save_csv("pairwise_psa.csv", pairwise)
    precision: list[dict[str, object]] = []
    for repeat_seed in [41, 73, 101]:
        for portfolio, s in [("pilot", pilot), ("state", state)]:
            r = cast("_PsaResult", cast("object", compare_psa(s, n=n, seed=repeat_seed)))
            for key, v in r["summary"].items():
                precision.append({
                    "portfolio": portfolio,
                    "seed": repeat_seed,
                    "n": n,
                    "strategy": key,
                    "mean": v["mean"],
                    "p_optimal": v["p_optimal"],
                })
    save_csv("psa_seed_precision.csv", precision)
    ow: list[dict[str, object]] = []
    tw: list[dict[str, object]] = []
    pairs: list[tuple[str, str]] = [
        ("calls_per_site", "odds_ratio"),
        ("obsbot_installed_cost", "obsbot_reliability"),
        ("mobile_capital_share", "obsbot_reliability"),
        ("life_years", "marginal_fraction"),
    ]
    for portfolio, s in [("pilot", pilot), ("state", state)]:
        ow.extend({"portfolio": portfolio, **row} for row in one_way(s, points=21))
        for a, b in pairs:
            tw.extend(
                {
                    "portfolio": portfolio,
                    "x_parameter": a,
                    "y_parameter": b,
                    "x_value": row[a],
                    "y_value": row[b],
                    **{k: row[k] for k in KEYS},
                    "best": row["best"],
                    "runner_up": row["runner_up"],
                    "margin": row["margin"],
                    "design_kind": row["design_kind"],
                }
                for row in two_way(s, a, b, points=31)
            )
    save_csv("one_way.csv", ow)
    save_csv("two_way.csv", tw)
    qmc = _optional_module(_QmcModule, "scipy.stats.qmc")
    stats = _optional_module(_StatsModule, "scipy.stats")
    cluster = _optional_module(_ClusterModule, "sklearn.cluster")
    decomposition = _optional_module(_DecompositionModule, "sklearn.decomposition")
    ensemble = _optional_module(_EnsembleModule, "sklearn.ensemble")
    metrics = _optional_module(_MetricsModule, "sklearn.metrics")
    tree_mod = _optional_module(_TreeModule, "sklearn.tree")

    u_train = qmc.Sobol(len(NAMES), scramble=True, seed=501).random_base2(13)
    u_select = qmc.Sobol(len(NAMES), scramble=True, seed=502).random_base2(11)
    u_test = qmc.Sobol(len(NAMES), scramble=True, seed=504).random_base2(12)
    train = from_unit(u_train)
    select = from_unit(u_select)
    test = from_unit(u_test)
    y_train = evaluate_design(pilot, train)
    y_select = evaluate_design(pilot, select)
    y_test = evaluate_design(pilot, test)
    labels_train = np.argmax(y_train, axis=1)
    labels_test = np.argmax(y_test, axis=1)
    # Unsupervised means outcome-blind: preprocessing/clustering fit on train inputs only.
    centre = u_train.mean(axis=0)
    scale = u_train.std(axis=0)
    ztrain = (u_train - centre) / scale
    ztest = (u_test - centre) / scale
    km = cluster.KMeans(n_clusters=4, n_init=10, random_state=71).fit(ztrain)
    clusters = km.predict(ztest)
    silhouette = float(metrics.silhouette_score(ztest, clusters, sample_size=2000, random_state=72))
    aris: list[float] = []
    for cluster_seed in [79, 83]:
        alt = cluster.KMeans(n_clusters=4, n_init=10, random_state=cluster_seed).fit(ztrain)
        aris.append(float(metrics.adjusted_rand_score(clusters, alt.predict(ztest))))
    pca = decomposition.PCA(n_components=2).fit(ztrain)
    projection = pca.transform(ztest)
    save_csv(
        "input_clusters_projection.csv",
        [
            {
                "pc1": _cell(projection, i, 0),
                "pc2": _cell(projection, i, 1),
                "input_cluster": int(cast("int", clusters[i])),
                "exact_best": KEYS[int(cast("int", labels_test[i]))],
            }
            for i in range(len(test))
        ],
    )
    cr: list[dict[str, object]] = []
    for c in range(4):
        mask = cast("NDArray[np.bool_]", clusters == c)
        cr.append({
            "cluster": c,
            "n": int(mask.sum()),
            **{
                f"design_fraction_{key}": float(np.mean(cast("NDArray[np.bool_]", labels_test[mask] == j)))
                for j, key in enumerate(KEYS)
            },
            **{f"mean_{name}": float(test[mask, j].mean()) for j, name in enumerate(NAMES)},
        })
    save_csv("input_cluster_summary.csv", cr)
    print("INPUT CLUSTER SILHOUETTE", silhouette, "ARI", aris, flush=True)  # ruff: ignore[print] -- CLI progress goes to stdout
    print("FITTING REGRESSOR", time.monotonic() - start, flush=True)  # ruff: ignore[print] -- CLI progress goes to stdout
    forest = ensemble.ExtraTreesRegressor(
        n_estimators=192, min_samples_leaf=3, max_depth=24, n_jobs=2, random_state=81
    ).fit(u_train, y_train)
    print("FITTING CLASSIFIER", time.monotonic() - start, flush=True)  # ruff: ignore[print] -- CLI progress goes to stdout
    classifier = ensemble.HistGradientBoostingClassifier(
        max_iter=250,
        max_leaf_nodes=15,
        l2_regularization=1,
        learning_rate=0.08,
        random_state=102,
        early_stopping=True,
        validation_fraction=0.15,
    ).fit(u_train, labels_train)

    def decision_scores(x: NDArray[np.float64]) -> NDArray[np.float64]:
        chosen = classifier.predict(x)
        scores = np.zeros((len(x), len(KEYS)))
        scores[np.arange(len(x)), chosen] = 1
        return scores

    def importance(x: NDArray[np.float64], y: NDArray[np.float64], repeats: int, rng_seed: int) -> list[_Importance]:
        rng = np.random.default_rng(rng_seed)
        base = decision_quality(decision_scores(x), y)["mean_regret"]
        rows: list[_Importance] = []
        for j, name in enumerate(NAMES):
            impacts: list[float] = []
            for _ in range(repeats):
                perm = x.copy()
                perm[:, j] = perm[rng.permutation(len(x)), j]
                impacts.append(decision_quality(decision_scores(perm), y)["mean_regret"] - base)
            rows.append({
                "parameter": name,
                "increase_in_mean_regret": float(np.mean(impacts)),
                "sd_across_permutations": float(np.std(impacts, ddof=1)),
                "repeats": repeats,
                "scope": "predictive importance, not causal or EVPPI",
            })
        return sorted(rows, key=operator.itemgetter("increase_in_mean_regret"), reverse=True)

    print("SELECTION IMPORTANCE", time.monotonic() - start, flush=True)  # ruff: ignore[print] -- CLI progress goes to stdout
    selected_importance = importance(u_select, y_select, 4, 84)
    axes = [row["parameter"] for row in selected_importance[:5]]
    save_csv("selection_importance.csv", selected_importance)
    grid5 = k_way(pilot, axes, levels=5)
    save_csv("five_way_selected_grid.csv", grid5)
    grid4 = k_way(pilot, ["obsbot_installed_cost", "obsbot_reliability", "calls_per_site", "odds_ratio"], levels=7)
    save_csv("four_way_equipment_grid.csv", grid4)
    print("HELDOUT IMPORTANCE", time.monotonic() - start, flush=True)  # ruff: ignore[print] -- CLI progress goes to stdout
    save_csv("heldout_permutation_importance.csv", importance(u_test, y_test, 6, 85))
    pred = forest.predict(u_test)
    fm: dict[str, object] = dict(decision_quality(pred, y_test))
    fm.update({
        "balanced_accuracy": metrics.balanced_accuracy_score(labels_test, np.argmax(pred, axis=1)),
        "r2_by_arm": dict(
            zip(
                KEYS,
                cast("list[float]", metrics.r2_score(y_test, pred, multioutput="raw_values").tolist()),
                strict=True,
            )
        ),
        "mae_by_arm": dict(
            zip(
                KEYS,
                cast("list[float]", metrics.mean_absolute_error(y_test, pred, multioutput="raw_values").tolist()),
                strict=True,
            )
        ),
        "confusion_matrix": metrics.confusion_matrix(
            labels_test, np.argmax(pred, axis=1), labels=np.arange(5)
        ).tolist(),
    })
    classified = decision_scores(u_test)
    cm: dict[str, object] = dict(decision_quality(classified, y_test))
    cm["balanced_accuracy"] = metrics.balanced_accuracy_score(labels_test, np.argmax(classified, axis=1))
    cm["confusion_matrix"] = metrics.confusion_matrix(
        labels_test, np.argmax(classified, axis=1), labels=np.arange(5)
    ).tolist()
    tree = tree_mod.DecisionTreeClassifier(max_depth=5, min_samples_leaf=80, random_state=86).fit(train, labels_train)
    tree_choice = tree.predict(test)
    tree_pred = np.zeros_like(y_test)
    tree_pred[np.arange(len(y_test)), tree_choice] = 1
    tm: dict[str, object] = dict(decision_quality(tree_pred, y_test))
    tm["balanced_accuracy"] = metrics.balanced_accuracy_score(labels_test, tree_choice)
    tm["confusion_matrix"] = metrics.confusion_matrix(labels_test, tree_choice, labels=np.arange(5)).tolist()
    _ = (OUT / "shallow_decision_rules.txt").write_text(
        tree_mod.export_text(tree, feature_names=[v.label for v in VARIABLES])
        + "\nClass mapping: "
        + str(dict(enumerate(KEYS)))
        + "\nSynthetic design explanation only; exact model remains authoritative.\n"
    )
    save_csv(
        "heldout_predictions.csv",
        [
            {
                "design_id": i,
                "exact_best": KEYS[int(cast("int", labels_test[i]))],
                "forest_choice": KEYS[int(np.argmax(_row(pred, i)))],
                "classifier_choice": KEYS[int(np.argmax(_row(classified, i)))],
                "tree_choice": KEYS[int(cast("int", tree_choice[i]))],
                "forest_regret": float(_row(y_test, i).max() - _cell(y_test, i, np.argmax(_row(pred, i)))),
                "tree_regret": float(_row(y_test, i).max() - _cell(y_test, i, int(cast("int", tree_choice[i])))),
                "classifier_regret": float(_row(y_test, i).max() - _cell(y_test, i, np.argmax(_row(classified, i)))),
                **{name: _cell(test, i, j) for j, name in enumerate(NAMES)},
            }
            for i in range(len(test))
        ],
    )
    print("HELDOUT_CLASSIFIER", cm, "SELECTED", axes, flush=True)  # ruff: ignore[print] -- CLI progress goes to stdout
    # Independent uniform design, explicitly NOT a Sobol decomposition of correlated PSA.

    def response(u: NDArray[np.float64]) -> NDArray[np.float64]:
        exact = evaluate_design(pilot, from_unit(u.T))
        return np.column_stack((exact[:, 1:], exact[:, 2] - exact[:, 4], exact.max(axis=1))).T

    response_names = ["mobile_net", "panda_net", "fixed_net", "obsbot_net", "panda_minus_obsbot", "best_attainable_net"]
    sr: list[dict[str, object]] = []
    for m, sd in [(11, 91), (12, 92)]:
        res = stats.sobol_indices(
            func=response, n=cast("int", 2**m), dists=[stats.uniform() for _ in NAMES], rng=np.random.default_rng(sd)
        )
        for k, outcome in enumerate(response_names):
            for j, name in enumerate(NAMES):
                sr.append({
                    "n_base": 2**m,
                    "seed": sd,
                    "outcome": outcome,
                    "parameter": name,
                    "first_order": _cell(res.first_order, k, j),
                    "total_order": _cell(res.total_order, k, j),
                    "interaction_gap": _cell(res.total_order, k, j) - _cell(res.first_order, k, j),
                    "scope": "Independent uniform design ranges; not PSA prior decomposition",
                })
    save_csv("sobol_indices.csv", sr)
    save_csv(
        "global_heldout_design.csv",
        [
            {
                "design_id": i,
                **{name: _cell(test, i, j) for j, name in enumerate(NAMES)},
                **{key: _cell(y_test, i, j) for j, key in enumerate(KEYS)},
                "best": KEYS[int(cast("int", labels_test[i]))],
            }
            for i in range(len(test))
        ],
    )
    learning: dict[str, object] = {
        "n_train": 8192,
        "n_selection": 2048,
        "n_independent_test": 4096,
        "design_seeds": [501, 502, 504],
        "retired_diagnostic_holdout": 503,
        "clustering": "Input-only train-fitted KMeans; all clusters retained; no clinical subgroup claim",
        "silhouette": silhouette,
        "seed_stability_ari": aris,
        "pca_variance_explained": pca.explained_variance_ratio_.tolist(),
        "forest": fm,
        "classifier": cm,
        "shallow_tree": tm,
        "selected_kway_axes": axes,
        "independent_design_samples": 14336,
        "kway_points": len(grid5),
        "fourway_points": len(grid4),
        "interpretation": "Emulator agreement with this assumed exact model, not clinical validation",
    }
    old = cast("_V4Results", json.loads((ROOT / "outputs/v4/results_v2.json").read_text()))
    parity: dict[str, bool] = {}
    for portfolio, key in [("pilot", "pilot_new"), ("spokes", "state_new")]:
        actual = cast("Mapping[str, dict[str, float]]", psa_results[key]["summary"])["panda"]
        previous = old["psa"][portfolio + "_attenuated"]
        # Pre-existing v5 tolerance (HEAD had rtol=1e-12, atol=1e-7) preserved verbatim:
        # this guard records v4 result parity as the v5 track defined it. Tightening it to
        # exact equality, or loosening it further, would both change recorded behaviour.
        parity[portfolio] = all(
            np.isclose(actual[k], previous[k], rtol=1e-12, atol=1e-7) for k in ["mean", "median", "lower", "upper"]
        )
    if not all(parity.values()):
        msg = "Original Panda PSA changed"
        raise AssertionError(msg)
    output: dict[str, object] = {
        "version": "5.0.0-preliminary",
        "date": "2026-10-28",
        "protected_v4_result_parity": parity,
        "psa": psa_results,
        "learning": learning,
        "deterministic_count": len(deterministic),
        "one_way_rows": len(ow),
        "two_way_grid_points": len(tw),
        "psa_primary_structures": len(psa_results),
        "psa_iterations_each": n,
        "seed_precision_runs": 6,
        "sobol_evaluations": (2048 + 4096) * (len(NAMES) + 2),
        "scientific_runtime": {k: importlib.metadata.version(k) for k in ["numpy", "scipy", "scikit-learn"]},
        "elapsed_seconds": time.monotonic() - start,
        "qualification": (
            "Researcher-prior analysis; prototype unvalidated; deterministic design fractions are not probabilities"
        ),
    }
    _ = (OUT / "results_v5.json").write_text(json.dumps(output, indent=2) + "\n")
    write_manifest(OUT)
    print("COMPLETED", output["elapsed_seconds"], flush=True)  # ruff: ignore[print] -- CLI completion notice goes to stdout


if __name__ == "__main__":
    main()
