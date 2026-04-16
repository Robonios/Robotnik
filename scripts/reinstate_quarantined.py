#!/usr/bin/env python3
"""
Robotnik — Reinstate Quarantined Entity
========================================
Reinstates a quarantined entity ONLY if it appears in ready_for_reinstatement.json.
Refuses to act if the entity is not ready.

Usage: python scripts/reinstate_quarantined.py 012450.KS
"""

import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "data" / "registries" / "entity_registry.json"
READY_FILE = ROOT / "data" / "quarantine" / "ready_for_reinstatement.json"
WATCH_FILE = ROOT / "data" / "quarantine" / "reinstatement_watch.json"


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/reinstate_quarantined.py <TICKER>")
        print("Example: python scripts/reinstate_quarantined.py '012450 KS'")
        sys.exit(1)

    ticker = sys.argv[1]

    # Check ready_for_reinstatement.json
    if not READY_FILE.exists():
        print(f"ERROR: {READY_FILE} does not exist. No entities are ready for reinstatement.")
        sys.exit(1)

    ready = json.load(open(READY_FILE))
    if ticker not in ready:
        print(f"REFUSED: {ticker} is NOT in ready_for_reinstatement.json.")
        print(f"An entity must have 5 consecutive clean fetches before reinstatement.")
        if WATCH_FILE.exists():
            watch = json.load(open(WATCH_FILE))
            if ticker in watch:
                w = watch[ticker]
                print(f"Current status: {w.get('consecutive_clean_fetches', 0)} clean fetches"
                      f" (need 5). Last: {w.get('last_fetch_status', '?')}")
        sys.exit(1)

    entry = ready[ticker]
    print(f"Reinstating: {ticker} ({entry.get('name', '')})")
    print(f"  Quarantined: {entry.get('quarantine_date')}")
    print(f"  Ready since: {entry.get('ready_date')}")
    print(f"  Clean fetches: {entry.get('consecutive_clean_fetches')}")
    print(f"  Recent USD values: {entry.get('recent_values_usd')}")

    # Update registry
    reg = json.load(open(REGISTRY))
    if ticker in reg and isinstance(reg[ticker], dict):
        # Remove quarantine fields
        reg[ticker].pop("status", None)
        reg[ticker].pop("quarantine_reason", None)
        reg[ticker].pop("quarantine_date", None)
        # Add reinstatement audit trail
        reg[ticker]["reinstatement_date"] = datetime.utcnow().strftime("%Y-%m-%d")
        reg[ticker]["reinstatement_notes"] = (
            f"Reinstated after {entry.get('consecutive_clean_fetches')} consecutive clean fetches. "
            f"Quarantined {entry.get('quarantine_date')} — {entry.get('ready_date')}."
        )
        with open(REGISTRY, "w") as f:
            json.dump(reg, f, indent=2)
        print(f"  ✓ Registry updated: quarantine fields removed, reinstatement_date set")
    else:
        print(f"  WARNING: {ticker} not found in registry")

    # Remove from ready file
    del ready[ticker]
    with open(READY_FILE, "w") as f:
        json.dump(ready, f, indent=2)
    print(f"  ✓ Removed from ready_for_reinstatement.json")

    # Remove from watch file
    if WATCH_FILE.exists():
        watch = json.load(open(WATCH_FILE))
        if ticker in watch:
            del watch[ticker]
            with open(WATCH_FILE, "w") as f:
                json.dump(watch, f, indent=2)
            print(f"  ✓ Removed from reinstatement_watch.json")

    print(f"\nREINSTATED: {ticker}")
    print(f"Next step: run 'python scripts/calculate_index.py' to rebuild index with reinstated entity.")


if __name__ == "__main__":
    main()
