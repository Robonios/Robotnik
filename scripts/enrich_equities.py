#!/usr/bin/env python3
"""
Robotnik Public Equities — Per-Constituent Enrichment
=====================================================
Consolidates 5 sources of truth into one enriched record per equity and
computes the advanced metric set the API needs for portfolio analysis:

  - Returns (mirrored from calculate_metrics.py for cross-source parity)
  - Volatility (30D, 90D — annualised from daily log returns)
  - Drawdown (current from ATH, max 1Y, max 3Y rolling)
  - Momentum (3M and 6M — risk-adjusted = return / annualised vol)
  - Volume (30D, 90D averages — duplicated from calculate_metrics for completeness)
  - Beta (vs SPY, IXIC, URTH — 1Y daily, 250 trading-day window)
  - Bottleneck multiplier (4.0 / 2.5 / 1.5 / 1.0 — Critical / High / Medium / Low)
  - Cross-sectional rankings (within sector and subsector)
  - Data completeness flag (full / partial / minimal / missing)

Where history is insufficient for a given metric, returns null. Never extrapolates.

Inputs:
    data/prices/equities.json           — canonical universe + current quote
    data/prices/history/*.json          — 5Y daily OHLCV per constituent
    data/prices/benchmarks.json         — 5Y daily series for SPY/IXIC/URTH/QQQ/SOXX/ROBO
    data/index/market_caps.json         — USD market caps
    data/markets/robotnik_public_markets.json — fundamentals (PE, FCF, etc.) + sparkline
    data/markets/enrichment_data.json   — bottleneck_risk + qualitative notes (rated subset)
    data/registries/entity_registry.json — subsector + value_chain (canonical)

Outputs:
    data/markets/enriched_equities.json  — one consolidated record per constituent
    data/markets/coverage_report.json    — per-metric coverage across the universe

Usage:
    python scripts/enrich_equities.py
"""

import json
import math
import os
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from statistics import median

# ── paths ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
EQUITIES_PATH       = ROOT / "data" / "prices" / "equities.json"
HISTORY_DIR         = ROOT / "data" / "prices" / "history"
BENCHMARKS_PATH     = ROOT / "data" / "prices" / "benchmarks.json"
MARKET_CAPS_PATH    = ROOT / "data" / "index" / "market_caps.json"
PUBLIC_MARKETS_PATH = ROOT / "data" / "markets" / "robotnik_public_markets.json"
ENRICHMENT_PATH     = ROOT / "data" / "markets" / "enrichment_data.json"
REGISTRY_PATH       = ROOT / "data" / "registries" / "entity_registry.json"

OUT_ENRICHED        = ROOT / "data" / "markets" / "enriched_equities.json"
OUT_COVERAGE        = ROOT / "data" / "markets" / "coverage_report.json"

# ── config ───────────────────────────────────────────────────────────────
TRADING_DAYS_PER_YEAR = 252
BETA_WINDOW_DAYS      = 252  # ~1Y rolling for beta

# Bottleneck multipliers (v1.0 — see metrics_methodology.md for rationale).
# Critical→High step is categorical (sole-source vs costly-substitute), not
# gradient, so non-linear encoding. Unrated → 1.0 (no amplification, conservative).
BOTTLENECK_MULTIPLIERS = {
    "CRITICAL": 4.0,
    "HIGH":     2.5,
    "MEDIUM":   1.5,
    "LOW":      1.0,
    None:       1.0,   # unrated default
}

# Enum mapping from 4-level equity (CRITICAL/HIGH/MEDIUM/LOW) to 5-level private
# (Critical/High/Medium/Low/Pre-commercial). Public equities are by definition
# revenue-generating and so never qualify as Pre-commercial; the public→private
# join uses these mappings when sectors are compared across asset classes.
EQUITY_TO_PRIVATE_ENUM = {
    "CRITICAL": "Critical",
    "HIGH":     "High",
    "MEDIUM":   "Medium",
    "LOW":      "Low",
}

