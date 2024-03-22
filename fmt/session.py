import pykakasi
from lev.session import lev
from share.session import config
from fmt.tools import load_slim_map

kks = pykakasi.kakasi()

data_path = config['general']['data_path']
output_path = f'{data_path}/output'
ja_map_file = f'{data_path}/TextMapJP.json'

# with open(ja_map_file, 'r', encoding='utf-8') as f:
#     ja_map = json.load(f)

ja_map = load_slim_map(lev.map, ja_map_file)
# this doesn't decrease memory usage
# necessity of it needs further investigation
