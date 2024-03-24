import time
import numpy as np
from ocr.session import gi
from typing import Optional
from ocr.screenshot import grab_screenshot


speaker_color = (255, 195, 0)


def take_screenshot() -> Optional[np.ndarray]:
    # make a screenshot handler
    # to avoid taking screenshots too frequently

    # now = time.time()
    if time.time() - gi.last_shot < 1:
        return gi.screenshot

    image = grab_screenshot(*gi.coords)
    if image is None or not image.any():
        return gi.screenshot

    gi.screenshot = image
    gi.last_shot = time.time()
    return image
