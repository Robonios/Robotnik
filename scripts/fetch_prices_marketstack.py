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
    fetch_eod_latest, fetch_v2_eod, US_ADR_OVERRIDES,
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


def require_marketstack_resolved(n_resolved, n_failed, api_calls):
    """Fail loud on a SYSTEMIC MarketStack failure — 0 names resolved while names
    WERE routable. That is not a partial miss (assemble's merge handles a few
    dropped names); it is an outage — a missing/mismatched MARKETSTACK_API_KEY
    (the secret-name-mismatch class that froze the book), an auth failure, or a
    total IP block. Without this, the merge silently retains the ENTIRE prior
    book and the run goes GREEN on stale data. Exit non-zero so the step errors
    and the pipeline serves last-good instead of committing a frozen book. Makes
    a post-key-fix run self-verifying: it can only pass if MS actually resolved.
    """
    routable = n_resolved + n_failed
    if routable > 0 and n_resolved == 0:
        print("FATAL: MarketStack resolved 0 of {} routable names "
              "(api_calls_used={}) — SYSTEMIC vendor failure (missing/mismatched "
              "MARKETSTACK_API_KEY, auth, or total block), NOT a partial miss. "
              "Failing the run to serve last-good rather than commit a "
              "green-but-stale book.".format(routable, api_calls), file=sys.stderr)
        sys.exit(1)


# Resolution-completeness: >= this many routable names unresolved in ONE run is SYSTEMIC
# (a resolver regression, a vendor-catalogue change, a key/auth failure) and halts, rather
# than silently publishing a book missing that many names. 1-2 is consistent with
# INDIVIDUAL corporate actions (a delisting, a re-ticker) resolving separately, so those
# are quarantine-and-continue instead of the blunt whole-pipeline FATAL (the SkyWater
# lesson). The bias is deliberate: a false FATAL is a recoverable halt; a false mass-
# quarantine silently corrupts the index. Resolver-induced mass regressions are caught
# upstream by check_entity_lifecycle --validate (E3) before a map is committed.
SYSTEMIC_GAP_THRESHOLD = 3


def _quarantine_route_gaps(gaps):
    """Flag route-less names in the shared candidate store. calculate_index reads this into
    the reverse-parity guard's `_documented` set, so a quarantined name is documented-out
    (not 'missing') and does not trip the guard; the weekly quarantine report reads it too."""
    path = ROOT / "data" / "quarantine" / "auto_quarantine_candidates.json"
    cand = {}
    if path.exists():
        try:
            cand = json.loads(path.read_text())
        except Exception:
            cand = {}
    now = datetime.utcnow().isoformat() + "Z"
    for tk in gaps:
        cand[tk] = {"source": "completeness_guard", "signal": "route_gap",
                    "reason": "no fresh v2 symbol and no Yahoo override — suspected "
                              "delisting / re-ticker", "flagged_date": now}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cand, indent=2))


def handle_route_gaps(gaps):
    """Softened resolution-completeness guard. Systemic (>= threshold) FATALs as before; an
    individual gap (1-2) is quarantined and the run CONTINUES, so one dead constituent no
    longer halts the whole pipeline."""
    if not gaps:
        return
    if len(gaps) >= SYSTEMIC_GAP_THRESHOLD:
        print("FATAL: resolution-completeness violation — {} routable name(s) have neither a "
              "fresh MarketStack symbol nor a Yahoo override: {}. {} at once is SYSTEMIC (a "
              "resolver regression / vendor-catalogue change / key failure), not individual "
              "corporate actions — halting rather than publishing a book missing {} names. "
              "Re-run resolve_marketstack_symbols.py or add data_source_overrides entries.".format(
              len(gaps), ", ".join(gaps), len(gaps), len(gaps)), file=sys.stderr)
        sys.exit(1)
    _quarantine_route_gaps(gaps)
    print("WARN: {} routable name(s) have no vendor route ({}) — AUTO-QUARANTINED for this run "
          "(dropped from the index, flagged in data/quarantine/auto_quarantine_candidates.json "
          "for human review); pipeline CONTINUES. Suspected delisting / re-ticker. A human "
          "confirms: exclude (delisted), re-key (re-ticker), or add an override.".format(
          len(gaps), ", ".join(gaps)), file=sys.stderr)


def main():
    print("=" * 60)
    print("ROBOTNIK PRICE FETCHER — MarketStack")
    print("  Universe: {} equities".format(len(EQUITIES)))
    print("=" * 60)

    print("  Refreshing daily FX rates (native → USD)...")
    cc.refresh_all(fetcher=fetch_fx_daily)

    # UNIFORM-V2 (#55): names not MS-fresh must have a Yahoo override; any with
    # neither is a resolution-completeness gap, surfaced + gated below.
    try:
        _ov = json.loads((ROOT / "data" / "registries" / "data_source_overrides.json").read_text())
        OVERRIDE_TICKERS = {k for k, v in _ov.items()
                            if not k.startswith("_") and isinstance(v, dict) and v.get("provider") != "skip"}
    except Exception:
        OVERRIDE_TICKERS = set()

    results = []
    skipped_yahoo = []     # tickers in MARKETSTACK_UNSUPPORTED → caller routes to Yahoo
    failed = []            # tickers that should resolve but didn't

    for i, (ticker, name, sector, country) in enumerate(EQUITIES, 1):
        sym, ver, supported = route_for_ticker(ticker, country)
        if not supported:
            # UNIFORM-V2 (#55): not MS-fresh → route to the Yahoo override (the 28
            # recent-listing / native-EU residual). NO override = a resolution-
            # completeness gap → surfaced (and gated by the completeness guard).
            if ticker in OVERRIDE_TICKERS:
                skipped_yahoo.append({"ticker": ticker, "name": name,
                                      "sector": sector, "country": country,
                                      "reason": "yahoo_override"})
            else:
                failed.append({"ticker": ticker, "name": name,
                               "country": country,
                               "reason": "unresolved_no_override"})
            continue

        try:
            r = fetch_v2_eod(sym)
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

        if r is None:
            failed.append({"ticker": ticker, "name": name,
                           "country": country, "ms_symbol": sym,
                           "reason": "no_nonzero_close"})
            time.sleep(INTER_CALL_SLEEP)
            continue
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

    # Systemic-failure guard (write-then-gate): equities.json with failed_detail
    # is already persisted above for diagnosis; now fail loud if MS resolved zero
    # while names were routable (the secret-name-mismatch / auth / block class).
    require_marketstack_resolved(len(results), len(failed), call_count())

    # Resolution-completeness guard (#55): every routable entity must be EITHER
    # MS-fresh OR have a Yahoo override. A name with neither ("unresolved_no_override")
    # would silently drop from the book — surface it and fail rather than publish a
    # gap. (Catches a re-ticker / a newly-added universe name with no resolution.)
    gaps = sorted(f["ticker"] for f in failed if f.get("reason") == "unresolved_no_override")
    handle_route_gaps(gaps)   # softened: quarantine 1-2 and continue; FATAL if systemic


if __name__ == "__main__":
    try:
        main()
    except MissingKeyError as e:
        # Belt-and-suspenders: if a key error ever propagates uncaught, fail the
        # process (was: printed FAIL but exited 0 — a silent green on no data).
        print("FAIL: {}".format(e), file=sys.stderr)
        sys.exit(1)
        sys.exit(1)
    except AuthError as e:
        print("AUTH FAIL: {}".format(e))
        sys.exit(2)
