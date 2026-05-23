#!/usr/bin/env python3
"""
Robotnik Index Metrics
======================
Mirrors the per-constituent metric set at the index level for each of the
4 sub-indices and the Composite. Outputs:

  - Returns (1M, 3M, 6M, YTD, 1Y, 3Y, 5Y)
  - Volatility (30D, 90D, 1Y — annualised log-return stdev)
  - Drawdown (current from ATH, max 1Y, max 3Y)
  - Momentum (3M, 6M — risk-adjusted return / annualised vol)
  - Beta (vs SPY, IXIC, URTH — 1Y daily, 252-day window)
  - Daily change % (last close vs prior close)

Inputs:
    data/index/robotnik_index.json    — composite daily series
    data/index/sub_indices.json       — 4 sub-index daily series
    data/prices/benchmarks.json       — broad-market beta references

Output:
    data/index/index_metrics.json     — per-series metric block + composite

Usage:
    python scripts/calculate_index_metrics.py
"""

import json
import math
from datetime import datetime, date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMPOSITE_PATH  = ROOT / "data" / "index" / "robotnik_index.json"
SUB_PATH        = ROOT / "data" / "index" / "sub_indices.json"
BENCHMARKS_PATH = ROOT / "data" / "prices" / "benchmarks.json"
OUTPUT_PATH     = ROOT / "data" / "index" / "index_metrics.json"

TRADING_DAYS_PER_YEAR = 252
BETA_WINDOW = 252

TODAY     = date.today()
YTD_START = "{}-12-31".format(TODAY.year - 1)
TARGETS = {
    "1m":  (TODAY - timedelta(days=30)).isoformat(),
    "3m":  (TODAY - timedelta(days=90)).isoformat(),
    "6m":  (TODAY - timedelta(days=180)).isoformat(),
    "ytd": YTD_START,
    "1y":  (TODAY - timedelta(days=365)).isoformat(),
    "3y":  (TODAY - timedelta(days=365 * 3)).isoformat(),
    "5y":  (TODAY - timedelta(days=365 * 5)).isoformat(),
}


def load_json(path):
    with open(path) as f:
        return json.load(f)


def _round(v, n=4):
    if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
        return None
    return round(v, n)


def _series_to_map(series):
    return {pt["date"]: pt["value"] for pt in series if pt.get("value") is not None}


def _find_value(by_date, target_date, window=5):
    target_dt = datetime.strptime(target_date, "%Y-%m-%d").date()
    for offset in range(window + 1):
        d = (target_dt - timedelta(days=offset)).isoformat()
        if d in by_date:
            return by_date[d]
    return None


def _log_returns(by_date, dates):
    out = []
    prev = None
    for d in dates:
        v = by_date.get(d)
        if v is None or v <= 0:
            prev = None
            continue
        if prev is not None and prev > 0:
            out.append((d, math.log(v / prev)))
        prev = v
    return out


def _ann_vol(log_rets):
    if len(log_rets) < 10:
        return None
    rs = [r for _, r in log_rets]
    n = len(rs)
    mean = sum(rs) / n
    var = sum((r - mean) ** 2 for r in rs) / (n - 1)
    return math.sqrt(var) * math.sqrt(TRADING_DAYS_PER_YEAR)


def _max_dd(by_date, start_date_str):
    dates = sorted(d for d in by_date if d >= start_date_str)
    if len(dates) < 5:
        return None
    peak = -1.0
    mx = 0.0
    for d in dates:
        v = by_date[d]
        if v is None or v <= 0:
            continue
        if v > peak:
            peak = v
        if peak > 0:
            dd = (v - peak) / peak
            if dd < mx:
                mx = dd
    return mx * 100.0


def _current_dd(by_date, dates_sorted):
    vals = [by_date[d] for d in dates_sorted if by_date.get(d) and by_date[d] > 0]
    if not vals:
        return None
    peak = max(vals)
    cur = vals[-1]
    if peak <= 0:
        return None
    return (cur - peak) / peak * 100.0


def _beta(log_x, log_b):
    xm, bm = dict(log_x), dict(log_b)
    common = sorted(set(xm) & set(bm))
    if len(common) < 30:
        return None
    common = common[-BETA_WINDOW:]
    xs = [xm[d] for d in common]
    bs = [bm[d] for d in common]
    n = len(xs)
    mx = sum(xs) / n
    mb = sum(bs) / n
    cov = sum((x - mx) * (b - mb) for x, b in zip(xs, bs)) / (n - 1)
    var_b = sum((b - mb) ** 2 for b in bs) / (n - 1)
    if var_b == 0:
        return None
    return cov / var_b


