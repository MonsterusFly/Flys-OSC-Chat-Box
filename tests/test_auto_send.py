from core.settings import Settings


def test_auto_send_defaults_to_repeating():
    settings = Settings()
    assert settings.only_send_when_changed is False


def test_old_settings_default_to_repeating(tmp_path):
    p = tmp_path / 'settings.json'
    p.write_text('{"auto_send":true,"auto_interval":15,"version":2}')
    settings = Settings.load(p)
    assert settings.auto_send
    assert settings.auto_interval == 15
    assert not settings.only_send_when_changed


def test_only_changed_setting_persists(tmp_path):
    p = tmp_path / 'settings.json'
    s = Settings(only_send_when_changed=True)
    s.save(p)
    assert Settings.load(p).only_send_when_changed
