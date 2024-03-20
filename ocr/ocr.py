import logging
import numpy as np
from ocr.configs import paddings
from ocr.session import gi, ppocr
from ocr.wintools import crop_image


# max_right = dialog_area[config['game']['resolution']][2]
# max_left = dialog_area[config['game']['resolution']][0]


def is_same_line(box1: list, box2: list, img_size: tuple, threshold: float = 0.02):
    # box1 = [[26.0, 635.0], [810.0, 635.0], [810.0, 657.0], [26.0, 657.0]]
    # box2 = [[836.0, 636.0], [863.0, 636.0], [863.0, 655.0], [836.0, 655.0]]
    # img_size = [1920, 1080]

    # image_width = img_size[0]
    # box1_right = (box1[1][0] + box1[2][0]) / 2
    # box2_left = (box2[0][0] + box2[3][0]) / 2
    # judge_0 = box1_right - box2_left > threshold * 5 * image_width
    # if judge_0:  # 框1右边界 > 框2左边界 ==> 框1在框2右边
    #     return False

    image_height = img_size[1]
    box1_y1 = (box1[0][1] + box1[1][1]) / 2  # 635
    box1_y2 = (box1[2][1] + box1[3][1]) / 2  # 657
    box2_y1 = (box2[0][1] + box2[1][1]) / 2  # 636
    box2_y2 = (box2[2][1] + box2[3][1]) / 2  # 655
    # box1_height = box1_y2 - box1_y1  # 22
    # box2_height = box2_y2 - box2_y1  # 19
    judge_1 = abs(box1_y1 - box2_y1) < threshold * image_height  # 1 < 0.02 * 1080 ==> True
    judge_2 = abs(box1_y2 - box2_y2) < threshold * image_height  # 2 < 0.02 * 1080 ==> True
    # judge_3 = abs(box1_height - box2_height) < threshold * image_height  # 3 < 0.02 * 1080 ==> True
    return judge_1 and judge_2  # and judge_3


def get_textbox(
        image: np.ndarray
) -> list[  # boxes
        list[  # box
            list[  # coord
                float, float  # x, y
            ]
        ]
]:
    results = ppocr.ocr(image, det=True, rec=False, cls=False)
    boxes = results[0]
    # [[[90.0, 9.0], [405.0, 9.0], [405.0, 36.0], [90.0, 36.0]], [[1210.0, 9.0], [1556.0, 9.0], [1556.0, 36.0], [1210.0, 36.0]]]
    if not boxes:
        return []
    if len(boxes) < 2:
        return boxes

    # paddleocr cannot detect long textbox
    # so if we find two boxes are on the same line
    # then we combine them
    # by take the leftmost box's left and the rightmost box's right

    new_boxes = []
    last_box = None
    for box in boxes:
        # [[90.0, 9.0], [405.0, 9.0], [405.0, 36.0], [90.0, 36.0]]
        if last_box:
            if is_same_line(last_box, box, image.shape[:2]):
                leftmost = [
                    min(last_box[0][0], box[0][0]),
                    min(last_box[0][1], box[0][1]),
                ]
                rightmost = [
                    max(last_box[1][0], box[1][0]),
                    max(last_box[2][1], box[2][1]),
                ]
                last_box = [
                    leftmost,
                    [rightmost[0], leftmost[1]],
                    rightmost,
                    [leftmost[0], rightmost[1]],
                ]
            else:
                new_boxes.append(last_box)
                last_box = box
        else:
            last_box = box
    if last_box:
        new_boxes.append(last_box)

    # sort by y
    new_boxes.sort(key=lambda x: x[0][1])

    return new_boxes


