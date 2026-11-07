"""Desktop launcher integration checks; no KDE session required."""
from pathlib import Path
import importlib.util
import tempfile
import unittest
from unittest.mock import patch

MODULE_PATH = Path(__file__).resolve().parents[1] / "install-launcher.py"
spec = importlib.util.spec_from_file_location("chatbox_launcher", MODULE_PATH)
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


class LauncherTests(unittest.TestCase):
    def test_desktop_entry_uses_project_path_and_no_terminal(self):
        entry = launcher.desktop_entry(Path('/home/fly/Documents/Projects/linux-osc-chatbox'))
        assert 'Exec="/home/fly/Documents/Projects/linux-osc-chatbox/.venv/bin/python" "/home/fly/Documents/Projects/linux-osc-chatbox/main.py"' in entry
        assert 'Terminal=false' in entry
        assert 'Type=Application' in entry

    def test_installer_creates_application_shortcut(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            project = base / 'linux-osc-chatbox'
            (project / '.venv/bin').mkdir(parents=True)
            (project / 'main.py').touch()
            (project / 'launch-chatbox.sh').touch()
            (project / '.venv/bin/python').touch()
            with patch.dict('os.environ', {'XDG_DATA_HOME': str(base / 'data')}):
                paths = launcher.install(project)
            assert paths[0].exists()
            assert 'Exec=' in paths[0].read_text()
            assert (project / 'launch-chatbox.sh').stat().st_mode & 0o111

    def test_installer_refuses_missing_environment(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            (project / 'main.py').touch()
            (project / 'launch-chatbox.sh').touch()
            try:
                launcher.install(project)
            except FileNotFoundError:
                return
            assert False, 'Expected a missing environment error'
