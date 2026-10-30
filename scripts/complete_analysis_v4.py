# ruff: ignore[implicit-namespace-package] -- scripts/ is a namespace package run via python -m
"""Complete diagnostics and figures from unchanged economic inputs and verified draws."""

import csv
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

import matplotlib as mpl
import numpy as np
from matplotlib.figure import Figure

mpl.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from quality.analysis_checks import audit_outputs, prefix_diagnostics  # ruff: ignore[module-import-not-at-top-of-file] -- import requires ROOT on sys.path
from src.statewide import Parameters, evaluate, load_sites, psa, select_sites  # ruff: ignore[module-import-not-at-top-of-file] -- import requires ROOT on sys.path

OUT = ROOT / "outputs/v4"
FIG = OUT / "figures"
FIG.mkdir(exist_ok=True)
r = json.loads((OUT / "results_v2.json").read_text())
p = Parameters(**json.loads((ROOT / "data/parameters.json").read_text()))


def read(name: str) -> list[dict[str, str]]:
    """Read one output CSV directory as a list of row mappings.

    Returns:
        The parsed rows, keyed by header name.
    """
    with (OUT / name).open(newline="") as f:
        return list(csv.DictReader(f))


def save(name: str, rows: list[dict[str, Any]]) -> None:
    """Write rows to one output CSV, using the first row's keys as the header."""
    with (OUT / name).open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def finish(fig: Figure, name: str, note: str | None = None) -> None:
    """Save a figure as PNG and SVG with an optional caption, then close it."""
    if note:
        fig.text(0.02, 0.012, note, fontsize=8)
        fig.tight_layout(rect=(0, 0.06, 1, 1))
    else:
        fig.tight_layout()
    fig.savefig(FIG / f"{name}.png", dpi=170)
    fig.savefig(FIG / f"{name}.svg")
    plt.close(fig)


diagnostics = []
seeds = []
life = []
thresholds = []
for portfolio, title in [("pilot", "Three-site pilot"), ("spokes", "Illustrative 33-site network")]:
    sites = select_sites(load_sites(), portfolio)
    arr = np.genfromtxt(OUT / f"{portfolio}_attenuated_draws.csv", delimiter=",", names=True)
    vals = arr["net_saving"]
    diagnostics.extend({"portfolio": portfolio, **row} for row in prefix_diagnostics(vals, (2000, 5000, 10000, 20000)))
    for seed in (20261028, 20261029, 20261030):
        v = psa(sites, n=20000, seed=seed, parameters=p)["summary"]
        seeds.append({
            "portfolio": portfolio,
            "seed": seed,
            "draws": 20000,
            "p_saving": v["probability_cost_saving"],
            "mean_net_saving": v["mean"],
        })
    life.extend(
        {
            "portfolio": portfolio,
            "equipment_life_years": years,
            **evaluate(sites, replace(p, life_years=years)),
        }
        for years in (3, 5, 7)
    )
    for calls in (10, 12.5, 15):
        for fraction in (0.25, 0.5, 1):
            q = replace(p, calls_per_pilot_site=calls, marginal_fraction=fraction)
            low, high = 0.01, 1.0
            if evaluate(sites, replace(q, odds_ratio=low))["net_saving"] < 0:
                cutoff = None
            else:
                for _ in range(55):
                    mid = (low + high) / 2
                    if evaluate(sites, replace(q, odds_ratio=mid))["net_saving"] > 0:
                        low = mid
                    else:
                        high = mid
                cutoff = (low + high) / 2
            thresholds.append({
                "portfolio": portfolio,
                "calls_per_pilot_site": calls,
                "avoidable_fraction": fraction,
                "break_even_transfer_odds_ratio": cutoff,
                "interpretation": "Conditional threshold; other parameters fixed; not a treatment recommendation",
            })
    fig, ax = plt.subplots(figsize=(8.6, 4.7))
    ax.hist(vals / 1000, bins=110)
    ax.axvline(0, ls="--", lw=1)
    ax.set_xlim(np.quantile(vals, 0.005) / 1000, np.quantile(vals, 0.995) / 1000)
    ax.set(
        title=f"{title}: annual cost uncertainty",
        xlabel="Net resource saving (AUD thousands)",
        ylabel="Simulation draws",
    )
    finish(
        fig,
        f"{portfolio}_psa",
        "20,000 prior-based simulations; not observed savings. Display excludes outer 0.5% tails each side.",
    )
    dd = [x for x in diagnostics if x["portfolio"] == portfolio]
    fig, ax = plt.subplots(figsize=(8.6, 4.5))
    ax.errorbar(
        [x["draws"] for x in dd],
        [100 * x["p_saving"] for x in dd],
        yerr=[196 * x["mcse_probability"] for x in dd],
        fmt="o-",
        capsize=4,
    )
    ax.set(title=f"{title}: Monte Carlo precision", xlabel="Nested draws", ylabel="Probability of cost saving (%)")
    finish(
        fig,
        f"{portfolio}_mc_precision",
        "Error bars: ±1.96 Monte Carlo SE, not clinical uncertainty. Prefixes overlap; independent seeds are "
        "tabulated.",
    )
    ds = read(f"{portfolio}_five_year_budget.csv")
    fig, ax = plt.subplots(figsize=(8.6, 4.5))
    ax.plot([int(x["year"]) for x in ds], [float(x["cash_expenditure"]) / 1000 for x in ds], marker="o")
    ax.set(
        title=f"{title}: implementation cash expenditure", xlabel="Year", ylabel="Programme expenditure (AUD thousands)"
    )
    finish(
        fig,
        f"{portfolio}_budget",
        "Budget expenditure is separate from economic annualisation and modelled resource offsets.",
    )

