"""Prevent structural assumptions being described with the wrong denominator."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_rescue_scenario_identifies_retained_infant_denominator():
    text = (ROOT/'scripts/analyse_v6.py').read_text()
    assert 'excess_rescue_2pct_retained' in text
    assert 'excess_rescue_2pp' not in text

def test_reference_parameter_export_is_labelled_not_a_live_config():
    assert 'reference snapshot, not a live configuration input' in (ROOT/'conductor/runbook.md').read_text()
