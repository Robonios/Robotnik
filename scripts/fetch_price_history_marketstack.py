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
    INTER_CALL_SLEEP, call_count, route_for_ticker,
    fetch_eod_historical, US_ADR_OVERRIDES, apply_split_adjustment,
)
from fetch_prices import EQUITIES
from guard_corporate_actions import load_route as load_ca_route
import currency_convert as cc
from fetch_fx import fetch_fx_daily   # ECB-primary FX (CI-resilient), Yahoo fallback for TWD

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
    cc.refresh_all(backfill=args.backfill, fetcher=fetch_fx_daily)

    # UNIFORM-V2 (#55): names not MS-fresh must have a Yahoo override (the residual,
    # back-filled via fetch_yahoo.py --history-overrides); any with neither is a
    # resolution-completeness gap, surfaced + gated below. Mirrors the daily
    # fetcher's gate EXACTLY so the two pipelines route identically — a divergence
    # here would seam the history tail against the daily price.
    try:
        _ov = json.loads((ROOT / "data" / "registries" / "data_source_overrides.json").read_text())
        OVERRIDE_TICKERS = {k for k, v in _ov.items()
                            if not k.startswith("_") and isinstance(v, dict) and v.get("provider") != "skip"}
    except Exception:
        OVERRIDE_TICKERS = set()

    # Corporate-action route (#55): names whose v2 split_factor misses a bonus/scrip/rights.
    # Their HISTORY is Yahoo-sourced (fetch_yahoo_overrides --history-overrides); skip them
    # here so the v2 path does not re-write them under-adjusted on each refresh. Daily latest
    # price still uses v2 (post-all-events, correct). Surfaced by guard_corporate_actions.
    CA_ROUTE = load_ca_route()

    refreshed = 0
    skipped_yahoo = 0
    failed = 0
    backfilled = 0
    gaps = []   # routable names with neither an MS-fresh symbol nor a Yahoo override

    for i, (ticker, name, sector, country) in enumerate(EQUITIES, 1):
        fname = ticker_to_filename(ticker)
        hpath = HISTORY_DIR / "{}.json".format(fname)

        if args.backfill and hpath.exists():
            continue  # backfill only for new tickers without history

        if ticker in CA_ROUTE:
            # v2 misses this name's corporate action → Yahoo-sourced history. Skip the
            # v2 path (fetch_yahoo_overrides --history-overrides writes it instead).
            skipped_yahoo += 1
            continue

        sym, ver, supported = route_for_ticker(ticker, country)
        if not supported:
            # not MS-fresh → Yahoo override (history-overrides path). No override =
            # completeness gap → surfaced + gated (same as the daily fetcher).
            if ticker in OVERRIDE_TICKERS:
                skipped_yahoo += 1
            else:
                gaps.append(ticker)
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

        # Drop non-positive-close bars (v2 unsettled current day / dead-listing
        # zeros) BEFORE adjust+convert — a 0 close becomes $0 and a −100%/+inf
        # return artifact in the 5y series. Mirrors the daily path's
        # non-zero-close rule (fetch_v2_eod scans for the first real close).
        rows = [r for r in rows if r.get("close") is not None and float(r.get("close")) > 0]
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
        # PRICE-RETURN split adjustment from the reliable split_factor (NOT MS
        # adj_close, which is systemically broken — see §13), then convert the
        # split-adjusted NATIVE price to USD via daily FX.
        adj_rows = apply_split_adjustment(rows, sym)
        conv_rows = []
        for r in adj_rows:
            d = r.get("date")
            if not d:
                continue
            conv_rows.append({
                "date": d,
                "open":  cc.to_usd(r.get("open"), native_ccy, d),
                "high":  cc.to_usd(r.get("high"), native_ccy, d),
                "low":   cc.to_usd(r.get("low"), native_ccy, d),
                "close": cc.to_usd(r.get("close"), native_ccy, d),
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

    # Resolution-completeness guard (#55) — mirror the daily fetcher: every
    # routable entity must be EITHER MS-fresh OR have a Yahoo override. A name
    # with neither would silently stop refreshing its history → a return seam
    # against its fresh daily price. Surface + fail rather than degrade silently.
    # In the normal pipeline the daily fetcher hard-gates this FIRST, so history
    # sees gaps only if run standalone — failing loud is still correct there.
    if gaps:
        print("FATAL: resolution-completeness violation (history) — {} routable name(s) have "
              "neither a fresh MarketStack symbol nor a Yahoo override: {}. Re-run "
              "resolve_marketstack_symbols.py or add a data_source_overrides entry."
              .format(len(gaps), ", ".join(sorted(gaps))), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except MissingKeyError as e:
        print("FAIL: {}".format(e))
        sys.exit(1)
    except AuthError as e:
        print("AUTH FAIL: {}".format(e))
        sys.exit(2)
