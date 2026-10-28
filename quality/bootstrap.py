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
        stream = archive.extractfile(matches[0])
        if stream is None:
            raise ValueError('Executable cannot be read')
        with stream:
            content = stream.read()
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
            parsed = urlsplit(asset['url'])
            if (parsed.scheme != 'https' or parsed.hostname != 'github.com'
                    or parsed.username or parsed.password or parsed.port
                    or '/releases/download/' not in parsed.path):
                raise ValueError('Unapproved native download URL')
            with urllib.request.urlopen(asset['url'], timeout=20) as response:
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
