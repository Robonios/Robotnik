#!/usr/bin/env python3
"""
Robotnik Price History Fetcher
==============================
Fetches extended daily price history for all tracked entities.
- Equities: 5 years via EODHD (daily OHLCV)
- Tokens: 365 days via CoinGecko /market_chart (daily close)

Outputs:
    data/prices/history/  — one JSON file per entity (TICKER.json)
    data/prices/history_index.json — manifest listing all available tickers

Usage:
    python scripts/fetch_price_history.py
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, date, timedelta, timezone
from pathlib import Path

# ── paths ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
HISTORY_DIR = ROOT / "data" / "prices" / "history"
HISTORY_DIR.mkdir(parents=True, exist_ok=True)
INDEX_FILE = ROOT / "data" / "prices" / "history_index.json"

# ── load env & API keys ─────────────────────────────────────────────────
def load_env():
    env_path = ROOT / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env()
EODHD_KEY = os.environ.get("EODHD_API_KEY", "")
COINGECKO_KEY = os.environ.get("COINGECKO_API_KEY", "")

# ── import universe from fetch_prices.py ─────────────────────────────────
sys.path.insert(0, str(ROOT / "scripts"))
from fetch_prices import EQUITIES, TOKENS, ticker_to_eodhd, guess_currency, load_source_overrides
from quarantine_utils import is_sentinel

EQUITY_DAYS_BACK = 1825  # ~5 years for equities
TOKEN_DAYS_BACK  = 365   # 1 year for tokens (CoinGecko demo plan max)

# USD conversion rates for native-currency history. Must match fetch_prices.py
# so that history and live pipelines agree. If these drift, the splice point
# between history and today's injected live price will jump.
FX_TO_USD = {
    "USD": 1.0,
    "KRW": 1 / 1450.0,
    # Other currencies kept at 1.0 (no conversion) until explicitly needed —
    # the index is not distorted by non-USD units while prices stay within
    # plausible per-share ranges, and the live fetcher only converts KRW
    # today. Extend this map in lockstep with fetch_prices.py.
}


def fetch_url(url, timeout=20):
    """Fetch URL and return parsed JSON, or None on error."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Robotnik/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return None


def _fetch_from_yahoo_override(ticker, override, days_back):
    """Return a USD-denominated OHLCV series for an override-routed ticker.

    Used for tickers EODHD cannot serve faithfully — e.g. Hanwha Aerospace
    (012450 KS), whose real KRW price exceeds EODHD's ₩999,999.9999 field
    cap and returns the cap value instead of the true close.
    """
    from fetch_yahoo import fetch_yahoo_daily, YahooFetchError
    sym = override.get("yahoo_symbol")
    if not sym:
        return None
    # Map days_back to a Yahoo range token.
    rng = "5y" if days_back >= 365 else "1y" if days_back >= 90 else "3mo"
    try:
        y = fetch_yahoo_daily(sym, output_size=rng)
    except YahooFetchError:
        return None
    ccy = (y.get("currency") or "USD").upper()
    rate = FX_TO_USD.get(ccy, 1.0)
    out = []
    for d, bar in sorted(y["series"].items()):
        close = bar.get("close")
        if close is None:
            continue
        bad, _ = is_sentinel(close, ccy)
        if bad:
            continue
        out.append({
            "date": d,
            "open": round(bar["open"] * rate, 4) if bar.get("open") is not None else None,
            "high": round(bar["high"] * rate, 4) if bar.get("high") is not None else None,
            "low": round(bar["low"] * rate, 4) if bar.get("low") is not None else None,
            "close": round(close * rate, 4),
            "volume": bar.get("volume"),
        })
    return out


def fetch_equity_history(ticker, country, days_back=EQUITY_DAYS_BACK, override=None):
    """Fetch daily OHLCV for one equity. Output is always denominated in USD.

    days_back defaults to 5 years (full backfill). Pass a smaller window
    (e.g. 45) for an incremental refresh that only pulls the recent tail.
    If a per-ticker override is supplied (see data_source_overrides.json),
    the override provider is used instead of EODHD — this keeps history
    in lockstep with the live fetcher for tickers EODHD cannot serve.
    """
    if override:
        provider = override.get("provider")
        if provider == "yahoo":
            return _fetch_from_yahoo_override(ticker, override, days_back)
        # Unknown override: fall through to EODHD so we get SOMETHING rather
        # than silently dropping the ticker. The live pipeline will still
        # refuse to fall back, so any mismatch will show up in quarantine.

    eodhd_ticker = ticker_to_eodhd(ticker, country)
    from_date = (date.today() - timedelta(days=days_back)).isoformat()
    to_date = date.today().isoformat()

    url = (
        f"https://eodhd.com/api/eod/{eodhd_ticker}"
        f"?api_token={EODHD_KEY}&fmt=json&order=a"
        f"&from={from_date}&to={to_date}"
    )
    data = fetch_url(url)
    if not data or not isinstance(data, list):
        return None

    # Convert to standard format: [{date, open, high, low, close, volume}, ...]
    # Use adjusted_close for split-adjusted prices (critical for stocks like
    # NVDA 10:1 split Jun 2024, AMZN 20:1 split Jun 2022, etc.) then convert
    # to USD using the same per-currency rates as fetch_prices.py.
    currency = guess_currency(eodhd_ticker)
    fx_rate = FX_TO_USD.get(currency, 1.0)
    series = []
    for d in data:
        try:
            adj = d.get("adjusted_close")
            raw = d.get("close")
            close_native = adj if adj is not None else raw
            if close_native is None:
                continue
            # Reject sentinels in the native currency BEFORE conversion, so
            # EODHD's ₩999,999.9999 cap doesn't get silently written as a
            # plausible-looking $689 USD close.
            is_bad, _ = is_sentinel(close_native, currency)
            if is_bad:
                continue
            # Calculate adjustment factor to adjust OHLC consistently
            factor = (adj / raw) if (adj and raw and raw != 0) else 1.0
            series.append({
                "date": d["date"],
                "open":   round(d.get("open", 0) * factor * fx_rate, 4) if d.get("open") else None,
                "high":   round(d.get("high", 0) * factor * fx_rate, 4) if d.get("high") else None,
                "low":    round(d.get("low", 0) * factor * fx_rate, 4) if d.get("low") else None,
                "close":  round(close_native * fx_rate, 4),
                "volume": d.get("volume"),
            })
        except (KeyError, TypeError):
            continue
    return series


