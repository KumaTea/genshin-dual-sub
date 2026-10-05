import json
import logging
from typing import Optional

from cpl.process import reversed_map_file

# 长度超过这个值的都归到同一个桶里，避免桶太稀疏
MAX_LENGTH = 100


class LevInfo:
    def __init__(self):
        self.map: dict[str, str] = {}
        # 按文本长度分桶：长度差太多的两句话不可能是同一句
        self.len_map: dict[int, dict[str, str]] = {}
        self.last_query: str = ''
        self.last_result: Optional[str] = None

    def load(self, path: Optional[str] = None) -> None:
        path = path or reversed_map_file()
        with open(path, 'r', encoding='utf-8') as f:
            self.map = json.load(f)

        self.len_map = {}
        for key, value in self.map.items():
            bucket = min(len(key), MAX_LENGTH)
            self.len_map.setdefault(bucket, {})[key] = value
        logging.info(f'[LEV]\t索引载入完成，共 {len(self.map)} 条')

    def reset(self) -> None:
        self.last_query = ''
        self.last_result = None


lev = LevInfo()
