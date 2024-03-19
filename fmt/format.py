# formatting text


from fmt.ja import pronouns_ja
from fmt.ruby import get_ruby_pair, magic_ruby_to_pair, combine_rubies
from cpl.format import replace_pronoun, remove_html_tags, remove_others


def format_text(text: str) -> list[list[str, str]]:
    text = replace_pronoun(text, pronouns_ja)
    text = remove_html_tags(text)
    text = remove_others(text)

    if 'RUBY' in text:
        ruby_pair = magic_ruby_to_pair(text)
    else:
        ruby_pair = get_ruby_pair(text)
    return combine_rubies(ruby_pair)
