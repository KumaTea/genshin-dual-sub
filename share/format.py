from share.session import config
from share.assets import replace_pattern, html_tag_pattern, pronoun_choice_pattern


male = int(config['game']['male'])


def choose_pronoun(text: str) -> str:
    """
    :param text: "荣誉骑士{M#哥哥}{F#姐姐}再见，大家再见…"
    :return: "荣誉骑士哥哥再见，大家再见…"
    """
    find_results: list[tuple[str, str]] = pronoun_choice_pattern.findall(text)
    if not find_results:
        return text

    choices = find_results[0]
    raw_text = '{M#%s}{F#%s}' % choices
    pronoun = choices[0] if male else choices[1]
    return text.replace(raw_text, pronoun)


def replace_pronoun(text: str, pronouns: dict[str, str]) -> str:
    if not text.startswith('#'):
        return text
    text = text[1:]

    text = choose_pronoun(text)
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


def remove_from_list(text: str, rm_list: list) -> str:
    for item in rm_list:
        text = text.replace(item, '')
    return text
