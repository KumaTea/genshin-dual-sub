import os
import json
from tqdm import tqdm
from share.session import config
from cpl.format import format_text


data_path = config['general']['data_path']
output_path = f'{data_path}/output'
text_map_file = f'{data_path}/TextMapCHS.json'

os.makedirs(output_path, exist_ok=True)


def get_reversed_map():
    reversed_map = {}

    with open(text_map_file, 'r', encoding='utf-8') as f:
        text_map = json.load(f)

    for key, value in tqdm(text_map.items()):
        new_key = format_text(value)
        if new_key:
            reversed_map[new_key] = key

    return reversed_map


def process():
    reversed_map = get_reversed_map()

    with open(f'{output_path}/ReversedMap.json', 'w', encoding='utf-8') as f:
        json.dump(reversed_map, f, ensure_ascii=False, indent=2)


def init():
    if os.path.exists(f'{output_path}/ReversedMap.json'):
        return None
    process()
