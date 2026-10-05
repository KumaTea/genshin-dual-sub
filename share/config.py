"""配置读写。

原先各模块直接 `config['overlay']['font_size']` 取字符串再手动 int()，
键缺失就 KeyError，改动也无法回写。这里统一成一个带默认值的 settings 对象：

* 缺少的键用默认值补齐，并写回 config.ini（附带注释），首次运行即可得到完整配置
* 类型转换集中在一处
* 运行时改动（字幕框位置、背景透明度）可以 save() 持久化
"""

import logging
import os
from configparser import ConfigParser

CONFIG_FILE = os.environ.get('GDS_CONFIG', 'config.ini')

# section -> key -> (默认值, 说明)
DEFAULTS: dict[str, dict[str, tuple[str, str]]] = {
    'general': {
        'data_path': ('data', '文本数据存放目录'),
        'dst_lang': ('ja-jp', '第二字幕语言：ja-jp / en-us / ko-kr / ...'),
        'log_level': ('INFO', 'DEBUG / INFO / WARNING / ERROR'),
    },
    'game': {
        'nickname': ('旅行者', '游戏内昵称'),
        'is_male': ('1', '主角性别 True: 1 / False: 0'),
        'wanderer': ('流浪者', '散兵的名字'),
        'little_one': ('小黑', '纳塔小龙的名字'),
        'data_path': ('', '游戏 YuanShen_Data / GenshinImpact_Data 目录，留空则自动查找'),
        'resolution': ('', '游戏分辨率，留空则自动检测'),
        'require_foreground': ('1', '1 = 只在游戏处于前台时工作（省资源、识别更准）；0 = 一直工作'),
        'capture_region': ('', '固定抓取区域 left,top,right,bottom；留空则自动跟随游戏窗口。'
                               '填的话要是游戏画面的完整范围，不能只圈字幕那一条'),
    },
    'intervals': {
        'genshin_info': ('5', '检测游戏窗口的间隔（秒）'),
        'genshin_fg': ('5', '检测游戏是否在前台的间隔（秒）'),
        'talking': ('0.5', '检测是否在对话的间隔（秒）'),
        'dialog': ('0.5', '识别对话文本的间隔（秒）'),
        'draw': ('0.1', '重绘字幕的间隔（秒）'),
    },
    'overlay': {
        'x': ('-1', '字幕窗口左上角 X，-1 表示水平居中'),
        'y': ('-1', '字幕窗口左上角 Y，-1 表示贴屏幕底部'),
        'width': ('0', '字幕窗口宽度，0 表示与屏幕同宽'),
        'height': ('160', '字幕窗口高度'),
        'fps': ('10', '字幕窗口刷新率'),
        'font_size': ('72', '正文字号'),
        'ruby_size': ('36', '注音字号'),
        'font_path': ('', '字体文件，留空则使用游戏自带字体'),
        'text_color': ('#ffffff', '字幕颜色'),
        'bg_color': ('#000000', '字幕背景色'),
        'bg_opacity': ('0', '字幕背景不透明度，0 = 全透明，100 = 纯色'),
        'locked': ('1', '1 = 鼠标穿透（不可拖动），0 = 可以拖动'),
        'show_ruby': ('1', '是否显示注音'),
        'show_official_ruby': ('1', '有官方上标时显示上标（而不是假名读音）'),
    },
    'download': {
        'allow_download': ('0', '是否允许自动下载文本数据，1 = 允许，0 = 每次询问'),
        'base_url': (
            'https://gitlab.com/Dimbreath/animegamedata2/-/raw/main/TextMap',
            '文本数据下载地址',
        ),
    },
}


def _hex_to_rgb(value: str, fallback: tuple[int, int, int]) -> tuple[int, int, int]:
    text = value.strip().lstrip('#')
    if len(text) != 6:
        return fallback
    try:
        return int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16)
    except ValueError:
        return fallback


class Settings:
    def __init__(self, path: str = CONFIG_FILE):
        self.path = path
        self.parser = ConfigParser(allow_no_value=True)
        self.parser.read(path, encoding='utf-8')
        self._missing = self._fill_defaults()

    def _fill_defaults(self) -> bool:
        """补齐缺失的 section / key，返回是否有改动。"""
        missing = False
        for section, keys in DEFAULTS.items():
            if not self.parser.has_section(section):
                self.parser.add_section(section)
                missing = True
            for key, (default, _) in keys.items():
                if not self.parser.has_option(section, key):
                    self.parser.set(section, key, default)
                    missing = True
        return missing

    # ---------- 取值 ----------

    def get(self, section: str, key: str) -> str:
        return self.parser.get(section, key, fallback=DEFAULTS[section][key][0])

    def int(self, section: str, key: str) -> int:
        raw = self.get(section, key)
        try:
            return int(float(raw))
        except (TypeError, ValueError):
            return int(float(DEFAULTS[section][key][0]))

    def float(self, section: str, key: str) -> float:
        raw = self.get(section, key)
        try:
            return float(raw)
        except (TypeError, ValueError):
            return float(DEFAULTS[section][key][0])

    def bool(self, section: str, key: str) -> bool:
        return self.get(section, key).strip().lower() in ('1', 'true', 'yes', 'on')

    def color(self, section: str, key: str) -> tuple[int, int, int]:
        return _hex_to_rgb(self.get(section, key), _hex_to_rgb(DEFAULTS[section][key][0], (0, 0, 0)))

    def set(self, section: str, key: str, value) -> None:
        if not self.parser.has_section(section):
            self.parser.add_section(section)
        self.parser.set(section, key, str(value))

    # ---------- 写回 ----------

    def _extra_options(self, section: str) -> list[str]:
        """用户自己加的、或者旧版本遗留的键。"""
        if not self.parser.has_section(section):
            return []
        known = DEFAULTS.get(section, {})
        return [k for k in self.parser.options(section) if k not in known]

    def save(self) -> None:
        """带注释写回 config.ini。

        每个 section 只能写一次——之前把"额外的键"放在第二轮循环里单独补，
        结果同一个 section 出现两次，configparser 再读就报 DuplicateSectionError。
        """
        lines = ['; 本文件由程序自动补全，注释使用英文分号', '']

        for section, keys in DEFAULTS.items():
            lines.append(f'[{section}]')
            for key, (_, comment) in keys.items():
                if comment:
                    lines.append(f'; {comment}')
                lines.append(f'{key} = {self.get(section, key)}')
                lines.append('')
            extra = self._extra_options(section)
            if extra:
                lines.append('; 以下是本程序不认识的配置项，原样保留')
                lines.extend(f'{k} = {self.parser.get(section, k)}' for k in extra)
                lines.append('')
            lines.append('')

        for section in self.parser.sections():
            if section in DEFAULTS:
                continue
            lines.append(f'[{section}]')
            lines.extend(f'{k} = {self.parser.get(section, k)}'
                         for k in self.parser.options(section))
            lines.append('')

        try:
            with open(self.path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
        except OSError as e:
            logging.error(f'[CFG]\t无法写入 {self.path}: {e}')

    def save_if_incomplete(self) -> None:
        if self._missing:
            logging.info(f'[CFG]\t已补全 {self.path} 中缺失的配置项')
            self.save()
            self._missing = False


settings = Settings()
