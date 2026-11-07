"""Read-only Linux GPU telemetry: amdgpu sysfs first, NVIDIA CLI fallback."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import subprocess
import shutil

@dataclass(frozen=True)
class GPUStats:
    name: str = ""
    usage_percent: int | None = None
    temperature_c: float | None = None
    vram_used_mib: int | None = None
    vram_total_mib: int | None = None

    @property
    def display(self) -> str:
        if not self.name:
            return "GPU unavailable"
        parts = ["GPU"]
        if self.usage_percent is not None:
            parts.append(f"{self.usage_percent}%")
        if self.temperature_c is not None:
            parts.append(f"{self.temperature_c:.0f}°C")
        return " · ".join(parts) if len(parts)>1 else "GPU: " + self.name

def _read_int(path: Path) -> int | None:
    try:
        return int(path.read_text().strip())
    except (OSError, ValueError):
        return None

def read_amd(root: Path = Path('/sys/class/drm')) -> GPUStats | None:
    for card in sorted(root.glob('card[0-9]*')):
        device = card / 'device'
        try:
            if (device / 'vendor').read_text().strip().lower() != '0x1002':
                continue
        except OSError:
            continue
        usage = _read_int(device / 'gpu_busy_percent')
        used = _read_int(device / 'mem_info_vram_used')
        total = _read_int(device / 'mem_info_vram_total')
        temps = [_read_int(p) for p in sorted((device / 'hwmon').glob('hwmon*/temp1_input'))]
        temp = next((t / 1000 for t in temps if t is not None), None)
        return GPUStats('AMD Radeon', max(0,min(100,usage)) if usage is not None else None,
                        temp, round(used / 1048576) if used is not None else None,
                        round(total / 1048576) if total is not None else None)
    return None

def read_nvidia() -> GPUStats | None:
    if not shutil.which('nvidia-smi'):
        return None
    try:
        cmd = ['nvidia-smi','--query-gpu=name,utilization.gpu,temperature.gpu,memory.used,memory.total','--format=csv,noheader,nounits']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1.5, check=False)
        if result.returncode != 0 or not result.stdout.strip():
            return None
        parts = [s.strip() for s in result.stdout.splitlines()[0].split(',')]
        if len(parts) != 5:
            return None
        def number(s):
            try: return int(s)
            except ValueError: return None
        return GPUStats(parts[0], number(parts[1]), number(parts[2]), number(parts[3]), number(parts[4]))
    except (OSError, subprocess.TimeoutExpired):
        return None

def snapshot() -> GPUStats:
    return read_amd() or read_nvidia() or GPUStats()
