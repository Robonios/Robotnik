#!/usr/bin/env python3
"""
Staged v2-native 5Y history re-backfill (#55 INDEX RESTATEMENT).
================================================================
The committed data/prices/history/ was built on v1 + MIC-suffix symbols, so the
agorot/cross-listing/stale-tail/identity bugs the v2 cutover fixed for the DAILY
price also run through the whole 5Y series. Re-backfilling on v2-native restates
the index's historical values for international constituents — the published
track record shifts. This is justified (v2-native is more correct) but it IS a
restatement, so this script is deliberately NON-DESTRUCTIVE:

  • Writes the new series to data/prices/history_v2_staging/ ALONGSIDE the
    committed data/prices/history/ (preserved as the restatement baseline).
  • Routes each name to the SAME source the production pipeline uses
    (route_for_ticker: map-fresh → MarketStack v2; else → Yahoo override), so
    staging reflects what will ship, not a bespoke simulation.
  • Records per-name coverage (earliest / latest / n_bars) into a manifest so the
    validator can flag names whose v2 symbol does NOT extend back the full
    window — the listing/ticker-change class (Schaeffler / Hiab / JBT) where the
    current symbol lost its predecessor's pre-change history → stitch or a
    documented, surfaced gap.

NOTHING is swapped here. Run validate_history_restatement.py next; swap only
after per-name validation + the user checkpoint.

Usage:
    python scripts/rebackfill_history_v2.py                 # full universe
    python scripts/rebackfill_history_v2.py --only "SCC IT,CLS CN,NVDA"
"""
import argparse
import json
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from marketstack_client import (
    AuthError, MarketStackError, route_for_ticker, fetch_eod_historical,
    apply_split_adjustment, US_ADR_OVERRIDES, call_count,
)
from fetch_yahoo import fetch_yahoo_daily, YahooFetchError
from fetch_prices import EQUITIES
from guard_corporate_actions import load_route as load_ca_route
import currency_convert as cc
from fetch_fx import fetch_fx_daily

STAGING_DIR = ROOT / "data" / "prices" / "history_v2_staging"
MANIFEST = ROOT / "data" / "prices" / "history_v2_staging_manifest.json"
WINDOW_DAYS = 5 * 365 + 30   # ~5Y, matches the production backfill window


