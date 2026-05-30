#!/usr/bin/env python3
"""
Shared currency → USD conversion for the Robotnik price pipeline.

Converts native-currency prices to USD using DAILY FX (each bar at its own
date's rate), so the index sees true USD returns (local return + FX return),
not fixed-FX or raw-local. Used by ALL THREE production price sources:
  - fetch_prices_marketstack.py        (MarketStack live)
  - fetch_price_history_marketstack.py (MarketStack history)
  - fetch_yahoo_overrides.py           (Yahoo override live + history)

Design / guarantees:
  - MIC/exchange-suffix → currency map for MarketStack-routed symbols, with a
    country→currency fallback so a local listing can never silently resolve to
    USD.
  - GBp (London pence) handled per ACTUAL quote convention: only when the
    source currency is GBp/GBX is the price divided by 100 (then the GBP rate
    applied). Pounds-quoted London listings are NOT divided.
  - Daily FX history sourced from Yahoo `<CCY>USD=X` (USD per 1 local unit),
    cached to data/prices/fx/<CCY>.json.
  - fx_rate(): exact date → most-recent-prior (weekend/holiday fill) →, only if
    the target predates FX coverage, the earliest rate WITH a one-time
    staleness warning. It NEVER returns 1.0 for a non-USD currency, and raises
    CurrencyError for an unknown currency or total FX miss — silence here would
    reintroduce the very bug this module exists to kill.
"""

import bisect
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FX_DIR = ROOT / "data" / "prices" / "fx"
FX_DIR.mkdir(parents=True, exist_ok=True)

# Gap (in days) beyond which a prior-date FX fill is considered suspicious and
# warned. Weekends/holidays sit well inside this; anything larger is flagged.
PRIOR_FILL_WARN_DAYS = 7


class CurrencyError(Exception):
    """Raised when a currency cannot be resolved or has no FX rate."""


# ── MIC / exchange-suffix → currency (from the MarketStack-routed symbol) ──
# Keyed on the token after the final '.' in the routed symbol (e.g. "6857.T"
# → "T", "ASML.XAMS" → "XAMS"). GBp denotes London pence (÷100 handled below).
MIC_TO_CURRENCY = {
    # Japan
    "T": "JPY", "XTKS": "JPY", "XTKO": "JPY", "TSE": "JPY",
    # China A-shares
    "XSHE": "CNY", "XSHG": "CNY", "SS": "CNY", "SZ": "CNY", "SHE": "CNY", "SHG": "CNY",
    # Hong Kong
    "XHKG": "HKD", "HK": "HKD",
    # UK (pence)
    "L": "GBp", "XLON": "GBp", "LSE": "GBp",
    # Korea
    "XKRX": "KRW", "XKOS": "KRW", "KS": "KRW", "KQ": "KRW", "KO": "KRW",
    # Taiwan
    "XTAI": "TWD", "TW": "TWD", "TWO": "TWD",
    # Eurozone exchanges
    "XFRA": "EUR", "XETR": "EUR", "XETRA": "EUR", "F": "EUR", "DE": "EUR",
    "XPAR": "EUR", "PA": "EUR", "XAMS": "EUR", "AS": "EUR",
    "XMIL": "EUR", "MI": "EUR", "XBRU": "EUR", "BR": "EUR",
    "XHEL": "EUR", "HE": "EUR", "XMAD": "EUR", "MC": "EUR",
    "XWBO": "EUR", "VI": "EUR", "XDUB": "EUR", "IR": "EUR",
    # Other Europe
    "XSWX": "CHF", "SW": "CHF", "SWX": "CHF",
    "XSTO": "SEK", "ST": "SEK",
    "XOSL": "NOK", "OL": "NOK",
    # Israel
    "XTAE": "ILS", "TA": "ILS",
    # APAC / NA
    "XASX": "AUD", "AX": "AUD", "ASX": "AUD",
    "XTSE": "CAD", "TO": "CAD", "TSX": "CAD", "XTSX": "CAD",
    # US (and bare symbols)
    "US": "USD", "": "USD",
}

