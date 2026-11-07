import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from core.backups import export_backup, inspect_backup, restore_backup
from core.diagnostics import SendHistory
from core.settings import Settings
from core.message_engine import render_template, unknown_variables
from integrations.gpu import read_amd, GPUStats, read_nvidia
from integrations.artwork import local_album_art
from integrations.music import current_track


def test_backup_roundtrip_preserves_profiles_and_theme():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        src, dest = root/'backup.json', root/'config.json'
        original = Settings(theme='Royal Purple', status_profiles=[{'name':'hello','text':'Hi 😀','enabled':True}], music_player='spotify', show_gpu=True)
        export_backup(src, original)
        assert inspect_backup(src)['status_profiles'][0]['text'] == 'Hi 😀'
        restored = restore_backup(src, dest)
        assert restored.theme == 'Royal Purple'
        assert restored.show_gpu is True
        assert Settings.load(dest).status_profiles[0]['name'] == 'hello'

def test_restore_creates_safety_copy():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        target = root/'settings.json'
        Settings(status_text='older').save(target)
        source = export_backup(root/'backup.json', Settings(status_text='newer'))
        restore_backup(source, target)
        assert Settings.load(target).status_text == 'newer'
        assert any(root.glob('settings.pre-import-*.json'))

def test_invalid_backup_does_not_overwrite():
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp); target=root/'settings.json'; target.write_text('{"untouched": 1}')
        bad=root/'invalid.json'; bad.write_text('{"format":"wrong"}')
        try: restore_backup(bad, target)
        except ValueError: pass
        else: assert False
        assert target.read_text()=='{"untouched": 1}'

def test_osc_history_is_bounded_and_says_unconfirmed():
    history=SendHistory(limit=2)
    history.add('Manual','127.0.0.1',9000,'first')
    history.add('Auto','127.0.0.1',9000,'second',error='down')
    history.add('Auto','127.0.0.1',9000,'third')
    assert len(history.records)==2
    assert 'unconfirmed' in history.lines()[0]
    assert 'down' in history.lines()[1]

def test_amd_gpu_sysfs():
    with tempfile.TemporaryDirectory() as tmp:
        dev=Path(tmp)/'card0'/'device'; dev.mkdir(parents=True)
        (dev/'vendor').write_text('0x1002')
        (dev/'gpu_busy_percent').write_text('42')
        (dev/'mem_info_vram_total').write_text(str(8*1024**3))
        (dev/'mem_info_vram_used').write_text(str(2*1024**3))
        h=dev/'hwmon'/'hwmon1'; h.mkdir(parents=True)
        (h/'temp1_input').write_text('55000')
        gpu=read_amd(Path(tmp))
        assert gpu.usage_percent == 42
        assert gpu.temperature_c == 55
        assert gpu.vram_used_mib == 2048
        assert gpu.vram_total_mib == 8192

def test_no_gpu_data():
    with tempfile.TemporaryDirectory() as tmp:
        assert read_amd(Path(tmp)) is None
    assert GPUStats().display == 'GPU unavailable'

def test_local_album_art_rejects_network():
    assert local_album_art('https://example.com/image.png') is None
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/'a.png'; path.write_bytes(b'example')
        assert local_album_art(path.as_uri()) == path

def test_music_fallback_respects_manual_selection():
    with patch('integrations.music.list_players', return_value=['firefox']), patch('integrations.music._playerctl', side_effect=lambda *a: 'Playing' if a[-1]=='status' else ''):
        assert not current_track('spotify').player
        assert current_track('spotify', fallback_to_auto=True).player=='firefox'

def test_gpu_variables_supported():
    assert not unknown_variables('{gpu} {gpu_usage} {gpu_temp} {vram}')
    assert render_template('{gpu}', {'gpu':'GPU · 25%'}) == 'GPU · 25%'

def test_desktop_launcher_stays_direct_python():
    from pathlib import Path
    import importlib.util
    spec=importlib.util.spec_from_file_location('launcher', Path(__file__).resolve().parents[1]/'install-launcher.py')
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    entry=m.desktop_entry(Path('/home/fly/Documents/Projects/linux-osc-chatbox'))
    assert 'Exec="/home/fly/Documents/Projects/linux-osc-chatbox/.venv/bin/python"' in entry
    assert '/launch-chatbox.sh' not in entry
