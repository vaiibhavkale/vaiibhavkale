#!/usr/bin/env python3
"""
Render the streak and numbers card beside the ASCII portrait.

Six tiles count up, then a monthly bar chart grows in. The canvas matches
vaibhav-ascii.svg so the two panels line up at the same display width.

    python scripts/render_stats_svg.py
"""
import datetime
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data", "contributions.json")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "stats.svg")
ASCII_SVG = os.path.join(ROOT, "vaibhav-ascii.svg")

BG = "#0d1117"
BG2 = "#161b22"
TILE = "#161b22"
FRAME = "#30363d"
MUTED = "#7d8590"
INK = "#e6edf3"
GREEN = "#3fb950"
BAR = "#238636"
FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

PAD = 16
TITLE_H = 32
GAP = 12
COLS, ROWS = 2, 3

TILE_STAGGER = 0.12
SLIDE_DUR = 0.4
COUNT_DUR = 1.1
FRAMES = 14
BAR_STAGGER = 0.05
BAR_DUR = 0.55


def canvas_size():
    if not os.path.exists(ASCII_SVG):
        return 796, 833
    with open(ASCII_SVG, encoding="utf-8") as handle:
        head = handle.read(240)
    match = re.search(r'width="(\d+)" height="(\d+)"', head)
    if not match:
        return 796, 833
    return int(match.group(1)), int(match.group(2))


def short(iso):
    if not iso:
        return ""
    day = datetime.date.fromisoformat(iso)
    return f"{day.strftime('%b')} {day.day}"


def span(streak):
    if not streak["length"]:
        return "-"
    return f"{short(streak['start'])} - {short(streak['end'])}"


def fmt(value, like):
    if isinstance(like, float):
        return f"{value:,.1f}"
    return f"{int(round(value)):,}"


