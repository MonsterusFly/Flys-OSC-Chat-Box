"""Live system stats sampled independently from chatbox sending.

psutil.cpu_percent(interval=None) is a delta since the previous measurement;
prime it once, then sample on a fixed cadence to avoid a misleading 0%.
"""
from __future__ import annotations

from dataclasses import dataclass
import time
import psutil


@dataclass(frozen=True)
class SystemSnapshot:
    cpu: int
    ram: int
    used_gib: float = 0.0
    total_gib: float = 0.0
    uptime_seconds: int = 0
    sampled_at: float = 0.0

    @property
    def display(self) -> str:
        return f"CPU {self.cpu}% · RAM {self.ram}%"


class SystemMonitor:
    """Stateful sampler; call sample() roughly every 2 seconds."""

    def __init__(self) -> None:
        psutil.cpu_percent(interval=None)

    def sample(self) -> SystemSnapshot:
        cpu = max(0, min(100, round(psutil.cpu_percent(interval=None))))
        mem = psutil.virtual_memory()
        uptime = max(0, round(time.time() - psutil.boot_time()))
        gib = 1024 ** 3
        return SystemSnapshot(
            cpu=cpu,
            ram=round(mem.percent),
            used_gib=round(mem.used / gib, 1),
            total_gib=round(mem.total / gib, 1),
            uptime_seconds=uptime,
            sampled_at=time.monotonic(),
        )


_default_monitor: SystemMonitor | None = None


def snapshot() -> SystemSnapshot:
    global _default_monitor
    if _default_monitor is None:
        _default_monitor = SystemMonitor()
    return _default_monitor.sample()


def system_status() -> str:
    return snapshot().display