# Date anchors
TODAY      = date.today()
YTD_START  = "{}-12-31".format(TODAY.year - 1)
TARGETS = {
    "1m":  (TODAY - timedelta(days=30)).isoformat(),
    "3m":  (TODAY - timedelta(days=90)).isoformat(),
    "6m":  (TODAY - timedelta(days=180)).isoformat(),
    "ytd": YTD_START,
    "1y":  (TODAY - timedelta(days=365)).isoformat(),
    "3y":  (TODAY - timedelta(days=365 * 3)).isoformat(),
    "5y":  (TODAY - timedelta(days=365 * 5)).isoformat(),
}


# ── small helpers ────────────────────────────────────────────────────────
def load_json(path):
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def _round_or_none(v, places=4):
    if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
        return None
    return round(v, places)


def _pct_change(old, new):
    if old is None or new is None or old == 0:
        return None
    return (new - old) / old * 100.0


def _find_close_on_or_before(series, target_date_str, window=5):
    """Return (close, actual_date_used) for target or nearest prior trading day.

    series : dict of date_str -> close_price
    Returns (None, None) if nothing within `window` days.
    """
    target_dt = datetime.strptime(target_date_str, "%Y-%m-%d").date()
    for offset in range(window + 1):
        d_str = (target_dt - timedelta(days=offset)).isoformat()
        if d_str in series:
            return series[d_str], d_str
    return None, None


def _log_returns(close_by_date, dates):
    """Compute daily log returns over a chronological list of dates.

    Skips zero/negative prices defensively. Returns list of (date, log_return)
    where log_return is ln(p_t / p_{t-1}).
    """
    out = []
    prev = None
    for d in dates:
        c = close_by_date.get(d)
        if c is None or c <= 0:
            prev = None
            continue
        if prev is not None and prev > 0:
            out.append((d, math.log(c / prev)))
        prev = c
    return out


def _annualised_vol(log_rets):
    """Sample-stdev of daily log returns × sqrt(252). Requires ≥10 obs."""
    if len(log_rets) < 10:
        return None
    rs = [r for _, r in log_rets]
    n = len(rs)
    mean = sum(rs) / n
    var = sum((r - mean) ** 2 for r in rs) / (n - 1)
    return math.sqrt(var) * math.sqrt(TRADING_DAYS_PER_YEAR)


def _max_drawdown(close_by_date, start_date_str):
    """Maximum peak-to-trough drawdown from start_date forward.

    Walks the series, tracks running peak, returns max (peak-trough)/peak as
    a negative percentage (e.g. -45.3). None if fewer than 5 obs in window.
    """
    dates = sorted(d for d in close_by_date if d >= start_date_str)
    if len(dates) < 5:
        return None
    peak = -1.0
    max_dd = 0.0
    for d in dates:
        c = close_by_date[d]
        if c is None or c <= 0:
            continue
        if c > peak:
            peak = c
        if peak > 0:
            dd = (c - peak) / peak  # negative or zero
            if dd < max_dd:
                max_dd = dd
    return max_dd * 100.0  # percent


def _current_drawdown(close_by_date, dates_sorted, all_time=True):
    """Current price expressed as % below all-time peak (negative number).

    Mirrors pct_from_ath but recomputed here for self-containment.
    """
    if not dates_sorted:
        return None
    closes = [close_by_date[d] for d in dates_sorted if close_by_date.get(d) and close_by_date[d] > 0]
    if not closes:
        return None
    peak = max(closes)
    current = closes[-1]
    if peak <= 0:
        return None
    return (current - peak) / peak * 100.0


def _beta_against(log_returns_x, log_returns_b, max_lookback=BETA_WINDOW_DAYS):
    """OLS beta of x against benchmark b over the last ``max_lookback`` aligned days.

    Each input is a list of (date, log_return). Aligns by date, takes the
    tail of length `max_lookback`. Returns None if <30 aligned observations.
    """
    x_map = dict(log_returns_x)
    b_map = dict(log_returns_b)
    common = sorted(set(x_map) & set(b_map))
    if len(common) < 30:
        return None
    common = common[-max_lookback:]
    xs = [x_map[d] for d in common]
    bs = [b_map[d] for d in common]
    n = len(xs)
    mean_x = sum(xs) / n
    mean_b = sum(bs) / n
    cov = sum((x - mean_x) * (b - mean_b) for x, b in zip(xs, bs)) / (n - 1)
    var_b = sum((b - mean_b) ** 2 for b in bs) / (n - 1)
    if var_b == 0:
        return None
    return cov / var_b


