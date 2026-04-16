#!/usr/bin/env python3
"""
Robotnik Composite Index Calculator

Produces a market-cap weighted index with:
- 5% single-entity cap with iterative redistribution
- Base value 1000.00 (set to earliest available history date)
- 4 sub-indices: Semiconductor, Robotics, Cross-stack, Token
- Historical backfill using price history files
- Outputs: weights.json, robotnik_index.json, sub_indices.json,
           base_date.json, summary.json
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict

# ── paths ────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR   = os.path.dirname(SCRIPT_DIR)
INDEX_DIR  = os.path.join(ROOT_DIR, "data", "index")
HISTORY_DIR = os.path.join(ROOT_DIR, "data", "prices", "history")

MCAP_PATH    = os.path.join(INDEX_DIR, "market_caps.json")
PRICES_PATH  = os.path.join(ROOT_DIR, "data", "prices", "all_prices.json")

WEIGHTS_PATH   = os.path.join(INDEX_DIR, "weights.json")
INDEX_PATH     = os.path.join(INDEX_DIR, "robotnik_index.json")
SUB_IDX_PATH   = os.path.join(INDEX_DIR, "sub_indices.json")
BASE_DATE_PATH = os.path.join(INDEX_DIR, "base_date.json")
SUMMARY_PATH   = os.path.join(INDEX_DIR, "summary.json")

BASE_VALUE = 1000.0
NORMALISE_DATE = "2025-03-31"  # All indices normalised to BASE_VALUE on this date
CAP_LIMIT  = 0.05  # 5% max weight per entity
MIN_MARKET_CAP = 10_000_000  # $10M minimum for index inclusion

# sector mapping for sub-indices (Cross-Stack eliminated — entities reclassified)
SECTOR_MAP = {
    "Semiconductor":      "Semiconductor",
    "Semiconductors":     "Semiconductor",
    "Semis":              "Semiconductor",
    "Robotics":           "Robotics",
    "Space":              "Space",
    "Cross-stack":        "Semiconductor",  # Legacy: former Cross-Stack → Semiconductor
    "Cross-Stack":        "Semiconductor",  # Legacy: former Cross-Stack → Semiconductor
    "Materials":          "Materials",
    "Materials & Inputs": "Materials",
    "Token":              "Token",
    "Tokens":             "Token",
}


def load_json(path):
    with open(path) as f:
        return json.load(f)


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  -> {os.path.relpath(path, ROOT_DIR)}")


def compute_capped_weights(entities, cap=CAP_LIMIT):
    """
    Market-cap weighted with iterative 5% cap redistribution.
    Each entity above the cap is pinned at cap%; the excess is
    redistributed proportionally among uncapped entities. Repeat
    until no entity exceeds the cap.
    """
    total_mcap = sum(e["market_cap_usd"] for e in entities)
    if total_mcap == 0:
        return {e["ticker"]: 0.0 for e in entities}

    weights = {e["ticker"]: e["market_cap_usd"] / total_mcap for e in entities}

    for _ in range(50):  # max iterations (converges in <10)
        capped = {t: w for t, w in weights.items() if w > cap}
        if not capped:
            break

        excess = sum(w - cap for w in capped.values())
        uncapped = {t: w for t, w in weights.items() if w <= cap}
        uncapped_total = sum(uncapped.values())

        if uncapped_total == 0:
            break

        for t in capped:
            weights[t] = cap

        for t in uncapped:
            weights[t] += excess * (uncapped[t] / uncapped_total)

    return weights


def load_all_history():
    """
    Load all price history files and build:
    - price_matrix: {date_str -> {ticker -> close_price}}
    - ticker_meta: {ticker -> {name, sector}}
    - all_dates: sorted list of all dates
    """
    history_dir = Path(HISTORY_DIR)
    if not history_dir.exists():
        print("  WARNING: No price history directory found. Run fetch_price_history.py first.")
        return {}, {}, []

    price_matrix = defaultdict(dict)
    ticker_meta = {}

    json_files = list(history_dir.glob("*.json"))
    print(f"  Loading {len(json_files)} history files...")

    for f in json_files:
        try:
            data = json.loads(f.read_text())
            ticker = data.get("ticker", f.stem)
            name = data.get("name", ticker)
            sector = SECTOR_MAP.get(data.get("sector", ""), data.get("sector", "Other"))
            ticker_meta[ticker] = {"name": name, "sector": sector}

            for point in data.get("series", []):
                d = point.get("date")
                close = point.get("close")
                if d and close is not None and close > 0:
                    price_matrix[d][ticker] = close
        except Exception:
            continue

    all_dates = sorted(price_matrix.keys())
    print(f"  Date range: {all_dates[0]} to {all_dates[-1]} ({len(all_dates)} trading days)")
    print(f"  Tickers with history: {len(ticker_meta)}")

    return price_matrix, ticker_meta, all_dates


def backfill_index(entities, weights, price_matrix, all_dates, base_date_str, current_prices=None):
    """
    Calculate index values for every date in history.
    Uses fixed weights (current market-cap weights) applied retroactively.
    Base value = 1000.00 at base_date_str.
    Carries forward prices when a ticker is missing on a given day.
    """
    # Get base prices (prices on base date)
    base_prices = price_matrix.get(base_date_str, {})
    if not base_prices:
        # Find nearest available date
        for d in all_dates:
            if d >= base_date_str:
                base_prices = price_matrix[d]
                base_date_str = d
                break

    # Build carry-forward price matrix: for each date, if a ticker has no price,
    # use the most recent previous price (avoids coverage drops on partial days)
    last_known = {}  # ticker -> most recent close price

    series = []
    for d in all_dates:
        if d < base_date_str:
            # Still update last_known for carry-forward
            for ticker, price in price_matrix.get(d, {}).items():
                last_known[ticker] = price
            continue

        # Update last_known with today's prices
        for ticker, price in price_matrix.get(d, {}).items():
            last_known[ticker] = price

        weighted_return = 0.0
        active_weight = 0.0

        for ticker, weight in weights.items():
            p_now = last_known.get(ticker)
            p_base = base_prices.get(ticker)
            if p_now is not None and p_base is not None and p_base > 0:
                weighted_return += weight * (p_now / p_base)
                active_weight += weight

        if active_weight > 0:
            value = BASE_VALUE * (weighted_return / active_weight)
        else:
            value = series[-1]["value"] if series else BASE_VALUE

        series.append({"date": d, "value": round(value, 2)})

    return series, base_date_str, base_prices


def normalise_series(series, target_date=NORMALISE_DATE, target_value=BASE_VALUE):
    """
    Rescale an entire index series so that the value on target_date = target_value.
    If target_date is not in the series, use the nearest available date.
    Returns (normalised_series, actual_target_date, scale_factor).
    """
    if not series:
        return series, target_date, 1.0

    # Find the value on or nearest to target_date
    raw_value = None
    actual_date = None
    for pt in series:
        if pt["date"] == target_date:
            raw_value = pt["value"]
            actual_date = target_date
            break
        if pt["date"] > target_date and raw_value is None:
            raw_value = pt["value"]
            actual_date = pt["date"]
            break
        raw_value = pt["value"]
        actual_date = pt["date"]

    if raw_value is None or raw_value == 0:
        return series, target_date, 1.0

    scale_factor = target_value / raw_value
    normalised = [{"date": pt["date"], "value": round(pt["value"] * scale_factor, 2)} for pt in series]
    return normalised, actual_date, scale_factor


def main():
    print("Robotnik Index Calculator (with backfill)")
    print("=" * 50)

    # ── load inputs ──────────────────────────────────────────────────
    mcap_data   = load_json(MCAP_PATH)
    prices_data = load_json(PRICES_PATH)

    entities = mcap_data["market_caps"]
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # build price lookup: ticker -> price (USD)
    prices_by_ticker = {}
    for p in prices_data["prices"]:
        t = p["ticker"]
        if p.get("price") is not None:
            prices_by_ticker[t] = p["price"]

    # normalize sectors
    for e in entities:
        e["sector"] = SECTOR_MAP.get(e.get("sector", ""), e.get("sector", "Other"))

    # filter to entities that have mcap >= minimum threshold, a current price, not excluded/quarantined, and not Token
    eligible = [e for e in entities
                if e["market_cap_usd"] >= MIN_MARKET_CAP
                and e["ticker"] in prices_by_ticker
                and e.get("status") not in ("excluded", "data_quarantine")
                and e.get("sector") != "Token"]

    excluded_micro = [e for e in entities
                      if 0 < e["market_cap_usd"] < MIN_MARKET_CAP and e["ticker"] in prices_by_ticker]

    print(f"  Eligible entities: {len(eligible)} / {len(entities)} (min mcap: ${MIN_MARKET_CAP:,.0f})")
    if excluded_micro:
        print(f"  Excluded (below min mcap): {len(excluded_micro)} entities")
        for e in sorted(excluded_micro, key=lambda x: x['market_cap_usd'], reverse=True)[:5]:
            print(f"    {e['ticker']:12s} ${e['market_cap_usd']:>12,.0f}  {e['name']}")

    # ── compute capped weights ───────────────────────────────────────
    weights = compute_capped_weights(eligible)

    # ── load price history ───────────────────────────────────────────
    price_matrix, ticker_meta, all_dates = load_all_history()

    # Inject current prices from all_prices.json into today's price_matrix
    # This ensures the latest prices are used even if history files haven't
    # been updated yet today (e.g., EODHD end-of-day not yet available)
    if today_str not in price_matrix:
        price_matrix[today_str] = {}
        all_dates.append(today_str)
        all_dates.sort()
    skipped_currency = 0
    for ticker, price in prices_by_ticker.items():
        # Sanity: skip prices that look like non-USD (>$5,000 for a single share is suspicious)
        # Legitimate high-price stocks (ASML ~$1,400, KLAC ~$1,700) are well under this
        if price > 5000:
            skipped_currency += 1
            continue
        price_matrix[today_str][ticker] = price
    injected = len(prices_by_ticker) - skipped_currency
    print(f"  Injected {injected} current prices for {today_str}" +
          (f" (skipped {skipped_currency} non-USD)" if skipped_currency else ""))

    # Determine base date: ~1 year ago (where we have good token coverage)
    # We want the earliest date where at least 50% of eligible entities have data
    min_coverage = len(eligible) * 0.3  # 30% coverage threshold
    base_date_str = all_dates[0] if all_dates else today_str

    if all_dates:
        # Find 1 year ago target
        from datetime import timedelta
        target = (datetime.strptime(today_str, "%Y-%m-%d") - timedelta(days=365)).strftime("%Y-%m-%d")
        # Find the nearest trading day >= target with decent coverage
        for d in all_dates:
            if d >= target:
                day_coverage = sum(1 for t in weights if t in price_matrix.get(d, {}))
                if day_coverage >= min_coverage:
                    base_date_str = d
                    break

    print(f"  Base date: {base_date_str}")

    # ── weights.json ─────────────────────────────────────────────────
    weights_output = {
        "calculated_at": datetime.now(timezone.utc).isoformat() + "Z",
        "cap_limit_pct": CAP_LIMIT * 100,
        "entity_count": len(eligible),
        "weights": sorted(
            [{"ticker": e["ticker"], "name": e["name"], "sector": e["sector"],
              "market_cap_usd": e["market_cap_usd"],
              "weight_pct": round(weights[e["ticker"]] * 100, 4)}
             for e in eligible],
            key=lambda x: x["weight_pct"], reverse=True
        ),
    }
    save_json(WEIGHTS_PATH, weights_output)

    # ── DYNAMIC COMPOSITION: two index series ────────────────────────
    # 1. Full basket (equities + tokens): ~1Y of data
    # 2. Equities only: ~5Y of data (tokens excluded — no long history)
    # The frontend picks the appropriate series based on selected range.

    from datetime import timedelta

    # Split eligible entities into equities and tokens
    equities_only = [e for e in eligible if e["sector"] != "Token"]
    equities_weights = compute_capped_weights(equities_only)

    print(f"  Full basket: {len(eligible)} entities (equities + tokens)")
    print(f"  Equities only: {len(equities_only)} entities")

    # --- Full basket (1Y) base date ---
    full_base_str = all_dates[0] if all_dates else today_str
    if all_dates:
        target_1y = (datetime.strptime(today_str, "%Y-%m-%d") - timedelta(days=365)).strftime("%Y-%m-%d")
        min_coverage_full = len(eligible) * 0.3
        for d in all_dates:
            if d >= target_1y:
                day_cov = sum(1 for t in weights if t in price_matrix.get(d, {}))
                if day_cov >= min_coverage_full:
                    full_base_str = d
                    break

    # --- Equities-only (5Y) base date ---
    eq_base_str = all_dates[0] if all_dates else today_str
    if all_dates:
        target_5y = (datetime.strptime(today_str, "%Y-%m-%d") - timedelta(days=1825)).strftime("%Y-%m-%d")
        min_coverage_eq = len(equities_only) * 0.3
        for d in all_dates:
            if d >= target_5y:
                day_cov = sum(1 for t in equities_weights if t in price_matrix.get(d, {}))
                if day_cov >= min_coverage_eq:
                    eq_base_str = d
                    break

    print(f"  Full basket base date: {full_base_str}")
    print(f"  Equities-only base date: {eq_base_str}")

    # --- Backfill and produce a SINGLE unified series ---
    # Strategy: compute full-basket (equities+tokens) from its start date,
    # compute equities-only from its earlier start date, then splice them
    # into one continuous series. Use the full-basket for all dates where
    # it exists; prepend equities-only history (rescaled) for earlier dates.
    # Normalise the unified series ONCE so 2025-03-31 = 1000.00.
    if all_dates and price_matrix:
        # Full basket series (~1Y)
        composite_series, actual_base_date, base_prices = backfill_index(
            eligible, weights, price_matrix, all_dates, full_base_str
        )
        print(f"  Full basket series: {len(composite_series)} data points")

        # Equities-only series (~5Y)
        eq_series_raw, eq_actual_base, eq_base_prices = backfill_index(
            equities_only, equities_weights, price_matrix, all_dates, eq_base_str
        )
        print(f"  Equities-only series: {len(eq_series_raw)} data points")

        # Splice: use equities-only for dates BEFORE the full basket starts,
        # scaled so the splice point is seamless.
        full_start_date = composite_series[0]["date"] if composite_series else today_str
        full_start_value = composite_series[0]["value"] if composite_series else BASE_VALUE

        # Find equities-only value at the splice date
        eq_at_splice = None
        for pt in eq_series_raw:
            if pt["date"] >= full_start_date:
                eq_at_splice = pt["value"]
                break
        if eq_at_splice and eq_at_splice > 0:
            splice_factor = full_start_value / eq_at_splice
        else:
            splice_factor = 1.0

        # Build unified series: rescaled eq history + full basket
        unified_series = []
        for pt in eq_series_raw:
            if pt["date"] < full_start_date:
                unified_series.append({"date": pt["date"], "value": round(pt["value"] * splice_factor, 2)})
        unified_series.extend(composite_series)

        # Normalise the entire unified series once: value on NORMALISE_DATE = 1000.00
        unified_series, norm_date, norm_factor = normalise_series(unified_series)
        composite_value = unified_series[-1]["value"] if unified_series else BASE_VALUE
        print(f"  Unified series: {len(unified_series)} data points (spliced at {full_start_date})")
        print(f"  Normalised to {BASE_VALUE:.2f} on {norm_date} (factor: {norm_factor:.6f})")

        # For backwards compat, set eq_series = the same unified series
        eq_series = unified_series
        eq_value = composite_value
    else:
        unified_series = [{"date": today_str, "value": BASE_VALUE}]
        composite_series = unified_series
        composite_value = BASE_VALUE
        actual_base_date = today_str
        base_prices = prices_by_ticker
        eq_series = unified_series
        eq_value = BASE_VALUE
        eq_actual_base = today_str
        eq_base_prices = prices_by_ticker

    # ── base_date.json ───────────────────────────────────────────────
    base_data = {
        "base_date": NORMALISE_DATE,
        "base_value": BASE_VALUE,
        "raw_base_date": actual_base_date,
        "normalise_date": NORMALISE_DATE,
        "base_prices": base_prices,
        "base_weights": weights,
        "entity_count": len(eligible),
        "equities_only_base_date": eq_actual_base,
        "equities_only_entity_count": len(equities_only),
    }
    save_json(BASE_DATE_PATH, base_data)

    # ── robotnik_index.json ──────────────────────────────────────────
    # Use the unified series for BOTH the main series and equities_only
    # (they are now identical — one continuous normalised series)
    index_output = {
        "name": "Robotnik Composite Index",
        "base_date": NORMALISE_DATE,
        "base_value": BASE_VALUE,
        "current_value": composite_value,
        "current_date": today_str,
        "entity_count": len(eligible),
        "series": unified_series,
        # equities_only kept for backwards compat — same unified series
        "equities_only": {
            "base_date": NORMALISE_DATE,
            "base_value": BASE_VALUE,
            "current_value": composite_value,
            "entity_count": len(equities_only),
            "series": unified_series,
        },
    }
    save_json(INDEX_PATH, index_output)

    # ── sub-indices (with backfill) ──────────────────────────────────
    sub_sectors = ["Semiconductor", "Robotics", "Space", "Materials", "Token"]
    sub_indices = {}

    for sector in sub_sectors:
        sector_entities = [e for e in eligible if e["sector"] == sector]
        if not sector_entities:
            continue

        sector_weights = compute_capped_weights(sector_entities)

        # Backfill sub-index using the same equities-only approach as the composite
        if all_dates and price_matrix:
            # Use equities-only base date to get 5Y of history
            sub_series_raw, _, _ = backfill_index(
                sector_entities, sector_weights, price_matrix, all_dates, eq_base_str
            )
            # Sanity check: cap any single-day value at 20x the median to catch currency errors
            if sub_series_raw:
                vals = [pt["value"] for pt in sub_series_raw if pt["value"] > 0]
                if vals:
                    median_val = sorted(vals)[len(vals) // 2]
                    cap = median_val * 20
                    for pt in sub_series_raw:
                        if pt["value"] > cap:
                            pt["value"] = cap
            sub_series = sub_series_raw
            # Normalise sub-index to BASE_VALUE on NORMALISE_DATE
            sub_series, sub_norm_date, sub_norm_factor = normalise_series(sub_series)
            sector_value = sub_series[-1]["value"] if sub_series else BASE_VALUE
            print(f"    {sector}: normalised on {sub_norm_date} (factor: {sub_norm_factor:.6f})")
        else:
            sub_series = [{"date": today_str, "value": BASE_VALUE}]
            sector_value = BASE_VALUE

        sub_key = sector.lower().replace("-", "_")
        sub_indices[sub_key] = {
            "name": f"Robotnik {sector} Index",
            "current_value": sector_value,
            "entity_count": len(sector_entities),
            "top_5": sorted(
                [{"ticker": e["ticker"], "name": e["name"],
                  "weight_pct": round(sector_weights[e["ticker"]] * 100, 2)}
                 for e in sector_entities],
                key=lambda x: x["weight_pct"], reverse=True
            )[:5],
            "series": sub_series,
        }

    save_json(SUB_IDX_PATH, sub_indices)

    # ── summary.json ─────────────────────────────────────────────────
    # daily change (compare last 2 entries in series)
    if len(composite_series) >= 2:
        prev_value = composite_series[-2]["value"]
        daily_change_pct = round((composite_value - prev_value) / prev_value * 100, 2) if prev_value else 0
    else:
        daily_change_pct = 0.0

    summary = {
        "calculated_at": datetime.now(timezone.utc).isoformat() + "Z",
        "composite": {
            "name": "Robotnik Composite Index",
            "value": composite_value,
            "daily_change_pct": daily_change_pct,
            "base_date": NORMALISE_DATE,
            "base_value": BASE_VALUE,
            "entities": len(eligible),
        },
        "equities_only": {
            "name": "Robotnik Composite Index (Equities Only)",
            "value": eq_value,
            "base_date": eq_actual_base,
            "base_value": BASE_VALUE,
            "entities": len(equities_only),
        },
        "sub_indices": {
            k: {"name": v["name"], "value": v["current_value"],
                "entities": v["entity_count"]}
            for k, v in sub_indices.items()
        },
        "top_10_weights": weights_output["weights"][:10],
    }
    save_json(SUMMARY_PATH, summary)

    # ── print summary ────────────────────────────────────────────────
    print()
    print(f"  ROBOTNIK COMPOSITE INDEX")
    print(f"    Full basket:    {composite_value:,.2f}  ({len(eligible)} entities, {len(composite_series)} pts, base: {actual_base_date})")
    print(f"    Equities only:  {eq_value:,.2f}  ({len(equities_only)} entities, {len(eq_series)} pts, base: {eq_actual_base})")
    print(f"    Daily change: {daily_change_pct:+.2f}%")
    print()
    for k, v in sub_indices.items():
        print(f"  {v['name']}: {v['current_value']:,.2f} ({v['entity_count']} entities, {len(v['series'])} pts)")
    print()
    print("  Top 5 weights:")
    for w in weights_output["weights"][:5]:
        print(f"    {w['ticker']:8s} {w['weight_pct']:6.2f}%  ({w['name']})")
    print()
    print("Done.")


if __name__ == "__main__":
    main()
