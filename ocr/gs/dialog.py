import logging
import time

from lev.handler import lev_handler
from ocr.format import format_ocr_output
from ocr.gs.screen import take_screenshot
from ocr.ocr import do_ocr
from ocr.configs import lines_centered
from ocr.imgtools import crop
from ocr.session import gi


def get_dialog_text() -> str:
    if not gi.talking:
        return ''

    image = take_screenshot()
    if image is None:
        return ''

    return do_ocr(crop(image, gi.dialog_area()), lines_centered(gi.layout))


def send_dialog_text() -> None:
    text = get_dialog_text()
    if not text:
        return None
    text = format_ocr_output(text)
    logging.info(f'[OCR]\t对话文本：{text}')
    return lev_handler(text)


def debug_dialog_text() -> None:
    started = time.perf_counter()
    text = get_dialog_text()
    elapsed = time.perf_counter() - started
    if text:
        print(f'{elapsed:.3f}s:\t{text}')
