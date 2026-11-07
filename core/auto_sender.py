"""Pure scheduling state for repeatable automatic OSC sends.

Qt timers wake this scheduler; the clock is monotonic so wall-clock changes do
not unexpectedly reset the schedule. GUI code handles dispatch and rendering.
"""
from __future__ import annotations

import math
import time


class AutoSendScheduler:
    def __init__(self, interval_seconds: int = 20):
        self.interval_seconds = max(1, int(interval_seconds))
        self.enabled = False
        self.next_send_at: float | None = None

    def configure(self, enabled: bool, interval_seconds: int, *, now: float | None = None) -> None:
        now = time.monotonic() if now is None else now
        interval = max(1, int(interval_seconds))
        changed = enabled != self.enabled or interval != self.interval_seconds
        self.enabled = enabled
        self.interval_seconds = interval
        if not enabled:
            self.next_send_at = None
        elif changed or self.next_send_at is None:
            self.next_send_at = now + interval

    def seconds_remaining(self, *, now: float | None = None) -> int | None:
        if self.next_send_at is None:
            return None
        now = time.monotonic() if now is None else now
        return max(0, math.ceil(self.next_send_at - now))

    def due(self, *, now: float | None = None) -> bool:
        now = time.monotonic() if now is None else now
        return self.next_send_at is not None and now >= self.next_send_at

    def advance(self, *, now: float | None = None) -> bool:
        """Return True once per elapsed period, skipping missed ticks (no floods)."""
        now = time.monotonic() if now is None else now
        if not self.due(now=now):
            return False
        assert self.next_send_at is not None
        periods = math.floor((now - self.next_send_at) / self.interval_seconds) + 1
        self.next_send_at += periods * self.interval_seconds
        return True
