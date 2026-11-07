from core.settings import Settings
from integrations import music
from integrations.music import choose_player


def test_player_selection():
    players = ['firefox.instance11', 'spotify', 'vlc']
    statuses = {'firefox.instance11': 'Paused', 'spotify': 'Playing', 'vlc': 'Playing'}
    assert choose_player(players, 'Auto', statuses) == 'spotify'
    assert choose_player(players, 'firefox.instance11', statuses) == 'firefox.instance11'
    assert choose_player(players, 'offline', statuses) == ''
    assert choose_player([], 'Auto', {}) == ''


def test_player_filter_no_fallback(monkeypatch):
    def fake(*args):
        if args == ('-l',): return 'firefox\nspotify'
        if args[-1] == 'status': return 'Playing' if args[1] == 'spotify' else 'Paused'
        if args[2] == 'metadata': return 'Song\tArtist\t100000000'
        if args[-1] == 'position': return '11'
        return ''
    monkeypatch.setattr(music, '_playerctl', fake)
    assert music.current_track('firefox').player == 'firefox'
    assert music.current_track('firefox').playing is False
    assert music.current_track('not-open').title == ''
    assert music.current_track('Auto').player == 'spotify'


def test_settings_music_and_named_layouts(tmp_path):
    path = tmp_path / 'settings.json'
    s = Settings(music_player='firefox.instance9', music_show_paused=True,
                 custom_layouts={'Cozy': '{status}\n♫ {music}', 'Compact': '{status} | {time}'},
                 status_profiles=[{'name': 'Important', 'text': '🍀 Hi', 'enabled': True}])
    s.save(path)
    loaded = Settings.load(path)
    assert loaded == s
    assert loaded.custom_layouts['Cozy'] == '{status}\n♫ {music}'
    assert loaded.status_profiles == s.status_profiles


def test_legacy_config_defaults(tmp_path):
    path = tmp_path / 'settings.json'
    path.write_text('{"version":6,"show_music":true,"status_profiles":[{"name":"old","text":"yay","enabled":true}]}')
    s = Settings.load(path)
    assert s.music_player == 'Auto' and s.custom_layouts == {}
    assert s.status_profiles[0]['text'] == 'yay'
