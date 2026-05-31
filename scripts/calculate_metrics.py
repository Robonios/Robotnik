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
    data/index/weights.json          (index constituents — RPM mirrors the index)
    data/index/market_caps.json
    data/registries/entity_registry.json

NOTE: EODHD fundamentals (revenue/margins/PE/EV-EBITDA/shares/etc.) were removed in the
B-sweep — EODHD is decommissioned and those fields were a licensing exposure via this
displayed file. Re-source from a clean-terms vendor before re-adding.

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
WEIGHTS_PATH = ROOT / "data" / "index" / "weights.json"
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


def _assert_periods_distinct(entities, field_a, field_b, max_match_pct=0.9, tol=0.01):
    """Fail the pipeline if two return periods produce identical values for
    more than `max_match_pct` of rows where both are populated.

    A handful of rows matching by coincidence (zero-volume days, halted
    tickers) is normal. Nearly every row matching means one of:
      - a render bug reading the same field twice
      - a fetcher bug writing one value to both fields
      - stale history that collapses the lookback window
    Either way, the UI shouldn't silently ship it.
    """
    matches = total = 0
    for r in entities.values():
        a = r.get(field_a)
        b = r.get(field_b)
        if a is None or b is None:
            continue
        total += 1
        if abs(a - b) < tol:
            matches += 1
    if total > 10 and matches / total > max_match_pct:
        raise RuntimeError(
            "Data integrity check failed: {a} and {b} are identical for "
            "{m}/{t} entities ({pct:.1f}%). Threshold is {lim:.0%}. "
            "Likely causes: duplicate field assignment, stale price history, "
            "or lookup collapse onto the last-close date.".format(
                a=field_a, b=field_b, m=matches, t=total,
                pct=matches / total * 100, lim=max_match_pct,
            )
        )


def _find_price_on_date(series, target, window=5):
    """Find close price on target date or nearest prior within window days.

    Returns (price, actual_date) tuple. The actual_date is critical: it lets
    the caller detect cases where two different periods (e.g. "24h" and "7d")
    both resolve to the same baseline date — a sign that price history is
    stale and the returns are degenerate. The caller should null the shorter-
    overlapping period in that case, otherwise the UI shows identical values
    for different time windows. See the 7D/30D identical-values bug
    investigation for the full chain.

    Returns (None, None) if no price is found within the window.
    """
    target_dt = datetime.strptime(target, "%Y-%m-%d")
    for offset in range(window + 1):
        d = (target_dt - timedelta(days=offset)).strftime("%Y-%m-%d")
        if d in series:
            return series[d], d
    return None, None


