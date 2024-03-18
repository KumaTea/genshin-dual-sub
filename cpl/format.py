# formatting text


from typing import Optional
from cpl.configs import blacklist, pronouns_zh, remove_list
from share.assets import replace_pattern, html_tag_pattern, ruby_pattern


def has_bl(text: str) -> bool:
    return any(word in text.lower() for word in blacklist)


def replace_pronoun(text: str, pronouns: dict[str, str]) -> str:
    if not text.startswith('#'):
        return text

    text = text[1:]
    match_items = replace_pattern.findall(text)
    for item in match_items:
        matched = False
        for key in pronouns:
            if key in item:
                text = text.replace(item, pronouns[key])
                matched = True
                break
        if not matched:
            text = text.replace(item, ' ')
    return text


def remove_html_tags(text: str) -> str:
    return html_tag_pattern.sub('', text)


def remove_others(text: str) -> str:
    for item in remove_list:
        text = text.replace(item, '')
    return text


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
    text = remove_others(text)
    text = extract_ruby(text)
    return text.strip()
