from pathlib import Path
import importlib.util
import sys

ROOT = Path(__file__).resolve().parents[1]

def test_rpm_desktop_launcher():
    text = (ROOT/'packaging/fedora/flys-osc-chat-box.desktop').read_text()
    assert 'Exec=flys-osc-chat-box' in text
    assert "Name=Fly's OSC Chat Box" in text

def test_rpm_no_pip_during_install():
    spec = (ROOT/'packaging/fedora/flys-osc-chat-box.spec').read_text()
    assert 'Requires:       python3-pyside6' in spec
    assert 'Requires:       python3-psutil' in spec
    assert '%post' not in spec
    assert 'pip install' not in spec

def test_user_uninstall_keeps_settings_by_default():
    text = (ROOT/'scripts/uninstall.sh').read_text()
    assert 'PURGE=false' in text
    assert 'if [[ "$PURGE" == true ]]' in text
    assert 'flys-osc-chat-box-uninstall.desktop' in text

def test_osc_fallback_encoding():
    import importlib.util
    spec = importlib.util.spec_from_file_location('simpleosc', ROOT/'core/simple_osc.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    b = module._osc_message('/chatbox/input', ['Test', True, False])
    assert b.startswith(b'/chatbox/input\x00')
    assert b',sTF\x00' in b
    assert b'Test\x00' in b
