import logging

from fmt import session
from fmt.format import format_text
from ovl.handler import ovl_handler


def fmt_handler(key: str) -> None:
    original = session.target_map.get(key)
    if not original:
        # 两份 TextMap 的 key 不保证完全一致，缺条目是正常的
        logging.debug(f'[FMT]\t目标语言中没有 {key}')
        return

    ovl_handler(format_text(original))
