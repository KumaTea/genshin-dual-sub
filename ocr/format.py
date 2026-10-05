"""OCR 输出的规范化。

必须和 cpl.format 对原始数据做的处理保持一致，否则查表会差一点点匹配不上。
"""

mapping = {
    '···': '…',
    '【': '「',
    '】': '」',
    ',': '，',
}


def format_ocr_output(text: str) -> str:
    text = text.replace(' ', '')
    for old, new in mapping.items():
        text = text.replace(old, new)
    return text.strip()
