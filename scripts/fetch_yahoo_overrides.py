#!/usr/bin/env python3
"""
Yahoo Override Fetcher — D2 of the EODHD → MarketStack cutover.

Reads data/registries/data_source_overrides.json and back-fills the listed
tickers via Yahoo Finance. These are the entries in MARKETSTACK_UNSUPPORTED
plus the Hanwha KRW field-cap edge case — MarketStack cannot serve them, so
the production pipeline relies on Yahoo for the override subset.

Modes:
  --overrides           Latest EOD for each override ticker; merges into
                        data/prices/equities.json (appended/replaced per ticker).
  --history-overrides   Daily history for each override ticker; writes one
                        data/prices/history/{ticker}.json per entry, merging
                        with on-disk history (same shape as the MarketStack
                        history fetcher).

Usage:
    python scripts/fetch_yahoo_overrides.py --overrides
    python scripts/fetch_yahoo_overrides.py --history-overrides [--backfill]
"""

import argparse
import json
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from fetch_yahoo import fetch_yahoo_daily, fetch_latest_from_yahoo, YahooFetchError
from fetch_fx import fetch_fx_daily   # ECB-primary FX (CI-resilient); override PRICES stay on Yahoo
import currency_convert as cc

OVERRIDES_PATH = ROOT / "data" / "registries" / "data_source_overrides.json"
EQUITIES_PATH  = ROOT / "data" / "prices" / "equities.json"
HISTORY_DIR    = ROOT / "data" / "prices" / "history"
INTER_CALL_SLEEP = 0.10  # 100ms between Yahoo calls — conservative


def load_active_overrides():
    """Return list of (robotnik_ticker, yahoo_symbol) pairs that need Yahoo backfill.

    Filters to entries whose `applies_to_vendors` includes "marketstack" — these
    are the tickers MarketStack cannot serve. Skips `_meta` and entries flagged
    `provider: skip` (e.g. registry duplicates like MOG/A).
    """
    with open(OVERRIDES_PATH) as f:
        overrides = json.load(f)
    out = []
    for ticker, entry in overrides.items():
        if ticker.startswith("_"):
            continue
        if not isinstance(entry, dict):
            continue
        provider = entry.get("provider")
        if provider == "skip":
            continue
        applies = entry.get("applies_to_vendors") or []
        if "marketstack" not in applies and "eodhd" not in applies:
            continue
        yahoo_sym = entry.get("yahoo_symbol")
        if not yahoo_sym:
            continue
        out.append((ticker, yahoo_sym, entry))
    return out


def ticker_to_filename(ticker):
    """Map Robotnik ticker to history-file basename (matches MS fetcher)."""
    return ticker.replace(" ", "_").replace("/", "_")


def cmd_overrides():
    """Fetch latest EOD for each override and merge into equities.json."""
    targets = load_active_overrides()
    print("=" * 60)
    print("YAHOO OVERRIDE FETCHER — latest EOD")
    print("  {} override tickers to fetch".format(len(targets)))
    print("=" * 60)
    cc.refresh_all(fetcher=fetch_fx_daily)

    # Load existing equities.json to merge into
    eq = {"equities": []}
    if EQUITIES_PATH.exists():
        with open(EQUITIES_PATH) as f:
            eq = json.load(f)
    by_ticker = {e["ticker"]: e for e in eq.get("equities", [])}

    ok = failed = 0
    for ticker, yahoo_sym, entry in targets:
        try:
            row = fetch_latest_from_yahoo(yahoo_sym)
            # Yahoo reports the true native currency (incl. GBp); convert to USD
            # via daily FX so overrides match the MarketStack USD convention.
            native_ccy = row["currency"]
            usd_price = cc.to_usd(row["price"], native_ccy, row["date"])
            by_ticker[ticker] = {
                "ticker": ticker,
                "yahoo_symbol": yahoo_sym,
                "name": (entry.get("reason") or "").split(" — ")[0][:60] or ticker,
                "price": usd_price,          # USD (daily-FX converted)
                "currency": "USD",
                "native_price": row["price"],
                "native_currency": native_ccy,
                "change_pct": row["change_pct"],
                "volume": row["volume"],
                "date": row["date"],
                "source": "Yahoo (override)",
            }
            ok += 1
            print("  OK  {:14s} ({:14s}) {} {} → ${} @ {}".format(
                ticker, yahoo_sym, row["price"], native_ccy, usd_price, row["date"]))
        except YahooFetchError as e:
            failed += 1
            print("  FAIL {:14s} ({:14s}) {}".format(ticker, yahoo_sym, str(e)[:80]))
        time.sleep(INTER_CALL_SLEEP)

    # Reassemble + write
    eq["equities"] = list(by_ticker.values())
    eq["fetched_at"] = datetime.utcnow().isoformat() + "Z"
    eq["source"] = (eq.get("source") or "MarketStack") + " + Yahoo overrides"
    eq["count"] = len(eq["equities"])
    with open(EQUITIES_PATH, "w") as f:
        json.dump(eq, f, indent=2)

    print("\nRESULT: {} ok, {} failed".format(ok, failed))
    print("Output: {}".format(EQUITIES_PATH.relative_to(ROOT)))


