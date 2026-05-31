#!/usr/bin/env python3
"""
Robotnik Commodities Price Fetcher
====================================
Fetches daily prices for frontier-stack commodities via EODHD.
Uses FOREX pairs for precious metals, ETF proxies for others.

Output:  data/prices/commodities.json
Usage:   python scripts/fetch_commodities.py
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
OUTPUT = ROOT / "data" / "prices" / "commodities.json"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

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

# Commodity definitions: name, EODHD symbol, category, unit
COMMODITIES = [
    # Precious metals — FOREX pairs (spot price in USD)
    {"id": "gold", "name": "Gold", "symbol": "XAUUSD.FOREX", "category": "Precious Metals", "unit": "$/oz"},
    {"id": "silver", "name": "Silver", "symbol": "XAGUSD.FOREX", "category": "Precious Metals", "unit": "$/oz"},
    {"id": "platinum", "name": "Platinum", "symbol": "XPTUSD.FOREX", "category": "Precious Metals", "unit": "$/oz"},
    {"id": "palladium", "name": "Palladium", "symbol": "XPDUSD.FOREX", "category": "Precious Metals", "unit": "$/oz"},
    # Industrial metals — ETF proxies
    {"id": "copper", "name": "Copper", "symbol": "CPER.US", "category": "Industrial Metals", "unit": "ETF", "note": "US Copper Index Fund ETF"},
    # Battery materials — ETF proxies
    {"id": "lithium", "name": "Lithium", "symbol": "LIT.US", "category": "Battery Materials", "unit": "ETF", "note": "Global X Lithium & Battery Tech ETF"},
    # Energy
    {"id": "oil_wti", "name": "Crude Oil (WTI)", "symbol": "USO.US", "category": "Energy", "unit": "ETF", "note": "US Oil Fund ETF"},
    {"id": "natural_gas", "name": "Natural Gas", "symbol": "UNG.US", "category": "Energy", "unit": "ETF", "note": "US Natural Gas Fund ETF"},
    # Rare earths — ETF proxy
    {"id": "rare_earths", "name": "Rare Earths", "symbol": "REMX.US", "category": "Critical Minerals", "unit": "ETF", "note": "VanEck Rare Earth/Strategic Metals ETF"},
    # Uranium
    {"id": "uranium", "name": "Uranium", "symbol": "URA.US", "category": "Nuclear", "unit": "ETF", "note": "Global X Uranium ETF"},
]


def fetch_eod(symbol, days=90):
    """Fetch recent daily EOD data from EODHD."""
    from_date = (date.today() - timedelta(days=days)).isoformat()
    url = "https://eodhd.com/api/eod/{}?from={}&period=d&api_token={}&fmt=json".format(
        symbol, from_date, KEY)
    req = urllib.request.Request(url, headers={"User-Agent": "Robotnik/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def main():
    if not KEY:
        print("ERROR: EODHD_API_KEY not set")
        sys.exit(1)

    print("=" * 60)
    print("ROBOTNIK COMMODITIES PRICE FETCHER")
    print("=" * 60)

    results = []
    for c in COMMODITIES:
        print("[{}] {} ...".format(c["id"], c["symbol"]), end=" ")
        try:
            data = fetch_eod(c["symbol"])
            if data and isinstance(data, list) and len(data) > 0:
                latest = data[-1]
                # Calculate 30D change
                chg_30d = None
                if len(data) >= 22:
                    old = data[-22]["close"]
                    if old and old > 0:
                        chg_30d = round((latest["close"] - old) / old * 100, 2)

                results.append({
                    "id": c["id"],
                    "name": c["name"],
                    "symbol": c["symbol"],
                    "category": c["category"],
                    "unit": c["unit"],
                    "note": c.get("note", ""),
                    "price": latest["close"],
                    "date": latest["date"],
                    "change_30d_pct": chg_30d,
                    "days": len(data),
                    "series": [{"date": d["date"], "close": d["close"]} for d in data],
                })
                print("{} ({} days, 30D: {}%)".format(
                    latest["close"], len(data),
                    "{:+.2f}".format(chg_30d) if chg_30d else "N/A"))
            else:
                print("NO DATA")
                results.append({
                    "id": c["id"], "name": c["name"], "symbol": c["symbol"],
                    "category": c["category"], "unit": c["unit"],
                    "price": None, "date": None, "change_30d_pct": None,
                    "days": 0, "series": [],
                })
        except Exception as e:
            print("ERROR: {}".format(e))
            results.append({
                "id": c["id"], "name": c["name"], "symbol": c["symbol"],
                "category": c["category"], "unit": c["unit"],
                "price": None, "date": None, "change_30d_pct": None,
                "days": 0, "series": [], "error": str(e),
            })
        time.sleep(0.2)

    output = {
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "source": "EODHD (FOREX + ETF proxies)",
        "count": len([r for r in results if r.get("price")]),
        "commodities": results,
    }

    with open(OUTPUT, "w") as f:
        json.dump(output, f, indent=2)

    print("\n" + "=" * 60)
    print("DONE: {}/{} commodities with data".format(
        output["count"], len(results)))
    print("Output: {}".format(OUTPUT))
    print("=" * 60)


if __name__ == "__main__":
    main()