def cut_long_textbox(box: list[list[float, float]], threshold: int = 320, max_padding: int = 20) -> list[list[list[float, float]]]:
    # paddleocr cannot detect long textbox
    # maximum width is 320

    # [[19.0, 12.0], [1556.0, 12.0], [1556.0, 42.0], [19.0, 42.0]]
    left = box[0][0]
    top = box[0][1]
    right = box[2][0]
    bottom = box[2][1]
    width = right - left
    cut_into = int(width // threshold + 1)
    if cut_into == 1:
        return [box]

    cut_size = int(width // cut_into + 1)
    # (2 * padding + cut_size) cannot exceed threshold
    padding = min([max_padding, (threshold - cut_size) // 2])

    cut_boxes = []
    for i in range(cut_into):
        box_left = max([left, left + i * cut_size - padding])
        box_right = min([right, box_left + cut_size + padding])
        cut_boxes.append([
            [box_left, top],
            [box_right, top],
            [box_right, bottom],
            [box_left, bottom],
        ])
    return cut_boxes


def textbox_at_center(box: list[list[float, float]], image_size: tuple[int, int], tolerance: int = 0.05) -> bool:
    # box = [[19.0, 12.0], [1556.0, 12.0], [1556.0, 42.0], [19.0, 42.0]]
    # image_size = [1920, 1080]
    center_x = (box[0][0] + box[1][0]) / 2
    # center_y = (box[0][1] + box[2][1]) / 2
    image_width = image_size[1]
    # image_height = image_size[0]
    at_center = abs(center_x - image_width / 2) < tolerance * image_width
    if not at_center:
        logging.warning(f'[OCR]\t对话框不在中央: x={center_x}, w={image_width}, r={abs(center_x - image_width / 2) / image_width:.2f}')
    return at_center


def combine_text_core(text1: str, text2: str) -> str:
    comp1 = text1[-3:]
    comp2 = text2[:3]
    unique = set(comp1 + comp2)

    if len(unique) == len(comp1) + len(comp2):
        return text1 + text2

    dup = set(comp1) & set(comp2)
    # first_dup = any(i for i in comp2 if i in dup)
    for i in comp2:
        if i in dup:
            first_dup = i
            break
    try:
        idx1 = text1.rfind(first_dup)
        idx2 = text2.find(first_dup)
        return text1[:idx1] + text2[idx2:]
    except UnboundLocalError:
        return text1 + text2


def combine_texts(rec_results: list[list[tuple[str, float]]], boxes: list[list[list[float, float]]], image: np.ndarray) -> str:
    # text = ''
    # for result in results:
    #     content, prob = result[0]
    #     if text and text[-1] == content[0]:
    #         # because of padding
    #         content = content[1:]
    #     text += content
    text = ''
    pairs = zip(rec_results, boxes)
    last_box = None
    for result, box in pairs:
        content, prob = result[0]
        if last_box:
            if is_same_line(last_box, box, image.shape[:2]):
                text = combine_text_core(text, content)
                last_box = box
            else:
                text += content
        else:
            text += content
            last_box = box
    return text


def do_ocr_raw(image: np.ndarray) -> str:
    results = ppocr.ocr(image, rec=True, det=False, cls=False)
    result = results[0]
    if not result:
        return ''
    text = result[0][0]
    return text


def do_ocr(image: np.ndarray) -> str:
    # scale image
    # scale = scales[gi.resolution]
    # image = cv2.resize(
    #     image,
    #     (0, 0),
    #     fx=scale,
    #     fy=scale,
    #     interpolation=cv2.INTER_CUBIC
    # )

    # DO NOT SCALE
    # WORSE PERFORMANCE

    text_boxes = get_textbox(image)
    if not text_boxes:
        return ''

    done_print = textbox_at_center(text_boxes[0], image.shape[:2])
    if not done_print:
        logging.warning(f'[OCR]\t因为识别对话框未居中，我猜字还没出全')
        return ''

    new_boxes = []
    for box in text_boxes:
        new_boxes.extend(
            cut_long_textbox(
                box,
                # max_padding=int(paddings[gi.resolution] / scales[gi.resolution])
                max_padding=paddings[gi.resolution]
            )
        )

    images = []
    for box in new_boxes:
        images.append(crop_image(image, (
            int(box[0][0]),
            int(box[0][1]),
            int(box[2][0]),
            int(box[2][1]),
        )))

    # results = ppocr.ocr(
    #     images,
    #     rec=True,
    #     # det_max_side_len=max_right - max_left,
    #     det=False,
    #     # det: use text detection or not. If False, only rec will be exec.
    #     cls=False,
    #     # cls: use angle classifier or not. Default is True.
    #     # If True, the text with rotation of 180 degrees can be recognized.
    #     # If no text is rotated by 180 degrees, use cls=False to get better performance.
    #     # max_text_length=100,
    # )

    results = [
        # do this to ensure every piece of cropped image is processed
        ppocr.ocr(
            image,
            rec=True,
            det=False,
            cls=False,
        )[0]
        for image in images
    ]

    # for result in results:
    # result = results[0]
    if not results[0]:
        # continue
        return ''

    text = combine_texts(results, new_boxes, image)
    return text
