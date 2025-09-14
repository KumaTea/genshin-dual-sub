import os
import json
from tqdm import tqdm
from cpl.format import format_text
from share.session import config, logging


data_path = config['general']['data_path']
output_path = f'{data_path}/output'
text_map_file = f'{data_path}/TextMapCHS.json'

os.makedirs(output_path, exist_ok=True)

TEXT_MAPS_CHS = 'https://gitlab.com/Dimbreath/AnimeGameData/-/raw/master/TextMap/TextMapCHS.json?inline=false'
TEXT_MAPS_JP = 'https://gitlab.com/Dimbreath/AnimeGameData/-/raw/master/TextMap/TextMapJP.json?inline=false'
NO_TEXT_MAPS_MSG = (
    f'\n'
    f'TextMapCHS.json not found.\n'
    f'Please download it from:\n'
    f'  {TEXT_MAPS_CHS}\n'
    f'  {TEXT_MAPS_JP}\n'
    f'and place it in {data_path}.\n'
    f'P.S. I cannot download it for you because the author does not specify a license.\n'
    f'Press Enter when you finish that...\n'
    f'\n'
    f'未找到 TextMapCHS.json。\n'
    f'请从以下地址下载：\n'
    f'  {TEXT_MAPS_CHS}\n'
    f'  {TEXT_MAPS_JP}\n'
    f'并放置于 {data_path} 中。\n'
    f'注：我无法为您下载，因为作者尚未指定一个允许这么做的协议。\n'
    f'下载完成后按 Enter...\n'
)
NO_TEXT_MAPS_MSG = '\n'.join(f'  {i}' for i in NO_TEXT_MAPS_MSG.splitlines())


def ensure_text_maps():
    while not os.path.exists(text_map_file):
        logging.error(NO_TEXT_MAPS_MSG)
        input('\n')


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

    ensure_text_maps()
    process()
