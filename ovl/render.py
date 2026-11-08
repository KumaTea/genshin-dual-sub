"""字幕排版与绘制。

用 pygame 的字体渲染，但不开 pygame 的窗口——只把结果画到内存 Surface 上，
再交给 ovl.window 推到分层窗口。这样字体渲染的能力留着，
显示部分不受 SDL 的窗口行为限制。

注音最多两行，自下而上：紧贴正文的是假名读音，再上面是游戏官方上标。
"""

import logging
from typing import Optional

import numpy as np
import pygame

from fmt.ruby import Segment
from ovl.fonts import get_font

# 正文与注音、注音与注音之间的间距（相对于注音字号）
ROW_GAP_RATIO = 0.05
# 长句缩小字号时按这个步长向下取整。不取整的话每句长度不同的字幕
# 都会算出一个新字号，各新建一个字体
FONT_SIZE_STEP = 4
# 最多同时缓存几个字体，多了就扔掉最久没用的。
# 游戏自带的日文字体有 11MB，每个 pygame 字体对象约占 1.5MB
MAX_CACHED_FONTS = 8


class Renderer:
    def __init__(self, width: int, height: int, font_path: Optional[str],
                 font_size: int, ruby_size: int):
        pygame.font.init()
        self.width, self.height = width, height
        self.font_path = font_path
        self.font_size = font_size
        self.ruby_size = ruby_size
        self._font_cache: dict[tuple[int, bool], pygame.font.Font] = {}

    # ------------------------------------------------------------ 字体

    def font(self, size: int, ruby: bool = False) -> pygame.font.Font:
        key = (size, ruby)
        # dict 保持插入顺序：每次用到就挪到末尾，开头的就是最久没用的
        font = self._font_cache.pop(key, None)
        if font is None:
            font = get_font(self.font_path, size)
            while len(self._font_cache) >= MAX_CACHED_FONTS:
                del self._font_cache[next(iter(self._font_cache))]
        self._font_cache[key] = font
        return font

    def _text_size(self, scale: float) -> int:
        return max(8, round(self.font_size * scale))

    def _ruby_size(self, scale: float) -> int:
        return max(6, int(self.ruby_size * scale))

    def resize(self, width: int, height: int) -> None:
        self.width, self.height = width, height

    def set_sizes(self, font_size: int, ruby_size: int) -> None:
        if (font_size, ruby_size) != (self.font_size, self.ruby_size):
            self.font_size, self.ruby_size = font_size, ruby_size
            self._font_cache.clear()

    # ------------------------------------------------------------ 排版

    def _fit_scale(self, segments: list[Segment]) -> float:
        """正文太长时整体缩小，直到能塞进窗口宽度。"""
        text = ''.join(s[0] for s in segments)
        if not text:
            return 1.0

        limit = self.width * 0.98
        scale = 1.0
        for _ in range(8):
            font = self.font(self._text_size(scale))
            width = sum(font.size(s[0])[0] for s in segments)
            if width <= limit:
                return scale
            scale *= max(0.5, limit / max(1, width))
            # 向下取整到 FONT_SIZE_STEP，字号就只有十几种可能
            size = int(self.font_size * scale) // FONT_SIZE_STEP * FONT_SIZE_STEP
            scale = max(8, size) / self.font_size
        return scale

    def layout(self, segments: list[Segment]) -> list[tuple[pygame.Surface, pygame.Rect]]:
        if not segments:
            return []

        scale = self._fit_scale(segments)
        font = self.font(self._text_size(scale))
        ruby_font = self.font(self._ruby_size(scale), ruby=True)
        ruby_height = ruby_font.get_height()
        gap = max(1, int(ruby_height * ROW_GAP_RATIO))

        max_rows = max((len(rows) for _, rows in segments), default=0)
        # 正文基线：把注音行的总高度腾出来后垂直居中
        ruby_block = max_rows * (ruby_height + gap)
        text_top = (self.height - font.get_height() - ruby_block) / 2 + ruby_block

        blits: list[tuple[pygame.Surface, pygame.Rect]] = []
        x = 0.0
        for text, rows in segments:
            surface = font.render(text, True, (255, 255, 255))
            rect = surface.get_rect(topleft=(int(x), int(text_top)))
            blits.append((surface, rect))

            for index, row in enumerate(rows):
                if not row:
                    continue
                ruby_surface = ruby_font.render(row, True, (255, 255, 255))
                bottom = int(text_top) - index * (ruby_height + gap) - gap
                blits.append((
                    ruby_surface,
                    ruby_surface.get_rect(centerx=rect.centerx, bottom=bottom),
                ))
            x += rect.width

        # 上面是左对齐排的，整体平移一次做水平居中
        offset = int((self.width - x) / 2)
        for _, rect in blits:
            rect.move_ip(offset, 0)
        return blits

    # ------------------------------------------------------------ 绘制

    def render(
            self,
            segments: list[Segment],
            text_color: tuple[int, int, int],
            bg_color: tuple[int, int, int],
            bg_opacity: int,
    ) -> tuple[np.ndarray, np.ndarray]:
        """返回 (rgb, alpha)，都是 (h, w, ...) 的 uint8 数组。"""
        surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA, 32)
        bg_alpha = int(round(max(0, min(100, bg_opacity)) * 255 / 100))
        surface.fill((*bg_color, bg_alpha))

        if segments:
            for text_surface, rect in self.layout(segments):
                # 字模本身是白色，用 alpha 通道当蒙版染成目标颜色，
                # 这样换颜色不用重新 render
                text_surface.fill((*text_color, 255), special_flags=pygame.BLEND_RGBA_MULT)
                surface.blit(text_surface, rect)

        rgb = np.ascontiguousarray(pygame.surfarray.pixels3d(surface).transpose(1, 0, 2))
        alpha = np.ascontiguousarray(pygame.surfarray.pixels_alpha(surface).transpose(1, 0))
        return rgb, alpha


def blank(width: int, height: int) -> tuple[np.ndarray, np.ndarray]:
    return (
        np.zeros((height, width, 3), dtype=np.uint8),
        np.zeros((height, width), dtype=np.uint8),
    )


def preview(segments: list[Segment], width: int, height: int, font_path: Optional[str],
            font_size: int, ruby_size: int, **kwargs) -> np.ndarray:
    """给测试和调试用：直接渲染成一张不透明的 BGR 图。"""
    renderer = Renderer(width, height, font_path, font_size, ruby_size)
    rgb, alpha = renderer.render(
        segments,
        kwargs.get('text_color', (255, 255, 255)),
        kwargs.get('bg_color', (0, 0, 0)),
        kwargs.get('bg_opacity', 100),
    )
    scaled = alpha.astype(np.uint16)[:, :, None]
    composited = (rgb.astype(np.uint16) * scaled // 255).astype(np.uint8)
    logging.debug(f'[OVL]\t预览渲染 {width}x{height}，{len(segments)} 段')
    return composited[:, :, ::-1]
