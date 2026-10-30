"""Hook commands cannot treat a repository filename as an executable flag."""

import pytest

from quality.hooks import hook_commands


@pytest.mark.parametrize("kind", ["python", "prose", "workflow"])
def test_filename_options_are_terminated(kind: str) -> None:
    commands = hook_commands(kind, ["--misleading.py"])
    assert all("--" in command for command in commands)


@pytest.mark.parametrize("path", ["../outside.py", "/outside.py"])
def test_external_paths_rejected(path: str) -> None:
    with pytest.raises(ValueError, match="Hook filenames must remain inside the repository"):
        _ = hook_commands("python", [path])


@pytest.mark.parametrize("kind", ["python", "prose", "workflow"])
def test_no_files_no_work(kind: str) -> None:
    assert hook_commands(kind, []) == []


def test_unknown_kind_rejected() -> None:
    with pytest.raises(ValueError, match="Unknown hook kind"):
        _ = hook_commands("unknown", [])


def test_secret_scan_does_not_require_filenames() -> None:
    command = hook_commands("secrets", [])[0]
    assert "--staged" in command
    assert "--redact=100" in command
