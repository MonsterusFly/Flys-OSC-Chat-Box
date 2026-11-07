"""Versioned, backwards-compatible settings in the XDG configuration directory."""
from __future__ import annotations

import json
import os
import shutil
from dataclasses import asdict, dataclass, fields, field
from pathlib import Path

from core.message_engine import DEFAULT_TEMPLATE
from core.status_profiles import StatusProfile
from core.sections import clean_sections
from core.themes import normalize_theme


def config_path() -> Path:
    base = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
    return base / "linux-osc-chatbox" / "settings.json"


@dataclass
class Settings:
    host: str = "127.0.0.1"
    port: int = 9000
    status_text: str = ""
    show_clock: bool = True
    show_system: bool = True
    show_music: bool = False
    show_music_progress: bool = False
    music_player: str = "Auto"
    music_show_paused: bool = False
    music_fallback_to_auto: bool = False
    show_gpu: bool = False
    custom_layouts: dict[str, str] = field(default_factory=dict)
    section_mode: bool = False
    message_sections: list[dict] = field(default_factory=list)
    music_bar_style: str = "Blocks"
    music_bar_filled: str = "◆"
    music_bar_empty: str = "◇"
    music_bar_width: int = 10
    auto_send: bool = False
    only_send_when_changed: bool = False
    auto_interval: int = 20
    minimize_to_tray: bool = True
    template: str = DEFAULT_TEMPLATE
    status_profiles: list[dict] | None = None
    selected_status: int = 0
    rotate_statuses: bool = False
    status_rotation_interval: int = 60
    theme: str = "Midnight Blue"
    check_updates: bool = True
    auto_download_updates: bool = False
    version: int = 10

    @classmethod
    def load(cls, path: Path | None = None) -> "Settings":
        target = path if path is not None else config_path()
        try:
            data = json.loads(target.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("Invalid settings data")
        except FileNotFoundError:
            return cls()
        except (OSError, ValueError, TypeError):
            backup = target.with_suffix(".json.bak")
            try:
                data = json.loads(backup.read_text(encoding="utf-8"))
                if not isinstance(data, dict):
                    raise ValueError("Invalid backup")
            except (OSError, ValueError, TypeError):
                return cls()
        try:
            allowed = {f.name for f in fields(cls)}
            obj = cls(**{k: v for k, v in data.items() if k in allowed})
            obj.port = int(obj.port)
            if not 1 <= obj.port <= 65535:
                obj.port = 9000
            obj.auto_interval = max(10, min(600, int(obj.auto_interval)))
            if obj.music_bar_style not in ("Blocks", "Squares", "Circles", "ASCII", "Custom"):
                obj.music_bar_style = "Blocks"
            obj.music_bar_width = max(3, min(24, int(obj.music_bar_width)))
            obj.music_bar_filled = str(obj.music_bar_filled or "◆")[:4]
            obj.music_bar_empty = str(obj.music_bar_empty or "◇")[:4]
            if not isinstance(obj.music_player, str):
                obj.music_player = "Auto"
            obj.music_player = obj.music_player[:200] or "Auto"
            obj.music_show_paused = bool(obj.music_show_paused)
            obj.music_fallback_to_auto = bool(obj.music_fallback_to_auto)
            obj.show_gpu = bool(obj.show_gpu)
            if not isinstance(obj.custom_layouts, dict):
                obj.custom_layouts = {}
            obj.custom_layouts = {
                name[:60]: body[:4096] for name, body in list(obj.custom_layouts.items())[:100]
                if isinstance(name, str) and name.strip() and isinstance(body, str)
            }
            obj.theme = normalize_theme(obj.theme)
            obj.section_mode = bool(obj.section_mode)
            obj.message_sections = clean_sections(obj.message_sections)
            if not isinstance(obj.template, str):
                obj.template = DEFAULT_TEMPLATE
            if not isinstance(obj.host, str) or not obj.host.strip():
                obj.host = "127.0.0.1"
            if not isinstance(obj.status_text, str):
                obj.status_text = ""
            if obj.status_profiles is None and obj.version < 5:
                obj.status_profiles = [{"name": "Default", "text": obj.status_text, "enabled": True}]
            if obj.status_profiles is not None and not isinstance(obj.status_profiles, list):
                obj.status_profiles = []
            clean = []
            for profile in (obj.status_profiles or [])[:100]:
                if isinstance(profile, dict) and isinstance(profile.get("name"), str) and isinstance(profile.get("text"), str):
                    clean.append({"name": profile["name"][:80], "text": profile["text"][:4096], "enabled": bool(profile.get("enabled", True))})
            obj.status_profiles = clean if obj.status_profiles is not None else None
            obj.selected_status = max(0, min(len(clean) - 1, int(obj.selected_status))) if clean else (0 if obj.status_profiles is None else -1)
            obj.status_rotation_interval = max(5, min(3600, int(obj.status_rotation_interval)))
            obj.rotate_statuses = bool(obj.rotate_statuses)
            obj.check_updates = bool(obj.check_updates)
            obj.auto_download_updates = bool(obj.auto_download_updates)
            return obj
        except (OSError, ValueError, TypeError, OverflowError):
            return cls()

    def save(self, path: Path | None = None) -> None:
        target = path if path is not None else config_path()
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(".tmp")
        tmp.write_text(json.dumps(asdict(self), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        # Never replace the last known good backup with corrupt settings.
        if target.exists():
            try:
                json.loads(target.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                pass
            else:
                shutil.copy2(target, target.with_suffix(".json.bak"))
        tmp.replace(target)
