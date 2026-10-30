"""Regressions discovered by simulated economic and security review."""

from urllib.request import Request

import numpy as np
import pytest

import sources.retrieve_originals as module
from quality.cli import gates_for_profile
from scripts.analyse_v7 import evaluate_perspectives
from src.pathways_v6 import PathwaySpec
from src.portfolios_v7 import portfolio
from src.statewide import Parameters, Site, _base_arrays


def test_unrelated_statewide_site_does_not_add_chhhs_receiver_savings():
    p = Parameters()
    s = PathwaySpec()
    x = _base_arrays(p, 1)
    sites = portfolio("chhhs_tchhs")
    _, regional, _ = evaluate_perspectives(sites, p, s, x, {})
    _, expanded, _ = evaluate_perspectives(
        [*sites, Site("Outside referral catchment", 5000, 2022, "regional_proxy", "regional")], p, s, x, {}
    )
    for key in regional:
        assert np.allclose(regional[key]["provider_chhhs"], expanded[key]["provider_chhhs"])
    assert not np.allclose(regional["panda"]["health_system"], expanded["panda"]["health_system"])


def test_source_redirect_is_rejected_before_opening_an_unapproved_host():
    assert hasattr(module, "ApprovedRedirect"), "Missing pre-request redirect guard"
    handler = module.ApprovedRedirect()
    with pytest.raises(ValueError, match="Unapproved"):
        handler.redirect_request(
            Request("https://www.ihacpa.gov.au/a"), None, 302, "Found", {}, "https://example.invalid/secret"
        )


def test_current_gates_do_not_write_into_historical_verification():
    commands = [" ".join(g.command) for g in gates_for_profile("full")]
    assert not any("verification/v6/" in c for c in commands)
    assert any("verification/v7/" in c for c in commands)


def test_regional_retention_removes_only_known_pilot_capital():
    p = Parameters()
    s = PathwaySpec()
    x = _base_arrays(p, 1)
    sites = portfolio("chhhs_tchhs")
    new, _, _ = evaluate_perspectives(sites, p, s, x, {})
    retained, _, _ = evaluate_perspectives(sites, p, s, x, {}, sunk=("panda",))
    assert retained["panda"]["incremental_purchase_capital"][0] == 110000
    assert retained["panda"]["capital_annualised"][0] == pytest.approx(new["panda"]["capital_annualised"][0] * 11 / 14)


def test_current_core_coverage_includes_new_perspective_health_and_portfolio_modules():
    command = " ".join(next(g for g in gates_for_profile("full") if g.name == "core_coverage").command)
    for path in ("src/pathways_v6.py", "src/perspectives_v7.py", "src/portfolios_v7.py", "src/audit_v7.py"):
        assert path in command
