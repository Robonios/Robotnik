#!/usr/bin/env python3
"""
Keep a stored price history on one adjustment basis when a refreshed window is merged in.
========================================================================================
The daily refresh re-fetches a window of bars (45 days from MarketStack, about 100 from
Yahoo), already split-adjusted, and merges it over the stored five-year history. When a
split falls inside the window, the vendor divides every bar before the split by its
factor, but the stored bars older than the window keep the old basis. The merged series
then steps by about 1/k at the window's first date, a fall that never happened:
Ibiden's 2-for-1 split of 29 September 2026 left a 50% step on 1 May 2026, which the
chain-linked index booked as a real fall.

rebase_stored() compares the stored and the fetched closes on the earliest dates the two
share. When they agree, nothing changes. When every one of those dates gives the same
ratio, away from 1 (a split, a bonus issue or a change of quoting basis), the stored bars
before the change are divided by that ratio, and their volume multiplied by it, so the
merge leaves no step. Once merged, the next refresh finds the two in agreement, so the
rebase happens once per event.

Stdlib only. Ratios only in any output: never a price.
"""

import os

REBASE_MIN = 0.03   # a basis change under 3% is left alone
AGREE = 0.01        # the probed dates must agree on the ratio within 1%
PROBE = 5           # the earliest shared dates compared
MIN_PROBE = 3       # fewer shared dates than this: no decision


def _day(row):
    return str(row.get("date") or "")[:10]


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and x > 0


def rebase_factor(stored_rows, new_rows):
    """(stored/new close ratio on the earliest shared dates, the first shared date from
    which the two agree), or (None, None) when no rebase is due."""
    stored = {_day(r): r.get("close") for r in stored_rows}
    ratios = []
    for r in sorted(new_rows, key=_day):
        s, n = stored.get(_day(r)), r.get("close")
        if _num(s) and _num(n):
            ratios.append((_day(r), s / n))
    probe = [x for _, x in ratios[:PROBE]]
    if len(probe) < MIN_PROBE:
        return None, None
    f = sorted(probe)[len(probe) // 2]
    if abs(f - 1) < REBASE_MIN or any(abs(x / f - 1) > AGREE for x in probe):
        return None, None
    # The change sits where the shared dates stop giving f and start agreeing.
    boundary = next((d for d, x in ratios if abs(x - 1) <= AGREE), None)
    return f, boundary


def rebase_stored(stored_rows, new_rows):
    """(stored rows, with every bar dated before the change divided by the factor, and the
    factor), or (the stored rows unchanged, None)."""
    f, boundary = rebase_factor(stored_rows, new_rows)
    if f is None:
        return stored_rows, None
    out = []
    for r in stored_rows:
        if boundary is None or _day(r) < boundary:
            r = dict(r)
            for k in ("open", "high", "low", "close"):
                if _num(r.get(k)):
                    r[k] = r[k] / f
            if _num(r.get("volume")):
                r["volume"] = round(r["volume"] * f)
        out.append(r)
    return out, f


def note_rebase(ticker, factor):
    """One line, and a notice annotation in Actions: the ticker and the ratio, no price."""
    msg = ("REBASED {}: stored bars before the refreshed window's split or basis change "
           "divided by {:.4f}").format(ticker, factor)
    print("  " + msg)
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print("::notice::" + msg, flush=True)
