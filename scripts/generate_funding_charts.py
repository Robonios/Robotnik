"""
Generate Q1 2026 funding report charts using the locked visual template.

Outputs:
  - data/exports/report_charts/chart_q1_funding_breakdown.png  (donut)
  - data/exports/report_charts/chart_funding_trends.png         (monthly stacked bars)

Dataset: data/funding/rounds.json
Filters applied:
  - Exclude 'Token' sector (not part of frontier stack narrative).
  - Exclude Nth Cycle $1.1bn Mar 2026 entry — reclassified as offtake
    agreement with Trafigura per Section 1 verification, not a funding round.
"""

import json
from collections import defaultdict
from datetime import date
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from report_chart_style import (
    PALETTE, SIZE, DPI,
    apply_style, save_report_chart,
    title_font, subtitle_font,
)


ROOT = Path(__file__).resolve().parent.parent
ROUNDS_FILE = ROOT / "data" / "funding" / "rounds.json"
OUT_DIR = ROOT / "data" / "exports" / "report_charts"

# Sector order, labels, and colours — aligned with Figures 2 & 3 locked template.
# Materials uses the muted violet from PALETTE.subindices (was amber, swapped to
# avoid collision with the hero Robotnik yellow at chart scale).
SECTOR_ORDER = ["Robotics", "Semiconductors", "Space", "Materials"]
SECTOR_COLORS = {
    "Robotics":       PALETTE.subindices["robotics"],       # muted green
    "Semiconductors": PALETTE.subindices["semiconductor"],  # muted blue
    "Space":          PALETTE.subindices["space"],          # salmon
    "Materials":      PALETTE.subindices["materials"],      # muted violet
}


def load_rounds():
    with open(ROUNDS_FILE) as f:
        data = json.load(f)
    kept = []
    for r in data["rounds"]:
        sector = (r.get("sector") or "")
        if sector.lower() in ("token", "tokens"):
            continue
        if (r.get("company") or "").strip().lower() == "nth cycle":
            continue
        kept.append(r)
    return kept


def donut_chart(rounds, out_path):
    """Chart A — Q1 2026 Funding by Sector (donut)."""
    q1 = [r for r in rounds if r.get("quarter") == "1Q26"]

    totals = defaultdict(float)
    counts = defaultdict(int)
    for r in q1:
        totals[r["sector"]] += r.get("amount_m") or 0
        counts[r["sector"]] += 1

    grand_total = sum(totals.values())
    grand_count = sum(counts.values())

    sizes  = [totals[s]   for s in SECTOR_ORDER]
    labels = SECTOR_ORDER
    colors = [SECTOR_COLORS[s] for s in SECTOR_ORDER]

    fig, ax = plt.subplots(figsize=SIZE)
    fig.subplots_adjust(top=0.82, bottom=0.08, left=0.02, right=0.62)

    wedges, _ = ax.pie(
        sizes,
        colors=colors,
        startangle=90,
        counterclock=False,
        wedgeprops=dict(width=0.38, edgecolor=PALETTE.paper, linewidth=2.0),
    )

    # Centre total
    ax.text(0, 0.10, f"${grand_total/1000:.1f}bn",
            ha="center", va="center",
            fontsize=22, fontweight="bold", color=PALETTE.ink,
            fontproperties=title_font(size=22))
    ax.text(0, -0.12, f"{grand_count} rounds",
            ha="center", va="center",
            fontsize=10, color=PALETTE.axis)
    ax.text(0, -0.28, "Q1 2026",
            ha="center", va="center",
            fontsize=9, color=PALETTE.axis)

    # Legend with sector, rounds, capital, share
    legend_handles = []
    for s in SECTOR_ORDER:
        share = (totals[s] / grand_total) * 100 if grand_total else 0
        label = f"{s}\n{counts[s]} rounds · ${totals[s]/1000:.2f}bn · {share:.1f}%"
        legend_handles.append(mpatches.Patch(color=SECTOR_COLORS[s], label=label))

    ax.legend(
        handles=legend_handles,
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        frameon=False,
        fontsize=9,
        handlelength=1.2,
        handleheight=1.2,
        labelspacing=1.1,
    )

    # Title + subtitle — Space Grotesk
    fig.suptitle("Figure 4 — Q1 2026 Funding by Sector",
                 x=0.5, y=0.96, ha="center",
                 fontproperties=title_font(size=13),
                 color=PALETTE.ink)
    fig.text(0.5, 0.90,
             "Frontier stack private funding, capital ($bn) · excludes Nth Cycle offtake",
             ha="center", fontproperties=subtitle_font(size=9.5),
             color=PALETTE.axis)

    ax.set(aspect="equal")
    ax.axis("off")

    save_report_chart(fig, out_path)
    plt.close(fig)
    return {s: (counts[s], totals[s]) for s in SECTOR_ORDER}


