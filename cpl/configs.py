from share.session import config


nickname = config['game']['nickname']

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

"""
Frequency	Variable
84388	{NICKNAME}
2746	{MATEAVATARSEXPRO[INFO_MALE_PRONOUN_BROTHER|INFO_FEMALE_PRONOUN_SISTER]}
1273	{PLAYERAVATARSEXPRO[INFO_MALE_PRONOUN_BROTHER|INFO_FEMALE_PRONOUN_SISTERA]}
1051	{PLAYERAVATARSEXPRO[INFO_MALE_PRONOUN_HE|INFO_FEMALE_PRONOUN_SHE]}
944	{PLAYERAVATARSEXPRO[INFO_MALE_PRONOUN_SISTER|INFO_FEMALE_PRONOUN_BROTHER]}
896	{PLAYERAVATARSEXPRO[INFO_FEMALE_PRONOUN_SHE|INFO_MALE_PRONOUN_HE]}
490	{PLAYERAVATARSEXPRO[INFO_MALE_PRONOUN_BOYC|INFO_FEMALE_PRONOUN_GIRLC]}
468	{PLAYERAVATARSEXPRO[INFO_MALE_PRONOUN_SHE|INFO_FEMALE_PRONOUN_HE]}
441	{PLAYERAVATARSEXPRO[INFO_MALE_PRONOUN_YING|INFO_FEMALE_PRONOUN_BROTHER]}
436	{PLAYERAVATARSEXPRO[INFO_FEMALE_PRONOUN_SISTER|INFO_MALE_PRONOUN_BROTHER]}
408	{PLAYERAVATARSEXPRO[INFO_MALE_PRONOUN_BIGBROTHER|INFO_FEMALE_PRONOUN_BIGSISTER]}
336	{PLAYERAVATARSEXPRO[INFO_MALE_PRONOUN_GIRLD|INFO_FEMALE_PRONOUN_BOYD]}
302	{PLAYERAVATARSEXPRO[INFO_MALE_PRONOUN_BOY|INFO_FEMALE_PRONOUN_GIRL]}
211	{MATEAVATARSEXPRO[INFO_MALE_PRONOUN_HE|INFO_FEMALE_PRONOUN_SHE]}
192	{PLAYERAVATARSEXPRO[INFO_MALE_PRONOUN_BROTHER|INFO_FEMALE_PRONOUN_YING]}
192	{PLAYERAVATARSEXPRO[INFO_MALE_PRONOUN_UNCLE|INFO_FEMALE_PRONOUN_AUNT]}
144	{MATEAVATARSEXPRO[INFO_MALE_PRONOUN_BOY|INFO_FEMALE_PRONOUN_GIRL]}
80	{PLAYERAVATARSEXPRO[INFO_MALE_PRONOUN_YING|INFO_FEMALE_PRONOUN_KONG]}
64	{RUBY[D]Otets}
36	{PLAYERAVATARSEXPRO[INFO_MALE_PRONOUN_HERO|INFO_FEMALE_PRONOUN_HEROINE]}
34	{PLAYERAVATARSEXPRO[INFO_MALE_PRONOUN_SHE|INFO_MALE_PRONOUN_HE]}
33	{MATEAVATARSEXPRO[INFO_MALE_PRONOUN_BOYD|INFO_FEMALE_PRONOUN_GIRLD]}
31	{PLAYERAVATARSEXPRO[INFO_MALE_PRONOUN_HE|INFO_MALE_PRONOUN_SHE]}
16	{PLAYERAVATARSEXPRO[INFO_MALE_PRONOUN_BROANDSIS|INFO_FEMALE_PRONOUN_SISANDSIS]}
16	{PLAYERAVATARSEXPRO[INFO_MALE_PRONOUN_BROTHER|INFO_FEMALE_PRONOUN_SISTER]}
15	{QuestNpcID}
14	{PLAYERAVATARSEXPRO[INFO_MALE_PRONOUN_CUTEBIGBROTHER|INFO_FEMALE_PRONOUN_CUTEBIGSISTER]}
11	{PLAYERAVATARSEXPRO[INFO_MALE_PRONOUN_BROTHER|INFO_MALE_PRONOUN_BROANDSIS]}
8	{PLAYERAVATARSEXPRO[INFO_MALE_PRONOUN_XIABOY|INFO_FEMALE_PRONOUN_XIAGIRL]}
5	{PLAYERAVATARSEXPRO[INFO_MALE_PRONOUN_BOYE|INFO_FEMALE_PRONOUN_GIRLE]}
4	{MATEAVATARSEXPRO[INFO_FEMALE_PRONOUN_HE|INFO_MALE_PRONOUN_SHE]}
2	{QuestGatherID}
2	{PLAYERAVATARSEXPRO[INFO_MALE_PRONOUN_BOYA|INFO_FEMALE_PRONOUN_GIRLA]}
1	{PLAYERAVATARSEXPRO[INFO_MALE_PRONOUN_BOYA|INFO_FEMALE_PRONOUN_GIRLB]}
1	{PLAYERAVATARSEXPRO[INFO_MALE_PRONOUN_BOYA|INFO_FEMALE_PRONOUN_GIRLC]}
"""

male = int(config['game']['male'])

pronouns_zh = {
    'NICKNAME': nickname,
    'CUTEBIGBROTHER': '可爱的大' + ('哥哥' if male else '姐姐'),
    'BIGBROTHER': '大' + ('哥哥' if male else '姐姐'),
    'BROTHER': '哥哥' if male else '姐姐',
    'SHE': '他' if male else '她',
    'BOY': '男孩' if male else '女孩',
    'KONG': '空' if male else '荧',
    'YING': '哥哥' if male else '荧',
    'UNCLE': '叔叔' if male else '阿姨',
}
