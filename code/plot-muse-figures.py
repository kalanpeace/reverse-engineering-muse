#!/usr/bin/env python3
"""Draw the 15 figures in "Reverse Engineering How Muse Shops".

Every plotted number is read from this dataset's data/ files and checked against
the value the report prints, so a figure cannot drift from its text.

    python3 code/analyze_raw_tags.py            # writes data/raw-tags-analysis.json
    python3 code/plot-muse-figures.py --out figures [--fonts DIR]

--fonts should contain LibertinusSerif-{Regular,SemiBold,Italic}.ttf and
ShareTechMono-Regular.ttf (both SIL Open Font License); without them the figures
render in DejaVu. Requires matplotlib.
"""
import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

REPO = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("--out", type=Path, action="append", required=True, help="output directory (repeatable)")
parser.add_argument("--fonts", type=Path, help="directory with the Libertinus Serif and Share Tech Mono TTF files")
args = parser.parse_args()
OUTS = args.out

# Caeliai brand system: charcoal, sage and light gray; red is never a data series.
BLACK = "#0a0a0b"
CHARCOAL = "#2a2a2c"
SAGE = "#b5d6c0"
SAGE_DEEP = "#7fae8f"
SAGE_WASH = "#eef6f1"
GRAY = "#d4d4d6"
MUTED = "#6b6b70"
LINE = "#c9c9cc"
if args.fonts:
    for name in ("LibertinusSerif-Regular", "LibertinusSerif-SemiBold", "LibertinusSerif-Italic", "ShareTechMono-Regular"):
        font_manager.fontManager.addfont(str(args.fonts / f"{name}.ttf"))
SERIF = ["Libertinus Serif", "DejaVu Sans"]
MONO = ["Share Tech Mono", "Libertinus Serif", "DejaVu Sans"]
plt.rcParams.update(
    {
        "font.family": SERIF,
        "font.size": 12,
        "axes.edgecolor": LINE,
        "axes.labelcolor": CHARCOAL,
        "xtick.color": MUTED,
        "ytick.color": CHARCOAL,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "svg.fonttype": "none",
    }
)
WIDTH = 8.0  # inches; rendered at 200 dpi → 1600 px, shown at the 920 px content width.
DPI = 200


def expect(label, actual, expected):
    if actual != expected:
        raise SystemExit(f"{label}: data gives {actual!r}, report prints {expected!r}")


# ---------------------------------------------------------------- data
def load(name):
    return json.loads((REPO / "data" / name).read_text())


ranking = load("ranking-math-2026-09-27.json")
panel = load("merchant-benchmark-2026-09-27.json")
taste_summary = load("taste-study-summary.json")
taste = load("taste-analysis.json")
raw_tags = load("raw-tags-analysis.json")  # written by code/analyze_raw_tags.py
unicorn = load("unicorn-debug-analysis.json")  # written by code/analyze_unicorn.py
quality_counts = raw_tags["seller_quality_counts"]
expect("seller_quality counts", quality_counts, {"good": 2103, "elite": 401, "acceptable": 33, "poor": 5})


def mean(values):
    return sum(values) / len(values)


# ---------------------------------------------------------------- layout helpers
class Canvas:
    """Fixed-width figure laid out top-down in inches: header, body, source footer."""

    def __init__(self, number, title, body, sources):
        titles = wrap(title, 50)
        header = 0.62 + 0.44 * len(titles) + 0.62
        footer = 0.45 + 0.22 * len(sources) + 0.12
        self.h = header + body + footer
        self.fig = plt.figure(figsize=(WIDTH, self.h), facecolor="white")
        self.left, self.right = 0.55, WIDTH - 0.5
        self.text(self.left, 0.42, f"FIG. {number:02d}  ·  CAELIAI  ·  MUSE RESEARCH", MONO, 9.5, MUTED)
        y = 0.62
        for line in titles:
            y += 0.44
            self.text(self.left, y, line, SERIF, 21, BLACK)
        self.rule(y + 0.3, BLACK, 1.6)
        self.y = header  # top of the body
        y = header + body + 0.2
        self.rule(y, LINE, 0.8)
        for line in sources:
            y += 0.22
            self.text(self.left, y, line, MONO, 8.6, MUTED)

    def rule(self, y, color, lw):
        self.fig.add_artist(plt.Line2D([self.left / WIDTH, self.right / WIDTH], [1 - y / self.h] * 2, color=color, lw=lw))

    def text(self, x, y, s, family, size, color, **kw):
        return self.fig.text(x / WIDTH, 1 - y / self.h, s, family=family, fontsize=size, color=color, va="baseline", **kw)

    def axes(self, top, height, left=None, right=None):
        """Axes box `top` inches below the body top; tick labels need ~0.6 in below it."""
        left = self.left if left is None else left
        right = self.right if right is None else right
        return self.fig.add_axes([left / WIDTH, 1 - (self.y + top + height) / self.h, (right - left) / WIDTH, height / self.h])

    def save(self, stem):
        for out in OUTS:
            out.mkdir(parents=True, exist_ok=True)
            self.fig.savefig(out / f"{stem}.png", dpi=DPI, facecolor="white")
        plt.close(self.fig)
        print(f"wrote {stem}.png")


