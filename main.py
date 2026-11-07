"""Entry point for Fly's OSC Chat Box."""
from __future__ import annotations

import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Fly's OSC Chat Box")
    app.setOrganizationName("LinuxOSCChatbox")
    app.setQuitOnLastWindowClosed(False)
    window = MainWindow(app)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
