#!/usr/bin/env python3
"""
Robotnik Fundamentals Fetcher
==============================
Fetches financial fundamentals for all active public entities from EODHD.

Endpoint: https://eodhd.com/api/fundamentals/{TICKER}?api_token={KEY}&fmt=json

Extracts: market cap, revenue, margins, valuation multiples, shares,
          financials, earnings, and segment data where available.

Output:  data/markets/fundamentals.json
Usage:   python scripts/fetch_fundamentals.py
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

# ── paths ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT / "data" / "registries" / "entity_registry.json"
OUTPUT_PATH = ROOT / "data" / "markets" / "fundamentals.json"
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

# ── load env ─────────────────────────────────────────────────────────────
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

# ── import universe from fetch_prices.py ─────────────────────────────────
sys.path.insert(0, str(ROOT / "scripts"))
from fetch_prices import EQUITIES, ticker_to_eodhd


def _safe(d, *keys, default=None):
    """Safely navigate nested dicts."""
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k, default)
    return d


def _num(val):
    """Convert to float or return None."""
    if val is None or val == "" or val == "NA" or val == "None":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def fetch_fundamentals(eodhd_symbol):
    """Fetch fundamentals JSON from EODHD."""
    url = "https://eodhd.com/api/fundamentals/{}?api_token={}&fmt=json".format(
        eodhd_symbol, EODHD_KEY)
    req = urllib.request.Request(url, headers={"User-Agent": "Robotnik/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def extract_fundamentals(ticker, eodhd_symbol, data):
    """Extract key fields from EODHD fundamentals response."""
    hl = data.get("Highlights", {}) or {}
    val = data.get("Valuation", {}) or {}
    shares = data.get("SharesStats", {}) or {}
    gen = data.get("General", {}) or {}
    earn = data.get("Earnings", {}) or {}

    # Most recent annual financials
    income = data.get("Financials", {}).get("Income_Statement", {}).get("yearly", {}) or {}
    balance = data.get("Financials", {}).get("Balance_Sheet", {}).get("yearly", {}) or {}
    cashflow = data.get("Financials", {}).get("Cash_Flow", {}).get("yearly", {}) or {}

    # Get most recent year's data
    latest_income = {}
    latest_balance = {}
    latest_cf = {}
    if income:
        latest_key = sorted(income.keys(), reverse=True)[0]
        latest_income = income[latest_key] or {}
    if balance:
        latest_key = sorted(balance.keys(), reverse=True)[0]
        latest_balance = balance[latest_key] or {}
    if cashflow:
        latest_key = sorted(cashflow.keys(), reverse=True)[0]
        latest_cf = cashflow[latest_key] or {}

    # Earnings history — most recent
    earn_history = earn.get("History", {}) or {}
    latest_earn = {}
    if earn_history:
        latest_earn_key = sorted(earn_history.keys(), reverse=True)[0]
        latest_earn = earn_history[latest_earn_key] or {}

    # Next earnings date
    next_earnings = None
    for k in sorted(earn_history.keys(), reverse=True):
        e = earn_history[k]
        if e and e.get("reportDate"):
            rd = e["reportDate"]
            if rd >= datetime.utcnow().strftime("%Y-%m-%d"):
                next_earnings = rd
                break

    return {
        "ticker": ticker,
        "eodhd_symbol": eodhd_symbol,
        "name": gen.get("Name", ""),
        "sector": gen.get("Sector", ""),
        "industry": gen.get("Industry", ""),
        "country": gen.get("CountryName", ""),
        "currency": gen.get("CurrencyCode", "USD"),
        "exchange": gen.get("Exchange", ""),
        # Highlights
        "market_cap": _num(hl.get("MarketCapitalization")),
        "revenue_ttm": _num(hl.get("RevenueTTM")),
        "revenue_growth_yoy": _num(hl.get("QuarterlyRevenueGrowthYOY")),
        "operating_margin": _num(hl.get("OperatingMarginTTM")),
        "profit_margin": _num(hl.get("ProfitMargin")),
        "net_income_ttm": _num(hl.get("NetIncomeTTM") if "NetIncomeTTM" in hl
                                else latest_income.get("netIncome")),
        "eps": _num(hl.get("EarningsShare")),
        "eps_diluted": _num(hl.get("DilutedEpsTTM")),
        "pe_ratio": _num(hl.get("PERatio")),
        "forward_pe": _num(hl.get("ForwardPE")),
        "dividend_yield": _num(hl.get("DividendYield")),
        # Valuation
        "ev": _num(val.get("EnterpriseValue")),
        "ev_ebitda": _num(val.get("EnterpriseValueEbitda")),
        "ev_revenue": _num(val.get("EnterpriseValueRevenue")),
        "ps_ratio": _num(val.get("PriceSalesTTM")),
        "pb_ratio": _num(val.get("PriceBookMRQ")),
        # Shares
        "shares_outstanding": _num(shares.get("SharesOutstanding")),
        "shares_float": _num(shares.get("SharesFloat")),
        "short_ratio": _num(shares.get("ShortRatio")),
        "pct_insiders": _num(shares.get("PercentInsiders")),
        "pct_institutions": _num(shares.get("PercentInstitutions")),
        # Annual financials (most recent)
        "annual_revenue": _num(latest_income.get("totalRevenue")),
        "annual_gross_profit": _num(latest_income.get("grossProfit")),
        "annual_operating_income": _num(latest_income.get("operatingIncome")),
        "annual_net_income": _num(latest_income.get("netIncome")),
        "annual_total_assets": _num(latest_balance.get("totalAssets")),
        "annual_total_debt": _num(latest_balance.get("longTermDebt")),
        "annual_total_equity": _num(latest_balance.get("totalStockholderEquity")),
        "annual_free_cash_flow": _num(latest_cf.get("freeCashFlow")),
        # Earnings
        "next_earnings_date": next_earnings,
        "last_eps_actual": _num(latest_earn.get("epsActual")),
        "last_eps_estimate": _num(latest_earn.get("epsEstimate")),
        "last_eps_surprise_pct": _num(latest_earn.get("epsDifference")),
        # Status
        "fetch_status": "success",
    }


def main():
    if not EODHD_KEY:
        print("ERROR: EODHD_API_KEY not set")
        sys.exit(1)

    # Load entity registry to get active public tickers
    with open(REGISTRY_PATH) as f:
        reg = json.load(f)

    active_public = {}
    for k, v in reg.items():
        if isinstance(v, dict) and v.get("type") == "public" and v.get("status") != "excluded":
            active_public[k] = v

    # Build EODHD symbol mapping from EQUITIES list
    eodhd_map = {}
    for ticker, company, sector, country in EQUITIES:
        if ticker in active_public:
            eodhd_map[ticker] = ticker_to_eodhd(ticker, country)

    # Some tickers not in EQUITIES (tokens, etc.) — skip
    equity_tickers = [t for t in active_public if t in eodhd_map]

    print("=" * 60)
    print("ROBOTNIK FUNDAMENTALS FETCHER")
    print("  Source: EODHD (All-in-One)")
    print("  Entities: {} active public equities".format(len(equity_tickers)))
    print("=" * 60)

    ts = datetime.utcnow().isoformat() + "Z"
    results = {}
    errors = []
    total = len(equity_tickers)

    for i, ticker in enumerate(equity_tickers, 1):
        eodhd_sym = eodhd_map[ticker]
        if eodhd_sym == "UNAVAILABLE":
            errors.append("{} — UNAVAILABLE on EODHD".format(ticker))
            continue

        print("[{}/{}] {} -> {} ...".format(i, total, ticker, eodhd_sym), end=" ")

        try:
            data = fetch_fundamentals(eodhd_sym)
            if data and isinstance(data, dict) and "General" in data:
                result = extract_fundamentals(ticker, eodhd_sym, data)
                results[ticker] = result
                mc = result.get("market_cap")
                rev = result.get("revenue_ttm")
                mc_str = "${:.0f}B".format(mc / 1e9) if mc else "—"
                rev_str = "${:.0f}B".format(rev / 1e9) if rev else "—"
                print("OK (mcap={}, rev={})".format(mc_str, rev_str))
            else:
                results[ticker] = {"ticker": ticker, "eodhd_symbol": eodhd_sym,
                                   "fetch_status": "no_data"}
                errors.append("{} — no fundamentals data".format(ticker))
                print("NO DATA")
        except urllib.error.HTTPError as e:
            results[ticker] = {"ticker": ticker, "eodhd_symbol": eodhd_sym,
                               "fetch_status": "error", "error": str(e)}
            errors.append("{} — HTTP {}".format(ticker, e.code))
            print("HTTP {}".format(e.code))
        except Exception as e:
            results[ticker] = {"ticker": ticker, "eodhd_symbol": eodhd_sym,
                               "fetch_status": "error", "error": str(e)}
            errors.append("{} — {}".format(ticker, e))
            print("ERROR: {}".format(e))

        time.sleep(0.1)  # 100ms delay — well within 1000/min limit

    # Save output
    output = {
        "last_updated": ts,
        "source": "EODHD Fundamentals API (All-in-One)",
        "total_entities": len(results),
        "success_count": sum(1 for v in results.values() if v.get("fetch_status") == "success"),
        "error_count": len(errors),
        "entities": results,
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print("\n" + "=" * 60)
    print("DONE: {}/{} entities fetched ({} errors)".format(
        output["success_count"], total, len(errors)))
    if errors:
        print("\nErrors ({}):\n  {}".format(len(errors), "\n  ".join(errors[:20])))
        if len(errors) > 20:
            print("  ... and {} more".format(len(errors) - 20))
    print("\nOutput: {}".format(OUTPUT_PATH))
    print("=" * 60)


if __name__ == "__main__":
    main()
