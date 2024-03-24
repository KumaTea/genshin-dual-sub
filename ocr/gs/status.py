import logging
from ocr.session import gi
from ocr.imgtools import has_color
from ovl.handler import ovl_handler
from ocr.gs.screen import take_screenshot


speaker_color = (255, 195, 0)


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
