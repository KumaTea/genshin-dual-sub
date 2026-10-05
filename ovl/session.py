"""字幕的运行时状态。

OCR 在后台线程里跑，绘制在主线程，两边只通过这个对象交换数据，
所以写入要加锁。
"""

import threading
from typing import Optional

from fmt.ruby import Segment
from share.config import settings


class Overlay:
    def __init__(self):
        self._lock = threading.Lock()
        self.segments: list[Segment] = []
        self.dirty: bool = True

        self.text_color = settings.color('overlay', 'text_color')
        self.bg_color = settings.color('overlay', 'bg_color')
        self.bg_opacity = max(0, min(100, settings.int('overlay', 'bg_opacity')))
        self.locked = settings.bool('overlay', 'locked')
        self.visible = True

    def set_segments(self, segments: list[Segment]) -> None:
        with self._lock:
            if segments == self.segments:
                return
            self.segments = segments
            self.dirty = True

    def take(self) -> Optional[list[Segment]]:
        """有更新时返回待绘制内容，否则 None。"""
        with self._lock:
            if not self.dirty:
                return None
            self.dirty = False
            return list(self.segments)

    def touch(self) -> None:
        with self._lock:
            self.dirty = True

    def set_bg_opacity(self, value: int) -> int:
        self.bg_opacity = max(0, min(100, value))
        self.touch()
        return self.bg_opacity


overlay = Overlay()
