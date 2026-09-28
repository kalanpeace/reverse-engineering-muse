#!/usr/bin/env python3
"""Animated explainer of how Muse shops, built from one real saved search.

    python3 code/animate-how-muse-shops.py --out <dir> [--fonts DIR] [--variant paper]

Uses raw-tags search A-R1-Q01 ("stainless steel frying pan", 27 September 2026):
Unicorn's 100 candidates, the flywheel list and the products returned, with every dot
placed from the real product IDs. Writes a 1080x1350 MP4 (H.264, for LinkedIn), a GIF
and a poster PNG. Requires matplotlib and ffmpeg.
"""
import argparse
import json
import re
import subprocess
import zipfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.animation import FFMpegWriter
from matplotlib.patches import FancyBboxPatch, Rectangle

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("--out", type=Path, required=True)
parser.add_argument("--fonts", type=Path)
parser.add_argument("--variant", choices=["social", "paper"], default="social", help="paper: no closing card, GIF only, for use inside the report")
args = parser.parse_args()
if args.fonts:
    for name in ("LibertinusSerif-Regular", "LibertinusSerif-SemiBold", "ShareTechMono-Regular"):
        font_manager.fontManager.addfont(str(args.fonts / f"{name}.ttf"))
SERIF = ["Libertinus Serif", "DejaVu Sans"]
MONO = ["Share Tech Mono", "DejaVu Sans Mono"]

BLACK, CHARCOAL, SAGE, SAGE_DEEP, SAGE_WASH = "#0a0a0b", "#2a2a2c", "#b5d6c0", "#7fae8f", "#eef6f1"
FADED, MUTED = "#e2e2e4", "#6b6b70"

# ------------------------------------------------------------------ data (one real search)
archive = next((ROOT / "evidence/raw-tags-2026-09-27").glob("*.zip"))
with zipfile.ZipFile(archive) as z:
    member = next(n for n in z.namelist() if n.endswith("A-R1-Q01/stdout.bin"))
    response = json.loads(z.read(member))["tool_responses"][0]
pool = [str(i) for i in json.loads(response["metadata"])["query_debug_info"][0]["product_ids"]]
flywheel = {str(f["fbid"]) for f in response["flywheel_identifiers"]}
returned = re.findall(r"<product_id>(.*?)</product_id>", response["result_content"])
assert (len(pool), len(flywheel), len(returned)) == (100, 78, 42), (len(pool), len(flywheel), len(returned))
assert set(returned) <= flywheel <= set(pool)
rank = {pid: k for k, pid in enumerate(returned)}
PICKED = [29, 1, 9]  # returned spots 30, 2 and 10 (the paper's frying-pan task, Finding 11)

# ------------------------------------------------------------------ layout (pixels, y down)
W, H, FPS, DPI = 1080, 1350, 30, 100
fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI, facecolor="white")
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W)
ax.set_ylim(H, 0)
ax.axis("off")


