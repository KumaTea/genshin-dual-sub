import re

# {NICKNAME}
# #{PLAYERAVATAR#SEXPRO[INFO_MALE_PRONOUN_BIGBROTHER|INFO_FEMALE_PRONOUN_BIGSISTER]}加油！
replace_pattern = re.compile(r'\{.*?\}')

# <color=#00E1FFFF>Unta nunu</color>…好像和时间什么的有关系…
html_tag_pattern = re.compile(r'<.*?>')

# 阿弥{RUBY#[D]生论派}利多学院 / 雪の{RUBY#[S]スネグーラチカ}娘
# [D] 多是释义，[S] 多是读音，两种都要处理——原先只匹配 [D]，
# 于是带 [S] 的句子会把 "{RUBY#[S]...}" 原样显示在字幕上
ruby_pattern = re.compile(r'\{RUBY#\[[DS]\](.*?)\}')
ruby_content_pattern = ruby_pattern

# {M#哥哥}{F#姐姐}
pronoun_choice_pattern = re.compile(r'\{M#(.*?)\}\{F#(.*?)\}')
