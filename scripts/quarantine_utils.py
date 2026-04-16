"""
Robotnik Data Quality — Quarantine Utilities
=============================================
Shared sentinel detection, rejection logging, and reinstatement watch
used by fetch_prices.py, fetch_live_prices.py, and calculate_index.py.
"""

import json
import os
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUARANTINE_DIR = ROOT / "data" / "quarantine"
QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)

REJECTIONS_LOG = QUARANTINE_DIR / "fetcher_rejections.jsonl"
AUTO_CANDIDATES = QUARANTINE_DIR / "auto_quarantine_candidates.json"
REINSTATEMENT_WATCH = QUARANTINE_DIR / "reinstatement_watch.json"
READY_FOR_REINSTATEMENT = QUARANTINE_DIR / "ready_for_reinstatement.json"

# ── Sentinel patterns (native currency, before FX conversion) ──
SENTINEL_RANGES = [
    (999990, 1000010),       # ₩999,999.9999
    (99999.0, 100001.0),     # ₩99,999 or similar
    (9999.90, 10000.10),     # 9,999.99
    (999.990, 1000.010),     # 999.99 (careful: some real prices are ~$1000)
    (-0.001, 0.001),         # Zero or near-zero
]

# Max plausible share price by currency (native units)
IMPLAUSIBLE_MAX = {
    "USD": 50000, "EUR": 50000, "GBP": 50000, "CHF": 50000,
    "JPY": 500000, "KRW": 5000000, "TWD": 50000, "HKD": 50000,
    "CNY": 50000, "SEK": 50000, "NOK": 50000, "CAD": 50000, "AUD": 50000,
}


def is_sentinel(price, currency="USD"):
    """Check if a price matches known sentinel patterns."""
    if price is None:
        return True, "null price"
    if price <= 0:
        return True, "zero or negative"

    ccy = (currency or "USD").upper()

    # KRW sentinel: ₩999,999.9999
    if ccy == "KRW" and 999990 <= price <= 1000010:
        return True, f"KRW sentinel {price:.2f}"

    # Generic near-zero sentinel
    if price < 0.01:
        return True, f"near-zero {price}"

    # Implausible price for the currency
    max_price = IMPLAUSIBLE_MAX.get(ccy, 50000)
    if price > max_price:
        return True, f"implausible {price:.2f} > {max_price} {ccy}"

    return False, None


def log_rejection(ticker, raw_value, currency, source, reason):
    """Append a rejection record to the JSONL log."""
    record = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "ticker": ticker,
        "raw_value": raw_value,
        "currency": currency,
        "source": source,
        "reason": reason,
    }
    with open(REJECTIONS_LOG, "a") as f:
        f.write(json.dumps(record) + "\n")
    print(f"  REJECTED: {ticker} value={raw_value} {currency} — {reason}")


def check_consecutive_rejections(ticker):
    """Check if a ticker has been rejected 3+ consecutive times. If so, flag as candidate."""
    if not REJECTIONS_LOG.exists():
        return

    # Read recent rejections for this ticker
    rejections = []
    with open(REJECTIONS_LOG) as f:
        for line in f:
            try:
                r = json.loads(line.strip())
                if r.get("ticker") == ticker:
                    rejections.append(r)
            except:
                continue

    if len(rejections) < 3:
        return

    # Check last 3 are consecutive (no clean fetches in between)
    # For simplicity, just check if the 3 most recent are all rejections
    last3 = rejections[-3:]

    # Load or create candidates file
    candidates = {}
    if AUTO_CANDIDATES.exists():
        candidates = json.load(open(AUTO_CANDIDATES))

    if ticker not in candidates:
        candidates[ticker] = {
            "first_rejection": last3[0]["timestamp"],
            "rejection_count": len(rejections),
            "latest_reason": last3[-1]["reason"],
            "flagged_date": datetime.utcnow().isoformat() + "Z",
        }
        with open(AUTO_CANDIDATES, "w") as f:
            json.dump(candidates, f, indent=2)
        print(f"  AUTO-QUARANTINE CANDIDATE: {ticker} — {len(rejections)} consecutive rejections")


