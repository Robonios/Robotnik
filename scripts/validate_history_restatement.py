#!/usr/bin/env python3
"""
Per-name history restatement validator (#55) — staging vs committed.
====================================================================
Compares the staged v2-native 5Y history (data/prices/history_v2_staging/)
against the committed v1+MIC history (data/prices/history/) for EVERY name,
across the WHOLE series, and classifies every divergence so the restatement can
be explained name-by-name (NO blanket re-baseline) before the index regen.

The index is chain-linked on daily RETURNS, so the decisive distinction is:

  • LEVEL restatement  — a (near-)constant staged/committed price ratio. Changes
    the displayed price chart for that name but, because a constant scale cancels
    in a return, moves the index by ~0. This is the agorot ÷100 (SCC) and clean
    cross-listing/FX-basis class.
  • RETURN restatement — the daily-return SHAPE differs (split-realignment steps,
    a genuinely different instrument, or the stale-tail un-freeze adding bars the
    committed series never had). THIS is what actually moves the track record.

So per name we report median level-ratio (level move) AND the overlap cumulative-
return difference + the post-committed tail (return move), weight each by the
index weight, and surface:
  - coverage-short: staging does NOT reach as far back as committed → the v2
    symbol lost its predecessor's pre-change history (Schaeffler/Hiab/JBT class)
    → stitch or a documented, surfaced gap.
  - dropped / new names, and high-dispersion ratios needing individual review.

Read-only. Writes a report to data/prices/history_restatement_report.json.

Usage:  python scripts/validate_history_restatement.py
"""
import json
import statistics as st
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from fetch_prices import EQUITIES

COMMITTED = ROOT / "data" / "prices" / "history"
STAGING = ROOT / "data" / "prices" / "history_v2_staging"
WEIGHTS = ROOT / "data" / "index" / "weights.json"
REPORT = ROOT / "data" / "prices" / "history_restatement_report.json"

LEVEL_TOL = 0.02      # |median ratio − 1| under this = no level restatement
RET_DIFF_TOL = 0.005  # per-day return diff under this = same return that day
COVERAGE_TOL_DAYS = 20  # staging earliest later than committed by more than this = short


def fname(t):
    return t.replace(" ", "_").replace("/", "_")


def load_series(path):
    """Return {date: close} for a history file, or {} if absent/unreadable."""
    if not path.exists():
        return {}
    try:
        d = json.loads(path.read_text())
        return {r["date"]: float(r["close"]) for r in d.get("series", [])
                if r.get("close") is not None and r.get("date")}
    except Exception:
        return {}


def load_weights():
    """Robustly pull {ticker: weight_pct} from weights.json whatever the nesting."""
    try:
        W = json.loads(WEIGHTS.read_text())
    except Exception:
        return {}
    out = {}

    def rec(o):
        if isinstance(o, list):
            for x in o:
                rec(x)
        elif isinstance(o, dict):
            if "ticker" in o and ("weight_pct" in o or "weight" in o):
                out[o["ticker"]] = o.get("weight_pct", o.get("weight"))
            else:
                for v in o.values():
                    rec(v)
    rec(W)
    return out


def cumret(closes_by_date, dates):
    """Compounded return across `dates` (ascending) = c_last/c_first − 1."""
    if len(dates) < 2:
        return 0.0
    c0, c1 = closes_by_date[dates[0]], closes_by_date[dates[-1]]
    return (c1 / c0 - 1.0) if c0 else 0.0


