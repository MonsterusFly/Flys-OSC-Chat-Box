#!/usr/bin/env bash
# Launch from a KDE desktop shortcut without depending on shell activation.
set -euo pipefail
APP_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$APP_DIR/.venv/bin/python"
LOG_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/linux-osc-chatbox"
mkdir -p "$LOG_DIR"
if [[ ! -x "$PYTHON" ]]; then
    MESSAGE="Fly's OSC Chat Box: Python environment missing at $PYTHON. Follow the README installation instructions."
    printf '%s\n' "$MESSAGE" >&2
    if command -v kdialog >/dev/null 2>&1; then kdialog --error "$MESSAGE" --title 'Fly's OSC Chat Box' || true; fi
    exit 1
fi
cd -- "$APP_DIR"
# Keep errors for troubleshooting when launched from the KDE menu.
exec "$PYTHON" "$APP_DIR/main.py" >> "$LOG_DIR/launcher.log" 2>&1
