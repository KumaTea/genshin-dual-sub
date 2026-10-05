"""字幕窗口。

原先用 pygame 开窗 + SetLayeredWindowAttributes 的 colorkey 做透明：
指定一个"透明色"（黑），画面上所有这个颜色的像素都完全透明。
这么做没法要一个半透明的黑色背景——黑色恰好就是透明色。

改成 UpdateLayeredWindow 推逐像素 alpha 的位图：背景可以是任意颜色 + 任意
不透明度，文字始终不透明。窗口也不再依赖 SDL，位置、鼠标穿透、置顶都自己管。
一帧约 1.5ms。
"""

import ctypes
import logging
from ctypes import wintypes
from typing import Callable, Optional

import numpy as np
import win32api
import win32con
import win32gui

gdi32 = ctypes.windll.gdi32
user32 = ctypes.windll.user32

# 必须显式声明句柄类型。ctypes 默认按 32 位 int 传参、按 32 位 int 取返回值，
# 而 x64 下 HWND / HDC / HBITMAP 都是指针宽度的：
#
# * 传 HWND_TOPMOST(-1) 时，32 位的 -1 进到 64 位寄存器里变成 0x00000000FFFFFFFF
#   而不是 -1，SetWindowPos 认不出这个"窗口句柄"，直接失败还不设置 LastError
# * CreateDIBSection 之类返回的句柄会被截断成 32 位
#
# 窗口管理直接用 pywin32（它自己会正确处理），只有 UpdateLayeredWindow
# 这种 pywin32 没包装的才走 ctypes。
gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
gdi32.CreateCompatibleDC.restype = wintypes.HDC
gdi32.CreateDIBSection.argtypes = [
    wintypes.HDC, ctypes.c_void_p, wintypes.UINT,
    ctypes.POINTER(ctypes.c_void_p), wintypes.HANDLE, wintypes.DWORD,
]
gdi32.CreateDIBSection.restype = wintypes.HBITMAP
gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
gdi32.SelectObject.restype = wintypes.HGDIOBJ
gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
gdi32.DeleteDC.argtypes = [wintypes.HDC]
user32.GetDC.argtypes = [wintypes.HWND]
user32.GetDC.restype = wintypes.HDC
user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]

ULW_ALPHA = 0x02
WINDOW_CLASS = 'GenshinDualSubOverlay'


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ('biSize', wintypes.DWORD), ('biWidth', wintypes.LONG), ('biHeight', wintypes.LONG),
        ('biPlanes', wintypes.WORD), ('biBitCount', wintypes.WORD),
        ('biCompression', wintypes.DWORD), ('biSizeImage', wintypes.DWORD),
        ('biXPelsPerMeter', wintypes.LONG), ('biYPelsPerMeter', wintypes.LONG),
        ('biClrUsed', wintypes.DWORD), ('biClrImportant', wintypes.DWORD),
    ]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [('bmiHeader', BITMAPINFOHEADER), ('bmiColors', wintypes.DWORD * 3)]


class BLENDFUNCTION(ctypes.Structure):
    _fields_ = [
        ('BlendOp', ctypes.c_ubyte), ('BlendFlags', ctypes.c_ubyte),
        ('SourceConstantAlpha', ctypes.c_ubyte), ('AlphaFormat', ctypes.c_ubyte),
    ]


