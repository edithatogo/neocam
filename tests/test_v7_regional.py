import importlib

import numpy as np
import pytest

from src.pathways_v6 import compare_v6
from src.statewide import load_sites, select_sites


def test_explicit_calls_override_without_changing_births():
    sites = select_sites(load_sites(), "pilot")
    counts = {s.name: np.array([2.0]) for s in sites}
    r = compare_v6(sites, site_calls=counts)
    assert r["panda"]["consultations"][0] == 6
    assert sum(s.births for s in sites) == 486


def test_calls_override_unknown_site_is_rejected():
    with pytest.raises(ValueError, match="Unknown site in activity override"):
        compare_v6(select_sites(load_sites(), "pilot"), site_calls={"x": np.array([2.0])})


def test_regional_census_preserves_missingness_and_reopened_status():
    try:
        m = importlib.import_module("src.portfolios_v7")
    except ModuleNotFoundError:
        pytest.fail("regional module absent")
    rows = m.regional_roster()
    assert len([r for r in rows if r["hhs"] == "CHHHS"]) == 10
    assert len([r for r in rows if r["hhs"] == "TCHHS"]) == 4
    assert next(r for r in rows if r["name"] == "Weipa")["births_2022"] is None
    assert next(r for r in rows if r["name"] == "Cooktown")["current_status"] == "birthing resumed September 2026"
