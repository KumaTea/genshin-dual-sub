"""几何计算：分辨率归类、区域换算。"""

import pytest

from ocr.configs import (
    ASPECT_16_9,
    ASPECT_WIDE,
    aspect_class,
    dialog_area,
    parse_resolution,
    speaker_band,
)


@pytest.mark.parametrize('width,height,expected', [
    (1920, 1080, ASPECT_16_9),
    (2560, 1440, ASPECT_16_9),
    (3840, 2160, ASPECT_16_9),
    (1280, 720, ASPECT_16_9),
    (2560, 1080, ASPECT_WIDE),
    (3440, 1440, ASPECT_WIDE),
    (3840, 1600, ASPECT_WIDE),
])
def test_aspect_class(width, height, expected):
    assert aspect_class(width, height) == expected


@pytest.mark.parametrize('width,height', [
    (3840, 2160), (3840, 1600), (2560, 1440), (2560, 1080), (1920, 1080), (1280, 720),
])
@pytest.mark.parametrize('layout', ['chat', 'idle', 'type2', None])
def test_dialog_area_is_sane(width, height, layout):
    """任意分辨率都要能算出区域，且落在画面内、下半屏。"""
    left, top, right, bottom = dialog_area(width, height, layout)
    assert 0 <= left < right <= width
    assert 0 <= top < bottom <= height
    assert top > height / 2, '对话区应该在画面下半部分'


def test_dialog_area_covers_measured_text():
    """3840x2160 下实测的正文位置必须落在裁切区里。"""
    # (版式, 文本上边, 文本下边)
    measured = [('chat', 1826, 1954), ('type2', 1827, 1881), ('idle', 1763, 1810)]
    for layout, text_top, text_bottom in measured:
        _, top, _, bottom = dialog_area(3840, 2160, layout)
        assert top < text_top, f'{layout} 上边界切到文字了'
        assert bottom > text_bottom, f'{layout} 下边界切到文字了'


def test_dialog_area_covers_measured_text_wide():
    """3840x1600 同上。"""
    measured = [('chat', 1332, 1371), ('type2', 1358, 1397)]
    for layout, text_top, text_bottom in measured:
        _, top, _, bottom = dialog_area(3840, 1600, layout)
        assert top < text_top
        assert bottom > text_bottom


def test_union_area_covers_every_layout():
    """不知道版式时给的并集要能盖住所有版式。"""
    for width, height in ((3840, 2160), (3840, 1600)):
        union = dialog_area(width, height, None)
        for layout in ('chat', 'idle', 'type2'):
            area = dialog_area(width, height, layout)
            assert union[0] <= area[0] and union[1] <= area[1]
            assert union[2] >= area[2] and union[3] >= area[3]


def test_speaker_band_above_dialog():
    """名字横条要在正文上方，否则版式判定会读到正文。"""
    for width, height in ((3840, 2160), (3840, 1600), (1920, 1080)):
        _, band_top, _, band_bottom = speaker_band(width, height)
        _, chat_top, _, _ = dialog_area(width, height, 'chat')
        assert band_top < chat_top
        assert band_bottom <= chat_top + (height * 0.02)


@pytest.mark.parametrize('text,expected', [
    ('3840x2160', (3840, 2160)),
    ('1920X1080', (1920, 1080)),
    ('', None),
    ('abc', None),
    ('1920', None),
])
def test_parse_resolution(text, expected):
    assert parse_resolution(text) == expected
