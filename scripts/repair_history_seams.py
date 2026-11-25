#!/usr/bin/env python3
"""
Repair the split seams left in the stored price history before history_rebase.py existed.
==========================================================================================
Until the refresh learned to rebase (history_rebase.py), a split inside the refreshed
window left the older stored bars on the old basis, and the history stepped by about 1/k
where the window began, months before the split. data/registries/history_seam_repairs.json
lists each such split, checked against the exchange's own notice: ticker, ex-date, factor.

For each, this finds the one unreverted step whose ratio is within TOL of 1/factor, dated
from LOOKBACK_DAYS before the ex-date to a week after it, and divides every bar before
that step by the factor (volume multiplied by it). The day's own move survives: Keyence's
step of 0.1997 on 6 October 2026 becomes 0.9985. A history with no such step is already
repaired, or never had one, and is left alone, so the script can run on every pipeline
run. More than one candidate is left alone and reported.

Prints tickers, dates and ratios only, never a price.

Usage:
    python scripts/repair_history_seams.py           # report what would change
    python scripts/repair_history_seams.py --apply   # write the repaired histories
"""
import json
import os
import sys
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORY_DIR = os.path.join(ROOT, "data", "prices", "history")
REGISTRY = os.path.join(ROOT, "data", "registries", "history_seam_repairs.json")

TOL = 0.2              # |ratio x factor - 1| for a step to count as the seam
REVERT = 0.12          # a step undone by the next bar is a bad print, not a seam
LOOKBACK_DAYS = 220    # the Yahoo refresh reaches about 100 trading days back


def say(msg, level=None):
    print("  " + msg)
    if level and os.environ.get("GITHUB_ACTIONS") == "true":
        print("::{}::{}".format(level, msg), flush=True)


def history_path(ticker, history_dir=HISTORY_DIR):
    return os.path.join(history_dir, ticker.replace(" ", "_").replace("/", "_") + ".json")


def _close(row):
    c = row.get("close")
    return c if isinstance(c, (int, float)) and not isinstance(c, bool) and c > 0 else None


def find_seams(series, ex_date, factor):
    """Indexes i of rows whose step from the previous priced row looks like the seam."""
    rows = [(i, r) for i, r in enumerate(series) if _close(r)]
    lo = (date.fromisoformat(ex_date) - timedelta(days=LOOKBACK_DAYS)).isoformat()
    hi = (date.fromisoformat(ex_date) + timedelta(days=7)).isoformat()
    found = []
    for k in range(1, len(rows)):
        i, r = rows[k]
        day = str(r.get("date"))[:10]
        if not lo <= day <= hi:
            continue
        step = _close(r) / _close(rows[k - 1][1])
        if abs(step * factor - 1) > TOL:
            continue
        if k + 1 < len(rows) and abs(step * (_close(rows[k + 1][1]) / _close(r)) - 1) <= REVERT:
            continue                   # a bad print the next bar undoes
        if k >= 2 and abs(step * (_close(rows[k - 1][1]) / _close(rows[k - 2][1])) - 1) <= REVERT:
            continue                   # the bar undoing a bad print
        found.append((i, day, step))
    return found


def repair(series, index, factor):
    """The series with every row before `index` divided by the factor."""
    out = []
    for i, r in enumerate(series):
        if i < index:
            r = dict(r)
            for k in ("open", "high", "low", "close"):
                v = r.get(k)
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    r[k] = v / factor
            v = r.get("volume")
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                r["volume"] = round(v * factor)
        out.append(r)
    return out


def run(apply=False, registry=REGISTRY, history_dir=HISTORY_DIR):
    """[(ticker, outcome)] for each listed split; writes the repairs when apply is set."""
    splits = []
    if os.path.exists(registry):
        with open(registry) as f:
            splits = json.load(f).get("splits") or []
    results = []
    for s in splits:
        ticker, ex_date, factor = s["ticker"], s["ex_date"], float(s["factor"])
        path = history_path(ticker, history_dir)
        if not os.path.exists(path):
            results.append((ticker, "no history file"))
            continue
        with open(path) as f:
            doc = json.load(f)
        series = sorted(doc.get("series") or [], key=lambda r: str(r.get("date")))
        seams = find_seams(series, ex_date, factor)
        if not seams:
            results.append((ticker, "clean"))
            continue
        if len(seams) > 1:
            say("{}: {} candidate steps for the {}-for-1 split of {}; left alone".format(
                ticker, len(seams), int(factor), ex_date), "warning")
            results.append((ticker, "ambiguous"))
            continue
        i, day, step = seams[0]
        if apply:
            doc["series"] = repair(series, i, factor)
            with open(path, "w") as f:
                json.dump(doc, f, indent=2)
        say("{} {}: step {:.4f} -> {:.4f} ({}-for-1 split of {}){}".format(
            ticker, day, step, step * factor, int(factor), ex_date,
            "" if apply else " [dry run]"), "notice" if apply else None)
        results.append((ticker, "repaired" if apply else "would repair"))
    return results


def main():
    apply = "--apply" in sys.argv[1:]
    print("HISTORY SEAM REPAIR ({})".format("apply" if apply else "dry run"))
    results = run(apply=apply)
    for ticker, outcome in results:
        print("  {:10} {}".format(ticker, outcome))
    return 0


if __name__ == "__main__":
    sys.exit(main())
