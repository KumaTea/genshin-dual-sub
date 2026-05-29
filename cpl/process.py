import os
import json
from cpl.format import format_text
from share.session import config, logging


try:
    from tqdm import tqdm
    has_tqdm = True
except ImportError:
    has_tqdm = False


data_path = config['general']['data_path']
output_path = f'{data_path}/output'

os.makedirs(output_path, exist_ok=True)

TEXT_MAPS_CHS = 'https://gitlab.com/Dimbreath/AnimeGameData/-/raw/master/TextMap/TextMapCHS.json?inline=false'
TEXT_MAPS_JP = 'https://gitlab.com/Dimbreath/AnimeGameData/-/raw/master/TextMap/TextMapJP.json?inline=false'
TEXT_MAPS_CHS_EXT = 'https://gitlab.com/Dimbreath/AnimeGameData/-/raw/master/TextMap/TextMap_MediumCHS.json?inline=false'
TEXT_MAPS_JP_EXT = 'https://gitlab.com/Dimbreath/AnimeGameData/-/raw/master/TextMap/TextMap_MediumJP.json?inline=false'

NO_TEXT_MAPS_MSG = (
    f'\n'
    f'TextMap_MediumCHS.json not found.\n'
    f'Please download it from:\n'
    f'  {TEXT_MAPS_CHS}\n'
    f'  {TEXT_MAPS_JP}\n'
    f'  {TEXT_MAPS_CHS_EXT}\n'
    f'  {TEXT_MAPS_JP_EXT}\n'
    f'and place it in {data_path}.\n'
    f'P.S. I cannot download it for you because the author does not specify a license.\n'
    f'Press Enter when you finish that...\n'
    f'\n'
    f'未找到 TextMap_MediumCHS.json。\n'
    f'请从以下地址下载：\n'
    f'  {TEXT_MAPS_CHS}\n'
    f'  {TEXT_MAPS_JP}\n'
    f'  {TEXT_MAPS_CHS_EXT}\n'
    f'  {TEXT_MAPS_JP_EXT}\n'
    f'并放置于 {data_path} 中。\n'
    f'注：我无法为您下载，因为作者尚未指定一个允许这么做的协议。\n'
    f'下载完成后按 Enter...\n'
)
NO_TEXT_MAPS_MSG = '\n'.join(f'  {i}' for i in NO_TEXT_MAPS_MSG.splitlines())


def ensure_text_maps():
    while not os.path.exists(f'{data_path}/TextMap_MediumCHS.json'):
        logging.error(NO_TEXT_MAPS_MSG)
        input('\n')


def combine_chs() -> dict[str, str]:
    combined_map = {}

    with open(f'{data_path}/TextMapCHS.json', 'r', encoding='utf-8') as f:
        combined_map.update(json.load(f))

    with open(f'{data_path}/TextMap_MediumCHS.json', 'r', encoding='utf-8') as f:
        combined_map.update(json.load(f))

    with open(f'{output_path}/CombinedMapCHS.json', 'w', encoding='utf-8') as f:
        json.dump(combined_map, f, ensure_ascii=False, indent=2)

    return combined_map


def combine_jp():  #  -> dict[str, str]:
    combined_map = {}

    with open(f'{data_path}/TextMapJP.json', 'r', encoding='utf-8') as f:
        combined_map.update(json.load(f))

    with open(f'{data_path}/TextMap_MediumJP.json', 'r', encoding='utf-8') as f:
        combined_map.update(json.load(f))

    with open(f'{output_path}/CombinedMapJP.json', 'w', encoding='utf-8') as f:
        json.dump(combined_map, f, ensure_ascii=False, indent=2)

    # return combined_map


def get_reversed_map():
    reversed_map = {}
    text_map = combine_chs()

    if has_tqdm:
        items = text_map.items()
    else:
        items = list(text_map.items())
        logging.warning('tqdm not found, progress bar disabled. Install it via "pip install tqdm" to enable it.')

    for key, value in items:
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
    # combine_chs()
    combine_jp()
    process()
