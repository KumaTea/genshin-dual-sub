import time
import paddle
import psutil
import numpy as np
from paddleocr import PaddleOCR
from share.session import config


class GenshinInfo:
    def __init__(self):
        self.running: bool = False
        self.foreground: bool = False
        self.hwnd: int = 0
        self.resolution: str = '1920x1080'
        self.coords: tuple = (0, 0, 0, 0)
        self.talking: bool = False
        self.screenshot: np.ndarray = np.zeros((1080, 1920, 3), dtype=np.uint8)
        self.last_shot: float = 0.

        self.load()

    def load(self):
        self.resolution = config['game']['resolution']
        self.last_shot = time.time()


gi = GenshinInfo()

ppocr = PaddleOCR(
    lang='ch',
    use_gpu=paddle.device.is_compiled_with_cuda() and psutil.virtual_memory().total > 16 * 1024 ** 3,
    use_angle_cls=False,
)
