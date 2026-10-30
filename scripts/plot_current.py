# ruff: ignore[implicit-namespace-package] -- standalone figure script, not a package module
"""Plot current exact-model tables, never historical artifacts or fitted surrogates."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, cast

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

if TYPE_CHECKING:
    from collections.abc import Sequence

    from matplotlib.figure import Figure

ROOT = Path(__file__).resolve().parents[1]

UTILITY_DIFFERENCE = 0.13
IMPROVED_FRACTION = 0.001


class _Axis(Protocol):
    """Minimal typed surface of a matplotlib axis object."""

    def set_major_formatter(self, formatter: FuncFormatter) -> None: ...


class _Axes(Protocol):
    """Minimal typed surface of the axes methods this module calls.

    matplotlib's bundled stubs mark these methods partially unknown because they
    end in an unannotated ``**kwargs``; the runtime calls below are fully specified.
    """

    xaxis: _Axis
    yaxis: _Axis

    def errorbar(
        self,
        x: Sequence[float],
        y: Sequence[int],
        *,
        xerr: Sequence[Sequence[float]],
        fmt: str,
        capsize: int,
    ) -> object: ...

    def set_yticks(self, ticks: Sequence[int], labels: Sequence[str]) -> object: ...

    def axvline(self, x: float, *, linestyle: str, linewidth: float) -> object: ...

    def set_xlabel(self, label: str) -> object: ...

    def set_title(self, label: str) -> object: ...

    def plot(self, x: Sequence[int], y: Sequence[float], *, marker: str, label: str) -> object: ...

    def set_xticks(self, ticks: Sequence[int]) -> object: ...

    def set_ylim(self, *, bottom: int) -> tuple[float, float]: ...

    def set_ylabel(self, label: str) -> object: ...

    def legend(self) -> object: ...

    def bar(self, x: Sequence[str], height: Sequence[float]) -> object: ...

    def text(self, x: float, y: float, s: str, *, ha: str, fontsize: int) -> object: ...


def _thousands(value: float, _position: float) -> str:
    """Format a dollar axis tick, matching the published "$<n>k" labels.

    Returns:
        The tick value rendered as thousands of dollars.
    """
    return f"${value / 1000:,.0f}k"


def main(output: Path | None = None) -> None:
    """Render the current resource, mixed-estate and utility figures."""
    output = Path(output or ROOT / "outputs/v12")
    figures = output / "figures"
    figures.mkdir(exist_ok=True)

    def read(name: str) -> list[dict[str, str]]:
        with (output / name).open(newline="") as stream:
            return list(csv.DictReader(stream))

    def save(fig: Figure, name: str) -> None:
        fig.tight_layout()
        fig.savefig(figures / (name + ".png"), dpi=170)  # pyright: ignore[reportUnknownMemberType] -- matplotlib savefig stub ends in unannotated **kwargs
        fig.savefig(figures / (name + ".svg"))  # pyright: ignore[reportUnknownMemberType] -- matplotlib savefig stub ends in unannotated **kwargs
        plt.close(fig)

    rows = [
        r
        for r in read("psa_perspectives.csv")
        if r["scenario"] == "reference" and r["strategy"] == "panda" and r["perspective"] == "health_system"
    ]
    labels = {
        "pilot": "Pilot (3)",
        "chhhs": "CHHHS (10)",
        "chhhs_tchhs": "CHHHS + TCHHS (14)",
        "spokes": "Illustrative state (33)",
    }
    means = [float(r["mean"]) for r in rows]
    lower = [float(r["lower"]) for r in rows]
    upper = [float(r["upper"]) for r in rows]
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax = cast("_Axes", cast("object", ax))
    _ = ax.errorbar(
        means,
        range(len(rows)),
        xerr=[[m - lo for m, lo in zip(means, lower, strict=True)], [u - m for m, u in zip(means, upper, strict=True)]],
        fmt="o",
        capsize=5,
    )
    _ = ax.set_yticks(range(len(rows)), [labels[r["portfolio"]] for r in rows])
    _ = ax.axvline(0, linestyle="--", linewidth=1)
    ax.xaxis.set_major_formatter(FuncFormatter(_thousands))
    _ = ax.set_xlabel("Annual net resource saving (AUD): mean and 95% prior interval")
    _ = ax.set_title("Panda Vision versus telephone — conditional, not observed savings")
    save(fig, "resource_intervals")
    budget = read("mixed_estate_budget.csv")
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax = cast("_Axes", cast("object", ax))
    for keep, label in [("True", "Retain 3; purchase 7"), ("False", "Purchase all 10")]:
        rs = [
            r
            for r in budget
            if r["portfolio"] == "chhhs" and r["strategy"] == "panda" and r["retain_known_estate"] == keep
        ]
        _ = ax.plot([int(r["year"]) for r in rs], [float(r["capital"]) for r in rs], marker="o", label=label)
    _ = ax.set_xticks(range(1, 8))
    _ = ax.set_ylim(bottom=0)
    ax.yaxis.set_major_formatter(FuncFormatter(_thousands))
    _ = ax.set_xlabel("Budget year")
    _ = ax.set_ylabel("Capital purchases (AUD; constant prices)")
    _ = ax.set_title("CHHHS mixed estate: ownership and replacement made explicit")
    _ = ax.legend()
    save(fig, "mixed_estate_capital")
    rows = [
        r
        for r in read("utility_bridge_scenarios.csv")
        if float(r["utility_difference"]) == UTILITY_DIFFERENCE  # ruff: ignore[float-equality-comparison] -- published selection must not change
        and int(r["duration_years_assumed"]) == 1
        and float(r["fraction_consultations_improved_assumed"]) == IMPROVED_FRACTION  # ruff: ignore[float-equality-comparison] -- published selection must not change
    ]
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax = cast("_Axes", cast("object", ax))
    _ = ax.bar(
        [f"{float(r['discount_rate']):.0%}" for r in rows],
        [float(r["qalys_per_1000_consultations"]) for r in rows],
    )
    _ = ax.set_ylim(bottom=0)
    _ = ax.set_xlabel("Discount rate")
    _ = ax.set_ylabel("Illustrative QALYs per 1,000 consultations")
    _ = ax.set_title("One year of assumed utility gain begins at age 11, not birth")
    _ = fig.text(  # pyright: ignore[reportUnknownMemberType] -- matplotlib text stub ends in unannotated **kwargs
        0.5,
        0.01,
        "0.13 utility contrast; 1 improved infant per 1,000 consultations. Not a video-effect estimate.",
        ha="center",
        fontsize=9,
    )
    save(fig, "utility_correction")
    print("Created three current PNG/SVG figures from CSV tables.")  # ruff: ignore[print] -- script status line goes to stdout


if __name__ == "__main__":
    main()
