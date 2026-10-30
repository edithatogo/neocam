"""Regional hospital/emergency scenarios; not a census of all community clinics."""

from __future__ import annotations

import numpy as np

from src.pathways_v6 import _activity  # pyright: ignore[reportPrivateUsage] -- in-package activity helper shared with the portfolio layer
from src.statewide import Site, load_sites, select_sites

CHHHS = (
    "Cairns",
    "Atherton",
    "Mareeba",
    "Innisfail",
    "Tully",
    "Mossman",
    "Babinda",
    "Gordonvale",
    "Herberton",
    "Yarrabah Emergency Service",
)
TCHHS = ("Cooktown", "Weipa", "Thursday Island", "Bamaga")


def regional_roster() -> list[dict[str, object]]:
    """Return the public hospital/emergency roster with missing births left as ``None``."""
    old = {s.name: s for s in load_sites()}
    rows: list[dict[str, object]] = []
    for name in CHHHS + TCHHS:
        s = old.get(name)
        role = (
            "birth/referral"
            if name == "Cairns"
            else "birthing"
            if name in {"Atherton", "Mareeba", "Innisfail", "Thursday Island"}
            else "reopened birthing"
            if name in {"Cooktown", "Weipa"}
            else "readiness scenario"
        )
        status = (
            "birthing resumed September 2026"
            if name == "Cooktown"
            else "birthing resumed May 2024"
            if name == "Weipa"
            else "not asserted to have planned birthing"
            if role == "readiness scenario"
            else "current service directory"
        )
        rows.append({
            "name": name,
            "hhs": "CHHHS" if name in CHHHS else "TCHHS",
            "role": role,
            "births_2022": None if s is None else s.births,
            "current_status": status,
            "births_status": "missing from retained table; NOT observed zero" if s is None else "2022 historical count",
            "source_id": "CHHHS_DIR" if name in CHHHS else "TCHHS_DIR",
            "scope": "hospital/emergency network only; community/primary health centres excluded",
        })
    return rows


def portfolio(name: str) -> list[Site]:
    """Return the named regional site portfolio, preserving published birth counts.

    Raises:
        ValueError: If the portfolio name is unknown.
    """
    old = {s.name: s for s in load_sites()}
    if name in {"pilot", "spokes"}:
        return select_sites(list(old.values()), name)
    names = CHHHS if name == "chhhs" else CHHHS + TCHHS if name == "chhhs_tchhs" else None
    if names is None:
        msg = "Unknown portfolio"
        raise ValueError(msg)
    # A zero in this computational record is an inactive-exposure placeholder;
    # the public roster retains None and does not report it as zero births.
    return [
        old[n] if n in old else Site(n, 0, 2022, "readiness", "remote" if n in TCHHS else "regional") for n in names
    ]


def consultation_overrides(  # ruff: ignore[too-many-arguments] -- published scenario API
    sites: list[Site],
    inputs: dict[str, np.ndarray],
    *,
    reopened: bool = False,
    readiness_calls: float = 0.0,
    cairns_hub_only: bool = False,
    cooktown_annual_births: float = 50.0,
) -> dict[str, np.ndarray]:
    """Expose uncertain activity without manufacturing birth observations.

    Reopened uses published Weipa32 births in2025, and Cooktown50/year assumed
    (not observed). No new 2026 denominator is asserted. Readiness calls are
    separate incident scenarios; a zero-benefit reference still incurs readiness.

    Returns:
        Per-site consultation overrides for the selected scenario.

    Raises:
        ValueError: If readiness calls or assumed births are negative or non-finite.
    """
    if (
        not np.isfinite(readiness_calls)
        or readiness_calls < 0
        or not np.isfinite(cooktown_annual_births)
        or cooktown_annual_births < 0
    ):
        msg = "Nonnegative finite activity required"
        raise ValueError(msg)
    n = len(inputs["odds_ratio"])
    out: dict[str, np.ndarray] = {}
    for s in sites:
        if s.name == "Cairns" and cairns_hub_only:
            out[s.name] = np.zeros(n)
        elif reopened and s.name in {"Cooktown", "Weipa"}:
            births = 32.0 if s.name == "Weipa" else cooktown_annual_births
            out[s.name] = births * (3 * inputs["calls_per_pilot_site"] / 486) * 1.25 * inputs["state_uptake"]
        elif s.group == "readiness":
            out[s.name] = _activity(s, inputs) + readiness_calls * (inputs["calls_per_pilot_site"] / 12.5)
    return out
