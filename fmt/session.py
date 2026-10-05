"""目标语言文本表 & kakasi 实例。"""

import json
import logging
from typing import Optional

from cpl.process import combined_map_file
from fmt.tools import load_slim_map
from lev.session import lev
from share.config import settings
from share.langs import get_language

_kks = None
target_map: dict[str, str] = {}


class _LazyKakasi:
    """pykakasi 初始化要好几百毫秒，用到再说。"""

    def convert(self, text: str):
        global _kks
        if _kks is None:
            import pykakasi
            _kks = pykakasi.kakasi()
        return _kks.convert(text)


kks = _LazyKakasi()


def load(lang_code: Optional[str] = None) -> dict[str, str]:
    """载入目标语言文本，只保留索引里出现过的 ID。"""
    global target_map
    lang = get_language(lang_code or settings.get('general', 'dst_lang'))
    if lang is None:
        raise ValueError(f'不支持的语言：{lang_code}')

    path = combined_map_file(lang.text_map)
    with open(path, 'r', encoding='utf-8') as f:
        full_map = json.load(f)

    target_map = load_slim_map(lev.map, full_map)
    logging.info(f'[FMT]\t{lang.name}文本载入完成，共 {len(target_map)} 条')
    return target_map


# 兼容旧代码
ja_map = target_map
