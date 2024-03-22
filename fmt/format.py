# formatting text


from fmt.ja import pronouns_ja
from cpl.configs import remove_list
from fmt.ruby import get_ruby_pair, magic_ruby_to_pair, combine_rubies
from share.format import replace_pronoun, remove_html_tags, remove_from_list


def format_text(text: str) -> list[list[str, str]]:
    text = replace_pronoun(text, pronouns_ja)
    text = remove_html_tags(text)
    text = remove_from_list(text, remove_list)

    if 'RUBY' in text:
        ruby_pair = magic_ruby_to_pair(text)
    else:
        ruby_pair = get_ruby_pair(text)
    return combine_rubies(ruby_pair)
