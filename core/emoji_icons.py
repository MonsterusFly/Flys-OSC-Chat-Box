"""Render emoji icons using Pillow rather than Qt emoji text shaping.

Color emoji fonts often appear blank in Qt QLabel on Linux. Rasterizing with
Pillow and using QLabel pixmaps sidesteps the Qt font fallback path.
"""
from __future__ import annotations

from functools import lru_cache
from io import BytesIO
from pathlib import Path
import subprocess


@lru_cache(maxsize=1)
def emoji_font_path() -> str | None:
    # fc-match chooses the local font; no network call or bundled font needed.
    try:
        result = subprocess.run(
            ["fc-match", "-f", "%{file}", "Noto Color Emoji"],
            capture_output=True, text=True, timeout=3, check=False,
        )
        path = result.stdout.strip()
        if result.returncode == 0 and path and Path(path).is_file() and "emoji" in Path(path).name.lower():
            return path
    except (OSError, subprocess.TimeoutExpired):
        pass
    for candidate in (
        "/usr/share/fonts/google-noto-emoji/NotoColorEmoji.ttf",
        "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
    ):
        if Path(candidate).is_file():
            return candidate
    return None


@lru_cache(maxsize=256)
def emoji_png(emoji: str, size: int = 44) -> bytes | None:
    """Return a transparent PNG of an emoji or None when rendering is unavailable."""
    path = emoji_font_path()
    if not path or not emoji or not 16 <= size <= 128:
        return None
    try:
        from PIL import Image, ImageDraw, ImageFont

        # Noto Color Emoji is a bitmap font and only supports fixed strikes.
        font = None
        for strike in (109, 128, 136, 72, 64):
            try:
                font = ImageFont.truetype(path, strike)
                break
            except OSError:
                continue
        if font is None:
            return None
        canvas = Image.new("RGBA", (384, 192), (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas)
        draw.text((12, 12), emoji, font=font, embedded_color=True)
        bounds = canvas.getbbox()
        if bounds is None:
            return None
        cropped = canvas.crop(bounds)
        cropped.thumbnail((size, size), Image.Resampling.LANCZOS)
        output = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        output.alpha_composite(cropped, ((size-cropped.width)//2, (size-cropped.height)//2))
        blob = BytesIO()
        output.save(blob, format="PNG")
        return blob.getvalue()
    except (ImportError, OSError, ValueError):
        return None
