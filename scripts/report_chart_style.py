"""
Robotnik Report Chart Style — Locked Visual Template
====================================================
Single source of truth for every chart that appears in a Robotnik
quarterly report (Figures 1, 2, 3 of 1Q26, and every future figure).

Usage:
    from report_chart_style import apply_style, PALETTE, SIZE, save_report_chart
    apply_style()
    fig, ax = plt.subplots(figsize=SIZE)
    ax.plot(xs, ys, **PALETTE.composite_kw())
    save_report_chart(fig, 'chart_name.png')

Import this module BEFORE any matplotlib figure is created; the
apply_style() call mutates rcParams globally.
"""

from pathlib import Path
from types import SimpleNamespace

import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt


# ─────────────────────────────────────────────────────────────────────
# Fonts — Space Grotesk (titles/subtitles) + Mulish (everything else)
# ─────────────────────────────────────────────────────────────────────
# Bundled as TTFs in assets/fonts/ so every machine (laptop, CI, render
# server) renders identically. No dependency on system-installed fonts.

_FONT_DIR = (Path(__file__).resolve().parent.parent / "assets" / "fonts")

FONT_TITLE = "Space Grotesk"     # used for titles and subtitles
FONT_TEXT  = "Mulish"            # used for axis labels, ticks, legend, annotations

_fonts_registered = False

def _register_fonts() -> None:
    """Register bundled TTFs with matplotlib's FontManager. Idempotent."""
    global _fonts_registered
    if _fonts_registered:
        return
    if not _FONT_DIR.exists():
        return
    for ttf in _FONT_DIR.glob("*.ttf"):
        fm.fontManager.addfont(str(ttf))
    _fonts_registered = True


# FontProperties instances for per-element application (titles, subtitles)
def title_font(size=13, weight="bold"):
    _register_fonts()
    return fm.FontProperties(family=FONT_TITLE, size=size, weight=weight)


def subtitle_font(size=9.5, weight="regular"):
    _register_fonts()
    return fm.FontProperties(family=FONT_TITLE, size=size, weight=weight)


# ─────────────────────────────────────────────────────────────────────
# Canvas
# ─────────────────────────────────────────────────────────────────────

# 7" x 4.5" at 300 DPI → 2100 x 1350 px; aspect 1.556:1.  Print-friendly.
SIZE = (7.0, 4.5)
DPI = 300

# ─────────────────────────────────────────────────────────────────────
# Palette — Robotnik yellow as hero, muted secondaries
# ─────────────────────────────────────────────────────────────────────

PALETTE = SimpleNamespace(
    # Background + text
    paper="#FFFFFF",
    ink="#1A1F2B",
    axis="#374151",
    grid="#E5E7EB",

    # Hero line — Robotnik Composite (always)
    composite="#F5D921",

    # Base / reference line (index 100, etc.)
    base_ref="#9CA3AF",

    # Benchmarks (Figure 1 reference treatment)
    benchmarks={
        "SPY":  "#6B7280",   # S&P 500 — muted grey
        "QQQ":  "#60A5FA",   # NASDAQ — muted blue
        "SOXX": "#F87171",   # Philadelphia Semi Index — salmon
        "ROBO": "#6EE7B7",   # ROBO ETF — muted green
    },

    # Sub-indices (Figure 3 reference treatment).
    # Materials was amber (#FBBF24) but read too close to the hero Robotnik
    # yellow at chart scale. Swapped to muted violet so the four sub-index
    # colours all sit well away from yellow on the colour wheel, and away
    # from each other in luminance + hue — readable in grayscale too.
    subindices={
        "semiconductor": "#60A5FA",   # muted blue
        "robotics":      "#6EE7B7",   # muted green
        "space":         "#F87171",   # salmon
        "materials":     "#A78BFA",   # muted violet
    },

    # Annotation fill + border
    annotation_fill="#FFFFFF",
    annotation_border="#9CA3AF",
)


# Keyword-arg bundles for matplotlib plot() calls — keeps call sites short
def composite_kw(label=None):
    return dict(color=PALETTE.composite, linewidth=2.5, label=label,
                solid_capstyle="round", solid_joinstyle="round")


def secondary_kw(color, label=None):
    return dict(color=color, linewidth=1.5, label=label,
                solid_capstyle="round", solid_joinstyle="round")


