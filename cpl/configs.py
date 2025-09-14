from share.session import config


nickname = config['game']['nickname']
wanderer = config['game']['wanderer']
little_one = config['game']['little_one']

blacklist = [
    'test',
    'param',
    'HIDDEN'.lower(),
    'UNRELEASED'.lower(),
    'SPRITE_PRESET'.lower(),
    '$['
]

remove_list = ['{%d}' % i for i in range(10)]
remove_list.append('\\n')  # yes

# https://github.com/mrzjy/GenshinDialog
# starts with '#'

is_male = int(config['game']['is_male'])

pronouns_zh = {
    'NICKNAME': nickname,
    'CUTEBIGBROTHER': '可爱的大' + ('哥哥' if is_male else '姐姐'),
    'BIGBROTHER': '大' + ('哥哥' if is_male else '姐姐'),
    'BROTHER': '哥哥' if is_male else '姐姐',
    'SHE': '他' if is_male else '她',
    'BOY': '男孩' if is_male else '女孩',
    'KONG': '空' if is_male else '荧',
    'YING': '哥哥' if is_male else '荧',
    'UNCLE': '叔叔' if is_male else '阿姨',

    # {REALNAME[ID(1)|DELAYHANDLE(true)]}
    # {REALNAME[ID(1)|HOSTONLY(true)]}
    # {REALNAME[ID(1)]}
    'REALNAME[ID(1)': wanderer,

    # {REALNAME[ID(2)|SHOWHOST(true)]}
    'REALNAME[ID(2)': little_one,
}
