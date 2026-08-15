#!/usr/bin/env python3
"""
Staleness monitor — mechanises "green != fresh".
================================================
Catches the failure class where a scheduled writer silently stops producing and
nothing exits non-zero. Precedent: the fetch-intel cron was never registered, so
research.json / filings.json / reports.json went dormant for ~4 months with CI
green throughout. Nothing errors when a file simply stops being written.

HOW IT DISTINGUISHES "writer died" FROM "nothing changed":
  It reads each artefact's own RUN-STAMP field (calculated_at / fetched_at /
  updated) where it has one. A run-stamp is rewritten EVERY run regardless of
  whether the data moved, so it tracks writer-liveness, not data-change: a weekly
  index that correctly holds its last observation between marks still bumps its
  stamp each Saturday; a monthly RPCI mid-month has a recent stamp; a DEAD writer
  freezes it. Where no run-stamp exists, it falls back to the git commit-date
  (the file is re-committed every run because the daily series always diffs).
  It reports which source it used per artefact.

TOLERANCES are sized to the largest LEGITIMATE no-update gap plus a one-run
margin, so a normal hold never trips STALE but a real death does. STALE => a
writer has died (exit 1). AGEING => approaching the limit (warning, exit 0).

Reads only files + git; needs no API keys. Run it as its OWN scheduled workflow,
never as a step inside a job it monitors — a monitor inside the job dies with it.

Usage:  python scripts/check_staleness.py [--json]
Exit :  1 if any monitored artefact is STALE; else 0.
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Tolerances (days). AGEING warns; STALE fails (exit 1).
#   daily   = weekday EOD cron; Fri 22:00 -> Mon is a legitimate ~3d weekend hold,
#             so >4d means a weekday run actually died. (A rare public holiday may
#             trip it; we accept that over missing a real death.)
#   weekly  = 7d cadence + 2d margin (catches one missed run without alerting on
#             the normal 7d hold).
#   monthly = a full month + margin; a mid-month RPCI is not stale (stamp recent).
TOL = {
    "daily":   {"ageing": 3,  "stale": 4},
    "weekly":  {"ageing": 8,  "stale": 9},
    "monthly": {"ageing": 33, "stale": 38},
}

# Inventory: (path, writer, cadence, freshness-spec).
#   freshness-spec ("field", <name>) reads an in-file run-stamp;
#   ("mtime",) uses git commit-date (only where no run-stamp exists).
# Cadences verified against .github/workflows/ crons; writers via grep.
MONITORED = [
    # -- daily: weekday EOD pipeline, 22:00 UTC (fetch-data.yml) --
    ("data/index/robotnik_index.json",                "calculate_index.py",                "daily",   ("mtime",)),
    ("data/index/sub_indices.json",                   "calculate_index.py",                "daily",   ("mtime",)),
    ("data/index/weights.json",                       "calculate_index.py",                "daily",   ("field", "calculated_at")),
    ("data/index/summary.json",                       "calculate_index.py",                "daily",   ("field", "calculated_at")),
    ("data/index/market_caps.json",                   "fetch_market_caps.py",              "daily",   ("field", "fetched_at")),
    ("data/prices/all_prices.json",                   "assemble_all_prices.py",            "daily",   ("field", "fetched_at")),
    ("data/prices/equities.json",                     "fetch_prices_marketstack.py",       "daily",   ("field", "fetched_at")),
    ("data/prices/benchmarks.json",                   "fetch_benchmarks.py",               "daily",   ("field", "fetched_at")),
    ("data/index/bottleneck_weighted_composite.json", "calculate_bottleneck_composite.py", "daily",   ("field", "calculated_at")),
    ("data/index/index_summary.json",                 "build_index_summary.py",            "daily",   ("mtime",)),
    ("data/news.json",                                "fetch_news.py",                     "daily",   ("field", "fetched_at")),
    # -- weekly: commodities/composite, Sat 08:00 UTC (weekly-commodities-composite.yml) --
    ("data/index/commodities_index.json",             "calculate_commodities_index.py",    "weekly",  ("field", "calculated_at")),
    ("data/index/composite_index.json",               "calculate_composite_index.py",      "weekly",  ("field", "calculated_at")),
    # -- weekly: intel feeds, Mon 06:00 UTC (fetch-data.yml) -- the class that died --
    ("data/research.json",                            "fetch_research.py",                 "weekly",  ("field", "updated")),
    ("data/filings.json",                             "fetch_filings.py",                  "weekly",  ("field", "updated")),
    ("data/reports.json",                             "fetch_reports.py",                  "weekly",  ("field", "updated")),
    # -- monthly: RPCI, manual sweep (no cron) --
    ("data/index/private_capital_index.json",         "calculate_private_index.py",        "monthly", ("field", "fetched_at")),
]

# Deliberately NOT monitored (printed for transparency, and audited 2026-08-15).
EXCLUDED = [
    ("data/index/index_metrics.json",
     "DEAD - writer calculate_index_metrics.py is in no workflow and nothing reads it (last 2026-05-23). Remove it."),
    ("data/registries/search_index.json",
     "NO REPRODUCIBLE BUILD - served (nav search + asset-profile) but NO script writes it; generated ad-hoc 2026-07-03. "
     "Build a generator + schedule it, THEN monitor. Serious: it is already stale vs the universe."),
    ("data/markets/enrichment_data.json", "hand-curated ratings - no schedule."),
    ("sitemap.xml",                       "event-driven (on push) - no time cadence."),
    ("data/index/base_date.json",         "legitimately static (index base date) - mtime would false-positive."),
]


def parse_ts(s):
    """Parse the assorted timestamp formats the writers emit. Note several writers
    emit a MALFORMED '...+00:00Z' (both an offset and a trailing Z, from
    now(utc).isoformat()+'Z') — handle it rather than choke on it."""
    if s is None:
        return None
    s = str(s).strip()
    if s.endswith("Z"):
        body = s[:-1]
        # An offset already present (after the YYYY-MM-DD date) -> drop the
        # redundant Z; otherwise convert a bare Z to +00:00.
        s = body if ("+" in body[10:] or "-" in body[10:]) else body + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        pass
    core = s.split("+")[0].split("Z")[0].strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(core, fmt).replace(tzinfo=timezone.utc)
        except Exception:
            continue
    return None


def git_commit_dt(path):
    try:
        out = subprocess.check_output(
            ["git", "log", "-1", "--format=%cI", "--", path],
            cwd=ROOT, stderr=subprocess.DEVNULL).decode().strip()
        return parse_ts(out) if out else None
    except Exception:
        return None


def freshness(path, spec):
    """Return (datetime, source-label). source-label says which signal was used."""
    full = os.path.join(ROOT, path)
    if not os.path.exists(full):
        return None, "MISSING FILE"
    if spec[0] == "field":
        try:
            d = json.load(open(full))
            if isinstance(d, dict) and d.get(spec[1]) is not None:
                dt = parse_ts(d[spec[1]])
                if dt:
                    return dt, spec[1]
        except Exception:
            pass
        # run-stamp expected but absent/unparseable -> fall back, but flag loudly
        return git_commit_dt(path), "git-commit (WARN: field '%s' missing)" % spec[1]
    return git_commit_dt(path), "git-commit"


def main():
    as_json = "--json" in sys.argv
    now = datetime.now(timezone.utc)
    rows, any_stale = [], False

    for path, writer, cadence, spec in MONITORED:
        dt, src = freshness(path, spec)
        if dt is None:
            verdict, age = "STALE", None
            any_stale = True
        else:
            age = (now - dt).total_seconds() / 86400.0
            t = TOL[cadence]
            verdict = "STALE" if age > t["stale"] else ("AGEING" if age > t["ageing"] else "FRESH")
            any_stale = any_stale or (verdict == "STALE")
        rows.append({
            "artefact": path, "writer": writer, "cadence": cadence, "source": src,
            "last_fresh": dt.isoformat() if dt else None,
            "age_days": round(age, 2) if age is not None else None, "verdict": verdict,
        })

    order = {"STALE": 0, "AGEING": 1, "FRESH": 2}
    rows.sort(key=lambda r: (order.get(r["verdict"], 0), -(r["age_days"] or 0)))

    if as_json:
        print(json.dumps({
            "now": now.isoformat(), "any_stale": any_stale, "monitored": rows,
            "excluded": [{"artefact": p, "reason": r} for p, r in EXCLUDED],
        }, indent=2))
        return 1 if any_stale else 0

    mark = {"STALE": "STALE ", "AGEING": "AGEING", "FRESH": "fresh "}
    print("STALENESS MONITOR  -  %s" % now.strftime("%Y-%m-%d %H:%M UTC"))
    print("=" * 78)
    for r in rows:
        lf = (r["last_fresh"] or "-")[:19]
        age = ("%.1fd" % r["age_days"]) if r["age_days"] is not None else "  -"
        print("[%s] %s" % (mark[r["verdict"]], r["artefact"]))
        print("          %-34s %-8s age %-7s fresh %s  via %s"
              % (r["writer"], r["cadence"], age, lf, r["source"]))
    print("-" * 78)
    print("NOT MONITORED (audited):")
    for p, reason in EXCLUDED:
        print("  - %s\n      %s" % (p, reason))
    print("=" * 78)
    print("RESULT: %s" % ("STALE artefact(s) detected -- a writer has died (exit 1)."
                          if any_stale else "all monitored artefacts fresh (exit 0)."))
    return 1 if any_stale else 0


if __name__ == "__main__":
    sys.exit(main())
