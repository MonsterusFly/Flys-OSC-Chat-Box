from pathlib import Path
from unittest.mock import patch
import hashlib
import io
import pytest
from core import updater


def test_semver_comparison():
    assert updater.version_tuple('v1.3.0') > updater.version_tuple('1.2.2')
    with pytest.raises(ValueError): updater.version_tuple('v1.3.0-rc1')
    with pytest.raises(ValueError): updater.version_tuple('bad')


def test_release_selects_matching_fedora_asset():
    name = 'flys-osc-chat-box-1.3.1-1.fc44.noarch.rpm'
    base = 'https://github.com/MonsterusFly/Flys-OSC-Chat-Box/releases/download/v1.3.1/'
    payload = {'tag_name': 'v1.3.1', 'draft': False, 'prerelease': False, 'assets': [
        {'name': name, 'browser_download_url': base + name},
        {'name': name+'.sha256', 'browser_download_url': base + name+'.sha256'}
    ]}
    with patch.object(updater, '_fetch_json', return_value=payload), patch.object(updater, 'fedora_version', return_value='44'):
        result = updater.check_release('1.3.0')
    assert result['version'] == '1.3.1'
    assert result['rpm_name'] == name
    assert result['checksum_url'] == base+name+'.sha256'


def test_no_update_and_missing_rpm():
    with patch.object(updater, '_fetch_json', return_value={'tag_name': 'v1.2.2'}):
        assert updater.check_release('1.3.0') is None
    with patch.object(updater, '_fetch_json', return_value={'tag_name': 'v1.3.1', 'assets': []}), patch.object(updater, 'fedora_version', return_value='44'):
        assert updater.check_release('1.3.0')['rpm_url'] is None


def test_checksum_validation_and_download(tmp_path):
    name='flys-osc-chat-box-1.3.1-1.fc44.noarch.rpm'
    base='https://github.com/MonsterusFly/Flys-OSC-Chat-Box/releases/download/v1.3.1/'
    data=b'fake-rpm-contents'
    digest=hashlib.sha256(data).hexdigest()
    class Response(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *_): self.close()
    def fetch(request, timeout=None):
        url=request.full_url
        return Response((f'{digest}  {name}\n'.encode() if url.endswith('.sha256') else data))
    release={'rpm_name':name,'rpm_url':base+name,'checksum_url':base+name+'.sha256'}
    with patch.object(updater, 'urlopen', side_effect=fetch), patch.dict('os.environ', {'XDG_CACHE_HOME': str(tmp_path)}):
        downloaded=updater.download_verified_rpm(release)
    assert downloaded.read_bytes()==data
    assert downloaded.name==name


def test_missing_checksum_rejected():
    with pytest.raises(ValueError, match='checksum'):
        updater.download_verified_rpm({'rpm_name':'flys-osc-chat-box-1.3.1-1.fc44.noarch.rpm', 'rpm_url':'https://github.com/MonsterusFly/Flys-OSC-Chat-Box/releases/download/v1.3.1/test'})


def test_no_rpm_install_from_source(tmp_path):
    with patch.object(updater, 'installed_via_rpm', return_value=False):
        with pytest.raises(RuntimeError, match='RPM installations'):
            updater.rpm_install_command(tmp_path/'update.rpm')


def test_private_repo_404_error_is_actionable():
    from urllib.error import HTTPError
    error = HTTPError(updater.RELEASE_API, 404, 'Not Found', {}, None)
    with patch.object(updater, '_fetch_json', side_effect=error):
        with pytest.raises(updater.UpdateCheckError, match='private'):
            updater.check_release('1.3.0')


def test_release_notes_and_file_size():
    name = 'flys-osc-chat-box-1.3.1-1.fc44.noarch.rpm'
    payload = {'tag_name': 'v1.3.1', 'body': 'Fix music panel', 'assets': [
        {'name': name, 'size': 1048576,
         'browser_download_url': 'https://github.com/MonsterusFly/Flys-OSC-Chat-Box/releases/download/v1.3.1/' + name}
    ]}
    with patch.object(updater, '_fetch_json', return_value=payload), patch.object(updater, 'fedora_version', return_value='44'):
        result = updater.check_release('1.3.0')
    assert result['notes'] == 'Fix music panel'
    assert updater.human_size(result['rpm_size']) == '1.0 MiB'


def test_auto_download_setting_roundtrip(tmp_path):
    from core.settings import Settings
    path = tmp_path / 'settings.json'
    Settings(auto_download_updates=True).save(path)
    assert Settings.load(path).auto_download_updates is True


def test_no_rpm_install_when_running_source_even_if_system_rpm_installed():
    with patch.object(updater.Path, 'exists', return_value=True), patch.object(updater.shutil, 'which', return_value='/usr/bin/rpm'):
        assert updater.installed_via_rpm() is False
