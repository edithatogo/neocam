"""Guard strict tool settings and the absence of silent CI shortcuts."""

import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def config():
    return tomllib.loads((ROOT / "pyproject.toml").read_text())


def test_ruff_all_preview_no_unsafe_fixes():
    ruff = config()["tool"]["ruff"]
    assert ruff["preview"] is True
    assert ruff["lint"]["select"] == ["ALL"]
    assert ruff["unsafe-fixes"] is False
    # Only documented formatter conflicts are disabled globally; selectors use
    # canonical rule names (rule-codes-in-selectors).
    assert set(ruff["lint"]["ignore"]) == {
        "missing-trailing-comma",
        "single-line-implicit-string-concatenation",
    }
    assert ruff["lint"]["explicit-preview-rules"] is False


def test_both_type_checkers_are_strict_and_unsuppressed():
    tool = config()["tool"]
    assert tool["ty"]["rules"]["all"] == "error"
    assert tool["basedpyright"]["typeCheckingMode"] == "all"
    assert tool["basedpyright"]["failOnWarnings"] is True
    assert not tool["basedpyright"].get("ignore")
    assert not (ROOT / ".basedpyright/baseline.json").exists()


def test_mutation_checks_all_operator_classes_without_pardons():
    mutation = config()["tool"]["pytest-gremlins"]
    assert set(mutation["operators"]) == {"comparison", "arithmetic", "boolean", "boundary", "return"}
    assert mutation["max_pardons"] == 0
    assert mutation["cache"] is False
    assert "src/statewide.py" in mutation["paths"]


def test_dataframe_policy_and_tools_are_declared():
    cfg = config()
    tabular = cfg["project"]["optional-dependencies"]["tabular"]
    assert tabular == ["polars==2.1.0"]
    dependencies = cfg["dependency-groups"]["assurance"]
    for tool in ["ruff", "ty", "basedpyright", "pytest-gremlins", "scalene", "hypothesis", "pip-audit"]:
        assert any(isinstance(dep, str) and dep.startswith(tool + "==") for dep in dependencies)
    assert "hypothesis[all]" not in "\n".join(dep for dep in dependencies if isinstance(dep, str))


def test_native_tools_have_pinned_binary_integrity():
    path = ROOT / "quality/native-tools.json"
    assert path.exists()
    manifest = json.loads(path.read_text())
    for tool in ["gitleaks", "vale"]:
        assert manifest[tool]["version"]
        linux = manifest[tool]["linux-x86_64"]
        assert len(linux["sha256"]) == 64
        assert linux["url"].startswith("https://github.com/")


def test_ci_no_dynamic_resolution_or_partial_bypass():
    workflow = (ROOT / ".github/workflows/ci.yml").read_text()
    assert "uv sync --frozen" in workflow
    assert "uv lock --upgrade" not in workflow
    assert "--ci" not in workflow
    assert "quality.cli --profile full" in workflow
    assert "fetch-depth: 0" in workflow
    assert "continue-on-error" not in workflow


def test_context_has_single_authoritative_runbook():
    assert (ROOT / "GEMINI.md").exists()
    assert (ROOT / "conductor/runbook.md").exists()
    for name in ["AGENTS.md", "GEMINI.md"]:
        assert "conductor/runbook.md" in (ROOT / name).read_text()


def test_no_fake_uv_lock_is_supplied():
    path = ROOT / "uv.lock"
    if path.exists():
        from quality.contracts import validate_lock  # ruff: ignore[import-outside-top-level] -- imported only when a lock is present

        assert validate_lock(path) == []
    else:
        state = json.loads((ROOT / "conductor/current-state.json").read_text())
        assert state["release_ready"] is False


def test_scalene_profile_keeps_cpu_and_memory_measurement():
    from quality.cli import gates_for_profile  # ruff: ignore[import-outside-top-level] -- keeps the tool import local to this contract

    gate = next(item for item in gates_for_profile("full") if item.name == "scalene")
    assert "--cpu-only" not in gate.command


def test_every_python_release_target_has_an_enforced_pin():
    cfg = config()
    declarations = cfg["project"]["dependencies"] + cfg["project"]["optional-dependencies"]["tabular"]
    declarations += cfg["dependency-groups"]["test"]
    declarations += [item for item in cfg["dependency-groups"]["assurance"] if isinstance(item, str)]
    pins = dict(item.split("==", 1) for item in declarations)
    targets = json.loads((ROOT / "evidence/dependency_targets_v3.json").read_text())["packages"]
    for target in targets:
        assert pins.get(target["name"]) == target["target_version"]
