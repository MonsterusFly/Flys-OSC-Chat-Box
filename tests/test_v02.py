from core.message_engine import DEFAULT_TEMPLATE, PRESETS, render_template, unknown_variables
from core.settings import Settings


def test_template_removes_empty_lines():
    result = render_template(DEFAULT_TEMPLATE, {"status": "Gaming", "music": "", "system": "CPU 19%", "time": "05:22"})
    assert result == "Gaming\nCPU 19%\n05:22"


def test_compact_template_without_optional_parts():
    result = render_template(PRESETS["Compact"], {"status": "Gaming", "time": "08:30"})
    assert result == "Gaming | 08:30"


def test_unknown_tokens_visible_and_detected():
    assert unknown_variables("{status} {typo}") == {"typo"}
    assert render_template("{typo}", {}) == "{typo}"


def test_template_limit():
    assert len(render_template("{status}", {"status": "🎮" * 150})) == 144


def test_v01_settings_upgrade(tmp_path):
    file = tmp_path / "settings.json"
    file.write_text('{"host":"10.0.0.2","auto_interval":30,"show_music":true}', encoding="utf-8")
    s = Settings.load(file)
    assert s.host == "10.0.0.2"
    assert s.auto_interval == 30
    assert s.show_music
    assert s.template == DEFAULT_TEMPLATE
    s.save(file)
    assert Settings.load(file) == s
