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
from fetch_prices import EQUITIES, TOKENS, ticker_to_eodhd

EQUITY_DAYS_BACK = 1825  # ~5 years for equities
TOKEN_DAYS_BACK  = 365   # 1 year for tokens (CoinGecko demo plan max)


def fetch_url(url, timeout=20):
    """Fetch URL and return parsed JSON, or None on error."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Robotnik/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return None


def fetch_equity_history(ticker, country):
    """Fetch daily OHLCV for one equity from EODHD (5 years)."""
    eodhd_ticker = ticker_to_eodhd(ticker, country)
    from_date = (date.today() - timedelta(days=EQUITY_DAYS_BACK)).isoformat()
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
    # NVDA 10:1 split Jun 2024, AMZN 20:1 split Jun 2022, etc.)
    series = []
    for d in data:
        try:
            adj = d.get("adjusted_close")
            raw = d.get("close")
            close_price = adj if adj is not None else raw
            # Calculate adjustment factor to adjust OHLC consistently
            factor = (adj / raw) if (adj and raw and raw != 0) else 1.0
            series.append({
                "date": d["date"],
                "open": round(d.get("open", 0) * factor, 4) if d.get("open") else None,
                "high": round(d.get("high", 0) * factor, 4) if d.get("high") else None,
                "low": round(d.get("low", 0) * factor, 4) if d.get("low") else None,
                "close": close_price,
                "volume": d.get("volume"),
            })
        except (KeyError, TypeError):
            continue
    return series


def fetch_token_history(coingecko_id):
    """Fetch daily prices for one token from CoinGecko (365 days)."""
    url = (
        f"https://api.coingecko.com/api/v3/coins/{coingecko_id}"
        f"/market_chart?vs_currency=usd&days={TOKEN_DAYS_BACK}&interval=daily"
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


def save_history(ticker, name, sector, series, source):
    """Save one entity's price history."""
    safe_ticker = ticker.replace("/", "_").replace(" ", "_")
    path = HISTORY_DIR / f"{safe_ticker}.json"
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


def main():
    print("Robotnik Price History Fetcher")
    print("=" * 40)

    index = {}
    errors = []

    # ── equities (EODHD) ─────────────────────────────────────────────
    print(f"\nFetching {len(EQUITIES)} equities from EODHD...")
    for i, (ticker, name, sector, country) in enumerate(EQUITIES):
        series = fetch_equity_history(ticker, country)
        if series and len(series) > 0:
            safe = save_history(ticker, name, sector, series, "EODHD")
            index[ticker] = {
                "name": name, "sector": sector, "file": f"{safe}.json",
                "days": len(series),
            }
            status = f"OK ({len(series)} days)"
        else:
            errors.append(ticker)
            status = "FAIL"

        if (i + 1) % 25 == 0 or status == "FAIL":
            print(f"  [{i+1}/{len(EQUITIES)}] {ticker:12s} {status}")

        # Rate limit: EODHD allows ~1000/day, be gentle
        time.sleep(0.15)

    print(f"  Equities: {len(index)} OK, {len(errors)} errors")

    # ── tokens (CoinGecko) ───────────────────────────────────────────
    token_count = 0
    token_errors = 0
    print(f"\nFetching {len(TOKENS)} tokens from CoinGecko...")
    for i, (ticker, (cg_id, name)) in enumerate(TOKENS.items()):
        series = fetch_token_history(cg_id)
        if series and len(series) > 0:
            safe = save_history(ticker, name, "Token", series, "CoinGecko")
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

        if (i + 1) % 10 == 0 or status == "FAIL":
            print(f"  [{i+1}/{len(TOKENS)}] {ticker:12s} {status}")

        # CoinGecko rate limit: 10-30 req/min on demo plan
        time.sleep(2.5)

    print(f"  Tokens: {token_count} OK, {token_errors} errors")

    # ── save index ───────────────────────────────────────────────────
    index_data = {
        "fetched_at": datetime.now(timezone.utc).isoformat() + "Z",
        "count": len(index),
        "equity_days_back": EQUITY_DAYS_BACK,
        "token_days_back": TOKEN_DAYS_BACK,
        "entities": index,
    }
    with open(INDEX_FILE, "w") as f:
        json.dump(index_data, f, indent=2)
    print(f"\n  -> history_index.json ({len(index)} entities)")

    if errors:
        print(f"\n  Errors ({len(errors)}): {', '.join(errors[:15])}")
        if len(errors) > 15:
            print(f"    ... and {len(errors) - 15} more")

    print("\nDone.")


if __name__ == "__main__":
    main()
