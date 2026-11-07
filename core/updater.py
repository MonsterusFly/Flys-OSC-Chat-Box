"""Explicit, checksum-verified GitHub release updates for Fedora RPM installations."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

APP_VERSION = "1.3.1"
RELEASE_API = "https://api.github.com/repos/MonsterusFly/Flys-OSC-Chat-Box/releases/latest"
RELEASES_URL = "https://github.com/MonsterusFly/Flys-OSC-Chat-Box/releases"
MAX_JSON = 1024 * 1024
MAX_RPM = 80 * 1024 * 1024
MAX_RELEASE_NOTES = 1200


class UpdateCheckError(RuntimeError):
    """User-facing network or repository-access error."""


def explain_update_error(exc: Exception) -> str:
    if isinstance(exc, HTTPError):
        if exc.code == 404:
            return ("GitHub could not find a public latest release (HTTP 404). "
                    "If the repository is private, the public updater cannot access it. "
                    "Make the release public when ready, or use GitHub manually.")
        if exc.code == 403:
            return "GitHub refused this request (HTTP 403), possibly due to rate limiting. Try again later."
        return f"GitHub returned HTTP {exc.code}. Try again later."
    if isinstance(exc, (URLError, TimeoutError, ConnectionError)):
        return "Cannot reach GitHub. Check your network connection and try again."
    return str(exc)


def human_size(size: int | None) -> str:
    if not isinstance(size, int) or size < 0:
        return "unknown size"
    return f"{size / (1024 * 1024):.1f} MiB"


def clean_release_notes(value: object) -> str:
    if not isinstance(value, str):
        return "No release notes provided."
    # Plain-text Qt labels; never render release-provided HTML/Markdown as rich text.
    value = ''.join(ch for ch in value if ch in '\n\t' or ch.isprintable()).strip()
    return (value[:MAX_RELEASE_NOTES] + '…') if len(value) > MAX_RELEASE_NOTES else (value or 'No release notes provided.')



def version_tuple(value: str) -> tuple[int, int, int]:
    m = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", value.strip())
    if not m:
        raise ValueError("Unexpected release version")
    return tuple(int(m.group(i)) for i in (1, 2, 3))


def installed_via_rpm() -> bool:
    return (Path(__file__).resolve().is_relative_to('/usr/share/flys-osc-chat-box')
            and shutil.which('rpm') is not None and subprocess.run(
        ['rpm', '-q', 'flys-osc-chat-box'], capture_output=True, timeout=5, check=False
    ).returncode == 0)


def fedora_version() -> str | None:
    try:
        contents = Path('/etc/os-release').read_text(encoding='utf-8')
        values = dict(line.split('=', 1) for line in contents.splitlines() if '=' in line)
        if values.get('ID', '').strip('"') != 'fedora':
            return None
        number = values.get('VERSION_ID', '').strip('"')
        return number if number.isdecimal() else None
    except OSError:
        return None


def _fetch_json(url: str) -> dict:
    req = Request(url, headers={'User-Agent': 'Flys-OSC-Chat-Box-updater', 'Accept': 'application/vnd.github+json'})
    with urlopen(req, timeout=12) as response:
        payload = response.read(MAX_JSON + 1)
    if len(payload) > MAX_JSON:
        raise ValueError('GitHub response too large')
    data = json.loads(payload)
    if not isinstance(data, dict):
        raise ValueError('Unexpected GitHub response')
    return data


def _asset_url(item: dict) -> str:
    url = item.get('browser_download_url', '')
    if not isinstance(url, str) or not url.startswith('https://github.com/MonsterusFly/Flys-OSC-Chat-Box/releases/download/'):
        raise ValueError('Release asset is not hosted at the expected GitHub repository')
    return url


def check_release(current: str = APP_VERSION) -> dict | None:
    try:
        data = _fetch_json(RELEASE_API)
    except (HTTPError, URLError, TimeoutError, ConnectionError) as exc:
        raise UpdateCheckError(explain_update_error(exc)) from exc
    if data.get('draft') or data.get('prerelease'):
        return None
    tag = data.get('tag_name', '')
    if version_tuple(tag) <= version_tuple(current):
        return None
    assets = {x.get('name'): x for x in data.get('assets', []) if isinstance(x, dict)}
    rpm = None
    checksum = None
    fedora = fedora_version()
    if fedora:
        pattern = re.compile(rf'flys-osc-chat-box-{re.escape(tag.lstrip("v"))}-[^/]+\.fc{re.escape(fedora)}\.noarch\.rpm')
        for name, item in assets.items():
            if isinstance(name, str) and pattern.fullmatch(name):
                rpm = item
                checksum = assets.get(name + '.sha256')
                break
    url = data.get('html_url', RELEASES_URL)
    if not isinstance(url, str) or not url.startswith(RELEASES_URL):
        url = RELEASES_URL
    return {
        'version': tag.lstrip('v'), 'url': url,
        'rpm_name': rpm.get('name') if rpm else None,
        'rpm_url': _asset_url(rpm) if rpm else None,
        'checksum_url': _asset_url(checksum) if checksum else None,
        'rpm_size': rpm.get('size') if rpm else None,
        'notes': clean_release_notes(data.get('body')),
        'published_at': data.get('published_at') if isinstance(data.get('published_at'), str) else '',
    }


def download_verified_rpm(release: dict) -> Path:
    """Fetch release RPM and separately published SHA-256 sidecar, never execute it."""
    name = release.get('rpm_name')
    if not name or not re.fullmatch(r'flys-osc-chat-box-[A-Za-z0-9._-]+\.rpm', name):
        raise ValueError('No compatible Fedora RPM found for this release')
    if not release.get('checksum_url'):
        raise ValueError('RPM checksum not published; use GitHub release page to update manually')
    checksum_url = release['checksum_url']
    rpm_url = release['rpm_url']
    _asset_url({'browser_download_url': checksum_url})
    _asset_url({'browser_download_url': rpm_url})
    req = Request(checksum_url, headers={'User-Agent': 'Flys-OSC-Chat-Box-updater'})
    with urlopen(req, timeout=20) as response:
        line = response.read(500).decode('ascii').strip()
    match = re.fullmatch(r'([0-9a-fA-F]{64})  \*?(.+)', line)
    if not match or match.group(2) != name:
        raise ValueError('RPM checksum file is invalid or mismatched')
    base = Path(os.environ.get('XDG_CACHE_HOME', str(Path.home() / '.cache'))) / 'flys-osc-chat-box' / 'updates'
    base.mkdir(parents=True, exist_ok=True, mode=0o700)
    # Shared system-installed code must never trust arbitrary cached update contents.
    # Every download is re-hashed against the official sidecar before use.
    fd, tmp = tempfile.mkstemp(prefix='.download-', dir=base)
    dest = base / name
    digest = hashlib.sha256()
    total = 0
    try:
        with os.fdopen(fd, 'wb') as out:
            req = Request(rpm_url, headers={'User-Agent': 'Flys-OSC-Chat-Box-updater'})
            with urlopen(req, timeout=45) as response:
                while True:
                    chunk = response.read(256 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > MAX_RPM:
                        raise ValueError('RPM exceeds maximum download size')
                    digest.update(chunk)
                    out.write(chunk)
        if digest.hexdigest().lower() != match.group(1).lower():
            raise ValueError('RPM checksum verification failed')
        os.replace(tmp, dest)
        return dest
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def rpm_install_command(rpm_path: Path) -> list[str]:
    """Run only after explicit confirmation. Polkit requests admin authentication."""
    if not installed_via_rpm():
        raise RuntimeError('Automatic RPM installation is only available for RPM installations')
    if not rpm_path.is_file() or not rpm_path.name.endswith('.rpm'):
        raise ValueError('The verified RPM file is missing')
    if not shutil.which('pkexec'):
        raise RuntimeError('pkexec is unavailable; install the RPM through Discover')
    dnf = shutil.which('dnf5') or shutil.which('dnf')
    if not dnf or not Path(dnf).is_absolute():
        raise RuntimeError('Fedora DNF was not found')
    return ['pkexec', dnf, 'install', '-y', str(rpm_path.resolve())]