def fetch_token_history(coingecko_id, days_back=TOKEN_DAYS_BACK):
    """Fetch daily prices for one token from CoinGecko (default 365 days)."""
    url = (
        f"https://api.coingecko.com/api/v3/coins/{coingecko_id}"
        f"/market_chart?vs_currency=usd&days={days_back}&interval=daily"
    )
    if COINGECKO_KEY:
        url += f"&x_cg_demo_api_key={COINGECKO_KEY}"

    data = fetch_url(url)
    if not data or "prices" not in data:
        return None

    series = []
    for ts, price in data["prices"]:
        d = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
        series.append({
            "date": d,
            "close": round(price, 8),
        })

    # Deduplicate by date (keep last per day)
    seen = {}
    for s in series:
        seen[s["date"]] = s
    return sorted(seen.values(), key=lambda x: x["date"])


def save_history(ticker, name, sector, series, source, merge=False):
    """Save one entity's price history.

    If merge=True and a history file already exists, combine the incoming
    `series` with the on-disk series (incoming wins on date conflicts — so
    a refresh can correct a stale or preliminary close). Used by --refresh
    to apply an incremental tail to a preserved 5-year backfill.
    """
    safe_ticker = ticker.replace("/", "_").replace(" ", "_")
    path = HISTORY_DIR / f"{safe_ticker}.json"

    if merge and path.exists():
        try:
            with open(path) as f:
                existing = json.load(f)
            by_date = {p["date"]: p for p in existing.get("series", []) if p.get("date")}
            for p in series:
                if p.get("date"):
                    by_date[p["date"]] = p
            series = sorted(by_date.values(), key=lambda p: p["date"])
        except Exception:
            # If merge fails for any reason, fall through to a clean overwrite.
            pass

    data = {
        "ticker": ticker,
        "name": name,
        "sector": sector,
        "source": source,
        "days": len(series),
        "from": series[0]["date"] if series else None,
        "to": series[-1]["date"] if series else None,
        "series": series,
    }
    with open(path, "w") as f:
        json.dump(data, f)
    return safe_ticker


def load_coingecko_mapping():
    """Load explicit CoinGecko ID mapping from data/mappings/coingecko_ids.json if available."""
    mapping_path = ROOT / "data" / "mappings" / "coingecko_ids.json"
    if mapping_path.exists():
        with open(mapping_path) as f:
            return json.load(f)
    return None


