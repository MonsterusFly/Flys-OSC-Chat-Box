> **RPM & uninstall:** See [RPM-INSTALL.md](RPM-INSTALL.md).

# Fly's OSC Chat Box v1.2.0

**New installers and GitHub packaging:** See [PUBLIC-RELEASE.md](PUBLIC-RELEASE.md).

On Fedora KDE, extract the release archive, open a terminal in the extracted directory, and run:

```bash
bash scripts/install.sh --desktop
```

The installer checks Python, installs application Python dependencies in a user-private virtual environment, creates a KDE launcher, and preserves existing saved profiles in `~/.config/linux-osc-chatbox/`. It may need network access for Python packages; optional music integration needs `playerctl`. This release does not yet include an RPM; an initial terminal command is required.

---

# Fly's OSC Chat Box v1.0.0 — Backup, OSC diagnostics, GPU and music

**Upgrade from v0.9.1:** close the app and its tray process, download and extract the ZIP inside `~/Documents/Projects` (it contains the `linux-osc-chatbox/` directory). Launch from your existing KDE shortcut. The project `.venv` and the settings under `~/.config/linux-osc-chatbox/` are not in the ZIP. The KDE desktop entry continues launching `.venv/bin/python` directly, not the shell launcher.

New features:
- **Settings → Backup and restore:** export/import a complete JSON backup. Import validates the format, writes a timestamped `settings.pre-import-*.json` safety copy and exits the application; relaunch to use restored settings.
- **OSC Diagnostics page:** last 100 outgoing UDP attempts and errors, target IP/port, and message preview. A successful UDP send is **not** a VRChat delivery confirmation.
- **System page / Integrations:** GPU usage, temperature and VRAM (AMD sysfs; NVIDIA `nvidia-smi` if installed). Use `{gpu}`, `{gpu_usage}`, `{gpu_temp}`, `{vram}` in messages. Missing metrics remain blank.
- **Music page:** optional fallback to another player if your selected music app disappears, and album artwork for players exposing a local `file://` image. Remote artwork is **not downloaded**; the name and progress still work.

For new features see [CHANGELOG-v1.0.0.md](CHANGELOG-v1.0.0.md). Tests: `python -m pytest -q`.

## v0.9.1 — Responsive layout and reliable KDE launcher

- All pages scroll vertically if the window is too small to fit their controls. At extremely narrow widths, the page can scroll horizontally rather than overlap labels and inputs.
- Chatbox preset, template actions, saved layouts and send buttons are stacked to prevent clipping or overlap at smaller sizes.
- Statuses and Composer action buttons use two columns, with readable editor and preview heights.
- The KDE launcher installer now launches `.venv/bin/python main.py` directly. This matches the working Fedora KDE shortcut; after installing this version run `python3 install-launcher.py --desktop` **once** to refresh the entry.
- Keeps the existing `~/.config/linux-osc-chatbox/settings.json` configuration directory; the ZIP contains no settings file or `.venv`.
- If your desktop has display scaling above 100%, Qt will use your Plasma scaling. This update prioritizes readability via scrolling rather than shrinking text.

## v0.8.0 — Visual Composer and presets

See [CHANGELOG-v0.8.0.md](CHANGELOG-v0.8.0.md). New **Composer** page: drag message sections to change ordering, edit and rotate alternatives per section, and load Gaming / Music / AFK starter layouts. Default remains your existing text template until you enable visual sections. The launcher file is packaged executable.

## v0.6.6 — KDE application launcher

Run `python3 install-launcher.py --desktop` once from the project folder to add a KDE Applications menu entry and a desktop icon. See [LAUNCHER.md](LAUNCHER.md). Your `.venv` and saved statuses remain unchanged.

## v0.6.5 — Compact Statuses layout

- Reduced unused vertical space in saved statuses and editor sections.
- Moved the image-backed emoji preview immediately beneath the message editor and limited its height to 48px.
- Kept status editing, auto-save, rotation checkboxes, and all OSC behavior unchanged.
- Long statuses may be visually clipped in the compact preview; the complete message remains in the editor and outgoing OSC.

# Fly's OSC Chat Box v0.6.0 — Emoji picker, custom music bars, status autosave

