from pathlib import Path
import subprocess
import sys
from scripts.package_release import pack

ROOT = Path(__file__).resolve().parents[1]

def test_install_script_shell_syntax():
    subprocess.run(['bash', '-n', str(ROOT/'scripts/install.sh')], check=True)
    subprocess.run(['bash', '-n', str(ROOT/'scripts/uninstall.sh')], check=True)

def test_installer_keeps_config_and_direct_python():
    s = (ROOT/'scripts/install.sh').read_text()
    assert 'linux-osc-chatbox' in s
    assert 'settings.json.pre-v1.1' in s
    assert 'Exec="$VENV/bin/python" "$APP_DIR/main.py"' in s
    assert 'rm -rf -- "$CONFIG_DIR"' not in s

def test_release_archive_excludes_personal_files():
    import zipfile
    z, t = pack('test-release')
    with zipfile.ZipFile(z) as a:
        names = a.namelist()
        assert any(x.endswith('scripts/install.sh') for x in names)
        assert not any('/.venv/' in x or '/__pycache__/' in x or 'settings.json' in x for x in names)
        info = next(i for i in a.infolist() if i.filename.endswith('scripts/install.sh'))
        assert ((info.external_attr >> 16) & 0o111) != 0
    z.unlink();t.unlink()