def wrap(text, width):
    words, lines, line = text.split(), [], ""
    for word in words:
        if line and len(line) + 1 + len(word) > width:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return lines + [line]


def style_axes(ax, grid_axis="x"):
    ax.tick_params(length=0, labelsize=10.5)
    ax.grid(axis=grid_axis, color="#ececee", lw=0.8)
    ax.set_axisbelow(True)
    for axis in ("x", "y"):
        if axis == grid_axis or grid_axis == "both":
            labels = ax.get_xticklabels() if axis == "x" else ax.get_yticklabels()
            for label in labels:
                label.set_family(MONO)
                label.set_fontsize(10)
                label.set_color(MUTED)


def box(ax, x, y, w, h, fill="white", edge=CHARCOAL, lw=1.2):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="square,pad=0", fc=fill, ec=edge, lw=lw))


def arrow(ax, start, end, color=CHARCOAL):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=16, color=color, lw=1.4, shrinkA=0, shrinkB=0))


def blank(ax):
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")


def bar_axes(ax):
    ax.spines["left"].set_visible(False)
    style_axes(ax, "x")


# ---------------------------------------------------------------- 01 How Muse shops
def fig_how_muse_shops():
    c = Canvas(1, "How Muse shops, in six steps", 5.4, ["Traced Muse shopping tasks · 27 September 2026 · home goods: 5 tasks, fashion: 6 tasks"])
    ax = c.axes(0, 5.4)
    blank(ax)
    steps = [
        ("The shopper asks a question.", ""),
        ("Muse turns it into a search", "of the Muse catalog, behind meta-catalog-search."),
        ("The Muse catalog returns a list.", "40 to 71 products, each with a score."),
        ("Muse picks a few.", "Usually 3 to check."),
        ("A browser checks those products", "on the stores' own websites: price, stock, exact variant."),
        ("Muse shows the shopper", "2 or 3 cards."),
    ]
    cols, bw, bh, gx, gy = 3, 0.29, 0.42, 0.065, 0.16
    for i, (head, detail) in enumerate(steps):
        row, col = divmod(i, cols)
        x = col * (bw + gx)
        y = 1 - (row + 1) * bh - row * gy
        last = i == len(steps) - 1
        box(ax, x, y, bw, bh, fill=SAGE_WASH if last else "white", edge=BLACK if last else CHARCOAL)
        ax.text(x + 0.022, y + bh - 0.05, f"{i + 1:02d}", family=MONO, fontsize=13, color=BLACK if last else SAGE_DEEP, va="top")
        head_lines = wrap(head, 19)
        ax.text(x + 0.022, y + bh - 0.115, "\n".join(head_lines), family=SERIF, fontsize=13.5, color=BLACK, va="top", weight="semibold", linespacing=1.15)
        if detail:
            ax.text(x + 0.022, y + bh - 0.14 - 0.06 * len(head_lines), "\n".join(wrap(detail, 24)), family=SERIF, fontsize=11.5, color=MUTED, va="top", linespacing=1.25)
        if col < cols - 1:
            arrow(ax, (x + bw + 0.008, y + bh / 2), (x + bw + gx - 0.008, y + bh / 2))
    # Row wrap: step 3 down, across, into step 4.
    x3, x4, top_row_bottom = 2 * (bw + gx) + bw / 2, bw / 2, 1 - bh
    mid = top_row_bottom - gy / 2
    ax.plot([x3, x3, x4], [top_row_bottom - 0.01, mid, mid], color=CHARCOAL, lw=1.4)
    arrow(ax, (x4, mid), (x4, top_row_bottom - gy + 0.008))
    c.save("fig-how-muse-shops")


# ---------------------------------------------------------------- 02 Three lists
def fig_three_lists():
    fw = unicorn["flywheel"]
    sizes = fw["sizes_when_unicorn_list_is_100"]
    expect("nesting holds in every search", (fw["returned_within_flywheel"], fw["flywheel_within_unicorn_list"], fw["of_those_with_flywheel_list"]), (417, 417, 417))
    expect("median sizes", (sizes["flywheel"]["median"], sizes["returned"]["median"]), (80, 47))
    expect("flywheel cap", (sizes["flywheel_max"], sizes["flywheel_exactly_80"], sizes["calls"]), (80, 228, 375))
    c = Canvas(2, "Unicorn's candidates, the flywheel list and the returned products, one inside the next", 3.9, [
        f"All raw responses in the evidence · bars: median of the {sizes['calls']} searches where Unicorn listed 100",
        "lines: middle half of those searches · 26–27 September 2026",
    ])
    ax = c.axes(0.1, 2.75, left=2.75, right=WIDTH - 0.55)
    rows = [
        ("Unicorn's candidates\n(query_debug_info)", 100, None, GRAY, "100"),
        ("Flywheel list\n(flywheel_identifiers)", sizes["flywheel"]["median"], sizes["flywheel"], SAGE_DEEP, f"{sizes['flywheel']['median']}  ·  never more than 80"),
        ("Returned to Muse", sizes["returned"]["median"], sizes["returned"], CHARCOAL, f"{sizes['returned']['median']}"),
    ]
    for i, (label, value, spread, color, text) in enumerate(rows):
        ax.barh(i, value, color=color, height=0.55)
        if spread:
            ax.plot([spread["q1"], spread["q3"]], [i + 0.38, i + 0.38], color=BLACK, lw=1.2)
            for x in (spread["q1"], spread["q3"]):
                ax.plot([x, x], [i + 0.33, i + 0.43], color=BLACK, lw=1.2)
        ax.text(value + 1.5, i, text, family=MONO, fontsize=11.5, color=BLACK, va="center")
    ax.set_yticks(range(len(rows)), [r[0] for r in rows], fontsize=12)
    ax.invert_yaxis()
    ax.set_xlim(0, 150)
    ax.set_xticks([0, 20, 40, 60, 80, 100])
    ax.set_xlabel("Products", fontsize=11.5, labelpad=8)
    bar_axes(ax)
    c.text(c.left, c.y + 3.75, f"In all {fw['of_those_with_flywheel_list']} single searches, each list sat entirely inside the one above it.", SERIF, 12.5, BLACK)
    c.save("fig-three-lists")


