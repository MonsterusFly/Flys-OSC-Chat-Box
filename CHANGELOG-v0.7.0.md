# Linux OSC Chatbox v0.7.0

## Music source selector

On **Music**, click **Scan apps**. Choose **Auto — first playing app** or a specific MPRIS instance (Spotify, VLC, Firefox, Chromium etc.). Auto prefers the first player in the Playing state; selecting a named instance pins metadata and media controls to only that instance, even if it pauses. An offline player displays no track rather than falling back to another app. Individual browser media sessions are listed only if the browser exposes separate MPRIS instances. Enable **Show paused tracks in chatbox** if desired. Turn on **Now playing** in Integrations to populate the chatbox variables.

## Advanced message layouts

On **Chatbox**, place the cursor in the message template and use **Insert variable**, **Insert | separator**, and **Insert newline**. Save custom layouts with **Save layout as…**, choose them from **Saved layouts…**, or delete one. Layouts are stored in the existing XDG settings JSON, which is automatically backed up before each successful overwrite. The message preview and 144-character limit remain unchanged.

Example:

```
{status}
♫ {artist} — {title}
{music_bar} {music_progress}
{system} | {time}
```

Disabled or unavailable integration variables produce empty content. Send cadence, status rotation, media polling, and system polling remain independent.

## Upgrade

1. Close the running application from its system tray icon.
2. Optional backup: `cp ~/.config/linux-osc-chatbox/settings.json ~/chatbox-settings-before-v0.7.json`.
3. Extract `linux-osc-chatbox-v0.7.0.zip` into `~/Documents/Projects` using `unzip -o ~/Downloads/linux-osc-chatbox-v0.7.0.zip`.
4. Launch using your existing KDE Application Launcher shortcut, or `cd ~/Documents/Projects/linux-osc-chatbox && .venv/bin/python main.py`.

The archive excludes `.venv`, all user settings, and compiled caches. Your KDE launcher continues working because the project directory and entrypoint are unchanged.

## Verification

Run `.venv/bin/python -m pytest -q` (install pytest first if needed). CI-style non-GUI source tests passed on the build machine; the GUI must be verified on Fedora KDE. Ensure `playerctl` is installed (`sudo dnf install playerctl`).
