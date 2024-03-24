import time
import logging
from ocr.session import gi
from ocr.ocr import do_ocr  # , do_ocr_raw
from lev.handler import lev_handler
from ocr.wintools import crop_image
from ocr.configs import dialog_area  # , speaker_area
from ocr.format import format_ocr_output
from ocr.gs.screen import take_screenshot


speaker_color = (255, 195, 0)


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
