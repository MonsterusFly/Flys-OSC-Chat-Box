#!/usr/bin/env bash
set -Eeuo pipefail
APP_HOME="${XDG_DATA_HOME:-$HOME/.local/share}/flys-osc-chat-box"
DESKTOP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/linux-osc-chatbox"
ASSUME_YES=false
PURGE=false
for arg in "$@"; do
  case "$arg" in
    --yes) ASSUME_YES=true ;;
    --purge-settings) PURGE=true ;;
    --help|-h) echo 'Usage: bash scripts/uninstall.sh [--yes] [--purge-settings]'; exit 0 ;;
    *) echo "Unknown option: $arg" >&2; exit 2 ;;
  esac
done
if [[ "$ASSUME_YES" != true ]]; then
  read -r -p "Remove Fly's OSC Chat Box (settings kept by default)? [y/N] " answer
  [[ "$answer" =~ ^[Yy]$ ]] || exit 0
fi
if [[ "$PURGE" == true && "$ASSUME_YES" == true ]]; then
  echo 'To delete settings, run again without --yes and confirm interactively.' >&2
  exit 2
fi
if [[ "$PURGE" == true ]]; then
  read -r -p "PERMANENTLY remove saved statuses, layouts and preferences too? Type DELETE: " answer
  [[ "$answer" == DELETE ]] || { echo 'Cancelled'; exit 0; }
fi
# Only remove the user-local installation. Never remove an RPM via rm.
rm -rf -- "$APP_HOME"
rm -f -- "$DESKTOP_DIR/flys-osc-chat-box.desktop" "$DESKTOP_DIR/flys-osc-chat-box-uninstall.desktop"
desktop_path="$(xdg-user-dir DESKTOP 2>/dev/null || true)"
[[ -n "$desktop_path" ]] || desktop_path="$HOME/Desktop"
rm -f -- "$desktop_path/flys-osc-chat-box.desktop"
if [[ "$PURGE" == true ]]; then rm -rf -- "$CONFIG_DIR"; fi
echo "Application removed. Saved profiles: $([[ "$PURGE" == true ]] && echo deleted || echo preserved)"
