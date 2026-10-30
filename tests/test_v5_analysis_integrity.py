"""Output lineage and separation of clinical evidence from explanatory learning."""

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Protocol, TypedDict, cast

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


class AnalysisModule(Protocol):
    """The subset of the analyse_v5 driver this module loads by file path."""

    def write_manifest(self, output: Path, *, root: Path) -> None:
        """Write the analysis manifest for ``output`` relative to ``root``."""
        ...


class PsaEntry(TypedDict):
    """One recorded PSA structure in the v5 results document."""

    summary: dict[str, dict[str, float]]
    cost_only_evpi: float


class ResultsV5(TypedDict):
    """The recorded v5 results document."""

    protected_v4_result_parity: dict[str, bool]
    psa_primary_structures: int
    psa_iterations_each: int
    psa: dict[str, PsaEntry]


def load_driver() -> AnalysisModule:
    """Import the analyse_v5 driver from its file path, typed as its used surface.

    Returns:
        The executed driver module typed as the manifest-writing surface.
    """
    spec = importlib.util.spec_from_file_location("analysis_v5", ROOT / "scripts/analyse_v5.py")
    assert spec is not None
    assert spec.loader is not None
    raw = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(raw)
    # exec_module yields ModuleType; the attributed surface is asserted by these tests.
    return cast("AnalysisModule", cast("object", raw))


def test_analysis_manifest_excludes_its_own_mutating_digest(tmp_path: Path) -> None:
    module = load_driver()
    d = tmp_path / "outputs"
    d.mkdir()
    _ = (d / "table.csv").write_text("x\n1\n")
    _ = (d / "analysis_manifest.json").write_text("{}")
    module.write_manifest(d, root=tmp_path)
    first = (d / "analysis_manifest.json").read_bytes()
    module.write_manifest(d, root=tmp_path)
    assert first == (d / "analysis_manifest.json").read_bytes()
    payload = cast("dict[str, object]", json.loads(first))
    assert not any(k.endswith("analysis_manifest.json") for k in payload)
    assert payload["outputs/table.csv"] == hashlib.sha256((d / "table.csv").read_bytes()).hexdigest()


def test_recorded_five_arm_results_retain_v4_panda() -> None:
    r = cast("ResultsV5", json.loads((ROOT / "outputs/v5/results_v5.json").read_text()))
    assert all(r["protected_v4_result_parity"].values())
    assert r["psa_primary_structures"] == 18
    assert r["psa_iterations_each"] == 20000
    for result in r["psa"].values():
        assert np.isclose(sum(v["p_optimal"] for v in result["summary"].values()), 1)
        assert result["cost_only_evpi"] >= 0


def test_all_recorded_analysis_hashes_are_current() -> None:
    manifest = cast("dict[str, str]", json.loads((ROOT / "outputs/v5/analysis_manifest.json").read_text()))
    assert not any(k.endswith("analysis_manifest.json") for k in manifest)
    for name, digest in manifest.items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