# ---------------------------------------------------------------- 03 Quince
def fig_quince():
    neutral = ranking["neutral"]
    expect("neutral run", neutral["run_id"], "neutral_baseline/ncap-n50-run2")
    positions = [p["position"] for p in neutral["products"]]
    scores = [float(p["ranking_score"]) for p in neutral["products"]]
    expect("neutral products", len(scores), 43)
    expect("Hestan #40", (positions[39], scores[39]), (40, 0.558594))
    expect("Quince #41", (positions[40], scores[40]), (41, 0.773438))
    higher = sum(s > scores[40] for s in scores)
    expect("products scoring higher than Quince", higher, 19)
    c = Canvas(3, "A higher score can sit lower on the list", 4.4,
               ["neutral_baseline/ncap-n50-run2 · \"stainless steel frying pan\" -n 50 · 43 products · 26 September 2026"])
    ax = c.axes(0.1, 3.55, left=1.2)
    ax.plot(positions, scores, color=GRAY, lw=1.4, zorder=1)
    ax.scatter(positions, scores, s=16, color=CHARCOAL, zorder=2)
    ax.axhline(scores[40], color=SAGE_DEEP, lw=1, ls=(0, (4, 3)), zorder=0)
    ax.scatter([41], [scores[40]], s=110, color=SAGE, ec=BLACK, lw=1.4, zorder=3)
    ax.scatter([40], [scores[39]], s=70, color="white", ec=BLACK, lw=1.4, zorder=3)
    ax.annotate("Quince · spot 41 · 0.773438", (41, scores[40]), (26.5, 0.835), family=MONO, fontsize=10.5, color=BLACK,
                arrowprops=dict(arrowstyle="-", color=BLACK, lw=0.8))
    ax.annotate("Hestan · spot 40 · 0.558594", (40, scores[39]), (22.5, 0.5), family=MONO, fontsize=10.5, color=BLACK,
                arrowprops=dict(arrowstyle="-", color=BLACK, lw=0.8))
    ax.text(1, scores[40] - 0.022, f"{higher} products score higher than Quince", family=SERIF, fontsize=11.5, color=SAGE_DEEP)
    ax.set_xlim(0, 44)
    ax.set_ylim(0.45, 0.87)
    ax.set_xticks([1, 10, 20, 30, 40, 43])
    ax.set_xlabel("Spot on the returned list", fontsize=11.5, labelpad=8)
    ax.set_ylabel("ranking_score", family=MONO, fontsize=10.5, labelpad=8)
    style_axes(ax, "both")
    c.save("fig-quince-score-vs-position")


# ---------------------------------------------------------------- 04 Score jumps
def fig_score_jumps():
    hist = ranking["historical"]
    expect("early runs with a jump", (hist["nonmonotone_runs"], hist["eligible_scored_runs"]), (130, 173))
    expect("panel lists with a jump", panel["numeric_score_order"]["calls_with_increases"], 41)
    panel_3plus = sum(r["returned_records"] >= 3 for r in panel["runs"])
    fashion = (taste_summary["nonempty_calls_with_adjacent_score_rise"], taste_summary["nonempty_calls"])
    expect("fashion lists with a jump", fashion, (33, 69))
    rows = [
        ("Early runs", 130, 173, "lists with 3 or more products"),
        ("100-search panel", 41, panel_3plus, "lists with 3 or more products"),
        ("Fashion study", *fashion, "non-empty lists"),
    ]
    c = Canvas(4, "Share of lists with at least one upward score jump", 3.3, [
        "Upward jump: a product scores higher than the one right above it.",
        "Separate searches, dates and program versions · 26–27 September 2026",
    ])
    ax = c.axes(0.1, 2.6, left=2.4, right=WIDTH - 1.2)
    for i, (label, k, n, unit) in enumerate(rows):
        share = k / n
        ax.barh(i, 1, color="#f1f1f2", height=0.42)
        ax.barh(i, share, color=CHARCOAL, height=0.42)
        ax.text(1.03, i, f"{share:.0%}", family=MONO, fontsize=15, color=BLACK, va="center")
        ax.text(0, i + 0.38, f"{k} of {n} {unit}", family=MONO, fontsize=9.5, color=MUTED, va="center")
    ax.set_yticks(range(len(rows)), [r[0] for r in rows], fontsize=13)
    ax.set_ylim(len(rows) - 0.4, -0.45)
    ax.set_xlim(0, 1)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1], ["0%", "25%", "50%", "75%", "100%"])
    bar_axes(ax)
    c.save("fig-score-jumps")


