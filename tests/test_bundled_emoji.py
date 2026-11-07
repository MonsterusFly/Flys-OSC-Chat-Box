from io import BytesIO
from PIL import Image
from core.emojis import EMOJIS
from core.emoji_assets import emoji_icon_path

def test_every_emoji_has_real_bundled_icon():
    for char, name in EMOJIS:
        path = emoji_icon_path(char)
        assert path is not None, name
        with Image.open(BytesIO(path.read_bytes())) as img:
            assert img.size == (64, 64)
            assert img.convert("RGBA").getbbox() is not None, name

def test_unknown_emoji_has_no_asset():
    assert emoji_icon_path("NOT AN EMOJI") is None
