"""Hook commands cannot treat a repository filename as an executable flag."""
import pytest
from quality.hooks import hook_commands


@pytest.mark.parametrize('kind',['python','prose','workflow'])
def test_filename_options_are_terminated(kind):
    commands=hook_commands(kind,['--misleading.py'])
    assert all('--' in command for command in commands)


@pytest.mark.parametrize('path',['../outside.py','/outside.py'])
def test_external_paths_rejected(path):
    with pytest.raises(ValueError):hook_commands('python',[path])


@pytest.mark.parametrize('kind',['python','prose','workflow'])
def test_no_files_no_work(kind):
    assert hook_commands(kind,[]) == []


def test_unknown_kind_rejected():
    with pytest.raises(ValueError):hook_commands('unknown',[])


def test_secret_scan_does_not_require_filenames():
    command=hook_commands('secrets',[])[0]
    assert '--staged' in command and '--redact=100' in command
