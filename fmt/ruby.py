"""注音（ruby）。

产出统一是一串 Segment：

    Segment = (基准文本, (注音,) 或 ())

关于游戏自带的 {RUBY#[D]...} / {RUBY#[S]...}：
标签插在被注释词语的**中间**，覆盖范围横跨标签两侧，数据里并没有给出边界。

    雪の{RUBY#[S]スネグーラチカ}娘   -> スネグーラチカ 注在「雪の娘」上
    社稷{RUBY#[S]しゃしょくしん}神   -> 注在「社稷神」上
    ナナツ{RUBY#[D]こだまの子}カヤン -> 注在「ナナツカヤン」上

所以上标不能只挂在标签前的那一个字上（第一例会挂到「の」上），而要从标签处
向两边扩展，吃掉连续的汉字/片假名等"词内字符"；中间夹着的平假名只有在两侧
都是词内字符时才吸收（这样「雪の娘」能连上，但不会一路吃到后面的助词）。

同一段上官方上标和假名读音只留一个：官方上标优先，假名读音丢掉。
两个一起显示会顶到字幕框外面去。

相邻的注音段会合并成一整块，例如

    超(ちょう) 最強(さいきょう)  ->  超最強(ちょうさいきょう)

不合并的话，每段假名各自居中在很窄的汉字上方，字数一多就会互相压到一起。
"""

from typing import Optional

from Levenshtein import opcodes

from fmt.session import kks
from share.assets import ruby_pattern

Segment = tuple[str, tuple[str, ...]]
# (起始, 结束, 种类, 注音文本)
Span = tuple[int, int, int, str]

READING = 0   # kakasi 推出来的假名读音
OFFICIAL = 1  # 游戏数据里自带的上标，优先级更高

# 向两侧扩展时最多吃掉多少个字
MAX_SPAN = 12

HIRAGANA = range(0x3041, 0x309F)


def _is_hiragana(char: str) -> bool:
    return ord(char) in HIRAGANA


def _is_word_char(char: str) -> bool:
    """能构成词干的字符：汉字、片假名、拉丁字母、数字。"""
    if char.isalnum() and not _is_hiragana(char):
        return True
    return char in '々〆ヶ・ー'


# ---------------------------------------------------------------- 官方上标

def _expand_left(text: str, index: int) -> int:
    """从 index（不含）向左吃掉词内字符，返回起始下标。"""
    start = index
    while start > 0 and index - start < MAX_SPAN:
        char = text[start - 1]
        if _is_word_char(char):
            start -= 1
        elif _is_hiragana(char) and start - 1 > 0 and _is_word_char(text[start - 2]):
            # 夹在词中间的平假名（「雪の娘」的「の」）
            start -= 1
        else:
            break
    return start


def _expand_right(text: str, index: int) -> int:
    """从 index（含）向右吃掉词内字符，返回结束下标。"""
    end = index
    while end < len(text) and end - index < MAX_SPAN:
        if _is_word_char(text[end]):
            end += 1
        else:
            break
    return end


def extract_official_ruby(text: str) -> tuple[str, list[Span]]:
    """剥掉 {RUBY#[..]xxx} 标签，返回纯文本和上标覆盖范围。"""
    if 'RUBY' not in text:
        return text, []

    base = ''
    anchors: list[tuple[int, str]] = []
    cursor = 0
    for match in ruby_pattern.finditer(text):
        content = match.group(1)
        if not content:
            continue
        base += text[cursor:match.start()]
        anchors.append((len(base), content))  # 标签在纯文本里的位置
        cursor = match.end()
    base += text[cursor:]

    # 标签全部剥掉之后再扩展，否则会把还没剥的标签算进词里
    spans: list[Span] = []
    for anchor, content in anchors:
        start = _expand_left(base, anchor)
        end = _expand_right(base, anchor)
        if start == end:  # 两侧都不是词内字符，退而求其次盖住前一个字
            start, end = max(0, anchor - 1), anchor
        spans.append((start, end, OFFICIAL, content))
    return base, spans


# ---------------------------------------------------------------- 假名读音

