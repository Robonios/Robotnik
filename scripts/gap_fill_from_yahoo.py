#!/usr/bin/env python3
"""
Gap-fill MarketStack coverage holes from Yahoo (#64) — and the standing contiguity guard.
=========================================================================================
MarketStack has recurring multi-week holes in international (esp. Asian) coverage —
e.g. 2025-06-20→07-29 (39d, ~12% index weight: Japan/China/Korea/Taiwan), a 2025-05
window (~10%), 2026-02 (China), etc. The freshness floor catches a stale TAIL; it does
NOT catch a hole in the MIDDLE of an active series. This closes that gap.

Self-classifying: a real market holiday is missing from BOTH MarketStack and Yahoo, so
it is never "filled"; only genuine MS holes (Yahoo has the trading day, MS does not) get
filled.

Fill correctness (the two must-haves):
  (i)  Yahoo RAW native prices converted through the SAME ECB FX layer
       (currency_convert.to_usd), NOT Yahoo's own USD — else the spot-vs-fixing seam
       (the Condition-2 issue) would re-enter INSIDE the gaps.
  (ii) Boundary continuity: anchor-scale the Yahoo fill to the MS bar at EACH gap edge.
       If the two edges imply inconsistent scale factors (a corporate action inside the
       gap, or MS/Yahoo on different adjustment bases), DO NOT fill — SURFACE instead.
       A fill that introduces a step at the boundary is worse than the flat carry-forward
       it replaces.

Modes:
  --dry    (default) report every fillable gap (name, window, n bars, edge-scale, weight)
  --apply  write fills into data/prices/history/ (merge; existing bars untouched, fills
           tagged "_source":"yahoo-gapfill"); then re-run calculate_index + verify.

Standing use: run --dry periodically (out-of-band; Yahoo is CI-blocked) to SURFACE new
holes — the contiguity guard the freshness floor cannot provide.
"""
import argparse
import json
import math
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from fetch_prices import EQUITIES
from fetch_yahoo import fetch_yahoo_daily, YahooFetchError
import currency_convert as cc

HISTORY = ROOT / "data" / "prices" / "history"
WEIGHTS = ROOT / "data" / "index" / "weights.json"
GAP_DAYS = 7          # a span > this between consecutive bars = a candidate hole
EDGE_TOL = 0.015      # |scale_before/scale_after − 1| over this ⇒ inconsistent ⇒ surface, don't fill
START = "2021-06-01"  # only consider holes within the Yahoo-reachable window


def fn(t):
    return t.replace(" ", "_").replace("/", "_")


def load_weights():
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


def _dd(a, b):
    return (datetime.strptime(a, "%Y-%m-%d") - datetime.strptime(b, "%Y-%m-%d")).days


def find_gaps(dates, gap_days=GAP_DAYS):
    out = []
    for i in range(1, len(dates)):
        if _dd(dates[i], dates[i - 1]) > gap_days:
            out.append((dates[i - 1], dates[i], _dd(dates[i], dates[i - 1])))
    return out


