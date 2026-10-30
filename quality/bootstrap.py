"""Install pinned native tools locally after checksum verification.

This is an explicit developer maintenance action, not a model import side effect.
It uses only HTTPS release URLs in the checked-in manifest and never extracts
arbitrary paths or executes an installation script from a remote server.
"""

from __future__ import annotations

import hashlib
import io
import json
import platform
import tarfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

if TYPE_CHECKING:
    import http.client
    from urllib.request import Request

ROOT = Path(__file__).resolve().parents[1]
MAX_BINARY_BYTES = 100_000_000
MAX_ARCHIVE_BYTES = 50_000_000
# First printable ASCII ordinal; anything below it is a control character.
MIN_PRINTABLE_ORDINAL = 32
RELEASE_HOSTS = frozenset({"github.com", "release-assets.githubusercontent.com", "objects.githubusercontent.com"})
NATIVE_TOOLS = frozenset({"gitleaks", "vale", "actionlint"})


def validate_release_url(url: str, *, initial: bool = False) -> None:
    """Reject unsafe origins before any request, including redirected requests.

    Raises:
        ValueError: If the URL is not an approved HTTPS release origin.
    """
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname not in RELEASE_HOSTS
        or any((parsed.username, parsed.password, parsed.port))
        or any(ord(character) < MIN_PRINTABLE_ORDINAL for character in url)
    ):
        msg = "Unapproved native download URL"
        raise ValueError(msg)
    if initial and (parsed.hostname != "github.com" or "/releases/download/" not in parsed.path):
        msg = "Unapproved initial native download URL"
        raise ValueError(msg)


class TrustedReleaseRedirect(urllib.request.HTTPRedirectHandler):
    """Check each redirect target before urllib opens the next connection."""

    def redirect_request(  # ruff: ignore[too-many-arguments, too-many-positional-arguments] -- signature must mirror urllib's redirect handler
        self,
        request: Request,
        response: http.client.HTTPResponse,
        code: int,
        message: str,
        headers: http.client.HTTPMessage,
        newurl: str,
    ) -> Request | None:
        """Validate a redirect target before the base handler follows it.

        Returns:
            Request | None: The base handler's follow-up request, when any.
        """
        validate_release_url(newurl)
        return super().redirect_request(request, response, code, message, headers, newurl)


def open_release(url: str) -> http.client.HTTPResponse:
    """Use an instance-local opener; do not mutate global urllib behaviour.

    Returns:
        http.client.HTTPResponse: The open response for the validated release URL.
    """
    validate_release_url(url, initial=True)
    return urllib.request.build_opener(TrustedReleaseRedirect()).open(url, timeout=20)


def unpack_binary(payload: bytes, expected: str, name: str, destination: Path) -> Path:
    """Extract only the exact regular executable from a checksum-matched archive.

    Returns:
        Path: The installed executable path inside `destination`.

    Raises:
        ValueError: If the checksum, tool name, archive contents or size are invalid.
    """
    if hashlib.sha256(payload).hexdigest() != expected:
        msg = "Native archive checksum mismatch"
        raise ValueError(msg)
    if name not in NATIVE_TOOLS:
        msg = "Unknown native tool"
        raise ValueError(msg)
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as archive:
        matches = [item for item in archive.getmembers() if item.name == name and item.isfile()]
        if len(matches) != 1:
            msg = "Archive must contain one exact regular executable"
            raise ValueError(msg)
        if matches[0].size > MAX_BINARY_BYTES:
            msg = "Unexpected executable size"
            raise ValueError(msg)
        stream = archive.extractfile(matches[0])
        if stream is None:
            msg = "Executable cannot be read"
            raise ValueError(msg)
        with stream:
            content = stream.read(MAX_BINARY_BYTES + 1)
        if len(content) > MAX_BINARY_BYTES:
            msg = "Unexpected executable size"
            raise ValueError(msg)
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / name
    target.write_bytes(content)
    target.chmod(0o755)
    return target


def download_archive(asset: dict) -> bytes:
    """Download one checksum-addressed release archive after URL validation.

    Returns:
        bytes: The downloaded archive payload.

    Raises:
        ValueError: If the release URL or the reported archive size is invalid.
    """
    validate_release_url(asset["url"], initial=True)
    with open_release(asset["url"]) as response:
        payload = response.read(MAX_ARCHIVE_BYTES + 1)
    if len(payload) > MAX_ARCHIVE_BYTES:
        msg = "Unexpected archive size"
        raise ValueError(msg)
    return payload


def main() -> int:
    """Download into .tools/bin, without changing the global machine environment.

    Returns:
        int: 0 when all tools install, 1 on a failed install, 69 when blocked.
    """
    manifest = json.loads((ROOT / "quality/native-tools.json").read_text(encoding="utf-8"))
    key = f"{platform.system().lower()}-{platform.machine().lower()}"
    failed = False
    blocked = False
    for name, entries in manifest.items():
        if key not in entries:
            print(f"BLOCKED {name}: platform {key} has no verified binary record")  # ruff: ignore[print] -- install receipt goes to stdout
            blocked = True
            continue
        asset = entries[key]
        try:
            target = unpack_binary(download_archive(asset), asset["sha256"], name, ROOT / ".tools/bin")
            print(f"Installed checksum-verified {name} {entries['version']}: {target}")  # ruff: ignore[print] -- install receipt goes to stdout
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            print(f"BLOCKED {name}: {error}")  # ruff: ignore[print] -- install receipt goes to stdout
            blocked = True
        except (ValueError, tarfile.TarError) as error:
            print(f"FAILED {name}: {error}")  # ruff: ignore[print] -- install receipt goes to stdout
            failed = True
    return 1 if failed else (69 if blocked else 0)


if __name__ == "__main__":
    raise SystemExit(main())
