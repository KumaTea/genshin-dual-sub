"""字幕窗口的移动 / 重置。

会真的建一个分层窗口（本项目本来就只跑在 Windows 上）。
"""

import os
import tempfile

import pytest
import win32con
import win32gui

from ovl.window import OverlayWindow


@pytest.fixture
def window():
    win = OverlayWindow(100, 200, 640, 160, locked=True)
    yield win
    win.close()


def rect(win) -> tuple[int, int]:
    left, top, _, _ = win32gui.GetWindowRect(win.hwnd)
    return left, top


def test_window_starts_where_asked(window):
    assert rect(window) == (100, 200)


def test_move_actually_moves_the_window(window):
    """曾经这里只改了内部变量，屏幕上的窗口纹丝不动。

    原因是用裸 ctypes 调 SetWindowPos：HWND_TOPMOST 是 -1，
    没声明 argtypes 时按 32 位传进去，在 64 位寄存器里变成 0xFFFFFFFF，
    句柄不合法，调用直接失败（返回 0 且不设置 LastError）。
    """
    window.move(640, 300)
    assert rect(window) == (640, 300), '窗口没有真的移动'
    assert (window.x, window.y) == (640, 300)


def test_move_notifies_by_default(window):
    seen = []
    window.on_moved = lambda x, y: seen.append((x, y))
    window.move(300, 400)
    assert seen == [(300, 400)]


def test_move_can_skip_notification(window):
    """重置位置要把配置写回 -1，不能让回调把具体坐标又写回去。"""
    seen = []
    window.on_moved = lambda x, y: seen.append((x, y))
    window.move(300, 400, remember=False)
    assert rect(window) == (300, 400), '不通知也要真的移动'
    assert seen == []


def test_nudge_moves_relatively(window):
    window.move(500, 500)
    window.nudge(-20, 30)
    assert rect(window) == (480, 530)


def test_sync_position_reads_back_external_moves(window):
    """用户拖动之后要能把真实位置读回来。"""
    win32gui.SetWindowPos(window.hwnd, win32con.HWND_TOPMOST, 777, 333, 0, 0,
                          win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)
    assert window.sync_position() is True
    assert (window.x, window.y) == (777, 333)
    assert window.sync_position() is False, '没动就不该报告变化'


def test_raise_to_top_keeps_position(window):
    window.move(250, 350)
    window.raise_to_top()
    assert rect(window) == (250, 350)


def test_locked_window_is_click_through(window):
    def transparent() -> bool:
        style = win32gui.GetWindowLong(window.hwnd, win32con.GWL_EXSTYLE)
        return bool(style & win32con.WS_EX_TRANSPARENT)

    assert transparent() is True
    window.set_locked(False)
    assert transparent() is False
    window.set_locked(True)
    assert transparent() is True


def test_reset_position_restores_default_and_keeps_sentinel():
    """重置之后：窗口回到默认位置，配置里存回 -1（自动）。"""
    os.environ['GDS_CONFIG'] = os.path.join(tempfile.mkdtemp(), 'reset.ini')
    from share.config import Settings
    import ovl.configs as configs
    import ovl.manager as manager_module

    settings = Settings(os.environ['GDS_CONFIG'])
    settings.set('overlay', 'width', 640)
    settings.set('overlay', 'height', 160)
    monkey = [(configs, 'settings', configs.settings), (manager_module, 'settings', manager_module.settings)]
    for module, name, _ in monkey:
        setattr(module, name, settings)
    try:
        overlay_manager = manager_module.OverlayManager()
        try:
            default = configs.window_geometry()[:2]
            overlay_manager.window.move(900, 400)
            assert rect(overlay_manager.window) == (900, 400)

            overlay_manager.reset_position()
            assert rect(overlay_manager.window) == default, '没有回到默认位置'
            assert settings.int('overlay', 'x') == -1
            assert settings.int('overlay', 'y') == -1
        finally:
            overlay_manager.close()
    finally:
        for module, name, original in monkey:
            setattr(module, name, original)
