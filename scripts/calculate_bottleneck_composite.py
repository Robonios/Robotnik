#!/usr/bin/env python3
"""
Robotnik Bottleneck-Weighted Composite (v1.0 — Preliminary)
============================================================
A market-cap × bottleneck-multiplier weighted composite of public equities.
Pattern A multiplicative tilt:

    raw_weight_i = market_cap_i × multiplier(bottleneck_i)
    weight_i     = raw_weight_i / Σ raw_weight  (then 5% cap, redistributed)

Multipliers (v1.0 — analytical choice, NOT empirically derived):
    CRITICAL  4.0   sole-source, no viable substitute
    HIGH      2.5   costly substitute, multi-quarter switch
    MEDIUM    1.5   imperfect substitute, viable workaround
    LOW       1.0   commoditised, fungible
    UNRATED   1.0   no amplification (conservative default — 246 of 304)

5% cap is retained for parity with the mcap-weighted Composite (otherwise the
largest amplified mega-cap, e.g. NVDA × 2.5, would dominate the series and
drown out the broader bottleneck signal). The dampening this introduces is
disclosed in the methodology doc — see metrics_methodology.md.

⚠ HONESTY CAVEAT — directional signal only, not headline-publishable:
   Only 58 of 304 equities (~19%) carry a bottleneck rating, so this index
   reads as the rated-subset's concentration, NOT the universe's. It graduates
   to a headline metric only once rating coverage exceeds 80%.

Inputs:
    data/index/market_caps.json          — USD market caps
    data/prices/all_prices.json          — current quotes
    data/prices/history/*.json           — 5Y daily history
    data/markets/enrichment_data.json    — bottleneck ratings (rated subset)
    data/registries/entity_registry.json — excluded-status tags
    data/index/robotnik_index.json       — mcap-weighted Composite (for divergence)

Outputs:
    data/index/bottleneck_weighted_composite.json
    data/index/bottleneck_composite_divergence.log
    data/index/bottleneck_weighted_methodology.md  — version log appended here

Usage:
    python scripts/calculate_bottleneck_composite.py
"""

import json
import math
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX_DIR    = ROOT / "data" / "index"
HISTORY_DIR  = ROOT / "data" / "prices" / "history"
PRICES_PATH  = ROOT / "data" / "prices" / "all_prices.json"
MCAP_PATH    = INDEX_DIR / "market_caps.json"
ENRICHMENT_PATH = ROOT / "data" / "markets" / "enrichment_data.json"
REGISTRY_PATH   = ROOT / "data" / "registries" / "entity_registry.json"
COMPOSITE_PATH  = INDEX_DIR / "robotnik_index.json"

OUT_PATH        = INDEX_DIR / "bottleneck_weighted_composite.json"
OUT_DIVERGENCE  = INDEX_DIR / "bottleneck_composite_divergence.log"

BASE_VALUE      = 1000.0
NORMALISE_DATE  = "2025-03-31"
CAP_LIMIT       = 0.05
MIN_MARKET_CAP  = 10_000_000
MAX_LOAD_USD    = 10_000  # discard implausible KRW/JPY leakage at load time

BOTTLENECK_MULTIPLIERS = {
    "CRITICAL": 4.0,
    "HIGH":     2.5,
    "MEDIUM":   1.5,
    "LOW":      1.0,
    None:       1.0,  # unrated default — conservative no-tilt
}

# Divergence flag threshold: monthly average gap (bw - mcap) / mcap × 100
# beyond this magnitude is surfaced in the log. The 5% threshold mirrors the
# existing Composite-vs-subindices divergence guardrail in calculate_index.py.
DIVERGENCE_FLAG_PCT = 5.0

SECTOR_MAP = {
    "Semiconductor":      "Semiconductor",
    "Semiconductors":     "Semiconductor",
    "Cross-stack":        "Semiconductor",
    "Cross-Stack":        "Semiconductor",
    "Robotics":           "Robotics",
    "Space":              "Space",
    "Materials":          "Materials",
    "Materials & Inputs": "Materials",
    "Token":              "Token",
    "Tokens":             "Token",
}


