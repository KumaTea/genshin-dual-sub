import time
import psutil
import numpy as np
from ocr.configs import dialog_area
from share.session import config, logging

try:
    from onnxocr.onnx_paddleocr import ONNXPaddleOcr as PaddleOCR
    use_paddle = False
    logging.info('Using OnnxOCR for OCR inference.')
except ImportError:
    import paddle
    from paddleocr import PaddleOCR
    use_paddle = True
    logging.info('Using PaddlePaddle for OCR inference.')


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

if use_paddle:
    use_gpu = paddle.device.is_compiled_with_cuda() and psutil.virtual_memory().total > 16 * 1024 ** 3
else:
    use_gpu = False

# the shape of the dialog box is extremely narrow
# we set the min height to avoid resizing the image
# which is the default behavior of PaddleOCR

dialog_height = dialog_area[gi.resolution][3] - dialog_area[gi.resolution][1]

ppocr = PaddleOCR(
    lang='ch',
    use_gpu=use_gpu,
    use_angle_cls=False,
    det_limit_side_len=dialog_height,
    det_limit_type='min'
)