def main():
    print("=" * 60)
    print("ROBOTNIK PUBLIC MARKETS METRICS CALCULATOR")
    print("=" * 60)

    # Load data sources
    reg = load_json(REGISTRY_PATH) or {}
    prices_data = load_json(PRICES_PATH) or {"prices": []}
    mcap_path = ROOT / "data" / "index" / "market_caps.json"
    mcap_json = load_json(mcap_path) or {"market_caps": []}

    # RPM mirrors the INDEX: restrict to the index constituents (weights.json) so the
    # displayed Public Market Universe == the validated index — no excluded names, no
    # tokens (both already absent from the index), structurally pinned to the
    # reverse-parity-guarded 196-name membership set.
    weights_json = load_json(WEIGHTS_PATH) or {"weights": []}
    index_constituents = {w["ticker"] for w in weights_json.get("weights", [])}

    excluded = {k for k, v in reg.items() if isinstance(v, dict) and v.get("status") == "excluded"}
    sector_map = {k: v.get("sector", "") for k, v in reg.items()
                  if isinstance(v, dict) and v.get("status") != "excluded"}
    subsector_map = {k: v.get("subsector") for k, v in reg.items()
                     if isinstance(v, dict) and v.get("status") != "excluded"}
    value_chain_map = {k: v.get("value_chain") for k, v in reg.items()
                       if isinstance(v, dict) and v.get("status") != "excluded"}

    # USD market cap lookup (already converted by fetch_market_caps.py)
    mcap_usd = {m["ticker"]: m["market_cap_usd"] for m in mcap_json.get("market_caps", [])
                if m.get("market_cap_usd") and m["ticker"] not in excluded}

    # Current price lookup — restricted to the index constituents (RPM mirrors index)
    current_prices = {}
    for p in prices_data.get("prices", []):
        if p["ticker"] in index_constituents:
            current_prices[p["ticker"]] = p

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

        # Calculate price changes. Each period uses a target-date lookup that
        # walks backward by up to `window` days to find the nearest earlier
        # trading-day close — so "7d" might resolve to 8 days ago over a long
        # weekend, and that's fine.
        changes = {}
        baseline_dates = {}
        for period, target_date in targets.items():
            old_price, old_date = _find_price_on_date(history_series, target_date)
            changes[period] = _pct_change(old_price, current_close)
            baseline_dates[period] = old_date

        # Override 24h: the "last available close vs current" interpretation
        # only makes sense if the last close is actually recent. When price
        # history is stale (e.g. last close 10 days ago), sorted_hist[-2]
        # produces a 10-day return labelled "24h" AND collides with the 7d
        # lookback, making the two columns identical. Gate the override on a
        # freshness check: the previous trading day must be within 3 days of
        # yesterday; otherwise 24h is None and the target-based lookup above
        # stands (which will itself be None if yesterday's close isn't within
        # its own window).
        sorted_hist = sorted(history_series.keys())
        if len(sorted_hist) >= 2:
            prev_trading_day = sorted_hist[-2]
            prev_dt = datetime.strptime(prev_trading_day, "%Y-%m-%d").date()
            yesterday = today - timedelta(days=1)
            if (yesterday - prev_dt).days <= 3:
                changes["24h"] = _pct_change(history_series[prev_trading_day], current_close)
                baseline_dates["24h"] = prev_trading_day
            else:
                # Stale history — don't pretend the last-close return is 24h.
                changes["24h"] = None
                baseline_dates["24h"] = None

        # Sanity check: cap implausible short-period moves as likely data
        # errors (a 500%+ move in a single day/week is virtually always
        # a split or bad tick, not a real return). For long periods we
        # deliberately NEVER cap — NVDA's 5Y is +1216%, AVGO's is +875%,
        # and those are the numbers we want to surface, not silently null.
        SHORT_PERIOD_CAP = 500
        for k in ("24h", "7d", "30d"):
            v = changes.get(k)
            if v is not None and abs(v) > SHORT_PERIOD_CAP:
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

        # Use USD market cap from market_caps.json (already currency-converted)
        usd_mcap = mcap_usd.get(ticker)
        subsector = subsector_map.get(ticker) or None
        value_chain = value_chain_map.get(ticker) or None

        entity = {
            "ticker": ticker,
            "name": name,
            "sector": sector,
            "subsector": subsector,
            "value_chain": value_chain,
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
            # Market cap (USD-converted from market_caps.json — Yahoo, not EODHD)
            "market_cap": usd_mcap,
            # Volume
            "volume": vol_current,
            "volume_avg_7d": round(sum(vol_7d) / len(vol_7d)) if vol_7d else None,
            "volume_avg_30d": round(sum(vol_30d) / len(vol_30d)) if vol_30d else None,
            # EODHD fundamentals (revenue/margins/PE/EV-EBITDA/shares/earnings) removed in
            # the B-sweep: EODHD decommissioned + licensing exposure via this displayed file.
            # Re-source from a clean-terms vendor before re-adding.
        }
        results[ticker] = entity
        processed += 1

    # Regression guard: two different return windows should rarely produce
    # identical values. If they match for >90% of rows, it's almost certainly
    # a pipeline bug (duplicate field, wrong calculation) or catastrophically
    # stale history data. Fail loudly so the next run of a refresh workflow
    # doesn't silently ship garbage to the live page.
    _assert_periods_distinct(results, "change_7d_pct", "change_24h_pct")
    _assert_periods_distinct(results, "change_7d_pct", "change_30d_pct")
    _assert_periods_distinct(results, "change_30d_pct", "change_ytd_pct")

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