def load_json(path):
    with open(path) as f:
        return json.load(f)


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def compute_capped_weights(raw_weights, cap=CAP_LIMIT):
    """Iterative 5% cap with proportional excess redistribution.

    Pattern lifted verbatim from calculate_index.py so the cap behaviour is
    identical to the mcap-weighted Composite — divergence then reflects only
    the bottleneck tilt, not different cap algorithms.
    """
    total = sum(raw_weights.values())
    if total <= 0:
        return {t: 0.0 for t in raw_weights}
    weights = {t: w / total for t, w in raw_weights.items()}
    for _ in range(50):
        capped = {t: w for t, w in weights.items() if w > cap}
        if not capped:
            break
        excess = sum(w - cap for w in capped.values())
        uncapped = {t: w for t, w in weights.items() if w <= cap}
        uc_total = sum(uncapped.values())
        if uc_total == 0:
            break
        for t in capped:
            weights[t] = cap
        for t in uncapped:
            weights[t] += excess * (uncapped[t] / uc_total)
    return weights


def load_all_history():
    price_matrix = defaultdict(dict)
    ticker_meta = {}
    files = list(HISTORY_DIR.glob("*.json"))
    print("  Loading {} history files…".format(len(files)))
    for f in files:
        try:
            data = json.loads(f.read_text())
            ticker = data.get("ticker", f.stem)
            ticker_meta[ticker] = {
                "name": data.get("name", ticker),
                "sector": SECTOR_MAP.get(data.get("sector", ""), data.get("sector", "Other")),
            }
            for pt in data.get("series", []):
                d = pt.get("date")
                c = pt.get("close")
                if not (d and c is not None and c > 0):
                    continue
                if c > MAX_LOAD_USD:
                    continue
                price_matrix[d][ticker] = c
        except Exception:
            continue
    all_dates = sorted(price_matrix.keys())
    if all_dates:
        print("    Date range: {} -> {} ({} days)".format(
            all_dates[0], all_dates[-1], len(all_dates)))
    return price_matrix, ticker_meta, all_dates


def backfill_index(weights, price_matrix, all_dates, base_date_str):
    base_prices = price_matrix.get(base_date_str, {})
    if not base_prices:
        for d in all_dates:
            if d >= base_date_str:
                base_prices = price_matrix[d]
                base_date_str = d
                break
    last_known = {}
    series = []
    for d in all_dates:
        for t, p in price_matrix.get(d, {}).items():
            last_known[t] = p
        if d < base_date_str:
            continue
        weighted_return = 0.0
        active_weight = 0.0
        for t, w in weights.items():
            p_now = last_known.get(t)
            p_base = base_prices.get(t)
            if p_now is not None and p_base is not None and p_base > 0:
                weighted_return += w * (p_now / p_base)
                active_weight += w
        if active_weight > 0:
            value = BASE_VALUE * (weighted_return / active_weight)
        else:
            value = series[-1]["value"] if series else BASE_VALUE
        series.append({"date": d, "value": round(value, 2)})
    return series, base_date_str, base_prices


def normalise_series(series, target_date=NORMALISE_DATE, target_value=BASE_VALUE):
    if not series:
        return series, target_date, 1.0
    raw = None
    actual = None
    for pt in series:
        if pt["date"] == target_date:
            raw = pt["value"]
            actual = target_date
            break
        if pt["date"] > target_date and raw is None:
            raw = pt["value"]
            actual = pt["date"]
            break
        raw = pt["value"]
        actual = pt["date"]
    if raw is None or raw == 0:
        return series, target_date, 1.0
    factor = target_value / raw
    return [{"date": pt["date"], "value": round(pt["value"] * factor, 2)} for pt in series], actual, factor


def compute_divergence(bw_series, mcap_series, flag_threshold=DIVERGENCE_FLAG_PCT):
    """Per-day divergence + monthly-rollup flag log.

    Returns (per_day_list, flag_log_lines).
    per_day = [{date, bw_value, mcap_value, divergence_pct}]
    Monthly rollup averages the per-day divergence and surfaces months where
    |avg| >= flag_threshold.
    """
    mcap_by_date = {pt["date"]: pt["value"] for pt in mcap_series}
    by_month = defaultdict(list)
    per_day = []
    for pt in bw_series:
        d = pt["date"]
        m_val = mcap_by_date.get(d)
        if m_val is None or m_val <= 0:
            continue
        diff_pct = (pt["value"] - m_val) / m_val * 100.0
        per_day.append({
            "date": d,
            "bw": pt["value"],
            "mcap": m_val,
            "divergence_pct": round(diff_pct, 3),
        })
        by_month[d[:7]].append(diff_pct)

    flag_lines = []
    flag_lines.append("# Bottleneck-Weighted vs Market-Cap Composite — Monthly Divergence")
    flag_lines.append("# Flagged: |monthly average divergence pct| >= {}%".format(flag_threshold))
    flag_lines.append("# Negative = bottleneck-weighted UNDERPERFORMS mcap composite")
    flag_lines.append("# Positive = bottleneck-weighted OUTPERFORMS mcap composite")
    flag_lines.append("")
    flag_lines.append("month     avg_div_pct  n_days  flagged")
    flag_lines.append("-" * 42)
    for m, vals in sorted(by_month.items()):
        avg = sum(vals) / len(vals)
        flagged = "Y" if abs(avg) >= flag_threshold else " "
        flag_lines.append("{:7s}   {:+10.3f}%   {:>4d}    {}".format(m, avg, len(vals), flagged))

    return per_day, flag_lines


