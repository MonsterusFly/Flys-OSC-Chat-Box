"""Portable settings backups: validate before importing, never overwrite blindly."""
from __future__ import annotations
import json
import os
from pathlib import Path
from datetime import datetime, timezone
from core.settings import Settings, config_path

FORMAT = "flys-osc-chat-box-backup-v1"

def export_backup(destination: Path, settings: Settings) -> Path:
    destination = Path(destination)
    payload = {"format": FORMAT, "exported_at": datetime.now(timezone.utc).isoformat(), "settings": __import__("dataclasses").asdict(settings)}
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp = destination.with_name(destination.name + ".tmp")
    try:
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp.replace(destination)
    finally:
        tmp.unlink(missing_ok=True)
    return destination

def inspect_backup(source: Path) -> dict:
    if source.stat().st_size > 2_000_000:
        raise ValueError("Backup exceeds the 2 MB size limit")
    data = json.loads(Path(source).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("format") != FORMAT or not isinstance(data.get("settings"), dict):
        raise ValueError("Not a Fly's OSC Chat Box backup")
    settings = data["settings"]
    if "status_profiles" not in settings or "template" not in settings:
        raise ValueError("Backup is missing required settings fields")
    return settings

def restore_backup(source: Path, target: Path | None = None) -> Settings:
    target = target or config_path()
    raw = inspect_backup(source)
    # Settings.load performs all existing validation and backwards-compatibility handling.
    import tempfile
    with tempfile.TemporaryDirectory() as temp:
        staging = Path(temp) / "settings.json"
        staging.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
        validated = Settings.load(staging)
    # Preserve a separate, timestamped pre-import snapshot for rollback.
    if target.exists():
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
        rescue = target.with_name(f"settings.pre-import-{stamp}.json")
        rescue.write_bytes(target.read_bytes())
    validated.save(target)
    return validated
