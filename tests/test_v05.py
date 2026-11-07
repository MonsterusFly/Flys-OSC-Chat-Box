from integrations.music import Track, styled_progress_bar, control_player
from core.message_engine import render_template, SUPPORTED_VARIABLES


def test_music_bar_styles():
    track = Track(title='Track', duration_seconds=100, position_seconds=50, playing=False)
    assert styled_progress_bar(track, 'Squares', 4) == '■■□□'
    assert styled_progress_bar(track, 'Circles', 4) == '●●○○'
    assert styled_progress_bar(track, 'ASCII', 4) == '##--'
    assert styled_progress_bar(Track(), 'Squares') == ''


def test_unsupported_control_is_rejected():
    assert not control_player('spotify', 'invalid')
    assert not control_player('', 'next')


def test_status_token():
    assert render_template('{status}', {'status': 'In VRChat'}) == 'In VRChat'
