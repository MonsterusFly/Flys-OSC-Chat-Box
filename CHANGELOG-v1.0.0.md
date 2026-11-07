# Fly's OSC Chat Box v1.0.0

- Export/import validated portable settings backups, with timestamped pre-import safety copies and app exit after restore.
- OSC diagnostics page: destination, outgoing UDP attempts, errors, last 100 sends. **Sending does not confirm VRChat receipt.**
- AMD Radeon sysfs GPU utilization/temperature/VRAM and NVIDIA nvidia-smi fallback. Added template variables `{gpu}`, `{gpu_usage}`, `{gpu_temp}`, `{vram}`.
- Music: optional fallback from selected app to another running app. Local-file album art preview when player exposes `file://` artwork. HTTP artwork deliberately not fetched.
- Preserves ~/.config/linux-osc-chatbox/settings.json, original project directory and direct-Python KDE launcher.