# Country → currency fallback (used only if the suffix is unrecognised, so a
# local listing can never silently default to USD).
COUNTRY_TO_CURRENCY = {
    "United States": "USD", "Japan": "JPY", "China": "CNY", "Hong Kong": "HKD",
    "United Kingdom": "GBp", "South Korea": "KRW", "Taiwan": "TWD",
    "Germany": "EUR", "France": "EUR", "Netherlands": "EUR", "Italy": "EUR",
    "Belgium": "EUR", "Finland": "EUR", "Austria": "EUR", "Ireland": "EUR",
    "Spain": "EUR", "Portugal": "EUR", "Luxembourg": "EUR",
    "Switzerland": "CHF", "Sweden": "SEK", "Norway": "NOK",
    "Australia": "AUD", "Canada": "CAD", "Israel": "ILS",
}

# Currencies we fetch FX for. GBp is NOT a Yahoo pair — it maps to GBP/100.
FX_CURRENCIES = ["JPY", "CNY", "EUR", "GBP", "HKD", "KRW", "TWD",
                 "CHF", "SEK", "NOK", "AUD", "CAD", "ILS"]

_FX_CACHE = {}          # ccy -> {"dates": [...sorted...], "rates": {date: rate}}
_WARNED_STALE = set()   # (ccy) one-time staleness warnings


def currency_for_marketstack(routed_symbol, ticker, country, is_adr=False):
    """Resolve the native currency of a MarketStack-routed price.

    Precedence: ADR override → USD; routed-symbol suffix → MIC_TO_CURRENCY;
    country fallback; else raise (never silently default to USD for a non-US
    name).
    """
    if is_adr:
        return "USD"
    suffix = routed_symbol.rsplit(".", 1)[1] if "." in (routed_symbol or "") else ""
    if suffix in MIC_TO_CURRENCY:
        return MIC_TO_CURRENCY[suffix]
    # Bare symbol with a non-US country is a red flag — fall back on country.
    if country in COUNTRY_TO_CURRENCY:
        ccy = COUNTRY_TO_CURRENCY[country]
        if suffix not in ("", "US") or country != "United States":
            sys.stderr.write(
                "[currency_convert] WARN: unmapped suffix {!r} for {} ({}), "
                "country-fallback → {}\n".format(suffix, ticker, routed_symbol, ccy))
        return ccy
    raise CurrencyError("cannot resolve currency for {} (symbol={!r}, country={!r})"
                        .format(ticker, routed_symbol, country))


def _fx_path(ccy):
    return FX_DIR / "{}.json".format(ccy)


def ensure_fx(ccy, backfill=False, fetcher=None):
    """Load (and refresh) the daily FX series for `ccy` (USD per 1 local unit).

    Returns {date: rate}. GBp uses the GBP series. backfill=True pulls 5Y;
    otherwise a compact tail is merged into the on-disk cache.
    """
    if ccy in ("USD",):
        return {}
    if ccy in ("GBp", "GBX"):
        ccy = "GBP"
    if ccy in _FX_CACHE and not backfill:
        return _FX_CACHE[ccy]["rates"]

    rates = {}
    p = _fx_path(ccy)
    if p.exists():
        try:
            rates = json.loads(p.read_text()).get("rates", {})
        except Exception:
            rates = {}

    if fetcher is not None and (backfill or not rates):
        size = "5y" if backfill else "1y"
        try:
            data = fetcher("{}USD=X".format(ccy), output_size=size)
            for d, bar in data.get("series", {}).items():
                c = bar.get("close")
                if c:
                    rates[d] = float(c)
            p.write_text(json.dumps({
                "currency": ccy, "quote": "{}USD=X".format(ccy),
                "meaning": "USD per 1 {}".format(ccy),
                "rates": rates,
            }, indent=2))
        except Exception as e:
            sys.stderr.write("[currency_convert] WARN: FX fetch failed for {}: {}\n"
                             .format(ccy, str(e)[:100]))

    _FX_CACHE[ccy] = {"dates": sorted(rates.keys()), "rates": rates}
    return rates


