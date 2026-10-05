import time
from typing import Optional

import numpy as np

from ocr.screenshot import grab_screenshot
from ocr.session import gi

# 同一帧在这段时间内复用，避免"检测对话状态"和"识别文本"两个任务各抓一次屏
CACHE_SECONDS = 0.3


def take_screenshot(force: bool = False) -> Optional[np.ndarray]:
    if not force and gi.screenshot is not None and time.time() - gi.last_shot < CACHE_SECONDS:
        return gi.screenshot

    image = grab_screenshot(*gi.coords)
    if image is None or not image.any():
        # 抓失败（画面没变化时 dxcam 会返回 None）就沿用上一帧
        return gi.screenshot

    gi.screenshot = image
    gi.last_shot = time.time()
    return image