# ---------------------------------------------------------------- 05 Hydro Flask
def fig_hydro_flask():
    base, brand = ranking["preference"]["BASE"], ranking["preference"]["BRAND"]
    for cond in (base, brand):
        assert len({json.dumps(p, sort_keys=True) for p in cond["primary"]}) == 1  # identical in all 3 repeats
    b, f = base["primary"][0], brand["primary"][0]
    expect("Hydro Flask product", {b["product_id"], f["product_id"]}, {"27333065053055404"})
    expect("no filter", (b["position"], b["ranking_score"], base["records_per_repeat"][0]), (15, "0.753906", 40))
    expect("brand filter", (f["position"], f["ranking_score"], brand["records_per_repeat"][0]), (6, "0.750000", 47))
    c = Canvas(5, "Hydro Flask moved up while its score went down", 3.3, [
        "color/R02-BASE-1, color/R03-BRAND-1 · product 27333065053055404 · each run 3 times, identical",
        "\"32 oz stainless steel insulated water bottle\" -n 50 --raw · 27 September 2026",
    ])
    rows = ["No brand filter\n40 products", "--brand \"Hydro Flask\"\n47 products"]
    c.text(2.55, c.y + 0.12, "SPOT ON THE LIST  (1 = TOP)", MONO, 9.5, MUTED)
    c.text(5.2, c.y + 0.12, "RANKING_SCORE", MONO, 9.5, MUTED)
    ax1 = c.axes(0.35, 1.7, left=2.55, right=4.75)
    ax2 = c.axes(0.35, 1.7, left=5.2, right=c.right)
    for ax, values, lim, fmt in ((ax1, [15, 6], (48, 0), "{:.0f}"), (ax2, [0.753906, 0.750000], (0.70, 0.80), "{:.6f}")):
        for i, v in enumerate(values):
            ax.scatter([v], [i], s=130, color=SAGE if i == 1 else CHARCOAL, ec=BLACK, lw=1.2, zorder=2)
            ax.text(v, i - 0.3, fmt.format(v), family=MONO, fontsize=12, color=BLACK, ha="center")
        ax.set_ylim(1.5, -0.8)
        ax.set_xlim(*lim)
        bar_axes(ax)
    ax1.set_xticks([47, 30, 15, 6, 1])
    ax2.set_xticks([0.70, 0.75, 0.80])
    ax1.set_yticks([0, 1], rows, fontsize=12, family=MONO)
    ax2.set_yticks([])
    style_axes(ax1, "x")
    style_axes(ax2, "x")
    for label in ax1.get_yticklabels():
        label.set_color(CHARCOAL)
    c.text(c.left, c.y + 2.95, "The bottle moved up 9 spots while its score dropped by 0.003906.", SERIF, 13, BLACK)
    c.save("fig-hydro-flask-position-vs-score")


# ---------------------------------------------------------------- 06 Requested vs returned
def fig_requested_vs_returned():
    cb = ranking["count_boundary"]
    expect("Levoit asked 10", cb["L/n10"][0], 63)
    expect("Misen asked 11", cb["M/n11"][0], 5)
    rc = panel["returned_count"]
    expect("panel range", (rc["min"], rc["max"]), (0, 67))
    requested = [1, 9, 10, 11, 20, 50]
    c = Canvas(6, "Products requested versus products returned", 4.9, [
        "boundary36 count runs, 3 repeats each (dots) · Levoit: \"small air purifier for a bedroom\"",
        "Misen: \"stainless steel frying pan\" · 27 September 2026",
    ])
    ax = c.axes(0.1, 3.5, left=1.2)
    xs = list(range(len(requested)))
    ax.scatter(xs, requested, marker="_", s=900, color=BLACK, lw=1.6, zorder=1, label="Returned = requested")
    for key, label, color, dx in (("L", "--brand Levoit", CHARCOAL, -0.13), ("M", "--brand Misen", SAGE_DEEP, 0.13)):
        for j, n in enumerate(requested):
            ax.scatter([j + dx] * 3, cb[f"{key}/n{n}"], s=38, color=color, zorder=3, label=label if j == 0 else None)
    ax.annotate("asked 10, got 63", (2 - 0.13, 63), (0.15, 58), family=MONO, fontsize=10.5, color=BLACK,
                arrowprops=dict(arrowstyle="-", color=BLACK, lw=0.8), va="center")
    ax.annotate("asked 11, got 5", (3 + 0.13, 5), (1.45, 30), family=MONO, fontsize=10.5, color=BLACK,
                arrowprops=dict(arrowstyle="-", color=BLACK, lw=0.8))
    ax.set_xticks(xs, [str(n) for n in requested])
    ax.set_xlabel("Products requested (-n)", fontsize=11.5, labelpad=8)
    ax.set_ylabel("Products returned", fontsize=11.5, labelpad=8)
    ax.set_ylim(0, 70)
    ax.set_xlim(-0.5, 5.5)
    style_axes(ax, "both")
    ax.grid(axis="x", visible=False)
    ax.legend(loc="upper right", frameon=False, prop={"family": MONO, "size": 10})
    c.text(1.2, c.y + 4.65, f"100-search panel: every search asked for 50 and got back {rc['min']} to {rc['max']}.", SERIF, 13, BLACK)
    c.save("fig-requested-vs-returned")


