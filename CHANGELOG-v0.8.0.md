# Linux OSC Chatbox v0.8.0

## Visual Composer

- New **Composer** tab, opt-in. The v0.7 text-template editor remains available and unchanged by default.
- Add and delete individual sections; drag rows to reorder (or use Move up / Move down).
- Edit section name, text, enabled state and an optional list of alternative messages.
- **Rotate every** sets an independent interval (0 disables rotation) for a section's alternatives. One alternative per line; these are composed on an independent monotonic timebase. Rotation affects the next composed message, not the OSC send cadence.
- **Gaming**, **Music**, **AFK** starter presets. Loading a preset replaces composer sections only after confirmation and does not delete your existing custom status profiles or saved text layouts.
- Existing `{status}`, `{music}`, `{music_bar}`, `{music_progress}`, `{system}`, `{time}` variables work in sections.
- Section order, mode, text, options and intervals autosave into the XDG settings file, which retains its backup rotation.
- Visual Composer messages remain limited to VRChat's 144-character limit.

## Installation / upgrade (Fedora KDE)

1. Quit the current app, including the system tray.
2. Back up `~/.config/linux-osc-chatbox/settings.json`.
3. Extract `linux-osc-chatbox-v0.8.0.zip` into `~/Documents/Projects`.
4. Start using the **Linux OSC Chatbox** KDE menu item (your existing launcher remains valid).

The ZIP preserves executable permissions for `launch-chatbox.sh`. The ZIP contains no `.venv` and no user settings.

## Test coverage

61 non-GUI tests passed (core composer rotation, presets, migration, persistence, and prior behavior). Qt GUI needs a local Fedora KDE test.
