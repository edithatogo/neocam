"""Exercise installer integrity without claiming a live binary/tool execution."""

from __future__ import annotations

import hashlib
import io
import json
import platform
import subprocess  # ruff: ignore[suspicious-subprocess-import] -- the native version gate invokes pinned tools
import urllib.error
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

import pytest

from quality import bootstrap, checks
from tests.test_quality_gates import binary_tar

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


def native_fixture(
    root: Path, url: str = "https://github.com/vale-cli/vale/releases/download/v3.25.1/vale.tar.gz"
) -> bytes:
    payload = binary_tar()
    (root / "quality").mkdir()
    manifest = {"vale": {"version": "3.25.1", "test-test": {"url": url, "sha256": hashlib.sha256(payload).hexdigest()}}}
    _ = (root / "quality/native-tools.json").write_text(json.dumps(manifest), encoding="utf-8")
    return payload


def use_fixture(monkeypatch: pytest.MonkeyPatch, root: Path) -> None:
    monkeypatch.setattr(bootstrap, "ROOT", root)
    monkeypatch.setattr(platform, "system", lambda: "Test")
    monkeypatch.setattr(platform, "machine", lambda: "Test")


def test_installer_matching_digest_installs_only_local_binary(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    payload = native_fixture(tmp_path)
    use_fixture(monkeypatch, tmp_path)

    def open_release(*_args: object, **_kwargs: object) -> io.BytesIO:
        return io.BytesIO(payload)

    monkeypatch.setattr(bootstrap, "open_release", open_release)
    assert bootstrap.main() == 0
    assert (tmp_path / ".tools/bin/vale").read_bytes() == b"binary"


def test_installer_checksum_failure_is_failure_not_unavailability(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _ = native_fixture(tmp_path)
    use_fixture(monkeypatch, tmp_path)

    def open_release(*_args: object, **_kwargs: object) -> io.BytesIO:
        return io.BytesIO(b"tampered")

    monkeypatch.setattr(bootstrap, "open_release", open_release)
    assert bootstrap.main() == 1
    assert not (tmp_path / ".tools/bin/vale").exists()


@pytest.mark.parametrize(
    "url",
    ["http://github.com/vale-cli/vale/releases/download/a", "https://untrusted.invalid/vale", "file:///etc/passwd"],
)
def test_installer_rejects_unapproved_download_before_request(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, url: str
) -> None:
    _ = native_fixture(tmp_path, url)
    use_fixture(monkeypatch, tmp_path)

    def unexpected_request(*_args: object, **_kwargs: object) -> None:
        pytest.fail("Unsafe URL was fetched")

    monkeypatch.setattr(bootstrap, "open_release", unexpected_request)
    assert bootstrap.main() == 1


def test_installer_dns_failure_reports_unavailability(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _ = native_fixture(tmp_path)
    use_fixture(monkeypatch, tmp_path)

    def network_failure(*_args: object, **_kwargs: object) -> None:
        msg = "DNS unavailable"
        raise urllib.error.URLError(msg)

    monkeypatch.setattr(bootstrap, "open_release", network_failure)
    assert bootstrap.main() == 69


def test_installer_unsupported_platform_does_not_guess_asset(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _ = native_fixture(tmp_path)
    use_fixture(monkeypatch, tmp_path)
    monkeypatch.setattr(platform, "machine", lambda: "unknown")
    assert bootstrap.main() == 69


def test_installer_oversized_download_is_integrity_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _ = native_fixture(tmp_path)
    use_fixture(monkeypatch, tmp_path)

    def open_release(*_args: object, **_kwargs: object) -> io.BytesIO:
        return io.BytesIO(b"x" * 50_000_001)

    monkeypatch.setattr(bootstrap, "open_release", open_release)
    assert bootstrap.main() == 1


@pytest.mark.parametrize("output", ["vale version 3.25.1", "Vale 3.25.1 (build abc)"])
def test_native_version_contract_accepts_exact_release(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, output: str
) -> None:
    _ = native_fixture(tmp_path)

    def fake_run(*_args: object, **_kwargs: object) -> SimpleNamespace:
        return SimpleNamespace(returncode=0, stdout=output, stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    check = cast("Callable[..., list[str]]", getattr(checks, "native_version_errors", None))
    assert callable(check), "Native version gate has not been implemented"
    assert check(tmp_path) == []


@pytest.mark.parametrize(
    ("output", "code"),
    [("vale version 3.25.10", 0), ("vale version 3.25.0", 0), ("vale version 3.25.1", 1), ("unparseable", 0)],
)
def test_native_version_contract_rejects_wrong_or_failed_release(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, output: str, code: int
) -> None:
    _ = native_fixture(tmp_path)

    def fake_run(*_args: object, **_kwargs: object) -> SimpleNamespace:
        return SimpleNamespace(returncode=code, stdout=output, stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    check = cast("Callable[..., list[str]]", getattr(checks, "native_version_errors", None))
    assert callable(check), "Native version gate has not been implemented"
    assert check(tmp_path)


def test_native_version_contract_missing_tool_fails_closed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _ = native_fixture(tmp_path)

    def missing(*_args: object, **_kwargs: object) -> None:
        msg = "not installed"
        raise FileNotFoundError(msg)

    monkeypatch.setattr(subprocess, "run", missing)
    check = cast("Callable[..., list[str]]", getattr(checks, "native_version_errors", None))
    assert callable(check), "Native version gate has not been implemented"
    assert check(tmp_path)
