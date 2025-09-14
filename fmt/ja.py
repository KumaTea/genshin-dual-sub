from share.session import config


nickname = config['game']['nickname']
is_male = int(config['game']['is_male'])

pronouns_ja = {
    # unverified
    'NICKNAME': nickname,
    'CUTEBIGBROTHER': 'お' + ('兄' if is_male else '姉') + 'ちゃん',
    'BIGBROTHER': 'お' + ('兄' if is_male else '姉') + 'さん',
    'BROTHER': ('兄' if is_male else '姉') + 'さん',
    'SHE': '彼' if is_male else '彼女',
    'BOY': '男の子' if is_male else '女の子',
    'KONG': '空' if is_male else '蛍',
    'YING': 'お兄さん' if is_male else '蛍',
    'UNCLE': '伯父さん' if is_male else '叔母さん',
}