class OverlayWindow:
    def __init__(self, x: int, y: int, width: int, height: int, locked: bool = True):
        self.x, self.y = x, y
        self.width, self.height = max(1, width), max(1, height)
        self.locked = locked
        self.visible = True
        self.on_moved: Optional[Callable[[int, int], None]] = None

        self.hwnd = self._create_window()
        self._screen_dc = user32.GetDC(0)
        self._mem_dc = gdi32.CreateCompatibleDC(self._screen_dc)
        self._bitmap = None
        self._old_bitmap = None
        self._pixels: Optional[np.ndarray] = None
        self._blend = BLENDFUNCTION(win32con.AC_SRC_OVER, 0, 255, win32con.AC_SRC_ALPHA)
        self._allocate(self.width, self.height)

        self.set_locked(locked)
        win32gui.ShowWindow(self.hwnd, win32con.SW_SHOWNOACTIVATE)

    # ------------------------------------------------------------ 窗口

    def _create_window(self) -> int:
        instance = win32api.GetModuleHandle(None)
        window_class = win32gui.WNDCLASS()
        window_class.lpszClassName = WINDOW_CLASS
        window_class.hInstance = instance
        window_class.lpfnWndProc = {
            win32con.WM_NCHITTEST: self._on_hit_test,
            win32con.WM_DESTROY: lambda *_: 0,
        }
        try:
            win32gui.RegisterClass(window_class)
        except win32gui.error:
            pass  # 已注册（比如重启过窗口）

        style_ex = (
            win32con.WS_EX_LAYERED
            | win32con.WS_EX_TOOLWINDOW   # 不出现在任务栏和 Alt+Tab 里
            | win32con.WS_EX_TOPMOST
            | win32con.WS_EX_NOACTIVATE   # 点它不会把游戏切到后台
        )
        return win32gui.CreateWindowEx(
            style_ex, WINDOW_CLASS, 'Genshin Dual Sub', win32con.WS_POPUP,
            self.x, self.y, self.width, self.height, 0, 0, instance, None,
        )

    def _on_hit_test(self, hwnd, msg, wparam, lparam):
        """解锁时把整个窗口当作标题栏，拖动交给系统处理。"""
        if self.locked:
            return win32con.HTTRANSPARENT
        return win32con.HTCAPTION

    # ------------------------------------------------------------ 位图

    def _allocate(self, width: int, height: int) -> None:
        self._release_bitmap()

        info = BITMAPINFO()
        info.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        info.bmiHeader.biWidth = width
        info.bmiHeader.biHeight = -height  # 负数表示自上而下
        info.bmiHeader.biPlanes = 1
        info.bmiHeader.biBitCount = 32
        info.bmiHeader.biCompression = 0  # BI_RGB

        bits = ctypes.c_void_p()
        self._bitmap = gdi32.CreateDIBSection(
            self._screen_dc, ctypes.byref(info), 0, ctypes.byref(bits), None, 0)
        if not self._bitmap or not bits.value:
            raise RuntimeError('CreateDIBSection 失败')
        self._old_bitmap = gdi32.SelectObject(self._mem_dc, self._bitmap)

        buffer = (ctypes.c_uint8 * (width * height * 4)).from_address(bits.value)
        self._pixels = np.frombuffer(buffer, dtype=np.uint8).reshape(height, width, 4)
        self.width, self.height = width, height

    def _release_bitmap(self) -> None:
        self._pixels = None
        if self._bitmap:
            if self._old_bitmap:
                gdi32.SelectObject(self._mem_dc, self._old_bitmap)
            gdi32.DeleteObject(self._bitmap)
            self._bitmap = None
            self._old_bitmap = None

    def resize(self, width: int, height: int) -> None:
        if (width, height) == (self.width, self.height):
            return
        self._allocate(max(1, width), max(1, height))

    # ------------------------------------------------------------ 绘制

    def draw(self, rgb: np.ndarray, alpha: np.ndarray) -> None:
        """推一帧。rgb 是 (h, w, 3) 的 RGB，alpha 是 (h, w)。"""
        if self._pixels is None or not self.visible:
            return
        if rgb.shape[:2] != (self.height, self.width):
            self.resize(rgb.shape[1], rgb.shape[0])

        # UpdateLayeredWindow 要的是预乘 alpha 的 BGRA
        scaled = alpha.astype(np.uint16)
        self._pixels[:, :, 0] = (rgb[:, :, 2] * scaled // 255).astype(np.uint8)
        self._pixels[:, :, 1] = (rgb[:, :, 1] * scaled // 255).astype(np.uint8)
        self._pixels[:, :, 2] = (rgb[:, :, 0] * scaled // 255).astype(np.uint8)
        self._pixels[:, :, 3] = alpha

        self._push()

    def _push(self, position: Optional[tuple[int, int]] = None) -> None:
        # position 传 None 表示保持窗口当前位置——被系统拖动过之后
        # 不能再用我们记的旧坐标去覆盖，否则窗口会跳回去
        point = ctypes.byref(wintypes.POINT(*position)) if position else None
        ok = user32.UpdateLayeredWindow(
            wintypes.HWND(self.hwnd), wintypes.HDC(self._screen_dc),
            point, ctypes.byref(wintypes.SIZE(self.width, self.height)),
            wintypes.HDC(self._mem_dc), ctypes.byref(wintypes.POINT(0, 0)),
            wintypes.DWORD(0), ctypes.byref(self._blend), wintypes.DWORD(ULW_ALPHA),
        )
        if not ok:
            logging.debug(f'[OVL]\tUpdateLayeredWindow 失败: {ctypes.GetLastError()}')

    # ------------------------------------------------------------ 状态

    def sync_position(self) -> bool:
        """从系统读回真实位置（用户拖动之后）。返回位置是否变了。"""
        try:
            left, top, _, _ = win32gui.GetWindowRect(self.hwnd)
        except win32gui.error:
            return False
        if (left, top) == (self.x, self.y):
            return False
        self.x, self.y = left, top
        if self.on_moved:
            self.on_moved(left, top)
        return True

    def move(self, x: int, y: int, remember: bool = True) -> None:
        """把窗口挪到指定位置。

        remember=False 时不触发 on_moved 回调——"重置位置"要把配置写回
        -1（自动），不能让回调把算出来的具体坐标又写回去。
        """
        self.x, self.y = x, y
        win32gui.SetWindowPos(
            self.hwnd, win32con.HWND_TOPMOST, x, y, 0, 0,
            win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE,
        )
        if remember and self.on_moved:
            self.on_moved(x, y)

    def nudge(self, dx: int, dy: int) -> None:
        self.sync_position()
        self.move(self.x + dx, self.y + dy)

    def set_locked(self, locked: bool) -> None:
        """锁定 = 鼠标穿透，点击会落到下面的游戏上。"""
        self.locked = locked
        style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)
        if locked:
            style |= win32con.WS_EX_TRANSPARENT
        else:
            style &= ~win32con.WS_EX_TRANSPARENT
        win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, style)
        logging.info(f'[OVL]\t字幕窗口已{"锁定" if locked else "解锁，可以拖动了"}')

    def set_visible(self, visible: bool) -> None:
        self.visible = visible
        win32gui.ShowWindow(
            self.hwnd, win32con.SW_SHOWNOACTIVATE if visible else win32con.SW_HIDE)

    def raise_to_top(self) -> None:
        win32gui.SetWindowPos(
            self.hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE,
        )

    def close(self) -> None:
        self._release_bitmap()
        if self._mem_dc:
            gdi32.DeleteDC(self._mem_dc)
            self._mem_dc = None
        if self._screen_dc:
            user32.ReleaseDC(0, self._screen_dc)
            self._screen_dc = None
        if self.hwnd:
            try:
                win32gui.DestroyWindow(self.hwnd)
            except win32gui.error:
                pass
            self.hwnd = 0