def analyse(tk, weight):
    com = load_series(COMMITTED / (fname(tk) + ".json"))
    stg = load_series(STAGING / (fname(tk) + ".json"))
    rec = {"ticker": tk, "weight_pct": weight,
           "n_committed": len(com), "n_staged": len(stg)}
    if not stg and not com:
        rec["class"] = "absent_both"
        return rec
    if not stg:
        rec["class"] = "dropped_in_staging"   # had committed history, none staged
        return rec
    if not com:
        rec["class"] = "new_in_staging"        # no prior history (recent add)
        rec["staged_range"] = [min(stg), max(stg)]
        return rec

    com_dates, stg_dates = sorted(com), sorted(stg)
    overlap = sorted(set(com) & set(stg))
    rec["committed_range"] = [com_dates[0], com_dates[-1]]
    rec["staged_range"] = [stg_dates[0], stg_dates[-1]]
    rec["n_overlap"] = len(overlap)

    # ── coverage ──
    def dd(a, b):
        return (datetime.strptime(a, "%Y-%m-%d") - datetime.strptime(b, "%Y-%m-%d")).days
    back_short = dd(stg_dates[0], com_dates[0])     # >0 ⇒ staging starts later (lost depth)
    tail_ahead = dd(stg_dates[-1], com_dates[-1])   # >0 ⇒ staging extends past committed
    rec["coverage_back_short_days"] = back_short
    rec["coverage_tail_ahead_days"] = tail_ahead

    if not overlap:
        rec["class"] = "no_overlap"
        return rec

    # ── level ratio on overlap ──
    ratios = [stg[d] / com[d] for d in overlap if com[d]]
    med = st.median(ratios) if ratios else None
    p5 = ratios[max(0, int(0.05 * len(ratios)))] if ratios else None
    p95 = ratios[min(len(ratios) - 1, int(0.95 * len(ratios)))] if ratios else None
    sr = sorted(ratios)
    p5, p95 = (sr[max(0, int(0.05 * len(sr)))], sr[min(len(sr) - 1, int(0.95 * len(sr)))]) if sr else (None, None)
    rec["median_level_ratio"] = round(med, 6) if med else None
    rec["ratio_p5_p95"] = [round(p5, 4), round(p95, 4)] if p5 else None
    rec["ratio_dispersion"] = round((p95 / p5), 4) if (p5 and p95 and p5 > 0) else None

    # ── return-shape diff on overlap (constant scale cancels → isolates real move) ──
    ov_com_ret = cumret(com, overlap)
    ov_stg_ret = cumret(stg, overlap)
    rec["overlap_cumret_committed"] = round(ov_com_ret, 6)
    rec["overlap_cumret_staged"] = round(ov_stg_ret, 6)
    rec["overlap_cumret_diff"] = round(ov_stg_ret - ov_com_ret, 6)
    # per-day return divergence count (step-discontinuity / split-realignment finder)
    daydiffs = []
    for i in range(1, len(overlap)):
        d0, d1 = overlap[i - 1], overlap[i]
        if com[d0] and stg[d0]:
            rc = com[d1] / com[d0] - 1.0
            rs = stg[d1] / stg[d0] - 1.0
            if abs(rs - rc) > RET_DIFF_TOL:
                daydiffs.append((d1, round(rs - rc, 4)))
    rec["n_days_return_diff"] = len(daydiffs)
    rec["max_day_return_diff"] = max((abs(x[1]) for x in daydiffs), default=0.0)
    rec["worst_return_diff_days"] = sorted(daydiffs, key=lambda x: -abs(x[1]))[:5]

    # ── tail un-freeze: bars staged AFTER committed's last date ──
    tail = [d for d in stg_dates if d > com_dates[-1]]
    if len(tail) >= 1 and com_dates[-1] in stg:
        td = [com_dates[-1]] + tail
        rec["tail_days"] = len(tail)
        rec["tail_cumret"] = round((stg[td[-1]] / stg[td[0]] - 1.0), 6) if stg[td[0]] else None
    else:
        rec["tail_days"] = len(tail)
        rec["tail_cumret"] = None

    # ── classify ──
    level_moved = med is not None and abs(med - 1.0) > LEVEL_TOL
    return_moved = abs(rec["overlap_cumret_diff"]) > RET_DIFF_TOL or rec["n_days_return_diff"] > 0
    cls = []
    if back_short > COVERAGE_TOL_DAYS:
        cls.append("coverage_short")
    if tail_ahead > COVERAGE_TOL_DAYS or rec["tail_days"] > 3:
        cls.append("tail_unfreeze")
    if level_moved:
        # near-constant ratio (low dispersion) = clean unit/listing restatement
        if rec["ratio_dispersion"] and rec["ratio_dispersion"] < 1.15:
            cls.append("level_restatement_constant")
        else:
            cls.append("level_restatement_variable")
    if return_moved and rec["n_days_return_diff"] > 0:
        cls.append("return_shape_diff")
    if not cls:
        cls.append("unchanged")
    rec["class"] = "+".join(cls)
    return rec


