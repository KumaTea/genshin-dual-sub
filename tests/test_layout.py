"""用 debug/ 下的真实截图验证版式识别和 OCR。

截图文件名里带着期望的版式，所以可以直接当断言用。
"""

import os

import cv2
import pytest

from conftest import DEBUG_DIR, has_screenshots
from ocr.configs import dialog_area, lines_centered
from ocr.imgtools import crop
from ocr.layout import detect_layout

pytestmark = pytest.mark.skipif(not has_screenshots(), reason='缺少 debug/ 截图')

# 截图里含有游戏画面以外的部分，实际运行时 gi.coords 会裁掉，测试里手动裁。
# * _at_3840_2160：3840x1600 的游戏跑在 4K 桌面上，上下有黑边
# * _window_：窗口模式，1924x1140 的截图里客户区是 (2, 58) 起的 1920x1080，
#   和 get_no_title_coordinates 算出来的一致
LETTERBOXED = {
    'genshin_3840_1600_at_3840_2160.png': (0, 280, 3840, 1880),
    'genshin_1920_1080_window_default.png': (2, 58, 1922, 1138),
    'genshin_1920_1080_windowd_chatTypeIdle.png': (2, 58, 1922, 1138),
}


def expected_layout(filename: str) -> str:
    lowered = filename.lower()
    if 'chattype2' in lowered:
        return 'type2'
    if 'chattypeidle' in lowered:
        return 'idle'
    return 'chat'


def screenshots() -> list[str]:
    if not os.path.isdir(DEBUG_DIR):
        return []
    return sorted(f for f in os.listdir(DEBUG_DIR) if f.endswith('.png'))


def load(filename: str):
    image = cv2.imread(os.path.join(DEBUG_DIR, filename))
    assert image is not None, f'读不出 {filename}'
    if filename in LETTERBOXED:
        image = crop(image, LETTERBOXED[filename])
    return image


@pytest.mark.parametrize('filename', screenshots())
def test_detect_layout(filename):
    image = load(filename)
    assert detect_layout(image) == expected_layout(filename)


@pytest.mark.parametrize('filename', screenshots())
def test_dialog_text_is_recognised(filename):
    """每张截图都应该识别出一段非空的中文对话。"""
    from ocr.ocr import do_ocr

    image = load(filename)
    height, width = image.shape[:2]
    layout = detect_layout(image)
    # 和 ocr/gs/dialog.py 走同一条路径：不同版式的对齐方式不一样
    text = do_ocr(crop(image, dialog_area(width, height, layout)),
                  lines_centered(layout))

    assert text, f'{filename} 没识别出文本'
    assert len(text) >= 8, f'{filename} 识别结果太短：{text!r}'
    chinese = sum(1 for char in text if '一' <= char <= '鿿')
    assert chinese >= len(text) * 0.5, f'{filename} 结果里中文太少：{text!r}'


def test_blank_image_is_not_talking():
    import numpy as np

    assert detect_layout(np.zeros((1080, 1920, 3), dtype=np.uint8)) is None
    assert detect_layout(np.full((1080, 1920, 3), 255, dtype=np.uint8)) is None


def test_type2_second_line_is_left_aligned():
    """type2 整块居中、行内左对齐，第二行本来就不居中。

    按行判断居中会把所有多行的 type2 字幕都当成"字还没打完"而丢掉。
    """
    from ocr.ocr import box_bounds, detect_boxes
    from ocr.imgtools import filter_white

    image = load('genshin_3840_2160_chatType2_long.png')
    height, width = image.shape[:2]
    area = dialog_area(width, height, 'type2')
    sub = filter_white(crop(image, area))
    boxes = detect_boxes(sub)

    assert len(boxes) == 2, f'应该检测到两行，实际 {len(boxes)}'
    centers = [(box_bounds(b)[0] + box_bounds(b)[2]) / 2 for b in boxes]
    middle = sub.shape[1] / 2
    assert abs(centers[0] - middle) < sub.shape[1] * 0.06, '第一行应该居中'
    assert abs(centers[1] - middle) > sub.shape[1] * 0.06, '第二行应该明显靠左'
    assert lines_centered('type2') is False


def test_type2_appears_at_two_heights():
    """type2 在剧情里和在大世界里高度不同，裁切区要同时盖住两种。"""
    _, top, _, bottom = dialog_area(3840, 2160, 'type2')
    assert top < 1765, '盖不住大世界里的那一版'
    assert bottom > 1956, '盖不住剧情里换行后的第二行'


def test_distant_noise_is_not_merged_into_the_text():
    """远处的亮色块不能和正文并成一个横跨整屏的框。

    merge_boxes 排序是按上边界来的，靠右的框可能排在靠左的框前面，
    水平间距要按区间距离算，不能直接相减。
    """
    from ocr.ocr import box_bounds, merge_boxes, make_box

    text_box = make_box(808, 12, 2222, 71)
    far_noise = make_box(2869, 10, 2965, 40)
    merged = merge_boxes([text_box, far_noise])
    assert len(merged) == 2, f'隔了 600 多像素不该合并：{merged}'

    near = make_box(2260, 12, 2300, 71)
    assert len(merge_boxes([text_box, near])) == 1, '同一行挨着的应该合并'


def test_small_ui_text_is_dropped():
    """血条数字、图标残片比正文矮得多，要当噪点丢掉。"""
    from ocr.ocr import drop_noise_boxes, make_box

    line = make_box(300, 0, 2200, 60)
    hp_text = make_box(1400, 190, 1700, 220)
    kept = drop_noise_boxes([line, hp_text])
    assert kept == [line]

    second_line = make_box(300, 70, 900, 125)
    assert len(drop_noise_boxes([line, second_line])) == 2, '正常的第二行不能被丢掉'
