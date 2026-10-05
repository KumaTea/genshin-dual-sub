"""字幕窗口的几何计算。"""

import ctypes

from share.config import settings

user32 = ctypes.windll.user32


def screen_size() -> tuple[int, int]:
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)


def window_geometry() -> tuple[int, int, int, int]:
    """(x, y, width, height)。width=0 表示与屏幕同宽，x/y = -1 表示用默认位置。"""
    screen_width, screen_height = screen_size()

    width = settings.int('overlay', 'width') or screen_width
    height = max(40, settings.int('overlay', 'height'))
    width = max(120, min(width, screen_width))

    x = settings.int('overlay', 'x')
    y = settings.int('overlay', 'y')
    if x < 0:
        x = (screen_width - width) // 2
    if y < 0:
        y = screen_height - height

    return x, y, width, height


def clamp_to_screen(x: int, y: int, width: int, height: int) -> tuple[int, int]:
    """别让窗口被拖到屏幕外面找不回来。"""
    screen_width, screen_height = screen_size()
    margin = 40
    x = max(margin - width, min(x, screen_width - margin))
    y = max(0, min(y, screen_height - margin))
    return x, y


FPS = max(1, settings.int('overlay', 'fps'))
