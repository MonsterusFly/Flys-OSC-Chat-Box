# KDE menu and desktop launcher (v0.6.6)

The launcher uses your project's existing `.venv` and does not change your saved
statuses, templates, or integrations. Install it once after extracting the project.

```bash
cd ~/Documents/Projects/linux-osc-chatbox
python3 install-launcher.py --desktop
```

Find **Fly's OSC Chat Box** in the KDE Applications menu. You can right-click it and
choose **Pin to Task Manager** (wording depends on Plasma version). You can also
double-click the Desktop shortcut; KDE may ask you to mark the shortcut as trusted
or executable the first time. If you do not want a Desktop icon, omit `--desktop`.

If launching from the menu fails, view:

```bash
tail -n 60 ~/.cache/linux-osc-chatbox/launcher.log
```

Since v0.9.1 the `.desktop` entry invokes the venv Python executable and `main.py` directly, not the shell wrapper. Re-run `python3 install-launcher.py --desktop` once after upgrading.

The `.desktop` entry uses an absolute path, so install it again if you move the
project directory. It has `Terminal=false` and starts the application directly,
without a terminal window. The application's normal tray behavior is unchanged.
