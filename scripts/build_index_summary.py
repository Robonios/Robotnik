#!/usr/bin/env python3
"""
Single writer of data/index/index_summary.json — the read-only contract the home
page consumes for the Index Family + Sector Performance.

THE WRITER IS A READER. It reads the PUBLISHED series only and NEVER recomputes
the index:
  - `value` / `as_of` / `base` come straight from the published files (verbatim),
  - `series` is a slice of the published series (verbatim points),
  - `returns` are derived from the published series VALUES by nearest-prior-
    trading-day anchoring (anchor = latest series date <= as_of - P) — arithmetic
    on already-published numbers, the one derivation the site delegates here so it
    never computes. This is NOT a re-derivation of the index.

Sources (the only inputs):
  data/index/robotnik_index.json              -> Public Equities (equities-only, live)
  data/index/composite_index.json             -> Composite 75/25 blend (weekly, live)
  data/index/commodities_index.json           -> Commodities (weekly, forward-only, live)
  data/index/bottleneck_weighted_composite.json -> Bottleneck-Weighted (live)
  data/index/sub_indices.json                 -> Space/Robotics/Semiconductors/Materials (live)
  data/index/private_capital_index.json       -> RPCI (monthly, live; 2023 calibration excluded)

The trading-day axis is each series' OWN published dates (produced by
index_dates.py via calculate_index), so the summary cannot drift from the series.
SUB_INDEX_FLOOR is imported from index_dates purely to stamp span.floor.

Run:  python3 scripts/build_index_summary.py        (writes index_summary.json)
"""
import bisect
import calendar
import json
import os
import sys
from datetime import date, datetime, timedelta, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
INDEX_DIR = os.path.join(ROOT_DIR, "data", "index")
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
from index_dates import SUB_INDEX_FLOOR  # noqa: E402

OUT_PATH        = os.path.join(INDEX_DIR, "index_summary.json")
COMPOSITE_PATH  = os.path.join(INDEX_DIR, "robotnik_index.json")        # equities book -> Public Equities
BOTTLENECK_PATH = os.path.join(INDEX_DIR, "bottleneck_weighted_composite.json")
SUB_PATH        = os.path.join(INDEX_DIR, "sub_indices.json")
RPCI_PATH       = os.path.join(INDEX_DIR, "private_capital_index.json")
COMMODITIES_PATH     = os.path.join(INDEX_DIR, "commodities_index.json")   # Commodities (weekly) -> live
COMPOSITE_BLEND_PATH = os.path.join(INDEX_DIR, "composite_index.json")     # Composite 75/25 blend (weekly) -> live

RETURN_CONVENTION = ("nearest-prior-trading-day; per period P the anchor is the latest "
                     "published series date <= (as_of - P); return = (value/anchor - 1) * 100, "
                     "rounded to 2dp; daily P in {1W=7d,1M,3M,1Y,3Y,5Y}, monthly RPCI in {1M,3M,1Y,3Y,5Y}")
TRADING_DAY_CONVENTION = ("as_of is the latest session in the published series — already the "
                          ">=50% / 98-of-197 quorum trading day from index_dates.py; the summary "
                          "anchors returns on the series' own dates, so it cannot drift from it")
FRESHNESS_RULE = ("status='live' when the data (fresh_through) is current at the entry's OWN cadence "
                  "relative to the run date (as_of), else 'stale': daily within 4 days, weekly within "
                  "9 days, monthly within one calendar month (current or prior month live; two or more "
                  "months behind stale). A 'stale' entry still carries its last value and fresh_through "
                  "date and must be rendered as DELAYED - a real number with its age - not as a current "
                  "value and not as calibrating.")


def load(p):
    with open(p) as f:
        return json.load(f)


# ── date helpers ─────────────────────────────────────────────────────────
def _d(s):
    y, m, dd = map(int, str(s)[:10].split("-"))
    return date(y, m, dd)


def _months_before(d, n):
    m = d.month - n
    y = d.year + (m - 1) // 12
    m = (m - 1) % 12 + 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def _years_before(d, n):
    return date(d.year - n, d.month, min(d.day, calendar.monthrange(d.year - n, d.month)[1]))


def _ym_before(ym, n):
    y, m = map(int, ym.split("-"))
    m -= n
    y += (m - 1) // 12
    m = (m - 1) % 12 + 1
    return "%04d-%02d" % (y, m)


DAILY_PERIODS = [
    ("1W", lambda d: d - timedelta(days=7)),
    ("1M", lambda d: _months_before(d, 1)),
    ("3M", lambda d: _months_before(d, 3)),
    ("1Y", lambda d: _years_before(d, 1)),
    ("3Y", lambda d: _years_before(d, 3)),
    ("5Y", lambda d: _years_before(d, 5)),
]