def cmd_history_overrides(backfill=False):
    """Fetch history for each override ticker and write per-ticker JSON."""
    targets = load_active_overrides()
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 60)
    print("YAHOO OVERRIDE FETCHER — history ({})".format(
        "5Y backfill" if backfill else "compact refresh"))
    print("  {} override tickers to fetch".format(len(targets)))
    print("=" * 60)
    cc.refresh_all(backfill=backfill, fetcher=fetch_fx_daily)

    size = "5y" if backfill else "compact"
    ok = failed = 0
    for ticker, yahoo_sym, entry in targets:
        fname = ticker_to_filename(ticker)
        hpath = HISTORY_DIR / "{}.json".format(fname)
        try:
            data = fetch_yahoo_daily(yahoo_sym, output_size=size)
            native_ccy = data.get("currency")
            # data["series"] is a dict of date → {open, high, low, close, volume}.
            # Convert each bar to USD at its own date's FX rate.
            series_rows = []
            for d in sorted(data["series"]):
                pt = data["series"][d]
                series_rows.append({
                    "date": d,
                    "open":   cc.to_usd(pt.get("open"), native_ccy, d),
                    "high":   cc.to_usd(pt.get("high"), native_ccy, d),
                    "low":    cc.to_usd(pt.get("low"), native_ccy, d),
                    "close":  cc.to_usd(pt.get("close"), native_ccy, d),
                    "volume": pt.get("volume"),
                })
            # Merge with existing if compact refresh
            if not backfill and hpath.exists():
                try:
                    existing = json.loads(hpath.read_text())
                    by_date = {r["date"]: r for r in existing.get("series", [])}
                    for r in series_rows:
                        by_date[r["date"]] = r
                    series_rows = [by_date[d] for d in sorted(by_date)]
                except Exception:
                    pass
            out = {
                "ticker": ticker,
                "yahoo_symbol": yahoo_sym,
                "currency": "USD",
                "native_currency": native_ccy,
                "series": series_rows,
                "last_fetched": datetime.utcnow().isoformat() + "Z",
                "source": "Yahoo (override, USD via daily FX)",
            }
            hpath.write_text(json.dumps(out, indent=2))
            ok += 1
            print("  OK  {:14s} ({:14s}) {} bars → {}".format(
                ticker, yahoo_sym, len(series_rows), hpath.name))
        except YahooFetchError as e:
            failed += 1
            print("  FAIL {:14s} ({:14s}) {}".format(ticker, yahoo_sym, str(e)[:80]))
        time.sleep(INTER_CALL_SLEEP)

    print("\nRESULT: {} ok, {} failed".format(ok, failed))


def main():
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--overrides", action="store_true",
                   help="Latest EOD for override tickers; merge into equities.json")
    g.add_argument("--history-overrides", action="store_true",
                   help="Daily history for override tickers; write to history/{ticker}.json")
    p.add_argument("--backfill", action="store_true",
                   help="With --history-overrides: pull 5Y instead of compact refresh")
    args = p.parse_args()

    if args.overrides:
        cmd_overrides()
    elif args.history_overrides:
        cmd_history_overrides(backfill=args.backfill)


if __name__ == "__main__":
    main()
