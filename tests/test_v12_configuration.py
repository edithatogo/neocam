"""Declared inputs must reach the executed analysis, not merely agree with a register."""

import json
import shutil
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict, cast

import numpy as np
import pytest

from scripts import analyse_v7
from src import configuration
from src.pathways_v6 import PathwaySpec
from src.portfolios_v7 import portfolio
from src.statewide import Parameters, _base_arrays  # pyright: ignore[reportPrivateUsage] -- private kernel helper is the in-repo surface under test

if TYPE_CHECKING:
    from collections.abc import Callable

ROOT = Path(__file__).resolve().parents[1]

# Driver/config signatures declare bare containers; restate the asserted shapes.
Perspectives = tuple[dict[str, dict[str, np.ndarray]], dict[str, object], dict[str, object]]
evaluate_perspectives = cast("Callable[..., Perspectives]", analyse_v7.evaluate_perspectives)


class ConfigDocument(TypedDict):
    """The declared-input documents these tests read and corrupt."""

    run: dict[str, object]
    schema_version: object
    parameters: object
    equipment_cost: object
    hub_minutes_per_call: int
    owned_assets: object


def read_config(path: Path) -> ConfigDocument:
    """Read a declared-input document, typed as the fields these tests touch.

    Returns:
        The parsed document with its declared-authored fields.
    """
    return cast("ConfigDocument", json.loads(path.read_text(encoding="utf-8")))


def fixture(tmp_path: Path):
    assert (ROOT / "config").is_dir(), "Missing authoritative run configuration"
    _ = shutil.copytree(ROOT / "config", tmp_path / "config")
    _ = shutil.copytree(ROOT / "data", tmp_path / "data")
    return tmp_path


def test_default_resolved_values_preserve_reference() -> None:
    c = configuration.load_configuration(ROOT)
    assert asdict(c.parameters) == asdict(Parameters())
    assert asdict(c.pathways) == asdict(PathwaySpec())
    assert len(c.owned_assets) == 3


def test_changed_declared_price_reaches_driver(tmp_path: Path) -> None:
    m = configuration
    root = fixture(tmp_path)
    path = root / "data/parameters.json"
    d = read_config(path)
    d["equipment_cost"] = 20000.0
    _ = path.write_text(json.dumps(d))
    c = m.load_configuration(root)
    r, _, _ = evaluate_perspectives(
        portfolio("pilot"), c.parameters, c.pathways, _base_arrays(c.parameters, 1), {}, owned_assets=c.owned_assets
    )
    assert r["panda"]["incremental_purchase_capital"][0] == 60000
    snap = cast("Callable[..., dict[str, dict[str, float]]]", c.snapshot)()
    assert snap["parameters"]["equipment_cost"] == 20000


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"draws": True}, "Draw count must be an integer in 2..1000000"),
        ({"seed": -1}, "Seed must be a nonnegative integer"),
        ({"portfolios": ["pilot", "pilot"]}, "Unknown, empty or repeated portfolio"),
        ({"unknown": 1}, "Run controls requires exactly"),
    ],
)
def test_bad_run_config_rejected(tmp_path: Path, change: dict[str, object], message: str) -> None:
    m = configuration
    root = fixture(tmp_path)
    path = root / "config/reference.json"
    d = read_config(path)
    d["run"].update(change)
    _ = path.write_text(json.dumps(d))
    with pytest.raises(ValueError, match=message):
        _ = m.load_configuration(root)


def test_duplicate_json_keys_rejected(tmp_path: Path) -> None:
    m = configuration
    root = fixture(tmp_path)
    _ = (root / "config/pathways.json").write_text('{"endpoint":"eventual","endpoint":"initial"}')
    with pytest.raises(ValueError, match="Duplicate configuration key"):
        _ = m.load_configuration(root)


def test_partial_pathway_document_cannot_silently_default(tmp_path: Path) -> None:
    m = configuration
    root = fixture(tmp_path)
    _ = (root / "config/pathways.json").write_text('{"endpoint":"initial"}')
    with pytest.raises(ValueError, match="Pathways requires exactly"):
        _ = m.load_configuration(root)


def test_source_escape_rejected(tmp_path: Path) -> None:
    m = configuration
    root = fixture(tmp_path)
    path = root / "config/reference.json"
    d = read_config(path)
    d["parameters"] = "../escape.json"
    _ = path.write_text(json.dumps(d))
    with pytest.raises(ValueError, match="Invalid configuration source"):
        _ = m.load_configuration(root)


def test_configuration_hash_changes_with_live_pathway(tmp_path: Path) -> None:
    m = configuration
    root = fixture(tmp_path)
    a = m.load_configuration(root)
    path = root / "config/pathways.json"
    d = read_config(path)
    d["hub_minutes_per_call"] = 30
    _ = path.write_text(json.dumps(d))
    b = m.load_configuration(root)
    assert a.digest != b.digest
    assert b.pathways.hub_minutes_per_call == 30


@pytest.mark.parametrize(
    ("which", "value", "error"),
    [
        ("root", [], TypeError),
        ("schema", 2, ValueError),
        ("assets", None, TypeError),
        ("asset_record", {"site": "Atherton"}, ValueError),
        ("path", "/absolute", ValueError),
        ("remaining", 6, ValueError),
        ("nonfinite", float("nan"), ValueError),
    ],
)
def test_other_malformed_configuration_contracts(
    tmp_path: Path, which: str, value: object, error: type[Exception]
) -> None:
    m = configuration
    root = fixture(tmp_path)
    f = root / "config/reference.json"
    d = read_config(f)
    if which == "root":
        _ = f.write_text(json.dumps(value))
    elif which == "schema":
        d["schema_version"] = value
        _ = f.write_text(json.dumps(d))
    elif which == "path":
        d["parameters"] = value
        _ = f.write_text(json.dumps(d))
    elif which == "nonfinite":
        p = root / "data/parameters.json"
        v = read_config(p)
        v["equipment_cost"] = value
        _ = p.write_text(json.dumps(v))
    else:
        p = root / "config/equipment_estate.json"
        v = read_config(p)
        if which == "assets":
            v["owned_assets"] = value
        elif which == "asset_record":
            v["owned_assets"] = [value]
        else:
            assets = cast("list[dict[str, object]]", v["owned_assets"])
            assets[0]["remaining_life_years"] = value
        _ = p.write_text(json.dumps(v))
    with pytest.raises(error):
        _ = m.load_configuration(root)


def test_run_recipe_outside_repository_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Run configuration must remain inside the repository"):
        _ = configuration.load_configuration(tmp_path, tmp_path.parent / "elsewhere.json")


def test_misspelled_owned_site_cannot_silently_disappear(tmp_path: Path) -> None:
    m = configuration
    root = fixture(tmp_path)
    f = root / "config/equipment_estate.json"
    d = read_config(f)
    assets = cast("list[dict[str, object]]", d["owned_assets"])
    assets[0]["site"] = "Athertonn"
    _ = f.write_text(json.dumps(d))
    with pytest.raises(ValueError, match="Unknown site in owned equipment estate"):
        _ = m.load_configuration(root)
