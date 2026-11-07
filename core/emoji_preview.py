"""Render the bundled emoji PNGs in local previews; OSC still sends Unicode text.

The preview is deliberately separate from the outgoing message. VRChat decides
which Unicode glyphs it can display, and cannot receive images via /chatbox/input.
"""
from html import escape
from .emojis import EMOJIS
from .emoji_assets import emoji_icon_path

SORTED_EMOJI = sorted((emoji for emoji, _ in EMOJIS), key=len, reverse=True)


def rich_emoji_preview(text: str) -> str:
    """Return Qt-compatible rich text, retaining all non-emoji text literally."""
    output = []
    index = 0
    while index < len(text):
        emoji = next((value for value in SORTED_EMOJI if text.startswith(value, index)), None)
        if emoji:
            asset = emoji_icon_path(emoji)
            if asset is not None:
                output.append(f'<img src="{escape(str(asset), quote=True)}" width="20" height="20"/>')
            else:
                output.append(escape(emoji))
            index += len(emoji)
        else:
            char = text[index]
            output.append('<br/>' if char == '\n' else escape(char))
            index += 1
    return '<span style="color:#eaf0fa;">' + ''.join(output) + '</span>'
