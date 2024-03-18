import json
from tqdm import tqdm
from share.session import config


data_path = config['general']['data_path']
output_path = f'{data_path}/output'
map_file = f'{output_path}/ReversedMap.json'


class LevInfo:
    def __init__(self):
        self.map: dict[str, int] = {}
        self.len_map: dict[int, dict[str, int]] = {}
        self.last_query: str = ''
        self.last_result: str = '0'

        self.load()

    def load(self):
        with open(map_file, 'r', encoding='utf-8') as f:
            self.map = json.load(f)
        pbar = tqdm(self.map)
        pbar.set_description('Building ReversedMap...')
        for key in pbar:
            len_key = len(key) if len(key) < 100 else 100
            if len_key not in self.len_map:
                self.len_map[len_key] = {}
            self.len_map[len_key][key] = self.map[key]


lev = LevInfo()
