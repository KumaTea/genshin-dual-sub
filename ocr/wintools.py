# tools.py will result in the following error:
# ImportError: cannot import name 'get_window_handle' from 'tools'
# (...\Lib\site-packages\paddleocr\tools/__init__.py)


import ctypes
import win32gui
import numpy as np


DWMWA_EXTENDED_FRAME_BOUNDS = 9


def crop_image(image: np.ndarray, box: tuple[int, int, int, int]) -> np.ndarray:
    return image[box[1]:box[3], box[0]:box[2]]


def get_window_handle(title: str) -> int:
    hwnd = win32gui.FindWindow(None, title)
    return hwnd


def get_borderless_coordinates(hwnd: int) -> tuple[int, int, int, int]:
    return win32gui.GetWindowRect(hwnd)


def get_windowed_coordinates(hwnd: int) -> tuple[int, int, int, int]:
    # https://stackoverflow.com/a/13459850/10714490
    get_win_attr = ctypes.windll.dwmapi.DwmGetWindowAttribute
    rect = ctypes.wintypes.RECT()
    get_win_attr(
        ctypes.wintypes.HWND(hwnd),
        ctypes.wintypes.DWORD(DWMWA_EXTENDED_FRAME_BOUNDS),
        ctypes.byref(rect),
        ctypes.sizeof(rect)
    )
    return rect.left, rect.top, rect.right, rect.bottom


def get_no_title_coordinates(hwnd: int) -> tuple[int, int, int, int]:
    # https://stackoverflow.com/a/54707314/10714490
    rect = win32gui.GetWindowRect(hwnd)
    left, top, right, bottom = rect
    client_rect = win32gui.GetClientRect(hwnd)
    c_left, c_top, c_right, c_bottom = client_rect

    window_offset = int((right - left - c_right) / 2)
    title_offset = (bottom - top - c_bottom) - window_offset
    new_rect = left + window_offset, top + title_offset, right - window_offset, bottom - window_offset
    return new_rect


def get_foreground_window_title() -> str:
    return win32gui.GetWindowText(win32gui.GetForegroundWindow())
