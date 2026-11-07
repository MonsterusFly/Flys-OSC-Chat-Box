"""Read Linux MPRIS track information and playback progress via playerctl."""
from __future__ import annotations

import math
import shutil
import subprocess
import time
from dataclasses import dataclass, field


def format_time(seconds: float) -> str:
    """Format a nonnegative playback position as M:SS or H:MM:SS."""
    value = max(0, int(seconds))
    hours, remainder = divmod(value, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes}:{secs:02d}"


@dataclass(frozen=True)
class Track:
    artist: str = ""
    title: str = ""
    player: str = ""
    art_url: str = ""
    playing: bool = False
    position_seconds: float = 0.0
    duration_seconds: float = 0.0
    sampled_at: float = field(default_factory=time.monotonic)

    @property
    def display(self) -> str:
        if not self.title:
            return ""
        return f"{self.artist} - {self.title}" if self.artist else self.title

    @property
    def has_progress(self) -> bool:
        return self.duration_seconds > 0 and math.isfinite(self.duration_seconds)

    def elapsed(self, *, now: float | None = None) -> float:
        if not self.has_progress:
            return 0.0
        elapsed = self.position_seconds
        if self.playing:
            elapsed += max(0.0, (time.monotonic() if now is None else now) - self.sampled_at)
        return max(0.0, min(self.duration_seconds, elapsed))

    def progress(self, *, now: float | None = None) -> float:
        return self.elapsed(now=now) / self.duration_seconds if self.has_progress else 0.0

    def progress_text(self, *, now: float | None = None) -> str:
        if not self.has_progress:
            return ""
        return f"{format_time(self.elapsed(now=now))} / {format_time(self.duration_seconds)}"

    def progress_bar(self, *, width: int = 10, now: float | None = None) -> str:
        if not self.has_progress:
            return ""
        filled = max(0, min(width, int(self.progress(now=now) * width)))
        return "▰" * filled + "▱" * (width - filled)


def _playerctl(*args: str) -> str:
    if not shutil.which("playerctl"):
        return ""
    try:
        result = subprocess.run(
            ["playerctl", *args], capture_output=True, text=True,
            timeout=1.2, check=False,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def _number(value: str) -> float:
    try:
        number = float(value)
        return number if math.isfinite(number) and number > 0 else 0.0
    except (ValueError, TypeError):
        return 0.0


def list_players() -> list[str]:
    """Discover MPRIS instance names including separate browser instances."""
    return list(dict.fromkeys(p.strip() for p in _playerctl("-l").splitlines() if p.strip()))


def choose_player(players: list[str], requested: str, status: dict[str, str]) -> str:
    """Manual selection is strict; Auto prefers playing, then first available."""
    if requested and requested != "Auto":
        return requested if requested in players else ""
    return next((p for p in players if status.get(p) == "Playing"), players[0] if players else "")


def current_track(player_name: str = "Auto", fallback_to_auto: bool = False) -> Track:
    """Prefer a playing MPRIS player; display paused metadata too.

    MPRIS length is measured in microseconds, whereas `playerctl position`
    reports seconds. Some players omit length or do not support position.
    """
    players = list_players()
    statuses = {p: _playerctl("-p", p, "status") for p in players}
    selected = choose_player(players, player_name, statuses)
    if not selected and fallback_to_auto and player_name != "Auto":
        selected = choose_player(players, "Auto", statuses)
    playing = statuses.get(selected) == "Playing"
    if not selected:
        return Track()
    metadata = _playerctl(
        "-p", selected, "metadata", "--format",
        "{{title}}\t{{artist}}\t{{mpris:length}}\t{{mpris:artUrl}}",
    ).split("\t")
    title = metadata[0] if metadata else ""
    artist = metadata[1] if len(metadata) >= 2 else ""
    duration = _number(metadata[2]) / 1_000_000 if len(metadata) >= 3 else 0.0
    art_url = metadata[3].strip() if len(metadata) >= 4 else ""
    position = _number(_playerctl("-p", selected, "position")) if duration else 0.0
    return Track(
        artist=artist.replace("\n", " ")[:80],
        title=title.replace("\n", " ")[:80],
        player=selected,
        art_url=art_url,
        playing=playing,
        duration_seconds=duration,
        position_seconds=min(duration, position) if duration else 0.0,
        sampled_at=time.monotonic(),
    )


def now_playing() -> str:
    track = current_track()
    return track.display if track.playing else ""


def control_player(player: str, action: str) -> bool:
    """Control a specifically selected MPRIS player (never shell out)."""
    if action not in {"play-pause", "next", "previous"} or not player or not shutil.which("playerctl"):
        return False
    try:
        result = subprocess.run(["playerctl", "-p", player, action], capture_output=True, timeout=2, check=False)
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def styled_progress_bar(track: Track, style: str = "Blocks", width: int = 10, filled_char: str = "◆", empty_char: str = "◇") -> str:
    if not track.has_progress:
        return ""
    symbols = {"Blocks": ("▰", "▱"), "Squares": ("■", "□"), "Circles": ("●", "○"), "ASCII": ("#", "-")}
    filled, empty = (filled_char or "◆", empty_char or "◇") if style == "Custom" else symbols.get(style, symbols["Blocks"])
    width = max(3, min(24, int(width)))
    count = max(0, min(width, int(track.progress() * width)))
    return filled * count + empty * (width - count)
