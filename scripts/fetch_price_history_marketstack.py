#!/usr/bin/env python3
"""
MarketStack-routed price history fetcher — D1 of EODHD → MarketStack cutover.

Mirrors `scripts/fetch_price_history.py --refresh` behaviour:
  - Pulls a 45-day rolling window per ticker
  - Merges with existing on-disk history under `data/prices/history/`
  - Preserves the same per-ticker output JSON shape so calculate_index.py /
    enrich_equities.py work unchanged

Skips MARKETSTACK_UNSUPPORTED tickers — caller runs
`scripts/fetch_yahoo.py --history-overrides` to back-fill from Yahoo.

Usage:
    python scripts/fetch_price_history_marketstack.py --refresh
    python scripts/fetch_price_history_marketstack.py --backfill   (5Y for new tickers)
"""

import argparse
import json
import os
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from marketstack_client import (
    AuthError, MarketStackError, MissingKeyError, RateLimitError,
    TransportError, UnknownSymbolError,
    INTER_CALL_SLEEP, MARKETSTACK_UNSUPPORTED, call_count, route_for_ticker,
    fetch_eod_historical, US_ADR_OVERRIDES,
)
from fetch_prices import EQUITIES
import currency_convert as cc
from fetch_yahoo import fetch_yahoo_daily

HISTORY_DIR = ROOT / "data" / "prices" / "history"
HISTORY_DIR.mkdir(parents=True, exist_ok=True)

REFRESH_WINDOW_DAYS = 45
BACKFILL_WINDOW_DAYS = 5 * 365 + 30  # ~5Y


def ticker_to_filename(ticker):
    """Map Robotnik ticker (e.g. "012450 KS") to history-file basename."""
    return ticker.replace(" ", "_").replace("/", "_")


