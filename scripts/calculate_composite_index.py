#!/usr/bin/env python3
"""
Robotnik Composite Index (RCI) — 75/25 public-equities / commodities blend
==========================================================================
The headline Composite: a periodically-rebalanced two-leg blend per the
Composite Index methodology, built FORWARD-APPEND (one new weekly point per run;
prior points are never recomputed).

    Composite_t = Composite_{t-1} * (1 + 0.75 * r_equities + 0.25 * r_commodities)

The 75/25 weights are RESET each period (periodic rebalancing) — applied to each
period's leg RETURNS, not held as drifting unit allocations.

Legs (both read-only; this script never recomputes a leg):
  - equities    : Public Equities series   (data/index/robotnik_index.json)
  - commodities : Commodities series        (data/index/commodities_index.json)

Marks. The blend advances on the WEEKLY mark defined by the commodities leg (its
latest forward-only point). The daily equity leg is sampled at each mark by
nearest-prior trading day. To stay no-recompute even if the equity series
restates a past value, each composite point STORES its leg samples (eq_leg,
comm_leg); the next period's return is taken from the prior point's FROZEN
samples, not by re-sampling history.

Idempotency. A re-run within the same ISO week updates that week's point in
place (recomputed from the prior week's frozen point); it never double-appends,
and the base point is immutable.

FORWARD-ONLY. Base 1000.00 at the commodities launch (2026-06-17). Returns are
only taken BETWEEN marks (all >= launch), so no pre-2026 equity move can leak
in. At genesis (one commodity point) the output is a single 1000.00 point.

Output: data/index/composite_index.json   (this script does NOT git-commit)
Usage / env affordances
    python scripts/calculate_composite_index.py
    COMPOSITE_INDEX_OUT=<path>          read-and-write this record elsewhere (dry-run)
    COMPOSITE_EQUITIES_PATH=<path>      override the equity leg source (sim/test)
    COMPOSITE_COMMODITIES_PATH=<path>   override the commodities leg source (sim/test)
"""

import bisect
import json
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX_DIR = ROOT / "data" / "index"
EQUITIES_PATH    = Path(os.environ.get("COMPOSITE_EQUITIES_PATH")
                        or (INDEX_DIR / "robotnik_index.json"))        # Public Equities leg
COMMODITIES_PATH = Path(os.environ.get("COMPOSITE_COMMODITIES_PATH")
                        or (INDEX_DIR / "commodities_index.json"))     # Commodities leg
OUT_PATH = Path(os.environ.get("COMPOSITE_INDEX_OUT") or (INDEX_DIR / "composite_index.json"))

BASE_VALUE    = 1000.0
W_EQUITIES    = 0.75
W_COMMODITIES = 0.25


def load(p):
    with open(p) as f:
        return json.load(f)


def load_existing(p):
    try:
        return json.loads(Path(p).read_text())
    except Exception:
        return None


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


def _iso_week(d):
    y, m, dd = map(int, str(d)[:10].split("-"))
    return date(y, m, dd).isocalendar()[:2]


def advance(prior, eq, comm):
    """Forward-append one weekly composite point. Returns (series, base_date,
    action, info). The base point is immutable; leg samples are frozen on each
    point so prior points never need re-derivation."""
    eq_dates, eq_map = _series_map(eq["series"])
    comm_dates, comm_map = _series_map(comm["series"])
    base_date = str(comm.get("base_date") or (comm_dates[0] if comm_dates else None))[:10]

    # GENESIS — single base point at the commodities launch, with leg samples.
    if not prior or not prior.get("series"):
        eq0 = sample_prior(eq_dates, eq_map, base_date)
        comm0 = comm_map.get(base_date) or sample_prior(comm_dates, comm_map, base_date)
        series = [{"date": base_date, "value": round(BASE_VALUE, 2),
                   "eq_leg": eq0, "comm_leg": comm0}]
        return series, base_date, "genesis", {"eq_leg": eq0, "comm_leg": comm0}

    series = [dict(p) for p in prior["series"]]
    new_mark = comm_dates[-1] if comm_dates else base_date
    last = series[-1]
    last_in_week = (last["date"] != base_date) and (_iso_week(last["date"]) == _iso_week(new_mark))

    # No genuinely new commodities mark and not a same-week re-run → nothing to do.
    if new_mark <= last["date"] and not last_in_week:
        return series, base_date, "no-op (no new commodities mark)", {}

    # Anchor = the prior-week point (series[-2] on a same-week re-run, else the last point).
    anchor = series[-2] if (last_in_week and len(series) >= 2) else last

    a_eq = anchor.get("eq_leg")
    if a_eq is None:
        a_eq = sample_prior(eq_dates, eq_map, anchor["date"]); anchor["eq_leg"] = a_eq   # freeze
    a_comm = anchor.get("comm_leg")
    if a_comm is None:
        a_comm = comm_map.get(anchor["date"]) or sample_prior(comm_dates, comm_map, anchor["date"])
        anchor["comm_leg"] = a_comm                                                       # freeze

    n_eq = sample_prior(eq_dates, eq_map, new_mark)
    n_comm = comm_map.get(new_mark) or sample_prior(comm_dates, comm_map, new_mark)
    r_eq = (n_eq / a_eq - 1.0) if (n_eq and a_eq) else 0.0
    r_comm = (n_comm / a_comm - 1.0) if (n_comm and a_comm) else 0.0
    new_value = round(blend_step(anchor["value"], r_eq, r_comm), 2)
    pt = {"date": new_mark, "value": new_value, "eq_leg": n_eq, "comm_leg": n_comm}

    if last_in_week:
        series[-1] = pt
        action = "updated-in-place (current week re-run)"
    else:
        series.append(pt)
        action = "appended"
    info = {"anchor_date": anchor["date"], "mark": new_mark,
            "r_eq_pct": round(r_eq * 100, 4), "r_comm_pct": round(r_comm * 100, 4),
            "eq_anchor": a_eq, "eq_now": n_eq, "comm_anchor": a_comm, "comm_now": n_comm}
    return series, base_date, action, info