# ---------------------------------------------------------------- 07 Query combination
def fig_query_combination():
    comp = ranking["query_composition"]
    for rep in comp:
        expect("combined search", (rep["solo_intersection"], rep["AB_records"], rep["from_A"], rep["from_B"], len(rep["absent_from_solo_union"])), (0, 56, 27, 26, 3))
        expect("two queries vs one long query", (rep["AB_JOIN_intersection"], rep["AB_JOIN_union"]), (5, 99))
    stab = ranking["query_stability"]
    expect("A/B/JOIN counts", (stab["A"]["counts"][0], stab["B"]["counts"][0], stab["JOIN"]["counts"][0]), (43, 53, 48))
    c = Canvas(7, "Combined search found products neither search found alone", 4.4,
               ["synonyms/R03-A-1, R02-B-1, R05-AB-1, R04-JOIN-1 · 3 interleaved repeats, same counts · 27 September 2026"])
    ax = c.axes(0.1, 3.3, left=2.8, right=WIDTH - 0.5)
    rows = [
        ("A  \"stainless steel\nfrying pan\"", [(43, SAGE, "43")]),
        ("B  \"stainless steel\nskillet\"", [(53, CHARCOAL, "53")]),
        ("A and B as\ntwo --query flags", [(27, SAGE, "27 from A"), (26, CHARCOAL, "26 from B"), (3, None, "")]),
        ("A and B as\none long query", [(48, GRAY, "48")]),
    ]
    for i, (label, parts) in enumerate(rows):
        left = 0
        for width, color, text in parts:
            if color is None:
                ax.barh(i, width, left=left, color="white", height=0.55, ec=BLACK, lw=1.2, hatch="////")
            else:
                ax.barh(i, width, left=left, color=color, height=0.55, ec="white", lw=1.5)
                ax.text(left + width / 2, i, text, family=MONO, fontsize=11, color="white" if color == CHARCOAL else BLACK, ha="center", va="center")
            left += width
    ax.text(57, 2, "3 from neither", family=MONO, fontsize=10.5, color=BLACK, va="center")
    ax.set_yticks(range(len(rows)), [r[0] for r in rows], fontsize=12)
    ax.invert_yaxis()
    ax.set_xlim(0, 76)
    ax.set_xticks([0, 10, 20, 30, 40, 50, 60, 70])
    ax.set_xlabel("Products returned", fontsize=11.5, labelpad=8)
    bar_axes(ax)
    c.text(c.left, c.y + 4.3, "The two single searches shared zero products. The two versions of A + B shared 5 of 99.", SERIF, 12.5, BLACK)
    c.save("fig-query-combination")


# ---------------------------------------------------------------- 08 Five drop-out points
def fig_five_dropout_points():
    c = Canvas(8, "Five places a product can drop out", 4.9, ["Fashion shopping tasks · 27 September 2026 · examples, not rates"])
    ax = c.axes(0, 4.9)
    blank(ax)
    stages = [
        ("RETURNED", "The catalog returned 40 to 71 products per task."),
        ("CHECKED", "T11: a browser task with three store URLs: COS, Kiyonna and Reiss."),
        ("VERIFIED", "COS: 404 error twice. Lulus: blocked by a human-verification check (\"Are You Real?\")."),
        ("SELECTED", "\"keeping vs. reordering is still the model's call.\""),
        ("SHOWN", "Muse showed 2 or 3. A pre-owned dress got through a \"new only\" request."),
    ]
    h, gap = 0.155, 0.056
    for i, (label, text) in enumerate(stages):
        y = 1 - (i + 1) * h - i * gap
        last = label == "SHOWN"
        box(ax, 0, y, 1, h, fill=SAGE_WASH if last else "white", edge=BLACK if last else CHARCOAL)
        ax.text(0.03, y + h / 2, f"{i + 1:02d}  {label}", family=MONO, fontsize=12.5, color=BLACK, va="center")
        ax.text(0.3, y + h / 2, "\n".join(wrap(text, 46)), family=SERIF, fontsize=12.5, color=CHARCOAL, va="center", linespacing=1.3)
        if i < len(stages) - 1:
            arrow(ax, (0.12, y - 0.004), (0.12, y - gap + 0.004), color=MUTED)
    c.save("fig-five-dropout-points")