## What's new

- **Insert emoji / emote** on the Statuses page. Select from a built-in emoji grid; it inserts into the selected status text at the cursor.
- **Insert emoji into template** button on Chatbox page.
- **Custom progress bar** on Integrations: choose `Custom`, set your filled and empty symbols and a width between 3 and 24 characters. Use `{music_bar}` in the chatbox template. Example: `★★★······· 1:22 / 3:45`.
- **Automatic status saving**: status text/name edits, adding, deleting, reordering, selecting, and rotation toggles are saved after a 700 ms debounce. The Save buttons still work. Templates and progress-bar settings also autosave.
- **Recovery backup**: each successful save retains the preceding valid configuration as `~/.config/linux-osc-chatbox/settings.json.bak`. If the primary JSON is invalid, the app loads that backup. This does not replace a backup of the configuration that is already on your computer before upgrading.

## Upgrade Fedora KDE

Exit the existing application from the tray, then **back up your current settings before updating**:

```bash
mkdir -p ~/Documents/Projects/linux-osc-chatbox-backups
cp -a ~/.config/linux-osc-chatbox/settings.json ~/Documents/Projects/linux-osc-chatbox-backups/settings-before-v0.6.json
cd ~/Documents/Projects
unzip -o ~/Downloads/linux-osc-chatbox-v0.6.zip
cd linux-osc-chatbox
source .venv/bin/activate
python main.py
```

The ZIP contains application source only; it does **not** include `.venv` or any user's settings. Previous v0.5.x profiles are read from your existing settings file. If they were already lost in an earlier version, restoring them requires a previously saved backup.

**Important:** VRChat's chatbox is capped at 144 characters, so long or multi-codepoint emoji and long progress bars can be truncated. Not all emoji render in VRChat with identical appearance.

## Tests

```bash
python -m pip install pytest
python -m pytest -q
```

# Fly's OSC Chat Box v0.5.1

Status page improvement: each saved status now has its own checkbox directly in the list. Checked statuses participate in automatic rotation, while unchecked statuses remain available for manual selection. The former Include in rotation checkbox in the editor has been removed. Use **Save settings** to persist changes.

# Fly's OSC Chat Box v0.5.0 — Saved Statuses and Music Controls

Native Qt application for Fedora KDE and VRChat. Independent project, not affiliated with MagicChatbox.

## New in v0.5

- **Statuses page**: add, name, edit, delete, reorder, and select saved status profiles.
- **Manual mode**: uncheck status rotation and click the status you want. The chatbox `{status}` variable uses the selected text immediately.
- **Rotation mode**: turn on automatic rotation, select which statuses are eligible, and choose a 5–3600 second interval. Rotation skips unchecked statuses, wraps in list order, and runs independently of auto-send.
- **Music controls**: previous, play/pause, and next using the detected `playerctl`/MPRIS player. Controls run in a worker thread; functionality depends on the player.
- **Progress styles**: choose Blocks, Squares, Circles, or ASCII in Integrations. The `{music_bar}` variable uses the selected style.
- Existing music playback progress, system monitoring and OSC auto-send features are preserved.
- Existing settings at `~/.config/linux-osc-chatbox/settings.json` are migrated automatically. Original custom status becomes the initial Default profile.

## Installation / upgrade

Exit the application from its tray menu **before updating**. Back up settings if desired:

```bash
cp ~/.config/linux-osc-chatbox/settings.json ~/chatbox-settings-backup.json
```

Extract the `linux-osc-chatbox-v0.5.zip` archive into `~/Documents/Projects` so that it updates your existing `linux-osc-chatbox/` source folder. Your `.venv` and settings file are not included or modified by extraction.

```bash
cd ~/Documents/Projects
unzip -o ~/Downloads/linux-osc-chatbox-v0.5.zip
cd linux-osc-chatbox
source .venv/bin/activate
python -m pip install -r requirements.txt
sudo dnf install playerctl
python main.py
```

## Usage

