import cv2
import numpy as np


def to_gray(image: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def to_binary(image: np.ndarray, threshold: int = 127) -> np.ndarray:
    _, binary = cv2.threshold(image, threshold, 255, cv2.THRESH_BINARY)
    return binary


def set_gamma(image: np.ndarray, gamma: float = 1.0) -> np.ndarray:
    table = np.array([((i / 255.0) ** (1.0 / gamma)) * 255 for i in np.arange(0, 256)]).astype("uint8")
    return cv2.LUT(image, table)


def has_color(
        image: np.ndarray,
        # color: tuple[int, int, int] = (255, 195, 0),
        color: tuple[int, int, int] = None,
        # color_str: str = 'ffc300',
        color_str: str = None,
        threshold: int = 127
) -> bool:
    # return True if the color exists in the image
    color = color or tuple(int(color_str[i:i + 2], 16) for i in (0, 2, 4))
    mask = cv2.inRange(image, color, color)
    return cv2.countNonZero(mask) > threshold
