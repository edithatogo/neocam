"""Install pinned native tools locally after checksum verification.

This is an explicit developer maintenance action, not a model import side effect.
It uses only HTTPS release URLs in the checked-in manifest and never extracts
arbitrary paths or executes an installation script from a remote server.
"""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import platform
import tarfile
import urllib.error
import urllib.request
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
MAX_BINARY_BYTES = 100_000_000
RELEASE_HOSTS = frozenset({'github.com', 'release-assets.githubusercontent.com', 'objects.githubusercontent.com'})


def validate_release_url(url: str, *, initial: bool = False) -> None:
    """Reject unsafe origins before any request, including redirected requests."""
    parsed = urlsplit(url)
    if (parsed.scheme != 'https' or parsed.hostname not in RELEASE_HOSTS
            or parsed.username or parsed.password or parsed.port
            or any(ord(character) < 32 for character in url)):
        raise ValueError('Unapproved native download URL')
    if initial and (parsed.hostname != 'github.com' or '/releases/download/' not in parsed.path):
        raise ValueError('Unapproved initial native download URL')


class TrustedReleaseRedirect(urllib.request.HTTPRedirectHandler):
    """Check each redirect target before urllib opens the next connection."""

    def redirect_request(self, request, response, code, message, headers, newurl):
        validate_release_url(newurl)
        return super().redirect_request(request, response, code, message, headers, newurl)


def open_release(url: str):
    """Use an instance-local opener; do not mutate global urllib behaviour."""
    validate_release_url(url, initial=True)
    return urllib.request.build_opener(TrustedReleaseRedirect()).open(url, timeout=20)


def unpack_binary(payload: bytes, expected: str, name: str, destination: Path) -> Path:
    """Extract only the exact regular executable from a checksum-matched archive."""
    if hashlib.sha256(payload).hexdigest() != expected:
        raise ValueError('Native archive checksum mismatch')
    if name not in {'gitleaks', 'vale', 'actionlint'}:
        raise ValueError('Unknown native tool')
    with tarfile.open(fileobj=io.BytesIO(payload), mode='r:gz') as archive:
        matches = [item for item in archive.getmembers() if item.name == name and item.isfile()]
        if len(matches) != 1:
            raise ValueError('Archive must contain one exact regular executable')
        if matches[0].size > MAX_BINARY_BYTES:
            raise ValueError('Unexpected executable size')
        stream = archive.extractfile(matches[0])
        if stream is None:
            raise ValueError('Executable cannot be read')
        with stream:
            content = stream.read(MAX_BINARY_BYTES + 1)
        if len(content) > MAX_BINARY_BYTES:
            raise ValueError('Unexpected executable size')
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / name
    target.write_bytes(content)
    target.chmod(0o755)
    return target


def main() -> int:
    """Download into .tools/bin, without changing the global machine environment."""
    manifest = json.loads((ROOT / 'quality/native-tools.json').read_text(encoding='utf-8'))
    key = f'{platform.system().lower()}-{platform.machine().lower()}'
    failed = False
    blocked = False
    for name, entries in manifest.items():
        if key not in entries:
            print(f'BLOCKED {name}: platform {key} has no verified binary record')
            blocked = True
            continue
        asset = entries[key]
        try:
            validate_release_url(asset['url'], initial=True)
            with open_release(asset['url']) as response:
                payload = response.read(50_000_001)
            if len(payload) > 50_000_000:
                raise ValueError('Unexpected archive size')
            target = unpack_binary(payload, asset['sha256'], name, ROOT / '.tools/bin')
            print(f'Installed checksum-verified {name} {entries["version"]}: {target}')
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            print(f'BLOCKED {name}: {error}')
            blocked = True
        except (ValueError, tarfile.TarError) as error:
            print(f'FAILED {name}: {error}')
            failed = True
    return 1 if failed else (69 if blocked else 0)


if __name__ == '__main__':
    raise SystemExit(main())
