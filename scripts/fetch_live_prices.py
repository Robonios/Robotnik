#!/usr/bin/env python3
"""
Robotnik Live Price Fetcher (15-min delayed)
==============================================
Fetches real-time (15-min delayed) prices for top entities from EODHD.
Also fetches intraday hourly data for the past 5 days for chart rendering.

Endpoints:
  Real-time: https://eodhd.com/api/real-time/{TICKER}?api_token={KEY}&fmt=json
  Intraday:  https://eodhd.com/api/intraday/{TICKER}?interval=1h&api_token={KEY}&fmt=json

Output:
  data/prices/live.json       — latest snapshot for top entities
  data/prices/intraday.json   — hourly OHLCV for past 5 days (top 20)

Usage:
  python scripts/fetch_live_prices.py
"""

import json
import os
import sys
import time
import urllib.request
from datetime import datetime, date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIVE_OUTPUT = ROOT / "data" / "prices" / "live.json"
INTRADAY_OUTPUT = ROOT / "data" / "prices" / "intraday.json"

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
KEY = os.environ.get("EODHD_API_KEY", "")

# Top 20 entities by index weight — drive the most chart movement
TOP_20 = [
    ("NVDA", "NVDA.US"), ("TSM", "TSM.US"), ("AVGO", "AVGO.US"),
    ("ASML", "ASML.US"), ("MU", "MU.US"), ("AMD", "AMD.US"),
    ("LRCX", "LRCX.US"), ("AMAT", "AMAT.US"), ("INTC", "INTC.US"),
    ("KLAC", "KLAC.US"), ("TXN", "TXN.US"), ("ADI", "ADI.US"),
    ("QCOM", "QCOM.US"), ("MRVL", "MRVL.US"), ("CDNS", "CDNS.US"),
    ("SNPS", "SNPS.US"), ("NXPI", "NXPI.US"), ("ON", "ON.US"),
    ("ISRG", "ISRG.US"), ("LIN", "LIN.US"),
]


def fetch_live(eodhd_sym):
    url = "https://eodhd.com/api/real-time/{}?api_token={}&fmt=json".format(eodhd_sym, KEY)
    req = urllib.request.Request(url, headers={"User-Agent": "Robotnik/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def fetch_intraday(eodhd_sym):
    # Past 5 days of hourly data
    from_ts = int((datetime.utcnow() - timedelta(days=5)).timestamp())
    url = "https://eodhd.com/api/intraday/{}?interval=1h&from={}&api_token={}&fmt=json".format(
        eodhd_sym, from_ts, KEY)
    req = urllib.request.Request(url, headers={"User-Agent": "Robotnik/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def main():
    if not KEY:
        print("ERROR: EODHD_API_KEY not set")
        sys.exit(1)

    print("=" * 60)
    print("ROBOTNIK LIVE PRICE FETCHER (15-min delayed)")
    print("=" * 60)

    ts = datetime.utcnow().isoformat() + "Z"

    # ── Live snapshot ──
    print("\n--- Live prices (top 20) ---")
    live_data = {}
    for ticker, sym in TOP_20:
        try:
            d = fetch_live(sym)
            live_data[ticker] = {
                "ticker": ticker,
                "price": d.get("close"),
                "open": d.get("open"),
                "high": d.get("high"),
                "low": d.get("low"),
                "volume": d.get("volume"),
                "prev_close": d.get("previousClose"),
                "change": d.get("change"),
                "change_pct": d.get("change_p"),
                "timestamp": d.get("timestamp"),
            }
            print("  {:6s} ${:.2f} ({:+.2f}%)".format(
                ticker, d.get("close", 0), d.get("change_p", 0)))
        except Exception as e:
            print("  {:6s} ERROR: {}".format(ticker, e))
        time.sleep(0.1)

    with open(LIVE_OUTPUT, "w") as f:
        json.dump({"fetched_at": ts, "source": "EODHD Real-Time (15-min delayed)",
                    "count": len(live_data), "prices": live_data}, f, indent=2)

    # ── Intraday hourly ──
    print("\n--- Intraday hourly (top 20, 5 days) ---")
    intraday_data = {}
    for ticker, sym in TOP_20:
        try:
            data = fetch_intraday(sym)
            if data and isinstance(data, list):
                series = [{"datetime": d["datetime"], "close": d["close"],
                           "volume": d.get("volume")} for d in data if d.get("close")]
                intraday_data[ticker] = {
                    "ticker": ticker,
                    "points": len(series),
                    "series": series,
                }
                print("  {:6s} {} hourly points".format(ticker, len(series)))
            else:
                print("  {:6s} NO DATA".format(ticker))
        except Exception as e:
            print("  {:6s} ERROR: {}".format(ticker, e))
        time.sleep(0.1)

    with open(INTRADAY_OUTPUT, "w") as f:
        json.dump({"fetched_at": ts, "source": "EODHD Intraday (1h)",
                    "count": len(intraday_data), "tickers": intraday_data}, f, indent=2)

    print("\n" + "=" * 60)
    print("DONE: {} live prices, {} intraday series".format(
        len(live_data), len(intraday_data)))
    print("Output: {}, {}".format(LIVE_OUTPUT, INTRADAY_OUTPUT))
    print("=" * 60)


if __name__ == "__main__":
    main()