def update_reinstatement_watch(ticker, name, price_native, price_usd, currency,
                                 anchor_value=None, is_clean=True):
    """Track quarantined tickers' recovery toward reinstatement."""
    watch = {}
    if REINSTATEMENT_WATCH.exists():
        watch = json.load(open(REINSTATEMENT_WATCH))

    if ticker not in watch:
        watch[ticker] = {
            "name": name,
            "quarantine_date": None,
            "anchor_value_usd": anchor_value,
            "consecutive_clean_fetches": 0,
            "last_fetch_date": None,
            "last_fetch_value_native": None,
            "last_fetch_value_usd": None,
            "last_fetch_status": None,
            "currency": currency,
            "recent_clean_values_native": [],
            "recent_clean_values_usd": [],
        }

    entry = watch[ticker]
    entry["last_fetch_date"] = datetime.utcnow().strftime("%Y-%m-%d")
    entry["last_fetch_value_native"] = price_native
    entry["last_fetch_value_usd"] = price_usd
    entry["currency"] = currency

    if is_clean:
        # Plausibility check against anchor
        anchor = entry.get("anchor_value_usd") or anchor_value
        if anchor and price_usd:
            if price_usd > anchor * 10 or price_usd < anchor * 0.1:
                # Outside plausible range — not truly clean
                entry["last_fetch_status"] = "rejected_plausibility"
                entry["consecutive_clean_fetches"] = 0
                print(f"  REINSTATEMENT WATCH: {ticker} value ${price_usd:.2f} outside plausible range of anchor ${anchor:.2f}")
            else:
                entry["last_fetch_status"] = "clean"
                entry["consecutive_clean_fetches"] += 1
                entry["recent_clean_values_native"].append(price_native)
                entry["recent_clean_values_usd"].append(price_usd)
                # Keep only last 10
                entry["recent_clean_values_native"] = entry["recent_clean_values_native"][-10:]
                entry["recent_clean_values_usd"] = entry["recent_clean_values_usd"][-10:]
        else:
            entry["last_fetch_status"] = "clean"
            entry["consecutive_clean_fetches"] += 1
    else:
        entry["last_fetch_status"] = "rejected"
        entry["consecutive_clean_fetches"] = 0

    with open(REINSTATEMENT_WATCH, "w") as f:
        json.dump(watch, f, indent=2)

    # Check if ready for reinstatement (5 consecutive clean fetches)
    if entry["consecutive_clean_fetches"] >= 5:
        _flag_ready_for_reinstatement(ticker, entry)


def _flag_ready_for_reinstatement(ticker, watch_entry):
    """Write ticker to ready_for_reinstatement.json."""
    ready = {}
    if READY_FOR_REINSTATEMENT.exists():
        ready = json.load(open(READY_FOR_REINSTATEMENT))

    ready[ticker] = {
        "name": watch_entry.get("name", ""),
        "quarantine_date": watch_entry.get("quarantine_date"),
        "ready_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "consecutive_clean_fetches": watch_entry["consecutive_clean_fetches"],
        "recent_values_native": watch_entry["recent_clean_values_native"][-5:],
        "recent_values_usd": watch_entry["recent_clean_values_usd"][-5:],
        "currency": watch_entry.get("currency"),
        "recommendation": "Manual review and reinstatement",
    }

    with open(READY_FOR_REINSTATEMENT, "w") as f:
        json.dump(ready, f, indent=2)

    print(f"  READY FOR REINSTATEMENT: {ticker} has returned {watch_entry['consecutive_clean_fetches']} consecutive clean fetches")
    print(f"  → Review data/quarantine/ready_for_reinstatement.json")
