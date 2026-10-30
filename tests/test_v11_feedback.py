"""An interrupted second execution must not retain the first run's success seal."""

import json

import pytest

from quality import feedback


@pytest.mark.parametrize("mode", ["tests", "mutation"])
def test_success_seal_is_consumed_before_rerun(tmp_path, mode):
    initial = feedback.prepare(tmp_path, mode, available=True, environment={})
    feedback.complete(tmp_path, initial, 0)
    second = feedback.prepare(tmp_path, mode, available=True, environment={})
    assert second.cache_reused
    assert not (tmp_path / ".feedback-cache" / f"{mode}.json").exists()
    # Simulate interruption: no complete() for the second run.
    third = feedback.prepare(tmp_path, mode, available=True, environment={})
    assert not third.cache_reused


@pytest.mark.parametrize("value", [[], None, "not a mapping", 17])
def test_malformed_cache_record_rebuilds_not_crashes(tmp_path, value):
    directory = tmp_path / ".feedback-cache"
    directory.mkdir()
    (directory / "tests.json").write_text(json.dumps(value))
    plan = feedback.prepare(tmp_path, "tests", available=True, environment={})
    assert not plan.cache_reused


def test_unavailable_mutation_invalidates_previous_seal(tmp_path):
    plan = feedback.prepare(tmp_path, "mutation", available=True, environment={})
    feedback.complete(tmp_path, plan, 0)
    with pytest.raises(ModuleNotFoundError):
        feedback.prepare(tmp_path, "mutation", available=False, environment={})
    assert not (tmp_path / ".feedback-cache/mutation.json").exists()
