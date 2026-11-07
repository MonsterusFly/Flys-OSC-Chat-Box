# Fly's OSC Chat Box

**A customizable VRChat OSC Chatbox application for Linux.**

Fly's OSC Chat Box is a desktop application designed for Linux users who want to display custom statuses, music information, system statistics, and more in their VRChat chatbox.

Built with Python and PySide6, it provides an easy-to-use graphical interface with customizable themes and automatic updates.

## Features

- **Custom Statuses** — Create, save, and rotate between multiple status messages.
- **Music Integration** — Display currently playing music, song information, and playback progress.
- **System Monitoring** — Show CPU, RAM, and GPU information.
- **Chatbox Composer** — Customize how information appears in your VRChat chatbox.
- **OSC Integration** — Send messages directly to VRChat using OSC.
- **Themes** — Choose from multiple application themes.
- **Settings Backup** — Export and import your saved settings.
- **Automatic Updates** — Detect, download, and install new versions through the application.

## Installation

### Fedora / Nobara Linux (Recommended)

The easiest way to install Fly's OSC Chat Box is with the RPM package.

**1. Download the application**

Visit the [GitHub Releases page](https://github.com/MonsterusFly/Flys-OSC-Chat-Box/releases/latest).

Download the latest `.rpm` file for your Fedora version.

**2. Install the RPM**

Open the downloaded RPM using your graphical package installer, or install it through the terminal:

```bash
cd ~/Downloads
sudo dnf install ./flys-osc-chat-box-*.rpm
```

**3. Launch the application**

After installation, open your KDE Applications menu and search for:

**Fly's OSC Chat Box**

Launch the application and configure your preferences.

### Other Linux Distributions

Source installation is also available.

Download the latest source archive from [GitHub Releases](https://github.com/MonsterusFly/Flys-OSC-Chat-Box/releases/latest).

Extract the archive, open a terminal inside the extracted folder, and run:

```bash
bash scripts/install.sh --desktop
```

The installer creates a user-local application installation and desktop launcher.

Python 3.10 or newer and Python virtual environment support are required.

## Updating the Application

Fly's OSC Chat Box includes a built-in update system.

### Automatic Update Detection

By default, the application checks GitHub for new versions when it starts.

When an update is available:

1. Open **Settings → Software updates**.
2. Click **Check for updates**.
3. Review the available version.
4. Click **Download and install update**.
5. Confirm the download and installation.
6. Approve the administrator authentication request.
7. Restart the application.

The application downloads the RPM and verifies its SHA-256 checksum before installation.

Updates are **never installed silently**.

### Automatic Downloads

You can optionally enable:

**Settings → Automatically download verified Fedora RPMs**

When enabled, the application can download and verify new updates automatically. Installation still requires your confirmation.

### Manual Updates

You can also download the latest RPM from [GitHub Releases](https://github.com/MonsterusFly/Flys-OSC-Chat-Box/releases/latest) and install it using:

```bash
sudo dnf install ./flys-osc-chat-box-<version>.rpm
```

Replace `<version>` with the downloaded RPM filename, or provide the full path to the RPM.

For source installations, download the latest source archive and rerun the installation script.

## VRChat Setup

1. Open VRChat.
2. Enable **OSC** in your VRChat settings.
3. Open Fly's OSC Chat Box.
4. Configure your statuses and desired information.
5. Enable automatic sending or send messages manually.

The application uses the default VRChat OSC address:

- **Host:** `127.0.0.1`
- **Port:** `9000`

VRChat and Fly's OSC Chat Box must be able to communicate over the configured OSC network connection.

## Settings and Backups

Your settings are stored at:

```text
~/.config/linux-osc-chatbox/
```

Settings are retained when updating or uninstalling the RPM package.

You can also export and restore settings from within the application.

## Uninstalling

To remove an RPM installation:

```bash
sudo dnf remove flys-osc-chat-box
```

Your saved settings are retained.

For a source installation, run:

```bash
bash scripts/uninstall.sh
```

from the extracted project folder.

## License

Fly's OSC Chat Box is released under the **MIT License**.

See [LICENSE](LICENSE) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for licensing information and third-party artwork attribution.

## Links

- [GitHub Repository](https://github.com/MonsterusFly/Flys-OSC-Chat-Box)
- [Download Latest Release](https://github.com/MonsterusFly/Flys-OSC-Chat-Box/releases/latest)
- [Report a Bug](https://github.com/MonsterusFly/Flys-OSC-Chat-Box/issues)

---

Developed by **MonsterusFly**.

*Fly's OSC Chat Box is an independent community application and is not affiliated with VRChat Inc.*
