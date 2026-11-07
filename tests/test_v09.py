from pathlib import Path
import json
from core.settings import Settings
from core.themes import THEMES, DEFAULT_THEME, normalize_theme, stylesheet


def test_six_themes_and_styles():
    assert len(THEMES) == 6
    for name, colors in THEMES.items():
        css = stylesheet(name)
        assert colors['bg'] in css
        assert colors['accent'] in css
        assert 'QMainWindow' in css


def test_unknown_theme_falls_back():
    assert normalize_theme('unknown') == DEFAULT_THEME
    assert stylesheet('unknown') == stylesheet(DEFAULT_THEME)


def test_theme_roundtrip_with_profiles(tmp_path):
    path = tmp_path / 'settings.json'
    settings = Settings(theme='Forest', status_profiles=[{'name':'Test','text':'Hello','enabled':True}], custom_layouts={'demo':'{status}'})
    settings.save(path)
    loaded = Settings.load(path)
    assert loaded.theme == 'Forest'
    assert loaded.status_profiles == settings.status_profiles
    assert loaded.custom_layouts == settings.custom_layouts


def test_old_settings_get_default_theme(tmp_path):
    path = tmp_path / 'settings.json'
    path.write_text(json.dumps({'version':8,'status_profiles':[{'name':'Old','text':'Saved','enabled':True}]}))
    s = Settings.load(path)
    assert s.theme == DEFAULT_THEME
    assert s.status_profiles[0]['text'] == 'Saved'
