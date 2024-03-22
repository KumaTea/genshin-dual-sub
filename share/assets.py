import re


# {NICKNAME}
# #{PLAYERAVATAR#SEXPRO[INFO_MALE_PRONOUN_BIGBROTHER|INFO_FEMALE_PRONOUN_BIGSISTER]}加油！目标是在限制时间内，找到手鞠哦！
replace_pattern = re.compile(r'\{.*?\}')

# <color=#00E1FFFF>Unta nunu</color>…好像和时间什么的有关系…别忘了查查手册吧？
html_tag_pattern = re.compile(r'<.*?>')

# 阿弥{RUBY#[D]生论派}利多学院
ruby_pattern = re.compile(r'\{RUBY\#\[D\](.*?)\}')
ruby_content_pattern = re.compile(r'\{RUBY\#\[[DS]\](.*?)\}')

# {M#哥哥}{F#姐姐}
pronoun_choice_pattern = re.compile(r'\{M#(.*?)\}\{F#(.*?)\}')
