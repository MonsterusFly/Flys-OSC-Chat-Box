#!/usr/bin/env bash
set -Eeuo pipefail
# User-local installer: does not require root and never deletes user settings.
SOURCE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
APP_HOME="${XDG_DATA_HOME:-$HOME/.local/share}/flys-osc-chat-box"
APP_DIR="$APP_HOME/app"
VENV="$APP_HOME/venv"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/linux-osc-chatbox"
DESKTOP_DIR="$HOME/.local/share/applications"
DESKTOP_FILE="$DESKTOP_DIR/flys-osc-chat-box.desktop"
WITH_DESKTOP=false
ASSUME_YES=false
for arg in "$@"; do
  case "$arg" in
    --desktop) WITH_DESKTOP=true ;;
    --yes) ASSUME_YES=true ;;
    --help|-h) echo "Usage: bash scripts/install.sh [--desktop] [--yes]"; exit 0 ;;
    *) echo "Unknown option: $arg" >&2; exit 2 ;;
  esac
done
fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
command -v python3 >/dev/null || fail 'Python 3 missing. Fedora: sudo dnf install python3 python3-pip'
command -v pip3 >/dev/null || true
python3 - <<'PYV' || fail 'Python 3.10+ is required'
import sys
assert sys.version_info >= (3,10), sys.version
PYV
[[ -f "$SOURCE_DIR/main.py" && -f "$SOURCE_DIR/requirements.txt" ]] || fail 'Run the installer from the extracted source directory'
[[ "$SOURCE_DIR" != "$APP_DIR" ]] || fail 'The source directory cannot be the installed application directory'
command -v playerctl >/dev/null || printf 'NOTE: playerctl is missing; install with sudo dnf install playerctl for music integration.\n'
command -v git >/dev/null || printf 'NOTE: git is optional and not required to run the application.\n'
if [[ "$ASSUME_YES" != true ]]; then
  echo "Install Fly's OSC Chat Box into: $APP_HOME"
  echo "Existing statuses and preferences in $CONFIG_DIR will not be removed."
  read -r -p 'Continue? [Y/n] ' confirm
  [[ ! "$confirm" =~ ^[Nn] ]] || exit 0
fi
mkdir -p "$APP_HOME" "$CONFIG_DIR" "$DESKTOP_DIR"
if [[ -f "$CONFIG_DIR/settings.json" ]]; then
  stamp="$(date +%Y%m%d-%H%M%S)"
  cp -p -- "$CONFIG_DIR/settings.json" "$CONFIG_DIR/settings.json.pre-v1.1-$stamp.bak"
  echo "Configuration backup created."
fi
# Keep the virtual environment outside the app source for stable upgrades.
if [[ ! -x "$VENV/bin/python" ]]; then
  python3 -m venv "$VENV" || fail 'Cannot create venv. Fedora: sudo dnf install python3 python3-pip'
fi
"$VENV/bin/python" -m pip install -r "$SOURCE_DIR/requirements.txt" || fail 'Python dependencies failed to install. Check internet connection and Qt system libraries.'
STAGING="$APP_HOME/.app-staging-$$"
trap 'rm -rf -- "$STAGING"' EXIT
mkdir -p "$STAGING"
# Copy only application files, never build caches, git internals, or a developer venv.
for name in main.py requirements.txt core ui integrations assets LICENSE README.md; do
  cp -a -- "$SOURCE_DIR/$name" "$STAGING/$name"
done
find "$STAGING" -type d \( -name __pycache__ -o -name .pytest_cache \) -prune -exec rm -rf {} +
find "$STAGING" -type f -name '*.pyc' -delete
"$VENV/bin/python" -m compileall -q "$STAGING" || fail 'Installed source failed compilation'
# Replace only application code. Never touch CONFIG_DIR or VENV.
if [[ -d "$APP_DIR" ]]; then
  mv -- "$APP_DIR" "$APP_HOME/.app-previous-$$"
else
  mkdir -p "$APP_HOME/.app-previous-$$"
fi
previous="$APP_HOME/.app-previous-$$"
if ! mv -- "$STAGING" "$APP_DIR"; then
  [[ -f "$previous/main.py" ]] && mv -- "$previous" "$APP_DIR"
  fail 'Cannot install application files'
fi
rm -rf -- "$previous"
trap - EXIT
# The desktop launcher directly invokes the venv python; never relies on shell activation.
cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Version=1.0
Name=Fly's OSC Chat Box
Comment=VRChat OSC chatbox companion for Linux
Exec="$VENV/bin/python" "$APP_DIR/main.py"
Path=$APP_DIR
Icon=applications-multimedia
Terminal=false
Categories=AudioVideo;Utility;
StartupNotify=true
EOF
chmod 644 "$DESKTOP_FILE"
if [[ "$WITH_DESKTOP" == true ]]; then
  desktop_path="$(xdg-user-dir DESKTOP 2>/dev/null || true)"
  [[ -n "$desktop_path" && -d "$desktop_path" ]] || desktop_path="$HOME/Desktop"
  mkdir -p -- "$desktop_path"
  cp -f -- "$DESKTOP_FILE" "$desktop_path/flys-osc-chat-box.desktop"
  chmod +x -- "$desktop_path/flys-osc-chat-box.desktop"
  echo "Desktop shortcut created (KDE may require Trust and Launch)."
fi
command -v kbuildsycoca6 >/dev/null && kbuildsycoca6 >/dev/null 2>&1 || true
printf '\nInstalled successfully. Search for Fly\x27s OSC Chat Box in the Applications menu.\n'
printf 'App files: %s\nSettings: %s\n' "$APP_HOME" "$CONFIG_DIR"
