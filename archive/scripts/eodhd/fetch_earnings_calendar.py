#!/usr/bin/env python3
"""
Robotnik Earnings Calendar Fetcher
====================================
Fetches upcoming earnings dates for Robotnik universe entities from EODHD.

Output:  data/markets/earnings_calendar.json
Usage:   python scripts/fetch_earnings_calendar.py
"""

import json
import os
import sys
import urllib.request
from datetime import datetime, date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "data" / "registries" / "entity_registry.json"
OUTPUT = ROOT / "data" / "markets" / "earnings_calendar.json"
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


def main():
    if not KEY:
        print("ERROR: EODHD_API_KEY not set")
        sys.exit(1)

    # Load registry for US tickers (EDGAR-listed, can query EODHD earnings)
    with open(REGISTRY) as f:
        reg = json.load(f)

    us_tickers = set()
    for k, v in reg.items():
        if isinstance(v, dict) and v.get("type") == "public" and v.get("status") != "excluded":
            # Only US-listed entities have earnings on EODHD calendar
            if " " not in k and not any(c.isalpha() and c.isupper() for c in k[1:3] if c.isalpha()):
                us_tickers.add(k)

    today = date.today()
    from_date = today.isoformat()
    to_date = (today + timedelta(days=90)).isoformat()

    print("=" * 60)
    print("ROBOTNIK EARNINGS CALENDAR FETCHER")
    print("  Range: {} to {}".format(from_date, to_date))
    print("=" * 60)

    # Fetch earnings calendar for the period
    url = "https://eodhd.com/api/calendar/earnings?from={}&to={}&api_token={}&fmt=json".format(
        from_date, to_date, KEY)

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Robotnik/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print("ERROR fetching calendar: {}".format(e))
        sys.exit(1)

    earnings = data.get("earnings", [])
    print("  Total earnings in period: {}".format(len(earnings)))

    # Filter to Robotnik universe
    # EODHD uses CODE format like "NVDA.US"
    robotnik_earnings = []
    for e in earnings:
        code = e.get("code", "")
        ticker = code.split(".")[0] if "." in code else code
        if ticker in us_tickers:
            robotnik_earnings.append({
                "ticker": ticker,
                "code": code,
                "date": e.get("report_date", ""),
                "fiscal_period": e.get("fiscal_date_ending", ""),
                "eps_estimate": e.get("estimate"),
                "currency": e.get("currency", "USD"),
                "before_after": e.get("beforeAfterMarket", ""),
            })

    robotnik_earnings.sort(key=lambda x: x.get("date", ""))
    print("  Robotnik universe matches: {}".format(len(robotnik_earnings)))

    # Group by week
    weeks = {}
    for e in robotnik_earnings:
        d = e.get("date", "")
        if d:
            week_start = date.fromisoformat(d)
            week_start -= timedelta(days=week_start.weekday())  # Monday
            wk = week_start.isoformat()
            if wk not in weeks:
                weeks[wk] = []
            weeks[wk].append(e)

    output = {
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "source": "EODHD Earnings Calendar",
        "period": {"from": from_date, "to": to_date},
        "total_robotnik_earnings": len(robotnik_earnings),
        "upcoming": robotnik_earnings[:20],  # Next 20
        "by_week": weeks,
        "all": robotnik_earnings,
    }

    with open(OUTPUT, "w") as f:
        json.dump(output, f, indent=2)

    print("\nUpcoming ({}):\n".format(min(len(robotnik_earnings), 10)))
    for e in robotnik_earnings[:10]:
        print("  {} {:8s} {} eps_est={}".format(
            e["date"], e["ticker"], e.get("before_after", ""), e.get("eps_estimate", "")))

    print("\nOutput: {}".format(OUTPUT))
    print("=" * 60)


if __name__ == "__main__":
    main()
