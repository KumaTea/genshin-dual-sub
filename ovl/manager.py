"""把 Overlay 的状态画到窗口上。

**这个类的所有方法都只能在主线程调用。** 改窗口样式、移动窗口这些操作
会让 Windows 往窗口所属线程发消息，从别的线程调用会一直等到那个线程处理，
容易卡死。实际运行时这些动作都由 WM_HOTKEY / WM_COMMAND 触发，
本来就在主线程上；后台的 OCR 线程只通过 ovl.session.Overlay 传数据，不碰窗口。
"""

import logging
from typing import Optional

from ovl.configs import clamp_to_screen, window_geometry
from ovl.fonts import resolve_font_path
from ovl.render import Renderer, blank
from ovl.session import overlay
from ovl.window import OverlayWindow
from share.config import settings


class OverlayManager:
    def __init__(self):
        x, y, width, height = window_geometry()
        x, y = clamp_to_screen(x, y, width, height)

        self.window = OverlayWindow(x, y, width, height, locked=overlay.locked)
        self.window.on_moved = self._on_moved
        self.renderer = Renderer(
            width, height,
            resolve_font_path(),
            settings.int('overlay', 'font_size'),
            settings.int('overlay', 'ruby_size'),
        )

    # ------------------------------------------------------------ 绘制

    def draw_if_needed(self) -> None:
        segments = overlay.take()
        if segments is None:
            return

        if not segments:
            # 没字幕时整个窗口透明。背景色块只跟着文字出现，
            # 否则屏幕底部会一直挂着一条黑边
            self.window.draw(*blank(self.window.width, self.window.height))
            return

        rgb, alpha = self.renderer.render(
            segments, overlay.text_color, overlay.bg_color, overlay.bg_opacity)
        self.window.draw(rgb, alpha)

    # ------------------------------------------------------------ 交互

    def _on_moved(self, x: int, y: int) -> None:
        settings.set('overlay', 'x', x)
        settings.set('overlay', 'y', y)

    def toggle_locked(self) -> bool:
        if not self.window.locked:
            # 解锁期间可能被拖动过，先把真实位置读回来再存
            self.window.sync_position()
        self.window.set_locked(not self.window.locked)
        overlay.locked = self.window.locked
        settings.set('overlay', 'locked', int(self.window.locked))
        settings.save()
        overlay.touch()
        return self.window.locked

    def toggle_visible(self) -> bool:
        overlay.visible = not overlay.visible
        self.window.set_visible(overlay.visible)
        logging.info(f'[OVL]\t字幕已{"显示" if overlay.visible else "隐藏"}')
        return overlay.visible

    def nudge(self, dx: int, dy: int) -> None:
        self.window.nudge(dx, dy)
        settings.save()

    def reset_position(self) -> None:
        settings.set('overlay', 'x', -1)
        settings.set('overlay', 'y', -1)
        x, y, width, height = window_geometry()
        self.window.resize(width, height)
        self.renderer.resize(width, height)
        # remember=False：不让 on_moved 把算出来的具体坐标写回配置。
        # 配置里要保持 -1，这样以后换了分辨率还能重新算居中位置。
        self.window.move(x, y, remember=False)
        settings.save()
        overlay.touch()
        logging.info(f'[OVL]\t字幕位置已重置到 ({x}, {y})')

    def set_bg_opacity(self, value: int) -> int:
        result = overlay.set_bg_opacity(value)
        settings.set('overlay', 'bg_opacity', result)
        settings.save()
        logging.info(f'[OVL]\t背景不透明度：{result}%')
        return result

    def step_bg_opacity(self, delta: int) -> int:
        return self.set_bg_opacity(overlay.bg_opacity + delta)

    def sync(self) -> None:
        """定期把被拖动后的位置写回配置。"""
        if not self.window.locked and self.window.sync_position():
            settings.save()

    def close(self) -> None:
        self.window.close()


_manager: Optional[OverlayManager] = None


def get_manager() -> OverlayManager:
    global _manager
    if _manager is None:
        _manager = OverlayManager()
    return _manager
