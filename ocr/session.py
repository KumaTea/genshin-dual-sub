"""游戏状态 & OCR 引擎。

引擎改成惰性加载：原先 `import ocr.session` 就会把模型读进内存，
导致跑测试、看 --help 都要等好几秒，也没法在不加载模型的情况下单测几何计算。
"""

import logging
import threading
import time
from typing import Optional

import numpy as np

from ocr.configs import dialog_area, parse_resolution
from share.config import settings

_engine = None
_engine_lock = threading.Lock()
# 一个 RapidOCR 实例不能多线程同时调用：每次调用都会改实例上的开关，
# OpenVINO 引擎每个模型也只有一个推理请求。调用方要先拿这把锁。
engine_call_lock = threading.Lock()

# 推理后端，取值同 rapidocr.EngineType：'openvino' / 'onnxruntime' ...
# OpenVINO 和 onnxruntime 结果一样，在 Intel CPU 上更快。
INFERENCE_ENGINE = 'openvino'


def fixed_rec_shapes() -> bool:
    """识别输入要不要补宽到固定的几档（见 ocr.ocr.pad_for_rec）。

    只有 OpenVINO 需要：它的 CPU 插件每个新输入形状都要留约 20MB 不放。
    onnxruntime 同样的模型同样的输入不涨内存，补宽只会白白多算 10% 左右。
    """
    return INFERENCE_ENGINE == 'openvino'


# 和 onnxocr 4.x 的默认参数对齐。RapidOCR 自己的默认值不一样
# （会先缩放输入图、做膨胀、阈值也不同），不改的话识别结果会变。
ONNXOCR_4X = {
    'Global.use_cls': False,
    'Global.use_preprocess_img': False,
    'Global.use_vertical_padding': False,
    'Det.limit_side_len': 736,
    'Det.limit_type': 'min',
    'Det.mean': [0.485, 0.456, 0.406],
    'Det.std': [0.229, 0.224, 0.225],
    'Det.thresh': 0.2,
    'Det.box_thresh': 0.45,
    'Det.unclip_ratio': 1.4,
    'Det.max_candidates': 3000,
    'Det.use_dilation': False,
}


class GenshinInfo:
    """游戏窗口 & 对话状态。"""

    def __init__(self):
        self.running: bool = False
        self.foreground: bool = False
        self.hwnd: int = 0
        self.coords: tuple[int, int, int, int] = (0, 0, 0, 0)
        self.talking: bool = False
        self.layout: Optional[str] = None
        self.screenshot: Optional[np.ndarray] = None
        self.last_shot: float = 0.0

        configured = parse_resolution(settings.get('game', 'resolution'))
        self.width, self.height = configured or (1920, 1080)

    @property
    def resolution(self) -> str:
        return f'{self.width}x{self.height}'

    def set_resolution(self, width: int, height: int) -> bool:
        if (width, height) == (self.width, self.height) or width <= 0 or height <= 0:
            return False
        self.width, self.height = width, height
        logging.info(f'[OCR]\t分辨率：{self.resolution}')
        return True

    def dialog_area(self) -> tuple[int, int, int, int]:
        return dialog_area(self.width, self.height, self.layout)


gi = GenshinInfo()


def get_engine():
    """第一次用到时才加载 OCR 模型。"""
    global _engine
    if _engine is not None:
        return _engine
    with _engine_lock:
        if _engine is None:
            _engine = _build_engine()
    return _engine


def _build_engine():
    from rapidocr import EngineType, RapidOCR

    started = time.perf_counter()
    # 对话框又扁又宽，limit_type='min' 配合正文区域高度，
    # 可以让检测器不去缩放输入图，既快又准。
    _, top, _, bottom = gi.dialog_area()
    engine = RapidOCR(params={
        **ONNXOCR_4X,
        'Det.limit_side_len': max(64, bottom - top),
        **{f'{key}.engine_type': EngineType(INFERENCE_ENGINE) for key in ('Det', 'Cls', 'Rec')},
        'EngineConfig.openvino.performance_hint': 'LATENCY',
    })
    _plain_det_config(engine)
    logging.info(f'[OCR]\t模型加载完成，用时 {time.perf_counter() - started:.1f}s')
    return engine


def _plain_det_config(engine) -> None:
    """把检测器的 mean / std 从 omegaconf 的 ListConfig 换成普通 list。

    RapidOCR 每次检测都会 np.array(mean)。numpy 会先去 ListConfig 上找
    __array__ 之类的属性，ListConfig 每找一次就构造并抛出一个
    ConfigAttributeError（每帧 12 个），numpy 接住之后接着往下走。
    这些异常的 traceback 和栈帧互相引用成环，整条调用栈连同 18MB 的截图
    都要等循环垃圾回收才释放，平白多占一两百 MB，抛异常本身也费 CPU。
    """
    detector = getattr(engine, 'text_det', None)
    for name in ('mean', 'std'):
        value = getattr(detector, name, None)
        if value is not None:
            setattr(detector, name, [float(v) for v in value])
