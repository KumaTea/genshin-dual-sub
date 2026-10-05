import ctypes
from ctypes import wintypes

import win32gui

DWMWA_EXTENDED_FRAME_BOUNDS = 9


def get_window_handle(title: str) -> int:
    return win32gui.FindWindow(None, title)


def get_borderless_coordinates(hwnd: int) -> tuple[int, int, int, int]:
    return win32gui.GetWindowRect(hwnd)


def get_windowed_coordinates(hwnd: int) -> tuple[int, int, int, int]:
    # https://stackoverflow.com/a/13459850/10714490
    rect = wintypes.RECT()
    ctypes.windll.dwmapi.DwmGetWindowAttribute(
        wintypes.HWND(hwnd),
        wintypes.DWORD(DWMWA_EXTENDED_FRAME_BOUNDS),
        ctypes.byref(rect),
        ctypes.sizeof(rect),
    )
    return rect.left, rect.top, rect.right, rect.bottom


def get_no_title_coordinates(hwnd: int) -> tuple[int, int, int, int]:
    """去掉边框和标题栏后的客户区坐标。"""
    # https://stackoverflow.com/a/54707314/10714490
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    _, _, client_right, client_bottom = win32gui.GetClientRect(hwnd)

    window_offset = int((right - left - client_right) / 2)
    title_offset = (bottom - top - client_bottom) - window_offset
    return left + window_offset, top + title_offset, right - window_offset, bottom - window_offset


def get_foreground_window_title() -> str:
    return win32gui.GetWindowText(win32gui.GetForegroundWindow())
