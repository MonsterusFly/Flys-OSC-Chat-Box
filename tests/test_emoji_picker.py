from core.emojis import EMOJIS, matching_emojis


def test_every_emoji_has_readable_nonemoji_fallback():
    assert len(EMOJIS) >= 40
    assert all(name.isascii() and name.strip() for _, name in EMOJIS)


def test_search_returns_glyph_and_label():
    assert ('🦊', 'Fox') in matching_emojis('fox')
    assert ('🎵', 'Music') in matching_emojis('MUSIC')
    assert matching_emojis('unmatched string') == []


def test_search_no_filter_returns_all():
    assert matching_emojis('') == EMOJIS
