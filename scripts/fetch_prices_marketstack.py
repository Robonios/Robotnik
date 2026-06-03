#!/usr/bin/env python3
"""
MarketStack-routed price fetcher — D1 of the EODHD → MarketStack cutover.

Produces the same `data/prices/equities.json` output shape as the legacy
`fetch_prices.py` so downstream pipeline (calculate_index.py,
enrich_equities.py, etc.) is vendor-agnostic.

Per-ticker routing follows `scripts/marketstack_client.route_for_ticker`:
  - MARKETSTACK_UNSUPPORTED tickers are skipped here; caller runs
    `scripts/fetch_yahoo.py --overrides` to back-fill from Yahoo
  - TICKER_OVERRIDES route to per-ticker (symbol, version) pairs
  - US_ADR_OVERRIDES route to bare US on V1
  - Country defaults follow COUNTRY_TO_MIC + COUNTRY_TO_API_VERSION

Usage:
    python scripts/fetch_prices_marketstack.py
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from marketstack_client import (
    AuthError, MarketStackError, MissingKeyError, RateLimitError,
    TransportError, UnknownSymbolError,
    INTER_CALL_SLEEP, call_count, route_for_ticker,
    fetch_eod_latest, US_ADR_OVERRIDES,
)
from fetch_prices import EQUITIES, guess_currency  # canonical universe
import currency_convert as cc
from fetch_fx import fetch_fx_daily   # ECB-primary FX (CI-resilient), Yahoo fallback for TWD

OUTPUT_PATH = ROOT / "data" / "prices" / "equities.json"


def normalise_iso_date(d):
    """MarketStack returns '2026-05-22T00:00:00+0000'; we want '2026-05-22'."""
    if not d:
        return None
    return str(d).split("T", 1)[0]


def main():
    print("=" * 60)
    print("ROBOTNIK PRICE FETCHER — MarketStack")
    print("  Universe: {} equities".format(len(EQUITIES)))
    print("=" * 60)

    print("  Refreshing daily FX rates (native → USD)...")
    cc.refresh_all(fetcher=fetch_fx_daily)

    results = []
    skipped_yahoo = []     # tickers in MARKETSTACK_UNSUPPORTED → caller routes to Yahoo
    failed = []            # tickers that should resolve but didn't

    for i, (ticker, name, sector, country) in enumerate(EQUITIES, 1):
        sym, ver, supported = route_for_ticker(ticker, country)
        if not supported:
            # Either MARKETSTACK_UNSUPPORTED (intentional Yahoo route) OR
            # country_not_mapped (registry hygiene gap).
            if sym == "UNAVAILABLE":
                # Distinguish the two cases via the unsupported set membership.
                from marketstack_client import MARKETSTACK_UNSUPPORTED
                if ticker in MARKETSTACK_UNSUPPORTED:
                    skipped_yahoo.append({"ticker": ticker, "name": name,
                                          "sector": sector, "country": country,
                                          "reason": "marketstack_unsupported"})
                else:
                    failed.append({"ticker": ticker, "name": name,
                                   "country": country,
                                   "reason": "country_not_mapped"})
            continue

        try:
            rows = fetch_eod_latest([sym], limit=1, throttle=False, version=ver)
        except AuthError:
            raise  # fatal
        except UnknownSymbolError:
            failed.append({"ticker": ticker, "name": name,
                           "country": country, "ms_symbol": sym,
                           "reason": "unknown_symbol"})
            time.sleep(INTER_CALL_SLEEP)
            continue
        except (RateLimitError, TransportError) as e:
            failed.append({"ticker": ticker, "name": name,
                           "country": country, "ms_symbol": sym,
                           "reason": "transport:{}".format(str(e)[:80])})
            time.sleep(INTER_CALL_SLEEP)
            continue
        except MarketStackError as e:
            failed.append({"ticker": ticker, "name": name,
                           "country": country, "ms_symbol": sym,
                           "reason": "other:{}".format(str(e)[:80])})
            time.sleep(INTER_CALL_SLEEP)
            continue

        if not rows:
            failed.append({"ticker": ticker, "name": name,
                           "country": country, "ms_symbol": sym,
                           "reason": "empty_response"})
            time.sleep(INTER_CALL_SLEEP)
            continue

        r = rows[0]
        # Raw close (price-return basis). The latest bar needs no split
        # adjustment (no future corporate action); history is split-adjusted
        # separately. See metrics_methodology §13.
        close = r.get("close")
        prev = r.get("open")  # not always populated; use open as proxy
        change_pct = None
        if close is not None and prev and prev > 0:
            # % change is currency-invariant (same-day, same currency)
            change_pct = round((float(close) - float(prev)) / float(prev) * 100, 2)

        # Native currency from the routed exchange (NOT the broken guess on the
        # MS symbol), then convert to USD via daily FX. ADR-routed names are USD.
        is_adr = (ticker in US_ADR_OVERRIDES) or (ticker.split(" ", 1)[0] in US_ADR_OVERRIDES)
        date_iso = normalise_iso_date(r.get("date"))
        try:
            native_ccy = cc.currency_for_marketstack(sym, ticker, country, is_adr)
            usd_price = cc.to_usd(close, native_ccy, date_iso)
        except cc.CurrencyError as ce:
            failed.append({"ticker": ticker, "name": name, "country": country,
                           "ms_symbol": sym, "reason": "currency:{}".format(str(ce)[:80])})
            time.sleep(INTER_CALL_SLEEP)
            continue

        results.append({
            "ticker": ticker,
            "marketstack_symbol": sym,
            "marketstack_version": ver,
            "name": name,
            "sector": sector,
            "country": country,
            "price": usd_price,          # USD (daily-FX converted)
            "currency": "USD",
            "native_price": close,       # raw exchange close, for audit
            "native_currency": native_ccy,
            "change_pct": change_pct,
            "volume": r.get("volume"),
            "date": date_iso,
            "source": "MarketStack",
        })

        if i % 50 == 0:
            print("  [{}/{}] {} resolved, {} skipped-yahoo, {} failed (calls: {})".format(
                i, len(EQUITIES), len(results), len(skipped_yahoo),
                len(failed), call_count()))
        time.sleep(INTER_CALL_SLEEP)

    output = {
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "count": len(results),
        "source": "MarketStack (+ Yahoo overrides via fetch_yahoo.py --overrides)",
        "marketstack_resolved": len(results),
        "skipped_for_yahoo_backfill": len(skipped_yahoo),
        "failed": len(failed),
        "api_calls_used": call_count(),
        "equities": results,
        "skipped_yahoo": skipped_yahoo,
        "failed_detail": failed,
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print("\n" + "=" * 60)
    print("RESULT")
    print("  MarketStack resolved: {} / {}".format(len(results), len(EQUITIES)))
    print("  Skipped for Yahoo backfill: {} (run fetch_yahoo.py --overrides)".format(
        len(skipped_yahoo)))
    print("  Failed: {}".format(len(failed)))
    print("  API calls used: {}".format(call_count()))
    print("  Output: {}".format(OUTPUT_PATH.relative_to(ROOT)))
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
