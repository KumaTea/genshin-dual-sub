"""相似度匹配。用一个小索引替换真索引，避免测试依赖 80 万条数据。"""

import pytest

from lev import core
from lev.session import LevInfo


@pytest.fixture
def small_index(monkeypatch):
    index = LevInfo()
    index.map = {
        '我想应该都歇业了': '1001',
        '不好意思都歇业了': '1002',
        '稍等有报错提示': '1003',
        '这是一句完全不一样的很长的台词用来占位': '1004',
    }
    for key, value in index.map.items():
        index.len_map.setdefault(len(key), {})[key] = value

    committed: list[str] = []
    monkeypatch.setattr(core, 'lev', index)
    monkeypatch.setattr(core, 'commit', committed.append)
    return index, committed


def test_exact_match(small_index):
    _, committed = small_index
    core.search('我想应该都歇业了')
    assert committed == ['1001']


def test_ocr_typo_still_matches(small_index):
    """OCR 认错一个字也要能匹配回去。"""
    _, committed = small_index
    core.search('我想应该都歌业了')
    assert committed and committed[-1] == '1001'


def test_different_length_is_searched(small_index):
    """查询比索引里的条目短，也要能在相邻长度桶里找到。"""
    _, committed = small_index
    core.search('稍等有报错提')
    assert committed and committed[-1] == '1003'


def test_missing_length_bucket_does_not_raise(small_index):
    """原来 find_best 直接下标取桶，长度没命中就 KeyError。"""
    index, _ = small_index
    assert 999 not in index.len_map
    distance, result = core.find_best('x' * 999, 999)
    assert result is None


def test_repeated_query_is_ignored(small_index):
    _, committed = small_index
    core.search('我想应该都歇业了')
    core.search('我想应该都歇业了')
    assert committed == ['1001']


def test_near_identical_query_is_skipped(small_index):
    """逐字显字过程中的中间帧不该反复提交。"""
    _, committed = small_index
    core.search('这是一句完全不一样的很长的台词用来占位')
    before = len(committed)
    # 只差一个字，相对距离远小于 10%
    core.search('这是一句完全不一样的很长的台词用来占住')
    assert len(committed) == before


def test_empty_query(small_index):
    _, committed = small_index
    core.search('')
    assert committed == []


def test_search_window_does_not_drift(small_index):
    """原实现在内层 for 里覆盖了 length，搜索窗口会一路往下偏。

    这里用一个只存在于"更长"桶里的条目：窗口偏了就找不到。
    """
    index, committed = small_index
    long_text = '甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉'
    index.map[long_text] = '2001'
    index.len_map.setdefault(len(long_text), {})[long_text] = '2001'

    core.search('甲乙丙丁戊己庚辛壬癸子丑寅')  # 短 7 个字
    assert committed and committed[-1] == '2001'