def main():
    weights = load_weights()
    rows = [analyse(tk, weights.get(tk)) for (tk, *_rest) in EQUITIES]

    # index-impact proxy: weight × return move (level-only restatements ≈ 0 impact)
    def wf(r):
        w = r.get("weight_pct")
        return (w / 100.0) if isinstance(w, (int, float)) else 0.0
    restate_impact = sum(wf(r) * (r.get("overlap_cumret_diff") or 0.0) for r in rows)
    restate_gross = sum(abs(wf(r) * (r.get("overlap_cumret_diff") or 0.0)) for r in rows)
    tail_impact = sum(wf(r) * (r.get("tail_cumret") or 0.0) for r in rows)

    from collections import Counter
    classes = Counter()
    for r in rows:
        for c in (r.get("class") or "").split("+"):
            classes[c] += 1

    REPORT.write_text(json.dumps({
        "_meta": {"validated_at": datetime.now(timezone.utc).isoformat() + "Z",
                  "committed_dir": str(COMMITTED.relative_to(ROOT)),
                  "staging_dir": str(STAGING.relative_to(ROOT)),
                  "n_names": len(rows),
                  "class_counts": dict(classes),
                  "weighted_restatement_impact_overlap_net": round(restate_impact, 6),
                  "weighted_restatement_impact_overlap_gross": round(restate_gross, 6),
                  "weighted_tail_unfreeze_impact": round(tail_impact, 6)},
        "names": rows}, indent=2))

    # ── console summary ──
    print("=" * 72)
    print("HISTORY RESTATEMENT VALIDATION — staging(v2) vs committed(v1)  [{} names]".format(len(rows)))
    print("=" * 72)
    print("class counts:")
    for c, n in classes.most_common():
        print("  {:30} {}".format(c, n))

    def has(r, c):
        return c in (r.get("class") or "")

    cov = [r for r in rows if has(r, "coverage_short")]
    print("\nCOVERAGE-SHORT (staging loses pre-change depth → STITCH or documented gap) — {}:".format(len(cov)))
    for r in sorted(cov, key=lambda r: -(r.get("coverage_back_short_days") or 0)):
        print("  {:11} committed {} staged {}  (+{}d later start)  w={}".format(
            r["ticker"], r.get("committed_range", ["?"])[0], r.get("staged_range", ["?"])[0],
            r.get("coverage_back_short_days"), r.get("weight_pct")))

    rsd = [r for r in rows if has(r, "return_shape_diff")]
    print("\nRETURN-SHAPE DIFF (moves the index — individual explanation required) — {}:".format(len(rsd)))
    for r in sorted(rsd, key=lambda r: -abs((r.get("overlap_cumret_diff") or 0) * wf(r)))[:30]:
        print("  {:11} w={:>6}  overlap_cumret Δ={:+.3%}  n_day_diff={} max_day={:+.2%}  medratio={}".format(
            r["ticker"], r.get("weight_pct"), r.get("overlap_cumret_diff") or 0,
            r.get("n_days_return_diff"), r.get("max_day_return_diff") or 0,
            r.get("median_level_ratio")))

    lrv = [r for r in rows if has(r, "level_restatement_variable")]
    print("\nLEVEL-RESTATEMENT-VARIABLE (non-constant ratio — possible split/instrument issue) — {}:".format(len(lrv)))
    for r in sorted(lrv, key=lambda r: -(r.get("ratio_dispersion") or 0))[:20]:
        print("  {:11} medratio={} dispersion={} range com{} stg{}".format(
            r["ticker"], r.get("median_level_ratio"), r.get("ratio_dispersion"),
            r.get("committed_range"), r.get("staged_range")))

    drop = [r for r in rows if has(r, "dropped_in_staging")]
    if drop:
        print("\nDROPPED IN STAGING (had committed history, none staged) — {}: {}".format(
            len(drop), ", ".join(r["ticker"] for r in drop)))

    print("\nLEVEL-only restatements (constant ratio, ~0 index impact) — {}: examples:".format(
        sum(1 for r in rows if has(r, "level_restatement_constant"))))
    for r in [r for r in rows if has(r, "level_restatement_constant")][:12]:
        print("  {:11} medratio={:>10}  (e.g. agorot/pence/listing — level only)".format(
            r["ticker"], r.get("median_level_ratio")))

    print("\n" + "-" * 72)
    print("WEIGHTED index impact (proxy for since-inception move):")
    print("  existing-history restatement, NET   (overlap return Δ × weight): {:+.4%}".format(restate_impact))
    print("  existing-history restatement, GROSS (Σ|return Δ × weight|):      {:.4%}".format(restate_gross))
    print("  stale-tail un-freeze (intermediate bars × weight):              {:+.4%}".format(tail_impact))
    print("  NOTE: today's index LEVEL is already set by the daily cutover (06-04 values); this")
    print("        re-backfill restates the historical CURVE (inception→05-22 path + fills the")
    print("        05-22→06-04 intermediate bars). calculate_index is the authoritative number.")
    print("\nReport: {}".format(REPORT.relative_to(ROOT)))


if __name__ == "__main__":
    main()