save("mc_precision.csv", diagnostics)
save("independent_seed_checks.csv", seeds)
save("equipment_life_checks.csv", life)
save("break_even_thresholds.csv", thresholds)
sc = read("scenario_results.csv")
for portfolio, title in [("pilot", "Three-site pilot"), ("spokes", "Illustrative 33-site network")]:
    names = [
        "Base attenuated effect",
        "No incremental video effect",
        "Published OR without attenuation",
        "Increased transfers OR1.1",
        "25% avoidable retrieval resources",
        "Full allocated retrieval value",
        "No downstream hospital savings",
        "More local hospital cost",
        "Critical casemix50%",
        "Continuation: exclude sunk equipment",
        "Commercial cart45000",
    ]
    rows = [next(x for x in sc if x["portfolio"] == portfolio and x["scenario"] == name) for name in names]
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh([x["scenario"] for x in rows][::-1], [float(x["net_saving"]) / 1000 for x in rows][::-1])
    ax.axvline(0, ls="--")
    ax.set(title=f"{title}: structural scenarios", xlabel="Net resource saving (AUD thousands)")
    finish(
        fig,
        f"{portfolio}_scenarios",
        "One-way comparisons; full 58-row table is included. These are conditional model outputs.",
    )

fig, ax = plt.subplots(figsize=(8.6, 4.7))
for portfolio in ("pilot", "spokes"):
    modes = ["published", "attenuated", "skeptical", "null"]
    ax.plot(
        modes,
        [r["psa"][f"{portfolio}_{m}"]["probability_cost_saving"] * 100 for m in modes],
        marker="o",
        label=portfolio,
    )
ax.set(
    ylim=(0, 100), title="Effect assumptions drive the cost-saving conclusion", ylabel="Probability of cost saving (%)"
)
ax.legend()
finish(
    fig,
    "effect_structures",
    "Different structural priors are not independent clinical replications; no mortality effect in primary analysis.",
)

fig, ax = plt.subplots(figsize=(8.6, 4.7))
for fraction in (0.25, 0.5, 1):
    rr = [x for x in thresholds if x["portfolio"] == "pilot" and x["avoidable_fraction"] == fraction]
    ax.plot(
        [x["calls_per_pilot_site"] for x in rr],
        [x["break_even_transfer_odds_ratio"] for x in rr],
        marker="o",
        label=f"{fraction:.0%} avoidable",
    )
ax.set(
    title="Pilot: clinical effect needed to break even",
    xlabel="Annual consultations per pilot site",
    ylabel="Break-even transfer odds ratio",
)
ax.legend()
finish(
    fig,
    "break_even",
    "At these fixed assumptions, an odds ratio below the curve is cost saving. This is not a causal estimate.",
)