def monthly_stacked_bars(rounds, out_path):
    """Chart B — Frontier Stack Monthly Funding (Jan 2025 – latest)."""
    # Month buckets, 2025-01 through latest month present.
    months = []
    y, m = 2025, 1
    end_y, end_m = 2026, 3   # report window ends at Q1 2026
    while (y, m) <= (end_y, end_m):
        months.append((y, m))
        m += 1
        if m == 13:
            m = 1; y += 1

    def bucket(d):
        if not d: return None
        yy, mm = int(d[:4]), int(d[5:7])
        return (yy, mm)

    # sector -> list of capital_m aligned with months
    data = {s: [0.0] * len(months) for s in SECTOR_ORDER}
    idx = {m: i for i, m in enumerate(months)}

    for r in rounds:
        b = bucket(r.get("date"))
        if b not in idx:
            continue
        s = r.get("sector")
        if s not in data:
            continue
        data[s][idx[b]] += (r.get("amount_m") or 0) / 1000.0   # $bn

    apply_style()  # no-op if already applied, but safe
    fig, ax = plt.subplots(figsize=SIZE)
    fig.subplots_adjust(top=0.82, bottom=0.18, left=0.08, right=0.97)

    x = list(range(len(months)))
    bottom = [0.0] * len(months)
    for s in SECTOR_ORDER:
        ax.bar(
            x, data[s],
            bottom=bottom,
            color=SECTOR_COLORS[s],
            edgecolor=PALETTE.paper,
            linewidth=0.5,
            width=0.78,
            label=s,
        )
        bottom = [b + v for b, v in zip(bottom, data[s])]

    # X axis labels: "Jan 25", "Feb 25", ... quarter separators are implicit.
    labels = []
    for (yy, mm) in months:
        labels.append(f"{date(yy, mm, 1).strftime('%b')} {str(yy)[-2:]}")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)

    ax.set_ylabel("Capital raised ($bn)", fontsize=10, color=PALETTE.axis)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"${v:.0f}bn"))

    ymax = max(bottom) * 1.15
    ax.set_ylim(0, ymax)
    ax.set_xlim(-0.7, len(months) - 0.3)

    # Titles — Space Grotesk
    fig.suptitle("Figure 5 — Frontier Stack Monthly Funding, 2025–2026",
                 x=0.5, y=0.96, ha="center",
                 fontproperties=title_font(size=13),
                 color=PALETTE.ink)
    fig.text(0.5, 0.90,
             "Monthly capital raised by sector ($bn) · excludes Nth Cycle offtake",
             ha="center", fontproperties=subtitle_font(size=9.5),
             color=PALETTE.axis)

    # Legend — horizontal at top, under subtitle
    leg = ax.legend(
        loc="upper right",
        ncol=4,
        frameon=True,
        framealpha=0.92,
        edgecolor=PALETTE.grid,
        facecolor=PALETTE.paper,
        fontsize=9,
        columnspacing=1.4,
        handlelength=1.2,
        handleheight=1.0,
    )

    save_report_chart(fig, out_path)
    plt.close(fig)

    # Return per-month totals for sanity check
    totals_by_month = {m: sum(data[s][i] for s in SECTOR_ORDER) for i, m in enumerate(months)}
    return totals_by_month


def main():
    apply_style()
    rounds = load_rounds()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    donut_totals = donut_chart(rounds, OUT_DIR / "chart_q1_funding_breakdown.png")
    monthly_totals = monthly_stacked_bars(rounds, OUT_DIR / "chart_funding_trends.png")

    print("Q1 2026 donut totals (excl Tokens, excl Nth Cycle):")
    total = 0
    for s, (n, cap) in donut_totals.items():
        print(f"  {s:<16} n={n:>3}  cap=${cap/1000:.3f}bn")
        total += cap
    print(f"  TOTAL            n={sum(n for n,_ in donut_totals.values()):>3}  cap=${total/1000:.3f}bn")

    print("\nMonthly totals ($bn):")
    for (y, m), v in monthly_totals.items():
        print(f"  {y}-{m:02d}  ${v:.2f}bn")


if __name__ == "__main__":
    main()