def _reading_spans(original: str, hira: str, offset: int) -> list[Span]:
    """对齐原文和假名，找出需要注音的部分。

    kakasi 给的是整段的假名，用编辑距离对齐后，被"替换"掉的部分就是汉字。
    """
    spans: list[Span] = []
    pending = ''
    for op, orig_start, orig_end, hira_start, hira_end in opcodes(original, hira):
        if op == 'insert':
            pending += hira[hira_start:hira_end]
        elif op == 'replace':
            pending += hira[hira_start:hira_end]
            spans.append((offset + orig_start, offset + orig_end, READING, pending))
            pending = ''
    return spans


def get_reading_spans(text: str) -> list[Span]:
    spans: list[Span] = []
    offset = 0
    for item in kks.convert(text):
        original = item['orig']
        if original in (item['hira'], item['kana']):
            offset += len(original)
            continue
        spans.extend(_reading_spans(original, item['hira'], offset))
        offset += len(original)
    return spans


# ---------------------------------------------------------------- 合并

def _cluster(spans: list[Span]) -> list[Span]:
    """把有重叠的注音范围并成一条。

    读音和官方上标经常只是部分重叠（上标盖「雪の娘」，读音只盖「娘」），
    不并的话没法把注音居中对齐到正文上。
    并出来的这一条只保留一种注音：有官方上标就用官方的，否则拼接读音。
    """
    if not spans:
        return []

    ordered = sorted(spans)
    merged: list[Span] = []
    start, end, members = ordered[0][0], ordered[0][1], [ordered[0]]
    for span in ordered[1:]:
        if span[0] < end:
            end = max(end, span[1])
            members.append(span)
        else:
            merged.append(_reduce(start, end, members))
            start, end, members = span[0], span[1], [span]
    merged.append(_reduce(start, end, members))
    return merged


def _reduce(start: int, end: int, members: list[Span]) -> Span:
    official = [m[3] for m in members if m[2] == OFFICIAL]
    if official:
        return start, end, OFFICIAL, ''.join(official)
    return start, end, READING, ''.join(m[3] for m in members)


def _merge_adjacent(spans: list[Span]) -> list[Span]:
    """把紧挨着的、同类型的注音块并成一大块。

    超(ちょう)最強(さいきょう) -> 超最強(ちょうさいきょう)
    每块假名是居中画在自己那几个汉字上方的，块太窄假名太长就会和邻块重叠。
    """
    if not spans:
        return []

    merged = [spans[0]]
    for start, end, kind, text in spans[1:]:
        last_start, last_end, last_kind, last_text = merged[-1]
        if last_end == start and last_kind == kind:
            merged[-1] = (last_start, end, kind, last_text + text)
        else:
            merged.append((start, end, kind, text))
    return merged


def build_segments(base: str, spans: list[Span]) -> list[Segment]:
    spans = [s for s in spans if s[1] > s[0] and s[3]]
    segments: list[Segment] = []
    cursor = 0

    for start, end, _, text in _merge_adjacent(_cluster(spans)):
        if start > cursor:
            segments.append((base[cursor:start], ()))
        segments.append((base[start:end], (text,)))
        cursor = end

    if cursor < len(base):
        segments.append((base[cursor:], ()))
    return [s for s in segments if s[0]]


def combine_segments(segments: list[Segment]) -> list[Segment]:
    """把相邻的、都没有注音的段并起来，减少渲染时的 blit 次数。"""
    combined: list[Segment] = []
    for text, rows in segments:
        if combined and not rows and not combined[-1][1]:
            combined[-1] = (combined[-1][0] + text, ())
        else:
            combined.append((text, rows))
    return combined


def annotate(text: str, reading: bool = True, official: bool = True) -> list[Segment]:
    """入口：把一行原文变成带注音的 Segment 列表。"""
    base, official_spans = extract_official_ruby(text)
    spans: list[Span] = list(official_spans) if official else []
    if reading:
        spans.extend(get_reading_spans(base))
    return combine_segments(build_segments(base, spans))


# ---------------------------------------------------------------- 兼容旧接口

def get_ruby_pair(text: str) -> list[Segment]:
    return annotate(text, reading=True, official=False)


def magic_ruby_to_pair(text: str) -> list[Segment]:
    return annotate(text, reading=False, official=True)


def combine_rubies(segments: list[Segment]) -> list[Segment]:
    return combine_segments(segments)


def plain_text(segments: list[Segment]) -> str:
    return ''.join(text for text, _ in segments)


def first_row(segments: list[Segment]) -> Optional[str]:
    for _, rows in segments:
        if rows:
            return rows[0]
    return None
