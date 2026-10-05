"""屏幕抓取。

dxcam 默认输出 RGB，这里显式要 BGR，让整个项目和 OpenCV / cv2.imread 保持一致。
"""

import ctypes
import logging
import threading
from typing import Optional

import numpy as np

_camera = None
_camera_lock = threading.Lock()

user32 = ctypes.windll.user32


def screen_size() -> tuple[int, int]:
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)


def get_camera():
    global _camera
    if _camera is not None:
        return _camera
    with _camera_lock:
        if _camera is None:
            import dxcam
            _camera = dxcam.create(output_color='BGR')
            if _camera is None:
                logging.error('[OCR]\t无法创建屏幕抓取器（dxcam）')
    return _camera


def release_camera() -> None:
    global _camera
    with _camera_lock:
        if _camera is not None:
            try:
                _camera.release()
            except Exception:  # dxcam 在关闭时偶尔会抛 COM 错误，不值得为此中断退出流程
                pass
            _camera = None


def grab_screenshot(left: int, top: int, right: int, bottom: int) -> Optional[np.ndarray]:
    """抓取屏幕上的一块区域，失败返回 None。"""
    if right <= left or bottom <= top:
        return None

    screen_width, screen_height = screen_size()
    left, top = max(0, left), max(0, top)
    right, bottom = min(screen_width, right), min(screen_height, bottom)
    if right <= left or bottom <= top:
        return None

    camera = get_camera()
    if camera is None:
        return None

    try:
        return camera.grab(region=(left, top, right, bottom))
    except Exception as e:
        logging.debug(f'[OCR]\t抓屏失败：{e}')
        return None
