"""聊天版式识别。

从整屏截图里判断当前是哪种聊天版式，判据是说话人名字的颜色——
这个颜色不随角色、场景变化，比 OCR 便宜三个数量级。

只在名字所在的横条里找颜色，而不是全屏找：全屏的话任务追踪箭头、
元素图标之类的金色都会误判成"正在对话"。
"""

from typing import Optional

import numpy as np

from ocr.configs import (
    COLOR_MIN_PIXELS,
    COLOR_TOLERANCE,
    LAYOUT_PRIORITY,
    SPEAKER_COLORS,
    speaker_band,
)
from ocr.imgtools import count_color, crop


def detect_layout(image: np.ndarray) -> Optional[str]:
    """返回 'chat' / 'idle' / 'type2'，都不匹配则 None（没在对话）。"""
    if image is None or image.size == 0:
        return None

    height, width = image.shape[:2]
    band = crop(image, speaker_band(width, height))
    if band.size == 0:
        return None

    # 分辨率越高，同一个字的像素越多，阈值跟着画面面积走
    min_pixels = max(60, int(COLOR_MIN_PIXELS * (width * height) / (3840 * 2160)))

    best_layout, best_count = None, min_pixels
    for layout in LAYOUT_PRIORITY:
        count = count_color(band, SPEAKER_COLORS[layout], COLOR_TOLERANCE)
        if count > best_count:
            best_layout, best_count = layout, count

    return best_layout
