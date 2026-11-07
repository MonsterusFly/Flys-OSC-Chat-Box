"""Safe template-based VRChat chatbox composition."""
from __future__ import annotations

import re
from datetime import datetime

MAX_CHARS = 144
DEFAULT_TEMPLATE = "{status}\n{music}\n{system}\n{time}"
PRESETS = {
    "Full status": DEFAULT_TEMPLATE,
    "Compact": "{status} | {music} | {system} | {time}",
    "Music focus": "{status}\n{music}",
    "Music progress": "{music}\n{music_bar} {music_progress}",
    "System focus": "{status}\n{system} | {time}",
    "Custom status": "{status}",
}
SUPPORTED_VARIABLES = ("status", "music", "system", "time", "cpu", "ram", "artist", "title", "gpu", "gpu_usage", "gpu_temp", "vram", "music_progress", "music_bar", "music_with_progress", "position", "duration", "music_bar_custom")
TOKEN_RE = re.compile(r"\{([A-Za-z_][A-Za-z_0-9]*)\}")


def clamp_message(message: str, max_chars: int = MAX_CHARS) -> str:
    return message[:max_chars]


def unknown_variables(template: str) -> set[str]:
    return {match.group(1) for match in TOKEN_RE.finditer(template)} - set(SUPPORTED_VARIABLES)


def render_template(template: str, variables: dict[str, str], *, limit: int = MAX_CHARS) -> str:
    """Replace known tokens, remove empty lines/segments, and apply the OSC limit.

    Unknown tokens remain visible so user typos are obvious in the preview.
    """
    values = {key: str(variables.get(key, "")) for key in SUPPORTED_VARIABLES}
    result = TOKEN_RE.sub(lambda m: values.get(m.group(1), m.group(0)), template)
    lines = []
    for line in result.splitlines():
        # Remove empty pipe-separated segments (common in compact presets).
        chunks = [piece.strip() for piece in line.split("|") if piece.strip()]
        if chunks:
            lines.append(" | ".join(chunks))
    return clamp_message("\n".join(lines), limit)


def compose(status: str, *, clock: bool = False, system: str = "", music: str = "", now: datetime | None = None) -> str:
    """Backward-compatible v0.1 composer."""
    sections = [status.strip()]
    if music:
        sections.append("♫ " + music.strip())
    if system:
        sections.append(system.strip())
    if clock:
        sections.append((now or datetime.now()).strftime("%H:%M"))
    return clamp_message(" | ".join(section for section in sections if section))
