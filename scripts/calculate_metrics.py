#!/usr/bin/env python3
"""
Robotnik Public Markets Metrics Calculator
============================================
Calculates derived metrics for all active public entities:
  - Multi-timeframe price changes (24H, 7D, 30D, YTD, 3M, 6M, 1Y, 3Y, 5Y)
  - ATH and % from ATH
  - 30D sparkline
  - Market cap over time
  - Volume averages and sparkline

Inputs:
    data/prices/all_prices.json
    data/prices/history/*.json
    data/markets/fundamentals.json
    data/registries/entity_registry.json

Output:
    data/markets/robotnik_public_markets.json

Usage:
    python scripts/calculate_metrics.py
"""

import json
import os
from datetime import datetime, date, timedelta
from pathlib import Path
from collections import defaultdict

# ── paths ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
PRICES_PATH = ROOT / "data" / "prices" / "all_prices.json"
HISTORY_DIR = ROOT / "data" / "prices" / "history"
FUNDAMENTALS_PATH = ROOT / "data" / "markets" / "fundamentals.json"
REGISTRY_PATH = ROOT / "data" / "registries" / "entity_registry.json"
OUTPUT_PATH = ROOT / "data" / "markets" / "robotnik_public_markets.json"
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)


def load_json(path):
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def _pct_change(old, new):
    if old is None or new is None or old == 0:
        return None
    return round((new - old) / old * 100, 2)


def _find_price_on_date(series, target, window=5):
    """Find close price on target date or nearest prior within window days."""
    for offset in range(window + 1):
        d = (datetime.strptime(target, "%Y-%m-%d") - timedelta(days=offset)).strftime("%Y-%m-%d")
        if d in series:
            return series[d]
    return None


