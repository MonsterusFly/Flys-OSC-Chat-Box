from io import BytesIO
from PIL import Image
from core.emoji_icons import emoji_font_path, emoji_png


def test_empty_and_invalid_sizes():
    assert emoji_png('', 40) is None
    assert emoji_png('🦊', 0) is None


def test_icon_is_png_when_local_font_available():
    if emoji_font_path() is None:
        assert emoji_png('🦊') is None
        return
    blob = emoji_png('🦊', 44)
    assert blob is not None
    image = Image.open(BytesIO(blob))
    assert image.size == (44, 44)
    assert image.getbbox() is not None


def test_several_emoji_can_be_rendered():
    if emoji_font_path() is None:
        return
    for char in ('❤️', '🎵', '🥺', '🦊'):
        assert emoji_png(char, 42)