def daily_returns(series):
    """Nearest-prior-trading-day returns computed on the series' OWN dates."""
    dv = {_d(p["date"]): float(p["value"]) for p in series}
    ds = sorted(dv)
    latest, lv = ds[-1], dv[ds[-1]]
    out = {}
    for name, fn in DAILY_PERIODS:
        i = bisect.bisect_right(ds, fn(latest))
        if i == 0:
            out[name] = {"null": True, "reason": "insufficient_history"}
        else:
            out[name] = round((lv / dv[ds[i - 1]] - 1) * 100, 2)
    return out


def trailing_1y_daily(series):
    """Verbatim slice: the nearest-prior-1Y anchor onward (>= 1Y of daily points)."""
    ds = [_d(p["date"]) for p in series]
    j = bisect.bisect_right(ds, _years_before(ds[-1], 1))
    return [{"date": p["date"], "value": p["value"]} for p in series[max(0, j - 1):]]


def compute_status(cadence, fresh_through, run_date):
    """Cadence-aware freshness verdict: 'live' when the data (fresh_through) is current
    at the entry's OWN cadence relative to the run date, else 'stale'. This is what
    "fresh_through == as_of at the native cadence" actually means - an exact date match
    is wrong, because data legitimately lags the run at every cadence (a daily close is
    the prior session, a weekly mark is last Saturday, a monthly mark is last month), so
    exact equality would read every index stale on every normal day. Tolerances:
      daily   <= 4 days   -- a Fri session read the following Mon/Tue over a holiday is
                             ~3-4d; >4d means a weekday feed actually died (matches the
                             staleness-monitor daily bucket).
      weekly  <= 9 days   -- 7d cadence + 2d margin: a forward-only weekly index holds its
                             Saturday mark until the next Saturday; >9d means a weekly run
                             was missed.
      monthly <= 1 month  -- compared at MONTH granularity, not days: the prior month's
                             mark is current until the next month publishes, and RPCI is
                             an irregular manual sweep, so 0-1 months behind is live; a
                             day-based tolerance would read a normal mid-month RPCI stale.
                             >=2 months behind is a genuinely skipped sweep.
    """
    if fresh_through is None:
        return "live"
    if cadence == "monthly":
        fy, fm = map(int, str(fresh_through)[:7].split("-"))
        months_behind = (run_date.year * 12 + run_date.month) - (fy * 12 + fm)
        return "live" if months_behind <= 1 else "stale"
    gap = (run_date - _d(fresh_through)).days
    return "live" if gap <= (9 if cadence == "weekly" else 4) else "stale"


def daily_entry(name, value, series, base, run_date, entity_count=None, code=None):
    fresh_through = series[-1]["date"]           # latest session present in the data
    e = {
        "name": name, "status": compute_status("daily", fresh_through, run_date),
        "cadence": "daily",
        "value": value, "as_of": str(run_date), "fresh_through": fresh_through,
        "base": base,
        "span": {"start": series[0]["date"], "end": series[-1]["date"],
                 "points": len(series), "floor": SUB_INDEX_FLOOR},
        "returns": daily_returns(series),
        "series": trailing_1y_daily(series),
    }
    if code:
        e["code"] = code
    if entity_count is not None:
        e["entity_count"] = entity_count
    return e


def weekly_entry(name, src, run_date, code=None, note=None):
    """Live WEEKLY index entry (Commodities, Composite) — reader-only.

    value / base / series are taken verbatim from the published file; `returns`
    are nearest-prior-anchored on the series' OWN (weekly) dates via the same
    generic helper used for daily series, so a single genesis point yields every
    horizon {null, insufficient_history}. Forward-only: span.floor is the launch
    (base) date, not the equity SUB_INDEX_FLOOR.
    """
    series = [{"date": p["date"], "value": p["value"]} for p in src["series"]]
    fresh_through = series[-1]["date"]
    e = {
        "name": name, "status": compute_status("weekly", fresh_through, run_date), "cadence": "weekly",
        "value": src.get("current_value"), "as_of": str(run_date), "fresh_through": fresh_through,
        "base": {"value": src.get("base_value"), "date": src.get("base_date")},
        "span": {"start": series[0]["date"], "end": series[-1]["date"],
                 "points": len(series), "floor": src.get("base_date")},
        "returns": daily_returns(series),
        "series": series,
    }
    if code:
        e["code"] = code
    if note:
        e["methodology_note"] = note
    return e


def placeholder_entry(name, status, cadence=None, note=None, code=None):
    e = {"name": name, "status": status, "value": None, "as_of": None,
         "fresh_through": None, "returns": {}, "series": []}
    if code:
        e["code"] = code
    if cadence:
        e["cadence"] = cadence
    if note:
        e["methodology_note"] = note
    return e


