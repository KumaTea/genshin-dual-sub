"""托盘图标 + 全局快捷键 + 消息循环。

原先退出只能在控制台按 Ctrl+C，而这个程序平时是最小化在后台跑的，
要退出得先把控制台找出来。现在托盘右键就能退出，也支持快捷键，
控制台的 Ctrl+C 依然有效，三条路都走同一套收尾逻辑。
"""

import ctypes
import logging
from typing import Callable, Optional

import win32api
import win32con
import win32gui

user32 = ctypes.windll.user32

WM_TRAY = win32con.WM_USER + 20
TRAY_UID = 1
CLASS_NAME = 'GenshinDualSubTray'

# 菜单项 ID
ID_TOGGLE_VISIBLE = 1001
ID_TOGGLE_LOCK = 1002
ID_RESET_POSITION = 1003
ID_QUIT = 1004
ID_TOGGLE_FOREGROUND = 1005
ID_OPACITY_BASE = 1100  # +0/25/50/75/100

OPACITY_STEPS = (0, 25, 50, 75, 100)

# 快捷键：Ctrl+Alt+<键>
HOTKEY_MODIFIERS = win32con.MOD_CONTROL | win32con.MOD_ALT
HOTKEYS = {
    1: (ord('M'), 'toggle_lock'),
    2: (ord('H'), 'toggle_visible'),
    3: (ord('Q'), 'quit'),
    4: (win32con.VK_UP, 'nudge_up'),
    5: (win32con.VK_DOWN, 'nudge_down'),
    6: (win32con.VK_LEFT, 'nudge_left'),
    7: (win32con.VK_RIGHT, 'nudge_right'),
    8: (win32con.VK_PRIOR, 'opacity_up'),
    9: (win32con.VK_NEXT, 'opacity_down'),
}

HOTKEY_HELP = """快捷键：
  Ctrl+Alt+M        锁定 / 解锁字幕（解锁后可用鼠标拖动）
  Ctrl+Alt+方向键   微调字幕位置
  Ctrl+Alt+PgUp/Dn  背景不透明度 ±10%
  Ctrl+Alt+H        显示 / 隐藏字幕
  Ctrl+Alt+Q        退出
托盘图标右键同样可以操作。"""


