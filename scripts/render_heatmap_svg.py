#!/usr/bin/env python3
"""
Render data/contributions.json as a terminal-window contribution heatmap.

Rounded cells reveal once on a diagonal cascade (CSS keyframes inside the
SVG). A legend and stats footer use the scraped totals. Matches the layout
from the animated profile README blog post.

    python scripts/render_heatmap_svg.py
"""
import datetime
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
IN_PATH = os.path.join(HERE, "..", "data", "contributions.json")
OUT_PATH = os.path.join(HERE, "..", "contrib-heatmap.svg")

# GitHub-ish green ramp. Level 5 is a brighter neon top end.
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

CELL = 12
GAP = 3
STEP = CELL + GAP
PAD = 22
LEFT_LABEL_W = 30
TOP_LABEL_H = 20
TITLEBAR_H = 30

BG = "#0d1117"
BG2 = "#161b22"
FRAME = "#30363d"
MUTED = "#7d8590"
TEXT = "#e6edf3"
GREEN = "#3fb950"
FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

COL_T = 0.018
ROW_T = 0.045
CELL_DUR = 0.42

PROMPT = "vaibhav@github: ~/contributions --graph"


def level_for(count):
    if count == 0:
        return 0
    if count <= 5:
        return 1
    if count <= 15:
        return 2
    if count <= 30:
        return 3
    if count <= 50:
        return 4
    return 5


def build_grid(days):
    first = datetime.date.fromisoformat(days[0]["date"])
    lead_pad = (first.weekday() + 1) % 7
    grid = []
    column = [None] * lead_pad
    for day in days:
        date = datetime.date.fromisoformat(day["date"])
        weekday = (date.weekday() + 1) % 7
        while len(column) < weekday:
            column.append(None)
        level = level_for(day["count"])
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
    for col_index, column in enumerate(grid):
        for cell in column:
            if cell is None:
                continue
            date = datetime.date.fromisoformat(cell[0])
            key = (date.year, date.month)
            if key not in seen and date.day <= 7:
                too_close = labels and col_index - labels[-1][0] < 3
                too_late = last_col - col_index < 2
                seen.add(key)
                if not too_close and not too_late:
                    labels.append((col_index, date.strftime("%b")))
            break
    return labels


def render(data):
    grid = build_grid(data["days"])
    n_cols = len(grid)
    art_w = n_cols * STEP
    art_h = 7 * STEP
    canvas_w = PAD + LEFT_LABEL_W + art_w + PAD
    stats_h = 88
    canvas_h = TITLEBAR_H + TOP_LABEL_H + art_h + stats_h + PAD

    font = f'font-family="{FONT}"'
    css = (
        "@keyframes cell { from { opacity: 0; transform: translateY(-6px); } "
        f"to {{ opacity: 1; transform: translateY(0); }} }}"
        f".c {{ opacity: 0; animation: cell {CELL_DUR:.2f}s cubic-bezier(.2,.8,.2,1) both; }}"
        "@media (prefers-reduced-motion: reduce) { .c { opacity: 1; animation: none; } }"
    )

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="{canvas_h}" '
        f'viewBox="0 0 {canvas_w} {canvas_h}" role="img" '
        f'aria-label="GitHub contribution graph">',
        f"<style>{css}</style>",
        f'<rect width="{canvas_w}" height="{canvas_h}" rx="12" fill="{BG}" stroke="{FRAME}"/>',
        f'<rect width="{canvas_w}" height="{TITLEBAR_H}" rx="12" fill="{BG2}"/>',
        f'<rect y="{TITLEBAR_H - 12}" width="{canvas_w}" height="12" fill="{BG2}"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{canvas_w}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
    ]
    for index, color in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{16 + index * 16}" cy="16" r="5" fill="{color}"/>')
    parts.append(
        f'<text x="78" y="21" fill="{MUTED}" {font} font-size="13">{PROMPT}</text>'
    )

    grid_top = TITLEBAR_H + TOP_LABEL_H
    grid_left = PAD + LEFT_LABEL_W

    for col_index, label in month_labels(grid):
        x = grid_left + col_index * STEP
        parts.append(
            f'<text x="{x}" y="{TITLEBAR_H + 14}" fill="{MUTED}" {font} font-size="11">{label}</text>'
        )

    for row_index, name in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        y = grid_top + row_index * STEP + CELL * 0.78
        parts.append(f'<text x="{PAD}" y="{y:.1f}" fill="{MUTED}" {font} font-size="10">{name}</text>')

    for col_index, column in enumerate(grid):
        x = grid_left + col_index * STEP
        for row_index, cell in enumerate(column):
            if cell is None:
                continue
            date_s, count, level = cell
            y = grid_top + row_index * STEP
            delay = col_index * COL_T + row_index * ROW_T
            word = "contribution" if count == 1 else "contributions"
            parts.append(
                f'<rect class="c" style="animation-delay:{delay:.3f}s" '
                f'x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" '
                f'fill="{PALETTE[level]}">'
                f'<title>{date_s}: {count} {word}</title></rect>'
            )

    leg_y = grid_top + art_h + 6
    leg_x = canvas_w - PAD - (len(PALETTE) * (CELL + 3) + 70)
    parts.append(f'<text x="{leg_x}" y="{leg_y + 10}" fill="{MUTED}" {font} font-size="11">Less</text>')
    swatch_x = leg_x + 36
    for level, color in enumerate(PALETTE):
        parts.append(
            f'<rect x="{swatch_x + level * (CELL + 3)}" y="{leg_y}" '
            f'width="{CELL}" height="{CELL}" rx="2" fill="{color}"/>'
        )
    parts.append(
        f'<text x="{swatch_x + len(PALETTE) * (CELL + 3) + 4}" y="{leg_y + 10}" '
        f'fill="{MUTED}" {font} font-size="11">More</text>'
    )

    sep_y = leg_y + CELL + 14
    parts.append(f'<line x1="{PAD}" y1="{sep_y}" x2="{canvas_w - PAD}" y2="{sep_y}" stroke="{FRAME}"/>')

    current = data["current_streak"]["length"]
    longest = data["longest_streak"]["length"]
    total = data["total_contributions"]
    best = data["best_day"]
    span = data["range"]
    line_y = sep_y + 24
    parts.append(
        f'<text x="{PAD}" y="{line_y}" {font} font-size="14">'
        f'<tspan fill="{GREEN}" font-weight="700">{total:,}</tspan>'
        f'<tspan fill="{TEXT}"> contributions in the last year</tspan></text>'
    )
    parts.append(
        f'<text x="{canvas_w - PAD}" y="{line_y}" fill="{MUTED}" {font} font-size="12" text-anchor="end">'
        f'{span["start"]} to {span["end"]}</text>'
    )
    line_y += 24
    parts.append(
        f'<text x="{PAD}" y="{line_y}" {font} font-size="13">'
        f'<tspan fill="{MUTED}">current streak </tspan>'
        f'<tspan fill="{GREEN}" font-weight="700">{current} days</tspan>'
        f'<tspan fill="{MUTED}">   ·   longest </tspan>'
        f'<tspan fill="{TEXT}" font-weight="700">{longest} days</tspan>'
        f'<tspan fill="{MUTED}">   ·   best day </tspan>'
        f'<tspan fill="{TEXT}">{best["count"]} on {best["date"]}</tspan>'
        f"</text>"
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
