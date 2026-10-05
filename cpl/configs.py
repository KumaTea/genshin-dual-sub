"""建索引时用到的过滤规则。"""

from fmt.ja import pronouns_source
from share.config import settings

# 含这些词的条目是开发用的占位/测试文本，不该出现在字幕里
blacklist = [
    'test',
    'param',
    'hidden',
    'unreleased',
    'sprite_preset',
    '$[',
]

# {0} ~ {9} 是格式化占位符，\n 在数据里是两个字符
remove_list = ['{%d}' % i for i in range(10)]
remove_list.append('\\n')


def get_pronouns_zh() -> dict[str, str]:
    """中文侧代词表，额外补上散兵和小龙的自定义名字。"""
    pronouns = pronouns_source()
    pronouns.update({
        # {REALNAME[ID(1)|DELAYHANDLE(true)]} / {REALNAME[ID(1)|HOSTONLY(true)]} / {REALNAME[ID(1)]}
        'REALNAME[ID(1)': settings.get('game', 'wanderer'),
        # {REALNAME[ID(2)|SHOWHOST(true)]}
        'REALNAME[ID(2)': settings.get('game', 'little_one'),
    })
    return pronouns


# 兼容旧代码
pronouns_zh = get_pronouns_zh()