def main():
    eq = load(EQUITIES_PATH)
    comm = load(COMMODITIES_PATH)
    prior = load_existing(OUT_PATH)

    series, base_date, action, info = advance(prior, eq, comm)
    if not series:
        print("ERROR: no commodities marks at/after launch — nothing to build", file=sys.stderr)
        sys.exit(1)
    now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "") + "Z"

    if prior and prior.get("series"):
        record = dict(prior)                 # carry genesis-fixed metadata
    else:
        record = {
            "name": "Robotnik Composite Index",
            "code": "RCI",
            "version": "1.0 — forward-only launch (genesis base)",
            "methodology": "Composite Index methodology — 75/25 public-equities / commodities blend",
            "method": ("Composite_t = Composite_{t-1} * (1 + 0.75*r_equities + 0.25*r_commodities); "
                       "75/25 weights reset each period (periodic rebalancing); weekly marks from the "
                       "commodities leg; daily equity leg sampled nearest-prior; leg samples frozen per "
                       "point (no-recompute); forward-only from the commodities launch"),
            "frequency": "weekly",
            "rebalancing": "periodic — weights reset to 75/25 each period",
            "weights": {"equities": W_EQUITIES, "commodities": W_COMMODITIES},
            "forward_only": True,
        }
    record["legs"] = {
        "equities": {"name": "Public Equities", "source": "data/index/robotnik_index.json",
                     "leg_current_value": eq.get("current_value"), "leg_current_date": eq.get("current_date")},
        "commodities": {"name": comm.get("name", "Robotnik Commodities Index"),
                        "source": "data/index/commodities_index.json",
                        "leg_current_value": comm.get("current_value"), "leg_current_date": comm.get("current_date")},
    }
    record["base_date"] = base_date
    record["base_value"] = BASE_VALUE
    record["current_value"] = series[-1]["value"]
    record["current_date"] = series[-1]["date"]
    record["points"] = len(series)
    record["series"] = series
    record["last_update"] = {"action": action, "at": now_iso, **info}
    record["calculated_at"] = now_iso

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(record, f, indent=2)

    # ── surface ──
    print("=" * 60)
    print("ROBOTNIK COMPOSITE INDEX (RCI) — 75/25 blend")
    print("=" * 60)
    print("  base: {} = {:.2f}   weights: {:.0%} eq / {:.0%} comm".format(
        base_date, BASE_VALUE, W_EQUITIES, W_COMMODITIES))
    print("  legs: equities={} @ {} | commodities={} @ {}".format(
        eq.get("current_value"), eq.get("current_date"),
        comm.get("current_value"), comm.get("current_date")))
    print("  action: {}".format(action))
    if info.get("anchor_date"):
        print("  return: from {} -> {}: r_eq={:+.4f}%  r_comm={:+.4f}%  (eq {}->{}, comm {}->{})".format(
            info["anchor_date"], info["mark"], info["r_eq_pct"], info["r_comm_pct"],
            info["eq_anchor"], info["eq_now"], info["comm_anchor"], info["comm_now"]))
    print("  points: {}".format(len(series)))
    for pt in series[-5:]:
        print("    {}  {:.2f}".format(pt["date"], pt["value"]))
    print("  current_value: {:.2f} @ {}".format(record["current_value"], record["current_date"]))
    try:
        shown = OUT_PATH.relative_to(ROOT)
    except ValueError:
        shown = OUT_PATH
    print("  wrote -> {}".format(shown))
    print("=" * 60)


if __name__ == "__main__":
    main()