fig, ax = plt.subplots(figsize=(8.6, 4.7))
fr = read("survival_morbidity_frontier.csv")
for major in (0.1, 0.35, 0.7):
    rr = [
        x
        for x in fr
        if float(x["major_share"]) == major and float(x["discount"]) == 0.03 and float(x["wtp"]) == 50000  # ruff: ignore[float-equality-comparison, magic-value-comparison] -- exact match against literals written by this model; a tolerance would change the selected rows
    ]
    ax.plot(
        [100 * float(x["survival_gain"]) for x in rr],
        [float(x["total_nmb_including_acute_base"]) / 1000 for x in rr],
        marker="o",
        label=f"{major:.0%} major morbidity",
    )
ax.axhline(0, ls="--")
ax.set(
    title="Exploratory survival\u2013morbidity frontier",
    xlabel="Assumed absolute survival gain (percentage points)",
    ylabel="Net monetary benefit (AUD thousands)",
)
ax.legend()
finish(
    fig,
    "survival_frontier",
    "Illustrative $50,000/QALY, 3% discount, 40-year horizon; assumptions, NOT a calibrated lifetime CEA.",
)

fig, ax = plt.subplots(figsize=(8.6, 4.7))
for portfolio in ("pilot", "spokes"):
    rr = [x for x in life if x["portfolio"] == portfolio]
    ax.plot(
        [x["equipment_life_years"] for x in rr],
        [x["net_saving"] / x["site_count"] for x in rr],
        marker="o",
        label=portfolio,
    )
ax.axhline(0, ls="--")
ax.set(
    title="Equipment-life sensitivity",
    xlabel="Useful equipment life (years)",
    ylabel="Annual net resource saving per site (AUD)",
)
ax.legend()
finish(fig, "equipment_life", "Existing parameter tested at 3/5/7 years; no new clinical assumption introduced.")

fund = read("funding_sensitivity.csv")
grid = np.array([float(x["hypothetical_queensland_benchmark"]) for x in fund]).reshape(3, 3)
fig, ax = plt.subplots(figsize=(7, 4))
ax.axis("off")
table = ax.table(
    cellText=[[f"${v:,.0f}" for v in row] for row in grid],
    rowLabels=["QWAU/NWAU 0.9", "QWAU/NWAU 1.0", "QWAU/NWAU 1.1"],
    colLabels=["QEP/NEP 0.9", "QEP/NEP 1.0", "QEP/NEP 1.1"],
    cellLoc="center",
    loc="center",
    bbox=[0.20, 0.16, 0.79, 0.65],
)
table.auto_set_font_size(False)  # ruff: ignore[boolean-positional-value-in-call] -- matplotlib API takes the flag positionally
table.set_fontsize(11)
ax.set_title("Hypothetical Queensland funding sensitivity")
finish(
    fig,
    "funding_grid",
    "Reference: 1 NWAU \u00d7 $7,418 NEP26. Neither QEP nor local QWAU is verified. NOT a payment schedule.",
)

audit = audit_outputs()
(ROOT / "verification/v4/analysis_audit.json").write_text(json.dumps(audit, indent=2) + "\n")
(OUT / "release_metadata.json").write_text(
    json.dumps(
        {
            "artifact_release": "v4",
            "model": "unchanged v2/v3 economic specification",
            "as_of": "2026-10-28",
            "primary_deterministic_scenarios": 58,
            "psa_structures": 8,
            "draws_per_structure": 20000,
            "additional_precision_draws": 120000,
            "clinical_frontier_combinations": 108,
            "equipment_life_checks": 6,
            "break_even_thresholds": 18,
            "figures": len(list(FIG.glob("*.png"))),
            "parameters_added": 0,
            "analysis_audit": audit,
        },
        indent=2,
    )
    + "\n"
)
print(json.dumps(audit, indent=2))  # ruff: ignore[print] -- CLI audit report goes to stdout
print("Figures:", len(list(FIG.glob("*.png"))))  # ruff: ignore[print] -- CLI figure count goes to stdout