# ── core ─────────────────────────────────────────────────────────────────
def load_constituent_history(ticker):
    """Read OHLCV history for a ticker. Returns dict of date -> close (and dict of date -> volume)."""
    fpath = HISTORY_DIR / "{}.json".format(ticker)
    if not fpath.exists():
        # try fallback name with underscores (e.g. tickers with spaces)
        fpath = HISTORY_DIR / "{}.json".format(ticker.replace(" ", "_"))
        if not fpath.exists():
            return {}, {}
    try:
        data = json.loads(fpath.read_text())
    except Exception:
        return {}, {}
    close_by_date = {}
    vol_by_date = {}
    for pt in data.get("series", []):
        d = pt.get("date")
        c = pt.get("close")
        v = pt.get("volume")
        if d and c is not None and c > 0:
            close_by_date[d] = c
        if d and v is not None:
            vol_by_date[d] = v
    return close_by_date, vol_by_date


def compute_metrics_for_ticker(ticker, current_price, current_date_str,
                                benchmark_log_returns):
    """Compute all derived metrics for one constituent.

    Returns a dict of metrics + history-quality flags. Any metric that lacks
    sufficient history returns null.
    """
    close_by_date, vol_by_date = load_constituent_history(ticker)
    # Inject the live close so today's value enters returns/drawdown.
    if current_price is not None and current_price > 0 and current_date_str:
        close_by_date[current_date_str] = current_price

    if not close_by_date:
        return _empty_metrics(reason="no_history")

    dates_sorted = sorted(close_by_date.keys())
    history_span_days = (
        datetime.strptime(dates_sorted[-1], "%Y-%m-%d").date()
        - datetime.strptime(dates_sorted[0], "%Y-%m-%d").date()
    ).days

    # ── returns ──
    returns = {}
    for period, target in TARGETS.items():
        base, _ = _find_close_on_or_before(close_by_date, target)
        returns[period] = _pct_change(base, current_price)

    # ── ATH + drawdown ──
    all_closes = [close_by_date[d] for d in dates_sorted if close_by_date[d] > 0]
    ath = max(all_closes) if all_closes else None
    current_dd = _current_drawdown(close_by_date, dates_sorted)
    one_y_dd = _max_drawdown(close_by_date, TARGETS["1y"])
    three_y_dd = _max_drawdown(close_by_date, TARGETS["3y"])

    # ── log returns + volatility ──
    log_rets_all = _log_returns(close_by_date, dates_sorted)
    log_rets_30d = [(d, r) for d, r in log_rets_all if d >= TARGETS["1m"]]
    log_rets_90d = [(d, r) for d, r in log_rets_all if d >= TARGETS["3m"]]
    log_rets_1y  = [(d, r) for d, r in log_rets_all if d >= TARGETS["1y"]]

    vol_30d = _annualised_vol(log_rets_30d)
    vol_90d = _annualised_vol(log_rets_90d)
    vol_1y  = _annualised_vol(log_rets_1y)

    # ── momentum (risk-adjusted return: return_pct / annualised_vol_pct) ──
    # When the denominator is zero or null, the metric is meaningless → null.
    mom_3m = None
    if returns.get("3m") is not None and vol_90d is not None and vol_90d > 0:
        mom_3m = returns["3m"] / (vol_90d * 100.0)
    mom_6m = None
    if returns.get("6m") is not None and vol_1y is not None and vol_1y > 0:
        mom_6m = returns["6m"] / (vol_1y * 100.0)

    # ── beta vs broad-market benchmarks ──
    # Uses 1Y of daily log returns. Each broad benchmark gets its own beta.
    betas = {}
    for bench_key, bench_log_rets in benchmark_log_returns.items():
        betas["beta_" + bench_key.lower()] = _beta_against(log_rets_1y, bench_log_rets)

    # ── volume averages ──
    sorted_vol_dates = sorted(vol_by_date.keys())
    vol_30_obs = [vol_by_date[d] for d in sorted_vol_dates if d >= TARGETS["1m"]]
    vol_90_obs = [vol_by_date[d] for d in sorted_vol_dates if d >= TARGETS["3m"]]
    volume_avg_30d = round(sum(vol_30_obs) / len(vol_30_obs)) if vol_30_obs else None
    volume_avg_90d = round(sum(vol_90_obs) / len(vol_90_obs)) if vol_90_obs else None

    # ── data completeness flag ──
    if history_span_days >= 365 * 5 - 30:  # ≥ ~5Y
        completeness = "full"     # all metrics computable
    elif history_span_days >= 365 * 3 - 30:
        completeness = "partial"  # 5Y nulled, others computable
    elif history_span_days >= 365 - 30:
        completeness = "minimal"  # 3Y+5Y nulled
    else:
        completeness = "thin"     # under 1Y, only short-window metrics

    return {
        "history_days":       len(dates_sorted),
        "history_span_days":  history_span_days,
        "first_history_date": dates_sorted[0],
        "last_history_date":  dates_sorted[-1],
        "data_completeness":  completeness,
        # returns
        "return_1m_pct":  _round_or_none(returns.get("1m"), 2),
        "return_3m_pct":  _round_or_none(returns.get("3m"), 2),
        "return_6m_pct":  _round_or_none(returns.get("6m"), 2),
        "return_ytd_pct": _round_or_none(returns.get("ytd"), 2),
        "return_1y_pct":  _round_or_none(returns.get("1y"), 2),
        "return_3y_pct":  _round_or_none(returns.get("3y"), 2),
        "return_5y_pct":  _round_or_none(returns.get("5y"), 2),
        # drawdown
        "ath": _round_or_none(ath, 4),
        "drawdown_current_pct":  _round_or_none(current_dd, 2),
        "drawdown_max_1y_pct":   _round_or_none(one_y_dd, 2),
        "drawdown_max_3y_pct":   _round_or_none(three_y_dd, 2),
        # volatility (annualised, decimal form e.g. 0.354 = 35.4%)
        "volatility_30d_ann": _round_or_none(vol_30d, 4),
        "volatility_90d_ann": _round_or_none(vol_90d, 4),
        "volatility_1y_ann":  _round_or_none(vol_1y, 4),
        # momentum (risk-adjusted, unitless)
        "momentum_3m_risk_adj": _round_or_none(mom_3m, 4),
        "momentum_6m_risk_adj": _round_or_none(mom_6m, 4),
        # volume
        "volume_avg_30d": volume_avg_30d,
        "volume_avg_90d": volume_avg_90d,
        # beta
        **{k: _round_or_none(v, 3) for k, v in betas.items()},
    }


