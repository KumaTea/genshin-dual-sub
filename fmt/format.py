"""把匹配到的目标语言原文，处理成可以直接渲染的 Segment 列表。"""

from cpl.configs import remove_list
from fmt.ja import pronouns_for
from fmt.ruby import Segment, annotate, combine_segments
from share.config import settings
from share.format import remove_from_list, remove_html_tags, replace_pronoun

# 只有日语需要注音
RUBY_LANGS = ('ja-jp', 'ja', 'jp')


def _wants_ruby() -> bool:
    return (
        settings.bool('overlay', 'show_ruby')
        and settings.get('general', 'dst_lang').lower() in RUBY_LANGS
    )


def format_text(text: str) -> list[Segment]:
    text = replace_pronoun(text, pronouns_for(settings.get('general', 'dst_lang')))
    text = remove_html_tags(text)
    text = remove_from_list(text, remove_list)
    text = text.strip()
    if not text:
        return []

    if not _wants_ruby():
        # 非日语时仍然要剥掉 {RUBY#...} 标签，否则会原样显示出来
        return combine_segments(annotate(text, reading=False, official=False))

    return annotate(
        text,
        reading=True,
        official=settings.bool('overlay', 'show_official_ruby'),
    )