def process(ticker, weight):
    """Return a per-name result dict (gaps, fills, surfaced) — read-only (no write)."""
    hpath = HISTORY / (fn(ticker) + ".json")
    if not hpath.exists():
        return None
    h = json.loads(hpath.read_text())
    series = {b["date"]: b for b in h.get("series", []) if b.get("close")}
    dates = sorted(d for d in series if d >= START)
    gaps = [g for g in find_gaps(dates) if g[0] >= START]
    if not gaps:
        return None

    ysym = h.get("marketstack_symbol") or h.get("yahoo_symbol")
    nccy = h.get("native_currency")
    if not ysym or not nccy:
        return {"ticker": ticker, "weight": weight, "error": "no symbol/currency"}
    try:
        y = fetch_yahoo_daily(ysym, output_size="5y").get("series", {})
    except (YahooFetchError, Exception) as e:
        return {"ticker": ticker, "weight": weight, "error": "yahoo:" + str(e)[:60]}

    # MUST-HAVE (i): Yahoo RAW native → ECB FX via cc.to_usd (NOT Yahoo USD).
    yusd, ynat = {}, {}
    for d, bar in y.items():
        c = bar.get("close")
        if c:
            ynat[d] = bar
            try:
                yusd[d] = cc.to_usd(c, nccy, d)
            except cc.CurrencyError:
                pass
    ydates = sorted(yusd)

    def near(target, side):
        cands = [d for d in ydates if (d <= target if side < 0 else d >= target)]
        return (max(cands) if side < 0 else min(cands)) if cands else None

    fills, surfaced, fill_windows = [], [], []
    for d_before, d_after, gd in gaps:
        interior = [d for d in ydates if d_before < d < d_after and d not in series]
        if not interior:
            continue  # holiday: Yahoo also lacks it → nothing to fill (self-classifying)
        # MUST-HAVE (ii): anchor-scale at BOTH edges; refuse if inconsistent.
        ab, aa = near(d_before, -1), near(d_after, +1)
        sb = (series[d_before]["close"] / yusd[ab]) if (ab and yusd.get(ab)) else None
        sa = (series[d_after]["close"] / yusd[aa]) if (aa and yusd.get(aa)) else None
        if sb and sa and abs(sb / sa - 1.0) > EDGE_TOL:
            surfaced.append({"window": [d_before, d_after], "days": gd,
                             "reason": "edge-scale mismatch sb={:.4f} sa={:.4f} "
                                       "(corp action in gap?)".format(sb, sa)})
            continue
        scale = math.sqrt(sb * sa) if (sb and sa) else (sb or sa or 1.0)
        for d in interior:
            bar = ynat[d]
            def cv(k):
                v = bar.get(k)
                return round(cc.to_usd(v, nccy, d) * scale, 6) if v else None
            fills.append({"date": d, "open": cv("open"), "high": cv("high"),
                          "low": cv("low"), "close": round(yusd[d] * scale, 6),
                          "volume": bar.get("volume"), "_source": "yahoo-gapfill"})
        fill_windows.append({"window": [d_before, d_after], "days": gd,
                             "n_fill": len(interior), "edge_scale": round(scale, 5),
                             "scale_consistent": (None if not (sb and sa) else round(sb / sa, 4))})
    return {"ticker": ticker, "weight": weight, "ysym": ysym, "native_ccy": nccy,
            "n_gaps": len(gaps), "fills": fills, "fill_windows": fill_windows,
            "surfaced": surfaced}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write the fills (default: dry report)")
    ap.add_argument("--only", default="", help="comma-separated ticker filter")
    args = ap.parse_args()
    only = {s.strip() for s in args.only.split(",") if s.strip()} or None
    weights = load_weights()

    # Only names that HAVE a local gap need a Yahoo fetch (efficient).
    universe = [(tk, weights.get(tk, 0.0)) for (tk, *_r) in EQUITIES if (only is None or tk in only)]
    results, n_fetch = [], 0
    for tk, w in universe:
        hpath = HISTORY / (fn(tk) + ".json")
        if not hpath.exists():
            continue
        ser = sorted(b["date"] for b in json.loads(hpath.read_text()).get("series", []) if b.get("close"))
        if not [g for g in find_gaps([d for d in ser if d >= START]) if g[0] >= START]:
            continue  # no gap → skip (no Yahoo call)
        r = process(tk, w)
        n_fetch += 1
        if r:
            results.append(r)

    fillable = [r for r in results if r.get("fills")]
    surfaced = [r for r in results if r.get("surfaced")]
    errored = [r for r in results if r.get("error")]
    tot_w = sum(r["weight"] or 0 for r in fillable)
    tot_bars = sum(len(r["fills"]) for r in fillable)

    print("=" * 76)
    print("GAP-FILL {} — {} names with holes (Yahoo-fetched), {} fillable, Σwt {:.2f}%, {} bars".format(
        "APPLY" if args.apply else "DRY", n_fetch, len(fillable), tot_w, tot_bars))
    print("=" * 76)
    for r in sorted(fillable, key=lambda r: -(r["weight"] or 0)):
        wins = "; ".join("{}→{}({}d,{}bar,scale {})".format(
            w["window"][0], w["window"][1], w["days"], w["n_fill"], w["edge_scale"])
            for w in r["fill_windows"])
        print("  {:11} w={:>6.3f}  {} bars | {}".format(r["ticker"], r["weight"] or 0,
                                                        len(r["fills"]), wins))
    if surfaced:
        print("\nSURFACED (edge-scale mismatch — NOT filled, needs review / corp-action route):")
        for r in surfaced:
            for s in r["surfaced"]:
                print("  {:11} {} {}".format(r["ticker"], s["window"], s["reason"]))
    if errored:
        print("\nERRORED (Yahoo/symbol):", ", ".join("{}({})".format(r["ticker"], r["error"]) for r in errored))

    if args.apply:
        n = 0
        for r in fillable:
            hpath = HISTORY / (fn(r["ticker"]) + ".json")
            h = json.loads(hpath.read_text())
            by_date = {b["date"]: b for b in h.get("series", [])}
            for fb in r["fills"]:
                if fb["date"] not in by_date:   # never overwrite an existing MS bar
                    by_date[fb["date"]] = fb
            h["series"] = [by_date[d] for d in sorted(by_date)]
            h["_gapfill"] = {"filled_bars": len(r["fills"]), "source": "yahoo (ECB FX, edge-anchored)",
                             "windows": r["fill_windows"], "at": "#64"}
            hpath.write_text(json.dumps(h, indent=2))
            n += 1
        print("\nAPPLIED: filled {} names. NEXT: calculate_index + verify_index_reconstruction (Δ=0) + §12.6.".format(n))
    else:
        print("\nDRY — nothing written. Checkpoint this scope, then --apply.")


if __name__ == "__main__":
    main()
