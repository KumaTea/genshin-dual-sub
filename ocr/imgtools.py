"""图像处理。

统一约定：本项目内部所有 ndarray 都是 **BGR**（OpenCV 约定），
dxcam 也按 BGR 初始化。这样 debug/ 下的 png 用 cv2.imread 读进来
就能直接当测试输入，不用再关心通道顺序。
"""

import cv2
import numpy as np


def to_gray(image: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def crop(image: np.ndarray, box: tuple[int, int, int, int]) -> np.ndarray:
    """按 (left, top, right, bottom) 裁切，坐标会被限制在图像范围内。"""
    height, width = image.shape[:2]
    left = max(0, min(int(box[0]), width))
    top = max(0, min(int(box[1]), height))
    right = max(left, min(int(box[2]), width))
    bottom = max(top, min(int(box[3]), height))
    return image[top:bottom, left:right]


def count_color(
        image: np.ndarray,
        rgb: tuple[int, int, int],
        tolerance: int = 3,
) -> int:
    """图中有多少像素接近给定颜色（入参是 RGB，图是 BGR）。"""
    red, green, blue = rgb
    lower = np.array([
        max(0, blue - tolerance),
        max(0, green - tolerance),
        max(0, red - tolerance),
    ], dtype=np.uint8)
    upper = np.array([
        min(255, blue + tolerance),
        min(255, green + tolerance),
        min(255, red + tolerance),
    ], dtype=np.uint8)
    return int(cv2.countNonZero(cv2.inRange(image, lower, upper)))


def has_color(
        image: np.ndarray,
        rgb: tuple[int, int, int],
        tolerance: int = 3,
        threshold: int = 127,
) -> bool:
    return count_color(image, rgb, tolerance) > threshold


def filter_white(image: np.ndarray) -> np.ndarray:
    """只保留接近白色的像素，其余涂黑。

    对话正文是白色，说话人名字是金色/青色，描边是深色。
    留白之后 OCR 只会看到正文，名字和背景都被抹掉了。
    """
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array([0, 0, 200]), np.array([179, 25, 255]))
    return cv2.bitwise_and(image, image, mask=mask)