class TrayApp:
    """隐藏窗口，负责收托盘消息和快捷键。"""

    def __init__(self, actions: dict[str, Callable]):
        self.actions = actions
        self.running = True
        self.hwnd = self._create_window()
        self._add_icon()
        self._register_hotkeys()

    # ------------------------------------------------------------ 窗口

    def _create_window(self) -> int:
        instance = win32api.GetModuleHandle(None)
        window_class = win32gui.WNDCLASS()
        window_class.lpszClassName = CLASS_NAME
        window_class.hInstance = instance
        window_class.lpfnWndProc = {
            WM_TRAY: self._on_tray,
            win32con.WM_COMMAND: self._on_command,
            win32con.WM_HOTKEY: self._on_hotkey,
            win32con.WM_CLOSE: self._on_close,
            win32con.WM_DESTROY: self._on_close,
            win32con.WM_ENDSESSION: self._on_close,
            win32con.WM_QUERYENDSESSION: lambda *_: 1,
        }
        try:
            win32gui.RegisterClass(window_class)
        except win32gui.error:
            pass
        return win32gui.CreateWindow(
            CLASS_NAME, 'Genshin Dual Sub', win32con.WS_OVERLAPPED,
            0, 0, 0, 0, 0, 0, instance, None,
        )

    def _add_icon(self) -> None:
        icon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
        win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, (
            self.hwnd, TRAY_UID,
            win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP,
            WM_TRAY, icon, '原神双语字幕',
        ))

    def _remove_icon(self) -> None:
        try:
            win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, (self.hwnd, TRAY_UID))
        except win32gui.error:
            pass

    # ------------------------------------------------------------ 快捷键

    def _register_hotkeys(self) -> None:
        failed = []
        for hotkey_id, (key, _) in HOTKEYS.items():
            if not user32.RegisterHotKey(self.hwnd, hotkey_id, HOTKEY_MODIFIERS, key):
                failed.append(hotkey_id)
        if failed:
            logging.warning(f'[OVL]\t{len(failed)} 个快捷键被其他程序占用，未能注册')

    def _unregister_hotkeys(self) -> None:
        for hotkey_id in HOTKEYS:
            user32.UnregisterHotKey(self.hwnd, hotkey_id)

    def _on_hotkey(self, hwnd, msg, wparam, lparam):
        entry = HOTKEYS.get(wparam)
        if entry:
            self._run(entry[1])
        return 0

    # ------------------------------------------------------------ 托盘菜单

    def _on_tray(self, hwnd, msg, wparam, lparam):
        if lparam in (win32con.WM_RBUTTONUP, win32con.WM_LBUTTONDBLCLK):
            self._show_menu()
        return 0

    def _show_menu(self) -> None:
        state = self.actions.get('state', dict)()
        menu = win32gui.CreatePopupMenu()

        win32gui.AppendMenu(
            menu, win32con.MF_STRING, ID_TOGGLE_VISIBLE,
            '隐藏字幕\tCtrl+Alt+H' if state.get('visible', True) else '显示字幕\tCtrl+Alt+H')
        win32gui.AppendMenu(
            menu, win32con.MF_STRING, ID_TOGGLE_LOCK,
            '解锁位置（可拖动）\tCtrl+Alt+M' if state.get('locked', True)
            else '锁定位置\tCtrl+Alt+M')
        win32gui.AppendMenu(menu, win32con.MF_STRING, ID_RESET_POSITION, '重置位置')

        flags = win32con.MF_STRING
        if state.get('require_foreground', True):
            flags |= win32con.MF_CHECKED
        win32gui.AppendMenu(menu, flags, ID_TOGGLE_FOREGROUND, '仅在游戏前台时工作')

        submenu = win32gui.CreatePopupMenu()
        current = state.get('bg_opacity', 0)
        for step in OPACITY_STEPS:
            flags = win32con.MF_STRING
            if step == current:
                flags |= win32con.MF_CHECKED
            win32gui.AppendMenu(submenu, flags, ID_OPACITY_BASE + step, f'{step}%')
        win32gui.AppendMenu(menu, win32con.MF_POPUP, submenu, '背景不透明度')

        win32gui.AppendMenu(menu, win32con.MF_SEPARATOR, 0, '')
        win32gui.AppendMenu(menu, win32con.MF_STRING, ID_QUIT, '退出\tCtrl+Alt+Q')

        # 不先 SetForegroundWindow 的话，菜单点外面不会消失
        position = win32gui.GetCursorPos()
        win32gui.SetForegroundWindow(self.hwnd)
        win32gui.TrackPopupMenu(
            menu, win32con.TPM_LEFTALIGN | win32con.TPM_RIGHTBUTTON,
            position[0], position[1], 0, self.hwnd, None)
        win32gui.PostMessage(self.hwnd, win32con.WM_NULL, 0, 0)
        win32gui.DestroyMenu(menu)

    def _on_command(self, hwnd, msg, wparam, lparam):
        command = win32api.LOWORD(wparam)
        if command == ID_TOGGLE_VISIBLE:
            self._run('toggle_visible')
        elif command == ID_TOGGLE_LOCK:
            self._run('toggle_lock')
        elif command == ID_RESET_POSITION:
            self._run('reset_position')
        elif command == ID_TOGGLE_FOREGROUND:
            self._run('toggle_foreground')
        elif command == ID_QUIT:
            self._run('quit')
        elif ID_OPACITY_BASE <= command <= ID_OPACITY_BASE + 100:
            self._run('set_opacity', command - ID_OPACITY_BASE)
        return 0

    def _on_close(self, hwnd, msg, wparam, lparam):
        self.running = False
        return 0

    # ------------------------------------------------------------ 循环

    def _run(self, name: str, *args) -> None:
        action = self.actions.get(name)
        if not action:
            return
        try:
            action(*args)
        except Exception:
            logging.exception(f'[OVL]\t执行 {name} 时出错')

    def pump(self) -> bool:
        win32gui.PumpWaitingMessages()
        return self.running

    def stop(self) -> None:
        self.running = False

    def notify(self, title: str, message: str) -> None:
        try:
            win32gui.Shell_NotifyIcon(win32gui.NIM_MODIFY, (
                self.hwnd, TRAY_UID, win32gui.NIF_INFO, 0, 0, '',
                message, 5000, title, win32gui.NIIF_INFO,
            ))
        except win32gui.error:
            pass

    def close(self) -> None:
        self._unregister_hotkeys()
        self._remove_icon()
        if self.hwnd:
            try:
                win32gui.DestroyWindow(self.hwnd)
            except win32gui.error:
                pass
            self.hwnd = 0


_app: Optional[TrayApp] = None


def get_app(actions: Optional[dict[str, Callable]] = None) -> Optional[TrayApp]:
    global _app
    if _app is None and actions is not None:
        _app = TrayApp(actions)
    return _app
