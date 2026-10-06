#!/usr/bin/env python3
"""
Render data/contributions.json as a GitHub-style heatmap SVG.

Boxes reveal once on a diagonal, then hold. A legend and a stats footer
use the scraped totals.

    python scripts/render_heatmap_svg.py
"""
import datetime
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
IN_PATH = os.path.join(HERE, "..", "data", "contributions.json")
OUT_PATH = os.path.join(HERE, "..", "contrib-heatmap.svg")

# GitHub dark green ramp. data-level is 0..4.
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]

CELL = 11
GAP = 3
STEP = CELL + GAP
PAD = 18
LEFT_LABEL_W = 32
TOP_LABEL_H = 18
TITLEBAR_H = 32

BG = "#0d1117"
BG2 = "#161b22"
FRAME = "#30363d"
MUTED = "#7d8590"
TEXT = "#e6edf3"
GREEN = "#3fb950"

COL_T = 0.016
ROW_T = 0.04
CELL_DUR = 0.4


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
    for index, column in enumerate(grid):
        for cell in column:
            if cell is None:
                continue
            date = datetime.date.fromisoformat(cell[0])
            key = (date.year, date.month)
            if key not in seen and date.day <= 7:
                seen.add(key)
                labels.append((index, date.strftime("%b")))
            break
    return labels


def render(data):
    grid = build_grid(data["days"])
    n_cols = len(grid)
    art_w = n_cols * STEP
    art_h = 7 * STEP
    canvas_w = PAD + LEFT_LABEL_W + art_w + PAD
    stats_h = 78
    canvas_h = TITLEBAR_H + TOP_LABEL_H + art_h + stats_h + PAD

    font = 'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"'
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="{canvas_h}" '
        f'viewBox="0 0 {canvas_w} {canvas_h}" role="img" '
        f'aria-label="GitHub contributions in the last year">',
        "<style>",
        "@keyframes cell { from { opacity: 0; transform: translateY(-6px); } to { opacity: 1; transform: translateY(0); } }",
        f".c {{ opacity: 0; animation: cell {CELL_DUR:.2f}s cubic-bezier(.2,.8,.2,1) both; }}",
        "@media (prefers-reduced-motion: reduce) { .c { opacity: 1; animation: none; } }",
        "</style>",
        f'<rect width="{canvas_w}" height="{canvas_h}" rx="12" fill="{BG}" stroke="{FRAME}"/>',
        f'<rect width="{canvas_w}" height="{TITLEBAR_H}" rx="12" fill="{BG2}"/>',
        f'<rect y="{TITLEBAR_H - 12}" width="{canvas_w}" height="12" fill="{BG2}"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{canvas_w}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
    ]
    for i, color in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{16 + i * 16}" cy="16" r="5" fill="{color}"/>')
    parts.append(
        f'<text x="78" y="21" fill="{MUTED}" {font} font-size="13">'
        f'vaibhav@github: ~/contributions --graph</text>'
    )

    grid_top = TITLEBAR_H + TOP_LABEL_H
    grid_left = PAD + LEFT_LABEL_W

    for col_index, label in month_labels(grid):
        x = grid_left + col_index * STEP
        parts.append(
            f'<text x="{x}" y="{TITLEBAR_H + 14}" fill="{MUTED}" {font} font-size="11">{label}</text>'
        )

    for row_index, name in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        y = grid_top + row_index * STEP + CELL * 0.82
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
                f'x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{PALETTE[level]}">'
                f'<title>{date_s}: {count} {word}</title></rect>'
            )

    legend_y = grid_top + art_h + 8
    legend_x = canvas_w - PAD - (len(PALETTE) * (CELL + 3) + 78)
    parts.append(f'<text x="{legend_x}" y="{legend_y + 10}" fill="{MUTED}" {font} font-size="11">Less</text>')
    box_x = legend_x + 36
    for level, color in enumerate(PALETTE):
        parts.append(
            f'<rect x="{box_x + level * (CELL + 3)}" y="{legend_y}" width="{CELL}" height="{CELL}" rx="2" fill="{color}"/>'
        )
    more_x = box_x + len(PALETTE) * (CELL + 3) + 4
    parts.append(f'<text x="{more_x}" y="{legend_y + 10}" fill="{MUTED}" {font} font-size="11">More</text>')

    sep_y = legend_y + CELL + 12
    parts.append(f'<line x1="{PAD}" y1="{sep_y}" x2="{canvas_w - PAD}" y2="{sep_y}" stroke="{FRAME}"/>')

    total = data["total_contributions"]
    current = data["current_streak"]["length"]
    longest = data["longest_streak"]["length"]
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
    line_y += 22
    parts.append(
        f'<text x="{PAD}" y="{line_y}" {font} font-size="13">'
        f'<tspan fill="{MUTED}">current streak </tspan>'
        f'<tspan fill="{GREEN}" font-weight="700">{current} days</tspan>'
        f'<tspan fill="{MUTED}">   ·   longest </tspan>'
        f'<tspan fill="{TEXT}" font-weight="700">{longest} days</tspan>'
        f'<tspan fill="{MUTED}">   ·   best day </tspan>'
        f'<tspan fill="{TEXT}">{best["count"]} on {best["date"]}</tspan>'
        f'</text>'
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
