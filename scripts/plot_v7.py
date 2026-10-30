# ruff: ignore[implicit-namespace-package] -- standalone figure script, not a package module
"""Separate figures from the exact v7 tables; no custom colour or global style."""

import csv
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "outputs/v7"
FIG = OUT / "figures"
FIG.mkdir(exist_ok=True)


def read(name: str) -> list[dict[str, str]]:
    """Read a v7 CSV output table as a list of string-valued records.

    Returns:
        One dictionary per CSV row, keyed by header.
    """
    with (OUT / name).open(newline="") as f:
        return list(csv.DictReader(f))


P = read("psa_perspectives.csv")
V = read("value_of_perspective.csv")
A = read("allocation_two_way.csv")
H = read("health_thresholds.csv")
U = read("utility_bridge_scenarios.csv")
S = read("structural_scenarios.csv")
N = {
    "pilot": "Three-site pilot",
    "chhhs": "CHHHS: 10 locations",
    "chhhs_tchhs": "CHHHS + TCHHS: 14",
    "spokes": "Illustrative state: 33",
}
K = ["telephone", "mobile", "panda", "fixed", "obsbot"]
L = ["Telephone", "Mobile unit", "Panda Vision", "Fixed PTZ", "Tablet / OBSBOT"]
PN = ["health_system", "societal_bounded", "provider_chhhs", "patient_family", "state", "commonwealth"]
PL = ["Health system", "Health + family", "CHHHS provider", "Patient / family", "State allocation", "Commonwealth"]
WTP_PER_QALY = 50000
DURATION_YEARS = 5
DISCOUNT_RATE = 0.05


def finish(name: str, title: str, note: str) -> None:
    """Title, annotate and save the current figure to PNG and SVG."""
    ax = plt.gca()
    ax.set_title(title, pad=15)
    plt.figtext(0.02, 0.015, note, ha="left", fontsize=9, wrap=True)
    plt.tight_layout(rect=(0, 0.09, 1, 1))
    for ext in ("png", "svg"):
        plt.savefig(FIG / f"{name}.{ext}", dpi=180, bbox_inches="tight")
    plt.close()


def get(net: str, scenario: str, view: str, k: str) -> dict[str, str]:
    """Return the single perspective row matching portfolio, scenario, view and strategy."""
    return next(
        r
        for r in P
        if r["portfolio"] == net and r["scenario"] == scenario and r["perspective"] == view and r["strategy"] == k
    )


plt.figure(figsize=(9, 4.9))
for i, net in enumerate(["pilot", "chhhs", "chhhs_tchhs"]):
    r = get(net, "reference", "health_system", "panda")
    m, lo, hi = [float(r[x]) / 1000 for x in ("mean", "lower", "upper")]
    plt.errorbar(m, i, xerr=[[m - lo], [hi - m]], fmt="o", capsize=5)
plt.yticks(range(3), [N[n] for n in ["pilot", "chhhs", "chhhs_tchhs"]])
plt.axvline(0, linestyle="--")
plt.xlabel("Annual net resource saving (AUD thousands)")
finish(
    "01_regional_uncertainty",
    "Panda Vision versus telephone: regional uncertainty",
    "Mean and 95% researcher-prior interval; 20,000 paired draws. No observed saving or mortality benefit is claimed.",
)
plt.figure(figsize=(10, 5.2))
x = np.arange(5)
width = 0.18
for j, view in enumerate(PN[:4]):
    vals = [float(get("chhhs_tchhs", "prototype_uncertain", view, k)["mean"]) / 1000 for k in K]
    plt.bar(x + (j - 1.5) * width, vals, width, label=PL[j])
plt.xticks(x, L)
plt.axhline(0, linestyle="--")
plt.ylabel("Expected annual net value (AUD thousands)")
plt.legend(fontsize=9)
finish(
    "02_perspective_comparison",
    "Different evaluative perspectives, same clinical draws",
    "Combined regional scenario; prototype performance/cost uncertain. Provider resources precede unverified revenue effects; family scope is limited.",  # ruff: ignore[line-too-long] -- authored report text kept verbatim
)
indices = [0, 1, 2, 4]
vp = [PN[i] for i in indices]
vl = [PL[i] for i in indices]
plt.figure(figsize=(8, 5.8))
matrix = np.zeros((4, 4))
for i, p in enumerate(vp):
    for j, q in enumerate(vp):
        matrix[i, j] = (
            float(
                next(
                    r
                    for r in V
                    if r["portfolio"] == "chhhs_tchhs"
                    and r["scenario"] == "provider_local_only"
                    and r["choose_under"] == p
                    and r["evaluate_under"] == q
                )["value"]
            )
            / 1000
        )
plt.imshow(matrix, aspect="auto")
plt.xticks(range(4), vl, rotation=30, ha="right")
plt.yticks(range(4), vl)
plt.ylabel("Choose under")
plt.xlabel("Evaluate under")
plt.colorbar(label="Directional expected regret (AUD thousands/year)")
finish(
    "03_value_of_perspective",
    "Value of perspective: a cost-allocation stress test",
    "Current-information fixed choices, not perfect information. Patient and Commonwealth tie cases and bounds remain in the full tables.",  # ruff: ignore[line-too-long] -- authored report text kept verbatim
)
# Exact deterministic accounting sensitivity, not a new clinical model fit.
plt.figure(figsize=(9, 5))
from scripts.analyse_v7 import evaluate_perspectives  # ruff: ignore[module-import-not-at-top-of-file] -- deferred so plotting setup runs first
from src.pathways_v6 import PathwaySpec  # ruff: ignore[module-import-not-at-top-of-file] -- import requires ROOT on sys.path
from src.portfolios_v7 import portfolio  # ruff: ignore[module-import-not-at-top-of-file] -- import requires ROOT on sys.path
from src.statewide import Parameters, _base_arrays  # ruff: ignore[module-import-not-at-top-of-file, import-private-name] -- import requires ROOT on sys.path; internal helper used deliberately

