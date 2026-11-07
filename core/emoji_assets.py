"""Pre-rendered emoji assets bundled with the application. No runtime fonts required."""
from pathlib import Path
from .emojis import EMOJIS

_ASSETS = Path(__file__).resolve().parent.parent / "assets" / "emoji"
_INDEX = {emoji: i for i, (emoji, _) in enumerate(EMOJIS)}

def emoji_icon_path(emoji: str) -> Path | None:
    index = _INDEX.get(emoji)
    if index is None:
        return None
    path = _ASSETS / f"{index:03d}.png"
    return path if path.is_file() else None