def main():
    print("=" * 60)
    print("ROBOTNIK PUBLIC MARKETS METRICS CALCULATOR")
    print("=" * 60)

    # Load data sources
    reg = load_json(REGISTRY_PATH) or {}
    prices_data = load_json(PRICES_PATH) or {"prices": []}
    fundamentals_data = load_json(FUNDAMENTALS_PATH) or {"entities": {}}
    mcap_path = ROOT / "data" / "index" / "market_caps.json"
    mcap_json = load_json(mcap_path) or {"market_caps": []}

    excluded = {k for k, v in reg.items() if isinstance(v, dict) and v.get("status") == "excluded"}
    sector_map = {k: v.get("sector", "") for k, v in reg.items()
                  if isinstance(v, dict) and v.get("status") != "excluded"}
    subsector_map = {k: v.get("subsector") for k, v in reg.items()
                     if isinstance(v, dict) and v.get("status") != "excluded"}

    # USD market cap lookup (already converted by fetch_market_caps.py)
    mcap_usd = {m["ticker"]: m["market_cap_usd"] for m in mcap_json.get("market_caps", [])
                if m.get("market_cap_usd") and m["ticker"] not in excluded}

    # Current price lookup
    current_prices = {}
    for p in prices_data.get("prices", []):
        if p["ticker"] not in excluded:
            current_prices[p["ticker"]] = p

    fundas = fundamentals_data.get("entities", {})

    today = date.today()
    today_str = today.isoformat()
    ytd_start = "{}-12-31".format(today.year - 1)
    targets = {
        "24h": (today - timedelta(days=1)).isoformat(),
        "7d": (today - timedelta(days=7)).isoformat(),
        "30d": (today - timedelta(days=30)).isoformat(),
        "ytd": ytd_start,
        "3m": (today - timedelta(days=90)).isoformat(),
        "6m": (today - timedelta(days=180)).isoformat(),
        "1y": (today - timedelta(days=365)).isoformat(),
        "3y": (today - timedelta(days=365 * 3)).isoformat(),
        "5y": (today - timedelta(days=365 * 5)).isoformat(),
    }

    results = {}
    processed = 0
    no_history = 0

    # Process each active public entity with current price data
    for ticker, cp in current_prices.items():
        sector = sector_map.get(ticker, cp.get("sector", ""))
        name = cp.get("name", ticker)
        current_close = cp.get("price", 0)
        currency = cp.get("currency", "USD")

        # Load history
        history_files = [
            HISTORY_DIR / "{}.json".format(ticker),
            HISTORY_DIR / "{}.json".format(ticker.replace(" ", "_")),
        ]
        history_series = {}  # date -> close
        volume_series = {}   # date -> volume
        all_closes = []

        for hf in history_files:
            if hf.exists():
                try:
                    hdata = json.load(open(hf))
                    for pt in hdata.get("series", []):
                        d = pt.get("date")
                        c = pt.get("close")
                        if d and c:
                            history_series[d] = c
                            all_closes.append((d, c))
                        v = pt.get("volume")
                        if d and v:
                            volume_series[d] = v
                except Exception:
                    pass
                break

        # Add current price to history
        cp_date = cp.get("date", today_str)
        if cp_date and current_close:
            history_series[cp_date] = current_close
            all_closes.append((cp_date, current_close))

        if not history_series:
            no_history += 1

        # Calculate price changes
        changes = {}
        for period, target_date in targets.items():
            old_price = _find_price_on_date(history_series, target_date)
            changes[period] = _pct_change(old_price, current_close)

        # Override 24h: use previous trading day (second-to-last date in history)
        sorted_hist = sorted(history_series.keys())
        if len(sorted_hist) >= 2:
            prev_trading_day = sorted_hist[-2]
            changes["24h"] = _pct_change(history_series[prev_trading_day], current_close)

        # Sanity check: cap any change >500% as likely data error
        for k in changes:
            if changes[k] is not None and abs(changes[k]) > 500:
                changes[k] = None  # Null out suspicious values

        # ATH
        ath = max((c for _, c in all_closes), default=None) if all_closes else None
        pct_from_ath = _pct_change(ath, current_close) if ath else None

        # 30D sparkline (last 30 days of closes)
        sorted_dates = sorted(history_series.keys())
        sparkline_30d = []
        cutoff_30d = (today - timedelta(days=35)).isoformat()
        for d in sorted_dates:
            if d >= cutoff_30d:
                sparkline_30d.append(round(history_series[d], 4))

        # Volume metrics
        sorted_vol_dates = sorted(volume_series.keys())
        vol_7d = [volume_series[d] for d in sorted_vol_dates[-7:]] if len(sorted_vol_dates) >= 7 else []
        vol_30d = [volume_series[d] for d in sorted_vol_dates[-30:]] if len(sorted_vol_dates) >= 30 else []
        vol_current = volume_series.get(sorted_vol_dates[-1]) if sorted_vol_dates else cp.get("volume")

        # Fundamentals data
        fdata = fundas.get(ticker, {})

        # Use USD market cap from market_caps.json (already currency-converted)
        usd_mcap = mcap_usd.get(ticker)
        subsector = subsector_map.get(ticker) or None

        entity = {
            "ticker": ticker,
            "name": name,
            "sector": sector,
            "subsector": subsector,
            "currency": currency,
            # Current price
            "price": current_close,
            "price_date": cp_date,
            # Price changes
            "change_24h_pct": changes.get("24h"),
            "change_7d_pct": changes.get("7d"),
            "change_30d_pct": changes.get("30d"),
            "change_ytd_pct": changes.get("ytd"),
            "change_3m_pct": changes.get("3m"),
            "change_6m_pct": changes.get("6m"),
            "change_1y_pct": changes.get("1y"),
            "change_3y_pct": changes.get("3y"),
            "change_5y_pct": changes.get("5y"),
            # ATH
            "ath": ath,
            "pct_from_ath": pct_from_ath,
            # Sparkline
            "sparkline_30d": sparkline_30d[-30:] if sparkline_30d else [],
            # Market cap (USD-converted from market_caps.json)
            "market_cap": usd_mcap,
            "shares_outstanding": fdata.get("shares_outstanding"),
            # Volume
            "volume": vol_current,
            "volume_avg_7d": round(sum(vol_7d) / len(vol_7d)) if vol_7d else None,
            "volume_avg_30d": round(sum(vol_30d) / len(vol_30d)) if vol_30d else None,
            # Fundamentals (from fetch_fundamentals.py)
            "revenue_ttm": fdata.get("revenue_ttm"),
            "revenue_growth_yoy": fdata.get("revenue_growth_yoy"),
            "operating_margin": fdata.get("operating_margin"),
            "net_income_ttm": fdata.get("net_income_ttm"),
            "eps": fdata.get("eps"),
            "pe_ratio": fdata.get("pe_ratio"),
            "forward_pe": fdata.get("forward_pe"),
            "ev": fdata.get("ev"),
            "ev_ebitda": fdata.get("ev_ebitda"),
            "ps_ratio": fdata.get("ps_ratio"),
            "pb_ratio": fdata.get("pb_ratio"),
            "dividend_yield": fdata.get("dividend_yield"),
            "total_debt": fdata.get("annual_total_debt"),
            "free_cash_flow": fdata.get("annual_free_cash_flow"),
            "next_earnings_date": fdata.get("next_earnings_date"),
        }
        results[ticker] = entity
        processed += 1

    # Save output
    output = {
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "total_entities": len(results),
        "entities_with_history": processed - no_history,
        "entities_without_history": no_history,
        "entities": results,
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    size = os.path.getsize(OUTPUT_PATH)
    print("\nProcessed: {} entities ({} with history, {} without)".format(
        processed, processed - no_history, no_history))
    print("Output: {} ({:.1f} KB)".format(OUTPUT_PATH, size / 1024))
    print("=" * 60)


if __name__ == "__main__":
    main()
