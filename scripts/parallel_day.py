#!/usr/bin/env python3
"""
Parallel-Day Orchestrator — D2-D6 of the cutover.

Runs both EODHD and MarketStack+Yahoo on the same trading day, snapshots
each vendor's output to a side-by-side path under `data/prices/_compare/`,
then runs the parity report.

Sequence:
  1. EODHD baseline (fetch_prices.py)              → snapshot eodhd_DATE.json
  2. MarketStack candidate (fetch_prices_marketstack.py
     + fetch_yahoo_overrides.py --overrides)       → snapshot marketstack_DATE.json
  3. Parity report (parity_report.py DATE)         → parity_report_DATE.json

Both vendor scripts write to data/prices/equities.json by design; this driver
snapshots each output before the next vendor overwrites it. Restores the
final snapshot back to equities.json at the end so downstream pipeline reads
the MarketStack+Yahoo composite (the candidate-vendor state).

Usage:
    python scripts/parallel_day.py [YYYY-MM-DD]

If a date is omitted, today's UTC date is used.
"""

import json
import shutil
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EQUITIES_PATH = ROOT / "data" / "prices" / "equities.json"
COMPARE_DIR   = ROOT / "data" / "prices" / "_compare"
COMPARE_DIR.mkdir(parents=True, exist_ok=True)


def run(cmd, label):
    """Run a subprocess, stream stdout/stderr live, raise on non-zero exit."""
    print("\n{0}\n[{1}] {2}\n{0}".format("─" * 60, label, " ".join(cmd)))
    rc = subprocess.call(cmd, cwd=str(ROOT))
    if rc != 0:
        print("\nFAIL: {} returned exit {}".format(label, rc))
        sys.exit(rc)


def main():
    target_date = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()

    print("=" * 60)
    print("PARALLEL-DAY ORCHESTRATOR — {}".format(target_date))
    print("  Sequence:")
    print("    1. EODHD baseline (fetch_prices.py)")
    print("    2. MarketStack + Yahoo candidate")
    print("    3. Parity report")
    print("=" * 60)

    # ── Step 1: EODHD ──
    run(["python3", "scripts/fetch_prices.py"], "EODHD baseline")
    eodhd_snap = COMPARE_DIR / "eodhd_{}.json".format(target_date)
    shutil.copy(EQUITIES_PATH, eodhd_snap)
    print("→ Snapshotted EODHD output: {}".format(eodhd_snap.relative_to(ROOT)))

    # ── Step 2: MarketStack + Yahoo ──
    run(["python3", "scripts/fetch_prices_marketstack.py"], "MarketStack candidate")
    run(["python3", "scripts/fetch_yahoo_overrides.py", "--overrides"], "Yahoo overrides")
    ms_snap = COMPARE_DIR / "marketstack_{}.json".format(target_date)
    shutil.copy(EQUITIES_PATH, ms_snap)
    print("→ Snapshotted MarketStack + Yahoo output: {}".format(ms_snap.relative_to(ROOT)))

    # ── Step 3: Parity report ──
    run(["python3", "scripts/parity_report.py", target_date], "Parity report")

    print("\n" + "=" * 60)
    print("PARALLEL DAY COMPLETE — {}".format(target_date))
    print("=" * 60)
    print("Snapshots:")
    print("  {}".format(eodhd_snap.relative_to(ROOT)))
    print("  {}".format(ms_snap.relative_to(ROOT)))
    print("Parity report:")
    print("  data/prices/_compare/parity_report_{}.json".format(target_date))
    print()
    print("Current equities.json reflects MarketStack + Yahoo composite (the")
    print("candidate-vendor state). Downstream pipeline (calculate_index.py,")
    print("enrich_equities.py) reads this for the cutover-side composite.")


if __name__ == "__main__":
    main()
