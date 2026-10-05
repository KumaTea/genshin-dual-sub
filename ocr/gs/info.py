import logging
from typing import Optional

from ocr.session import gi
from ocr.wintools import (
    get_foreground_window_title,
    get_no_title_coordinates,
    get_window_handle,
)
from share.config import settings

GENSHIN_TITLES = ('原神', 'Genshin Impact')

# 低于这个尺寸多半是最小化或者刚启动，不当成有效分辨率
MIN_RESOLUTION = (640, 360)

_warned_bad_region = False


def find_genshin_window() -> int:
    for title in GENSHIN_TITLES:
        hwnd = get_window_handle(title)
        if hwnd:
            return hwnd
    return 0


def capture_region() -> Optional[tuple[int, int, int, int]]:
    """配置里写死的抓取区域，格式 left,top,right,bottom。

    填了就不再去找游戏窗口——串流、改过标题的客户端、或者干脆想抓
    别的窗口时用得上。注意这里要给游戏画面的完整范围，因为对话区的
    位置是按画面比例算出来的，只圈字幕那一条会算歪。
    """
    global _warned_bad_region
    raw = settings.get('game', 'capture_region').strip()
    if not raw:
        return None

    try:
        left, top, right, bottom = (int(part) for part in raw.replace('，', ',').split(','))
    except ValueError:
        if not _warned_bad_region:
            logging.error(f'[OCR]\tcapture_region 格式不对：{raw!r}，应为 left,top,right,bottom')
            _warned_bad_region = True
        return None

    if right - left < MIN_RESOLUTION[0] or bottom - top < MIN_RESOLUTION[1]:
        if not _warned_bad_region:
            logging.error(f'[OCR]\tcapture_region 太小：{raw!r}')
            _warned_bad_region = True
        return None

    _warned_bad_region = False
    return left, top, right, bottom


def check_genshin_info() -> int:
    region = capture_region()
    if region:
        if not gi.running:
            logging.info(f'[OCR]\t使用固定抓取区域 {region}，不再跟随游戏窗口')
        gi.running = True
        gi.coords = region
        gi.set_resolution(region[2] - region[0], region[3] - region[1])
        return gi.hwnd

    hwnd = find_genshin_window()
    changed = hwnd != gi.hwnd

    if not hwnd:
        if changed:
            logging.info('[OCR]\t原神，关闭！')
        gi.hwnd, gi.running, gi.coords = 0, False, (0, 0, 0, 0)
        return 0

    if changed:
        logging.info(f'[OCR]\t原神，启动！hwnd={hwnd}')
    gi.hwnd, gi.running = hwnd, True
    gi.coords = get_no_title_coordinates(hwnd)

    width = gi.coords[2] - gi.coords[0]
    height = gi.coords[3] - gi.coords[1]
    if width >= MIN_RESOLUTION[0] and height >= MIN_RESOLUTION[1]:
        gi.set_resolution(width, height)
    return hwnd


def check_genshin_foreground() -> bool:
    """只在游戏前台时工作可以省下大量抓屏和 OCR，但不是所有人都要这个。

    关掉 require_foreground 之后一律当作在前台，窗口化游戏、双屏、
    或者一边看攻略一边挂着字幕的场景就能用了。
    """
    if not settings.bool('game', 'require_foreground'):
        if not gi.foreground:
            gi.foreground = True
            logging.info('[OCR]\t已忽略游戏前台状态，将持续识别')
        return True

    status = get_foreground_window_title() in GENSHIN_TITLES
    if status == gi.foreground:
        return status

    gi.foreground = status
    logging.debug(f'[OCR]\t原神前台状态：{status}')
    return status
