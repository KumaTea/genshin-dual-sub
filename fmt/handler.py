from fmt.session import ja_map
from fmt.format import format_text
from ovl.handler import ovl_handler


def fmt_handler(key: str) -> None:
    original_text = ja_map[key]
    ruby_text = format_text(original_text)
    return ovl_handler(ruby_text)