def _empty_metrics(reason):
    """Skeleton with all metric fields nulled — keeps schema uniform across constituents."""
    return {
        "history_days": 0,
        "history_span_days": 0,
        "first_history_date": None,
        "last_history_date": None,
        "data_completeness": "missing",
        "missing_reason": reason,
        "return_1m_pct": None, "return_3m_pct": None, "return_6m_pct": None,
        "return_ytd_pct": None, "return_1y_pct": None, "return_3y_pct": None,
        "return_5y_pct": None,
        "ath": None,
        "drawdown_current_pct": None, "drawdown_max_1y_pct": None, "drawdown_max_3y_pct": None,
        "volatility_30d_ann": None, "volatility_90d_ann": None, "volatility_1y_ann": None,
        "momentum_3m_risk_adj": None, "momentum_6m_risk_adj": None,
        "volume_avg_30d": None, "volume_avg_90d": None,
        "beta_spy": None, "beta_ixic": None, "beta_urth": None,
    }


def build_benchmark_log_returns(benchmarks_data):
    """Pre-compute log-return series for each broad-market benchmark.

    Returns dict of benchmark_key -> list[(date, log_return)].
    Only "broad"-role benchmarks are exposed for beta calculations — sector
    benchmarks (QQQ/SOXX/ROBO) are reported on the index side but never used
    as broad-market beta references (would amount to industry-on-industry beta).
    """
    out = {}
    for key, info in benchmarks_data.get("benchmarks", {}).items():
        if info.get("role") != "broad":
            continue
        close_by_date = {pt["date"]: pt["close"] for pt in info.get("series", [])
                         if pt.get("close") and pt["close"] > 0}
        dates_sorted = sorted(close_by_date.keys())
        out[key] = _log_returns(close_by_date, dates_sorted)
    return out