# ---------------------------------------------------------------- 09 Returned vs shown
def fig_returned_vs_shown():
    # (task, [(catalog spot, shown?, label, label x-offset)]) from the manuscript's Finding 11 table and frying-pan task.
    rows = [
        ("Frying pan", [(30, True, "card 1", 0), (2, True, "card 2", 0), (10, True, "card 3", 0)]),
        ("\"Show me women's\ndresses.\"", [(3, False, "COS · 404", 2), (35, True, "card 1", 0), (65, True, "card 2", 0)]),
        ("\"Show me fashionable\nwomen's dresses.\"", [(2, True, "card 1", -1.5), (5, True, "card 2", 3.5)]),
        ("Clean lines,\nno visible logos", [(1, True, "card 1", 1)]),
        ("Bold prints,\nnew items only", [(40, True, "card 2 · pre-owned", 0)]),
        ("Lesser-known\ndesigners", [(29, True, "", 0), (52, True, "", 0), (63, True, "", 0)]),
        ("Current dress\ntrends", [(24, False, "Lulus · blocked", 0)]),
    ]
    c = Canvas(9, "Returned is not the same as shown", 5.9, [
        "Home-goods frying-pan task and fashion tasks · products matched by page, not size or color",
        "27 September 2026 · examples from one chat, not rates",
    ])
    c.text(2.45, c.y + 0.15, "●  shown as a card        ○  checked, not shown", MONO, 10.5, CHARCOAL)
    ax = c.axes(0.45, 4.75, left=2.45, right=WIDTH - 0.45)
    ax.axvspan(0.5, 10.5, color=SAGE_WASH, zorder=0)
    ax.text(5.5, -0.8, "TOP 10", family=MONO, fontsize=10, color=SAGE_DEEP, ha="center")
    for i, (_, points) in enumerate(rows):
        ax.plot([0.5, 71], [i, i], color="#ececee", lw=1, zorder=1)
        for spot, shown, label, dx in points:
            ax.scatter([spot], [i], s=95, color=CHARCOAL if shown else "white", ec=BLACK, lw=1.3, zorder=3)
            if label:
                ax.text(spot + dx, i - 0.32, label, family=MONO, fontsize=9.5, color=BLACK if shown else MUTED, ha="center")
    ax.text(46, 5 - 0.32, "cards 1–3", family=MONO, fontsize=9.5, color=BLACK, ha="center")
    ax.set_yticks(range(len(rows)), [r[0] for r in rows], fontsize=11.5)
    ax.set_ylim(len(rows) - 0.45, -1.15)
    ax.set_xlim(0.5, 71)
    ax.set_xticks([1, 10, 20, 30, 40, 50, 60, 70])
    ax.set_xlabel("Spot on the catalog's returned list", fontsize=11.5, labelpad=8)
    bar_axes(ax)
    c.save("fig-returned-vs-shown")


# ---------------------------------------------------------------- 10 Seller quality mix
def fig_seller_quality_mix():
    order = ["good", "elite", "acceptable", "poor"]
    total = sum(quality_counts.values())
    shares = [f"{quality_counts[q] / total:.1%}" for q in order]
    expect("seller_quality shares", shares, ["82.7%", "15.8%", "1.3%", "0.2%"])
    c = Canvas(10, "Meta rates every seller: seller_quality labels across 2,542 product records", 3.3,
               ["Raw-tags collection · 48 searches (12 categories + 4 products, 3 repeats each) · 27 September 2026"])
    ax = c.axes(0.1, 2.5, left=1.9, right=WIDTH - 2.0)
    for i, q in enumerate(order):
        n = quality_counts[q]
        ax.barh(i, n, color=CHARCOAL if q in ("good", "elite") else GRAY, height=0.55)
        ax.text(n + 40, i, f"{n:,}  ·  {shares[i]}", family=MONO, fontsize=12, color=BLACK, va="center")
    ax.set_yticks(range(4), order, family=MONO, fontsize=13)
    ax.invert_yaxis()
    ax.set_xlim(0, 2150)
    ax.set_xticks([0, 500, 1000, 1500, 2000], ["0", "500", "1,000", "1,500", "2,000"])
    ax.set_xlabel("Product records", fontsize=11.5, labelpad=8)
    bar_axes(ax)
    c.save("fig-seller-quality-mix")


# ---------------------------------------------------------------- 11 Elite gap by category
def fig_elite_gap():
    cats = raw_tags["elite_and_native_by_category_repeat_1"]
    rows = [(c["query"], c["elite_minus_good_mean_score"], c["elite_records"], c["good_records"]) for c in cats]
    gaps = [r[1] for r in rows]
    expect("elite higher in", sum(g > 0 for g in gaps), 8)
    expect("gap range", (round(min(gaps), 3), round(max(gaps), 3)), (-0.027, 0.061))
    expect("native lower in", sum(c["native_minus_non_native_mean_score"] < 0 for c in cats), 10)
    rows.sort(key=lambda r: -r[1])
    c = Canvas(11, "Elite minus good average score difference, by category", 5.6, [
        "Raw-tags collection, Arm A · 12 category searches, repeat 1 of 3 · 27 September 2026",
        "Averages within a search; products differ in other ways too.",
    ])
    ax = c.axes(0.1, 4.8, left=3.85, right=WIDTH - 0.5)
    for i, (query, g, ne, ng) in enumerate(rows):
        ax.barh(i, g, color=SAGE_DEEP if g > 0 else CHARCOAL, height=0.6)
        ax.text(g + (0.0015 if g > 0 else -0.0015), i, f"{g:+.3f}".replace("-", "−"), family=MONO, fontsize=10.5, color=BLACK,
                va="center", ha="left" if g > 0 else "right")
    ax.set_yticks(range(len(rows)), [f"{q}  ({ne} elite / {ng} good)" for q, _, ne, ng in rows], fontsize=10.5)
    ax.invert_yaxis()
    ax.axvline(0, color=BLACK, lw=1)
    ax.set_xlim(-0.05, 0.075)
    ax.set_xticks([-0.04, -0.02, 0, 0.02, 0.04, 0.06], ["−0.04", "−0.02", "0", "+0.02", "+0.04", "+0.06"])
    ax.set_xlabel("Average ranking_score: elite sellers minus good sellers", fontsize=11.5, labelpad=8)
    bar_axes(ax)
    c.save("fig-elite-gap-by-category")