def merge_series(existing, new_rows):
    """Merge new rows into existing series, dedup by date, keep latest."""
    by_date = {row["date"]: row for row in existing.get("series", [])}
    for r in new_rows:
        d = str(r.get("date", "")).split("T", 1)[0]
        if not d:
            continue
        by_date[d] = {
            "date": d,
            "open":  r.get("open"),
            "high":  r.get("high"),
            "low":   r.get("low"),
            "close": r.get("close"),
            "volume": r.get("volume"),
        }
    return [by_date[d] for d in sorted(by_date)]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--refresh", action="store_true",
                   help="45-day window for all tickers, merge with existing")
    p.add_argument("--backfill", action="store_true",
                   help="5Y window for tickers with no on-disk history")
    args = p.parse_args()
    if not (args.refresh or args.backfill):
        p.error("Specify --refresh or --backfill")

    window_days = BACKFILL_WINDOW_DAYS if args.backfill else REFRESH_WINDOW_DAYS
    date_to = date.today().isoformat()
    date_from = (date.today() - timedelta(days=window_days)).isoformat()

    print("=" * 60)
    print("ROBOTNIK PRICE HISTORY — MarketStack")
    print("  Mode: {}".format("backfill 5Y" if args.backfill else "refresh 45D"))
    print("  Window: {} → {}".format(date_from, date_to))
    print("=" * 60)

    print("  Refreshing daily FX rates (native → USD)...")
    cc.refresh_all(backfill=args.backfill, fetcher=fetch_yahoo_daily)

    refreshed = 0
    skipped_yahoo = 0
    failed = 0
    backfilled = 0

    for i, (ticker, name, sector, country) in enumerate(EQUITIES, 1):
        fname = ticker_to_filename(ticker)
        hpath = HISTORY_DIR / "{}.json".format(fname)

        if args.backfill and hpath.exists():
            continue  # backfill only for new tickers without history

        sym, ver, supported = route_for_ticker(ticker, country)
        if not supported:
            if ticker in MARKETSTACK_UNSUPPORTED:
                skipped_yahoo += 1
            else:
                failed += 1
            continue

        try:
            rows = fetch_eod_historical(sym, date_from, date_to,
                                        throttle=False, version=ver)
        except AuthError:
            raise
        except UnknownSymbolError:
            failed += 1
            time.sleep(INTER_CALL_SLEEP)
            continue
        except (RateLimitError, TransportError) as e:
            print("  WARN: {} ({}): {}".format(ticker, sym, str(e)[:80]))
            failed += 1
            time.sleep(INTER_CALL_SLEEP)
            continue
        except MarketStackError as e:
            print("  WARN: {} ({}): {}".format(ticker, sym, str(e)[:80]))
            failed += 1
            time.sleep(INTER_CALL_SLEEP)
            continue

        if not rows:
            failed += 1
            time.sleep(INTER_CALL_SLEEP)
            continue

        # Load existing on-disk history for merge (refresh mode)
        existing = {"ticker": ticker, "name": name, "sector": sector, "series": []}
        if hpath.exists() and args.refresh:
            try:
                existing = json.loads(hpath.read_text())
            except Exception:
                pass

        # Convert each bar to USD at its OWN date's FX rate → true USD returns.
        is_adr = (ticker in US_ADR_OVERRIDES) or (ticker.split(" ", 1)[0] in US_ADR_OVERRIDES)
        try:
            native_ccy = cc.currency_for_marketstack(sym, ticker, country, is_adr)
        except cc.CurrencyError as ce:
            print("  WARN: {} currency: {}".format(ticker, str(ce)[:80]))
            failed += 1
            time.sleep(INTER_CALL_SLEEP)
            continue
        # Use adj_* (split + dividend adjusted = total-return basis) so stock
        # splits (e.g. NVDA/AVGO 10:1) don't create artificial -90% bars. Falls
        # back to raw if an adjusted field is absent. TR basis MUST match the
        # benchmark series (also adjusted) — see metrics_methodology §13.
        def _adj(rr, field):
            v = rr.get("adj_" + field)
            return v if v is not None else rr.get(field)
        conv_rows = []
        for r in rows:
            d = str(r.get("date", "")).split("T", 1)[0]
            if not d:
                continue
            conv_rows.append({
                "date": d,
                "open":  cc.to_usd(_adj(r, "open"), native_ccy, d),
                "high":  cc.to_usd(_adj(r, "high"), native_ccy, d),
                "low":   cc.to_usd(_adj(r, "low"), native_ccy, d),
                "close": cc.to_usd(_adj(r, "close"), native_ccy, d),
                "volume": r.get("volume"),
            })

        merged_series = merge_series(existing, conv_rows)
        out = {
            "ticker": ticker,
            "marketstack_symbol": sym,
            "marketstack_version": ver,
            "name": name,
            "sector": sector,
            "country": country,
            "native_currency": native_ccy,
            "series": merged_series,
            "last_fetched": datetime.utcnow().isoformat() + "Z",
            "source": "MarketStack (USD via daily FX)",
        }
        hpath.write_text(json.dumps(out, indent=2))

        if args.backfill:
            backfilled += 1
        else:
            refreshed += 1

        if i % 50 == 0:
            print("  [{}/{}] refreshed={} backfilled={} skipped-yahoo={} failed={} (calls: {})".format(
                i, len(EQUITIES), refreshed, backfilled, skipped_yahoo, failed, call_count()))
        time.sleep(INTER_CALL_SLEEP)

    print("\n" + "=" * 60)
    print("RESULT")
    print("  Refreshed: {}".format(refreshed))
    print("  Backfilled: {}".format(backfilled))
    print("  Skipped for Yahoo backfill: {} (run fetch_yahoo.py --history-overrides)".format(
        skipped_yahoo))
    print("  Failed: {}".format(failed))
    print("  API calls used: {}".format(call_count()))
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except MissingKeyError as e:
        print("FAIL: {}".format(e))
        sys.exit(1)
    except AuthError as e:
        print("AUTH FAIL: {}".format(e))
        sys.exit(2)
