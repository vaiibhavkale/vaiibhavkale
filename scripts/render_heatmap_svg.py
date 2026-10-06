#!/usr/bin/env python3
"""
Render data/contributions.json as the flat contribution graph used on the
animated profile README: months, day labels, green cells that pop in once,
and the yearly total underneath. No year list and no terminal frame.

    python scripts/render_heatmap_svg.py
"""
import datetime
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
IN_PATH = os.path.join(HERE, "..", "data", "contributions.json")
OUT_PATH = os.path.join(HERE, "..", "contrib-heatmap.svg")

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]

CELL = 13
GAP = 3
STEP = CELL + GAP
LEFT = 34
TOP = 24
CANVAS_H = 158
FONT = "-apple-system, Segoe UI, Helvetica, Arial, sans-serif"


def build_grid(days):
    first = datetime.date.fromisoformat(days[0]["date"])
    lead = (first.weekday() + 1) % 7
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
    canvas_w = LEFT + len(grid) * STEP + 6
    total = data["total_contributions"]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="{CANVAS_H}" '
        f'viewBox="0 0 {canvas_w} {CANVAS_H}" font-family="{FONT}" role="img" '
        f'aria-label="{total:,} contributions in the last year">',
        "<style>",
        "text.lbl { fill: #7d8590; font-size: 13px; font-weight: 600; }",
        "text.total { fill: #e6edf3; font-size: 15px; font-weight: 700; }",
        ".c { transform-box: fill-box; transform-origin: center; opacity: 0; animation: pop 0.55s ease-out both; }",
        ".g { animation: pop 0.55s ease-out both, flash 0.7s ease-out both; }",
        "@keyframes pop { 0% { opacity: 0; transform: scale(0.2); } 60% { opacity: 1; transform: scale(1.1); } 100% { opacity: 1; transform: scale(1); } }",
        "@keyframes flash { 0% { filter: brightness(2.4); } 45% { filter: brightness(2.4); } 100% { filter: brightness(1); } }",
        "@media (prefers-reduced-motion: reduce) { .c, .g { opacity: 1; animation: none; } }",
        "</style>",
        f'<rect width="{canvas_w}" height="{CANVAS_H}" fill="none"/>',
    ]

    for col_index, label in month_labels(grid):
        x = LEFT + col_index * STEP
        parts.append(f'<text class="lbl" x="{x}" y="16">{label}</text>')

    for row_index, name in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        y = TOP + row_index * STEP + 11
        parts.append(f'<text class="lbl" x="2" y="{y}">{name}</text>')

    for col_index, column in enumerate(grid):
        x = LEFT + col_index * STEP
        for row_index, cell in enumerate(column):
            if cell is None:
                continue
            date_s, count, level = cell
            y = TOP + row_index * STEP
            delay = (col_index * 7 + row_index) * 0.004
            klass = "c g" if level >= 4 else "c"
            word = "contribution" if count == 1 else "contributions"
            parts.append(
                f'<rect class="{klass}" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" '
                f'fill="{PALETTE[level]}" style="animation-delay:{delay:.3f}s">'
                f"<title>{count} {word} on {date_s}</title></rect>"
            )

    parts.append(
        f'<text class="total" x="{LEFT}" y="152">{total:,} contributions in the last year</text>'
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
