"""建立"规范化中文 -> 文本 ID"的反查索引。

首次运行会读两份中文 TextMap，规范化每一条，再写成 ReversedMap.json。
之后 OCR 出来的中文就能直接查到 ID，再用 ID 取目标语言的原文。
"""

import json
import logging
import os
from typing import Optional

from cpl.download import download_missing
from cpl.format import format_text
from share.config import settings
from share.langs import SOURCE_LANG, get_language, text_map_files

try:
    from tqdm import tqdm
    has_tqdm = True
except ImportError:
    has_tqdm = False

# 规范化规则一改，旧索引就对不上了。改规则时把这个数字加一，
# 老用户下次启动会自动重建，而不是拿着不匹配的索引一直匹配不中。
INDEX_VERSION = 2


def data_path() -> str:
    return settings.get('general', 'data_path')


def output_path() -> str:
    return os.path.join(data_path(), 'output')


def reversed_map_file() -> str:
    return os.path.join(output_path(), 'ReversedMap.json')


def combined_map_file(text_map: str) -> str:
    return os.path.join(output_path(), f'CombinedMap{text_map}.json')


def version_file() -> str:
    return os.path.join(output_path(), 'index_version')


def index_is_current() -> bool:
    if not os.path.exists(reversed_map_file()):
        return False
    try:
        with open(version_file(), 'r', encoding='utf-8') as f:
            return int(f.read().strip()) == INDEX_VERSION
    except (OSError, ValueError):
        return False


def mark_index_version() -> None:
    with open(version_file(), 'w', encoding='utf-8') as f:
        f.write(str(INDEX_VERSION))


def _manual_hint(missing: list[str]) -> str:
    base = settings.get('download', 'base_url')
    lines = ['', '  缺少以下文本数据文件：']
    lines += [f'    - {name}' for name in missing]
    lines += [
        '',
        f'  请从 {base} 下载，',
        f'  并放到 {os.path.abspath(data_path())} 目录下。',
        '  或者在 config.ini 里把 [download] allow_download 设为 1，由程序代为下载。',
        '',
    ]
    return '\n'.join(lines)


def ensure_text_maps(languages) -> bool:
    """确认所需的 TextMap 都在。缺了就（在用户同意后）下载。"""
    required: list[str] = []
    for lang in languages:
        required.extend(text_map_files(lang))

    missing = download_missing(required, data_path())
    if missing:
        logging.error(_manual_hint(missing))
        return False
    return True


def combine(text_map: str) -> dict[str, str]:
    """基础表 + 增补表合成一份完整的 id -> 文本。"""
    combined: dict[str, str] = {}
    for filename in text_map_files_by_code(text_map):
        path = os.path.join(data_path(), filename)
        with open(path, 'r', encoding='utf-8') as f:
            combined.update(json.load(f))

    os.makedirs(output_path(), exist_ok=True)
    with open(combined_map_file(text_map), 'w', encoding='utf-8') as f:
        json.dump(combined, f, ensure_ascii=False)
    return combined


def text_map_files_by_code(text_map: str) -> tuple[str, str]:
    return f'TextMap{text_map}.json', f'TextMap_Medium{text_map}.json'


def build_reversed_map(source_map: dict[str, str]) -> dict[str, str]:
    reversed_map: dict[str, str] = {}
    items = source_map.items()
    if has_tqdm:
        items = tqdm(items, total=len(source_map), desc='建立索引', unit='条')
    else:
        logging.info('[CPL]\t正在建立索引（装了 tqdm 会有进度条）…')

    for key, value in items:
        if not isinstance(value, str):
            continue
        normalized = format_text(value)
        if normalized:
            reversed_map[normalized] = key
    return reversed_map


def init(dst_lang: Optional[str] = None) -> bool:
    """准备好运行所需的数据文件，返回是否成功。"""
    lang = get_language(dst_lang or settings.get('general', 'dst_lang'))
    if lang is None:
        logging.error(f'[CPL]\t不支持的语言：{dst_lang or settings.get("general", "dst_lang")}')
        return False

    os.makedirs(output_path(), exist_ok=True)
    need_reversed = not index_is_current()
    need_target = not os.path.exists(combined_map_file(lang.text_map))
    if not need_reversed and not need_target:
        return True
    if need_reversed and os.path.exists(reversed_map_file()):
        logging.info('[CPL]\t规范化规则已更新，正在重建索引…')

    languages = []
    if need_reversed:
        languages.append(SOURCE_LANG)
    if need_target:
        languages.append(lang)
    if not ensure_text_maps(languages):
        return False

    if need_target:
        logging.info(f'[CPL]\t正在合并 {lang.name} 文本…')
        combine(lang.text_map)

    if need_reversed:
        logging.info('[CPL]\t正在合并中文文本…')
        source_map = combine(SOURCE_LANG.text_map)
        reversed_map = build_reversed_map(source_map)
        with open(reversed_map_file(), 'w', encoding='utf-8') as f:
            json.dump(reversed_map, f, ensure_ascii=False)
        mark_index_version()
        logging.info(f'[CPL]\t索引建立完成，共 {len(reversed_map)} 条')

    return True
