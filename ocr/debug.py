import numpy as np
from ocr.ocr import *
from PIL import Image
from ocr.configs import *
from ocr.manager import *
from ocr.session import *
from ocr.wintools import *
from ocr.imgtools import *
from ocr.screenshot import *
from paddleocr import draw_ocr


def show(array: np.ndarray):
    return Image.fromarray(array).show()


def draw(image: np.ndarray, results: list) -> np.ndarray:
    if type(image) == Image:
        image = image.convert('RGB')
    else:
        image = Image.fromarray(image).convert('RGB')
    result = results[0]
    boxes = [line[0] for line in result]
    txts = [line[1][0] for line in result]
    scores = [line[1][1] for line in result]
    return draw_ocr(image, boxes, txts, scores)
