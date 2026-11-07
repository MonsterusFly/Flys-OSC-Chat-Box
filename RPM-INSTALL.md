# RPM and uninstall guide (v1.2.0)

## Fedora RPM
The Fedora RPM installs from the distro repositories, without pip, by depending
on `python3-pyside6`, `python3-psutil`, `python3-pillow`, and Python 3. `playerctl`
is recommended for music integration. OSC has a built-in Python UDP fallback.

Build on Fedora 44 with `sudo dnf install rpm-build` and `bash scripts/build_rpm.sh`.
GitHub Actions also builds an RPM artifact using `.github/workflows/rpm.yml`.
The produced RPM is unsigned. For testers only until signing and bundled artwork
attribution reviews have been completed. Download the Actions artifact and use
`sudo dnf install ./flys-osc-chat-box-1.2.0-1*.noarch.rpm`.

## RPM uninstall
Fedora KDE Discover > Installed > Fly's OSC Chat Box > Remove; or run
`sudo dnf remove flys-osc-chat-box`. A separate menu entry named
**Uninstall Fly's OSC Chat Box** opens an uninstall prompt with privilege escalation.
All methods preserve personal settings under `~/.config/linux-osc-chatbox/`.

## User-local installer uninstall
Choose **Uninstall Fly's OSC Chat Box** from the KDE Applications menu, or run:
`bash scripts/uninstall.sh` from the extracted sources. The uninstaller removes
the local app and shortcuts but preserves profiles. Removing settings requires
an explicit `--purge-settings` and typing `DELETE` during confirmation.

## Existing user-local installation
If already using the user-local installer, uninstall that copy before installing
the RPM to avoid duplicate shortcuts or conflicting versions. Saved settings remain.

## Packaging notes
RPM upgrades replace only package-managed files under `/usr`. RPM uninstall does
not delete user configuration. Do not run pip in an RPM scriptlet.