# ── cross-sectional rankings (Step 6) ────────────────────────────────────
def compute_rankings(records):
    """Append within-sector and within-subsector rank + percentile for the key metrics.

    Mutates `records` in place. Excludes nulls from rank denominators.
    """
    METRICS_TO_RANK = [
        ("return_1y_pct",         "higher_is_better"),
        ("return_3y_pct",         "higher_is_better"),
        ("volatility_1y_ann",     "lower_is_better"),
        ("drawdown_max_1y_pct",   "higher_is_better"),  # less negative = better
        ("beta_spy",              "lower_is_better"),   # lower beta = less broad-market exposure
        ("momentum_3m_risk_adj",  "higher_is_better"),
    ]

    for grouping in ("sector", "subsector"):
        buckets = defaultdict(list)
        for ticker, rec in records.items():
            g = rec.get(grouping)
            if not g:
                continue
            buckets[g].append((ticker, rec))

        for group_key, members in buckets.items():
            for metric, direction in METRICS_TO_RANK:
                vals = [(t, rec.get(metric)) for t, rec in members if rec.get(metric) is not None]
                if len(vals) < 3:
                    continue  # rankings within tiny universes are noise
                reverse = (direction == "higher_is_better")
                vals.sort(key=lambda x: x[1], reverse=reverse)
                n = len(vals)
                for rank, (t, _) in enumerate(vals, start=1):
                    pct = round((n - rank) / (n - 1) * 100, 1) if n > 1 else 100.0
                    key_rank = "rank_{}_{}_in_{}".format(metric, "desc" if reverse else "asc", grouping)
                    key_pct  = "percentile_{}_in_{}".format(metric, grouping)
                    records[t].setdefault("rankings", {})
                    records[t]["rankings"][key_rank] = rank
                    records[t]["rankings"][key_pct] = pct
                    records[t]["rankings"]["_universe_size_in_" + grouping] = n