def render(data):
    width, height = canvas_size()
    current = data["current_streak"]
    longest = data["longest_streak"]
    best = data["best_day"]
    n_days = len(data["days"])
    active = data["active_days"]
    share = f"{active / n_days:.0%} of the year" if n_days else "-"

    tiles = [
        ("current streak", current["length"], " days", span(current), GREEN),
        ("longest streak", longest["length"], " days", span(longest), INK),
        ("contributions", data["total_contributions"], "", "in the last year", INK),
        ("active days", active, f" / {n_days}", share, INK),
        ("best day", best["count"], "", short(best["date"]), INK),
        ("avg / active day", data["avg_per_active_day"], "", "contributions", INK),
    ]

    tile_w = (width - PAD * 2 - GAP) / COLS
    chart_h = 250
    tiles_top = TITLE_H + 14
    chart_top = height - PAD - chart_h
    tile_span = chart_top - GAP - tiles_top
    tile_h = (tile_span - GAP * (ROWS - 1)) / ROWS

    font = f'font-family="{FONT}"'
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="GitHub contribution stats">',
        "<style>",
        f".t{{opacity:0;animation:in {SLIDE_DUR}s ease-out both}}",
        "@keyframes in{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}",
        f".b{{transform-box:fill-box;transform-origin:bottom;transform:scaleY(0);animation:grow {BAR_DUR}s ease-out both}}",
        "@keyframes grow{to{transform:scaleY(1)}}",
        "@media (prefers-reduced-motion: reduce){.t,.b{opacity:1;transform:none;animation:none}}",
        "</style>",
        f'<rect width="{width}" height="{height}" rx="12" fill="{BG}" stroke="{FRAME}"/>',
        f'<rect width="{width}" height="{TITLE_H}" rx="12" fill="{BG2}"/>',
        f'<rect y="{TITLE_H - 12}" width="{width}" height="12" fill="{BG2}"/>',
        f'<line x1="0" y1="{TITLE_H}" x2="{width}" y2="{TITLE_H}" stroke="{FRAME}"/>',
    ]
    for index, color in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{16 + index * 16}" cy="16" r="5" fill="{color}"/>')
    parts.append(
        f'<text x="78" y="21" fill="{MUTED}" {font} font-size="13">vaibhav@github: ~$ ./stats.sh</text>'
    )

    for index, (label, value, suffix, caption, accent) in enumerate(tiles):
        col, row = index % COLS, index // COLS
        x = PAD + col * (tile_w + GAP)
        y = tiles_top + row * (tile_h + GAP)
        delay = index * TILE_STAGGER
        count_start = delay + SLIDE_DUR * 0.55
        parts.append(
            f'<g class="t" style="animation-delay:{delay:.2f}s">'
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{tile_w:.1f}" height="{tile_h:.1f}" rx="10" '
            f'fill="{TILE}" stroke="{FRAME}"/>'
            f'<text x="{x + 16:.1f}" y="{y + 28:.1f}" fill="{MUTED}" {font} font-size="15">$ {label}</text>'
        )
        number_y = y + tile_h * 0.62
        caption_y = y + tile_h - 16
        for frame in range(1, FRAMES + 1):
            progress = frame / FRAMES
            shown = value * (1 - (1 - progress) ** 3)
            on_at = count_start + COUNT_DUR * (frame - 1) / FRAMES
            off_at = count_start + COUNT_DUR * frame / FRAMES
            hold = frame == FRAMES
            anim = f'<set attributeName="opacity" to="1" begin="{on_at:.3f}s" fill="freeze"/>'
            if not hold:
                anim += f'<set attributeName="opacity" to="0" begin="{off_at:.3f}s" fill="freeze"/>'
            parts.append(
                f'<text x="{x + 16:.1f}" y="{number_y:.1f}" fill="{accent}" {font} '
                f'font-size="34" font-weight="700" opacity="0">'
                f'{fmt(shown, value)}<tspan font-size="16" font-weight="500" fill="{MUTED}">{suffix}</tspan>'
                f"{anim}</text>"
            )
        parts.append(
            f'<text x="{x + 16:.1f}" y="{caption_y:.1f}" fill="{MUTED}" {font} font-size="14">{caption}</text>'
            f"</g>"
        )

    monthly = data["monthly"]
    peak = max((item["total"] for item in monthly), default=1) or 1
    bar_delay0 = TILE_STAGGER * len(tiles) + 0.25
    parts.append(
        f'<g class="t" style="animation-delay:{bar_delay0:.2f}s">'
        f'<rect x="{PAD}" y="{chart_top:.1f}" width="{width - PAD * 2}" height="{chart_h - 4}" rx="10" '
        f'fill="{TILE}" stroke="{FRAME}"/>'
        f'<text x="{PAD + 16}" y="{chart_top + 28:.1f}" fill="{MUTED}" {font} font-size="15">'
        f"$ contributions / month</text>"
    )
    plot_top = chart_top + 56
    plot_bot = chart_top + chart_h - 36
    plot_l = PAD + 22
    plot_r = width - PAD - 22
    slot = (plot_r - plot_l) / max(len(monthly), 1)
    bar_w = slot * 0.55
    for index, item in enumerate(monthly):
        bar_h = max(3, (plot_bot - plot_top) * item["total"] / peak)
        bar_x = plot_l + index * slot + (slot - bar_w) / 2
        bar_y = plot_bot - bar_h
        fill = GREEN if item["total"] == peak else BAR
        delay = bar_delay0 + 0.15 + index * BAR_STAGGER
        parts.append(
            f'<rect class="b" style="animation-delay:{delay:.2f}s" '
            f'x="{bar_x:.1f}" y="{bar_y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" rx="3" fill="{fill}"/>'
        )
        month = datetime.date.fromisoformat(item["month"] + "-01").strftime("%b")[0]
        parts.append(
            f'<text x="{bar_x + bar_w / 2:.1f}" y="{plot_bot + 18:.1f}" fill="{MUTED}" {font} '
            f'font-size="12" text-anchor="middle">{month}</text>'
        )
        if item["total"] == peak:
            parts.append(
                f'<text x="{bar_x + bar_w / 2:.1f}" y="{bar_y - 8:.1f}" fill="{INK}" {font} '
                f'font-size="13" font-weight="700" text-anchor="middle">{peak:,}</text>'
            )
    parts.append("</g></svg>")
    return "".join(parts)


def main():
    with open(SRC, encoding="utf-8") as handle:
        data = json.load(handle)
    svg = render(data)
    with open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(svg)
    print(f"wrote {OUT} ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
