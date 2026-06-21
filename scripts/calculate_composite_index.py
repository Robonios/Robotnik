#!/usr/bin/env python3
"""
Robotnik Composite Index (RCI) — 75/25 public-equities / commodities blend
==========================================================================
The headline Composite: a periodically-rebalanced two-leg blend per the
Composite Index methodology.

    Composite_t = Composite_{t-1} * (1 + 0.75 * r_equities + 0.25 * r_commodities)

The 75/25 weights are RESET each period (periodic rebalancing) — they are applied
to each period's leg RETURNS, not held as drifting unit allocations.

Legs (both read-only; this script never recomputes a leg):
  - equities    : Public Equities series   (data/index/robotnik_index.json)
  - commodities : Commodities series        (data/index/commodities_index.json)

Marks. The blend is sampled at the WEEKLY end-of-week marks defined by the
commodities leg (the forward-only weekly series). The daily equity leg is
sampled at each mark by nearest-prior trading day (carry-forward).

FORWARD-ONLY. Base 1000.00 at the commodities launch (2026-06-17). The equity
leg's pre-launch history is NOT blended — the Composite has no pre-launch
series. Returns are only ever taken BETWEEN marks (all >= launch), so no
pre-2026 equity move can leak in. At genesis (one commodity point) the output
is a single 1000.00 point.

Output: data/index/composite_index.json   (this script does NOT git-commit)
Usage:  python scripts/calculate_composite_index.py
"""

import bisect
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX_DIR = ROOT / "data" / "index"
EQUITIES_PATH    = INDEX_DIR / "robotnik_index.json"        # Public Equities leg
COMMODITIES_PATH = INDEX_DIR / "commodities_index.json"     # Commodities leg
# Output path; a dry-run can redirect via COMPOSITE_INDEX_OUT (mirrors the family).
OUT_PATH = Path(os.environ.get("COMPOSITE_INDEX_OUT") or (INDEX_DIR / "composite_index.json"))

BASE_VALUE = 1000.0
W_EQUITIES    = 0.75
W_COMMODITIES = 0.25


def load(p):
    with open(p) as f:
        return json.load(f)


def blend_step(prev_value, r_eq, r_comm, w_eq=W_EQUITIES, w_comm=W_COMMODITIES):
    """One periodic-rebalance step: weights reset to (w_eq, w_comm) each period
    and applied to that period's leg returns. Pure function — unit-testable."""
    return prev_value * (1.0 + w_eq * r_eq + w_comm * r_comm)


def _series_map(series):
    """[{date,value}] -> (sorted_dates, {date: value})."""
    m = {str(p["date"])[:10]: float(p["value"])
         for p in series if p.get("value") is not None}
    return sorted(m), m


def sample_prior(dates, dmap, mark):
    """Value at the nearest-prior date <= mark (carry-forward); None if mark
    precedes the whole series."""
    i = bisect.bisect_right(dates, mark)
    return dmap[dates[i - 1]] if i > 0 else None


def build_series(eq, comm):
    """Build the forward-only blended series over the commodities weekly marks."""
    eq_dates, eq_map = _series_map(eq["series"])
    comm_dates, comm_map = _series_map(comm["series"])

    base_date = str(comm.get("base_date") or (comm_dates[0] if comm_dates else None))[:10]
    # Composite marks = commodities weekly marks at/after launch (forward-only).
    marks = [d for d in comm_dates if d >= base_date]

    series, missing = [], []
    composite = BASE_VALUE
    prev = None
    for k, mark in enumerate(marks):
        if k == 0:
            series.append({"date": mark, "value": round(composite, 2)})
            prev = mark
            continue
        eq_now, eq_prev = sample_prior(eq_dates, eq_map, mark), sample_prior(eq_dates, eq_map, prev)
        comm_now, comm_prev = comm_map.get(mark), comm_map.get(prev)
        r_eq = (eq_now / eq_prev - 1.0) if (eq_now and eq_prev) else 0.0
        r_comm = (comm_now / comm_prev - 1.0) if (comm_now and comm_prev) else 0.0
        if not (eq_now and eq_prev):
            missing.append(("equities", prev, mark))
        if not (comm_now and comm_prev):
            missing.append(("commodities", prev, mark))
        composite = blend_step(composite, r_eq, r_comm)
        series.append({"date": mark, "value": round(composite, 2)})
        prev = mark
    return series, base_date, missing


def main():
    eq = load(EQUITIES_PATH)
    comm = load(COMMODITIES_PATH)

    series, base_date, missing = build_series(eq, comm)
    if not series:
        print("ERROR: no commodities marks at/after launch — nothing to build", file=sys.stderr)
        sys.exit(1)

    record = {
        "name": "Robotnik Composite Index",
        "code": "RCI",
        "version": "1.0 — forward-only launch (genesis base)",
        "methodology": "Composite Index methodology — 75/25 public-equities / commodities blend",
        "method": ("Composite_t = Composite_{t-1} * (1 + 0.75*r_equities + 0.25*r_commodities); "
                   "75/25 weights reset each period (periodic rebalancing); weekly EOW marks from "
                   "the commodities leg; daily equity leg sampled nearest-prior; forward-only from "
                   "the commodities launch (no pre-launch equity history blended)"),
        "frequency": "weekly",
        "rebalancing": "periodic — weights reset to 75/25 each period",
        "weights": {"equities": W_EQUITIES, "commodities": W_COMMODITIES},
        "legs": {
            "equities": {"name": "Public Equities", "source": "data/index/robotnik_index.json",
                         "leg_current_value": eq.get("current_value"),
                         "leg_current_date": eq.get("current_date")},
            "commodities": {"name": comm.get("name", "Robotnik Commodities Index"),
                            "source": "data/index/commodities_index.json",
                            "leg_current_value": comm.get("current_value"),
                            "leg_current_date": comm.get("current_date")},
        },
        "base_date": base_date,
        "base_value": BASE_VALUE,
        "current_value": series[-1]["value"],
        "current_date": series[-1]["date"],
        "points": len(series),
        "forward_only": True,
        "series": series,
        "calculated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "") + "Z",
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(record, f, indent=2)

    # ── surface ──
    print("=" * 60)
    print("ROBOTNIK COMPOSITE INDEX (RCI) — 75/25 blend")
    print("=" * 60)
    print("  base: {} = {:.2f}   weights: {:.0%} equities / {:.0%} commodities".format(
        base_date, BASE_VALUE, W_EQUITIES, W_COMMODITIES))
    print("  legs: equities={} @ {} | commodities={} @ {}".format(
        eq.get("current_value"), eq.get("current_date"),
        comm.get("current_value"), comm.get("current_date")))
    print("  marks (weekly, forward-only): {}".format(len(series)))
    for pt in series[-5:]:
        print("    {}  {:.2f}".format(pt["date"], pt["value"]))
    if missing:
        print("  NOTE: leg samples missing on some marks (carried/zeroed): {}".format(missing[:5]))
    print("  current_value: {:.2f} @ {}".format(record["current_value"], record["current_date"]))
    try:
        shown = OUT_PATH.relative_to(ROOT)
    except ValueError:
        shown = OUT_PATH
    print("  wrote -> {}".format(shown))
    print("=" * 60)


if __name__ == "__main__":
    main()
