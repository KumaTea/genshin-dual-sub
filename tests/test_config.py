"""配置读写：缺项补默认、类型转换、回写。"""

import os

from share.config import DEFAULTS, Settings


def write(path: str, content: str) -> str:
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    return path


def test_missing_file_falls_back_to_defaults(tmp_path):
    settings = Settings(str(tmp_path / 'nope.ini'))
    assert settings.get('general', 'dst_lang') == DEFAULTS['general']['dst_lang'][0]
    assert settings.int('overlay', 'font_size') > 0


def test_partial_config_is_filled(tmp_path):
    path = write(str(tmp_path / 'config.ini'), '[general]\ndst_lang = en-us\n')
    settings = Settings(path)
    assert settings.get('general', 'dst_lang') == 'en-us'
    # 没写的键用默认值补上，而不是 KeyError
    assert settings.int('overlay', 'height') == int(DEFAULTS['overlay']['height'][0])

    settings.save_if_incomplete()
    reloaded = Settings(path)
    assert reloaded.get('general', 'dst_lang') == 'en-us'
    assert reloaded.parser.has_option('overlay', 'bg_opacity')


def test_bad_values_fall_back(tmp_path):
    path = write(str(tmp_path / 'config.ini'),
                 '[overlay]\nfont_size = abc\nbg_opacity = \n')
    settings = Settings(path)
    assert settings.int('overlay', 'font_size') == int(DEFAULTS['overlay']['font_size'][0])
    assert settings.int('overlay', 'bg_opacity') == 0


def test_float_accepts_int_and_float(tmp_path):
    path = write(str(tmp_path / 'config.ini'), '[intervals]\ndialog = 0.25\ntalking = 2\n')
    settings = Settings(path)
    assert settings.float('intervals', 'dialog') == 0.25
    assert settings.float('intervals', 'talking') == 2.0
    assert settings.int('intervals', 'dialog') == 0


def test_bool_parsing(tmp_path):
    path = write(str(tmp_path / 'config.ini'),
                 '[game]\nis_male = 0\n[overlay]\nlocked = true\nshow_ruby = YES\n')
    settings = Settings(path)
    assert settings.bool('game', 'is_male') is False
    assert settings.bool('overlay', 'locked') is True
    assert settings.bool('overlay', 'show_ruby') is True


def test_color_parsing(tmp_path):
    path = write(str(tmp_path / 'config.ini'),
                 '[overlay]\ntext_color = #ff8000\nbg_color = 00ff00\n')
    settings = Settings(path)
    assert settings.color('overlay', 'text_color') == (255, 128, 0)
    assert settings.color('overlay', 'bg_color') == (0, 255, 0)


def test_bad_color_falls_back(tmp_path):
    path = write(str(tmp_path / 'config.ini'), '[overlay]\ntext_color = nope\n')
    assert Settings(path).color('overlay', 'text_color') == (255, 255, 255)


def test_runtime_changes_persist(tmp_path):
    path = str(tmp_path / 'config.ini')
    settings = Settings(path)
    settings.set('overlay', 'x', 123)
    settings.set('overlay', 'bg_opacity', 60)
    settings.save()

    reloaded = Settings(path)
    assert reloaded.int('overlay', 'x') == 123
    assert reloaded.int('overlay', 'bg_opacity') == 60


def test_save_keeps_unknown_keys(tmp_path):
    path = write(str(tmp_path / 'config.ini'), '[general]\nmy_own_key = keep me\n')
    settings = Settings(path)
    settings.save()
    with open(path, encoding='utf-8') as f:
        assert 'my_own_key' in f.read()


def test_saved_file_is_reloadable_with_legacy_keys(tmp_path):
    """旧版本遗留的键（比如 general.width）不能让写回的文件变得读不了。

    之前 save() 把这些键放在第二轮循环里补，同一个 section 写了两次，
    再读就 DuplicateSectionError。
    """
    path = write(str(tmp_path / 'config.ini'),
                 '[general]\nwidth = 3840\nheight = 2160\n'
                 '[overlay]\novl_h = 120\novl_fps = 10\n')
    Settings(path).save()

    with open(path, encoding='utf-8') as f:
        content = f.read()
    assert content.count('[general]') == 1
    assert content.count('[overlay]') == 1

    reloaded = Settings(path)  # 读不回来就会在这里抛异常
    assert reloaded.parser.get('general', 'width') == '3840'
    assert reloaded.int('overlay', 'height') > 0


def test_unknown_section_is_preserved(tmp_path):
    path = write(str(tmp_path / 'config.ini'), '[my_section]\nfoo = bar\n')
    Settings(path).save()
    reloaded = Settings(path)
    assert reloaded.parser.get('my_section', 'foo') == 'bar'


def test_saved_file_has_comments(tmp_path):
    path = str(tmp_path / 'config.ini')
    Settings(path).save()
    assert os.path.exists(path)
    with open(path, encoding='utf-8') as f:
        content = f.read()
    assert '; ' in content
    assert '[overlay]' in content
