"""用编辑距离把 OCR 结果匹配回原文。

OCR 多少会认错字，所以不能只做精确查表。索引按文本长度分桶，
从和 query 等长的桶开始找，再向两侧扩散；一旦"长度差"本身已经
超过当前最优距离，就没必要再往外找了（长度差是编辑距离的下界）。
"""

import logging
import time
from typing import Optional

import Levenshtein

from fmt.handler import fmt_handler
from lev.session import MAX_LENGTH, lev

# 距离低于长度的这个比例就算匹配上了
GOOD_ENOUGH_RATIO = 0.2
# 和上一句太像就不重复提交（原神逐字显字，中间帧会反复触发）
TOO_SIMILAR_RATIO = 0.1


def commit(result: Optional[str]) -> None:
    if result:
        fmt_handler(result)


def find_best(query: str, length: int) -> tuple[int, Optional[str]]:
    """在指定长度桶里找最接近的一条。"""
    bucket = lev.len_map.get(min(length, MAX_LENGTH))
    if not bucket:
        return len(query), None

    best_distance = len(query)
    best_result = None
    for key, value in bucket.items():
        distance = Levenshtein.distance(query, key)
        if distance < best_distance:
            best_distance, best_result = distance, value
            if distance == 0:
                break
    return best_distance, best_result


def search(query: str) -> None:
    if not query or query == lev.last_query:
        return

    if lev.last_query:
        distance = Levenshtein.distance(query, lev.last_query)
        # 原写法是 len(query) / d < 0.1，d 最大就等于 len(query)，
        # 这个条件永远不成立，去重实际上从来没生效过
        if distance / len(query) < TOO_SIMILAR_RATIO:
            logging.debug(f'[LEV]\t与上一句过于接近，跳过：{query=} {distance=}')
            lev.last_query = query
            return

    lev.last_query = query

    if query in lev.map:
        result = lev.map[query]
        lev.last_result = result
        commit(result)
        return

    length = len(query)
    best_distance, best_result = find_best(query, length)
    if best_result and best_distance < length * GOOD_ENOUGH_RATIO:
        # 够好就先显示出来，后面找到更好的再更新
        lev.last_result = best_result
        commit(best_result)

    # 向两侧扩散。注意这里不能复用 length 做循环变量——
    # 原代码在内层 for 里覆盖了 length，导致每轮的搜索窗口越走越偏
    offset = 1
    while offset < length:
        for candidate_length in (length + offset, length - offset):
            if candidate_length <= 0 or candidate_length > MAX_LENGTH:
                continue
            distance, result = find_best(query, candidate_length)
            if result and distance < best_distance:
                best_distance, best_result = distance, result

        offset += 1
        if offset >= best_distance:
            # 再往外找，长度差本身就已经大于当前最优距离了
            break

    if best_result and lev.last_result != best_result:
        lev.last_result = best_result
        commit(best_result)


def debug_search(query: str) -> None:
    started = time.perf_counter()
    search(query)
    print(f'{time.perf_counter() - started:.3f}s')
