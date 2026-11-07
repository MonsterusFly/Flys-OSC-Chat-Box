#!/usr/bin/env python3
"""Graphical uninstall helper. Never deletes user settings automatically."""
from pathlib import Path
import os
import shutil
import subprocess
import sys
from PySide6.QtWidgets import QApplication, QMessageBox

APP_HOME = Path.home() / '.local/share/flys-osc-chat-box'

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Uninstall Fly's OSC Chat Box")
    is_rpm = subprocess.run(['/usr/bin/rpm', '-q', 'flys-osc-chat-box'],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0 if Path('/usr/bin/rpm').exists() else False
    if is_rpm:
        text = "Remove the installed RPM package? Your statuses, layouts and preferences will be kept."
    elif APP_HOME.is_dir():
        text = "Remove the user-local installation? Your statuses, layouts and preferences will be kept."
    else:
        QMessageBox.information(None, 'Not installed', "No supported Fly's OSC Chat Box installation was found.")
        return 0
    if QMessageBox.question(None, "Uninstall Fly's OSC Chat Box", text,
                            QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
        return 0
    if is_rpm:
        # Use distro package manager: the polkit prompt is explicit and cancellable.
        cmd = ['/usr/bin/pkexec', '/usr/bin/dnf', 'remove', '-y', 'flys-osc-chat-box']
        if not Path(cmd[0]).exists() or not Path(cmd[1]).exists():
            QMessageBox.warning(None, 'Package manager unavailable',
                                'Remove the RPM from KDE Discover or run: sudo dnf remove flys-osc-chat-box')
            return 1
        result = subprocess.run(cmd, check=False)
        if result.returncode:
            QMessageBox.warning(None, 'Uninstall cancelled or failed',
                                'The RPM was not removed. Try KDE Discover or: sudo dnf remove flys-osc-chat-box')
            return result.returncode
    else:
        cmd = ['/bin/bash', str(APP_HOME / 'app/scripts/uninstall.sh'), '--yes']
        result = subprocess.run(cmd, check=False)
        if result.returncode:
            QMessageBox.warning(None, 'Uninstall failed', 'Check the installed uninstall script.')
            return result.returncode
    QMessageBox.information(None, 'Uninstalled',
                            "Fly's OSC Chat Box has been removed. Your saved settings were kept.")
    return 0

if __name__ == '__main__':
    sys.exit(main())
