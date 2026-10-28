#!/usr/bin/env python3
"""Turn stale commodity sources into a visible signal.

calculate_commodities_index.py flags a constituent as stale when its source carried the
price forward (a strategicmetalsinvest partner price older than SOURCE_STALE_DAYS at the
mark) or when its relative has not moved for STALE_WEEKS, and records the stale share of
the live weight as stale_weight_pct. From launch until late September 2026 the eight
strategicmetalsinvest metals, 48% of the weight, sat unchanged for fifteen weeks while
the source showed a daily update date, and no flag fired.

This check reads the published record after the weekly run has committed it. It prints
each stale flag as a workflow warning and exits 1, so the run goes red, when the stale
share reaches stale_weight_stop_pct. It reads relatives, weights and dates only; the
record carries no raw price.

Usage:
  python scripts/check_commodities_freshness.py [--record data/index/commodities_index.json]
"""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RECORD = ROOT / "data" / "index" / "commodities_index.json"


def say(level, msg):
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print("::{}::{}".format(level, " ".join(str(msg).split())), flush=True)
    else:
        print("{}: {}".format(level.upper(), msg))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--record", default=str(DEFAULT_RECORD))
    args = ap.parse_args()
    rec = json.loads(Path(args.record).read_text())
    flags = [f for f in rec.get("flags") or [] if f.startswith(("STALE SOURCE", "PRICE DATE UNKNOWN"))]
    for f in flags:
        say("warning", "Commodities {}: {}".format(rec.get("current_date"), f))
    share = rec.get("stale_weight_pct")
    stop = rec.get("stale_weight_stop_pct")
    if share is None or stop is None:
        say("warning", "Commodities record has no stale_weight_pct; the freshness check could not run.")
        return 0
    print("Stale share of the live weight: {:.2f}% (stop at {:.0f}%)".format(share, stop))
    if share >= stop:
        say("error", "Commodities {}: {:.2f}% of the live weight is stale (stop at {:.0f}%). The index "
            "is holding these prices flat; see the STALE SOURCE flags.".format(
                rec.get("current_date"), share, stop))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
