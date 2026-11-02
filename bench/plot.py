"""baremetal.json + guest.json -> comparison.md and a bar chart (guest as % of bare metal).

Two copies of the svg so it looks right in GitHub's light and dark mode.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from xml.sax.saxutils import escape

THEMES = {
    "light": {
        "surface": "#fcfcfb",
        "ink": "#0b0b0b",
        "ink2": "#52514e",
        "muted": "#898781",
        "grid": "#e1e0d9",
        "axis": "#c3c2b7",
        "bar": "#2a78d6",
    },
    "dark": {
        "surface": "#1a1a19",
        "ink": "#f0efec",
        "ink2": "#c3c2b7",
        "muted": "#898781",
        "grid": "#2c2c2a",
        "axis": "#383835",
        "bar": "#3987e5",
    },
}

WIDTH = 720
LABEL_W = 230  # metric name + raw numbers
RIGHT_PAD = 70  # room for the % label
TOP = 92
ROW_H = 46
BAR_H = 20
FONT = "system-ui, -apple-system, 'Segoe UI', sans-serif"


def load(path: Path) -> dict:
    with path.open() as f:
        return json.load(f)


def pair_metrics(bare: dict, guest: dict) -> list[dict]:
    """metrics that are in both runs, with guest as % of bare metal"""
    g = {m["key"]: m for m in guest["metrics"]}
    rows = []
    for m in bare["metrics"]:
        if m["key"] not in g or not m["value"]:
            continue
        gv = g[m["key"]]["value"]
        rows.append(
            {
                "name": m["name"],
                "unit": m["unit"],
                "bare": m["value"],
                "guest": gv,
                "pct": 100.0 * gv / m["value"],
            }
        )
    return rows


def fmt(v: float) -> str:
    return f"{v:,.1f}" if v >= 10 else f"{v:,.2f}"


def bar_path(x: float, y: float, w: float, h: float, r: float = 4) -> str:
    """flat on the left, rounded on the right"""
    r = min(r, w, h / 2)
    return (
        f"M{x:.1f},{y:.1f} h{w - r:.1f} a{r},{r} 0 0 1 {r},{r} "
        f"v{h - 2 * r:.1f} a{r},{r} 0 0 1 -{r},{r} h-{w - r:.1f} Z"
    )


def render_svg(rows: list[dict], theme: str) -> str:
    c = THEMES[theme]
    x0 = LABEL_W
    plot_w = WIDTH - LABEL_W - RIGHT_PAD
    top_pct = max(110, math.ceil(max(r["pct"] for r in rows) / 10) * 10)
    sx = lambda p: x0 + plot_w * p / top_pct  # noqa: E731
    height = TOP + ROW_H * len(rows) + 36

    title = "Passthrough guest vs bare metal"
    desc = "; ".join(f"{r['name']}: {r['pct']:.1f}% of bare metal" for r in rows)
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
        f'viewBox="0 0 {WIDTH} {height}" role="img" aria-labelledby="t d" '
        f'font-family="{FONT}">',
        f'<title id="t">{title}</title><desc id="d">{escape(desc)}</desc>',
        f'<rect width="100%" height="100%" rx="8" fill="{c["surface"]}"/>',
        f'<text x="20" y="34" font-size="17" font-weight="600" fill="{c["ink"]}">{title}</text>',
        f'<text x="20" y="56" font-size="13" fill="{c["ink2"]}">'
        "Guest result as % of bare metal. 100% means passthrough costs nothing.</text>",
    ]

    # gridlines, then the 100% line
    axis_y = TOP + ROW_H * len(rows)
    for p in range(0, top_pct + 1, 25 if top_pct <= 150 else 50):
        x = sx(p)
        out.append(
            f'<line x1="{x:.1f}" y1="{TOP - 8}" x2="{x:.1f}" y2="{axis_y}" '
            f'stroke="{c["grid"]}" stroke-width="1"/>'
        )
        out.append(
            f'<text x="{x:.1f}" y="{axis_y + 18}" font-size="11" text-anchor="middle" '
            f'fill="{c["muted"]}">{p}%</text>'
        )
    x100 = sx(100)
    out.append(
        f'<line x1="{x100:.1f}" y1="{TOP - 14}" x2="{x100:.1f}" y2="{axis_y}" '
        f'stroke="{c["ink2"]}" stroke-width="1"/>'
    )
    out.append(
        f'<text x="{x100:.1f}" y="{TOP - 20}" font-size="11" text-anchor="middle" '
        f'fill="{c["ink2"]}">bare metal</text>'
    )
    out.append(
        f'<line x1="{x0}" y1="{TOP - 8}" x2="{x0}" y2="{axis_y}" '
        f'stroke="{c["axis"]}" stroke-width="1"/>'
    )

    for i, r in enumerate(rows):
        cy = TOP + ROW_H * i + ROW_H / 2
        out.append(
            f'<text x="20" y="{cy - 3:.1f}" font-size="13" fill="{c["ink"]}">'
            f"{escape(r['name'])}</text>"
        )
        out.append(
            f'<text x="20" y="{cy + 13:.1f}" font-size="11" fill="{c["ink2"]}">'
            f"{fmt(r['bare'])} → {fmt(r['guest'])} {escape(r['unit'])}</text>"
        )
        w = max(sx(r["pct"]) - x0, 1)
        out.append(f'<path d="{bar_path(x0, cy - BAR_H / 2, w, BAR_H)}" fill="{c["bar"]}"/>')
        out.append(
            f'<text x="{x0 + w + 8:.1f}" y="{cy + 4:.1f}" font-size="12" font-weight="600" '
            f'fill="{c["ink"]}">{r["pct"]:.1f}%</text>'
        )

    out.append("</svg>")
    return "\n".join(out) + "\n"


def render_markdown(rows: list[dict], bare: dict, guest: dict) -> str:
    lines = [
        "# Bare metal vs passthrough guest",
        "",
        "<picture>",
        '  <source media="(prefers-color-scheme: dark)" srcset="comparison-dark.svg">',
        '  <img alt="Guest benchmark results as a percentage of bare metal" '
        'src="comparison-light.svg">',
        "</picture>",
        "",
        "| Metric | Bare metal | Guest | Guest / bare metal |",
        "|---|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['name']} | {fmt(r['bare'])} {r['unit']} | {fmt(r['guest'])} {r['unit']} "
            f"| {r['pct']:.1f}% |"
        )
    be, ge = bare.get("environment", {}), guest.get("environment", {})
    lines += ["", "| Environment | Bare metal | Guest |", "|---|---|---|"]
    for key, label in [
        ("device", "Device"),
        ("kernel", "Kernel"),
        ("hip", "HIP"),
        ("torch", "PyTorch"),
    ]:
        lines.append(f"| {label} | {be.get(key, '')} | {ge.get(key, '')} |")
    lines.append(f"| Run at (UTC) | {bare.get('timestamp', '')} | {guest.get('timestamp', '')} |")
    lines += ["", "_Generated by `bench/plot.py` from `baremetal.json` and `guest.json`._", ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="compare bare metal and guest results")
    p.add_argument("--results-dir", type=Path, default=Path(__file__).parent / "results")
    args = p.parse_args(argv)

    d = args.results_dir
    missing = [n for n in ("baremetal.json", "guest.json") if not (d / n).exists()]
    if missing:
        print(f"missing in {d}: {', '.join(missing)}", file=sys.stderr)
        return 2

    bare, guest = load(d / "baremetal.json"), load(d / "guest.json")
    rows = pair_metrics(bare, guest)
    if not rows:
        print("no metrics in common between the two runs", file=sys.stderr)
        return 2

    for theme in THEMES:
        (d / f"comparison-{theme}.svg").write_text(render_svg(rows, theme))
    (d / "comparison.md").write_text(render_markdown(rows, bare, guest))
    for r in rows:
        print(f"{r['name']:22} {r['pct']:6.1f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
