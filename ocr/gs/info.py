import logging
from ocr.session import gi
from ocr.wintools import get_window_handle, get_no_title_coordinates, get_foreground_window_title


genshin_titles = {'原神', 'Genshin Impact'}
valid_resolutions = {'3840x2160', '3840x1600', '2560x1440', '2560x1080', '1920x1080'}


def check_genshin_info() -> int:
    hwnd = 0
    for title in genshin_titles:
        hwnd = get_window_handle(title)
        if hwnd:
            break

    before = gi.hwnd
    if hwnd == before:
        if hwnd:
            gi.coords = get_no_title_coordinates(hwnd)
        return hwnd

    # state changed
    gi.hwnd = hwnd
    gi.running = bool(hwnd)
    if hwnd:
        logging.warning(f'[OCR]\t原神，启动！{hwnd}')
        gi.coords = get_no_title_coordinates(hwnd)
        resolution = gi.coords[2] - gi.coords[0], gi.coords[3] - gi.coords[1]
        resolution_str = f'{resolution[0]}x{resolution[1]}'
        if resolution_str in valid_resolutions and resolution_str != gi.resolution:
            gi.resolution = resolution_str
            logging.warning(f'[OCR]\t分辨率改变为：{gi.resolution}')
    else:
        logging.warning('[OCR]\t原神，关闭！')
        gi.coords = (0, 0, 0, 0)
    return hwnd


def check_genshin_foreground() -> bool:
    status = get_foreground_window_title() in genshin_titles
    before = gi.foreground
    if status == before:
        return status

    gi.foreground = status
    logging.warning(f'[OCR]\t原神前台状态改变为：{gi.foreground}')
    return status
