"""Regression tests for plugin identity and version-isolated evidence."""
import json
from pathlib import Path
import subprocess
import sys

from quality.feedback import prepare


def test_testmon_loads_actual_upstream_plugin_module(tmp_path):
    """pytest-testmon 2.2.0 declares testmon.pytest_testmon, not testmon."""
    plan = prepare(tmp_path, 'tests', available=True, environment={})
    assert ('-p', 'testmon.pytest_testmon') in tuple(zip(plan.command, plan.command[1:]))


def test_source_integrity_accepts_evidence_version_and_preserves_history(tmp_path):
    root = tmp_path / 'repo'
    (root / 'quality').mkdir(parents=True)
    (root / 'sources').mkdir()
    (root / 'verification/v7').mkdir(parents=True)
    source = Path('quality/source_archive.py').read_text()
    (root / 'quality/source_archive.py').write_text(source)
    historic = root / 'verification/v7/source_archive.json'
    historic.write_text('historical evidence\n')
    (root / 'sources/manifest.json').write_text(json.dumps({'files': []}))
    result = subprocess.run([sys.executable, str(root / 'quality/source_archive.py'),
                             '--output', 'verification/v10/source_archive.json'], capture_output=True, text=True)
    assert result.returncode != 0  # An empty source scope remains a failure.
    assert historic.read_text() == 'historical evidence\n'
    assert (root / 'verification/v10/source_archive.json').exists()


def test_source_integrity_rejects_unsafe_evidence_version(tmp_path):
    root = tmp_path / 'repo'
    (root / 'quality').mkdir(parents=True)
    (root / 'quality/source_archive.py').write_text(Path('quality/source_archive.py').read_text())
    (root / 'sources').mkdir()
    (root / 'sources/manifest.json').write_text(json.dumps({'files': []}))
    result = subprocess.run([sys.executable, str(root / 'quality/source_archive.py'),
                             '--output', '../escape'], capture_output=True, text=True)
    assert result.returncode == 2
    assert not (tmp_path / 'escape').exists()