# ---------------------------------------------------------------- 12 Taste words
def taste_jaccard(left, right):
    for comp in taste["same_repeat_condition_comparisons"]:
        if comp["left"] == left and comp["right"] == right:
            values = [r["membership_overlap"]["jaccard"] for r in comp["repeat_comparisons"] if r["status"] == "available"]
            assert len(values) == 3
            return mean(values)
    raise KeyError((left, right))


def condition_counts(cid):
    return next(c["counts"] for c in taste_summary["conditions"] if c["condition_id"] == cid)


def fig_taste_words():
    rows = [("women's dresses (repeated)", taste_summary["original_within_mean_jaccard"], "about 91%")]
    for cid, word, printed in [
        ("T02", "fashionable", "15%"), ("T04", "trendy", "11%"), ("T03", "stylish", "11%"), ("T07", "minimalist", "1%"),
        ("T09", "bold", "1%"), ("T05", "designer", "1%"), ("T06", "luxury", "0%"), ("T10", "timeless", "0%"), ("T08", "quiet luxury", "0%"),
    ]:
        rows.append((f"{word} …", taste_jaccard(cid, "T01"), printed))
    for label, value, printed in rows:
        expect(f"kept for {label}", f"{round(value * 100):.0f}%", printed.replace("about ", ""))
    c = Canvas(12, "One word swaps out most of the results", 5.4, [
        "Fashion wording study · each wording run 3 times · shared products ÷ all different products, averaged",
        "27 September 2026",
    ])
    ax = c.axes(0.1, 4.6, left=2.75, right=WIDTH - 1.2)
    for i, (label, value, printed) in enumerate(rows):
        ax.barh(i, 1, color="#f1f1f2", height=0.6)
        ax.barh(i, value, color=SAGE_DEEP if i == 0 else CHARCOAL, height=0.6)
        ax.text(1.03, i, printed.replace("about ", "≈"), family=MONO, fontsize=12, color=BLACK, va="center")
    ax.set_yticks(range(len(rows)), [r[0] for r in rows], fontsize=12)
    ax.invert_yaxis()
    ax.set_xlim(0, 1)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1], ["0%", "25%", "50%", "75%", "100%"])
    ax.set_xlabel("Products kept in common with the plain search \"women's dresses\"", fontsize=11.5, labelpad=8)
    bar_axes(ax)
    c.save("fig-taste-words")


# ---------------------------------------------------------------- 13 Occasions
def fig_taste_overlap():
    rows = [("Show me women's dresses.", "T11", None)]
    for cid, label in [
        ("T13", "I'm going out for the evening …"),
        ("T17", "I'm attending a summer wedding as a guest …"),
        ("T15", "I'm going to dinner at an upscale restaurant …"),
        ("T18", "I'm meeting friends for a casual brunch …"),
        ("T16", "I'm going to an art gallery opening …"),
    ]:
        rows.append((label, cid, taste_jaccard(cid, "T11")))
    kept = [r[2] for r in rows[1:]]
    expect("occasion overlap range", (round(min(kept) * 100), round(max(kept) * 100)), (0, 3))
    expect("gallery counts", condition_counts("T16"), [17, 18, 19])
    c = Canvas(13, "Describe the occasion, get different products", 4.3, [
        "Fashion wording study · \"Kept\": products in common with \"Show me women's dresses.\"",
        "shared ÷ all different, averaged over 3 repeats · 27 September 2026",
    ])
    left, right = 3.9, WIDTH - 1.45
    c.text(left, c.y + 0.15, "PRODUCTS RETURNED (3 REPEATS)", MONO, 9.5, MUTED)
    c.text(right + 0.2, c.y + 0.15, "KEPT", MONO, 9.5, MUTED)
    ax = c.axes(0.4, 3.3, left=left, right=right)
    for i, (label, cid, overlap) in enumerate(rows):
        counts = condition_counts(cid)
        lo, hi = min(counts), max(counts)
        ax.barh(i, lo, color=SAGE_DEEP if i == 0 else CHARCOAL, height=0.55)
        if hi != lo:
            ax.barh(i, hi - lo, left=lo, color=GRAY, height=0.55)
        ax.text(hi + 1.2, i, f"{lo}–{hi}" if hi != lo else f"{lo}", family=MONO, fontsize=11, color=BLACK, va="center")
        c.text(right + 0.2, c.y + 0.4 + 3.3 * (i + 0.5) / len(rows) + 0.06, "baseline" if overlap is None else f"{overlap:.1%}".replace(".0%", "%"),
               MONO, 11, MUTED if overlap is None else BLACK)
    ax.set_yticks(range(len(rows)), [r[0] for r in rows], fontsize=11.5)
    ax.set_ylim(len(rows) - 0.5, -0.5)
    ax.set_xlim(0, 80)
    bar_axes(ax)
    c.save("fig-taste-overlap")


