"""对话区域几何 & 聊天版式。

原先每个分辨率一组硬编码像素坐标，新分辨率必须手动补表，漏了就 KeyError。
现在改成"按画面比例存比例值"：

* 原神的 UI 按画面高度缩放，同一宽高比下各元素的相对位置基本不变
* 于是只需要两套比例（16:9 一类、超宽屏一类），任意分辨率都能算出像素坐标
* 3840x2160 / 3840x1600 的比例值由 debug/ 下的截图实测得出

三种聊天版式（layout）靠"说话人名字的颜色"区分，这个颜色是固定的：

* chat  —— 剧情对话框，名字 #ffc300，每行各自居中
* idle  —— 世界里 NPC 的闲聊，名字 #f1b703，位置比 chat 高一些、字号更小
* type2 —— 「灰眸」等旁白/通讯，名字 #ccffff，整块居中但**行内左对齐**，
           而且剧情中和大世界里出现的高度不一样，区域要同时盖住两种
"""

from typing import Optional

# 版式 -> 说话人名字颜色 (R, G, B)
SPEAKER_COLORS: dict[str, tuple[int, int, int]] = {
    'chat': (255, 195, 0),
    'idle': (241, 183, 3),
    'type2': (204, 255, 255),
}

# 冲突时的优先级：idle 的金色和 chat 的金色很接近，chat 更常见，优先判定
LAYOUT_PRIORITY = ('chat', 'type2', 'idle')

# 判定颜色时的容差与最少像素数
COLOR_TOLERANCE = 3
COLOR_MIN_PIXELS = 200

# 画面比例分类
ASPECT_16_9 = '16:9'
ASPECT_WIDE = 'wide'

# 每一行是否各自居中。原神的对话是逐字显现的，靠"行有没有居中"判断字出全了没有；
# type2 是整块居中、行内左对齐，第二行天然靠左，不能按行判断。
LINES_CENTERED: dict[str, bool] = {
    'chat': True,
    'idle': True,
    'type2': False,
}

# 说话人名字所在的横条 (left, top, right, bottom)，均为占画面宽/高的比例。
# 只在这条窄带里找颜色，避免把任务追踪、元素图标之类的金色误判成对话。
SPEAKER_BAND: dict[str, tuple[float, float, float, float]] = {
    ASPECT_16_9: (0.10, 0.755, 0.90, 0.835),
    ASPECT_WIDE: (0.10, 0.740, 0.90, 0.820),
}

# 各版式的正文区域 (left, top, right, bottom)，同样是比例。
# 16:9 实测自 3840x2160，wide 实测自 3840x1600。
DIALOG_AREA: dict[str, dict[str, tuple[float, float, float, float]]] = {
    ASPECT_16_9: {
        # 单行 y 1826-1881，两行到 1956（@2160）；@1080 实测 912-940
        'chat': (0.10, 0.8287, 0.90, 0.9167),
        # type2 有两个高度：剧情里和 chat 同高（@2160 1827-1956），
        # 大世界里和 idle 差不多高（@2160 实测 1765-1815），所以上边界要抬到 1750 左右。
        # 再往上就会吃到说话人名字旁边那个发光图标。
        'type2': (0.10, 0.8100, 0.90, 0.9167),
        # 闲聊比对话框高、字号更小（@2160 1763-1810，@1080 两行 865-923）
        'idle': (0.10, 0.7972, 0.90, 0.8796),
    },
    ASPECT_WIDE: {
        # 单行 y 1332-1371，两行到约 1428（@1600）
        'chat': (0.10, 0.8188, 0.90, 0.9219),
        # 超宽屏下 type2 比 chat 低约 26px（@1600 实测 1358-1397），
        # 上边界留够大世界那一版的余量
        'type2': (0.10, 0.8125, 0.90, 0.9219),
        'idle': (0.10, 0.7906, 0.90, 0.8750),
    },
}


def aspect_class(width: int, height: int) -> str:
    """按宽高比归类。1.9 以下按 16:9 处理，以上按超宽屏处理。"""
    if height <= 0:
        return ASPECT_16_9
    return ASPECT_16_9 if width / height <= 1.9 else ASPECT_WIDE


def _to_pixels(
        fractions: tuple[float, float, float, float],
        width: int,
        height: int,
) -> tuple[int, int, int, int]:
    left, top, right, bottom = fractions
    return (
        int(round(left * width)),
        int(round(top * height)),
        int(round(right * width)),
        int(round(bottom * height)),
    )


def speaker_band(width: int, height: int) -> tuple[int, int, int, int]:
    return _to_pixels(SPEAKER_BAND[aspect_class(width, height)], width, height)


def lines_centered(layout: Optional[str]) -> bool:
    return LINES_CENTERED.get(layout, True)


def dialog_area(width: int, height: int, layout: Optional[str] = None) -> tuple[int, int, int, int]:
    """某个版式下的正文裁切区域。layout 为空时给出能覆盖所有版式的并集。"""
    areas = DIALOG_AREA[aspect_class(width, height)]
    if layout in areas:
        return _to_pixels(areas[layout], width, height)
    union = (
        min(a[0] for a in areas.values()),
        min(a[1] for a in areas.values()),
        max(a[2] for a in areas.values()),
        max(a[3] for a in areas.values()),
    )
    return _to_pixels(union, width, height)


def parse_resolution(text: str) -> Optional[tuple[int, int]]:
    """'3840x2160' -> (3840, 2160)"""
    try:
        width, height = text.lower().split('x')
        return int(width), int(height)
    except (AttributeError, ValueError):
        return None
