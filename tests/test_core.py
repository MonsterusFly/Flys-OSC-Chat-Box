from datetime import datetime

from core.message_engine import MAX_CHARS, clamp_message, compose
from core.settings import Settings


def test_clamp():
    assert len(clamp_message("x" * 250)) == MAX_CHARS


def test_compose():
    result = compose("Gaming", clock=True, system="CPU 10%", music="Artist - Song", now=datetime(2026, 11, 7, 4, 52))
    assert result == "Gaming | ♫ Artist - Song | CPU 10% | 04:52"


def test_empty_sections():
    assert compose("   ") == ""


def test_settings_roundtrip(tmp_path):
    path = tmp_path / "settings.json"
    expected = Settings(host="192.168.1.10", port=9001, auto_send=True)
    expected.save(path)
    actual = Settings.load(path)
    assert actual == expected


def test_bad_settings(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{oops", encoding="utf-8")
    assert Settings.load(path) == Settings()
