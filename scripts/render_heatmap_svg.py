#!/usr/bin/env python3
"""
Render data/contributions.json as GitHub's contribution graph:
heading, calendar, legend, and the year list.

    python scripts/render_heatmap_svg.py
"""
import datetime
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
IN_PATH = os.path.join(HERE, "..", "data", "contributions.json")
OUT_PATH = os.path.join(HERE, "..", "contrib-heatmap.svg")

# GitHub dark contribution ramp, level 0 through 4.
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]

CELL = 11
GAP = 3
STEP = CELL + GAP
LEFT_W = 32
TOP_H = 20
BOX_PAD_X = 10
BOX_PAD_Y = 8
HEAD_H = 32
YEAR_GAP = 14
YEAR_W = 58
FIRST_YEAR = 2020

BG = "#0d1117"
FRAME = "#3d444d"
MUTED = "#9198a1"
TEXT = "#e6edf3"
ACCENT = "#1f6feb"
FONT = '-apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif'


def build_grid(days):
    first = datetime.date.fromisoformat(days[0]["date"])
    lead = (first.weekday() + 1) % 7  # Sunday = 0
    grid = []
    column = [None] * lead
    for day in days:
        date = datetime.date.fromisoformat(day["date"])
        weekday = (date.weekday() + 1) % 7
        while len(column) < weekday:
            column.append(None)
        level = max(0, min(len(PALETTE) - 1, int(day["level"])))
        column.append((day["date"], day["count"], level))
        if len(column) == 7:
            grid.append(column)
            column = []
    if column:
        while len(column) < 7:
            column.append(None)
        grid.append(column)
    return grid


def month_labels(grid):
    labels = []
    seen = set()
    last_col = len(grid) - 1
    for index, column in enumerate(grid):
        for cell in column:
            if cell is None:
                continue
            date = datetime.date.fromisoformat(cell[0])
            key = (date.year, date.month)
            if key not in seen and date.day <= 7:
                too_close = labels and index - labels[-1][0] < 3
                too_late = last_col - index < 2
                seen.add(key)
                if not too_close and not too_late:
                    labels.append((index, date.strftime("%b")))
            break
    return labels


def render(data):
    grid = build_grid(data["days"])
    n_cols = len(grid)
    grid_w = n_cols * STEP
    grid_h = 7 * STEP
    box_w = BOX_PAD_X + LEFT_W + grid_w + BOX_PAD_X
    footer_h = 26
    box_h = BOX_PAD_Y + TOP_H + grid_h + footer_h + BOX_PAD_Y
    canvas_w = box_w + YEAR_GAP + YEAR_W
    canvas_h = HEAD_H + box_h

    end_year = datetime.date.fromisoformat(data["range"]["end"]).year
    years = list(range(end_year, FIRST_YEAR - 1, -1))
    total = data["total_contributions"]
    font = f'font-family="{FONT}"'

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="{canvas_h}" '
        f'viewBox="0 0 {canvas_w} {canvas_h}" role="img" '
        f'aria-label="{total:,} contributions in the last year">',
        f'<rect width="{canvas_w}" height="{canvas_h}" fill="{BG}"/>',
        f'<text x="2" y="20" fill="{TEXT}" {font} font-size="16" font-weight="400">'
        f'{total:,} contributions in the last year</text>',
    ]

    year_x = box_w + YEAR_GAP
    for index, year in enumerate(years):
        y = 4 + index * 22
        if year == end_year:
            parts.append(
                f'<rect x="{year_x}" y="{y}" width="{YEAR_W}" height="26" rx="6" fill="{ACCENT}"/>'
                f'<text x="{year_x + YEAR_W / 2}" y="{y + 18}" fill="#ffffff" {font} '
                f'font-size="14" font-weight="600" text-anchor="middle">{year}</text>'
            )
        else:
            parts.append(
                f'<text x="{year_x + YEAR_W / 2}" y="{y + 18}" fill="{MUTED}" {font} '
                f'font-size="14" text-anchor="middle">{year}</text>'
            )

    box_y = HEAD_H
    parts.append(
        f'<rect x="0.5" y="{box_y + 0.5}" width="{box_w - 1}" height="{box_h - 1}" rx="6" '
        f'fill="{BG}" stroke="{FRAME}"/>'
    )

    grid_left = BOX_PAD_X + LEFT_W
    grid_top = box_y + BOX_PAD_Y + TOP_H
    for col_index, label in month_labels(grid):
        x = grid_left + col_index * STEP
        parts.append(
            f'<text x="{x}" y="{box_y + BOX_PAD_Y + 12}" fill="{MUTED}" {font} font-size="12">{label}</text>'
        )

    for row_index, name in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        y = grid_top + row_index * STEP + CELL - 1
        parts.append(
            f'<text x="{BOX_PAD_X}" y="{y}" fill="{MUTED}" {font} font-size="11">{name}</text>'
        )

    for col_index, column in enumerate(grid):
        x = grid_left + col_index * STEP
        for row_index, cell in enumerate(column):
            if cell is None:
                continue
            date_s, count, level = cell
            y = grid_top + row_index * STEP
            word = "contribution" if count == 1 else "contributions"
            parts.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{PALETTE[level]}">'
                f'<title>{count} {word} on {date_s}</title></rect>'
            )

    footer_y = grid_top + grid_h + 18
    parts.append(
        f'<text x="{BOX_PAD_X + 2}" y="{footer_y}" fill="{MUTED}" {font} font-size="12">'
        f'Learn how we count contributions</text>'
    )

    legend_count = len(PALETTE)
    legend_w = 28 + legend_count * (CELL + 3) + 36
    legend_x = box_w - BOX_PAD_X - legend_w
    parts.append(
        f'<text x="{legend_x}" y="{footer_y}" fill="{MUTED}" {font} font-size="12">Less</text>'
    )
    swatch_x = legend_x + 36
    for level, color in enumerate(PALETTE):
        parts.append(
            f'<rect x="{swatch_x + level * (CELL + 3)}" y="{footer_y - 10}" '
            f'width="{CELL}" height="{CELL}" rx="2" fill="{color}"/>'
        )
    more_x = swatch_x + legend_count * (CELL + 3) + 4
    parts.append(
        f'<text x="{more_x}" y="{footer_y}" fill="{MUTED}" {font} font-size="12">More</text>'
    )
    parts.append("</svg>")
    return "".join(parts)


def main():
    with open(IN_PATH, encoding="utf-8") as handle:
        data = json.load(handle)
    svg = render(data)
    with open(OUT_PATH, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(svg)
    print(f"wrote {OUT_PATH} ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
