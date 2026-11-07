"""Safe local album artwork lookup. Remote URLs are intentionally never fetched."""
from __future__ import annotations
from pathlib import Path
from urllib.parse import urlparse, unquote

def local_album_art(url: str) -> Path | None:
    if not url or len(url) > 4096:
        return None
    parsed = urlparse(url)
    if parsed.scheme != 'file' or parsed.netloc not in ('', 'localhost'):
        return None
    path = Path(unquote(parsed.path))
    try:
        if path.is_file() and path.suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp') and path.stat().st_size <= 10_000_000:
            return path
    except OSError:
        pass
    return None
