"""对话文本识别。

流程：滤白 -> 检测文本框 -> 合并同一行的框 -> 丢掉噪点 -> 居中校验 -> 批量识别。

几个关键点：

* 合并同一行的框时限制水平间距。检测器有时会把远处的亮色背景（雪地、灯光）
  也框出来，不限距离就会把它和正文合并成一个横跨整屏的框，识别结果全是废话。
* 原神的对话是逐字显现的，没打完的行不居中。所以先看框居不居中，
  不居中就说明字还没出全，直接跳过这一帧。chat / idle 是每行各自居中，
  逐行检查；type2 整块居中、行内左对齐（第二行天生靠左），只能检查整块。
* 噪点框按"比最高的框矮多少"来丢。大世界里的 type2 字幕上下就贴着
  发光图标和血条数字，阈值松了它们会被拼进识别结果。
* 识别是批量做的。逐张调用会让推理引擎每次重新分配输入张量，
  两行文本的开销几乎翻倍。
"""

import logging
from typing import Optional

import numpy as np

from ocr.imgtools import crop, filter_white
from ocr.session import engine_call_lock, get_engine

Box = list[list[float]]

# 同一行的两个框，水平间距不超过行高的多少倍才合并
MAX_MERGE_GAP_RATIO = 2.0
# 框高低于最高框的多少比例就当噪点丢掉。
# 正文换行时各行高度几乎一样（实测 49/54、51/56），而血条数字、
# 图标残片只有正文的一半高，0.7 能把它们切干净。
MIN_BOX_HEIGHT_RATIO = 0.7
# 框宽小于行高的多少倍就当噪点丢掉
MIN_BOX_WIDTH_RATIO = 0.5


def box_bounds(box: Box) -> tuple[float, float, float, float]:
    """四点框 -> (left, top, right, bottom)。检测器给的是四边形，取外接矩形。"""
    xs = [point[0] for point in box]
    ys = [point[1] for point in box]
    return min(xs), min(ys), max(xs), max(ys)


def make_box(left: float, top: float, right: float, bottom: float) -> Box:
    return [[left, top], [right, top], [right, bottom], [left, bottom]]


def is_same_line(box1: Box, box2: Box, overlap_ratio: float = 0.5) -> bool:
    """两个框在垂直方向重叠超过较矮者的一半，就算同一行。

    比原先"上下边界差值小于画面宽度的 2%"稳：那个写法在 4K 下容差有 60 多像素，
    上下两行会被判成同一行。
    """
    _, top1, _, bottom1 = box_bounds(box1)
    _, top2, _, bottom2 = box_bounds(box2)
    height1, height2 = bottom1 - top1, bottom2 - top2
    if height1 <= 0 or height2 <= 0:
        return False
    overlap = min(bottom1, bottom2) - max(top1, top2)
    return overlap > overlap_ratio * min(height1, height2)


def merge_boxes(boxes: list[Box]) -> list[Box]:
    """把同一行、且挨得够近的框合并成一个。"""
    if len(boxes) < 2:
        return boxes

    # 先按 (上边界, 左边界) 排序，保证同一行的框相邻且从左到右
    ordered = sorted(boxes, key=lambda b: (box_bounds(b)[1], box_bounds(b)[0]))

    merged: list[Box] = []
    current = ordered[0]
    for box in ordered[1:]:
        left, top, right, bottom = box_bounds(current)
        next_left, next_top, next_right, next_bottom = box_bounds(box)
        # 两个区间之间的真实水平距离，重叠时为负。
        # 不能直接写 next_left - right：排序是按上边界来的，同一行里
        # 上边界差一两个像素就可能把靠右的框排到靠左的前面，那样算出来
        # 是个大负数，"间距够近"的判断就永远成立，远处的噪点会被并进正文。
        gap = max(left, next_left) - min(right, next_right)
        line_height = max(bottom - top, next_bottom - next_top)
        if is_same_line(current, box) and gap <= MAX_MERGE_GAP_RATIO * line_height:
            current = make_box(
                min(left, next_left), min(top, next_top),
                max(right, next_right), max(bottom, next_bottom),
            )
        else:
            merged.append(current)
            current = box
    merged.append(current)

    merged.sort(key=lambda b: box_bounds(b)[1])
    return merged