# ── main ─────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("ROBOTNIK EQUITIES ENRICHMENT")
    print("=" * 60)

    eq_data        = load_json(EQUITIES_PATH)        or {"equities": []}
    bench_data     = load_json(BENCHMARKS_PATH)      or {"benchmarks": {}}
    mcap_data      = load_json(MARKET_CAPS_PATH)     or {"market_caps": []}
    public_markets = load_json(PUBLIC_MARKETS_PATH)  or {"entities": {}}
    enrichment     = load_json(ENRICHMENT_PATH)      or {}
    registry       = load_json(REGISTRY_PATH)        or {}

    # ── lookup tables ──
    mcap_by_ticker = {m["ticker"]: m for m in mcap_data.get("market_caps", [])
                      if m.get("market_cap_usd")}
    fundamentals   = public_markets.get("entities", {})
    excluded = {k for k, v in registry.items()
                if isinstance(v, dict) and v.get("status") == "excluded"}

    # ── benchmark log returns (broad-market only — beta inputs) ──
    bench_log_returns = build_benchmark_log_returns(bench_data)
    print("\n  Benchmark log-return series built for: {}".format(
        ", ".join(sorted(bench_log_returns.keys()))))

    # ── per-constituent enrichment ──
    records = {}
    skipped = []

    for entry in eq_data.get("equities", []):
        ticker = entry["ticker"]
        if ticker in excluded:
            skipped.append((ticker, "registry_excluded"))
            continue

        # registry hits canonical taxonomy
        reg_entry = registry.get(ticker, {}) if isinstance(registry.get(ticker), dict) else {}
        sector    = reg_entry.get("sector")    or entry.get("sector")
        subsector = reg_entry.get("subsector")
        value_chain = reg_entry.get("value_chain")

        # bottleneck — only the 58-entity rated subset has data here
        rated = enrichment.get(ticker, {}) if isinstance(enrichment.get(ticker), dict) else {}
        bottleneck = rated.get("bottleneck_risk")
        multiplier = BOTTLENECK_MULTIPLIERS.get(bottleneck, 1.0)

        # fundamentals (from existing calculate_metrics pipeline)
        fund = fundamentals.get(ticker, {})

        # market cap (USD-converted)
        mcap_entry = mcap_by_ticker.get(ticker, {})

        # compute the heavy metrics
        metrics = compute_metrics_for_ticker(
            ticker=ticker,
            current_price=entry.get("price"),
            current_date_str=entry.get("date"),
            benchmark_log_returns=bench_log_returns,
        )

        records[ticker] = {
            # ── identity ──
            "ticker": ticker,
            "name": entry.get("name") or reg_entry.get("name"),
            "eodhd_symbol": entry.get("eodhd_symbol") or reg_entry.get("eodhd_ticker"),
            "sector": sector,
            "subsector": subsector,
            "value_chain": value_chain,
            "currency": entry.get("currency"),
            # ── current quote ──
            "price": entry.get("price"),
            "price_date": entry.get("date"),
            "price_source": entry.get("source"),
            # ── bottleneck ──
            "bottleneck_risk": bottleneck,
            "bottleneck_multiplier": multiplier,
            "bottleneck_rated": bottleneck is not None,
            # ── market cap ──
            "market_cap_usd": mcap_entry.get("market_cap_usd"),
            "market_cap_source": mcap_entry.get("source"),
            "market_cap_date": mcap_entry.get("date_fetched"),
            # ── fundamentals (from robotnik_public_markets.json) ──
            "shares_outstanding":    fund.get("shares_outstanding"),
            "revenue_ttm":           fund.get("revenue_ttm"),
            "revenue_growth_yoy":    fund.get("revenue_growth_yoy"),
            "operating_margin":      fund.get("operating_margin"),
            "net_income_ttm":        fund.get("net_income_ttm"),
            "eps":                   fund.get("eps"),
            "pe_ratio":              fund.get("pe_ratio"),
            "forward_pe":            fund.get("forward_pe"),
            "ev":                    fund.get("ev"),
            "ev_ebitda":             fund.get("ev_ebitda"),
            "ps_ratio":              fund.get("ps_ratio"),
            "pb_ratio":              fund.get("pb_ratio"),
            "dividend_yield":        fund.get("dividend_yield"),
            "total_debt":            fund.get("total_debt"),
            "free_cash_flow":        fund.get("free_cash_flow"),
            "next_earnings_date":    fund.get("next_earnings_date"),
            # ── computed metrics ──
            **metrics,
            # ── sparkline (already produced upstream) ──
            "sparkline_30d": fund.get("sparkline_30d"),
        }

    # ── cross-sectional rankings ──
    compute_rankings(records)

    # ── coverage report ──
    coverage = build_coverage_report(records)

    # ── write outputs ──
    output = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "schema_version": "enriched_equities/1.0",
        "universe_size": len(records),
        "skipped": skipped,
        "sources_of_truth": [
            "data/prices/equities.json",
            "data/prices/history/",
            "data/prices/benchmarks.json",
            "data/index/market_caps.json",
            "data/markets/robotnik_public_markets.json",
            "data/markets/enrichment_data.json",
            "data/registries/entity_registry.json",
        ],
        "broad_benchmarks_used_for_beta": list(bench_log_returns.keys()),
        "bottleneck_multipliers": BOTTLENECK_MULTIPLIERS,
        "equity_to_private_enum_map": EQUITY_TO_PRIVATE_ENUM,
        "entities": records,
    }
    save_json(OUT_ENRICHED, output)
    save_json(OUT_COVERAGE, coverage)

    print("\n  Enriched: {} constituents".format(len(records)))
    if skipped:
        print("  Skipped:  {}".format(len(skipped)))
    print("\n  Coverage by data_completeness:")
    for k, n in sorted(coverage["data_completeness"].items()):
        print("    {:10s} {:>4d}".format(k, n))
    print("\n  Coverage by metric (full = non-null):")
    for k, n in sorted(coverage["metric_full_count"].items()):
        pct = n / len(records) * 100 if records else 0
        print("    {:30s} {:>4d}  ({:5.1f}%)".format(k, n, pct))
    print("\n  Output: {}".format(OUT_ENRICHED.relative_to(ROOT)))
    print("  Output: {}".format(OUT_COVERAGE.relative_to(ROOT)))
    print("=" * 60)


