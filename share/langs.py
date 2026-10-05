"""语言注册表。

原先目标语言写死在两处：`cpl/process.py` 里的 TextMapJP 文件名，
和 `ovl/configs.py` 里拼出来的字体路径。想换语言得改代码。
这里集中成一张表，config.ini 里填语言代码即可。
"""

from typing import NamedTuple, Optional


class Language(NamedTuple):
    code: str        # config.ini 里写的代码，同时也是游戏字体文件名
    text_map: str    # TextMap 文件名中间那段，如 JP -> TextMapJP.json
    name: str


LANGUAGES: tuple[Language, ...] = (
    Language('zh-cn', 'CHS', '简体中文'),
    Language('zh-tw', 'CHT', '繁體中文'),
    Language('en-us', 'EN', 'English'),
    Language('ja-jp', 'JP', '日本語'),
    Language('ko-kr', 'KR', '한국어'),
    Language('de-de', 'DE', 'Deutsch'),
    Language('es-es', 'ES', 'Español'),
    Language('fr-fr', 'FR', 'Français'),
    Language('id-id', 'ID', 'Indonesia'),
    Language('it-it', 'IT', 'Italiano'),
    Language('pt-pt', 'PT', 'Português'),
    Language('ru-ru', 'RU', 'Русский'),
    Language('th-th', 'TH', 'ไทย'),
    Language('tr-tr', 'TR', 'Türkçe'),
    Language('vi-vn', 'VI', 'Tiếng Việt'),
)

_BY_CODE = {lang.code: lang for lang in LANGUAGES}
# 允许写简写：ja / jp 都指向 ja-jp
_ALIASES = {
    'ja': 'ja-jp', 'jp': 'ja-jp',
    'zh': 'zh-cn', 'chs': 'zh-cn', 'cht': 'zh-tw',
    'en': 'en-us', 'ko': 'ko-kr', 'kr': 'ko-kr',
    'de': 'de-de', 'es': 'es-es', 'fr': 'fr-fr', 'ru': 'ru-ru',
}

SOURCE_LANG = _BY_CODE['zh-cn']


def get_language(code: str) -> Optional[Language]:
    key = (code or '').strip().lower()
    key = _ALIASES.get(key, key)
    return _BY_CODE.get(key)


def text_map_files(lang: Language) -> tuple[str, str]:
    """(基础表, 增补表)。增补表 TextMap_Medium* 里是量最大的对话文本。"""
    return f'TextMap{lang.text_map}.json', f'TextMap_Medium{lang.text_map}.json'