def fx_rate(ccy, date):
    """USD per 1 unit of `ccy` on `date`. Exact → prior-date → earliest(+warn).

    Raises CurrencyError on total miss. Never returns 1.0 for a non-USD ccy.
    """
    if ccy == "USD":
        return 1.0
    if ccy in ("GBp", "GBX"):
        ccy = "GBP"
    if ccy not in _FX_CACHE:
        ensure_fx(ccy)
    entry = _FX_CACHE.get(ccy)
    if not entry or not entry["dates"]:
        raise CurrencyError("no FX series for {} (date {})".format(ccy, date))
    rates, dates = entry["rates"], entry["dates"]
    if date in rates:
        return rates[date]
    # most-recent-prior
    i = bisect.bisect_right(dates, date)
    if i > 0:
        prior = dates[i - 1]
        gap = (datetime.strptime(date, "%Y-%m-%d") - datetime.strptime(prior, "%Y-%m-%d")).days
        if gap > PRIOR_FILL_WARN_DAYS and ccy not in _WARNED_STALE:
            _WARNED_STALE.add(ccy)
            sys.stderr.write("[currency_convert] WARN: stale FX for {} on {} — "
                             "using {} ({}d old)\n".format(ccy, date, prior, gap))
        return rates[prior]
    # target predates FX coverage → surface, use earliest (do NOT drop the bar)
    if ccy not in _WARNED_STALE:
        _WARNED_STALE.add(ccy)
        sys.stderr.write("[currency_convert] WARN: {} FX history starts {} but a "
                         "price bar is dated {} — using earliest rate for earlier "
                         "bars (FX shorter than price history)\n"
                         .format(ccy, dates[0], date))
    return rates[dates[0]]


def to_usd(price, currency, date):
    """Convert a native price to USD using the daily FX rate for `date`.

    GBp/GBX prices are divided by 100 (pence→pounds) before the GBP rate.
    Returns None for a None price. Raises CurrencyError on unresolved currency.
    """
    if price is None:
        return None
    if currency == "USD":
        return float(price)
    if currency in ("GBp", "GBX"):
        return round(float(price) / 100.0 * fx_rate("GBP", date), 6)
    return round(float(price) * fx_rate(currency, date), 6)


def fx_depth_report(price_start_date):
    """Report currencies whose FX history starts AFTER price_start_date."""
    short = []
    for ccy in FX_CURRENCIES:
        ensure_fx(ccy)
        dates = _FX_CACHE.get(ccy, {}).get("dates", [])
        if not dates:
            short.append((ccy, "NO FX DATA"))
        elif dates[0] > price_start_date:
            short.append((ccy, "FX starts {}".format(dates[0])))
    return short


def refresh_all(backfill=False, fetcher=None):
    """Fetch/refresh FX for every currency in FX_CURRENCIES."""
    out = {}
    for ccy in FX_CURRENCIES:
        r = ensure_fx(ccy, backfill=backfill, fetcher=fetcher)
        out[ccy] = len(r)
    return out


if __name__ == "__main__":
    from fetch_yahoo import fetch_yahoo_daily
    print("Backfilling 5Y FX for {} currencies...".format(len(FX_CURRENCIES)))
    counts = refresh_all(backfill=True, fetcher=fetch_yahoo_daily)
    for ccy, n in counts.items():
        dates = _FX_CACHE[ccy]["dates"]
        span = "{} → {}".format(dates[0], dates[-1]) if dates else "EMPTY"
        print("  {:4} {:>5} bars  {}".format(ccy, n, span))
