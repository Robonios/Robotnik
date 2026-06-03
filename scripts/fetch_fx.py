#!/usr/bin/env python3
"""
ECB-primary FX fetcher (CI-resilient), drop-in for fetch_yahoo_daily's FX role.
==============================================================================
Yahoo `<CCY>USD=X` was the sole FX source for the whole price pipeline, but
Yahoo blocks the GitHub-Actions datacenter IP — so in CI the FX cache (which is
gitignored, hence absent on the runner) cannot be (re)built, every non-USD price
fails to convert, and the international book silently degrades to stale. The ECB
euro foreign-exchange reference rates are free, key-less, authoritative, and
reachable from CI — so they become the PRIMARY FX source here.

Coverage: the ECB daily reference set covers every currency the universe needs
EXCEPT TWD (Taiwan). Any currency ECB does not publish — and any transient ECB
failure — falls back to Yahoo (`fetch_yahoo_daily`), exactly the prior behaviour.
So this is a strict improvement with zero coverage regression and zero new
licensing commitment: the 12 ECB-covered currencies become CI-fresh; TWD keeps
its old Yahoo path (CI-stale, out-of-band-fresh, now backstopped by the
all_prices price age-floor). Closing the TWD-in-CI gap with a clean-terms
provider that covers it is the remaining #48 item.

Mechanics: ECB publishes EUR-based rates (foreign units per 1 EUR). The pipeline
wants USD per 1 foreign unit, so we cross through EUR:
    USD per 1 FOREIGN = (USD per EUR) / (FOREIGN per EUR)
and for EUR itself, USD per 1 EUR is the published USD line directly. Validated
against the prior Yahoo cache: sub-1% agreement on every currency (the expected
ECB-reference-fix vs Yahoo-intraday-spot drift).

Interface (matches fetch_yahoo_daily so it swaps in at the FX injection sites):
    fetch_fx_daily("JPYUSD=X", output_size="compact"|"1y"|"5y")
      -> {"currency": "JPY", "series": {"YYYY-MM-DD": {"close": <usd_per_unit>}},
          "source": "ECB"}                 # or the Yahoo dict on fallback

Stdlib only (urllib + xml.etree), consistent with the rest of the price layer.
"""
import sys
import urllib.request
import xml.etree.ElementTree as ET

# ECB euro reference rates. 90d file = recent tail (daily refresh / "compact");
# the full hist file (since 1999) backs "1y"/"5y" backfills.
ECB_90D  = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist-90d.xml"
ECB_HIST = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml"
_NS = {"g": "http://www.gesmes.org/xml/2002-08-01",
       "e": "http://www.ecb.int/vocabulary/2002-08-01/eurofxref"}

_ECB_CACHE = {}   # size-key ("90d"|"hist") -> {ccy: {date: usd_per_unit}}


def _ecb_url(output_size):
    return ECB_90D if output_size in ("compact", "90d", None) else ECB_HIST


def _fetch_ecb_table(output_size):
    """Parse an ECB reference-rate file into {ccy: {date: USD-per-1-unit}}.

    Memoised per file so a 13-currency refresh downloads each file once, not 13×.
    EUR is included with USD-per-EUR (the published USD line). Raises on network
    or parse failure so the caller can fall back to Yahoo.
    """
    key = "90d" if output_size in ("compact", "90d", None) else "hist"
    if key in _ECB_CACHE:
        return _ECB_CACHE[key]
    raw = urllib.request.urlopen(_ecb_url(output_size), timeout=30).read()
    root = ET.fromstring(raw)
    table = {}
    for daycube in root.findall(".//e:Cube/e:Cube[@time]", _NS):
        date = daycube.get("time")
        row = {}
        for c in daycube.findall("e:Cube", _NS):
            try:
                row[c.get("currency")] = float(c.get("rate"))
            except (TypeError, ValueError):
                continue
        usd_per_eur = row.get("USD")
        if not usd_per_eur:
            continue
        table.setdefault("EUR", {})[date] = usd_per_eur          # USD per 1 EUR
        for ccy, per_eur in row.items():
            if per_eur:
                table.setdefault(ccy, {})[date] = usd_per_eur / per_eur
    _ECB_CACHE[key] = table
    return table


def _ecb_series(ccy, output_size):
    """USD-per-1-unit series for `ccy` as {date: {"close": rate}}, or None if ECB
    does not publish it (e.g. TWD) — signalling the caller to fall back."""
    table = _fetch_ecb_table(output_size)
    dates = table.get(ccy)
    if not dates:
        return None
    return {d: {"close": r} for d, r in dates.items()}


def fetch_fx_daily(symbol, output_size="compact"):
    """ECB-primary FX with Yahoo fallback. Drop-in for fetch_yahoo_daily.

    `symbol` is the pipeline's `<CCY>USD=X` form. Returns USD-per-1-CCY closes
    from ECB where available; otherwise (currency ECB lacks, or any ECB error)
    delegates to fetch_yahoo_daily so behaviour never regresses below today's.
    """
    ccy = symbol.split("USD=X", 1)[0] if "USD=X" in symbol else symbol
    if ccy and ccy != "USD":
        try:
            series = _ecb_series(ccy, output_size)
            if series:
                return {"currency": ccy, "series": series, "source": "ECB"}
        except Exception as e:
            sys.stderr.write("[fetch_fx] ECB fetch failed for {} ({}); "
                             "falling back to Yahoo\n".format(ccy, str(e)[:80]))
    # ECB does not cover this currency (TWD) or ECB is unreachable → Yahoo.
    from fetch_yahoo import fetch_yahoo_daily
    return fetch_yahoo_daily(symbol, output_size=output_size)


if __name__ == "__main__":
    # Self-test: ECB for the covered set, Yahoo fallback for TWD.
    for sym in ["JPYUSD=X", "EURUSD=X", "GBPUSD=X", "KRWUSD=X", "ILSUSD=X", "TWDUSD=X"]:
        d = fetch_fx_daily(sym, output_size="compact")
        ser = d.get("series") or {}
        latest = max(ser) if ser else None
        print("{:10} source={:6} n={:>4}  latest {} -> {}".format(
            sym, d.get("source", "Yahoo"), len(ser), latest,
            ser.get(latest, {}).get("close") if latest else "EMPTY"))
