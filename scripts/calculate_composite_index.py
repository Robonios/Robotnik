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
latest forward-only point). Each weekly return takes BOTH ends from the legs'
current series: the daily equity leg at its nearest-prior trading day on or before
each mark, the commodities leg at the mark. A published point is never recomputed,
so a later restatement of a leg cannot move it; and since both ends of a return
come from the same series, a restatement at the prior mark cannot pass into the
next return either. Each point stores the leg levels it was struck from (eq_leg,
comm_leg) and the prior-mark levels its return was taken from (eq_anchor,
comm_anchor).

Version 1.0 took each return from the samples stored on the prior point, so a
restatement of Public Equities at the prior mark passed into the next return as a
move that did not happen. On adopting version 1.1 the record is recomputed once,
at the marks already published, from the current series (REBUILD_ON_ADOPTION);
after that it is forward-only again.

Idempotency. A re-run within the same ISO week updates that week's point in
place (recomputed from the prior week's point); it never double-appends, and the
base point is immutable.

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
sys.path.insert(0, str(ROOT / "scripts"))
from currency_convert import PRIOR_FILL_WARN_DAYS  # noqa: E402 — reuse the FX staleness threshold (7d); don't invent a new one
EQUITIES_PATH    = Path(os.environ.get("COMPOSITE_EQUITIES_PATH")
                        or (INDEX_DIR / "robotnik_index.json"))        # Public Equities leg
COMMODITIES_PATH = Path(os.environ.get("COMPOSITE_COMMODITIES_PATH")
                        or (INDEX_DIR / "commodities_index.json"))     # Commodities leg
OUT_PATH = Path(os.environ.get("COMPOSITE_INDEX_OUT") or (INDEX_DIR / "composite_index.json"))

BASE_VALUE    = 1000.0
W_EQUITIES    = 0.75
W_COMMODITIES = 0.25

VERSION = "1.1"
VERSION_LABEL = "1.1: each weekly return taken from the current leg series at both marks"
METHOD = ("Composite_t = Composite_{t-1} * (1 + 0.75*r_equities + 0.25*r_commodities); "
          "75/25 weights reset each period (periodic rebalancing); weekly marks from the "
          "commodities leg; daily equity leg sampled nearest-prior; both ends of each return "
          "taken from the current leg series; published points never recomputed; forward-only "
          "from the commodities launch")
# Recompute the published points once when the stored record predates VERSION (the
# one-time restatement on adopting 1.1). Set False to keep earlier points as published.
REBUILD_ON_ADOPTION = True


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
    action, info). The base point is immutable, published points are never
    recomputed, and each point stores the leg levels its return was taken from."""
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

    # Both ends of the return come from the legs' current series, so a restatement of a
    # leg at the anchor mark cannot pass into this return. The anchor point itself, like
    # every published point, is left as it is.
    a_eq = sample_prior(eq_dates, eq_map, anchor["date"])
    a_comm = comm_map.get(anchor["date"]) or sample_prior(comm_dates, comm_map, anchor["date"])

    n_eq = sample_prior(eq_dates, eq_map, new_mark)
    # Equity-leg staleness warning (mirror commodities FX PRIOR_FILL_WARN_DAYS): the
    # new-mark sample carries forward the nearest-prior equity date; warn, never raise,
    # continuity is preserved, if that date is stale beyond the threshold. The anchor
    # mark is a past date the series has already passed, so only the new mark needs it.
    _ni = bisect.bisect_right(eq_dates, new_mark)
    if _ni > 0:
        _eq_date = eq_dates[_ni - 1]
        _gap = (date.fromisoformat(new_mark) - date.fromisoformat(_eq_date)).days
        if _gap > PRIOR_FILL_WARN_DAYS:
            sys.stderr.write("[composite] WARN: equity leg stale — sampled {} for mark {} "
                             "({}d gap > {}d); appending as normal\n".format(
                                 _eq_date, new_mark, _gap, PRIOR_FILL_WARN_DAYS))
    n_comm = comm_map.get(new_mark) or sample_prior(comm_dates, comm_map, new_mark)
    r_eq = (n_eq / a_eq - 1.0) if (n_eq and a_eq) else 0.0
    r_comm = (n_comm / a_comm - 1.0) if (n_comm and a_comm) else 0.0
    new_value = round(blend_step(anchor["value"], r_eq, r_comm), 2)
    pt = {"date": new_mark, "value": new_value, "eq_leg": n_eq, "comm_leg": n_comm,
          "eq_anchor": a_eq, "comm_anchor": a_comm}

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


def rebuild(points, eq, comm):
    """Recompute every published point at its own mark from the legs' current series:
    the one-time restatement on adopting VERSION. The marks are the dates already
    published, and the base point stays at BASE_VALUE."""
    eq_dates, eq_map = _series_map(eq["series"])
    comm_dates, comm_map = _series_map(comm["series"])
    out = []
    for p in points:
        m = p["date"]
        e = sample_prior(eq_dates, eq_map, m)
        c = comm_map.get(m) or sample_prior(comm_dates, comm_map, m)
        if not out:
            out.append({"date": m, "value": round(BASE_VALUE, 2), "eq_leg": e, "comm_leg": c})
            continue
        a = out[-1]
        r_eq = (e / a["eq_leg"] - 1.0) if (e and a["eq_leg"]) else 0.0
        r_comm = (c / a["comm_leg"] - 1.0) if (c and a["comm_leg"]) else 0.0
        out.append({"date": m, "value": round(blend_step(a["value"], r_eq, r_comm), 2),
                    "eq_leg": e, "comm_leg": c, "eq_anchor": a["eq_leg"], "comm_anchor": a["comm_leg"]})
    return out


def main():
    eq = load(EQUITIES_PATH)
    comm = load(COMMODITIES_PATH)
    prior = load_existing(OUT_PATH)

    restated = None
    if (REBUILD_ON_ADOPTION and prior and prior.get("series")
            and not str(prior.get("version", "")).startswith(VERSION)):
        before = prior["series"][-1]
        prior = dict(prior)
        prior["series"] = rebuild(prior["series"], eq, comm)
        after = prior["series"][-1]
        restated = {"from_version": prior.get("version"), "to_version": VERSION,
                    "points": len(prior["series"]), "date": before["date"],
                    "value_before": before["value"], "value_after": after["value"],
                    "at": datetime.now(timezone.utc).isoformat().replace("+00:00", "") + "Z"}

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
            "methodology": "Composite Index methodology — 75/25 public-equities / commodities blend",
            "frequency": "weekly",
            "rebalancing": "periodic — weights reset to 75/25 each period",
            "weights": {"equities": W_EQUITIES, "commodities": W_COMMODITIES},
            "forward_only": True,
        }
    record["version"] = VERSION_LABEL
    record["method"] = METHOD
    if restated:
        record["restatement"] = restated
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
    if restated:
        print("  restated once on adopting version {}: {} points; {} {:.2f} -> {:.2f}".format(
            VERSION, restated["points"], restated["date"], restated["value_before"],
            restated["value_after"]))
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
