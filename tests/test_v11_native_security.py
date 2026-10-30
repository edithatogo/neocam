"""Exercise installer trust boundaries without claiming a live download."""

import hashlib
import io
import urllib.request
from http.client import HTTPMessage
from pathlib import Path
from typing import Protocol, cast

import pytest

from quality import bootstrap
from tests.test_quality_gates import binary_tar


class TrustedRedirect(Protocol):
    """The redirect policy surface the installer must expose."""

    def redirect_request(  # ruff: ignore[too-many-arguments, too-many-positional-arguments] -- mirrors the urllib redirect handler contract
        self,
        req: urllib.request.Request,
        fp: io.BytesIO,
        code: int,
        msg: str,
        headers: HTTPMessage,
        newurl: str,
    ) -> urllib.request.Request | None:
        """Return the followed request, or raise for an unapproved host."""
        ...


@pytest.mark.parametrize(
    "url",
    [
        "https://untrusted.invalid/binary",
        "http://release-assets.githubusercontent.com/binary",
        "https://user:password@github.com/binary",
        "https://release-assets.githubusercontent.com:444/binary",
    ],
)
def test_native_redirect_denied_before_follow(url: str) -> None:
    handler_type = cast("type[TrustedRedirect] | None", getattr(bootstrap, "TrustedReleaseRedirect", None))
    assert handler_type is not None, "Native download lacks a redirect policy"
    request = urllib.request.Request("https://github.com/a/b/releases/download/v1/tool")
    with pytest.raises(ValueError, match="URL"):
        _ = handler_type().redirect_request(request, io.BytesIO(b""), 302, "Found", HTTPMessage(), url)


def test_native_github_asset_redirect_is_allowed() -> None:
    handler_type = cast("type[TrustedRedirect] | None", getattr(bootstrap, "TrustedReleaseRedirect", None))
    assert handler_type is not None
    request = urllib.request.Request("https://github.com/a/b/releases/download/v1/tool")
    response = handler_type().redirect_request(
        request, io.BytesIO(b""), 302, "Found", HTTPMessage(), "https://release-assets.githubusercontent.com/a/b"
    )
    assert response is not None
    assert response.full_url == "https://release-assets.githubusercontent.com/a/b"


def test_extracted_executable_has_size_limit(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(bootstrap, "MAX_BINARY_BYTES", 3, raising=False)
    payload = binary_tar()
    with pytest.raises(ValueError, match="size"):
        _ = bootstrap.unpack_binary(payload, hashlib.sha256(payload).hexdigest(), "vale", tmp_path)
    assert not (tmp_path / "vale").exists()