def get_coingecko_id(ticker, default_id):
    """Get the correct CoinGecko ID, preferring the mapping file over inline defaults."""
    cg_mapping = load_coingecko_mapping()
    if cg_mapping and ticker in cg_mapping:
        mapped = cg_mapping[ticker]
        if mapped != "not_found":
            return mapped
        return None  # explicitly marked as not found
    return default_id


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Robotnik Price History Fetcher")
    parser.add_argument("--sector", type=str, default=None,
                        help="Only fetch tickers in this sector (e.g., Materials, Token, Semiconductor)")
    parser.add_argument("--backfill", action="store_true",
                        help="Only fetch tickers that don't already have history files")
    parser.add_argument("--refresh", action="store_true",
                        help="Incremental refresh: fetch the last ~45 days for every "
                             "existing ticker and merge into their history files. "
                             "Use this for the daily pipeline — far cheaper than a "
                             "full 5-year refetch and keeps history current.")
    parser.add_argument("--refresh-days", type=int, default=45,
                        help="How many days of recent history to pull per ticker in "
                             "--refresh mode (default: 45 — covers ~30 trading days "
                             "plus buffer for holidays and weekends).")
    args = parser.parse_args()

    sector_filter = args.sector
    backfill_only = args.backfill
    refresh_mode = args.refresh
    refresh_days = args.refresh_days

    if backfill_only and refresh_mode:
        parser.error("--backfill and --refresh are mutually exclusive")

    # In refresh mode, fetch short windows and merge with existing files.
    equity_days = refresh_days if refresh_mode else EQUITY_DAYS_BACK
    # CoinGecko accepts values up to 365 on the demo plan; keep token refresh
    # proportionate to the equity one.
    token_days = refresh_days if refresh_mode else TOKEN_DAYS_BACK

    print("Robotnik Price History Fetcher")
    if sector_filter:
        print(f"  Sector filter: {sector_filter}")
    if backfill_only:
        print(f"  Backfill mode: only missing tickers")
    if refresh_mode:
        print(f"  Refresh mode: last {refresh_days} days, merging with existing")
    print("=" * 40)

    index = {}
    errors = []

    def needs_fetch(ticker):
        """Decide whether to fetch this ticker given the current mode.

        - backfill:  only fetch if no history file exists yet
        - refresh:   only fetch if a history file DOES exist (incremental tail)
        - default:   always fetch (full 5-year pull — used for full rebuilds)
        """
        safe = ticker.replace("/", "_").replace(" ", "_")
        exists = (HISTORY_DIR / f"{safe}.json").exists()
        if backfill_only:
            return not exists
        if refresh_mode:
            return exists
        return True

    # ── equities (EODHD or override) ─────────────────────────────────
    overrides = load_source_overrides() or {}
    equities = EQUITIES
    if sector_filter:
        equities = [(t, n, s, c) for t, n, s, c in EQUITIES if s == sector_filter]

    if equities:
        to_fetch = [(t, n, s, c) for t, n, s, c in equities if needs_fetch(t)]
        print(f"\nEquities: {len(to_fetch)} to fetch (of {len(equities)} in scope)")
        if overrides:
            print(f"  Source overrides: {', '.join(overrides.keys())}")
        for i, (ticker, name, sector, country) in enumerate(to_fetch):
            ov = overrides.get(ticker)
            series = fetch_equity_history(ticker, country, days_back=equity_days, override=ov)
            if series and len(series) > 0:
                safe = save_history(ticker, name, sector, series, "EODHD",
                                    merge=refresh_mode)
                index[ticker] = {
                    "name": name, "sector": sector, "file": f"{safe}.json",
                    "days": len(series),
                }
                status = f"OK ({len(series)} days)"
            else:
                errors.append(ticker)
                status = "FAIL"

            if (i + 1) % 25 == 0 or status == "FAIL" or len(to_fetch) <= 50:
                print(f"  [{i+1}/{len(to_fetch)}] {ticker:12s} {status}")

            time.sleep(0.15)

        print(f"  Equities: {len(index)} OK, {len(errors)} errors")

    # ── tokens (CoinGecko) ───────────────────────────────────────────
    if sector_filter is None or sector_filter == "Token":
        tokens_to_fetch = {}
        for ticker, (cg_id_default, name) in TOKENS.items():
            if not needs_fetch(ticker):
                continue
            cg_id = get_coingecko_id(ticker, cg_id_default)
            if cg_id:
                tokens_to_fetch[ticker] = (cg_id, name)

        token_count = 0
        token_errors = 0
        print(f"\nTokens: {len(tokens_to_fetch)} to fetch")
        for i, (ticker, (cg_id, name)) in enumerate(tokens_to_fetch.items()):
            series = fetch_token_history(cg_id, days_back=token_days)
            if series and len(series) > 0:
                safe = save_history(ticker, name, "Token", series, "CoinGecko",
                                    merge=refresh_mode)
                index[ticker] = {
                    "name": name, "sector": "Token", "file": f"{safe}.json",
                    "days": len(series),
                }
                token_count += 1
                status = f"OK ({len(series)} days)"
            else:
                errors.append(ticker)
                token_errors += 1
                status = "FAIL"

            if (i + 1) % 10 == 0 or status == "FAIL" or len(tokens_to_fetch) <= 50:
                print(f"  [{i+1}/{len(tokens_to_fetch)}] {ticker:12s} {status}")

            time.sleep(2.5)

        print(f"  Tokens: {token_count} OK, {token_errors} errors")

    # ── save/update index ───────────────────────────────────────────
    # In backfill/sector mode, merge with existing index
    existing_index = {}
    if INDEX_FILE.exists():
        with open(INDEX_FILE) as f:
            existing_data = json.load(f)
            existing_index = existing_data.get("entities", {})

    existing_index.update(index)

    index_data = {
        "fetched_at": datetime.now(timezone.utc).isoformat() + "Z",
        "count": len(existing_index),
        "equity_days_back": EQUITY_DAYS_BACK,
        "token_days_back": TOKEN_DAYS_BACK,
        "entities": existing_index,
    }
    with open(INDEX_FILE, "w") as f:
        json.dump(index_data, f, indent=2)
    print(f"\n  -> history_index.json ({len(existing_index)} entities)")

    if errors:
        print(f"\n  Errors ({len(errors)}): {', '.join(errors[:15])}")
        if len(errors) > 15:
            print(f"    ... and {len(errors) - 15} more")

    print("\nDone.")


if __name__ == "__main__":
    main()
