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

        self.load()

    def load(self):
        self.resolution = config['game']['resolution']


gi = GenshinInfo()

ppocr = PaddleOCR(
    lang='ch',
    use_angle_cls=False,
)
