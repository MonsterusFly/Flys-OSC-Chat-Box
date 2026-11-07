"""Validated drag-and-drop sections and independent per-section text rotation."""
from __future__ import annotations
from dataclasses import dataclass
import time
from core.message_engine import MAX_CHARS, render_template

SECTION_PRESETS = {
    "Gaming": [
        {"name": "Status", "text": "🎮 {status}", "enabled": True, "interval": 0},
        {"name": "Hardware", "text": "{system}", "enabled": True, "interval": 0},
        {"name": "Clock", "text": "{time}", "enabled": True, "interval": 0}],
    "Music": [
        {"name": "Now playing", "text": "{music}", "enabled": True, "interval": 0},
        {"name": "Progress", "text": "{music_bar} {music_progress}", "enabled": True, "interval": 0},
        {"name": "Status", "text": "{status}", "enabled": True, "interval": 0}],
    "AFK": [
        {"name": "Away", "text": "💤 {status}", "enabled": True, "interval": 0},
        {"name": "Clock", "text": "{time}", "enabled": True, "interval": 0}],
}


def _interval(value):
    try:
        return max(0, min(3600, int(value or 0)))
    except (TypeError, ValueError, OverflowError):
        return 0


def clean_sections(items):
    if not isinstance(items, list):
        return []
    result = []
    for item in items[:40]:
        if not isinstance(item, dict):
            continue
        raw_options = item.get('options', [])
        if isinstance(raw_options, str):
            raw_options = raw_options.splitlines()
        if not isinstance(raw_options, list):
            raw_options = []
        options = [str(o)[:1024] for o in raw_options[:20] if isinstance(o, str) and o.strip()]
        result.append({
            'name': str(item.get('name', 'Section'))[:80] or 'Section',
            'text': str(item.get('text', ''))[:1024],
            'enabled': bool(item.get('enabled', True)),
            'interval': _interval(item.get('interval', 0)),
            'options': options,
        })
    return result


class SectionComposer:
    def __init__(self):
        self.started = time.monotonic()

    def render(self, sections, variables, now=None):
        moment = time.monotonic() if now is None else now
        lines = []
        for section in clean_sections(sections):
            if not section['enabled']:
                continue
            options = section['options'] or [section['text']]
            if section['interval'] > 0 and len(options) > 1:
                index = max(0, int((moment - self.started) // section['interval'])) % len(options)
            else:
                index = 0
            value = render_template(options[index], variables, limit=4096)
            if value:
                lines.append(value)
        return '\n'.join(lines)[:MAX_CHARS]
