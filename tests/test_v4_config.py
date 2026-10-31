"""Keep local hooks thin and CI permission/cancellation boundaries explicit."""

import json
import tomllib
from pathlib import Path
from typing import TypedDict, cast

ROOT = Path(__file__).resolve().parents[1]


class RenovateConfig(TypedDict):
    """The asserted renovate.json contract."""

    automerge: bool
    packageRules: list[object]


def test_only_one_dependency_bot_and_reviewed_groups() -> None:
    assert not (ROOT / ".github/dependabot.yml").exists()
    cfg = cast("RenovateConfig", json.loads((ROOT / "renovate.json").read_text()))
    assert cfg["automerge"] is False
    assert len(cfg["packageRules"]) >= 2


def test_thin_hooks_no_expensive_acceptance_work() -> None:
    p = ROOT / ".pre-commit-config.yaml"
    assert p.exists()
    text = p.read_text()
    assert "repo: local" in text
    assert "quality.hooks" in text
    assert "--gremlins" not in text
    assert "quality.cli --profile full" not in text


def _nested_str(config: dict[str, object], *keys: str) -> str:
    """Return a nested string from a parsed document, failing if the shape is wrong."""
    section: dict[str, object] = config
    for key in keys[:-1]:
        child = section[key]
        assert isinstance(child, dict)
        section = cast("dict[str, object]", child)
    result = section[keys[-1]]
    assert isinstance(result, str)
    return result


def test_ci_pins_the_single_supported_interpreter() -> None:
    """One bleeding-edge interpreter (3.15) is declared, typed and run in CI."""
    text = (ROOT / ".github/workflows/ci.yml").read_text()
    cfg = cast("dict[str, object]", tomllib.loads((ROOT / "pyproject.toml").read_text()))
    minor = _nested_str(cfg, "project", "requires-python").removeprefix(">=").split(",")[0]
    assert minor == "3.15"
    assert _nested_str(cfg, "tool", "ty", "environment", "python-version") == minor
    assert _nested_str(cfg, "tool", "basedpyright", "pythonVersion") == minor
    assert f"python-version: '{minor}'" in text
    # No legacy interpreters remain, and a one-version project needs no version matrix.
    assert "matrix:" not in text
    for legacy in ("'3.13'", "'3.14'"):
        assert legacy not in text
    assert "cancel-in-progress: ${{ github.event_name == 'pull_request' }}" in text
    assert "quality.cli --profile pr" in text
    assert "uv lock --check" in text
    assert "enable-cache:" in text
    assert "github.event_name != 'pull_request'" in text


def test_feedback_plugins_are_not_runtime_dependencies() -> None:
    cfg = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert cfg["project"]["dependencies"] == ["numpy==2.5.4"]
    feedback = cast("list[str]", cfg["dependency-groups"]["feedback"])
    assert {"pytest-testmon==2.2.0", "pytest-xdist==3.8.0"} <= set(feedback)
