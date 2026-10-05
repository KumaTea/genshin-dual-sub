"""排版与背景透明度。"""

import numpy as np
import pytest

from ovl.render import Renderer, blank


@pytest.fixture(scope='module')
def renderer():
    return Renderer(800, 160, None, 40, 20)


def test_blank_is_fully_transparent():
    rgb, alpha = blank(320, 64)
    assert rgb.shape == (64, 320, 3)
    assert alpha.shape == (64, 320)
    assert not alpha.any()


def test_background_opacity_scales_alpha(renderer):
    for opacity, expected in ((0, 0), (50, 128), (100, 255)):
        _, alpha = renderer.render([], (255, 255, 255), (0, 0, 0), opacity)
        assert abs(int(alpha[0, 0]) - expected) <= 1, f'{opacity}% 的 alpha 不对'


def test_opacity_is_clamped(renderer):
    _, low = renderer.render([], (255, 255, 255), (0, 0, 0), -50)
    _, high = renderer.render([], (255, 255, 255), (0, 0, 0), 500)
    assert low[0, 0] == 0
    assert high[0, 0] == 255


def test_background_colour_is_used(renderer):
    rgb, _ = renderer.render([], (255, 255, 255), (10, 20, 30), 100)
    assert tuple(rgb[0, 0]) == (10, 20, 30)


def test_text_is_opaque_over_transparent_background(renderer):
    """背景全透明时文字仍然必须不透明，否则字幕根本看不见。"""
    _, alpha = renderer.render([('テスト文字', ())], (255, 255, 255), (0, 0, 0), 0)
    assert alpha.max() == 255, '文字应该是不透明的'
    assert alpha.min() == 0, '背景应该是透明的'


def test_text_colour_is_applied(renderer):
    rgb, alpha = renderer.render([('テスト', ())], (255, 0, 0), (0, 0, 0), 0)
    opaque = alpha == 255
    assert opaque.any()
    reds = rgb[:, :, 0][opaque]
    greens = rgb[:, :, 1][opaque]
    assert reds.mean() > greens.mean() + 50, '文字应该被染成红色'


def test_layout_is_horizontally_centred(renderer):
    _, alpha = renderer.render([('中', ())], (255, 255, 255), (0, 0, 0), 0)
    columns = np.nonzero(alpha.any(axis=0))[0]
    centre = (columns.min() + columns.max()) / 2
    assert abs(centre - renderer.width / 2) < renderer.width * 0.05


def test_long_line_is_shrunk_to_fit(renderer):
    long_text = '長い' * 60
    _, alpha = renderer.render([(long_text, ())], (255, 255, 255), (0, 0, 0), 0)
    columns = np.nonzero(alpha.any(axis=0))[0]
    assert columns.max() < renderer.width, '长句应该缩小到窗口内'


def test_two_ruby_rows_stack_above_text(renderer):
    """两行注音要一行叠一行，都在正文上方。"""
    blits = renderer.layout([('常夜', ('じょうや', '常世'))])
    assert len(blits) == 3  # 正文 + 两行注音
    text_rect = blits[0][1]
    reading_rect, official_rect = blits[1][1], blits[2][1]
    assert reading_rect.bottom <= text_rect.top
    assert official_rect.bottom <= reading_rect.top


def test_single_ruby_row(renderer):
    blits = renderer.layout([('漢字', ('かんじ',))])
    assert len(blits) == 2
    assert blits[1][1].bottom <= blits[0][1].top


def test_ruby_is_centred_over_its_base(renderer):
    # layout 的产出顺序：每段先是正文，紧跟它自己的注音行
    blits = renderer.layout([('あ', ()), ('漢字', ('かんじ',)), ('い', ())])
    assert len(blits) == 4
    base_rect = blits[1][1]
    ruby_rect = blits[2][1]
    assert ruby_rect.bottom <= base_rect.top
    assert abs(ruby_rect.centerx - base_rect.centerx) <= 2


def test_empty_segments_render_nothing(renderer):
    assert renderer.layout([]) == []
