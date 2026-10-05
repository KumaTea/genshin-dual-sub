"""注音：官方上标的覆盖范围、假名读音、相邻块合并。"""

import pytest

from fmt.ruby import (
    OFFICIAL,
    READING,
    annotate,
    build_segments,
    combine_segments,
    extract_official_ruby,
    plain_text,
)


def test_extract_official_ruby_removes_tags():
    base, spans = extract_official_ruby('常{RUBY#[D]常世}夜の中')
    assert base == '常夜の中'
    assert len(spans) == 1
    assert spans[0][3] == '常世'


@pytest.mark.parametrize('text,base,covered', [
    # 标签夹在词中间，上标要盖住整个词，而不是只盖标签前的一个字
    ('常{RUBY#[D]常世}夜', '常夜', '常夜'),
    ('雪の{RUBY#[S]スネグーラチカ}娘', '雪の娘', '雪の娘'),
    ('社稷{RUBY#[S]しゃしょくしん}神', '社稷神', '社稷神'),
    ('ナナツ{RUBY#[D]こだまの子}カヤン', 'ナナツカヤン', 'ナナツカヤン'),
    ('安楽{RUBY#[D]アームチェア}椅子', '安楽椅子', '安楽椅子'),
    ('ミン{RUBY#[S]ハッカ}ト', 'ミント', 'ミント'),
])
def test_official_ruby_span(text, base, covered):
    extracted, spans = extract_official_ruby(text)
    assert extracted == base
    start, end, kind, _ = spans[0]
    assert kind == OFFICIAL
    assert base[start:end] == covered


def test_official_ruby_stops_at_particles():
    """向右扩展不能一路吃到后面的助词。"""
    base, spans = extract_official_ruby('雪の{RUBY#[S]スネグーラチカ}娘のプリンセス')
    start, end, _, _ = spans[0]
    assert base[start:end] == '雪の娘'


def test_multiple_official_rubies():
    text = '天{RUBY#[D]てんこん}魂、またの名を胎{RUBY#[D]たいこう}光。'
    base, spans = extract_official_ruby(text)
    assert 'RUBY' not in base
    assert len(spans) == 2
    assert {s[3] for s in spans} == {'てんこん', 'たいこう'}


def test_annotate_keeps_text_intact():
    """无论怎么注音，拼回来的正文必须和原文一致。"""
    for text in (
        'こんにちは、世界。',
        '常{RUBY#[D]常世}夜の中、積み重なった罪が浄化されし後の真の色。',
        '雪の{RUBY#[S]スネグーラチカ}娘の大公による干渉が減った。',
    ):
        base, _ = extract_official_ruby(text)
        assert plain_text(annotate(text)) == base


def test_reading_row_is_produced():
    segments = annotate('私は会社員です。', reading=True, official=False)
    rows = [rows for _, rows in segments if rows]
    assert rows, '汉字应该有假名读音'
    assert all(len(row) == 1 for row in rows), '每段最多一行注音'


def test_official_ruby_replaces_reading():
    """有官方上标的那一段只显示上标，不再叠一行假名读音。

    两行一起显示会超出字幕框高度。
    """
    segments = annotate('常{RUBY#[D]常世}夜', reading=True, official=True)
    annotated = [(text, rows) for text, rows in segments if rows]
    assert annotated == [('常夜', ('常世',))]


def test_every_segment_has_at_most_one_ruby_row():
    text = ('常{RUBY#[D]常世}夜の中、積み重なった罪が浄化されし'
            '後の真の色——白夜の国。')
    for _, rows in annotate(text):
        assert len(rows) <= 1


def test_reading_still_applies_outside_official_spans():
    """官方上标只压住它自己那一段，句子其余部分照常注音。"""
    segments = annotate('常{RUBY#[D]常世}夜の中で会社員が働く。', reading=True, official=True)
    rubies = {text: rows[0] for text, rows in segments if rows}
    assert rubies.get('常夜') == '常世'
    assert any(base != '常夜' for base in rubies), '其他汉字也应该有读音'


def test_official_only_when_reading_disabled():
    segments = annotate('常{RUBY#[D]常世}夜', reading=False, official=True)
    assert [(t, r) for t, r in segments if r] == [('常夜', ('常世',))]


def test_reading_used_when_official_disabled():
    """关掉官方上标时，标签要剥干净并退回假名读音。"""
    segments = annotate('常{RUBY#[D]常世}夜', reading=True, official=False)
    assert plain_text(segments) == '常夜'
    rows = [rows[0] for _, rows in segments if rows]
    assert rows and '常世' not in rows


def test_no_annotation_when_both_disabled():
    segments = annotate('常{RUBY#[D]常世}夜', reading=False, official=False)
    assert segments == [('常夜', ())]


def test_adjacent_kanji_readings_are_merged():
    """相邻的注音块要并成一整块，否则假名会互相重叠。

    超(ちょう) + 最強(さいきょう) -> 超最強(ちょうさいきょう)
    """
    merged = build_segments('超最強のリーダー級戦力', [
        (0, 1, READING, 'ちょう'),
        (1, 3, READING, 'さいきょう'),
        (8, 9, READING, 'きゅう'),
        (9, 11, READING, 'せんりょく'),
    ])
    assert merged == [
        ('超最強', ('ちょうさいきょう',)),
        ('のリーダー', ()),
        ('級戦力', ('きゅうせんりょく',)),
    ]


def test_non_adjacent_readings_are_not_merged():
    merged = build_segments('漢字と熟語', [
        (0, 2, READING, 'かんじ'),
        (3, 5, READING, 'じゅくご'),
    ])
    assert merged == [('漢字', ('かんじ',)), ('と', ()), ('熟語', ('じゅくご',))]


def test_official_and_reading_blocks_are_not_merged():
    """相邻但类型不同的两块不能并——并了假名会跑到上标里去。"""
    merged = build_segments('常夜漢字', [
        (0, 2, OFFICIAL, '常世'),
        (2, 4, READING, 'かんじ'),
    ])
    assert merged == [('常夜', ('常世',)), ('漢字', ('かんじ',))]


def test_real_sentence_merges_runs():
    segments = annotate('超最強のリーダー級戦力', reading=True, official=False)
    annotated = [text for text, rows in segments if rows]
    assert '超最強' in annotated, f'相邻汉字没有合并：{segments}'


def test_combine_segments_merges_plain_runs():
    merged = combine_segments([('abc', ()), ('def', ()), ('漢', ('かん',)), ('ghi', ())])
    assert merged == [('abcdef', ()), ('漢', ('かん',)), ('ghi', ())]


def test_build_segments_drops_empty_spans():
    assert build_segments('あいう', [(0, 0, READING, 'x')]) == [('あいう', ())]
    assert build_segments('あいう', [(0, 2, READING, '')]) == [('あいう', ())]


def test_text_without_ruby_is_untouched():
    assert extract_official_ruby('ただの文章') == ('ただの文章', [])
