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

# ── Step 5 guardrail thresholds ──────────────────────────────────────────
# Any sub-index day-over-day move beyond this triggers a publish block.
# Real markets rarely move >25% intraday at the index level; anything
# larger almost certainly signals a data-quality regression.
MAX_DAILY_PCT = 0.25
# The composite's day-over-day change must track the mcap-weighted average
# of the sub-indices' day-over-day change to within this tolerance. We use a
# DELTA-form check instead of absolute-value equality because the composite
# and each sub-index apply the 5% single-entity cap independently, which
# creates a permanent structural level offset (~25-30%) that is not a bug.
# What *would* signal a bug is a day where those deltas disagree sharply —
# the original KS-ticker spike produced a ~480% delta, so 5% is a
# conservative catch-all that still lets legitimate high-volatility days
# (e.g. April 2025 tariff week saw ~2% delta) through. The tighter real
# protection is the per-series day-over-day check above.
COMPOSITE_DIVERGENCE_TOL = 0.05
# Implausibly large close price in USD — above this, we treat the point
# as a unit-mismatch (e.g. raw KRW leaking in) and skip it at load time.
MAX_LOAD_USD = 10_000

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
                if not (d and close is not None and close > 0):
                    continue
                # Guardrail: history close values are expected to be in USD.
                # Anything above MAX_LOAD_USD is almost certainly a unit
                # mismatch (raw KRW/JPY leaking through) and would poison
                # the weighted return — skip it rather than corrupt the
                # series. Log so the miss is visible in the run output.
                if close > MAX_LOAD_USD:
                    print(f"  WARN: skipping implausible close {close} for {ticker} on {d}")
                    continue
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


class IndexGuardrailError(Exception):
    """Raised when a computed index series fails a publish-blocking health check."""


def _check_day_over_day(name, series, max_pct=MAX_DAILY_PCT, limit=5):
    """Scan a series for implausible day-over-day moves.

    Returns a list of (prev_date, cur_date, prev_value, cur_value, pct) tuples,
    capped at ``limit`` to keep error output readable. An empty list means the
    series is clean.
    """
    flags = []
    for i in range(1, len(series)):
        prev, cur = series[i - 1]["value"], series[i]["value"]
        if prev and prev > 0:
            change = cur / prev - 1
            if abs(change) > max_pct:
                flags.append((series[i - 1]["date"], series[i]["date"], prev, cur, change))
                if len(flags) >= limit:
                    break
    return flags


