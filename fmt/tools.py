import json
from typing import Union


def load_slim_map(reversed_map: Union[str, dict], original_map: Union[str, dict]) -> dict:
    """只保留索引里出现过的条目。

    原始 TextMap 有 80 万条，其中绝大部分是道具名、系统提示之类，
    不会作为对话出现。按索引筛一遍能少存不少东西。
    """
    if isinstance(reversed_map, str):
        with open(reversed_map, 'r', encoding='utf-8') as f:
            reversed_map = json.load(f)
    if isinstance(original_map, str):
        with open(original_map, 'r', encoding='utf-8') as f:
            original_map = json.load(f)

    slim = {}
    for key in reversed_map.values():
        value = original_map.get(key)
        # 两份 TextMap 的 key 不保证完全一致，比如 4.5 版本的 3596235320
        if value:
            slim[key] = value
    return slim
