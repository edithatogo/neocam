"""Exercise installer trust boundaries without claiming a live download."""

import hashlib
import urllib.request

import pytest

from quality import bootstrap
from tests.test_quality_gates import binary_tar


@pytest.mark.parametrize(
    "url",
    [
        "https://untrusted.invalid/binary",
        "http://release-assets.githubusercontent.com/binary",
        "https://user:password@github.com/binary",
        "https://release-assets.githubusercontent.com:444/binary",
    ],
)
def test_native_redirect_denied_before_follow(url):
    handler_type = getattr(bootstrap, "TrustedReleaseRedirect", None)
    assert handler_type is not None, "Native download lacks a redirect policy"
    request = urllib.request.Request("https://github.com/a/b/releases/download/v1/tool")
    with pytest.raises(ValueError, match="URL"):
        handler_type().redirect_request(request, None, 302, "Found", {}, url)


def test_native_github_asset_redirect_is_allowed():
    handler_type = getattr(bootstrap, "TrustedReleaseRedirect", None)
    assert handler_type is not None
    request = urllib.request.Request("https://github.com/a/b/releases/download/v1/tool")
    response = handler_type().redirect_request(
        request, None, 302, "Found", {}, "https://release-assets.githubusercontent.com/a/b"
    )
    assert response.full_url == "https://release-assets.githubusercontent.com/a/b"


def test_extracted_executable_has_size_limit(monkeypatch, tmp_path):
    monkeypatch.setattr(bootstrap, "MAX_BINARY_BYTES", 3, raising=False)
    payload = binary_tar()
    with pytest.raises(ValueError, match="size"):
        bootstrap.unpack_binary(payload, hashlib.sha256(payload).hexdigest(), "vale", tmp_path)
    assert not (tmp_path / "vale").exists()
