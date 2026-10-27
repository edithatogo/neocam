"""Exercise installer integrity without claiming a live binary/tool execution."""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
from types import SimpleNamespace
import urllib.error

import pytest

from quality import bootstrap, checks
from tests.test_quality_gates import binary_tar


def native_fixture(root: Path, url: str = 'https://github.com/vale-cli/vale/releases/download/v3.25.1/vale.tar.gz') -> bytes:
    payload = binary_tar()
    (root / 'quality').mkdir()
    manifest = {'vale': {'version': '3.25.1', 'test-test': {'url': url, 'sha256': hashlib.sha256(payload).hexdigest()}}}
    (root / 'quality/native-tools.json').write_text(json.dumps(manifest), encoding='utf-8')
    return payload


def use_fixture(monkeypatch, root: Path) -> None:
    monkeypatch.setattr(bootstrap, 'ROOT', root)
    monkeypatch.setattr(bootstrap.platform, 'system', lambda: 'Test')
    monkeypatch.setattr(bootstrap.platform, 'machine', lambda: 'Test')


def test_installer_matching_digest_installs_only_local_binary(monkeypatch, tmp_path: Path) -> None:
    payload = native_fixture(tmp_path)
    use_fixture(monkeypatch, tmp_path)
    monkeypatch.setattr(bootstrap.urllib.request, 'urlopen', lambda *a, **k: io.BytesIO(payload))
    assert bootstrap.main() == 0
    assert (tmp_path / '.tools/bin/vale').read_bytes() == b'binary'


def test_installer_checksum_failure_is_failure_not_unavailability(monkeypatch, tmp_path: Path) -> None:
    native_fixture(tmp_path)
    use_fixture(monkeypatch, tmp_path)
    monkeypatch.setattr(bootstrap.urllib.request, 'urlopen', lambda *a, **k: io.BytesIO(b'tampered'))
    assert bootstrap.main() == 1
    assert not (tmp_path / '.tools/bin/vale').exists()


@pytest.mark.parametrize('url', ['http://github.com/vale-cli/vale/releases/download/a', 'https://untrusted.invalid/vale', 'file:///etc/passwd'])
def test_installer_rejects_unapproved_download_before_request(monkeypatch, tmp_path: Path, url: str) -> None:
    native_fixture(tmp_path, url)
    use_fixture(monkeypatch, tmp_path)
    def unexpected_request(*args, **kwargs):
        pytest.fail('Unsafe URL was fetched')
    monkeypatch.setattr(bootstrap.urllib.request, 'urlopen', unexpected_request)
    assert bootstrap.main() == 1


def test_installer_dns_failure_reports_unavailability(monkeypatch, tmp_path: Path) -> None:
    native_fixture(tmp_path)
    use_fixture(monkeypatch, tmp_path)
    def network_failure(*args, **kwargs):
        raise urllib.error.URLError('DNS unavailable')
    monkeypatch.setattr(bootstrap.urllib.request, 'urlopen', network_failure)
    assert bootstrap.main() == 69


def test_installer_unsupported_platform_does_not_guess_asset(monkeypatch, tmp_path: Path) -> None:
    native_fixture(tmp_path)
    use_fixture(monkeypatch, tmp_path)
    monkeypatch.setattr(bootstrap.platform, 'machine', lambda: 'unknown')
    assert bootstrap.main() == 69


def test_installer_oversized_download_is_integrity_failure(monkeypatch, tmp_path: Path) -> None:
    native_fixture(tmp_path)
    use_fixture(monkeypatch, tmp_path)
    monkeypatch.setattr(bootstrap.urllib.request, 'urlopen', lambda *a, **k: io.BytesIO(b'x'*50_000_001))
    assert bootstrap.main() == 1


@pytest.mark.parametrize('output', ['vale version 3.25.1', 'Vale 3.25.1 (build abc)'])
def test_native_version_contract_accepts_exact_release(monkeypatch, tmp_path: Path, output: str) -> None:
    native_fixture(tmp_path)
    monkeypatch.setattr(checks.subprocess, 'run', lambda *a, **k: SimpleNamespace(returncode=0, stdout=output, stderr=''))
    check = getattr(checks, 'native_version_errors', None)
    assert callable(check), 'Native version gate has not been implemented'
    assert check(tmp_path) == []


@pytest.mark.parametrize('output,code', [('vale version 3.25.10',0), ('vale version 3.25.0',0), ('vale version 3.25.1',1), ('unparseable',0)])
def test_native_version_contract_rejects_wrong_or_failed_release(monkeypatch, tmp_path: Path, output: str, code: int) -> None:
    native_fixture(tmp_path)
    monkeypatch.setattr(checks.subprocess, 'run', lambda *a, **k: SimpleNamespace(returncode=code, stdout=output, stderr=''))
    check = getattr(checks, 'native_version_errors', None)
    assert callable(check), 'Native version gate has not been implemented'
    assert check(tmp_path)


def test_native_version_contract_missing_tool_fails_closed(monkeypatch, tmp_path: Path) -> None:
    native_fixture(tmp_path)
    def missing(*args, **kwargs):
        raise FileNotFoundError('not installed')
    monkeypatch.setattr(checks.subprocess, 'run', missing)
    check = getattr(checks, 'native_version_errors', None)
    assert callable(check), 'Native version gate has not been implemented'
    assert check(tmp_path)
