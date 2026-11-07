# Fly's OSC Chat Box — Public release guide

## Install on Fedora KDE (first-time)

1. Download the release `Flys-OSC-Chat-Box-v1.1.0.tar.gz` or ZIP from GitHub Releases.
2. Extract it. Open a terminal in the extracted `Flys-OSC-Chat-Box-v1.1.0` directory.
3. Run `bash scripts/install.sh --desktop`. You can omit `--desktop` if you only want the KDE Applications menu entry.
4. The script verifies Python 3.10+, creates a private virtual environment under `~/.local/share/flys-osc-chat-box/`, installs PySide6, python-osc, psutil and Pillow from PyPI, installs the source, and creates a KDE launcher that calls Python **directly**.
5. Search for **Fly's OSC Chat Box** in KDE Applications. If KDE prompts for trust on the desktop shortcut, use **Trust and Launch**.

Optional Fedora dependency for media playback: `sudo dnf install playerctl`.
If Python or venv is missing: `sudo dnf install python3 python3-pip`.

This is a **guided first-time installer**, not yet a signed RPM or fully no-prompts one-click installer. A downloadable `.rpm` package is a next step.

## Updates

Download/extract the new release and rerun `bash scripts/install.sh --desktop`. The app files and virtual environment are stored separately; your config remains at `~/.config/linux-osc-chatbox/`. A timestamped settings backup is created before installation if settings exist. Do not run the installer while the app is running.

## Uninstall

Run `bash scripts/uninstall.sh` from an extracted release. The app and shortcuts are removed; settings are retained.

## Publish from your own GitHub repository

Create an empty repository named `Flys-OSC-Chat-Box` (public or private). Then inside this extracted folder:

```bash
git init
git add .
git commit -m 'Initial public release v1.1.0'
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/Flys-OSC-Chat-Box.git
git push -u origin main
git tag v1.1.0
git push origin v1.1.0
```

Replace `YOUR_USERNAME` with the actual account/organization. GitHub authentication is required. The tag triggers automated tests and release archive publishing. Review the contents and copyright/licenses **before making the repository public**.

## Licensing and attribution review required

`LICENSE` covers project code, but review the bundled `assets/emoji/*.png` attribution and the original Noto Emoji upstream license. Add attribution/notice files before publishing. Review licenses for PySide6/Qt and all third-party dependencies, particularly for binary distribution. The repo does not copy code from the original MagicChatbox project.

## CI

`.github/workflows/tests.yml` runs Python tests; `.github/workflows/release.yml` builds versioned ZIP/tarball files and SHA256SUMS on tags. Workflows are provided but have **not** yet run on GitHub, and must be verified after the first push.