def compute_block(series, name, bench_log_returns):
    """Compute the full metric set for one index series."""
    by_date = _series_to_map(series)
    if not by_date:
        return {"name": name, "missing": True}

    dates_sorted = sorted(by_date.keys())
    last_date = dates_sorted[-1]
    last_value = by_date[last_date]

    # ── daily change ──
    daily_pct = None
    if len(dates_sorted) >= 2:
        prev = by_date.get(dates_sorted[-2])
        if prev and prev > 0:
            daily_pct = (last_value - prev) / prev * 100.0

    # ── returns ──
    returns = {}
    for k, t in TARGETS.items():
        base = _find_value(by_date, t)
        if base is not None and base > 0:
            returns[k] = (last_value - base) / base * 100.0
        else:
            returns[k] = None

    # ── drawdown ──
    cur_dd  = _current_dd(by_date, dates_sorted)
    dd_1y   = _max_dd(by_date, TARGETS["1y"])
    dd_3y   = _max_dd(by_date, TARGETS["3y"])

    # ── volatility (annualised) ──
    log_all = _log_returns(by_date, dates_sorted)
    log_30  = [(d, r) for d, r in log_all if d >= TARGETS["1m"]]
    log_90  = [(d, r) for d, r in log_all if d >= TARGETS["3m"]]
    log_1y  = [(d, r) for d, r in log_all if d >= TARGETS["1y"]]
    vol_30  = _ann_vol(log_30)
    vol_90  = _ann_vol(log_90)
    vol_1y  = _ann_vol(log_1y)

    # ── momentum (risk-adjusted) ──
    mom_3m = None
    if returns.get("3m") is not None and vol_90 and vol_90 > 0:
        mom_3m = returns["3m"] / (vol_90 * 100.0)
    mom_6m = None
    if returns.get("6m") is not None and vol_1y and vol_1y > 0:
        mom_6m = returns["6m"] / (vol_1y * 100.0)

    # ── beta vs broad benchmarks ──
    betas = {}
    for bench_key, bench_log in bench_log_returns.items():
        betas["beta_" + bench_key.lower()] = _round(_beta(log_1y, bench_log), 3)

    # ── ATH ──
    all_vals = [by_date[d] for d in dates_sorted if by_date[d] > 0]
    ath = max(all_vals) if all_vals else None

    return {
        "name": name,
        "last_date": last_date,
        "last_value": _round(last_value, 2),
        "daily_change_pct": _round(daily_pct, 2),
        "ath": _round(ath, 2),
        "history_days": len(dates_sorted),
        "first_history_date": dates_sorted[0],
        "return_1m_pct":  _round(returns.get("1m"), 2),
        "return_3m_pct":  _round(returns.get("3m"), 2),
        "return_6m_pct":  _round(returns.get("6m"), 2),
        "return_ytd_pct": _round(returns.get("ytd"), 2),
        "return_1y_pct":  _round(returns.get("1y"), 2),
        "return_3y_pct":  _round(returns.get("3y"), 2),
        "return_5y_pct":  _round(returns.get("5y"), 2),
        "drawdown_current_pct": _round(cur_dd, 2),
        "drawdown_max_1y_pct":  _round(dd_1y, 2),
        "drawdown_max_3y_pct":  _round(dd_3y, 2),
        "volatility_30d_ann": _round(vol_30, 4),
        "volatility_90d_ann": _round(vol_90, 4),
        "volatility_1y_ann":  _round(vol_1y, 4),
        "momentum_3m_risk_adj": _round(mom_3m, 4),
        "momentum_6m_risk_adj": _round(mom_6m, 4),
        **betas,
    }


def main():
    print("=" * 60)
    print("ROBOTNIK INDEX METRICS")
    print("=" * 60)

    composite = load_json(COMPOSITE_PATH)
    sub = load_json(SUB_PATH)
    bench = load_json(BENCHMARKS_PATH)

    # ── benchmark log returns (broad only — beta inputs) ──
    bench_log = {}
    for k, info in bench.get("benchmarks", {}).items():
        if info.get("role") != "broad":
            continue
        by_date = {pt["date"]: pt["close"] for pt in info.get("series", [])
                   if pt.get("close") and pt["close"] > 0}
        dates_sorted = sorted(by_date)
        bench_log[k] = _log_returns(by_date, dates_sorted)

    print("\n  Benchmarks for beta: {}".format(", ".join(sorted(bench_log))))

    out = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "schema_version": "index_metrics/1.0",
        "broad_benchmarks_used_for_beta": list(bench_log.keys()),
        "composite": None,
        "sub_indices": {},
    }

    # ── composite ──
    comp_block = compute_block(composite.get("series", []),
                               composite.get("name", "Robotnik Composite Index"),
                               bench_log)
    comp_block["entity_count"] = composite.get("entity_count")
    out["composite"] = comp_block
    print("\n  Composite: {} ({} points)".format(comp_block["last_value"], comp_block["history_days"]))

    # ── sub-indices ──
    for k, info in sub.items():
        if not isinstance(info, dict):
            continue
        block = compute_block(info.get("series", []), info.get("name", k), bench_log)
        block["entity_count"] = info.get("entity_count")
        block["top_5"] = info.get("top_5")
        out["sub_indices"][k] = block
        print("  {:14s} {} ({} points)".format(k, block["last_value"], block["history_days"]))

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(out, f, indent=2)
    print("\n  Output: {}".format(OUTPUT_PATH.relative_to(ROOT)))
    print("=" * 60)


if __name__ == "__main__":
    main()
