"""Portable current-report contract: one data source, no host-specific helpers."""
import importlib
import importlib.util
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]


def test_current_report_builder_is_portable():
    assert importlib.util.find_spec('scripts.build_current_report'), 'Missing portable current-report builder'
    path=ROOT/'scripts/build_current_report.py'
    assert '/home/oai/' not in path.read_text()
    module=importlib.import_module('scripts.build_current_report')
    assert callable(module.build)


def test_current_ci_uses_one_evidence_version():
    text=(ROOT/'.github/workflows/ci.yml').read_text()
    assert '--evidence-version v8' not in text
    assert 'EVIDENCE_VERSION' in text


def test_reporting_is_separate_from_exact_model_dependencies():
    import tomllib
    cfg=tomllib.loads((ROOT/'pyproject.toml').read_text())
    assert 'reporting' in cfg['project']['optional-dependencies']
    assert not any('docx' in s or 'reportlab' in s for s in cfg['project']['dependencies'])
