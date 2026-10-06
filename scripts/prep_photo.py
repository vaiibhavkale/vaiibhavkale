"""
Turn the avatar into a zoomed line portrait for ASCII conversion.

The source is a dark illustrated poster. A brightness ramp turns the
hoodie into a solid blob, so this keeps a tight crop of the face and
draws only the contours: hair, glasses, beard, and the hand on the chin.
White pixels become blank glyphs later.

    python scripts/prep_photo.py source-photo.png
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
INP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-photo.png")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "source-prepped.png")

# Face, glasses, beard, and the hand-on-chin pose. Tuned for the 460px avatar.
DEFAULT_CROP = (152, 24, 322, 242)


def parse_crop(width, height):
    raw = os.environ.get("CROP", "")
    if raw:
        parts = [int(part) for part in raw.split(",")]
        if len(parts) != 4:
            raise SystemExit("CROP must be x0,y0,x1,y1")
        return tuple(parts)
    if (width, height) == (460, 460):
        return DEFAULT_CROP
    sx, sy = width / 460.0, height / 460.0
    x0, y0, x1, y1 = DEFAULT_CROP
    return int(x0 * sx), int(y0 * sy), int(x1 * sx), int(y1 * sy)


def skeleton(image):
    work = image.copy()
    skel = np.zeros(image.shape, np.uint8)
    element = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    while True:
        opened = cv2.morphologyEx(work, cv2.MORPH_OPEN, element)
        skel = cv2.bitwise_or(skel, cv2.subtract(work, opened))
        work = cv2.erode(work, element)
        if cv2.countNonZero(work) == 0:
            break
    return skel


def face_mask(crop):
    hsv = cv2.cvtColor(crop, cv2.COLOR_RGB2HSV)
    skin = cv2.inRange(hsv, (0, 35, 50), (28, 255, 255))
    skin = cv2.bitwise_or(skin, cv2.inRange(hsv, (165, 35, 50), (179, 255, 255)))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    skin = cv2.morphologyEx(skin, cv2.MORPH_CLOSE, kernel, iterations=3)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(skin, 8)
    if count < 2:
        return np.full(skin.shape, 255, np.uint8)
    largest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    mask = np.where(labels == largest, 255, 0).astype(np.uint8)
    return cv2.dilate(mask, kernel, iterations=6)


def main():
    image = Image.open(INP).convert("RGB")
    width, height = image.size
    x0, y0, x1, y1 = parse_crop(width, height)
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(width, x1), min(height, y1)
    crop = np.array(image.crop((x0, y0, x1, y1)))

    gray = cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY)
    smooth = cv2.bilateralFilter(gray, 7, 50, 50)
    smooth = cv2.bilateralFilter(smooth, 7, 40, 40)
    edges = cv2.bitwise_and(cv2.Canny(smooth, 45, 120), face_mask(crop))

    count, labels, stats, _ = cv2.connectedComponentsWithStats(edges, 8)
    kept = np.zeros_like(edges)
    for index in range(1, count):
        if stats[index, cv2.CC_STAT_AREA] >= 18:
            kept[labels == index] = 255
    kept = cv2.morphologyEx(kept, cv2.MORPH_CLOSE, np.ones((2, 2), np.uint8))
    thin = skeleton(kept)

    count, labels, stats, _ = cv2.connectedComponentsWithStats(thin, 8)
    img_h, img_w = thin.shape
    clean = np.zeros_like(thin)
    for index in range(1, count):
        box_x, box_y, box_w, box_h, area = stats[index]
        center_x = box_x + box_w / 2
        center_y = box_y + box_h / 2
        stray_sleeve = center_y > img_h * 0.82 and center_x < img_w * 0.35 and area < 180
        if not stray_sleeve:
            clean[labels == index] = 255

    ys, xs = np.where(clean > 0)
    if len(xs) == 0:
        raise SystemExit("no face contours found")
    margin = 8
    y0b = max(0, int(ys.min()) - margin)
    y1b = min(img_h, int(ys.max()) + margin + 1)
    x0b = max(0, int(xs.min()) - margin)
    x1b = min(img_w, int(xs.max()) + margin + 1)
    ink = clean[y0b:y1b, x0b:x1b]

    # Square canvas with a small margin so the face fills the terminal.
    side = int(max(ink.shape) * 1.12)
    canvas = np.full((side, side), 255, np.uint8)
    y_off = (side - ink.shape[0]) // 2
    x_off = (side - ink.shape[1]) // 2
    canvas[y_off:y_off + ink.shape[0], x_off:x_off + ink.shape[1]] = 255 - ink

    Image.fromarray(canvas, mode="L").save(OUT)
    print(f"wrote {OUT} {canvas.shape}")


if __name__ == "__main__":
    main()