def ticker_to_filename(ticker):
    """Match the MS / Yahoo history fetchers' file naming exactly."""
    return ticker.replace(" ", "_").replace("/", "_")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="",
                    help="comma-separated ticker filter (validation subset); default = all")
    ap.add_argument("--resume", action="store_true",
                    help="skip names already staged this session (cheap recovery after an "
                         "interruption — a network drop RAISES mid-fetch so staged files are "
                         "complete, never truncated; the validator is the backstop)")
    args = ap.parse_args()
    only = {s.strip() for s in args.only.split(",") if s.strip()} or None

    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    date_to = date.today().isoformat()
    date_from = (date.today() - timedelta(days=WINDOW_DAYS)).isoformat()
    print("=" * 60)
    print("STAGED v2 HISTORY RE-BACKFILL (#55 restatement)")
    print("  window: {} → {}  (staging, NON-destructive)".format(date_from, date_to))
    if only:
        print("  subset: {}".format(sorted(only)))
    print("=" * 60)

    print("  refreshing 5Y FX (ECB primary, Yahoo TWD fallback)...")
    cc.refresh_all(backfill=True, fetcher=fetch_fx_daily)

    # Override map: the not-map-fresh residual routes to Yahoo (yahoo_symbol).
    try:
        _ov = json.loads((ROOT / "data" / "registries" / "data_source_overrides.json").read_text())
        OVERRIDE = {k: v for k, v in _ov.items()
                    if not k.startswith("_") and isinstance(v, dict) and v.get("provider") != "skip"}
    except Exception:
        OVERRIDE = {}
    # Corporate-action route (#55): names whose v2 split_factor misses a bonus/scrip/rights
    # → their HISTORY must come from Yahoo (which back-adjusts it). History-only; daily stays v2.
    CA_ROUTE = load_ca_route()
    if CA_ROUTE:
        print("  corporate-action route: {} names → Yahoo history ({})".format(
            len(CA_ROUTE), ", ".join(sorted(CA_ROUTE))))

    manifest = {}
    n_ms = n_yh = n_gap = n_err = n_skip = 0
    gaps = []
    universe = [e for e in EQUITIES if (only is None or e[0] in only)]

    for i, (ticker, name, sector, country) in enumerate(universe, 1):
        hpath = STAGING_DIR / "{}.json".format(ticker_to_filename(ticker))
        if args.resume and hpath.exists():
            n_skip += 1
            continue
        try:
            sym, ver, supported = route_for_ticker(ticker, country)
            ca = CA_ROUTE.get(ticker)
            ov = OVERRIDE.get(ticker)
            # Routing precedence for HISTORY: corporate-action route (Yahoo — v2's
            # split_factor misses this name's bonus/scrip/rights) > v2 map > Yahoo
            # override. The corporate-action route is HISTORY-ONLY; the daily latest
            # price stays v2 (post-all-events, hence correct).
            if ca:
                yahoo_sym, yahoo_reason = ca.get("yahoo_symbol"), "corporate-action route"
            elif supported:
                yahoo_sym, yahoo_reason = None, None
            elif ov:
                yahoo_sym, yahoo_reason = ov.get("yahoo_symbol"), "override"
            else:
                gaps.append(ticker)
                n_gap += 1
                manifest[ticker] = {"source": "GAP", "reason": "no_fresh_symbol_no_override"}
                continue

            if yahoo_sym:
                # Yahoo branch (corporate-action route OR not-map-fresh override). Yahoo's
                # series is already split + bonus/scrip adjusted → NO apply_split_adjustment.
                data = fetch_yahoo_daily(yahoo_sym, output_size="5y")
                native = data.get("currency")
                series = []
                for d in sorted(data.get("series", {})):
                    pt = data["series"][d]
                    if not pt.get("close"):
                        continue
                    series.append({
                        "date": d,
                        "open":  cc.to_usd(pt.get("open"), native, d),
                        "high":  cc.to_usd(pt.get("high"), native, d),
                        "low":   cc.to_usd(pt.get("low"), native, d),
                        "close": cc.to_usd(pt.get("close"), native, d),
                        "volume": pt.get("volume"),
                    })
                source = "Yahoo ({})".format(yahoo_reason)
                symkey, symval, ver = "yahoo_symbol", yahoo_sym, "yahoo"
                n_yh += 1
            else:
                # MarketStack v2 — split-adjust the raw native series, then convert
                # each bar at its OWN date's FX (true USD returns).
                rows = fetch_eod_historical(sym, date_from, date_to,
                                            throttle=False, version=ver)
                rows = [r for r in rows
                        if r.get("close") is not None and float(r.get("close")) > 0]
                if not rows:
                    raise RuntimeError("no_nonzero_rows")
                is_adr = (ticker in US_ADR_OVERRIDES) or (ticker.split(" ", 1)[0] in US_ADR_OVERRIDES)
                native = cc.currency_for_marketstack(sym, ticker, country, is_adr)
                adj = apply_split_adjustment(rows, sym)
                series = []
                for r in adj:
                    d = r.get("date")
                    if not d:
                        continue
                    series.append({
                        "date": d,
                        "open":  cc.to_usd(r.get("open"), native, d),
                        "high":  cc.to_usd(r.get("high"), native, d),
                        "low":   cc.to_usd(r.get("low"), native, d),
                        "close": cc.to_usd(r.get("close"), native, d),
                        "volume": r.get("volume"),
                    })
                source = "MarketStack v2"
                symkey, symval = "marketstack_symbol", sym
                n_ms += 1

            series.sort(key=lambda r: r["date"])
            earliest = series[0]["date"] if series else None
            latest = series[-1]["date"] if series else None
            out = {
                "ticker": ticker, symkey: symval, "marketstack_version": ver,
                "name": name, "sector": sector, "country": country,
                "native_currency": native, "series": series,
                "source": source + " (USD via daily FX)",
                "_rebackfill": {"earliest": earliest, "latest": latest, "n_bars": len(series)},
            }
            hpath.write_text(json.dumps(out, indent=2))
            manifest[ticker] = {"source": source, "symbol": symval,
                                "native_currency": native, "n_bars": len(series),
                                "earliest": earliest, "latest": latest}
        except AuthError:
            raise  # fatal — never silently degrade on auth
        except (YahooFetchError, MarketStackError, RuntimeError, cc.CurrencyError) as e:
            n_err += 1
            manifest[ticker] = {"source": "ERROR", "reason": str(e)[:120]}
            print("  ERR  {:12} {}".format(ticker, str(e)[:80]))

        if i % 40 == 0:
            print("  [{}/{}] ms-v2={} yahoo={} gap={} err={} skip={} (calls {})".format(
                i, len(universe), n_ms, n_yh, n_gap, n_err, n_skip, call_count()))
        time.sleep(0.03)

    # Merge into any existing manifest so a targeted --only re-stage (e.g. restaging
    # just the corporate-action class) preserves the entries for names not processed
    # this run, rather than clobbering the full-universe manifest.
    merged = {}
    if MANIFEST.exists():
        try:
            merged = json.loads(MANIFEST.read_text()).get("names", {})
        except Exception:
            merged = {}
    merged.update(manifest)
    MANIFEST.write_text(json.dumps({
        "_meta": {"staged_at": datetime.now(timezone.utc).isoformat() + "Z",
                  "window": [date_from, date_to],
                  "this_run": {"ms_v2": n_ms, "yahoo": n_yh, "gap": n_gap, "err": n_err,
                               "subset": sorted(only) if only else "ALL"},
                  "n_names": len(merged),
                  "staging_dir": str(STAGING_DIR.relative_to(ROOT))},
        "names": merged}, indent=2))

    print("\n" + "=" * 60)
    print("STAGED: ms-v2={} yahoo={} gap={} err={} skip={}  → {}".format(
        n_ms, n_yh, n_gap, n_err, n_skip, STAGING_DIR.relative_to(ROOT)))
    if gaps:
        print("  GAPS (no source — completeness):", ", ".join(sorted(gaps)))
    print("  manifest: {}".format(MANIFEST.relative_to(ROOT)))
    print("  API calls used: {}".format(call_count()))
    print("  NEXT: validate_history_restatement.py  (NOTHING swapped yet)")


if __name__ == "__main__":
    try:
        main()
    except AuthError as e:
        print("AUTH FAIL: {}".format(e), file=sys.stderr)
        sys.exit(2)
