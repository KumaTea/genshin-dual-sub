"""各语言的代词替换表。

游戏文本里 {M#哥哥}{F#姐姐}、{NICKNAME} 之类的占位符要按玩家设置替换掉，
否则会原样显示，还会让相似度匹配失准。
"""

from share.config import settings
from share.langs import get_language


def _nickname() -> str:
    return settings.get('game', 'nickname')


def _is_male() -> bool:
    return settings.bool('game', 'is_male')


def _pronouns_ja() -> dict[str, str]:
    male = _is_male()
    return {
        'NICKNAME': _nickname(),
        'CUTEBIGBROTHER': 'お' + ('兄' if male else '姉') + 'ちゃん',
        'BIGBROTHER': 'お' + ('兄' if male else '姉') + 'さん',
        'BROTHER': ('兄' if male else '姉') + 'さん',
        'SHE': '彼' if male else '彼女',
        'BOY': '男の子' if male else '女の子',
        'KONG': '空' if male else '蛍',
        'YING': 'お兄さん' if male else '蛍',
        'UNCLE': '伯父さん' if male else '叔母さん',
    }


def _pronouns_zh() -> dict[str, str]:
    male = _is_male()
    return {
        'NICKNAME': _nickname(),
        'CUTEBIGBROTHER': '可爱的大' + ('哥哥' if male else '姐姐'),
        'BIGBROTHER': '大' + ('哥哥' if male else '姐姐'),
        'BROTHER': '哥哥' if male else '姐姐',
        'SHE': '他' if male else '她',
        'BOY': '男孩' if male else '女孩',
        'KONG': '空' if male else '荧',
        'YING': '哥哥' if male else '荧',
        'UNCLE': '叔叔' if male else '阿姨',
    }


def _pronouns_en() -> dict[str, str]:
    male = _is_male()
    return {
        'NICKNAME': _nickname(),
        'CUTEBIGBROTHER': 'big ' + ('brother' if male else 'sister'),
        'BIGBROTHER': 'big ' + ('brother' if male else 'sister'),
        'BROTHER': 'brother' if male else 'sister',
        'SHE': 'he' if male else 'she',
        'BOY': 'boy' if male else 'girl',
        'KONG': 'Aether' if male else 'Lumine',
        'YING': 'brother' if male else 'Lumine',
        'UNCLE': 'uncle' if male else 'aunt',
    }


def _pronouns_ko() -> dict[str, str]:
    male = _is_male()
    return {
        'NICKNAME': _nickname(),
        'CUTEBIGBROTHER': '오빠' if male else '언니',
        'BIGBROTHER': '오빠' if male else '언니',
        'BROTHER': '오빠' if male else '언니',
        'SHE': '그' if male else '그녀',
        'BOY': '소년' if male else '소녀',
        'KONG': '공' if male else '형',
        'YING': '오빠' if male else '형',
        'UNCLE': '아저씨' if male else '아주머니',
    }


_TABLES = {
    'ja-jp': _pronouns_ja,
    'zh-cn': _pronouns_zh,
    'zh-tw': _pronouns_zh,
    'en-us': _pronouns_en,
    'ko-kr': _pronouns_ko,
}


def pronouns_for(code: str) -> dict[str, str]:
    """没有专门做表的语言退回英文表，至少不会把占位符原样显示出来。"""
    lang = get_language(code)
    builder = _TABLES.get(lang.code if lang else '', _pronouns_en)
    return builder()


# 源语言（中文）侧的替换表，供 cpl 建索引时使用
def pronouns_source() -> dict[str, str]:
    return _pronouns_zh()


# 兼容旧代码
pronouns_ja = _pronouns_ja()
