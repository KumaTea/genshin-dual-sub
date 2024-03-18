import json
import pykakasi
from share.session import config


kks = pykakasi.kakasi()

data_path = config['general']['data_path']
output_path = f'{data_path}/output'
ja_map_file = f'{data_path}/TextMapJP.json'

with open(ja_map_file, 'r', encoding='utf-8') as f:
    ja_map = json.load(f)