1. Open **Statuses** → Add; create statuses such as Gaming, AFK, Listening to music.
2. Click a status to select it. Edit its name/message/rotation eligibility and click **Save changes to this status**.
3. For manual mode, leave **Automatically rotate** off and select the desired status.
4. For rotation, enable at least two statuses and turn **Automatically rotate** on. Choose how often it switches.
5. Click **Save settings** in Chatbox or Settings to persist profiles.
6. Use `{status}` in the message template. The live preview changes on status selection or rotation.
7. **Auto-send is separate**: enable it in Chatbox if you want the currently selected status transmitted periodically to VRChat. Rotating a status does not itself send a packet.

## Notes

- The selected status and profile edits persist to the JSON settings file when you save settings or exit normally.
- If you select a different status before clicking **Save changes to this status**, uncommitted edits to the editor are discarded.
- Message length remains limited to VRChat's 144-character chatbox limit.
- Music progress inside VRChat advances at your configured auto-send interval, not at the GUI animation frame rate.
- This release does not yet include album artwork. That will require a separate artwork loading implementation; media controls and progress styles are ready now.
- UDP sending cannot confirm that VRChat actually displayed the message.

## Testing

```bash
python -m pip install pytest
python -m pytest -q
python -m compileall -q main.py core ui integrations
```

Optional Qt smoke test on a machine with PySide6 installed:

```bash
QT_QPA_PLATFORM=offscreen python -c 'from PySide6.QtWidgets import QApplication; from ui.main_window import MainWindow; app=QApplication([]); window=MainWindow(app); print("GUI initialized"); window._quit()'
```

### v0.6.1 — Emoji picker display fix

The emoji picker now uses an emoji-capable Qt font if available, always shows a readable text label for each emoji, includes a search box, and inserts at the original cursor position. If glyphs are blank on Fedora, install an emoji font (for example `sudo dnf install google-noto-emoji-color-fonts`) and restart the application. Names remain visible even if your Qt build cannot render color emoji glyphs.

Profiles and settings continue to be saved under `~/.config/linux-osc-chatbox/`, outside the source ZIP. Back up that directory before an update if it contains important custom statuses.

### v0.6.2 — Visible emoji icons in picker

The picker now rasterizes installed Noto Color Emoji glyphs into transparent PNGs
using Pillow, then displays those images in Qt. This avoids the blank-glyph
problem seen on some Fedora KDE / Qt configurations. Searchable names remain
available if no compatible font is installed.

On Fedora, install the system emoji font if necessary:

```bash
sudo dnf install google-noto-emoji-color-fonts
```

Install Python dependencies into the project's active `.venv`:

```bash
python -m pip install -r requirements.txt
```

Existing status profiles and settings are stored outside the source tree and
are not included in this source ZIP.

### v0.6.3 — Bundled emoji pictures

The picker now uses 48 pre-rendered PNG emoji icons bundled under `assets/emoji/`.
It no longer requires Fedora's emoji font to display icons, or Pillow at runtime
for picker icons. Buttons are native `QToolButton`s with icons, rather than
child labels that can be obscured by Qt/KDE button paint styles.

The included emoji artwork is rasterized from Google's Noto Color Emoji
(Open Font License); see https://github.com/googlefonts/noto-emoji .
No font files are distributed in this package.

**Upgrade:** Exit from the tray, then unzip v0.6.3 over the existing project.
Settings and status profiles are kept in `~/.config/linux-osc-chatbox/`.

## v0.6.4: Emoji visibility in local message previews

The Statuses editor now shows a **Visible emoji preview** underneath the editable
message. The Chatbox live preview also uses the 48 bundled emoji PNGs. This
avoids missing-glyph boxes in the local UI even when Qt cannot paint emojis in
the plain-text edit fields. The actual stored/sent text remains Unicode, not
images or HTML.

VRChat OSC `/chatbox/input` supports UTF-8 strings, but **VRChat decides which
Unicode emoji glyphs it can render**. If an icon appears in our preview but is
blank in VRChat, try another Unicode character (for example `♥`, `★`, `♫`).
Our program cannot transmit PNG images through the OSC chatbox endpoint.

To verify the on-wire text locally, use a UDP/OSC receiver on a *different*
port from the game's OSC listener. Do not run another listener on the same
127.0.0.1:9000 port while VRChat is active.
# Fly's OSC Chat Box v0.7.0

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