def rpci_entry(src, run_date):
    rows = src["series"]
    disp = sorted((x["month"], x["value"]) for x in rows if not x.get("calibration"))
    dispmap = dict(disp)
    data_month = src.get("current_month") or disp[-1][0]   # latest data month, e.g. "2026-07"
    lv = dispmap[data_month]                  # the latest published monthly mark
    returns = {"1W": {"null": True, "reason": "not_applicable_for_cadence"}}
    for name, n in [("1M", 1), ("3M", 3), ("1Y", 12), ("3Y", 36), ("5Y", 60)]:
        tg = _ym_before(data_month, n)
        returns[name] = (round((lv / dispmap[tg] - 1) * 100, 2)
                         if tg in dispmap else {"null": True, "reason": "insufficient_history"})
    return {
        "name": src.get("index_name", "Robotnik Private Capital Index"),
        "code": src.get("index_code"),
        "status": compute_status("monthly", data_month, run_date), "cadence": "monthly",
        "value": src.get("current_value"), "as_of": str(run_date), "fresh_through": data_month,
        "base": {"value": src.get("base_value"), "date": src.get("base_date")},
        "span": {"start": disp[0][0], "end": disp[-1][0], "points": len(disp),
                 "display_start": disp[0][0],
                 "calibration_excluded": sum(1 for x in rows if x.get("calibration"))},
        "returns": returns,
        "series": [{"date": m, "value": v} for m, v in disp[-12:]],
    }


def main():
    run_now = datetime.now(timezone.utc)
    run_date = run_now.date()            # as_of stamp + cadence-freshness reference

    comp = load(COMPOSITE_PATH)          # equities-only book -> Public Equities
    bn = load(BOTTLENECK_PATH)
    sub = load(SUB_PATH)
    rpci = load(RPCI_PATH)
    commod = load(COMMODITIES_PATH)      # Commodities (weekly, forward-only) -> live
    blend = load(COMPOSITE_BLEND_PATH)   # Composite 75/25 blend (weekly) -> live

    base = {"value": comp.get("base_value"), "date": comp.get("base_date")}

    indexes = {
        # The published equities book is the live Public Equities index. The headline
        # Composite is now the live 75/25 public-equities/commodities blend
        # (composite_index.json), distinct from Public Equities.
        "composite": weekly_entry(
            "Robotnik Composite Index", blend, run_date, code="RCI",
            note=("75% Public Equities + 25% Commodities, periodically rebalanced "
                  "(weights reset 75/25 each period). Forward-only from the 2026-06-17 "
                  "commodities launch — no pre-launch series.")),
        "public": daily_entry("Public Equities", comp["current_value"], comp["series"], base,
                              run_date, code="RPEI"),
        "bottleneck": daily_entry("Bottleneck-Weighted", bn["current_value"], bn["series"],
                                  {"value": bn.get("base_value"), "date": bn.get("base_date")},
                                  run_date, code="RBWC"),
        "commodities": weekly_entry(
            "Commodities", commod, run_date, code="RCMI",
            note=("Forward-only weekly index of frontier-input price relatives "
                  "(§6.1 live weights, 12% single-name cap). Launched 2026-06-17.")),
        "private": rpci_entry(rpci, run_date),
    }

    # source sub-index key -> contract sector key (registry vocabulary: "semiconductors")
    SECTORS = [("space", "Space"), ("robotics", "Robotics"),
               ("semiconductor", "Semiconductors"), ("materials", "Materials")]
    sectors = {}
    for src_key, label in SECTORS:
        v = sub[src_key]
        sectors[label.lower()] = daily_entry(label, v["current_value"], v["series"], base,
                                             run_date, entity_count=v.get("entity_count"))

    out = {
        "_meta": {
            "generated_at": run_now.isoformat().replace("+00:00", "Z"),
            "generator": "scripts/build_index_summary.py",
            "purpose": "read-only contract for the home-page Index Family + Sector Performance; "
                       "single writer = this script, single reader = the site (site reads, never computes)",
            "sources": {
                "public": "data/index/robotnik_index.json",
                "composite": "data/index/composite_index.json",
                "commodities": "data/index/commodities_index.json",
                "bottleneck": "data/index/bottleneck_weighted_composite.json",
                "sectors": "data/index/sub_indices.json",
                "private": "data/index/private_capital_index.json",
            },
            "status_enum": ["live", "stale", "calibrating", "soon"],
            "return_reasons": ["insufficient_history", "not_applicable_for_cadence"],
            "return_convention": RETURN_CONVENTION,
            "trading_day_convention": TRADING_DAY_CONVENTION,
            "freshness_rule": FRESHNESS_RULE,
            "sector_key_note": ("contract uses 'semiconductors' (registry vocabulary); the home.json "
                                "reader currently keys this sector as 'semi' and must map semi -> semiconductors"),
        },
        "indexes": indexes,
        "sectors": sectors,
    }

    with open(OUT_PATH, "w") as f:
        json.dump(out, f, indent=2)
    print("  -> {} ({:.1f} KB)".format(os.path.relpath(OUT_PATH, ROOT_DIR),
                                       os.path.getsize(OUT_PATH) / 1024))


if __name__ == "__main__":
    main()
