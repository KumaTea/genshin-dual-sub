import logging

from ocr.gs.screen import take_screenshot
from ocr.layout import detect_layout
from ocr.session import gi
from ovl.handler import clear_subtitle

LAYOUT_NAMES = {'chat': '剧情对话', 'idle': '闲聊', 'type2': '旁白/通讯'}


def check_talking() -> bool:
    """判断当前是否在对话，顺便记下是哪种聊天版式。"""
    if not gi.running:
        layout, reason = None, '游戏未运行'
    elif not gi.foreground:
        layout, reason = None, '游戏不在前台'
    else:
        image = take_screenshot()
        if image is None:
            # 抓不到画面时不改状态，否则字幕会闪
            return gi.talking
        layout = detect_layout(image)
        reason = LAYOUT_NAMES.get(layout, '对话区没有角色名')

    talking = layout is not None
    if talking == gi.talking and layout == gi.layout:
        return talking

    gi.talking, gi.layout = talking, layout
    logging.info(f'[OCR]\t对话状态：{talking}\t原因：{reason}')
    if not talking:
        clear_subtitle()
    return talking
