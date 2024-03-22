# formatting text


from typing import Optional
from share.assets import ruby_pattern
from cpl.configs import blacklist, pronouns_zh, remove_list
from share.format import replace_pronoun, remove_html_tags, remove_from_list


def has_bl(text: str) -> bool:
    return any(word in text.lower() for word in blacklist)


def extract_ruby(text: str) -> str:
    """
    测{RUBY#[D]示例}试
    """
    ruby_text = ruby_pattern.findall(text)
    if not ruby_text:
        return text
    upper = ''.join(ruby_text)
    lower = ruby_pattern.sub('', text)
    return upper + lower


def format_text(text: str) -> Optional[str]:
    if has_bl(text):
        return None

    text = replace_pronoun(text, pronouns_zh)
    text = remove_html_tags(text)
    text = remove_from_list(text, remove_list)
    text = extract_ruby(text)
    return text.strip()
