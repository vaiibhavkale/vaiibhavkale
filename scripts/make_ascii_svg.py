"""
Turn a prepped grayscale portrait into a monochrome ASCII SVG that types
itself once, row by row, then holds.

GitHub strips script tags from READMEs but plays SMIL inside an SVG
loaded with an img tag. Each row is a left-to-right clip wipe with a
block cursor on the leading edge.

    python scripts/make_ascii_svg.py
    STATIC=1 python scripts/make_ascii_svg.py   # frozen frame for previews
"""
import html
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-prepped.png")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "vaibhav-ascii.svg")

COLS = int(os.environ.get("COLS", "118"))
ART_W_TARGET = 760
CELL_W = ART_W_TARGET / COLS
CELL_H = CELL_W * 15 / 8
ROWS = round(COLS * 8 / 15)

PAD = 18
TITLEBAR_H = 32
STATUS_H = 32
ART_W = COLS * CELL_W
ART_H = ROWS * CELL_H
CANVAS_W = int(round(ART_W + PAD * 2))
CANVAS_H = int(round(TITLEBAR_H + ART_H + STATUS_H + 8))

BG = "#0d1117"
BG2 = "#161b22"
FRAME = "#30363d"
TITLE_TEXT = "#7d8590"
INK = "#c9d1d9"
CURSOR = "#c9d1d9"
GREEN = "#3fb950"

ROW_DUR = 5.6 / ROWS
STAGGER = ROW_DUR
STATIC = bool(os.environ.get("STATIC"))

PROMPT = "vaibhav@github"
WHOAMI = "Vaibhav Kale"


def sample_rows(path):
    """Sample the line portrait by cell. Any dark pixel becomes one stroke glyph."""
    image = np.array(Image.open(path).convert("L"))
    height, width = image.shape
    rows = []
    for y in range(ROWS):
        y0 = int(y * height / ROWS)
        y1 = max(y0 + 1, int((y + 1) * height / ROWS))
        chars = []
        for x in range(COLS):
            x0 = int(x * width / COLS)
            x1 = max(x0 + 1, int((x + 1) * width / COLS))
            patch = image[y0:y1, x0:x1]
            if patch.size == 0 or int(patch.min()) > 200:
                chars.append(" ")
                continue
            coverage = float(np.mean(patch < 128))
            chars.append("#" if coverage > 0.22 else "*")
        rows.append("".join(chars))
    return rows


def text_el(x, y, body, size, fill, extra=""):
    return (
        f'<text x="{x:.2f}" y="{y:.2f}" fill="{fill}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" '
        f'font-size="{size:.2f}" xml:space="preserve"{extra}>{body}</text>'
    )


def build(rows):
    font_size = CELL_H * 0.86
    art_top = TITLEBAR_H + 6
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{CANVAS_H}" '
        f'viewBox="0 0 {CANVAS_W} {CANVAS_H}" role="img" aria-label="ASCII portrait of Vaibhav Kale">',
        f'<rect width="{CANVAS_W}" height="{CANVAS_H}" rx="12" fill="{BG}" stroke="{FRAME}"/>',
        f'<rect width="{CANVAS_W}" height="{TITLEBAR_H}" rx="12" fill="{BG2}"/>',
        f'<rect y="{TITLEBAR_H - 12}" width="{CANVAS_W}" height="12" fill="{BG2}"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{CANVAS_W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
    ]
    for i, color in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{16 + i * 16}" cy="16" r="5" fill="{color}"/>')
    parts.append(text_el(78, 21, f"{PROMPT}: ~$ ./portrait.sh", 13, TITLE_TEXT))

    for ry, line in enumerate(rows):
        y = art_top + ry * CELL_H + CELL_H * 0.78
        row_y = art_top + ry * CELL_H
        delay = ry * STAGGER
        safe = html.escape(line)
        glyph = text_el(
            PAD,
            y,
            safe,
            font_size,
            INK,
            extra=f' textLength="{ART_W:.2f}" lengthAdjust="spacingAndGlyphs"',
        )
        if STATIC:
            parts.append(glyph)
            continue
        clip_id = f"row{ry}"
        parts.append(
            f'<clipPath id="{clip_id}">'
            f'<rect x="{PAD:.2f}" y="{row_y:.2f}" height="{CELL_H:.2f}" width="0">'
            f'<animate attributeName="width" from="0" to="{ART_W:.2f}" '
            f'dur="{ROW_DUR:.3f}s" begin="{delay:.3f}s" fill="freeze"/>'
            f'</rect></clipPath>'
        )
        parts.append(f'<g clip-path="url(#{clip_id})">{glyph}</g>')
        cursor_h = CELL_H * 0.72
        cursor_w = max(CELL_W * 0.65, 4)
        cursor_y = row_y + (CELL_H - cursor_h) / 2
        hide_at = delay + ROW_DUR
        parts.append(
            f'<rect x="{PAD:.2f}" y="{cursor_y:.2f}" width="{cursor_w:.2f}" height="{cursor_h:.2f}" '
            f'fill="{CURSOR}" opacity="0">'
            f'<animate attributeName="x" from="{PAD:.2f}" to="{PAD + ART_W - cursor_w:.2f}" '
            f'dur="{ROW_DUR:.3f}s" begin="{delay:.3f}s" fill="freeze"/>'
            f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.04;0.9;1" '
            f'dur="{ROW_DUR:.3f}s" begin="{delay:.3f}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0" begin="{hide_at:.3f}s" fill="freeze"/>'
            f'</rect>'
        )

    status_y = TITLEBAR_H + 6 + ART_H + 22
    status = f"{PROMPT}:~$ whoami  {WHOAMI}"
    parts.append(text_el(PAD, status_y, status, 13, TITLE_TEXT))
    cursor_x = PAD + len(status) * 7.6
    blink_begin = ROWS * STAGGER + 0.2
    parts.append(
        f'<rect x="{cursor_x:.2f}" y="{status_y - 12}" width="8" height="14" fill="{GREEN}">'
        f'<animate attributeName="opacity" values="1;0;1" dur="1.1s" '
        f'begin="{blink_begin:.3f}s" repeatCount="indefinite"/>'
        f'</rect>'
    )
    parts.append("</svg>")
    return "".join(parts)


def main():
    rows = sample_rows(SRC)
    svg = build(rows)
    with open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(svg)
    print(f"wrote {OUT} {len(svg)} bytes; {CANVAS_W}x{CANVAS_H}")


if __name__ == "__main__":
    main()
