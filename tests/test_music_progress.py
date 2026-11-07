from integrations import music
from integrations.music import Track, format_time
from core.message_engine import render_template, unknown_variables
from core.settings import Settings


def test_format_time():
    assert format_time(0) == '0:00'
    assert format_time(92.9) == '1:32'
    assert format_time(3700) == '1:01:40'


def test_progress_advances_and_clamps():
    track = Track(title='Song', playing=True, position_seconds=30, duration_seconds=120, sampled_at=100)
    assert track.progress_text(now=110) == '0:40 / 2:00'
    assert track.progress_bar(width=10, now=110) == '▰▰▰▱▱▱▱▱▱▱'
    assert track.progress_text(now=300) == '2:00 / 2:00'


def test_paused_progress_does_not_advance():
    track = Track(title='Song', playing=False, position_seconds=90, duration_seconds=180, sampled_at=100)
    assert track.progress_text(now=120) == track.progress_text(now=500) == '1:30 / 3:00'


def test_unknown_duration_no_progress():
    track = Track(title='Stream', playing=True)
    assert not track.has_progress
    assert track.progress_text() == ''
    assert track.progress_bar() == ''


def test_playerctl_metadata_and_position(monkeypatch):
    def fake(*args):
        if args == ('-l',):
            return 'vlc\nspotify'
        if args[-1] == 'status':
            return 'Playing' if args[1] == 'spotify' else 'Paused'
        if args[-1] == 'position':
            return '51.4'
        if args[2] == 'metadata':
            return 'Example track\tSinger\t200000000'
        return ''
    monkeypatch.setattr(music, '_playerctl', fake)
    track = music.current_track()
    assert track.player == 'spotify'
    assert track.title == 'Example track'
    assert track.playing
    assert track.duration_seconds == 200
    assert 51 <= track.position_seconds <= 52


def test_new_template_variables_and_settings(tmp_path):
    template = '{music_bar} {music_progress}'
    assert not unknown_variables(template)
    assert render_template(template, {'music_bar': '▰▱', 'music_progress': '1:00 / 3:00'}) == '▰▱ 1:00 / 3:00'
    settings = Settings(show_music=True, show_music_progress=True)
    path = tmp_path / 'settings.json'
    settings.save(path)
    assert Settings.load(path).show_music_progress
    old = tmp_path / 'old.json'
    old.write_text('{"version":3,"show_music":true}')
    assert Settings.load(old).show_music_progress is False
