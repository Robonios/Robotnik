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


# Bankruptcy / wipeout reorgs: {ticker: effective_date}. The old equity is
# cancelled to ~0 and a NEW equity issued at a fresh basis on this date — so the
# return across it is NOT zero (as a reverse-split is); it is a -100% wipeout of
# the old equity, then a fresh re-entry of the new instrument. Curated from real
# corporate events (anti-fabrication), distinct from the reverse-splits the CA
# guard neutralises to flat.
REORG_EVENTS = {
    "WOLF": "2025-09-29",   # Wolfspeed — Chapter 11 emergence; old ~$1.21 -> new ~$22
}


def backfill_index_chained(sector_entities, weights, price_matrix, all_dates):
    """Chain-linked daily-return sub-index (enter-at-first-price).

    index(d) = index(d-1) x [ Σ_i w_i·(p_i(d)/p_i(d-1)) / Σ_i w_i ], over
    constituents live on BOTH d-1 and d. A constituent that gets its first
    real price on day T joins last_known on T but is absent from the T-1
    snapshot, so it contributes NO return on its entry day (return ≡ 1.0, no
    dilution jump) and only its subsequent moves count. This is the only
    construction that admits post-base IPOs (R1 — Rocket Lab, Planet, …)
    without a fake entry-day step. Carry-forward: a missing day yields ratio
    1.0; a resume-after-gap attributes the gap move to the resume day (caught
    by the dod guardrail if implausible). Returns an UN-normalised series
    (caller normalises to 1000 on NORMALISE_DATE).
    """
    tickers = [e["ticker"] for e in sector_entities]
    wt = {t: weights.get(t, 0.0) for t in tickers}
    last_known, prev_known = {}, {}
    series = []
    idx = 1.0
    for k, d in enumerate(all_dates):
        day = price_matrix.get(d, {})
        for t in tickers:
            p = day.get(t)
            if p is not None and p > 0:
                last_known[t] = p
        if k == 0:
            series.append({"date": d, "value": round(idx, 2)})
            prev_known = dict(last_known)
            continue
        num = den = 0.0
        for t in tickers:
            w = wt[t]
            if w <= 0:
                continue
            pp, pc = prev_known.get(t), last_known.get(t)
            if pp is not None and pc is not None and pp > 0:
                r = pc / pp
                if REORG_EVENTS.get(t) == d:
                    # Bankruptcy/wipeout reorg: old equity -> ~0 (holders wiped),
                    # new equity issued at a fresh basis. Realize the -100%
                    # wipeout HERE (NOT flat — flat would hide the old-holder
                    # loss); the new instrument re-enters next day at its first
                    # price (prev_known resets to it automatically). The pre-reorg
                    # decline is already captured in the price history.
                    print("    [chain-link REORG] {} {}: old equity -> 0 "
                          "(-100% wipeout realized), new equity re-enters".format(t, d))
                    r = 0.0
                elif r > 5.0 or r < 0.2:
                    # Reverse-split / bad print: a share-count change preserves
                    # holder value, so neutralise to flat 1.0 (index continuous
                    # across the split). e.g. Ouster 1:10, Momentus 1:50,
                    # BlackSky 1:9. Chain-linking would otherwise compound the
                    # split ratio into every later point. Logged, not masked.
                    print("    [chain-link CA] {} {}: ratio {:.2f} neutralised "
                          "(reverse-split / bad print -> flat)".format(t, d, r))
                    r = 1.0
                num += w * r
                den += w
        idx *= (num / den) if den > 0 else 1.0
        series.append({"date": d, "value": round(idx, 2)})
        prev_known = dict(last_known)
    return series


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

    # 3. Degenerate / frozen sub-index guard. A real sub-index never holds a
    #    single value across a long series. A frozen sub-index means every
    #    constituent silently dropped out of the weighted return — the exact
    #    signature of the 2026-05 frozen-Semi regression, where the historical
    #    base date landed on a US market holiday (Memorial Day 2021-05-31) and
    #    every US-listed semiconductor name had no base price, pinning the whole
    #    sub-index at its 1000 base and dragging the composite ~30% low. This is
    #    NOT caught by the day-over-day or composite-divergence checks (a frozen
    #    series is perfectly smooth and moves in lockstep), so it gets its own
    #    publish-blocking guard. distinct<=1 over a long series == collapsed.
    for name, v in (sub_indices or {}).items():
        s = v.get("series", [])
        if len(s) >= 20:
            distinct = len({round(p["value"], 4) for p in s})
            if distinct <= 1:
                failures.append(
                    f"  {name}: FROZEN sub-index — {len(s)} points but only "
                    f"{distinct} distinct value(s). Every constituent lost its "
                    f"base price (base-date on a non-trading day? exact-base "
                    f"exclusion?). Composite would silently mis-scale."
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

    # Find the value on target_date, else the nearest trading day strictly
    # AFTER it, else (target beyond the series) the last point.
    #
    # R3 fix: the previous loop fell through to the LAST value whenever
    # target_date was missing-but-in-range (the `raw_value is None` guard only
    # held on the first iteration, so the >target branch never fired), which
    # would silently rescale the ENTIRE series by the wrong factor — a
    # whole-period multiplicative error. It was harmless only because
    # 2025-03-31 is actually present at 98% coverage; this makes the fallback
    # correct rather than relying on that.
    exact = next((pt for pt in series if pt["date"] == target_date), None)
    if exact is not None:
        raw_value, actual_date = exact["value"], target_date
    else:
        after = next((pt for pt in series if pt["date"] > target_date), None)
        chosen = after if after is not None else series[-1]
        raw_value, actual_date = chosen["value"], chosen["date"]

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
        # Membership: the index MUST honor registry status — same gate as
        # calculate_bottleneck_composite.py ("parity is essential"). Reading
        # status off market_caps (always null) silently admitted ~40% of weight
        # in deliberately-excluded names (GOOG/AMZN/TSLA/etc.). Registry is the
        # single source of truth for membership.
        registry_excluded = {k for k, v in _reg.items()
                             if isinstance(v, dict)
                             and v.get("status") in ("excluded", "data_quarantine")}
        # Lifecycle (Workstream C): the registry key is the immutable entity_id; the
        # trading symbol is the public_ticker FIELD. Resolve a market_caps ticker ->
        # entity_id via public_ticker (identity for native-public names). Only
        # lifecycle_status=="public" entities are index-eligible; private / pre_ipo_* /
        # delisted / acquired / withdrawn are excluded by status, the same as tokens.
        _pubtkr2eid = {v.get("public_ticker"): k for k, v in _reg.items()
                       if isinstance(v, dict) and v.get("public_ticker")}
        _lifecycle = {k: v.get("lifecycle_status") for k, v in _reg.items()
                      if isinstance(v, dict)}
    except Exception:
        token_tickers = set()
        registry_excluded = set()
        _pubtkr2eid = {}
        _lifecycle = {}

    def _eid(tkr):
        """market_caps / price ticker -> registry entity_id (identity for native-public)."""
        return _pubtkr2eid.get(tkr, tkr)

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
                and _eid(e["ticker"]) not in registry_excluded   # registry = source of truth
                and e.get("status") not in ("excluded", "data_quarantine")
                and _eid(e["ticker"]) not in token_tickers
                and e.get("sector") != "Token"
                and _lifecycle.get(_eid(e["ticker"])) == "public"]   # lifecycle gate (C)

    # ── Parity guard (publish-blocking) ──────────────────────────────
    # The index universe MUST equal the bottleneck-composite universe (both
    # gate on registry exclusions + tokens). If any registry-excluded name
    # leaks into eligible, the membership invariant is broken — abort rather
    # than publish a Big-Tech-contaminated index again.
    _leak = registry_excluded & {e["ticker"] for e in eligible}
    if _leak:
        raise IndexGuardrailError(
            "Membership parity violation — {} registry-excluded name(s) leaked "
            "into the index universe: {}".format(len(_leak), sorted(_leak)[:20]))

    # ── Reverse-parity guard (publish-blocking) ──────────────────────
    # The forward guard (above) catches registry-EXCLUDED names leaking INTO the
    # index. This catches the OPPOSITE direction — the failure mode that hid the
    # B-sweep's silent 13-name gap: a non-excluded FRONTIER name MISSING from the
    # index (added to the registry but lacking a market cap → no weight → dropped,
    # with nothing to flag it). Every non-excluded public name must be IN the index
    # OR acknowledged in index_membership_exceptions.json (secondary listings,
    # genuine unrecoverable data gaps). Makes missing-names structurally visible.
    try:
        _rev_reg = load_json(_reg_path)
    except Exception:
        _rev_reg = {}
    _exc_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "data", "registries", "index_membership_exceptions.json")
    try:
        _documented = set((load_json(_exc_path).get("exceptions") or {}).keys())
    except Exception:
        _documented = set()
    _non_excl_public = {k for k, v in _rev_reg.items() if isinstance(v, dict)
                        and v.get("lifecycle_status") == "public"
                        and v.get("status") not in ("excluded", "data_quarantine")}
    _elig_eids = {_eid(e["ticker"]) for e in eligible}
    _missing = _non_excl_public - _elig_eids - _documented
    if _missing:
        raise IndexGuardrailError(
            "Reverse-parity violation — {} non-excluded frontier name(s) MISSING from "
            "the index (no market cap / no weight). Backfill the cap (scripts/"
            "backfill_market_caps.py) or fix membership, or document the reason in "
            "data/registries/index_membership_exceptions.json: {}".format(
                len(_missing), sorted(_missing)[:20]))

    # ── Lifecycle-parity guard (publish-blocking, Workstream C) ───────
    # Only lifecycle_status=="public" entities may be in the index; private /
    # pre_ipo_* / delisted / acquired / withdrawn are index-excluded by status
    # (the same gate as excluded/token). And no entity_id may appear in BOTH the
    # active-private set and the public index — no double-count across the
    # private→public boundary. Both are structural under the single-row immutable-
    # entity_id model; asserted here so a future scan bug can't silently break it.
    _nonpublic_in_index = {eid for eid in _elig_eids if _lifecycle.get(eid) != "public"}
    if _nonpublic_in_index:
        raise IndexGuardrailError(
            "Lifecycle violation — {} non-public entity(ies) in the index: {}".format(
                len(_nonpublic_in_index), sorted(_nonpublic_in_index)[:20]))
    _active_private = {k for k, v in _rev_reg.items() if isinstance(v, dict)
                       and v.get("lifecycle_status") in ("private", "pre_ipo_filed", "pre_ipo_priced")}
    _double = _active_private & _elig_eids
    if _double:
        raise IndexGuardrailError(
            "Double-count violation — {} entity_id(s) in BOTH the active-private set and the "
            "public index: {}".format(len(_double), sorted(_double)[:20]))

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

    # ── Restrict the date axis to genuine TRADING days ────────────────
    # Token history is 7-day (crypto) and deep international history trades
    # on US market holidays — both inject dates on which the US-anchored
    # equity universe does NOT broadly trade. Left unfiltered these (a)
    # create flat phantom points every weekend and (b) pull the auto-
    # selected base date onto a US holiday (e.g. Memorial Day 2021-05-31,
    # 34% coverage) where every US-listed constituent has no bar — which
    # silently pinned the entire Semiconductor sub-index to its 1000 base.
    # A date is retained only when a quorum of eligible constituents
    # actually traded. The 50% line sits in the wide empty gap between
    # holiday sessions (≤35%, international-only) and real sessions (≥79%).
    _elig_set = {e["ticker"] for e in eligible}
    TRADING_COVERAGE = 0.50
    _need = max(1, int(len(eligible) * TRADING_COVERAGE))
    _trading = [d for d in all_dates
                if sum(1 for t in _elig_set if t in price_matrix.get(d, {})) >= _need]
    _dropped = len(all_dates) - len(_trading)
    if _trading:
        print(f"  Trading-day filter: kept {len(_trading)}/{len(all_dates)} dates "
              f"(dropped {_dropped} non-trading days <{TRADING_COVERAGE:.0%} eligible coverage)")
        all_dates = _trading

    # ── Determine the latest genuine TRADING date from the snapshot ───
    # The index must never move on a non-trading day (weekend or global
    # holiday). The wall-clock "today" is irrelevant — what governs is the
    # most recent date on which a QUORUM of index constituents actually
    # have a fresh price. On a Saturday the snapshot still carries Friday's
    # bars, so the latest trading date resolves to Friday and no synthetic
    # point is created. A thin lone session (e.g. a couple of Sunday-only
    # TASE listings) fails the quorum and is likewise ignored — the
    # composite only steps forward when the broad market actually traded.
    from collections import Counter as _Counter
    _eligible_tickers = {e["ticker"] for e in eligible}
    _date_counts = _Counter(
        str(p.get("date"))[:10] for p in prices_data["prices"]
        if p.get("price") is not None and p.get("date")
        and str(p.get("date"))[:10] <= today_str
        and p.get("ticker") in _eligible_tickers
    )
    TRADING_DAY_QUORUM = max(10, int(len(eligible) * 0.05))
    _trading_dates = sorted(d for d, c in _date_counts.items()
                            if c >= TRADING_DAY_QUORUM)
    data_date = _trading_dates[-1] if _trading_dates else None
    last_hist_date = all_dates[-1] if all_dates else None

    # Inject a fresh point ONLY when the snapshot is genuinely ahead of the
    # on-disk history (e.g. EOD history not yet refreshed for the latest
    # session). When history already covers the latest trading date — which
    # includes every weekend, where data_date stays pinned to Friday — we
    # trust the split/FX-adjusted EOD history and add nothing. This is the
    # "drop non-trading days" standard applied at the injection boundary.
    inject_date = None
    if data_date and (last_hist_date is None or data_date > last_hist_date):
        inject_date = data_date
        if inject_date not in price_matrix:
            price_matrix[inject_date] = {}
            all_dates.append(inject_date)
            all_dates.sort()

    # ── Layer 2: Index-side price validation (only when injecting) ────
    index_quarantine = set()
    skipped = 0
    if inject_date:
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
            # Reject >50% swing vs most recent prior valid price. Only check
            # against the immediately prior trading day to avoid false
            # positives from legitimate multi-day rallies during history gaps.
            if len(all_dates) >= 2:
                prev_day = all_dates[-2]  # Day before inject_date in the series
                prior_prices = price_matrix.get(prev_day, {})
                if ticker in prior_prices:
                    prior = prior_prices[ticker]
                    if prior and prior > 0 and abs(price / prior - 1) > 0.5:
                        index_quarantine.add(ticker)
                        skipped += 1
            if ticker not in index_quarantine:
                price_matrix[inject_date][ticker] = price

    injected = (len(prices_by_ticker) - skipped) if inject_date else 0
    if inject_date:
        print(f"  Injected {injected} current prices for {inject_date}" +
              (f" (quarantined {skipped} at index level)" if skipped else ""))
    else:
        print(f"  No injection: history current through {last_hist_date}; "
              f"latest snapshot trading day {data_date} already covered — "
              f"non-trading day '{today_str}' NOT added (drop-non-trading-days)")

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
            # Chain-linked daily-return sub-index — admits R1 post-base IPOs via
            # enter-at-first-price (see backfill_index_chained). The 20x-median
            # cap is intentionally dropped: it clips individual points, but a
            # compounded series carries a spike forward into every later point,
            # so mid-series clipping distorts the level. The dod guardrail blocks
            # a genuine daily spike at its source instead.
            sub_series_raw = backfill_index_chained(
                sector_entities, sector_weights, price_matrix, all_dates
            )
            # Emit only from the robust-coverage base date. The chain warms up
            # (carry-forward + compounding) over the earliest ~20 dates, but the
            # thinnest pre-quorum days — where the composite's share weighting
            # and the sub-index daily-change legitimately diverge on near-empty
            # coverage — are not published. Normalised values for every retained
            # date are identical (anchor = 2025-03-31), so this only trims the
            # thin head, exactly as the prior fixed-base method did.
            sub_series_raw = [pt for pt in sub_series_raw if pt["date"] >= sub_base_str]
            sub_series, sub_norm_date, sub_norm_factor = normalise_series(sub_series_raw)
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
    # current_date is the date of the LATEST actual point in the series — a
    # real trading day — never the wall-clock "today". On a weekend this is
    # the prior Friday's close; the headline must not advance to a date the
    # market never traded.
    current_date = unified_series[-1]["date"] if unified_series else today_str
    index_output = {
        "name": "Robotnik Composite Index",
        "base_date": NORMALISE_DATE,
        "base_value": BASE_VALUE,
        "current_value": composite_value,
        "current_date": current_date,
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
