"""Cached development must not silently reuse evidence for changed inputs."""

from pathlib import Path

import pytest

from quality import feedback


def sample(root: Path) -> None:
    for name, content in [
        ("src/a.py", "X=1"),
        ("data/x.csv", "a\n1"),
        ("pyproject.toml", '[project]\nname="x"'),
        ("tests/test_a.py", "def test_x(): pass"),
    ]:
        p = root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        _ = p.write_text(content)


def test_code_change_preserves_testmon_key_but_not_mutation(tmp_path: Path) -> None:
    sample(tmp_path)
    m = feedback
    a = m.cache_key(tmp_path, "tests", {"python": "3.13", "numpy": "2"})
    b = m.cache_key(tmp_path, "mutation", {"python": "3.13", "numpy": "2"})
    _ = (tmp_path / "src/a.py").write_text("X=2")
    assert m.cache_key(tmp_path, "tests", {"python": "3.13", "numpy": "2"}) == a
    assert m.cache_key(tmp_path, "mutation", {"python": "3.13", "numpy": "2"}) != b


@pytest.mark.parametrize(
    "path",
    ["data/x.csv", "pyproject.toml", "uv.lock", "tests/conftest.py", "quality/policy.py", ".pre-commit-config.yaml"],
)
def test_static_or_policy_change_invalidates_testmon(tmp_path: Path, path: str) -> None:
    sample(tmp_path)
    m = feedback
    before = m.cache_key(tmp_path, "tests", {})
    f = tmp_path / path
    f.parent.mkdir(parents=True, exist_ok=True)
    _ = f.write_text("changed")
    assert m.cache_key(tmp_path, "tests", {}) != before


def test_deletion_and_environment_invalidate(tmp_path: Path) -> None:
    sample(tmp_path)
    m = feedback
    before = m.cache_key(tmp_path, "tests", {"python": "A"})
    assert before != m.cache_key(tmp_path, "tests", {"python": "B"})
    (tmp_path / "data/x.csv").unlink()
    assert before != m.cache_key(tmp_path, "tests", {"python": "A"})


def test_outputs_and_receipts_do_not_invalidate(tmp_path: Path) -> None:
    sample(tmp_path)
    m = feedback
    before = m.cache_key(tmp_path, "tests", {})
    for name in ["outputs/a.txt", "verification/latest.json"]:
        p = tmp_path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        _ = p.write_text("log")
    assert before == m.cache_key(tmp_path, "tests", {})


def test_cold_tests_clear_database_not_other_files(tmp_path: Path) -> None:
    sample(tmp_path)
    m = feedback
    _ = (tmp_path / ".testmondata").write_text("stale")
    _ = (tmp_path / "user.txt").write_text("keep")
    plan = m.prepare(tmp_path, "tests", available=True, environment={})
    assert plan.cache_reused is False
    assert "--testmon" in plan.command
    assert not (tmp_path / ".testmondata").exists()
    assert (tmp_path / "user.txt").read_text() == "keep"


def test_cache_only_sealed_after_success(tmp_path: Path) -> None:
    sample(tmp_path)
    m = feedback
    plan = m.prepare(tmp_path, "tests", available=True, environment={})
    m.complete(tmp_path, plan, 1)
    assert m.prepare(tmp_path, "tests", available=True, environment={}).cache_reused is False
    m.complete(tmp_path, plan, 0)
    assert m.prepare(tmp_path, "tests", available=True, environment={}).cache_reused is True


def test_mutation_clean_then_incremental(tmp_path: Path) -> None:
    sample(tmp_path)
    m = feedback
    first = m.prepare(tmp_path, "mutation", available=True, environment={})
    assert "--gremlin-clear-cache" in first.command
    m.complete(tmp_path, first, 0)
    second = m.prepare(tmp_path, "mutation", available=True, environment={})
    assert "--gremlin-clear-cache" not in second.command
    assert "--gremlin-cache" in second.command


def test_missing_selection_tool_explicitly_falls_back_to_full_tests(tmp_path: Path) -> None:
    sample(tmp_path)
    plan = feedback.prepare(tmp_path, "tests", available=False, environment={})
    assert "--testmon" not in plan.command
    assert "full ordinary suite" in plan.reason
    assert not plan.cache_reused


def test_missing_mutation_tool_is_not_replaced_by_ordinary_tests(tmp_path: Path) -> None:
    sample(tmp_path)
    with pytest.raises(ModuleNotFoundError):
        _ = feedback.prepare(tmp_path, "mutation", available=False, environment={})


def test_invalid_modes_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unknown local feedback mode"):
        _ = feedback.cache_key(tmp_path, "release", {})


def test_deleted_source_file_invalidates_selection_inventory(tmp_path: Path) -> None:
    sample(tmp_path)
    m = feedback
    before = m.cache_key(tmp_path, "tests", {})
    (tmp_path / "src/a.py").unlink()
    assert m.cache_key(tmp_path, "tests", {}) != before
