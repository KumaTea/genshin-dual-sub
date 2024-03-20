import time
import logging
import numpy as np
from ocr.session import gi
from ocr.ocr import do_ocr  # , do_ocr_raw
from typing import Optional
from ocr.imgtools import has_color
from lev.handler import lev_handler
from ovl.handler import ovl_handler
from ocr.format import format_ocr_output
from ocr.screenshot import grab_screenshot
from share.session import scheduler, config
from ocr.configs import dialog_area  # , speaker_area
from ocr.wintools import get_window_handle, get_no_title_coordinates, crop_image, get_foreground_window_title


genshin_titles = {'原神', 'Genshin Impact'}
valid_resolutions = {'2560x1440', '2560x1080', '1920x1080'}
speaker_color = (255, 195, 0)


def take_screenshot() -> Optional[np.ndarray]:
    # make a screenshot handler
    # to avoid taking screenshots too frequently

    # now = time.time()
    if time.time() - gi.last_shot < 1:
        return gi.screenshot

    image = grab_screenshot(*gi.coords)
    if image is None or not image.any():
        return gi.screenshot

    gi.screenshot = image
    gi.last_shot = time.time()
    return image


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


def check_talking() -> bool:
    if not gi.running:
        talking = False
        reason = '未运行'
    elif not gi.foreground:
        talking = False
        reason = '不在前台'
    else:
        # image = grab_screenshot(*gi.coords)
        image = take_screenshot()
        if image is None or not image.any():
            # talking = False
            # reason = '截图失败'
            # don't change state
            # logging.warning(f'[OCR]\t截图失败: {image=}')
            return gi.talking
        else:
            # result = do_ocr_raw(crop_image(image, speaker_area[gi.resolution]))
            # talking = bool(result)

            # not using OCR
            # checking if the color of the speaker name exists
            # reducing 99% of time
            talking = has_color(image, color=speaker_color)
            reason = '检测对话区角色名称'

    before = gi.talking
    if talking == before:
        return before

    # state changed
    gi.talking = talking
    logging.warning(f'[OCR]\t对话状态改变为：{gi.talking}\t原因：{reason}')
    if not talking:
        # clear dialog text
        ovl_handler([])
    return gi.talking


def get_dialog_text() -> str:
    if not gi.talking:
        return ''

    # image = grab_screenshot(*gi.coords)
    image = take_screenshot()
    if image is None or not image.any():
        return ''
    return do_ocr(crop_image(image, dialog_area[gi.resolution]))


def debug_dialog_text() -> None:
    t0 = time.perf_counter()
    text = get_dialog_text()
    t = time.perf_counter() - t0
    if text:
        print(f'{t:.3f}s:\t{text}')


def send_dialog_text() -> None:
    text = get_dialog_text()
    if not text:
        return None
    text = format_ocr_output(text)
    logging.warning(f'[OCR]\t对话文本：{text}')
    return lev_handler(text)


def add_ocr_jobs() -> None:
    # do it now
    check_genshin_info()
    check_genshin_foreground()
    check_talking()
    send_dialog_text()

    # add jobs
    scheduler.add_job(check_genshin_info, 'interval', seconds=int(config['intervals']['genshin_info']))
    scheduler.add_job(check_genshin_foreground, 'interval', seconds=int(config['intervals']['genshin_fg']))
    scheduler.add_job(check_talking, 'interval', seconds=int(config['intervals']['talking']))
    scheduler.add_job(send_dialog_text, 'interval', seconds=int(config['intervals']['dialog']))
    # scheduler.add_job(debug_dialog_text, 'interval', seconds=2)
