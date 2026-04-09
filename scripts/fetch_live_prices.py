#!/usr/bin/env python3
"""
Robotnik Live Price Fetcher (15-min delayed)
==============================================
Fetches real-time (15-min delayed) prices from EODHD for all entities
and benchmark ETFs.

Endpoints:
  Real-time: https://eodhd.com/api/real-time/{TICKER}?api_token={KEY}&fmt=json
  Intraday:  https://eodhd.com/api/intraday/{TICKER}?interval=1h&api_token={KEY}&fmt=json

Output:
  data/prices/live.json       — latest snapshot for all entities + benchmarks
  data/prices/intraday.json   — hourly OHLCV for top 20 (chart rendering)

Usage:
  python scripts/fetch_live_prices.py [--top-only]

  --top-only: Only fetch top 20 entities (for frequent intra-day updates)
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIVE_OUTPUT = ROOT / "data" / "prices" / "live.json"
INTRADAY_OUTPUT = ROOT / "data" / "prices" / "intraday.json"
REGISTRY_PATH = ROOT / "data" / "registries" / "entity_registry.json"
MAPPING_PATH = ROOT / "data" / "mappings" / "eodhd_tickers.json"

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

# Benchmarks
BENCHMARKS = [("SPY", "SPY.US"), ("QQQ", "QQQ.US"), ("SOXX", "SOXX.US"), ("ROBO", "ROBO.US")]


def fetch_live(eodhd_sym):
    url = "https://eodhd.com/api/real-time/{}?api_token={}&fmt=json".format(eodhd_sym, KEY)
    req = urllib.request.Request(url, headers={"User-Agent": "Robotnik/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def fetch_intraday(eodhd_sym, hours=120):
    from_ts = int((datetime.utcnow() - timedelta(hours=hours)).timestamp())
    url = "https://eodhd.com/api/intraday/{}?interval=1h&from={}&api_token={}&fmt=json".format(
        eodhd_sym, from_ts, KEY)
    req = urllib.request.Request(url, headers={"User-Agent": "Robotnik/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def build_entity_list():
    """Build list of (robotnik_ticker, eodhd_symbol) for all active non-token entities."""
    # Load registry
    with open(REGISTRY_PATH) as f:
        reg = json.load(f)

    # Load explicit EODHD mapping
    eodhd_map = {}
    if MAPPING_PATH.exists():
        with open(MAPPING_PATH) as f:
            eodhd_map = json.load(f)

    # Import universe from fetch_prices
    sys.path.insert(0, str(ROOT / "scripts"))
    from fetch_prices import EQUITIES, ticker_to_eodhd

    entities = []
    seen = set()
    for ticker, company, sector, country in EQUITIES:
        if ticker in seen:
            continue
        seen.add(ticker)

        # Check registry
        entity = reg.get(ticker, {})
        if not isinstance(entity, dict):
            continue
        if entity.get("status") == "excluded":
            continue
        if entity.get("sector") == "Token":
            continue

        # Get EODHD symbol
        if ticker in eodhd_map:
            sym = eodhd_map[ticker]
        else:
            sym = ticker_to_eodhd(ticker, country)

        if sym == "UNAVAILABLE":
            continue

        entities.append((ticker, sym))

    return entities


def main():
    if not KEY:
        print("ERROR: EODHD_API_KEY not set")
        sys.exit(1)

    top_only = "--top-only" in sys.argv

    print("=" * 60)
    print("ROBOTNIK LIVE PRICE FETCHER")
    print("  Mode: {}".format("Top 20 only" if top_only else "Full universe"))
    print("=" * 60)

    ts = datetime.utcnow().isoformat() + "Z"
    entities = build_entity_list()

    if top_only:
        # Only fetch top 20 by known market cap order
        top20_tickers = {"NVDA","TSM","AVGO","ASML","MU","AMD","LRCX","AMAT","INTC","KLAC",
                         "TXN","ADI","QCOM","MRVL","CDNS","SNPS","NXPI","ON","ISRG","LIN"}
        entities = [(t, s) for t, s in entities if t in top20_tickers]

    print("  Entities: {}".format(len(entities)))

    # ── Live snapshot ──
    live_data = {}
    success = 0
    for ticker, sym in entities:
        try:
            d = fetch_live(sym)
            if d and d.get("close"):
                live_data[ticker] = {
                    "ticker": ticker,
                    "eodhd_symbol": sym,
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
                success += 1
        except (urllib.error.HTTPError, urllib.error.URLError):
            pass
        except Exception:
            pass
        time.sleep(0.05)  # 50ms = 20/sec, well within 1000/min

    # Add benchmarks
    for bm_ticker, bm_sym in BENCHMARKS:
        try:
            d = fetch_live(bm_sym)
            if d and d.get("close"):
                live_data["BM_" + bm_ticker] = {
                    "ticker": bm_ticker,
                    "eodhd_symbol": bm_sym,
                    "price": d.get("close"),
                    "change_pct": d.get("change_p"),
                    "timestamp": d.get("timestamp"),
                    "is_benchmark": True,
                }
        except Exception:
            pass
        time.sleep(0.05)

    print("  Live prices: {}/{} entities + {} benchmarks".format(
        success, len(entities), sum(1 for k in live_data if k.startswith("BM_"))))

    with open(LIVE_OUTPUT, "w") as f:
        json.dump({
            "fetched_at": ts,
            "source": "EODHD Real-Time (15-min delayed)",
            "count": len(live_data),
            "is_live": True,
            "prices": live_data,
        }, f, indent=2)

    # ── Intraday hourly (top 20 only — for chart) ──
    if not top_only:
        top20 = [(t, s) for t, s in entities[:20]]
    else:
        top20 = entities[:20]

    intraday_data = {}
    for ticker, sym in top20:
        try:
            data = fetch_intraday(sym)
            if data and isinstance(data, list):
                series = [{"datetime": d["datetime"], "close": d["close"],
                           "volume": d.get("volume")} for d in data if d.get("close")]
                intraday_data[ticker] = {"ticker": ticker, "points": len(series), "series": series}
        except Exception:
            pass
        time.sleep(0.05)

    with open(INTRADAY_OUTPUT, "w") as f:
        json.dump({
            "fetched_at": ts,
            "source": "EODHD Intraday (1h)",
            "count": len(intraday_data),
            "tickers": intraday_data,
        }, f, indent=2)

    print("  Intraday: {} tickers".format(len(intraday_data)))
    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)


if __name__ == "__main__":
    main()
