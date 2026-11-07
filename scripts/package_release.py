#!/usr/bin/env python3
"""Make deterministic, source-only portable archives. Does not include user data."""
from pathlib import Path
import argparse
import zipfile
import tarfile

ROOT = Path(__file__).resolve().parents[1]
EXCLUDE_DIRS = {'.git', '.venv', '__pycache__', '.pytest_cache', 'dist', 'build'}
EXCLUDE_SUFFIXES = {'.pyc', '.pyo'}

def files():
    return sorted(p for p in ROOT.rglob('*') if p.is_file()
                  and not any(part in EXCLUDE_DIRS for part in p.relative_to(ROOT).parts)
                  and p.suffix not in EXCLUDE_SUFFIXES
                  and not p.name.endswith('.bak'))

def pack(version):
    dist = ROOT / 'dist'
    dist.mkdir(exist_ok=True)
    base = f'Flys-OSC-Chat-Box-{version}'
    paths = files()
    zpath = dist / f'{base}.zip'
    tpath = dist / f'{base}.tar.gz'
    with zipfile.ZipFile(zpath, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for p in paths:
            rel = f'{base}/{p.relative_to(ROOT).as_posix()}'
            info = zipfile.ZipInfo(rel, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o755 if p.stat().st_mode & 0o111 else 0o644) << 16
            z.writestr(info, p.read_bytes())
    with tarfile.open(tpath, 'w:gz') as t:
        for p in paths:
            t.add(p, arcname=f'{base}/{p.relative_to(ROOT).as_posix()}')
    return zpath, tpath

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('version', nargs='?', default='v1.1.0')
    args = parser.parse_args()
    for p in pack(args.version):
        print(p)
