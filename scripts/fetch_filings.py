"""
Robotnik SEC EDGAR Filings Fetcher
=====================================
Fetches recent SEC filings (10-K, 10-Q, 8-K, 20-F) for tracked
robotics, semiconductor, and space technology companies. Outputs filings.json.

No API key needed — SEC EDGAR is free and public.
No external dependencies — uses urllib from stdlib.

Usage:
  python fetch_filings.py

Output:
  filings.json — most recent filing per tracked company
  archive_filings.json — full historical archive
"""

import json
import time
import urllib.request
from datetime import datetime, timedelta
import hashlib
from config import FILINGS_JSON, FILINGS_ARCHIVE_JSON
from archive_utils import archive_and_filter

USER_AGENT = "Robotniks/1.0 (robotniks.com, data@robotniks.com)"

# Tracked companies — same universe as index.html
COMPANIES = [
    {"ticker": "NVDA", "name": "NVIDIA"},
    {"ticker": "TSM", "name": "TSMC"},
    {"ticker": "AVGO", "name": "Broadcom"},
    {"ticker": "ASML", "name": "ASML"},
    {"ticker": "AMD", "name": "AMD"},
    {"ticker": "MU", "name": "Micron"},
    {"ticker": "TXN", "name": "Texas Instruments"},
    {"ticker": "ISRG", "name": "Intuitive Surgical"},
    {"ticker": "QCOM", "name": "Qualcomm"},
    {"ticker": "AMAT", "name": "Applied Materials"},
    {"ticker": "INTC", "name": "Intel"},
    {"ticker": "ARM", "name": "Arm Holdings"},
    {"ticker": "LRCX", "name": "Lam Research"},
    {"ticker": "ABB", "name": "ABB Ltd"},
    {"ticker": "MRVL", "name": "Marvell Technology"},
    {"ticker": "ROK", "name": "Rockwell Automation"},
    {"ticker": "FANUY", "name": "Fanuc"},
    {"ticker": "TER", "name": "Teradyne"},
    {"ticker": "SYM", "name": "Symbotic"},
    {"ticker": "CGNX", "name": "Cognex"},
    # Space technology
    {"ticker": "RKLB", "name": "Rocket Lab"},
    {"ticker": "PL", "name": "Planet Labs"},
    {"ticker": "ASTS", "name": "AST SpaceMobile"},
    {"ticker": "RDW", "name": "Redwire"},
    {"ticker": "LUNR", "name": "Intuitive Machines"},
    {"ticker": "BKSY", "name": "BlackSky Technology"},
    {"ticker": "SPIR", "name": "Spire Global"},
    {"ticker": "VSAT", "name": "Viasat"},
    {"ticker": "SATS", "name": "EchoStar"},
    {"ticker": "IRDM", "name": "Iridium Communications"},
    {"ticker": "GSAT", "name": "Globalstar"},
    {"ticker": "SPCE", "name": "Virgin Galactic"},
    {"ticker": "FLY", "name": "Firefly Aerospace"},
    {"ticker": "SATL", "name": "Satellogic"},
    {"ticker": "SIDU", "name": "Sidus Space"},
    {"ticker": "MNTS", "name": "Momentus"},
    {"ticker": "KRMN", "name": "Karman Holdings"},
    {"ticker": "VOYG", "name": "Voyager Technologies"},
    {"ticker": "HEI", "name": "HEICO"},
    {"ticker": "HXL", "name": "Hexcel"},
    {"ticker": "DCO", "name": "Ducommun"},
    {"ticker": "GOGO", "name": "Gogo"},
    {"ticker": "NN", "name": "NextNav"},
    {"ticker": "PSN", "name": "Parsons"},
    {"ticker": "ESE", "name": "ESCO Technologies"},
    {"ticker": "TTMI", "name": "TTM Technologies"},
    {"ticker": "TSAT", "name": "Telesat"},
]

# Filing types we care about
TARGET_FORMS = {"10-K", "10-Q", "8-K", "20-F", "6-K", "10-K/A", "10-Q/A"}

# How far back to look
LOOKBACK_DAYS = 180


def fetch_json(url):
    """Fetch JSON from a URL with required User-Agent header."""
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def load_ticker_to_cik():
    """Load SEC's ticker-to-CIK mapping."""
    print("  Loading ticker → CIK mapping...")
    data = fetch_json("https://www.sec.gov/files/company_tickers.json")
    mapping = {}
    for entry in data.values():
        ticker = entry.get("ticker", "").upper()
        cik = str(entry.get("cik_str", "")).zfill(10)
        mapping[ticker] = cik
    return mapping


def fetch_company_filings(cik, company_name, ticker, cutoff_date):
    """Fetch recent filings for a single company."""
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    try:
        data = fetch_json(url)
    except Exception as e:
        print(f"    [{ticker}] Failed to fetch: {e}")
        return []

    recent = data.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    accessions = recent.get("accessionNumber", [])
    descriptions = recent.get("primaryDocDescription", [])

    filings = []
    for i in range(len(forms)):
        form = forms[i] if i < len(forms) else ""
        date = dates[i] if i < len(dates) else ""
        accession = accessions[i] if i < len(accessions) else ""
        desc = descriptions[i] if i < len(descriptions) else ""

        if form not in TARGET_FORMS:
            continue
        if date < cutoff_date:
            continue

        # Build filing URL
        accession_clean = accession.replace("-", "")
        filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{accession_clean}/"

        filings.append({
            "id": hashlib.sha256(filing_url.encode()).hexdigest()[:12],
            "ticker": ticker,
            "company": company_name,
            "form_type": form,
            "date": date,
            "description": desc or form,
            "url": filing_url,
        })

    return filings


def main():
    print("Fetching SEC EDGAR filings...")

    ticker_to_cik = load_ticker_to_cik()
    cutoff = (datetime.now() - timedelta(days=LOOKBACK_DAYS)).strftime("%Y-%m-%d")
    all_filings = []

    for company in COMPANIES:
        ticker = company["ticker"]
        name = company["name"]
        cik = ticker_to_cik.get(ticker)

        if not cik:
            print(f"    [{ticker}] CIK not found — skipping")
            continue

        filings = fetch_company_filings(cik, name, ticker, cutoff)
        all_filings.extend(filings)
        print(f"    [{ticker}] {len(filings)} filings")
        time.sleep(0.12)  # respect 10 req/s limit

    # Archive all filings
    archive_and_filter(
        items=all_filings,
        archive_path=FILINGS_ARCHIVE_JSON,
        key_field="id",
        current_filter_fn=lambda f: True,
        data_key="filings",
    )

    # Keep only most recent filing per company for live output
    all_filings.sort(key=lambda x: x["date"], reverse=True)
    seen_tickers = set()
    most_recent = []
    for f in all_filings:
        if f["ticker"] not in seen_tickers:
            seen_tickers.add(f["ticker"])
            most_recent.append(f)

    output = {
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "source": "SEC EDGAR",
        "count": len(most_recent),
        "filings": most_recent,
    }

    with open(FILINGS_JSON, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nWrote {len(most_recent)} filings (most recent per company) to {FILINGS_JSON}")
    print(f"Archive: {len(all_filings)} total filings in {FILINGS_ARCHIVE_JSON}")


if __name__ == "__main__":
    main()