def grid_xy(k):
    return 255 + (k % 10) * 63, 395 + (k // 10) * 33


def strip_xy(k):
    return 150 + (k % 14) * 60, 880 + (k // 14) * 38


CARD_X = [270, 540, 810]
CARD_Y = 1062

# ------------------------------------------------------------------ timeline (seconds)
T_POP, T_FLY, T_CUT, T_MOVE, T_PICK, T_END, T_TOTAL = 1.5, 4.5, 7.5, 10.5, 14.5, 18.5, 23.0


def ease(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def window(t, start, length):
    return ease((t - start) / length)


def mix(a, b, u):
    return a + (b - a) * u


def mix_color(c1, c2, u):
    a = matplotlib.colors.to_rgb(c1)
    b = matplotlib.colors.to_rgb(c2)
    return tuple(mix(x, y, u) for x, y in zip(a, b))


# ------------------------------------------------------------------ static scene
T = lambda x, y, s, **kw: ax.text(x, y, s, **kw)
T(60, 70, "CAELIAI  ·  MUSE RESEARCH", family=MONO, fontsize=15, color=MUTED, va="center")
title = T(60, 135, "How Meta's Muse picks what you see", family=SERIF, fontsize=40, color=BLACK, va="center")
query = T(60, 215, "Shopper asks Muse:  “stainless steel frying pan”", family=SERIF, fontsize=24, color=CHARCOAL, va="center")
ax.add_patch(Rectangle((40, 300), W - 80, 440, fc="#f6f6f7", ec="none", zorder=0))
T(60, 330, "META'S SERVERS", family=MONO, fontsize=16, color=BLACK, va="center")
pool_label = T(W - 60, 330, "", family=MONO, fontsize=16, color=CHARCOAL, va="center", ha="right")
ax.add_patch(Rectangle((40, 752), W - 80, 30, fc=BLACK, ec="none", zorder=1))
T(60, 767, "THE WALL", family=MONO, fontsize=15, color="white", va="center", zorder=2)
T(W - 60, 767, "no one outside Meta can see past this", family=MONO, fontsize=13, color=SAGE, va="center", ha="right", zorder=2)
T(60, 820, "MUSE", family=MONO, fontsize=16, color=BLACK, va="center")
strip_label = T(W - 60, 820, "", family=MONO, fontsize=16, color=CHARCOAL, va="center", ha="right")
cards = []
for i, x in enumerate(CARD_X):
    patch = FancyBboxPatch((x - 115, CARD_Y - 58), 230, 116, boxstyle="round,pad=0,rounding_size=14", fc=SAGE_WASH, ec=BLACK, lw=1.6, alpha=0, zorder=3)
    ax.add_patch(patch)
    label = T(x, CARD_Y - 16, f"Card {i + 1}", family=SERIF, fontsize=22, color=BLACK, ha="center", va="center", alpha=0, zorder=4)
    spot = T(x, CARD_Y + 24, f"was spot {PICKED[i] + 1}", family=MONO, fontsize=15, color=MUTED, ha="center", va="center", alpha=0, zorder=4)
    cards.append((patch, label, spot))
card_note = T(W / 2, 1170, "In the home-goods frying-pan task, Muse's 3 cards came from spots 30, 2 and 10.", family=SERIF, fontsize=15, color=MUTED, ha="center", va="center", alpha=0)
caption = T(W / 2, 1238, "", family=SERIF, fontsize=27, color=BLACK, ha="center", va="center")
T(W / 2, 1305, "Real saved search · raw catalog output · 27 Sep 2026 · caeliai.com", family=MONO, fontsize=13, color=MUTED, ha="center", va="center")

dots = ax.scatter([0] * 100, [0] * 100, s=[0] * 100, zorder=5, linewidths=0)

end_panel = Rectangle((0, 0), W, H, fc="white", ec="none", alpha=0, zorder=10)
ax.add_patch(end_panel)
end_texts = [
    T(W / 2, 470, "100  →  78  →  42  →  3", family=MONO, fontsize=54, color=BLACK, ha="center", va="center", alpha=0, zorder=11),
    T(W / 2, 560, "Unicorn's candidates  ·  hidden list  ·  returned  ·  cards shown (2 or 3)", family=MONO, fontsize=17, color=MUTED, ha="center", va="center", alpha=0, zorder=11),
    T(W / 2, 700, "The ranking happens behind a wall.", family=SERIF, fontsize=36, color=BLACK, ha="center", va="center", alpha=0, zorder=11),
    T(W / 2, 760, "Here's what can be measured from outside it.", family=SERIF, fontsize=36, color=BLACK, ha="center", va="center", alpha=0, zorder=11),
    T(W / 2, 900, "Read the full paper", family=MONO, fontsize=20, color=CHARCOAL, ha="center", va="center", alpha=0, zorder=11),
    T(W / 2, 950, "caeliai.com/blog/reverse-engineering-how-muse-shops", family=MONO, fontsize=21, color=BLACK, ha="center", va="center", alpha=0, zorder=11),
    T(W / 2, 1010, "Evidence and code: github.com/kalanpeace/reverse-engineering-muse", family=MONO, fontsize=15, color=MUTED, ha="center", va="center", alpha=0, zorder=11),
]

CAPTIONS = [
    (0.0, ""),
    (T_POP, "1 · Meta's Unicorn search pulls 100 candidates"),
    (T_FLY, "2 · A hidden list keeps 78 of them"),
    (T_CUT, "3 · Only 42 come back, each with a score"),
    (T_MOVE, "4 · They reach Muse in a new order"),
    (T_PICK, "5 · Muse checks a few and shows 2 or 3 cards"),
]


def frame(i):
    t = i / FPS
    head = window(t, 0.0, 0.8)
    title.set_alpha(head)
    query.set_alpha(window(t, 0.6, 0.8))
    caption.set_text(next(text for start, text in reversed(CAPTIONS) if t >= start))
    offsets, colors, sizes = [], [], []
    for k, pid in enumerate(pool):
        gx, gy = grid_xy(k)
        x, y = gx, gy
        size = 150 * window(t, T_POP + k * 0.012, 0.35)
        color = CHARCOAL
        if pid not in flywheel:
            u = window(t, T_FLY, 1.0)
            color = mix_color(CHARCOAL, FADED, u)
            size *= mix(1, 0.55, u)
        elif pid not in rank:
            u = window(t, T_CUT, 1.0)
            color = mix_color(CHARCOAL, FADED, u)
            size *= mix(1, 0.55, u)
        else:
            r = rank[pid]
            u = window(t, T_MOVE + (r % 14) * 0.04 + (r // 14) * 0.25, 1.6)
            sx, sy = strip_xy(r)
            x, y = mix(gx, sx, u), mix(gy, sy, u)
            color = mix_color(CHARCOAL, SAGE_DEEP, u)
            if r in PICKED:
                c = PICKED.index(r)
                v = window(t, T_PICK + 0.8 + c * 0.35, 1.0)
                highlight = window(t, T_PICK, 0.5)
                color = mix_color(color, BLACK, highlight)
                size *= mix(1, 1.7, highlight) * (1 - v)
                x, y = mix(x, CARD_X[c], v), mix(y, CARD_Y, v)
        offsets.append((x, y))
        colors.append(color)
        sizes.append(size)
    dots.set_offsets(offsets)
    dots.set_facecolors(colors)
    dots.set_sizes(sizes)
    kept = "100 candidates" if t < T_FLY + 0.5 else "78 on the hidden list" if t < T_CUT + 0.5 else "42 kept" if t < T_MOVE + 1.5 else "58 left behind"
    pool_label.set_text(kept if t >= T_POP else "")
    strip_label.set_text("42 returned, re-ordered" if t >= T_MOVE + 1.5 else "")
    for c, (patch, label, spot) in enumerate(cards):
        a = window(t, T_PICK + 1.4 + c * 0.35, 0.6)
        for artist in (patch, label, spot):
            artist.set_alpha(a)
    card_note.set_alpha(window(t, T_PICK + 2.6, 0.8))
    e = window(t, T_END, 0.9)
    end_panel.set_alpha(e)
    for n, text in enumerate(end_texts):
        text.set_alpha(window(t, T_END + 0.5 + n * 0.25, 0.7))


args.out.mkdir(parents=True, exist_ok=True)
if args.variant == "paper":
    T_TOTAL = T_END + 0.5
    for text in end_texts:
        text.set_visible(False)
    end_panel.set_visible(False)
mp4 = args.out / ("how-muse-shops.mp4" if args.variant == "social" else "how-muse-shops-paper.tmp.mp4")
writer = FFMpegWriter(fps=FPS, codec="libx264", bitrate=6000, extra_args=["-pix_fmt", "yuv420p", "-movflags", "+faststart"])
with writer.saving(fig, str(mp4), dpi=DPI):
    first = int(1.2 * FPS) if args.variant == "paper" else 0  # paper: open on the titled scene, not a blank frame
    for i in range(first, int(T_TOTAL * FPS)):
        frame(i)
        writer.grab_frame(facecolor="white")
if args.variant == "social":
    frame(int((T_PICK + 3.5) * FPS))
    fig.savefig(args.out / "how-muse-shops-poster.png", dpi=DPI, facecolor="white")
gif = args.out / ("how-muse-shops.gif" if args.variant == "social" else "anim-how-muse-shops.gif")
width, colors = (540, 64) if args.variant == "social" else (720, 48)
subprocess.run(
    ["ffmpeg", "-y", "-loglevel", "error", "-i", str(mp4), "-vf",
     f"fps=12,scale={width}:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors={colors}:stats_mode=diff[p];[b][p]paletteuse=dither=none:diff_mode=rectangle",
     str(gif)],
    check=True,
)
if args.variant == "paper":
    mp4.unlink()
print(f"wrote {gif.name}")
