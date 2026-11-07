#!/usr/bin/env bash
set -Eeuo pipefail
APP_HOME="${XDG_DATA_HOME:-$HOME/.local/share}/flys-osc-chat-box"
DESKTOP_FILE="$HOME/.local/share/applications/flys-osc-chat-box.desktop"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/linux-osc-chatbox"
read -r -p "Uninstall Fly's OSC Chat Box application (keep saved settings)? [y/N] " ans
[[ "$ans" =~ ^[Yy]$ ]] || exit 0
rm -rf -- "$APP_HOME"
rm -f -- "$DESKTOP_FILE"
desktop_path="$(xdg-user-dir DESKTOP 2>/dev/null || true)"
[[ -n "$desktop_path" ]] || desktop_path="$HOME/Desktop"
rm -f -- "$desktop_path/flys-osc-chat-box.desktop"
echo "Application uninstalled. Saved profiles preserved at $CONFIG_DIR"
