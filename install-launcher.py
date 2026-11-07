#!/usr/bin/env python3
"""Install a local KDE .desktop entry for the existing project/virtual environment."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess

APP_NAME = "Fly's OSC Chat Box"
DESKTOP_FILENAME = "linux-osc-chatbox.desktop"


def desktop_entry(project: Path) -> str:
    launcher = project / ".venv/bin/python"
    if "\n" in str(launcher) or "\r" in str(launcher):
        raise ValueError("A path containing line breaks is not supported")
    # .desktop Exec syntax: quote absolute paths to handle spaces.
    quoted_exec = '"' + str(launcher).replace('\\', '\\\\').replace('"', '\\"') + '" "' + str(project / "main.py").replace('\\', '\\\\').replace('"', '\\"') + '"'
    return (
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Version=1.0\n"
        f"Name={APP_NAME}\n"
        "Comment=VRChat OSC chatbox companion for KDE Linux\n"
        f"Exec={quoted_exec}\n"
        f"Path={project}\n"
        "Icon=applications-games\n"
        "Terminal=false\n"
        "Categories=Game;Utility;\n"
        "StartupNotify=true\n"
    )


def desktop_directory() -> Path:
    try:
        answer = subprocess.run(["xdg-user-dir", "DESKTOP"], capture_output=True, text=True, timeout=3)
        value = answer.stdout.strip()
        if answer.returncode == 0 and value and Path(value).is_dir():
            return Path(value)
    except (OSError, subprocess.TimeoutExpired):
        pass
    return Path.home() / "Desktop"


def install(project: Path, desktop: bool = False) -> list[Path]:
    project = project.resolve()
    launcher = project / "launch-chatbox.sh"
    if not (project / "main.py").is_file() or not launcher.is_file():
        raise FileNotFoundError("Run this script from the extracted linux-osc-chatbox project")
    if not (project / ".venv/bin/python").is_file():
        raise FileNotFoundError("Project .venv is missing; create it and install requirements first")
    launcher.chmod(launcher.stat().st_mode | 0o111)
    xdg_data = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share")))
    locations = [xdg_data / "applications" / DESKTOP_FILENAME]
    if desktop:
        locations.append(desktop_directory() / DESKTOP_FILENAME)
    content = desktop_entry(project)
    for path in locations:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        if desktop and path.parent == desktop_directory():
            path.chmod(0o755)
    return locations


def main() -> int:
    parser = argparse.ArgumentParser(description="Add Fly's OSC Chat Box to KDE launcher")
    parser.add_argument("--desktop", action="store_true", help="Also create a desktop shortcut")
    args = parser.parse_args()
    try:
        outputs = install(Path(__file__).resolve().parent, desktop=args.desktop)
    except (FileNotFoundError, PermissionError, OSError) as exc:
        parser.exit(1, f"Launcher installation failed: {exc}\n")
    print("Installed KDE application launcher:")
    for path in outputs:
        print(f"  {path}")
    print("Find Fly's OSC Chat Box in your KDE Applications menu. Right-click to pin it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
