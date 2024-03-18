from ovl.session import overlay


def ovl_handler(ruby_text: list[list[str, str]]):
    overlay.text = ruby_text
    overlay.need_update = True
