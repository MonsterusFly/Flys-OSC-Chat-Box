"""Non-GUI assertions for scrollable pages and preserved launcher behavior."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_pages_scroll_instead_of_squashing():
    text = (ROOT / "ui/main_window.py").read_text()
    assert "def _scroll_page" in text
    for page in ("chatbox", "statuses", "music", "system", "integrations", "settings"):
        assert f"self._scroll_page(self._page_{page}())" in text
    assert "SetMinimumSize" in text

def test_message_editor_and_preview_have_readable_heights():
    text = (ROOT / "ui/main_window.py").read_text()
    assert "self.template.setMinimumHeight(115)" in text
    assert "self.preview.setMinimumHeight(85)" in text
    assert "self.setMinimumSize(550, 420)" in text

def test_kde_exec_invokes_python_directly():
    text = (ROOT / "install-launcher.py").read_text()
    assert 'project / ".venv/bin/python"' in text
    assert 'str(project / "main.py")' in text
