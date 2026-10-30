"""Portable current-report contract: one data source, no host-specific helpers."""

import importlib
import importlib.util
import tomllib
from pathlib import Path
from typing import Protocol, cast

ROOT = Path(__file__).resolve().parents[1]


class ReportBuilder(Protocol):
    """The portable report builder surface."""

    def build(self) -> None:
        """Generate the configured reports."""
        ...


def test_current_report_builder_is_portable() -> None:
    assert importlib.util.find_spec("scripts.build_current_report"), "Missing portable current-report builder"
    path = ROOT / "scripts/build_current_report.py"
    assert "/home/oai/" not in path.read_text()
    raw = importlib.import_module("scripts.build_current_report")
    # import_module yields ModuleType; the builder surface is asserted by this test.
    module = cast("ReportBuilder", cast("object", raw))
    assert callable(module.build)


def test_current_ci_uses_one_evidence_version() -> None:
    text = (ROOT / ".github/workflows/ci.yml").read_text()
    assert "--evidence-version v8" not in text
    assert "EVIDENCE_VERSION" in text


def test_reporting_is_separate_from_exact_model_dependencies() -> None:
    cfg = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert "reporting" in cfg["project"]["optional-dependencies"]
    dependencies = cast("list[str]", cfg["project"]["dependencies"])
    assert not any("docx" in s or "reportlab" in s for s in dependencies)
