"""
Robotniks Price Updater — Alpha Vantage Edition
=================================================
Fetches latest stock prices using your Alpha Vantage API key
and outputs prices.json for the landing page.

Setup:
  pip install requests

Usage:
  python fetch_prices_alphavantage.py

Output:
  prices.json — place in the same folder as your HTML file

Notes:
  - Free tier: 25 requests/day (standard), 5 requests/min
  - For 20 tickers, this uses 20 of your 25 daily calls
  - Run once per day after market close (4:30 PM ET)
  - To automate: use cron, GitHub Actions, or a simple scheduler

Alpha Vantage docs: https://www.alphavantage.co/documentation/
"""

import requests
import json
import time
from datetime import datetime

from config import ALPHA_VANTAGE_API_KEY as API_KEY
BASE_URL = "https://www.alphavantage.co/query"

# Your universe — add/remove tickers as needed
COMPANIES = [
    {"ticker": "NVDA",  "name": "NVIDIA",              "sub": "GPU / AI Compute",          "sector": "semi",  "color": "#76B900"},
    {"ticker": "TSM",   "name": "TSMC",                "sub": "Foundry",                   "sector": "semi",  "color": "#E31937"},
    {"ticker": "AVGO",  "name": "Broadcom",             "sub": "Networking / AI ASICs",     "sector": "semi",  "color": "#CC092F"},
    {"ticker": "ASML",  "name": "ASML",                 "sub": "EUV Lithography",           "sector": "infra", "color": "#00A3E0"},
    {"ticker": "AMD",   "name": "AMD",                  "sub": "GPU / CPU / FPGA",          "sector": "semi",  "color": "#ED1C24"},
    {"ticker": "MU",    "name": "Micron",               "sub": "Memory (DRAM / NAND)",      "sector": "semi",  "color": "#0058A3"},
    {"ticker": "TXN",   "name": "Texas Instruments",    "sub": "Analog / MCU",              "sector": "semi",  "color": "#CC0000"},
    {"ticker": "ISRG",  "name": "Intuitive Surgical",   "sub": "Surgical robotics",         "sector": "robo",  "color": "#00658A"},
    {"ticker": "QCOM",  "name": "Qualcomm",             "sub": "Mobile SoC / Edge AI",      "sector": "semi",  "color": "#3253DC"},
    {"ticker": "AMAT",  "name": "Applied Materials",    "sub": "Deposition / Etch",         "sector": "infra", "color": "#B5BD00"},
    {"ticker": "INTC",  "name": "Intel",                "sub": "IDM / Foundry services",    "sector": "semi",  "color": "#0071C5"},
    {"ticker": "ARM",   "name": "Arm Holdings",         "sub": "CPU IP / Licensing",        "sector": "semi",  "color": "#0091BD"},
    {"ticker": "LRCX",  "name": "Lam Research",         "sub": "Etch / Deposition equip.",  "sector": "infra", "color": "#003DA5"},
    {"ticker": "ABB",   "name": "ABB Ltd",              "sub": "Robotics / Electrification","sector": "robo",  "color": "#FF000F"},
    {"ticker": "MRVL",  "name": "Marvell Technology",   "sub": "Data infra / Custom",       "sector": "semi",  "color": "#8E1B3F"},
    {"ticker": "ROK",   "name": "Rockwell Automation",  "sub": "Industrial automation",     "sector": "robo",  "color": "#C8102E"},
    {"ticker": "FANUY", "name": "Fanuc",                "sub": "Industrial robots / CNC",   "sector": "robo",  "color": "#FFD100"},
    {"ticker": "TER",   "name": "Teradyne",             "sub": "ATE / Cobots (UR)",         "sector": "robo",  "color": "#E31B23"},
    {"ticker": "SYM",   "name": "Symbotic",             "sub": "Warehouse AI automation",   "sector": "robo",  "color": "#5B2D8E"},
    {"ticker": "CGNX",  "name": "Cognex",               "sub": "Machine vision",            "sector": "robo",  "color": "#8C1D40"},
]


def fetch_quote(ticker: str):
    """Fetch a single stock quote from Alpha Vantage GLOBAL_QUOTE endpoint."""
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": ticker,
        "apikey": API_KEY,
    }
    try:
        resp = requests.get(BASE_URL, params=params, timeout=10)
        data = resp.json()

        if "Global Quote" not in data or not data["Global Quote"]:
            print(f"  Warning: No data returned for {ticker}")
            return None

        q = data["Global Quote"]
        return {
            "price": float(q.get("05. price", 0)),
            "change": float(q.get("09. change", 0)),
            "change_pct": float(q.get("10. change percent", "0").replace("%", "")),
            "volume": int(q.get("06. volume", 0)),
            "prev_close": float(q.get("08. previous close", 0)),
        }

    except Exception as e:
        print(f"  Error fetching {ticker}: {e}")
        return None


def fetch_overview(ticker: str) -> str:
    """Fetch market cap from Company Overview endpoint. Uses 1 API call."""
    params = {
        "function": "OVERVIEW",
        "symbol": ticker,
        "apikey": API_KEY,
    }
    try:
        resp = requests.get(BASE_URL, params=params, timeout=10)
        data = resp.json()
        mcap_raw = int(data.get("MarketCapitalization", 0))
        if mcap_raw >= 1e12:
            return f"{mcap_raw/1e12:.2f}T"
        elif mcap_raw >= 1e9:
            return f"{mcap_raw/1e9:.0f}B"
        elif mcap_raw >= 1e6:
            return f"{mcap_raw/1e6:.0f}M"
        return "N/A"
    except:
        return "N/A"


def main():
    print(f"Robotniks Price Updater — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Fetching quotes for {len(COMPANIES)} tickers...\n")

    results = []

    for i, company in enumerate(COMPANIES):
        t = company["ticker"]
        print(f"  [{i+1}/{len(COMPANIES)}] {t}...", end=" ")

        quote = fetch_quote(t)
        if not quote:
            print("SKIP")
            continue

        # Format market cap — we'll estimate from price * approximate shares
        # For accurate mcap, uncomment the line below (uses 1 extra API call per ticker)
        # mcap = fetch_overview(t)
        mcap = "N/A"  # Using static mcap for now to save API calls

        results.append({
            **company,
            "price": round(quote["price"], 2),
            "change": round(quote["change_pct"], 2),
            # "mcap": mcap,  # Uncomment if using fetch_overview
        })
        print(f"${quote['price']:.2f} ({'+' if quote['change_pct'] >= 0 else ''}{quote['change_pct']:.2f}%)")

        # Rate limit: Alpha Vantage allows 5 calls/min on free tier
        if i < len(COMPANIES) - 1:
            time.sleep(12)  # 12s between calls = 5 per minute

    # Output
    output = {
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "source": "Alpha Vantage",
        "companies": results,
    }

    with open("prices.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nDone! Saved {len(results)} companies to prices.json")
    print(f"Timestamp: {output['updated']}")
    print(f"\nTo use: place prices.json alongside your HTML file.")
    print(f"The HTML can load it with: fetch('prices.json').then(r => r.json())")


if __name__ == "__main__":
    main()
