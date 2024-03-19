mapping = {
    '···': '…',
    '【': '「',
    '】': '」',
}


def format_ocr_output(text: str) -> str:
    text = text.replace(' ', '')
    for k, v in mapping.items():
        text = text.replace(k, v)
    return text.strip()
