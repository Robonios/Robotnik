#!/usr/bin/env python3
"""
Parity Report — D2-D6 parallel-run comparison.

Reads side-by-side EODHD and MarketStack+Yahoo snapshots for a given trading
day and produces the per-ticker parity report defined in the cutover plan §2.

Inputs:
    data/prices/_compare/eodhd_YYYY-MM-DD.json
    data/prices/_compare/marketstack_YYYY-MM-DD.json

Output:
    data/prices/_compare/parity_report_YYYY-MM-DD.json

Per-ticker fields (cutover plan §2):
    ticker, eodhd_close, marketstack_close, delta_pct,
    flag (OK ≤2% | DRIFT ≤10% | MAJOR >10%),
    eodhd_date, marketstack_date, marketstack_supported

Plus a daily-summary block with the four gate-criteria measurements.

Usage:
    python scripts/parity_report.py YYYY-MM-DD
    python scripts/parity_report.py            # uses today's UTC date
"""

import json
import sys
from datetime import date, datetime
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent
COMPARE_DIR = ROOT / "data" / "prices" / "_compare"
COMPARE_DIR.mkdir(parents=True, exist_ok=True)

# Gate-criteria thresholds (cutover plan §2)
TOL_OK_PCT     = 2.0    # |delta| ≤ 2% → OK
TOL_DRIFT_PCT  = 10.0   # 2 < |delta| ≤ 10% → DRIFT, beyond is MAJOR
GATE_2_TARGET  = 95.0   # ≥95% OK flag across resolved tickers


def load_snapshot(path):
    """Read an equities.json-shape snapshot, return ticker → record dict."""
    if not path.exists():
        return {}
    with open(path) as f:
        data = json.load(f)
    out = {}
    for e in data.get("equities", []):
        tk = e.get("ticker")
        if tk:
            out[tk] = e
    return out


def flag_for(delta_pct):
    if delta_pct is None:
        return None
    d = abs(delta_pct)
    if d <= TOL_OK_PCT:
        return "OK"
    if d <= TOL_DRIFT_PCT:
        return "DRIFT"
    return "MAJOR"


def main():
    target_date = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()

    eodhd_path = COMPARE_DIR / "eodhd_{}.json".format(target_date)
    ms_path    = COMPARE_DIR / "marketstack_{}.json".format(target_date)
    out_path   = COMPARE_DIR / "parity_report_{}.json".format(target_date)

    if not eodhd_path.exists() or not ms_path.exists():
        print("ERROR: missing inputs.")
        print("  Expected: {}".format(eodhd_path))
        print("  Expected: {}".format(ms_path))
        sys.exit(1)

    eodhd = load_snapshot(eodhd_path)
    ms = load_snapshot(ms_path)

    print("=" * 60)
    print("PARITY REPORT — {}".format(target_date))
    print("  EODHD tickers:       {}".format(len(eodhd)))
    print("  MarketStack tickers: {}".format(len(ms)))
    print("=" * 60)

    rows = []
    all_tickers = sorted(set(eodhd) | set(ms))
    for tk in all_tickers:
        e = eodhd.get(tk, {})
        m = ms.get(tk, {})
        e_close = e.get("price")
        m_close = m.get("price")
        delta = None
        if e_close is not None and m_close is not None and e_close not in (0, 0.0):
            try:
                delta = (float(m_close) - float(e_close)) / float(e_close) * 100.0
                delta = round(delta, 3)
            except (TypeError, ValueError):
                delta = None
        rows.append({
            "ticker": tk,
            "eodhd_close":      e_close,
            "marketstack_close": m_close,
            "delta_pct":        delta,
            "flag":             flag_for(delta),
            "eodhd_date":       e.get("date"),
            "marketstack_date": m.get("date"),
            "marketstack_supported": m.get("source", "") != "" and "Yahoo" not in (m.get("source") or ""),
            "in_eodhd":         tk in eodhd,
            "in_marketstack":   tk in ms,
        })

    # Daily-summary block — gate-criteria measurements
    eodhd_resolved = sum(1 for r in rows if r["in_eodhd"] and r["eodhd_close"] is not None)
    ms_resolved    = sum(1 for r in rows if r["in_marketstack"] and r["marketstack_close"] is not None)
    both_resolved  = sum(1 for r in rows if r["delta_pct"] is not None)

    by_flag = Counter(r["flag"] for r in rows if r["flag"])
    ok_pct = (by_flag.get("OK", 0) / both_resolved * 100) if both_resolved else 0.0
    coverage_pct = (ms_resolved / eodhd_resolved * 100) if eodhd_resolved else 0.0

    summary = {
        "trading_day": target_date,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "eodhd_resolved": eodhd_resolved,
        "marketstack_resolved": ms_resolved,
        "both_resolved": both_resolved,
        "by_flag": dict(by_flag),
        "ok_pct_of_both_resolved": round(ok_pct, 2),
        "ms_coverage_of_eodhd_pct": round(coverage_pct, 2),
        # Gate criteria
        "gate_1_coverage_ms_or_yahoo_of_eodhd_pct": round(coverage_pct, 2),
        "gate_2_ok_flag_pct": round(ok_pct, 2),
        "gate_2_meets_target": ok_pct >= GATE_2_TARGET,
        "gate_3_major_flags_today": by_flag.get("MAJOR", 0),
        # Gate 4 (composite agreement) is measured separately by calculate_index.py
        # against both vendor outputs; flagged here as not_yet_measured per day.
    }

    output = {
        "trading_day": target_date,
        "summary": summary,
        "rows": rows,
    }
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    # Console summary
    print()
    print("SUMMARY")
    print("  EODHD resolved:       {}".format(eodhd_resolved))
    print("  MarketStack resolved: {}  ({:.1f}% of EODHD)".format(ms_resolved, coverage_pct))
    print("  Both resolved:        {}".format(both_resolved))
    print("  Flag distribution:")
    for fl in ("OK", "DRIFT", "MAJOR"):
        n = by_flag.get(fl, 0)
        pct = n / both_resolved * 100 if both_resolved else 0
        marker = "  " if fl != "MAJOR" or n == 0 else " ⚠"
        print("    {:6s} {:>4d}  ({:5.1f}%){}".format(fl, n, pct, marker))
    print()
    print("  Gate 1 (coverage): {:.2f}% {}".format(
        coverage_pct, "MET" if coverage_pct >= 99 else "BELOW 99%"))
    print("  Gate 2 (OK pct):   {:.2f}% {}".format(
        ok_pct, "MET" if ok_pct >= GATE_2_TARGET else "BELOW 95%"))
    print("  Gate 3 (MAJOR today): {}{}".format(
        by_flag.get("MAJOR", 0), " ⚠" if by_flag.get("MAJOR", 0) else ""))
    print()
    print("  Output: {}".format(out_path.relative_to(ROOT)))
    print("=" * 60)

    # Surface top-5 worst MAJOR offenders for quick scan
    majors = sorted(
        [r for r in rows if r["flag"] == "MAJOR"],
        key=lambda r: abs(r["delta_pct"]),
        reverse=True,
    )
    if majors:
        print("\nTop MAJOR offenders (worst 10):")
        for r in majors[:10]:
            print("  {:12s} EODHD {:>10} vs MS {:>10}  delta {:+8.2f}%  {}".format(
                r["ticker"], r["eodhd_close"], r["marketstack_close"],
                r["delta_pct"], r.get("eodhd_date") or "?"))


if __name__ == "__main__":
    main()
