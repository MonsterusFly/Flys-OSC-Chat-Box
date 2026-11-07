import json
from core.settings import Settings
from integrations.music import Track, styled_progress_bar


def test_custom_music_bar():
    track = Track(title='Song', duration_seconds=100, position_seconds=50, playing=False)
    assert styled_progress_bar(track, 'Custom', 6, '★', '·') == '★★★···'
    assert styled_progress_bar(track, 'Custom', 3, '🟩', '⬜') == '🟩⬜⬜'


def test_settings_profiles_survive_reload(tmp_path):
    path = tmp_path / 'settings.json'
    s = Settings(status_profiles=[{'name':'Mood','text':'🦊 playing VRChat','enabled':False}], selected_status=0,
                 music_bar_style='Custom',music_bar_filled='⭐',music_bar_empty='·',music_bar_width=14)
    s.save(path)
    loaded = Settings.load(path)
    assert loaded.status_profiles == s.status_profiles
    assert loaded.music_bar_style == 'Custom'
    assert (loaded.music_bar_filled, loaded.music_bar_empty, loaded.music_bar_width) == ('⭐','·',14)


def test_damaged_settings_recovers_backup(tmp_path):
    path = tmp_path / 'settings.json'
    s = Settings(status_profiles=[{'name':'Safe','text':'hello','enabled':True}])
    s.save(path)
    s.status_profiles[0]['text'] = 'newer'
    s.save(path)
    path.write_text('{broken json', encoding='utf-8')
    assert Settings.load(path).status_profiles[0]['text'] == 'hello'
    # Bad primary should never replace the good backup.
    s.save(path)
    assert json.loads(path.with_suffix('.json.bak').read_text())['status_profiles'][0]['text'] == 'hello'


def test_legacy_settings_keeps_profiles(tmp_path):
    path = tmp_path / 'settings.json'
    path.write_text(json.dumps({'version':5,'status_profiles':[{'name':'VR','text':'uwu','enabled':True}]}))
    assert Settings.load(path).status_profiles[0]['text'] == 'uwu'