def base_ref_kw():
    return dict(color=PALETTE.base_ref, linestyle="--", linewidth=0.7, alpha=0.8)


# ─────────────────────────────────────────────────────────────────────
# Global rcParams — call apply_style() before plotting
# ─────────────────────────────────────────────────────────────────────

def apply_style() -> None:
    """Configure matplotlib for Robotnik report charts.

    Safe to call multiple times (idempotent). Must be called before the
    first figure is created in each process.
    """
    _register_fonts()
    plt.rcParams.update({
        # Typography — Mulish is the default (body text, axis labels, ticks,
        # legend, annotations). Titles + subtitles are applied explicitly
        # via title_font() / subtitle_font() — use set_title(fontproperties=
        # title_font()) and fig.text(..., fontproperties=subtitle_font()).
        "font.family": "sans-serif",
        "font.sans-serif": [
            FONT_TEXT,           # Mulish — primary
            "Helvetica", "Arial", "Liberation Sans",
            "DejaVu Sans", "sans-serif",
        ],

        # Figure + axes
        "figure.facecolor": PALETTE.paper,
        "axes.facecolor":   PALETTE.paper,
        "axes.edgecolor":   PALETTE.axis,
        "axes.linewidth":   0.8,
        "axes.labelcolor":  PALETTE.axis,
        "axes.labelsize":   10,
        "axes.titlesize":   13,
        "axes.titleweight": "bold",
        "axes.titlecolor":  PALETTE.ink,
        "axes.titlepad":    18,   # generous pad so title doesn't collide with anything

        # Spines — hide top+right
        "axes.spines.top":   False,
        "axes.spines.right": False,

        # Ticks
        "xtick.color":      PALETTE.axis,
        "ytick.color":      PALETTE.axis,
        "xtick.labelsize":  9,
        "ytick.labelsize":  9,
        "xtick.direction":  "out",
        "ytick.direction":  "out",

        # Grid
        "axes.grid":         True,
        "axes.axisbelow":    True,
        "grid.color":        PALETTE.grid,
        "grid.linewidth":    0.5,
        "grid.alpha":        1.0,

        # Legend — top-left, no heavy frame
        "legend.loc":         "upper left",
        "legend.fontsize":    10,
        "legend.frameon":     True,
        "legend.framealpha":  0.92,
        "legend.facecolor":   PALETTE.paper,
        "legend.edgecolor":   PALETTE.grid,
        "legend.borderpad":   0.6,
        "legend.labelspacing": 0.4,

        # Text
        "text.color": PALETTE.ink,

        # Saving
        "savefig.facecolor": PALETTE.paper,
        "savefig.dpi":       DPI,
        "savefig.bbox":      "tight",
    })


# ─────────────────────────────────────────────────────────────────────
# Annotation helper — pill box + leader line
# ─────────────────────────────────────────────────────────────────────

def annotate_event(ax, x, y, label, yoff, xoff=0, fontsize=9):
    """Anchor a dark-text white-pill annotation at (x, y) with leader line.

    yoff is in data units on the y-axis. Positive = above, negative = below.
    Stagger yoff across neighbouring annotations to avoid collisions —
    callers own the layout decisions.
    """
    ax.annotate(
        label,
        xy=(x, y),
        xytext=(x + xoff if xoff else x, y + yoff),
        ha="center",
        va="center",
        fontsize=fontsize,
        color=PALETTE.ink,
        bbox=dict(
            boxstyle="round,pad=0.32",
            fc=PALETTE.annotation_fill,
            ec=PALETTE.annotation_border,
            lw=0.6,
        ),
        arrowprops=dict(
            arrowstyle="-",
            color=PALETTE.annotation_border,
            lw=0.7,
            shrinkA=3,
            shrinkB=3,
        ),
    )
    ax.scatter([x], [y], s=18, color=PALETTE.ink, zorder=6,
               edgecolor=PALETTE.paper, linewidth=1.1)


# ─────────────────────────────────────────────────────────────────────
# Save helper
# ─────────────────────────────────────────────────────────────────────

def save_report_chart(fig, path):
    """Save a matplotlib figure at 300 DPI with white background."""
    fig.savefig(path, dpi=DPI, bbox_inches="tight", facecolor=PALETTE.paper)
    return path
