from ocr import *
import numpy as np
from PIL import Image
from configs import *
from manager import *
from session import *
from wintools import *
from screenshot import *
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
