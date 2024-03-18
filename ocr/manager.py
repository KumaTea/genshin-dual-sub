import time
import logging
from ocr.session import gi
from lev.handler import lev_handler
from ovl.handler import ovl_handler
from ocr.ocr import do_ocr, do_ocr_raw
from ocr.screenshot import grab_screenshot
from share.session import scheduler, config
from ocr.configs import speaker_area, dialog_area
from ocr.wintools import get_window_handle, get_no_title_coordinates, crop_image


genshin_titles = {'原神', 'Genshin Impact'}


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

    gi.hwnd = hwnd
    gi.running = bool(hwnd)
    if hwnd:
        logging.warning(f'原神，启动！{hwnd}')
        gi.coords = get_no_title_coordinates(hwnd)
    else:
        logging.warning('原神，关闭！')
        gi.coords = (0, 0, 0, 0)
    return hwnd


def check_talking() -> bool:
    if not gi.running:
        talking = False
        reason = '未运行'
    else:
        image = grab_screenshot(*gi.coords)
        if image is None or not image.any():
            talking = False
            reason = '截图失败'
        else:
            result = do_ocr_raw(crop_image(image, speaker_area[gi.resolution]))
            talking = bool(result)
            reason = 'OCR结果'

    before = gi.talking
    if talking == before:
        return before

    # state changed
    gi.talking = talking
    logging.info(f'对话状态改变为：{gi.talking}\t原因：{reason}')
    if not talking:
        # clear dialog text
        ovl_handler([])
    return gi.talking


def get_dialog_text() -> str:
    if not gi.talking:
        return ''

    image = grab_screenshot(*gi.coords)
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
    return lev_handler(text)


def add_ocr_jobs() -> None:
    # do it now
    check_genshin_info()
    check_talking()
    send_dialog_text()

    # add jobs
    scheduler.add_job(check_genshin_info, 'interval', seconds=int(config['intervals']['genshin_info']))
    scheduler.add_job(check_talking, 'interval', seconds=int(config['intervals']['talking']))
    scheduler.add_job(send_dialog_text, 'interval', seconds=int(config['intervals']['dialog']))
    # scheduler.add_job(debug_dialog_text, 'interval', seconds=2)
