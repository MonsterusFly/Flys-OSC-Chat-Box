"""Named status profiles and independent monotonic rotation timer."""
from __future__ import annotations

from dataclasses import dataclass
import math
import time


@dataclass
class StatusProfile:
    name: str
    text: str
    enabled: bool = True


class StatusRotator:
    def __init__(self, interval: int = 60):
        self.interval = max(5, int(interval))
        self.next_at: float | None = None
        self.enabled = False

    def configure(self, enabled: bool, interval: int, *, now: float | None = None):
        now = time.monotonic() if now is None else now
        interval = max(5, int(interval))
        changed = (enabled != self.enabled or interval != self.interval)
        self.enabled = enabled
        self.interval = interval
        if not enabled:
            self.next_at = None
        elif changed or self.next_at is None:
            self.next_at = now + interval

    def remaining(self, *, now: float | None = None) -> int | None:
        if self.next_at is None:
            return None
        now = time.monotonic() if now is None else now
        return max(0, math.ceil(self.next_at - now))

    def advance(self, *, now: float | None = None) -> bool:
        now = time.monotonic() if now is None else now
        if self.next_at is None or now < self.next_at:
            return False
        self.next_at = now + self.interval
        return True


def next_enabled_index(profiles: list[StatusProfile], current: int) -> int:
    if not profiles:
        return -1
    for step in range(1, len(profiles) + 1):
        index = (current + step) % len(profiles)
        if profiles[index].enabled:
            return index
    return current
