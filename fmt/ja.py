from share.session import config


nickname = config['game']['nickname']
male = int(config['game']['male'])

pronouns_ja = {
    # unverified
    'NICKNAME': nickname,
    'CUTEBIGBROTHER': 'お' + ('兄' if male else '姉') + 'ちゃん',
    'BIGBROTHER': 'お' + ('兄' if male else '姉') + 'さん',
    'BROTHER': ('兄' if male else '姉') + 'さん',
    'SHE': '彼' if male else '彼女',
    'BOY': '男の子' if male else '女の子',
    'KONG': '空' if male else '蛍',
    'YING': 'お兄さん' if male else '蛍',
    'UNCLE': '伯父さん' if male else '叔母さん',
}
