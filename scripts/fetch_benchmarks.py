#!/usr/bin/env python3
"""
Robotnik Benchmark Price Fetcher
=================================
Fetches daily price history for benchmark indices/ETFs:
  SPY  (S&P 500 proxy)
  QQQ  (NASDAQ Composite proxy)
  SOXX (PHLX Semiconductor Index proxy)
  ROBO (ROBO Global Robotics & Automation ETF)

Sources: EODHD (primary), Alpha Vantage (fallback)

Outputs:
    data/prices/benchmarks.json  — combined daily series for all benchmarks

Usage:
    python scripts/fetch_benchmarks.py
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, date, timedelta
from pathlib import Path

# ── paths ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "prices"
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_PATH = DATA_DIR / "benchmarks.json"

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
AV_KEY = os.environ.get("ALPHAVANTAGE_API_KEY", "")

# ── benchmarks ───────────────────────────────────────────────────────────
BENCHMARKS = {
    "SPY": {
        "name": "S&P 500 (SPY ETF)",
        "eodhd_symbol": "SPY.US",
        "color": "#7B8794",
    },
    "QQQ": {
        "name": "NASDAQ Composite (QQQ ETF)",
        "eodhd_symbol": "QQQ.US",
        "color": "#5B9BD5",
    },
    "SOXX": {
        "name": "PHLX Semiconductor Index (SOXX ETF)",
        "eodhd_symbol": "SOXX.US",
        "color": "#E97451",
    },
    "ROBO": {
        "name": "ROBO Global Robotics & Automation ETF",
        "eodhd_symbol": "ROBO.US",
        "color": "#70AD47",
    },
}

# ── EODHD fetcher ────────────────────────────────────────────────────────
def fetch_eodhd_history(symbol, years=5):
    """Fetch daily OHLCV from EODHD for the last N years."""
    from_date = (date.today() - timedelta(days=365 * years)).isoformat()
    url = (
        "https://eodhd.com/api/eod/{symbol}"
        "?api_token={key}&fmt=json&order=a&from={from_date}"
    ).format(symbol=symbol, key=EODHD_KEY, from_date=from_date)

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Robotnik/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        if not data or not isinstance(data, list):
            return None
        # Convert to series format
        series = []
        for day in data:
            series.append({
                "date": day["date"],
                "open": day.get("open"),
                "high": day.get("high"),
                "low": day.get("low"),
                "close": day["close"],
                "volume": day.get("volume"),
            })
        return series
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as e:
        print("  EODHD error for {}: {}".format(symbol, e))
        return None


# ── Alpha Vantage fallback ───────────────────────────────────────────────
def fetch_av_history(symbol):
    """Fetch daily prices from Alpha Vantage (compact = last 100 trading days)."""
    if not AV_KEY:
        return None
    url = (
        "https://www.alphavantage.co/query?"
        "function=TIME_SERIES_DAILY&symbol={symbol}"
        "&outputsize=compact&apikey={key}"
    ).format(symbol=symbol, key=AV_KEY)

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Robotnik/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())

        ts = data.get("Time Series (Daily)", {})
        if not ts:
            note = data.get("Note") or data.get("Information") or data.get("Error Message")
            print("  AV warning for {}: {}".format(symbol, note))
            return None

        series = []
        for date_str in sorted(ts.keys()):
            vals = ts[date_str]
            series.append({
                "date": date_str,
                "close": float(vals["4. close"]),
            })
        return series
    except (urllib.error.URLError, json.JSONDecodeError) as e:
        print("  AV error for {}: {}".format(symbol, e))
        return None


# ── main ─────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("ROBOTNIK BENCHMARK PRICE FETCHER")
    print("=" * 60)

    ts = datetime.utcnow().isoformat() + "Z"
    output = {
        "fetched_at": ts,
        "benchmarks": {},
    }

    for ticker, info in BENCHMARKS.items():
        print("\nFetching {} ({})...".format(ticker, info["name"]))

        series = None

        # Try EODHD first
        if EODHD_KEY:
            series = fetch_eodhd_history(info["eodhd_symbol"])
            if series:
                print("  EODHD: {} data points ({} to {})".format(
                    len(series), series[0]["date"], series[-1]["date"]
                ))

        # Fallback to Alpha Vantage
        if not series and AV_KEY:
            print("  Trying Alpha Vantage fallback...")
            series = fetch_av_history(ticker)
            if series:
                print("  AV: {} data points ({} to {})".format(
                    len(series), series[0]["date"], series[-1]["date"]
                ))
            time.sleep(15)  # AV rate limit

        if series:
            output["benchmarks"][ticker] = {
                "ticker": ticker,
                "name": info["name"],
                "color": info["color"],
                "days": len(series),
                "from": series[0]["date"],
                "to": series[-1]["date"],
                "series": series,
            }
        else:
            print("  WARNING: No data for {}".format(ticker))
            output["benchmarks"][ticker] = {
                "ticker": ticker,
                "name": info["name"],
                "color": info["color"],
                "days": 0,
                "from": None,
                "to": None,
                "series": [],
            }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    total = sum(b["days"] for b in output["benchmarks"].values())
    print("\n" + "=" * 60)
    print("DONE: {} benchmarks, {} total data points".format(
        len(output["benchmarks"]), total
    ))
    print("Output: {}".format(OUTPUT_PATH))
    print("=" * 60)


if __name__ == "__main__":
    main()
