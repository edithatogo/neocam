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


def test_primary_ci_is_not_duplicated_in_compatibility_matrix() -> None:
    text = (ROOT / ".github/workflows/ci.yml").read_text()
    assert "python: ['3.14', '3.15']" in text
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