# ---------------------------------------------------------------- 14 Same product, different seller
def fig_same_product():
    rows = []
    for pair, printed in zip(raw_tags["same_product_different_store"], [(0.550781, 0.710938), (0.593750, 0.683594), (0.746094, 0.792969)]):
        low, high = ((p["host"], p["seller_quality"], float(p["ranking_score"])) for p in (pair["lower"], pair["higher"]))
        expect(f"{pair['product']} scores", (low[2], high[2]), printed)
        rows.append((pair["product"], low, high))
    c = Canvas(14, "Same product, different seller, different score", 4.2,
               ["Raw-tags collection, repeat 1 · same product in the same search, matched by name · 27 September 2026"])
    ax = c.axes(0.1, 3.4, left=0.55, right=WIDTH - 0.5)
    for i, (label, low, high) in enumerate(rows):
        ax.text(0.2, i - 0.42, label, family=SERIF, fontsize=13.5, color=BLACK, weight="semibold")
        ax.plot([low[2], high[2]], [i, i], color=GRAY, lw=5, solid_capstyle="butt", zorder=1)
        for point, align, dx, fill in ((low, "right", -0.012, CHARCOAL), (high, "left", 0.012, SAGE)):
            ax.scatter([point[2]], [i], s=120, color=fill, ec=BLACK, lw=1.2, zorder=2)
            ax.text(point[2] + dx, i + 0.03, f"{point[0]} ({point[1]})\n{point[2]:.6f}", family=MONO, fontsize=10, color=BLACK,
                    ha=align, va="center", linespacing=1.3)
    ax.set_ylim(len(rows) - 0.45, -0.8)
    ax.set_xlim(0.2, 1.12)
    ax.set_yticks([])
    ax.set_xticks([0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    ax.set_xlabel("ranking_score", family=MONO, fontsize=10.5, labelpad=8)
    bar_axes(ax)
    c.save("fig-same-product-different-seller")


# ---------------------------------------------------------------- 15 Tail
def fig_tail_native():
    tail = raw_tags["tail_after_first_score_jump_repeat_1"]
    before = {True: tail["before_jump"].get("native", 0), False: tail["before_jump"].get("non_native", 0)}
    after = {True: tail["after_jump"].get("native", 0), False: tail["after_jump"].get("non_native", 0)}
    expect("lists with a jump", len(tail["lists_with_jump"]), 7)
    expect("before the jump (native, non-native)", (before[True], before[False]), (137, 169))
    expect("after the jump (native, non-native)", (after[True], after[False]), (0, 16))
    c = Canvas(15, "Products after the score jump are all non-native", 2.9,
               ["Raw-tags collection, repeat 1 · 7 lists with a jump (4 category, 3 product) · 27 September 2026"])
    c.text(2.5, c.y + 0.15, "■", MONO, 12, SAGE_DEEP)
    c.text(2.72, c.y + 0.15, "Native checkout: true", MONO, 10.5, CHARCOAL)
    c.text(5.0, c.y + 0.15, "■", MONO, 12, CHARCOAL)
    c.text(5.22, c.y + 0.15, "Native checkout: false", MONO, 10.5, CHARCOAL)
    ax = c.axes(0.4, 1.85, left=2.5, right=WIDTH - 0.5)
    for i, counts in enumerate((before, after)):
        total = counts[True] + counts[False]
        native_share = counts[True] / total
        ax.barh(i, native_share, color=SAGE_DEEP, height=0.55)
        ax.barh(i, 1 - native_share, left=native_share, color=CHARCOAL, height=0.55)
        if counts[True]:
            ax.text(native_share / 2, i, str(counts[True]), family=MONO, fontsize=13, color=BLACK, ha="center", va="center")
        ax.text(native_share + (1 - native_share) / 2, i, str(counts[False]), family=MONO, fontsize=13, color="white", ha="center", va="center")
    ax.set_yticks([0, 1], ["Before the jump\n(same lists)", "After the jump"], fontsize=12.5)
    ax.invert_yaxis()
    ax.set_xlim(0, 1)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1], ["0%", "25%", "50%", "75%", "100%"])
    bar_axes(ax)
    c.save("fig-tail-native")


for draw in (
    fig_how_muse_shops, fig_three_lists, fig_quince, fig_score_jumps, fig_hydro_flask,
    fig_requested_vs_returned, fig_query_combination, fig_five_dropout_points, fig_returned_vs_shown,
    fig_seller_quality_mix, fig_elite_gap, fig_taste_words, fig_taste_overlap, fig_same_product, fig_tail_native,
):
    draw()
