#!/usr/bin/env python3
"""
History seam check: single-day ratios in the price history that look like a share split.
=========================================================================================
The daily refresh (fetch_price_history_marketstack.py --refresh) re-fetches a 45-day
window, split-adjusts it, and merges it over the stored history. When a split falls
inside the window, the window is adjusted and the older stored bars are not, so the
series carries a step of about 1/k (a k-for-1 split) at the window's first date: Keyence
(1-for-5, trading split from 19 November 2026) left one at 6 October 2026.

calculate_index.py neutralises a daily ratio below 0.2 or above 5 as a corporate action,
so a 1-for-5 seam is caught only when the stock also fell that day, and a 2-, 3- or 4-for-1
seam (0.5, 0.33, 0.25) is never caught: the chain-link books it as a real fall.

This check reads every history file and reports each consecutive-bar ratio below
LOW or above HIGH, labelled with the nearest split factor when it is within TOL of one,
and whether the next bar reverts it (a bad print reverts; a seam or a real split stays).
It prints tickers, dates and ratios only, never a price. Read-only.

Usage:
    python scripts/check_history_seams.py            # report; exit 0
    python scripts/check_history_seams.py --strict   # exit 1 if an unreverted split-like step
                                                     # escapes the index's 0.2-5 neutraliser
    python scripts/check_history_seams.py --json     # machine-readable
"""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORY_DIR = os.path.join(ROOT, "data", "prices", "history")

LOW, HIGH = 0.55, 1.8          # beyond -45% / +80% in one bar
TOL = 0.12                     # |ratio x k - 1| within 12% counts as split-like
FACTORS = (2, 3, 4, 5, 6, 8, 10, 15, 20, 25, 30, 40, 50, 100)
NEUTRAL_LOW, NEUTRAL_HIGH = 0.2, 5.0   # calculate_index.backfill_index_chained


def split_label(r):
    """'1-for-k' style label for a forward (r ~ 1/k) or reverse (r ~ k) split, or None."""
    for k in FACTORS:
        if abs(r * k - 1) <= TOL:
            return "forward {}:1".format(k)
        if abs(r / k - 1) <= TOL:
            return "reverse 1:{}".format(k)
    return None


def closes(path):
    try:
        doc = json.load(open(path))
    except Exception:
        return None, []
    rows = [(str(r.get("date", ""))[:10], r.get("close")) for r in (doc.get("series") or [])]
    rows = [(d, c) for d, c in rows if d and isinstance(c, (int, float)) and c > 0]
    return doc.get("ticker") or os.path.basename(path)[:-5], sorted(rows)


def scan(history_dir=HISTORY_DIR):
    found = []
    for path in sorted(glob.glob(os.path.join(history_dir, "*.json"))):
        ticker, rows = closes(path)
        for i in range(1, len(rows)):
            r = rows[i][1] / rows[i - 1][1]
            if LOW <= r <= HIGH:
                continue
            nxt = rows[i + 1][1] / rows[i][1] if i + 1 < len(rows) else None
            reverted = nxt is not None and abs(r * nxt - 1) <= TOL
            label = split_label(r)
            found.append({
                "ticker": ticker, "date": rows[i][0], "prev_date": rows[i - 1][0],
                "ratio": round(r, 4), "split_like": label, "reverted_next_bar": reverted,
                "index_neutralises": r < NEUTRAL_LOW or r > NEUTRAL_HIGH,
            })
    return found


def main():
    args = sys.argv[1:]
    found = scan()
    files = len(glob.glob(os.path.join(HISTORY_DIR, "*.json")))
    risky = [f for f in found if f["split_like"] and not f["reverted_next_bar"]
             and not f["index_neutralises"]]
    if "--json" in args:
        print(json.dumps({"files": files, "steps": found, "unneutralised_split_like": risky},
                         indent=2))
    else:
        print("HISTORY SEAM CHECK: {} files, {} steps beyond {}..{}".format(
            files, len(found), LOW, HIGH))
        for f in found:
            print("  {:12} {} ratio {:>8.4f}  {:14} {}{}".format(
                f["ticker"], f["date"], f["ratio"], f["split_like"] or "large move",
                "reverts next bar" if f["reverted_next_bar"] else "stays",
                "" if not f["split_like"] or f["index_neutralises"]
                else "  <- the index books this as a real move"))
        print("RESULT: {} split-like step(s) the index does not neutralise".format(len(risky)))
        if os.environ.get("GITHUB_ACTIONS") == "true":
            for f in risky:
                print("::warning::History seam: {} {} ratio {:.4f} ({}), not neutralised by "
                      "the index.".format(f["ticker"], f["date"], f["ratio"], f["split_like"]))
    return 1 if ("--strict" in args and risky) else 0


if __name__ == "__main__":
    sys.exit(main())
