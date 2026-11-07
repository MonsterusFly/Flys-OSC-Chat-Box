from core.status_profiles import StatusProfile, StatusRotator, next_enabled_index
from core.settings import Settings


def test_wrap_and_skip_disabled():
    statuses = [StatusProfile('One', 'A'), StatusProfile('Two', 'B', False), StatusProfile('Three', 'C')]
    assert next_enabled_index(statuses, 0) == 2
    assert next_enabled_index(statuses, 2) == 0
    assert next_enabled_index([], 0) == -1


def test_rotation_clock_independent():
    r = StatusRotator(30)
    r.configure(True, 30, now=100)
    assert r.remaining(now=101) == 29
    assert not r.advance(now=129)
    assert r.advance(now=130)
    assert not r.advance(now=131)
    assert r.remaining(now=131) == 29
    r.configure(False, 30, now=132)
    assert r.remaining(now=140) is None


def test_rotation_reconfigures():
    r = StatusRotator()
    r.configure(True, 60, now=0)
    r.configure(True, 15, now=3)
    assert r.remaining(now=3) == 15


def test_profiles_roundtrip(tmp_path):
    path = tmp_path / 'settings.json'
    obj = Settings(status_profiles=[{'name':'BRB', 'text':'Away', 'enabled':True}, {'name':'Gaming', 'text':'Playing {music}', 'enabled':False}], selected_status=1, rotate_statuses=True, status_rotation_interval=15)
    obj.save(path)
    loaded = Settings.load(path)
    assert loaded.status_profiles == obj.status_profiles
    assert loaded.selected_status == 1
    assert loaded.rotate_statuses is True
    assert loaded.status_rotation_interval == 15


def test_legacy_migration(tmp_path):
    path = tmp_path / 'legacy.json'
    path.write_text('{"status_text":"Old status", "version":4}')
    loaded = Settings.load(path)
    assert loaded.status_profiles[0]['text'] == 'Old status'
