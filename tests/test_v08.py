from core.sections import SectionComposer, SECTION_PRESETS, clean_sections
from core.settings import Settings


def test_presets_and_migration(tmp_path):
    f = tmp_path / 'settings.json'
    f.write_text('{"version":7,"template":"{status}","status_profiles":[{"name":"custom","text":"keep me","enabled":true}]}')
    s = Settings.load(f)
    assert s.section_mode is False and s.message_sections == []
    assert s.status_profiles[0]['text'] == 'keep me'
    assert sorted(SECTION_PRESETS) == ['AFK', 'Gaming', 'Music']


def test_section_rotation_is_independent():
    comp = SectionComposer()
    comp.started = 100
    secs = [{'name':'alternates','text':'default', 'enabled': True, 'interval': 5, 'options':['one {status}','two {status}']},
            {'name':'always', 'text':'{time}', 'enabled':True, 'interval':0}]
    assert comp.render(secs, {'status':'A','time':'12:34'}, now=101) == 'one A\n12:34'
    assert comp.render(secs, {'status':'A','time':'12:34'}, now=106) == 'two A\n12:34'
    assert comp.render(secs, {'status':'A','time':'12:34'}, now=111) == 'one A\n12:34'


def test_empty_disabled_and_maxlen():
    c = SectionComposer()
    sections = [{'name':'ignore','text':'hidden','enabled':False}, {'name':'visible','text':'X'*150, 'enabled':True}]
    assert c.render(sections, {}) == 'X'*144
    assert c.render([{'text':'{music}', 'enabled':True}], {'music':''}) == ''


def test_clean_untrusted_sections():
    assert clean_sections({'not':'list'}) == []
    items = clean_sections([{'name':'foo','text':'hello','options':['a','b'],'interval':'bad','enabled':0}, 'bad'])
    assert items == [{'name':'foo','text':'hello','options':['a','b'],'interval':0,'enabled':False}]


def test_settings_roundtrip_sections(tmp_path):
    f = tmp_path/'config.json'
    original = Settings(section_mode=True, message_sections=clean_sections(SECTION_PRESETS['Music']),
                        status_profiles=[{'name':'hello','text':'🌟 hi','enabled':True}],
                        custom_layouts={'old':'{status}'})
    original.save(f)
    restored = Settings.load(f)
    assert restored == original
    assert restored.status_profiles == original.status_profiles


def test_source_package_launcher_executable():
    from pathlib import Path
    p = Path(__file__).resolve().parents[1] / 'launch-chatbox.sh'
    assert p.exists()
