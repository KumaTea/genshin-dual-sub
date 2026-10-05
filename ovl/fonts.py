"""字体查找。

原先字体路径是 `游戏目录 + 一长串写死的子路径 + 语言.ttf` 直接拼出来的，
路径填错或者游戏没装在这里，启动就崩在 pygame.font.Font 上，
报错信息还完全看不出是字体的问题。这里逐级回退，并把找到的字体打进日志。
"""

import logging
import os
from typing import Optional

import pygame

from share.config import settings

# 游戏自带字体在安装目录下的相对位置
GAME_FONT_SUBPATH = os.path.join(
    'StreamingAssets', 'MiHoYoSDKRes', 'HttpServerResources', 'font')

# 常见安装位置，游戏目录没配置时挨个试
COMMON_GAME_PATHS = (
    r'C:\Program Files\Genshin Impact\Genshin Impact Game\YuanShen_Data',
    r'C:\Program Files\Genshin Impact\Genshin Impact Game\GenshinImpact_Data',
    r'D:\Genshin Impact\Genshin Impact Game\YuanShen_Data',
    r'D:\Games\Genshin Impact\Genshin Impact Game\YuanShen_Data',
)

# 找不到游戏字体时用系统字体，按语言给出候选
SYSTEM_FONTS = (
    'Microsoft YaHei UI', 'Microsoft YaHei', 'Meiryo', 'Yu Gothic',
    'MS Gothic', 'Malgun Gothic', 'Segoe UI', 'Arial',
)


def game_data_path() -> Optional[str]:
    configured = settings.get('game', 'data_path').strip()
    if configured and os.path.isdir(configured):
        return configured
    for candidate in COMMON_GAME_PATHS:
        if os.path.isdir(candidate):
            return candidate
    return None


def game_font_path(lang_code: str) -> Optional[str]:
    data_path = game_data_path()
    if not data_path:
        return None
    path = os.path.join(data_path, GAME_FONT_SUBPATH, f'{lang_code}.ttf')
    return path if os.path.isfile(path) else None


def resolve_font_path() -> Optional[str]:
    """按 配置 -> 游戏自带 -> 系统字体 的顺序找一个能用的字体。"""
    configured = settings.get('overlay', 'font_path').strip()
    if configured:
        if os.path.isfile(configured):
            return configured
        logging.warning(f'[OVL]\t配置的字体不存在：{configured}')

    lang_code = settings.get('general', 'dst_lang').strip().lower()
    path = game_font_path(lang_code)
    if path:
        logging.info(f'[OVL]\t使用游戏自带字体：{path}')
        return path

    logging.warning('[OVL]\t未找到游戏自带字体，改用系统字体（注音显示可能略有差异）')
    return None


def get_font(path: Optional[str], size: int) -> pygame.font.Font:
    pygame.font.init()
    if path:
        try:
            return pygame.font.Font(path, size)
        except (OSError, pygame.error) as e:
            logging.warning(f'[OVL]\t无法加载字体 {path}：{e}')

    for name in SYSTEM_FONTS:
        found = pygame.font.match_font(name)
        if found:
            return pygame.font.Font(found, size)
    return pygame.font.Font(None, size)