# ── coverage report ──────────────────────────────────────────────────────
def build_coverage_report(records):
    completeness_counts = defaultdict(int)
    completeness_members = defaultdict(list)
    metric_full = defaultdict(int)
    bottleneck_counts = defaultdict(int)
    sector_counts = defaultdict(int)
    subsector_counts = defaultdict(int)

    metric_keys = [
        "return_1m_pct", "return_3m_pct", "return_6m_pct", "return_ytd_pct",
        "return_1y_pct", "return_3y_pct", "return_5y_pct",
        "drawdown_current_pct", "drawdown_max_1y_pct", "drawdown_max_3y_pct",
        "volatility_30d_ann", "volatility_90d_ann", "volatility_1y_ann",
        "momentum_3m_risk_adj", "momentum_6m_risk_adj",
        "volume_avg_30d", "volume_avg_90d",
        "beta_spy", "beta_ixic", "beta_urth",
        "market_cap_usd", "pe_ratio", "ev_ebitda", "free_cash_flow",
        "dividend_yield",
    ]
    for ticker, rec in records.items():
        bucket = rec.get("data_completeness", "missing")
        completeness_counts[bucket] += 1
        # Named members — sorted by first_history_date (most recent first)
        # so the recent-IPO drivers surface clearly when API docs cite this.
        completeness_members[bucket].append({
            "ticker": ticker,
            "name": rec.get("name"),
            "sector": rec.get("sector"),
            "subsector": rec.get("subsector"),
            "first_history_date": rec.get("first_history_date"),
            "history_span_days": rec.get("history_span_days"),
        })
        bottleneck_counts[rec.get("bottleneck_risk") or "UNRATED"] += 1
        if rec.get("sector"):
            sector_counts[rec["sector"]] += 1
        if rec.get("subsector"):
            subsector_counts[rec["subsector"]] += 1
        for m in metric_keys:
            if rec.get(m) is not None:
                metric_full[m] += 1

    # Sort each bucket's members by first_history_date desc (newest IPO first)
    # so API docs can lift the head of each list to explain null-metric coverage.
    for bucket in completeness_members:
        completeness_members[bucket].sort(
            key=lambda x: x["first_history_date"] or "0000-00-00",
            reverse=True
        )

    # Identify named constituents missing each metric — useful for the
    # "why is this null" diagnostic the API will need to surface.
    metric_null_members = {}
    for m in metric_keys:
        nulls = [
            {"ticker": t, "name": r.get("name"),
             "sector": r.get("sector"), "data_completeness": r.get("data_completeness")}
            for t, r in records.items() if r.get(m) is None
        ]
        # Sort by sector for readability — group missing constituents together.
        nulls.sort(key=lambda x: (x.get("sector") or "", x.get("ticker")))
        metric_null_members[m] = nulls

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "universe_size": len(records),
        "data_completeness":           dict(completeness_counts),
        "data_completeness_members":   dict(completeness_members),
        "bottleneck_distribution":     dict(bottleneck_counts),
        "sector_distribution":         dict(sector_counts),
        "subsector_distribution":      dict(subsector_counts),
        "metric_full_count":           dict(metric_full),
        "metric_null_members":         metric_null_members,
    }


if __name__ == "__main__":
    main()
