"""
Hand-authored neofetch-style info card. Lines fade and slide in once.

The canvas aspect is chosen so the card, shown at 490px, matches the
height of vaibhav-ascii.svg shown at 370px (370 + 490 = 860).

    python scripts/make_info_card.py
    STATIC=1 python scripts/make_info_card.py
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
OUT = os.path.join(ROOT, "info-card.svg")
ASCII_SVG = os.path.join(ROOT, "vaibhav-ascii.svg")

# Display widths in the README. Card aspect matches the portrait's displayed height.
SHOW_ASCII, SHOW_CARD = 370, 490
CARD_W = 980


def portrait_size():
    with open(ASCII_SVG, encoding="utf-8") as handle:
        head = handle.read(400)
    match = re.search(r'width="(\d+)" height="(\d+)"', head)
    if not match:
        raise SystemExit("generate vaibhav-ascii.svg before the info card")
    return int(match.group(1)), int(match.group(2))


PORTRAIT_W, PORTRAIT_H = portrait_size()
CARD_H = round(CARD_W * (SHOW_ASCII / SHOW_CARD) * (PORTRAIT_H / PORTRAIT_W))

BG = "#0d1117"
BG2 = "#161b22"
FRAME = "#30363d"
MUTED = "#7d8590"
INK = "#e6edf3"
KEY = "#58a6ff"
ACCENT = "#3fb950"
AMBER = "#f2cc60"

STATIC = bool(os.environ.get("STATIC"))

# (kind, key, value, value_color)
# kind is "rule" or "row"
LINES = [
    ("prompt", "", "vaibhav@github", ACCENT),
    ("rule", "", "", ""),
    ("row", "Now", "Software Engineer", INK),
    ("row", "", "backend, payments, system design", MUTED),
    ("row", "Prev", "Freelance engineer", INK),
    ("row", "Stack", "Java  ·  Spring Boot  ·  AWS  ·  Kubernetes", INK),
    ("row", "", "Python  ·  React  ·  TypeScript", MUTED),
    ("row", "GenAI", "RAG, LangChain, LangGraph, MCP", AMBER),
    ("row", "Also", "IoT  ·  ESP32, BLE, MQTT", INK),
    ("row", "Loves", "AI and algorithms", ACCENT),
    ("row", "Looking", "open source contributions", INK),
]


def main():
    pad = 36
    title_h = 32
    top = title_h + 48
    font = 26
    key_w = 168
    row_count = sum(1 for kind, *_rest in LINES if kind == "row")
    prompt_block = 64
    rule_block = 28
    cursor_block = 48
    bottom_pad = 40
    usable = CARD_H - top - prompt_block - rule_block - cursor_block - bottom_pad
    row_h = usable / row_count

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CARD_W}" height="{CARD_H}" '
        f'viewBox="0 0 {CARD_W} {CARD_H}" role="img" aria-label="Vaibhav Kale profile card">',
        "<style>",
        ".row { opacity: 0; animation: in 0.45s ease-out both; }",
        "@keyframes in { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }",
        "@media (prefers-reduced-motion: reduce) { .row { opacity: 1; animation: none; } }",
        "</style>",
        f'<rect width="{CARD_W}" height="{CARD_H}" rx="12" fill="{BG}" stroke="{FRAME}"/>',
        f'<rect width="{CARD_W}" height="{title_h}" rx="12" fill="{BG2}"/>',
        f'<rect y="{title_h - 12}" width="{CARD_W}" height="12" fill="{BG2}"/>',
        f'<line x1="0" y1="{title_h}" x2="{CARD_W}" y2="{title_h}" stroke="{FRAME}"/>',
    ]
    for i, color in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{16 + i * 16}" cy="16" r="5" fill="{color}"/>')
    parts.append(
        f'<text x="78" y="21" fill="{MUTED}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" '
        f'font-size="13">vaibhav@github: ~$ neofetch</text>'
    )

    y = top
    font_attr = 'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"'
    for index, (kind, key, value, color) in enumerate(LINES):
        delay = 0.12 * index
        cls = "" if STATIC else f' class="row" style="animation-delay:{delay:.2f}s"'
        if kind == "rule":
            parts.append(
                f'<g{cls}><line x1="{pad}" y1="{y - 8}" x2="{CARD_W - pad}" y2="{y - 8}" stroke="{FRAME}"/></g>'
            )
            y += rule_block
            continue
        if kind == "prompt":
            parts.append(
                f'<g{cls}><text x="{pad}" y="{y}" fill="{color}" {font_attr} font-size="34" font-weight="700">{value}</text></g>'
            )
            y += prompt_block
            continue
        key_text = key
        parts.append(f"<g{cls}>")
        if key_text:
            parts.append(
                f'<text x="{pad}" y="{y}" fill="{KEY}" {font_attr} font-size="{font}" font-weight="700">{key_text}</text>'
            )
        parts.append(
            f'<text x="{pad + key_w}" y="{y}" fill="{color}" {font_attr} font-size="{font}">{value}</text>'
        )
        parts.append("</g>")
        y += row_h

    cursor_y = y + 8
    blink = "" if STATIC else '<animate attributeName="opacity" values="1;0;1" dur="1.1s" begin="1.6s" repeatCount="indefinite"/>'
    parts.append(
        f'<rect x="{pad}" y="{cursor_y}" width="12" height="22" fill="{ACCENT}">{blink}</rect>'
    )
    parts.append("</svg>")

    svg = "".join(parts)
    with open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(svg)
    print(f"wrote {OUT} {CARD_W}x{CARD_H}")


if __name__ == "__main__":
    main()