def main():
    print("=" * 60)
    print("ROBOTNIK BOTTLENECK-WEIGHTED COMPOSITE (v1.0)")
    print("=" * 60)

    mcap_data = load_json(MCAP_PATH)
    prices_data = load_json(PRICES_PATH)
    enrichment = load_json(ENRICHMENT_PATH)
    registry = load_json(REGISTRY_PATH)
    composite = load_json(COMPOSITE_PATH)

    entities = mcap_data["market_caps"]
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    prices_by_ticker = {p["ticker"]: p["price"] for p in prices_data["prices"]
                        if p.get("price") is not None}

    for e in entities:
        e["sector"] = SECTOR_MAP.get(e.get("sector", ""), e.get("sector", "Other"))

    excluded = {k for k, v in registry.items()
                if isinstance(v, dict) and v.get("status") in ("excluded", "data_quarantine")}

    # Token isolation: tokens are a legacy content/research watchlist and must
    # NEVER enter any equity aggregation. Primary isolation is type=="token"
    # (robust to sector mis-tagging); sector=="Token" kept as belt-and-suspenders.
    token_tickers = {k for k, v in registry.items()
                     if isinstance(v, dict)
                     and (v.get("type") == "token" or v.get("sector") in ("Token", "Tokens"))}

    # Eligible universe: same gate as mcap composite (mcap ≥ $10M, has price,
    # not excluded, not a token). That parity is essential — divergence
    # must reflect only the tilt, not differing universes.
    eligible = [e for e in entities
                if e["market_cap_usd"] >= MIN_MARKET_CAP
                and e["ticker"] in prices_by_ticker
                and e["ticker"] not in excluded
                and e["ticker"] not in token_tickers
                and e.get("sector") != "Token"]

    print("  Eligible universe: {}".format(len(eligible)))

    # ── apply bottleneck multipliers ──
    raw_weights = {}
    bn_distribution = defaultdict(int)
    for e in eligible:
        ticker = e["ticker"]
        rated = enrichment.get(ticker, {}) if isinstance(enrichment.get(ticker), dict) else {}
        bn = rated.get("bottleneck_risk")
        m = BOTTLENECK_MULTIPLIERS.get(bn, 1.0)
        raw_weights[ticker] = e["market_cap_usd"] * m
        bn_distribution[bn or "UNRATED"] += 1

    print("  Bottleneck distribution in eligible universe:")
    for bn in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "UNRATED"):
        n = bn_distribution.get(bn, 0)
        pct = n / len(eligible) * 100 if eligible else 0
        mult = BOTTLENECK_MULTIPLIERS.get(bn if bn != "UNRATED" else None, 1.0)
        print("    {:8s}  ×{:.1f}   {:>4d}  ({:5.1f}%)".format(bn, mult, n, pct))

    # ── 5% cap (same as mcap composite) ──
    weights = compute_capped_weights(raw_weights)

    # ── load history ──
    price_matrix, ticker_meta, all_dates = load_all_history()

    # inject today's live prices
    if today_str not in price_matrix:
        price_matrix[today_str] = {}
        all_dates.append(today_str)
        all_dates.sort()
    for t, p in prices_by_ticker.items():
        if p is not None and 0 < p <= 5000:
            price_matrix[today_str][t] = p

    # ── base date selection ──
    # Same heuristic as calculate_index.py: earliest date within ~5Y window
    # where ≥30% of capped weight is represented.
    min_cov = sum(weights.values()) * 0.3
    base_date_str = all_dates[0]
    target_5y = (datetime.strptime(today_str, "%Y-%m-%d") - timedelta(days=1825)).strftime("%Y-%m-%d")
    for d in all_dates:
        if d >= target_5y:
            day_w = sum(w for t, w in weights.items() if t in price_matrix.get(d, {}))
            if day_w >= min_cov:
                base_date_str = d
                break
    print("  Base date: {}".format(base_date_str))

    # ── backfill ──
    raw_series, actual_base, _ = backfill_index(weights, price_matrix, all_dates, base_date_str)
    series, norm_date, factor = normalise_series(raw_series)
    print("  Normalised to {}={} (date: {}, factor: {:.6f})".format(
        BASE_VALUE, BASE_VALUE, norm_date, factor))
    if not series:
        print("  ERROR: empty series produced", file=sys.stderr)
        sys.exit(1)

    last_value = series[-1]["value"]
    print("  Last value: {} ({})".format(last_value, series[-1]["date"]))

    # ── divergence vs mcap composite ──
    per_day_div, flag_lines = compute_divergence(series, composite.get("series", []))
    flagged_months = [l for l in flag_lines if l.endswith("Y")]
    print("  Divergence vs mcap composite: {} months flagged (|avg| >= {}%)".format(
        len(flagged_months), DIVERGENCE_FLAG_PCT))

    # ── output ──
    weights_for_output = sorted(
        [{"ticker": t,
          "name": next((e["name"] for e in eligible if e["ticker"] == t), t),
          "sector": next((e["sector"] for e in eligible if e["ticker"] == t), None),
          "market_cap_usd": next((e["market_cap_usd"] for e in eligible if e["ticker"] == t), None),
          "bottleneck_risk": (enrichment.get(t, {}) if isinstance(enrichment.get(t), dict) else {}).get("bottleneck_risk"),
          "multiplier": BOTTLENECK_MULTIPLIERS.get(
              (enrichment.get(t, {}) if isinstance(enrichment.get(t), dict) else {}).get("bottleneck_risk"),
              1.0
          ),
          "weight_pct": round(w * 100, 4)}
         for t, w in weights.items()],
        key=lambda x: x["weight_pct"], reverse=True
    )

    output = {
        "name": "Robotnik Bottleneck-Weighted Composite",
        "version": "1.0",
        "status": "preliminary — directional signal only, not headline-publishable",
        "base_date": NORMALISE_DATE,
        "base_value": BASE_VALUE,
        "current_value": last_value,
        "current_date": series[-1]["date"],
        "entity_count": len(eligible),
        "rated_entity_count": sum(1 for e in eligible
                                  if (enrichment.get(e["ticker"], {}) if isinstance(enrichment.get(e["ticker"]), dict) else {}).get("bottleneck_risk")),
        "rating_coverage_pct": round(
            sum(1 for e in eligible
                if (enrichment.get(e["ticker"], {}) if isinstance(enrichment.get(e["ticker"]), dict) else {}).get("bottleneck_risk")) / len(eligible) * 100, 1
        ),
        "headline_publishable_threshold_pct": 80,
        "bottleneck_multipliers": BOTTLENECK_MULTIPLIERS,
        "method": "Pattern A multiplicative tilt: weight_i = mcap_i × multiplier(bottleneck_i), then 5% cap with proportional excess redistribution",
        "weights": weights_for_output[:50],   # top 50 only — full set is large
        "weight_count_total": len(weights_for_output),
        "series": series,
        "divergence_vs_mcap_composite": {
            "monthly_flag_threshold_pct": DIVERGENCE_FLAG_PCT,
            "months_flagged": len(flagged_months),
            "per_day_sample": per_day_div[-30:] if len(per_day_div) >= 30 else per_day_div,
        },
        "calculated_at": datetime.now(timezone.utc).isoformat() + "Z",
    }
    save_json(OUT_PATH, output)

    with open(OUT_DIVERGENCE, "w") as f:
        f.write("\n".join(flag_lines) + "\n")

    print("  Output: {}".format(OUT_PATH.relative_to(ROOT)))
    print("  Output: {}".format(OUT_DIVERGENCE.relative_to(ROOT)))

    # ── top 5 weights, top 5 bottleneck winners ──
    print("\n  Top 5 weights overall:")
    for w in weights_for_output[:5]:
        print("    {:8s} {:6.2f}%   ×{:.1f}   {}".format(
            w["ticker"], w["weight_pct"], w["multiplier"], w["name"]))

    crit_high = [w for w in weights_for_output
                 if w["bottleneck_risk"] in ("CRITICAL", "HIGH")]
    if crit_high:
        crit_high.sort(key=lambda x: x["weight_pct"], reverse=True)
        print("\n  Top Critical/High weighted constituents:")
        for w in crit_high[:5]:
            print("    {:8s} {:6.2f}%   ×{:.1f}   {} ({})".format(
                w["ticker"], w["weight_pct"], w["multiplier"], w["name"], w["bottleneck_risk"]))

    print("=" * 60)


if __name__ == "__main__":
    main()
