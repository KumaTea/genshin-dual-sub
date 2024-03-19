import dxcam
import ctypes
import numpy as np
from typing import Optional
from _ctypes import COMError
from ocr.wintools import get_window_handle, get_borderless_coordinates, get_no_title_coordinates


DWMWA_EXTENDED_FRAME_BOUNDS = 9

camera = dxcam.create()

screen_width = ctypes.windll.user32.GetSystemMetrics(0)
screen_height = ctypes.windll.user32.GetSystemMetrics(1)


def grab_screenshot(left: int, top: int, right: int, bottom: int) -> np.ndarray:
    if not right or not bottom:
        return np.zeros((bottom - top, right - left, 3), dtype=np.uint8)
    left = max(0, left)
    top = max(0, top)
    right = min(screen_width, right)
    bottom = min(screen_height, bottom)
    try:
        return camera.grab(region=(left, top, right, bottom))
    except COMError:
        return np.zeros((bottom - top, right - left, 3), dtype=np.uint8)


def screenshot(title: str, borderless: bool = False) -> Optional[np.ndarray]:
    hwnd = get_window_handle(title)
    if not hwnd:
        return None
    if borderless:
        coordinates = get_borderless_coordinates(hwnd)
    else:
        # coordinates = get_windowed_coordinates(hwnd)
        coordinates = get_no_title_coordinates(hwnd)
    if not any(coordinates):
        return None
    return grab_screenshot(*coordinates)
