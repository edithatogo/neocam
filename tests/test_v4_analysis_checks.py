"""Analysis inventory and Monte Carlo diagnostics are evidence, not new parameters."""

import importlib

import numpy as np
import pytest


def api():
    try:
        return importlib.import_module("quality.analysis_checks")
    except ModuleNotFoundError:
        pytest.fail("Analysis diagnostic module missing")


def test_nested_mc_diagnostics_use_actual_draws():
    rows = api().prefix_diagnostics(np.array([-3.0, -2.0, 1.0, 4.0]), (2, 4))
    assert rows[0]["p_saving"] == 0
    assert rows[1]["p_saving"] == pytest.approx(0.5)
    assert rows[1]["mcse_probability"] == pytest.approx(0.25)
    assert rows[1]["mean_net_saving"] == 0


@pytest.mark.parametrize(
    ("draws", "sizes", "message"),
    [
        (np.array([np.nan]), (1,), "Finite nonempty one-dimensional draws are required"),
        (np.array([]), (1,), "Finite nonempty one-dimensional draws are required"),
        (np.array([1.0, 2.0]), (3,), "Prefix sizes must be positive integers within the draw count"),
        (np.array([1.0, 2.0]), (True,), "Prefix sizes must be positive integers within the draw count"),
        (np.array([1.0, 2.0]), (0,), "Prefix sizes must be positive integers within the draw count"),
    ],
)
def test_mc_diagnostics_reject_invalid_inputs(draws, sizes, message):
    with pytest.raises(ValueError, match=message):
        api().prefix_diagnostics(draws, sizes)


def test_analysis_release_has_expected_inventory_and_parity():
    result = api().audit_outputs()
    assert result["scenario_rows"] == 58
    assert result["clinical_frontier_rows"] == 108
    assert result["site_rows"] == 65
    assert result["psa_structures"] == 8
    assert result["economic_defaults_unchanged"]
    assert result["protected_inputs_unchanged"]


def test_output_audit_is_portable_without_git_executable(monkeypatch):
    m = api()

    def unavailable(*args: object, **kwargs: object):
        msg = "A packaged source archive must not require Git for analysis tests"
        raise AssertionError(msg)

    if hasattr(m, "subprocess"):
        monkeypatch.setattr(m.subprocess, "run", unavailable)
    result = m.audit_outputs()
    assert result["protected_inputs_unchanged"]
