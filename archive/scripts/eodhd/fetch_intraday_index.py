#!/usr/bin/env python3
"""
Robotnik Intraday Index Proxy
===============================
Uses SOXX (semiconductor ETF) as a proxy to generate intraday
Robotnik Index values at 5-minute and 1-hour granularity.

Method: index_value = last_daily_close * (soxx_now / soxx_daily_close)

Output:  data/prices/intraday_index.json
Usage:   python scripts/fetch_intraday_index.py
"""

import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = ROOT / "data" / "index" / "robotnik_index.json"
OUTPUT = ROOT / "data" / "prices" / "intraday_index.json"

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


def fetch_intraday(symbol, interval="5m", days=7):
    from_ts = int((datetime.utcnow() - timedelta(days=days)).timestamp())
    url = "https://eodhd.com/api/intraday/{}?interval={}&from={}&api_token={}&fmt=json".format(
        symbol, interval, from_ts, KEY)
    req = urllib.request.Request(url, headers={"User-Agent": "Robotnik/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def fetch_eod_recent(symbol, days=10):
    from datetime import date, timedelta as td
    from_date = (date.today() - td(days=days)).isoformat()
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
    print("ROBOTNIK INTRADAY INDEX PROXY")
    print("=" * 60)

    # 1. Get last Robotnik Index daily close
    with open(INDEX_PATH) as f:
        idx = json.load(f)
    series = idx.get("series", [])
    if not series:
        print("ERROR: No index series data")
        sys.exit(1)
    last_pt = series[-1]
    robotnik_close = last_pt["value"]
    robotnik_date = last_pt["date"]
    print("  Robotnik last close: {:.2f} on {}".format(robotnik_close, robotnik_date))

    # 2. Get SOXX daily close for the same date
    print("  Fetching SOXX EOD...")
    soxx_eod = fetch_eod_recent("SOXX.US")
    soxx_daily = {}
    for d in soxx_eod:
        soxx_daily[d["date"]] = d["close"]

    # Find SOXX close matching the Robotnik date (or nearest prior)
    soxx_base = None
    for offset in range(5):
        check = (datetime.strptime(robotnik_date, "%Y-%m-%d") - timedelta(days=offset)).strftime("%Y-%m-%d")
        if check in soxx_daily:
            soxx_base = soxx_daily[check]
            break
    if not soxx_base:
        print("ERROR: No SOXX daily close near {}".format(robotnik_date))
        sys.exit(1)
    print("  SOXX base close: {:.2f}".format(soxx_base))

    # 3. Fetch SOXX 5-minute intraday (last 7 days)
    print("  Fetching SOXX 5-min intraday...")
    soxx_5m = fetch_intraday("SOXX.US", interval="5m", days=7)
    print("  Got {} 5-min bars".format(len(soxx_5m)))

    # 4. Convert to Robotnik Index values
    series_5m = []
    for bar in soxx_5m:
        if not bar.get("close") or bar["close"] <= 0:
            continue
        idx_val = round(robotnik_close * (bar["close"] / soxx_base), 2)
        series_5m.append({
            "datetime": bar["datetime"],
            "value": idx_val,
            "volume": bar.get("volume"),
        })

    # 5. Aggregate to 1-hour bars (take last bar in each hour)
    hourly = {}
    for bar in series_5m:
        dt = bar["datetime"]
        hour_key = dt[:13] + ":00:00"  # "2026-04-09 14:00:00"
        hourly[hour_key] = bar  # Last bar in hour wins

    series_1h = [{"datetime": k, "value": v["value"], "volume": v["volume"]}
                 for k, v in sorted(hourly.items())]

    # 6. Output
    output = {
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "source": "SOXX.US proxy (EODHD 5min intraday)",
        "robotnik_base_close": robotnik_close,
        "robotnik_base_date": robotnik_date,
        "soxx_base_close": soxx_base,
        "series_5m": series_5m,
        "series_1h": series_1h,
    }

    with open(OUTPUT, "w") as f:
        json.dump(output, f, indent=2)

    print("\n  5-min: {} bars".format(len(series_5m)))
    print("  1-hour: {} bars".format(len(series_1h)))
    if series_5m:
        print("  Range: {} to {}".format(series_5m[0]["datetime"], series_5m[-1]["datetime"]))
        print("  Index range: {:.2f} to {:.2f}".format(
            min(b["value"] for b in series_5m), max(b["value"] for b in series_5m)))
    print("\nOutput: {}".format(OUTPUT))

    # Freshness guard: surface a loud warning (and a non-zero exit) when the
    # fetched tail is older than 36 hours. EODHD's intraday feed has
    # occasionally returned Friday-only data on a Monday-evening pull; when
    # that happens the file still writes successfully and the UI silently
    # renders a stale window. A visible warning in CI logs turns that into
    # a detectable failure instead of a user-noticed one.
    if series_5m:
        latest = datetime.strptime(series_5m[-1]["datetime"], "%Y-%m-%d %H:%M:%S")
        age_hours = (datetime.utcnow() - latest).total_seconds() / 3600
        if age_hours > 36:
            print("  WARNING: latest intraday bar is {:.1f}h old — likely EODHD publish lag".format(age_hours))
            print("  WARNING: downstream 1D/1W chart views will anchor to this stale tail")
            sys.exit(2)  # non-zero, but distinct from hard errors (exit 1)
    print("=" * 60)


if __name__ == "__main__":
    main()
