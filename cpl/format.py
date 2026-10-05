"""源语言（中文）文本的规范化。

索引是"规范化后的中文 -> 文本 ID"，OCR 结果也走同一套规范化，
两边格式必须完全一致，否则相似度匹配会莫名其妙地差一截。
"""

from typing import Optional

from cpl.configs import blacklist, get_pronouns_zh, remove_list
from share.assets import ruby_pattern
from share.format import remove_from_list, remove_html_tags, replace_pronoun

_pronouns: Optional[dict[str, str]] = None


def has_bl(text: str) -> bool:
    return any(word in text.lower() for word in blacklist)


def extract_ruby(text: str) -> str:
    """把 {RUBY#[D]示例} 里的内容提到句首。

    中文侧的上标在游戏里是显示出来的，OCR 也会读到，
    所以索引里必须保留，位置对齐到 OCR 的阅读顺序。
    """
    ruby_text = ruby_pattern.findall(text)
    if not ruby_text:
        return text
    return ''.join(ruby_text) + ruby_pattern.sub('', text)


def format_text(text: str) -> Optional[str]:
    global _pronouns
    if has_bl(text):
        return None

    if _pronouns is None:
        _pronouns = get_pronouns_zh()

    text = replace_pronoun(text, _pronouns)
    text = remove_html_tags(text)
    text = remove_from_list(text, remove_list)
    text = extract_ruby(text)
    return text.strip()