p = Parameters()
s = PathwaySpec()
xx = np.linspace(0, 1, 11)
for key, label in zip(K, L, strict=True):
    vals = []
    for a in xx:
        _, ledger, _ = evaluate_perspectives(
            portfolio("chhhs_tchhs"), p, s, _base_arrays(p, 1), {}, receiver_share=float(a), retrieval_chhhs_share=0
        )
        vals.append(-float(ledger[key]["provider_chhhs"][0]) / 1000)
    plt.plot(xx, vals, marker="o", label=label)
plt.axhline(0, linestyle="--")
plt.xlabel("Share of regional receiving-hospital resource change allocated to CHHHS")
plt.ylabel("Provider annual net resource value (AUD thousands)")
plt.legend(fontsize=9)
finish(
    "04_provider_allocation",
    "Who bears receiving care changes the provider decision",
    "Retrieval savings allocated outside CHHHS in this stress test. Shares are assumptions, not measured routes or contractual payments.",  # ruff: ignore[line-too-long] -- authored report text kept verbatim
)
plt.figure(figsize=(9, 5))
subsidies = np.linspace(0, 1, 11)
for view, label in [
    ("state", "State allocation"),
    ("patient_family", "Patient / family"),
    ("societal_bounded", "Health + family total"),
]:
    vals = []
    for z in subsidies:
        _, ledger, _ = evaluate_perspectives(
            portfolio("chhhs_tchhs"), p, s, _base_arrays(p, 1), {}, subsidy_fraction=float(z)
        )
        vals.append(-float(ledger["panda"][view][0]) / 1000)
    plt.plot(subsidies, vals, marker="o", label=label)
plt.xlabel("Hypothetical subsidy fraction of family travel component")
plt.ylabel("Annual net value (AUD thousands)")
plt.legend()
finish(
    "05_subsidy_reconciliation",
    "A subsidy reallocates burden; it does not create resources",
    "Deterministic combined network; Commonwealth funding response fixed. Financial flows are not actual PTSS eligibility or cash predictions.",  # ruff: ignore[line-too-long] -- authored report text kept verbatim
)
plt.figure(figsize=(9, 4.7))
nets = list(N)
vals = [
    float(
        next(
            r
            for r in H
            if r["portfolio"] == n and r["strategy"] == "panda" and float(r["scenario_value_per_qaly"]) == WTP_PER_QALY  # ruff: ignore[float-equality-comparison] -- published selection must not change
        )["required_qaly_days_per_consultation"]
    )
    for n in nets
]
plt.barh([N[n] for n in nets], vals)
plt.xlim(0, max(vals) * 1.15)
plt.xlabel("Required additional quality-adjusted days per consultation")
for i, v in enumerate(vals):
    plt.text(v + 0.035, i, f"{v:.2f}", va="center")
finish(
    "06_health_threshold",
    "Health gain required when no transfers are avoided",
    "Hypothetical AUD50,000/QALY valuation; no official threshold or estimated video benefit. Includes the annual programme cost, not future survivor care.",  # ruff: ignore[line-too-long] -- authored report text kept verbatim
)
plt.figure(figsize=(9, 4.8))
for u in (0.13, 0.28):
    r = [
        z
        for z in U
        if float(z["utility_difference"]) == u  # ruff: ignore[float-equality-comparison] -- published selection must not change
        and int(z["duration_years_assumed"]) == DURATION_YEARS
        and float(z["discount_rate"]) == DISCOUNT_RATE  # ruff: ignore[float-equality-comparison] -- published selection must not change
    ]
    plt.plot(
        [float(z["fraction_consultations_improved_assumed"]) * 100 for z in r],
        [float(z["qalys_per_1000_consultations"]) for z in r],
        marker="o",
        label=f"Utility difference {u:.2f}",
    )
plt.xlabel("Assumed fraction with improved health state (%)")
plt.ylabel("Illustrative QALYs per 1,000 consultations")
plt.legend()
finish(
    "07_utility_bridge",
    "Alternative utility instruments give different illustrative gains",
    "EPICure2 age-11 contrasts; five assumed years from age 11, discounted from birth at 5%. Video is not shown to prevent prematurity or produce this improvement.",  # ruff: ignore[line-too-long] -- authored report text kept verbatim
)
plt.figure(figsize=(9, 5))
nets = ["pilot", "chhhs", "chhhs_tchhs"]
x = np.arange(3)
for j, scenario in enumerate(["reference", "reopened", "readiness_1_call"]):
    vals = [
        float(
            next(r for r in S if r["portfolio"] == n and r["scenario"] == scenario and r["strategy"] == "panda")[
                "mean_consultations"
            ]
        )
        for n in nets
    ]
    plt.bar(x + (j - 1) * 0.23, vals, 0.23, label=scenario.replace("_", " "))
plt.xticks(x, [N[n] for n in nets])
plt.ylabel("Expected consultation episodes/year")
plt.legend()
finish(
    "08_activity_scenarios",
    "Historical exposure is not current operational demand",
    "Reopened scenario uses Weipa32 births in2025 and assumed Cooktown50/year. Readiness calls are hypothetical additional incidents, not observed activity.",  # ruff: ignore[line-too-long] -- authored report text kept verbatim
)
print("Created 8 separate PNG/SVG figures.")  # ruff: ignore[print] -- script status line goes to stdout
