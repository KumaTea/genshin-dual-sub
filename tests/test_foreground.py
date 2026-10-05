"""前台限制开关 & 固定抓取区域。"""

import pytest

from ocr.gs import info
from share.config import Settings


@pytest.fixture
def env(tmp_path, monkeypatch):
    settings = Settings(str(tmp_path / 'config.ini'))
    monkeypatch.setattr(info, 'settings', settings)

    class FakeGI:
        hwnd = 0
        running = False
        foreground = False
        coords = (0, 0, 0, 0)
        width, height = 1920, 1080

        def set_resolution(self, width, height):
            self.width, self.height = width, height
            return True

    fake = FakeGI()
    monkeypatch.setattr(info, 'gi', fake)
    monkeypatch.setattr(info, '_warned_bad_region', False)
    return settings, fake


# ---------------------------------------------------------------- 前台开关

def test_foreground_required_by_default(env, monkeypatch):
    settings, gi = env
    assert settings.bool('game', 'require_foreground') is True
    monkeypatch.setattr(info, 'get_foreground_window_title', lambda: '记事本')
    assert info.check_genshin_foreground() is False
    assert gi.foreground is False


def test_genshin_in_foreground_is_detected(env, monkeypatch):
    _, gi = env
    monkeypatch.setattr(info, 'get_foreground_window_title', lambda: '原神')
    assert info.check_genshin_foreground() is True
    assert gi.foreground is True


def test_switch_off_ignores_foreground(env, monkeypatch):
    """关掉之后即使别的窗口在前台也照常工作。"""
    settings, gi = env
    settings.set('game', 'require_foreground', 0)
    monkeypatch.setattr(info, 'get_foreground_window_title',
                        lambda: pytest.fail('关掉之后不该再去查前台窗口'))
    assert info.check_genshin_foreground() is True
    assert gi.foreground is True


def test_switch_takes_effect_without_restart(env, monkeypatch):
    """开关是每次调用现读的，托盘里改完立刻生效。"""
    settings, _ = env
    monkeypatch.setattr(info, 'get_foreground_window_title', lambda: '记事本')
    assert info.check_genshin_foreground() is False
    settings.set('game', 'require_foreground', 0)
    assert info.check_genshin_foreground() is True
    settings.set('game', 'require_foreground', 1)
    assert info.check_genshin_foreground() is False


# ---------------------------------------------------------------- 抓取区域

def test_no_region_by_default(env):
    assert info.capture_region() is None


@pytest.mark.parametrize('raw,expected', [
    ('0,0,3840,2160', (0, 0, 3840, 2160)),
    (' 100 , 50 , 1920 , 1080 ', (100, 50, 1920, 1080)),
    ('0，0，1920，1080', (0, 0, 1920, 1080)),  # 全角逗号
])
def test_region_parsing(env, raw, expected):
    settings, _ = env
    settings.set('game', 'capture_region', raw)
    assert info.capture_region() == expected


@pytest.mark.parametrize('raw', ['abc', '1,2,3', '0,0,10,10', ''])
def test_bad_region_is_ignored(env, raw):
    """格式不对或者太小的区域要退回自动跟随窗口，而不是崩掉。"""
    settings, _ = env
    settings.set('game', 'capture_region', raw)
    assert info.capture_region() is None


def test_region_replaces_window_lookup(env, monkeypatch):
    """填了区域就不再找游戏窗口——游戏没开也能工作。"""
    settings, gi = env
    settings.set('game', 'capture_region', '0,0,3840,2160')
    monkeypatch.setattr(info, 'find_genshin_window',
                        lambda: pytest.fail('填了区域就不该再找窗口'))

    info.check_genshin_info()
    assert gi.running is True
    assert gi.coords == (0, 0, 3840, 2160)
    assert (gi.width, gi.height) == (3840, 2160)


def test_without_region_falls_back_to_window(env, monkeypatch):
    _, gi = env
    monkeypatch.setattr(info, 'find_genshin_window', lambda: 0)
    assert info.check_genshin_info() == 0
    assert gi.running is False
    assert gi.coords == (0, 0, 0, 0)


def test_window_coords_set_resolution(env, monkeypatch):
    _, gi = env
    monkeypatch.setattr(info, 'find_genshin_window', lambda: 4242)
    monkeypatch.setattr(info, 'get_no_title_coordinates', lambda hwnd: (2, 58, 1922, 1138))

    assert info.check_genshin_info() == 4242
    assert gi.running is True
    assert (gi.width, gi.height) == (1920, 1080)


def test_tiny_window_does_not_change_resolution(env, monkeypatch):
    """最小化时窗口尺寸会变得很小，不能拿它当分辨率。"""
    _, gi = env
    gi.width, gi.height = 3840, 2160
    monkeypatch.setattr(info, 'find_genshin_window', lambda: 7)
    monkeypatch.setattr(info, 'get_no_title_coordinates', lambda hwnd: (0, 0, 160, 90))

    info.check_genshin_info()
    assert (gi.width, gi.height) == (3840, 2160)