def drop_noise_boxes(boxes: list[Box]) -> list[Box]:
    """丢掉明显不是文本行的小框。"""
    if not boxes:
        return boxes

    heights = [box_bounds(b)[3] - box_bounds(b)[1] for b in boxes]
    tallest = max(heights)
    if tallest <= 0:
        return []

    kept = []
    for box, height in zip(boxes, heights):
        left, _, right, _ = box_bounds(box)
        if height < MIN_BOX_HEIGHT_RATIO * tallest:
            continue
        if right - left < MIN_BOX_WIDTH_RATIO * height:
            continue
        kept.append(box)
    return kept


def _is_centered(left: float, right: float, image_width: int, tolerance: float) -> bool:
    center = (left + right) / 2
    offset = abs(center - image_width / 2)
    if offset > tolerance * image_width:
        logging.debug(
            f'[OCR]	文本未居中，字应该还没出全: '
            f'x={center:.0f}, w={image_width}, 偏移={offset / image_width:.2f}'
        )
        return False
    return True


def boxes_at_center(
        boxes: list[Box],
        image_width: int,
        tolerance: float = 0.06,
        per_line: bool = True,
) -> bool:
    """判断这一帧的字是不是已经出全了。

    per_line=True：每行都要各自居中（chat / idle）。
    per_line=False：只要整块居中就行。type2 是整块居中、行内左对齐，
    第二行天生靠左，逐行检查会把所有多行的 type2 字幕都判成"还没打完"。
    """
    if not boxes:
        return False

    bounds = [box_bounds(b) for b in boxes]
    if not per_line:
        return _is_centered(
            min(b[0] for b in bounds), max(b[2] for b in bounds), image_width, tolerance)

    return all(_is_centered(b[0], b[2], image_width, tolerance) for b in bounds)


def detect_boxes(image: np.ndarray) -> list[Box]:
    engine = get_engine()
    with engine_call_lock:
        result = engine(image, use_det=True, use_cls=False, use_rec=False)
    # RapidOCR 没找到字时 boxes 是 None，找到了是 N×4×2 的 float32 数组
    if result.boxes is None or len(result.boxes) == 0:
        return []
    return drop_noise_boxes(merge_boxes(result.boxes.tolist()))


def recognize(images: list[np.ndarray]) -> list[str]:
    """批量识别，返回与输入等长的文本列表。"""
    if not images:
        return []
    from rapidocr.ch_ppocr_rec import TextRecInput

    engine = get_engine()
    with engine_call_lock:
        result = engine.text_rec(TextRecInput(img=images))
    return [text or '' for text in result.txts]


def do_ocr(image: np.ndarray, per_line_centered: bool = True) -> str:
    """对已经裁好的对话区域做识别，返回拼好的整段文本。"""
    if image is None or image.size == 0:
        return ''

    image = filter_white(image)

    boxes = detect_boxes(image)
    if not boxes:
        logging.debug('[OCR]\t未识别到对话框')
        return ''

    if not boxes_at_center(boxes, image.shape[1], per_line=per_line_centered):
        return ''

    crops = [crop(image, tuple(int(v) for v in box_bounds(box))) for box in boxes]
    crops = [c for c in crops if c.size > 0]
    if not crops:
        return ''

    return ''.join(recognize(crops))


def do_ocr_raw(image: np.ndarray) -> str:
    """跳过检测，直接把整张图当成一行来识别。"""
    texts = recognize([image])
    return texts[0] if texts else ''


def ocr_dialog(
        image: np.ndarray,
        area: tuple[int, int, int, int],
        per_line_centered: bool = True,
) -> Optional[str]:
    text = do_ocr(crop(image, area), per_line_centered)
    return text or None