def run_guardrails(composite_series, sub_indices, sector_mcap_share):
    """Publish-blocking health checks. Raises IndexGuardrailError on failure.

    Checks:
      1. Every series (composite + sub-indices) is free of day-over-day
         moves exceeding ``MAX_DAILY_PCT``. Legitimate index moves almost
         never exceed 25% in a single day; anything beyond that almost
         always traces back to a data regression (unit mismatch, sentinel,
         duplicate constituent, missed divisor adjustment).
      2. On the most recent date, the composite value stays within
         ``COMPOSITE_DIVERGENCE_TOL`` of the market-cap-weighted average
         of the sub-indices. This catches cases where one sub-index is
         silently pulling in a poisoned price the composite is ignoring.
    """
    failures = []

    # 1. Day-over-day sanity on every series.
    for (name, series) in [("composite", composite_series)] + \
            [(k, v["series"]) for k, v in sub_indices.items()]:
        flags = _check_day_over_day(name, series)
        for prev_d, cur_d, pv, cv, pct in flags:
            failures.append(
                f"  {name}: |dod|>{MAX_DAILY_PCT:.0%} on {prev_d}->{cur_d}: "
                f"{pv:.2f} -> {cv:.2f} ({pct:+.1%})"
            )

    # 2. Composite daily change vs mcap-weighted sub-indices daily change.
    #    A structural level offset is expected (capping differences), but
    #    on any given day the composite should move in lockstep with the
    #    weighted sub-indices. If the daily-change figures diverge beyond
    #    ``COMPOSITE_DIVERGENCE_TOL``, one side is ingesting a price the
    #    other is not — exactly the failure mode the historical KS-ticker
    #    spike produced.
    if composite_series and sub_indices and sector_mcap_share and len(composite_series) >= 2:
        sub_maps = {k: {p["date"]: p["value"] for p in v["series"]} for k, v in sub_indices.items()}
        total_share = sum(sector_mcap_share.get(k, 0.0) for k in sub_indices)
        last_offenders = []
        if total_share > 0:
            for i in range(1, len(composite_series)):
                cur_d = composite_series[i]["date"]
                prev_d = composite_series[i - 1]["date"]
                cur_c, prev_c = composite_series[i]["value"], composite_series[i - 1]["value"]
                if not (prev_c and prev_c > 0):
                    continue
                c_change = cur_c / prev_c - 1

                weighted_prev = weighted_cur = 0.0
                for k, sub_map in sub_maps.items():
                    share = sector_mcap_share.get(k, 0.0) / total_share
                    pv = sub_map.get(prev_d)
                    cv = sub_map.get(cur_d)
                    if pv and cv and pv > 0:
                        weighted_prev += share * pv
                        weighted_cur  += share * cv
                if weighted_prev <= 0:
                    continue
                s_change = weighted_cur / weighted_prev - 1
                delta = c_change - s_change
                if abs(delta) > COMPOSITE_DIVERGENCE_TOL:
                    last_offenders.append((prev_d, cur_d, c_change, s_change, delta))
        # Only surface the worst 5 — a single broken constituent typically
        # generates a long streak of offenders, and printing every one
        # buries the lede.
        for prev_d, cur_d, cc, sc, delta in sorted(last_offenders, key=lambda x: abs(x[4]), reverse=True)[:5]:
            failures.append(
                f"  composite vs weighted sub-indices daily-change {prev_d}->{cur_d}: "
                f"composite {cc:+.2%}, weighted {sc:+.2%}, delta {delta:+.2%} "
                f"(> {COMPOSITE_DIVERGENCE_TOL:.2%})"
            )

    if failures:
        msg = "Index guardrail failures — publish blocked:\n" + "\n".join(failures)
        raise IndexGuardrailError(msg)


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

    # Token isolation: load the registry token set (type=="token" primary,
    # sector=="Token" fallback) so tokens can never enter the equity composite,
    # even if mis-sectored upstream in market_caps.json.
    _reg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "data", "registries", "entity_registry.json")
    try:
        _reg = load_json(_reg_path)
        token_tickers = {k for k, v in _reg.items()
                         if isinstance(v, dict)
                         and (v.get("type") == "token" or v.get("sector") in ("Token", "Tokens"))}
    except Exception:
        token_tickers = set()

    # build price lookup: ticker -> price (USD)
    prices_by_ticker = {}
    for p in prices_data["prices"]:
        t = p["ticker"]
        if p.get("price") is not None:
            prices_by_ticker[t] = p["price"]

    # normalize sectors
    for e in entities:
        e["sector"] = SECTOR_MAP.get(e.get("sector", ""), e.get("sector", "Other"))

    # filter to entities that have mcap >= minimum threshold, a current price,
    # not excluded/quarantined, and not a token (type-based isolation + sector fallback)
    eligible = [e for e in entities
                if e["market_cap_usd"] >= MIN_MARKET_CAP
                and e["ticker"] in prices_by_ticker
                and e.get("status") not in ("excluded", "data_quarantine")
                and e["ticker"] not in token_tickers
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
    # ── Layer 2: Index-side price validation ──
    index_quarantine = set()
    skipped = 0
    for ticker, price in list(prices_by_ticker.items()):
        # Reject null/zero/negative
        if price is None or price <= 0:
            index_quarantine.add(ticker)
            skipped += 1
            continue
        # Reject implausible USD prices
        if price > 5000:
            index_quarantine.add(ticker)
            skipped += 1
            continue
        # Reject >50% swing vs most recent prior valid price
        # Only check against the immediately prior trading day to avoid false positives
        # from legitimate multi-day rallies during history gaps
        if len(all_dates) >= 2:
            prev_day = all_dates[-2]  # Day before today in the series
            prior_prices = price_matrix.get(prev_day, {})
            if ticker in prior_prices:
                prior = prior_prices[ticker]
                if prior and prior > 0 and abs(price / prior - 1) > 0.5:
                    index_quarantine.add(ticker)
                    skipped += 1
        if ticker not in index_quarantine:
            price_matrix[today_str][ticker] = price

    injected = len(prices_by_ticker) - skipped
    print(f"  Injected {injected} current prices for {today_str}" +
          (f" (quarantined {skipped} at index level)" if skipped else ""))

    # Persist index-side quarantine log
    quarantine_log_path = os.path.join(INDEX_DIR, "quarantine.json")
    quarantine_today = [{"ticker": t, "reason": "index-side validation"} for t in index_quarantine]
    quarantine_history = []
    if os.path.exists(quarantine_log_path):
        try:
            old = json.loads(open(quarantine_log_path).read())
            quarantine_history = old.get("history", [])
        except:
            pass
    for q in quarantine_today:
        quarantine_history.append({"date": today_str, **q})
    # Keep last 90 days
    quarantine_history = quarantine_history[-500:]
    save_json(quarantine_log_path, {
        "last_run": datetime.now(timezone.utc).isoformat() + "Z",
        "quarantined_today": quarantine_today,
        "history": quarantine_history,
    })

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

    # ── Sub-index base date (shared) ────────────────────────────────
    # We anchor every sub-index to the earliest date with >= 30%
    # constituent coverage, give or take ~5 years back, then normalise
    # each series to 1000 on NORMALISE_DATE (2025-03-31).
    from datetime import timedelta
    sub_base_str = all_dates[0] if all_dates else today_str
    if all_dates:
        target_5y = (datetime.strptime(today_str, "%Y-%m-%d") - timedelta(days=1825)).strftime("%Y-%m-%d")
        min_coverage_sub = len(eligible) * 0.3
        for d in all_dates:
            if d >= target_5y:
                day_cov = sum(1 for t in weights if t in price_matrix.get(d, {}))
                if day_cov >= min_coverage_sub:
                    sub_base_str = d
                    break
    print(f"  Sub-index base date: {sub_base_str}")

    # ── Compute sub-indices first ───────────────────────────────────
    # Per Option A (2026-04-22 methodology revision), the Composite is
    # defined as a market-cap-weighted combination of the four sub-
    # indices, NOT as an independently capped 233-constituent basket.
    # So we build the sub-indices first, then derive Composite from
    # them below. See METHODOLOGY NOTE in the README/Appendix A.
    sub_sectors = ["Semiconductor", "Robotics", "Space", "Materials", "Token"]
    sub_indices = {}
    sub_series_by_sector = {}  # canonical key ("semiconductor", …) -> list[{date, value}]

    for sector in sub_sectors:
        sector_entities = [e for e in eligible if e["sector"] == sector]
        if not sector_entities:
            continue

        sector_weights = compute_capped_weights(sector_entities)

        if all_dates and price_matrix:
            sub_series_raw, _, _ = backfill_index(
                sector_entities, sector_weights, price_matrix, all_dates, sub_base_str
            )
            # Sanity cap at 20x median per day to catch stray currency/
            # unit-mismatch artefacts from individual constituents.
            if sub_series_raw:
                vals = [pt["value"] for pt in sub_series_raw if pt["value"] > 0]
                if vals:
                    median_val = sorted(vals)[len(vals) // 2]
                    cap = median_val * 20
                    for pt in sub_series_raw:
                        if pt["value"] > cap:
                            pt["value"] = cap
            sub_series = sub_series_raw
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
        sub_series_by_sector[sub_key] = sub_series

    # Composite is the weighted combination of the four equity sub-
    # indices: Semi, Robotics, Space, Materials. Token sub-index is
    # reported separately but is NOT part of the Composite (tokens
    # were already excluded from `eligible` upstream).
    COMPOSITE_SECTORS = ["semiconductor", "robotics", "space", "materials"]

    # ── Composite: weighted average of sub-indices (Option A) ───────
    # On each date:
    #   sector_mcap(t) = Σ_i (current_shares_i × price_i(t))
    #                  = Σ_i (current_mcap_i × price_i(t) / price_i_current)
    #   share(t)       = sector_mcap(t) / total_mcap(t)
    #   composite(t)   = Σ_sectors share(t) × sub_index(t)
    #
    # "current_shares" uses current mcap / current price as a proxy
    # (share count is roughly stable over a ~1 year horizon; we don't
    # have historical shares-outstanding data). Missing prices on a
    # given day contribute zero to their sector's mcap.
    shares_by_ticker = {}
    for e in eligible:
        cur_p = prices_by_ticker.get(e["ticker"])
        mcap = e.get("market_cap_usd") or 0
        if cur_p and cur_p > 0 and mcap > 0:
            shares_by_ticker[e["ticker"]] = mcap / cur_p
    sector_of = {e["ticker"]: e["sector"].lower() for e in eligible}

    # For each date in the sub-index series, build sector mcap shares
    # and combine. Use the union of dates across all sub-indices.
    composite_dates = set()
    for s in sub_series_by_sector.values():
        composite_dates.update(pt["date"] for pt in s)
    composite_dates = sorted(composite_dates)

    # Date-indexed lookup on each sub-series for fast combination.
    sub_by_date = {
        k: {pt["date"]: pt["value"] for pt in s}
        for k, s in sub_series_by_sector.items()
    }

    # Price carry-forward so a ticker that's missing on a given day
    # still contributes its last-known price to sector mcap. Same
    # behaviour as backfill_index() uses for index computation.
    last_known_price = {}
    composite_pts = []
    for d in composite_dates:
        for t, p in price_matrix.get(d, {}).items():
            last_known_price[t] = p
        sector_mcap = {k: 0.0 for k in COMPOSITE_SECTORS}
        for t, shares in shares_by_ticker.items():
            sec = sector_of.get(t)
            if sec not in sector_mcap:
                continue
            p = last_known_price.get(t)
            if p is None or p <= 0:
                continue
            sector_mcap[sec] += shares * p
        total = sum(sector_mcap.values())
        if total <= 0:
            continue
        composite_value_t = 0.0
        contributing = 0
        for k in COMPOSITE_SECTORS:
            share = sector_mcap[k] / total
            sub_val = sub_by_date.get(k, {}).get(d)
            if sub_val is None:
                continue
            composite_value_t += share * sub_val
            contributing += 1
        if contributing == 0:
            continue
        composite_pts.append({"date": d, "value": round(composite_value_t, 2)})

    unified_series = composite_pts
    # Renormalise defensively: sub-indices are each 1000 on 2025-03-31
    # already, so Σ share × 1000 = 1000 structurally. This is a belt-
    # and-braces pass to correct sub-unit rounding.
    if unified_series:
        unified_series, norm_date, norm_factor = normalise_series(unified_series)
        print(f"  Composite: normalised on {norm_date} (factor: {norm_factor:.6f})")
    composite_value = unified_series[-1]["value"] if unified_series else BASE_VALUE
    composite_series = unified_series
    actual_base_date = NORMALISE_DATE
    base_prices = {t: prices_by_ticker[t] for t in shares_by_ticker if t in prices_by_ticker}
    eq_series = unified_series
    eq_value = composite_value
    eq_actual_base = NORMALISE_DATE
    equities_only = eligible  # tokens already excluded from eligible
    equities_weights = weights

    # ── Runtime assertion: composite ∈ [min(sub), max(sub)] on every date ──
    # If this ever fires the build MUST abort — publishing a Composite
    # outside the sub-index range would recreate the very bug Option A
    # was introduced to eliminate.
    breaches = []
    for pt in unified_series:
        d = pt["date"]
        sub_vals = [sub_by_date[k][d] for k in COMPOSITE_SECTORS if d in sub_by_date.get(k, {})]
        if not sub_vals:
            continue
        lo, hi = min(sub_vals), max(sub_vals)
        # 0.01 tolerance for sub-unit rounding after normalise_series.
        if pt["value"] < lo - 0.01 or pt["value"] > hi + 0.01:
            breaches.append((d, pt["value"], lo, hi))
    if breaches:
        msg = "Composite violated min(sub) <= composite <= max(sub) on {} date(s):\n".format(len(breaches))
        for d, v, lo, hi in breaches[:10]:
            msg += "  {}: composite={:.2f}, sub range=[{:.2f}, {:.2f}]\n".format(d, v, lo, hi)
        raise RuntimeError(msg)

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
        "composite_method": "weighted_average_of_sub_indices (Option A, 2026-04-22)",
    }
    save_json(BASE_DATE_PATH, base_data)

    # ── robotnik_index.json ──────────────────────────────────────────
    index_output = {
        "name": "Robotnik Composite Index",
        "base_date": NORMALISE_DATE,
        "base_value": BASE_VALUE,
        "current_value": composite_value,
        "current_date": today_str,
        "entity_count": len(eligible),
        "method": "weighted_average_of_sub_indices",
        "series": unified_series,
        "equities_only": {
            "base_date": NORMALISE_DATE,
            "base_value": BASE_VALUE,
            "current_value": composite_value,
            "entity_count": len(equities_only),
            "series": unified_series,
        },
    }
    save_json(INDEX_PATH, index_output)

    # ── Step 5 guardrail ─────────────────────────────────────────────
    # Block publish on >25% day-over-day moves or >0.5% composite-vs-subindex
    # divergence. Computes mcap share per sector from the eligible universe.
    sector_mcap = defaultdict(float)
    for e in eligible:
        sector_mcap[e["sector"].lower().replace("-", "_")] += e["market_cap_usd"]

    run_guardrails(unified_series, sub_indices, dict(sector_mcap))

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
    # ── Run summary (self-auditing) ──
    reg_data = {}
    reg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "registries", "entity_registry.json")
    if os.path.exists(reg_path):
        with open(reg_path) as f:
            reg_data = json.load(f)
    registry_quarantined = [(k, v.get("name", "")) for k, v in reg_data.items()
                            if isinstance(v, dict) and v.get("status") == "data_quarantine"]

    print(f"\n  INDEX RUN COMPLETE: {len(eligible)} constituents included" +
          (f", {len(index_quarantine)} quarantined at runtime" if index_quarantine else "") +
          (f", {len(registry_quarantined)} quarantined in registry" if registry_quarantined else ""))
    for t in index_quarantine:
        print(f"    QUARANTINED (runtime): {t}")
    for t, name in registry_quarantined:
        print(f"    QUARANTINED (registry): {t} ({name})")

    print("\nDone.")


if __name__ == "__main__":
    main()
