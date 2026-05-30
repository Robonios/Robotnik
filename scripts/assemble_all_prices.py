#!/usr/bin/env python3
"""
Assemble all_prices.json — the FINAL step of the MarketStack EOD price pipeline.
================================================================================
In the legacy EODHD pipeline, `fetch_prices.py` fetched equities AND tokens AND
assembled `all_prices.json` in one script. The MarketStack pipeline splits the
fetch across vendors, so the assembly must be its own step:

  fetch_prices_marketstack.py        -> data/prices/equities.json  (MarketStack)
  fetch_yahoo_overrides.py --overrides -> merges Yahoo override names INTO it
  (tokens.json                        -> CoinGecko; legacy watchlist, NOT in any
                                          equity aggregation — kept for the feed)
  THIS SCRIPT                          -> data/prices/all_prices.json (combined)

`all_prices.json` is what calculate_index.py, calculate_bottleneck_composite.py
and calculate_metrics.py read. Without this step the MarketStack YAML would leave
nothing producing it — the assembly gap the cutover dry-run is designed to catch.

Tokens are a legacy content watchlist (type=="token"), excluded from every equity
index by construction, so their freshness is non-critical: we fold in the most
recent tokens.json if present and never block on it.

Usage:  python scripts/assemble_all_prices.py
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EQ_PATH  = ROOT / "data" / "prices" / "equities.json"
TK_PATH  = ROOT / "data" / "prices" / "tokens.json"
OUT_PATH = ROOT / "data" / "prices" / "all_prices.json"


def _row(e):
    return {
        "ticker":   e.get("ticker"),
        "price":    e.get("price"),
        "currency": e.get("currency", "USD"),
        "date":     e.get("date"),
        "sector":   e.get("sector"),
        "source":   e.get("source"),
    }


def main():
    if not EQ_PATH.exists():
        print("FATAL: {} missing — run fetch_prices_marketstack.py first".format(
            EQ_PATH.name), file=sys.stderr)
        sys.exit(1)
    eq = json.loads(EQ_PATH.read_text())
    prices = [_row(e) for e in eq.get("equities", []) if e.get("price") is not None]
    n_eq = len(prices)

    n_tok = 0
    if TK_PATH.exists():
        try:
            tk = json.loads(TK_PATH.read_text())
            for t in tk.get("tokens", []):
                if t.get("price") is not None:
                    prices.append(_row(t)); n_tok += 1
        except Exception as exc:
            print("  WARN: tokens.json unreadable ({}); assembling equities only".format(exc))

    out = {
        "fetched_at": datetime.now(timezone.utc).isoformat() + "Z",
        "count": len(prices),
        "source": "MarketStack + Yahoo overrides + CoinGecko (assembled)",
        "prices": prices,
    }
    OUT_PATH.write_text(json.dumps(out, indent=2))
    from collections import Counter
    mix = dict(Counter(p["source"] for p in prices))
    print("Assembled all_prices.json: {} equities + {} tokens = {} rows  {}".format(
        n_eq, n_tok, len(prices), mix))


if __name__ == "__main__":
    main()
