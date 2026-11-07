from core.emoji_preview import rich_emoji_preview


def test_bundled_emoji_becomes_image():
    text = rich_emoji_preview('Hi 😀!')
    assert '<img src=' in text
    assert 'Hi ' in text
    assert 'width="20"' in text


def test_escapes_user_text():
    text = rich_emoji_preview('<script>&\nhello')
    assert '<script>' not in text
    assert '&lt;script&gt;&amp;<br/>hello' in text


def test_multiple_unicode_sequences():
    text = rich_emoji_preview('❤️ 💜 🎮')
    assert text.count('<img') == 3


def test_no_emoji_uses_original_plain_text():
    assert 'normal text' in rich_emoji_preview('normal text')
