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
EDGE_TOL = 0.015      # |scale_before/scale_after − 1| over this ⇒ inconsistent ⇒ try convergence-anchor, else surface
CONV_TOL = 0.01       # convergence-anchor: an after-edge MS bar with |MS/Yahoo − 1| < this is "convergent"
CONV_MAX_BARS = 8     #   ...search this many MS bars forward from the resume bar for re-convergence
START = "2021-06-01"  # only consider holes within the Yahoo-reachable window
MATERIAL_WT = 0.05    # a surfaced/errored (UNFILLABLE) hole at >= this weight % is "material"
                      # — never let a material constituent's hole be silently left behind (#64 follow-up)
PERSIST_DAYS = 14     # only a material hole STILL OPEN > this many days after its resume date
                      # halts the run (exit 3). A fresh gap (may self-heal next run) is persisted +
                      # reported but does NOT halt the pipeline.


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


def _converge_after(series, yusd, d_after, conv_tol=CONV_TOL, max_bars=CONV_MAX_BARS):
    """Convergence-anchor (#64 follow-up): when a gap's AFTER edge is off because the post-void
    MS RESUME bar(s) are noisy — not a persistent level shift — walk forward over the first
    `max_bars` MS bars from the resume date and return (conv_date, sa) at the first bar where
    MS/Yahoo RE-CONVERGES (|MS/Yahoo − 1| < conv_tol). Returns None if it never converges →
    a GENUINE persistent level disagreement (possible un-captured corp action) → caller must
    REFUSE (surface). At the handback the Yahoo fill is extended THROUGH the noisy resume bar(s)
    and control returns to MS at conv_date (dry-run-validated: 3037 TT/3436 JP/ARU AU)."""
    for d in sorted(d for d in series if d >= d_after)[:max_bars]:
        yv = yusd.get(d)
        if yv and abs(series[d]["close"] / yv - 1.0) < conv_tol:
            return d, series[d]["close"] / yv
    return None


def _converge_before(series, yusd, d_before, conv_tol=CONV_TOL, max_bars=CONV_MAX_BARS):
    """Mirror of `_converge_after` for a noisy ENTRY bar: walk BACKWARD over the first
    `max_bars` MS bars ending at d_before and return (conv_date, sb) at the first bar
    (closest to the gap, walking back) where MS/Yahoo re-converges (|MS/Yahoo − 1| <
    conv_tol). Returns None if it never converges → a GENUINE entry-level shift → caller
    must REFUSE (surface). At the handback the noisy entry bar(s) in (conv_date, d_after)
    are overwritten by the Yahoo fill, anchoring the before edge at conv_date — the
    symmetric counterpart of the resume-bar overwrite (dry-run-validated: 6506 JP)."""
    for d in sorted((d for d in series if d <= d_before), reverse=True)[:max_bars]:
        yv = yusd.get(d)
        if yv and abs(series[d]["close"] / yv - 1.0) < conv_tol:
            return d, series[d]["close"] / yv
    return None


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
        d_anchor_before, d_anchor_after = d_before, d_after
        if sb and sa and abs(sb / sa - 1.0) > EDGE_TOL:
            # Both edges present but inconsistent. Resolve whichever EDGE bar is the noisy one
            # via a convergence walk — AFTER-edge resume-bar noise forward (the 3 summer holes),
            # BEFORE-edge entry-bar noise backward (6506 JP). An edge already ~1.0 anchors as-is;
            # a noisy edge's bar(s) are overwritten by the Yahoo fill. If a noisy edge never
            # re-converges it is a GENUINE level disagreement (possible un-captured corp action)
            # → REFUSE (surface). Symmetric so neither entry- nor exit-edge noise is left behind.
            if abs(sa - 1.0) > CONV_TOL:
                conv = _converge_after(series, yusd, d_after)
                if conv is None:
                    surfaced.append({"window": [d_before, d_after], "days": gd,
                        "reason": "after-edge sa={:.4f} — PERSISTENT (no fwd convergence within "
                                  "{} bars; corp action / level shift?)".format(sa, CONV_MAX_BARS)})
                    continue
                d_anchor_after, sa = conv
            if abs(sb - 1.0) > CONV_TOL:
                conv = _converge_before(series, yusd, d_before)
                if conv is None:
                    surfaced.append({"window": [d_before, d_after], "days": gd,
                        "reason": "before-edge sb={:.4f} — PERSISTENT (no bwd convergence within "
                                  "{} bars; corp action / level shift?)".format(sb, CONV_MAX_BARS)})
                    continue
                d_anchor_before, sb = conv
            if abs(sb / sa - 1.0) > EDGE_TOL:   # edges still disagree after convergence
                surfaced.append({"window": [d_before, d_after], "days": gd,
                    "reason": "edge-scale persists after convergence sb@{}={:.4f} sa@{}={:.4f}"
                              .format(d_anchor_before, sb, d_anchor_after, sa)})
                continue
            # Fill ALL Yahoo dates between the (possibly re-anchored) edges: gap-interior INSERTS
            # + noisy edge-bar OVERWRITES, audited via _overwrite / _orig_ms_close.
            interior = [d for d in ydates if d_anchor_before < d < d_anchor_after]
        d_handback = d_anchor_after
        scale = math.sqrt(sb * sa) if (sb and sa) else (sb or sa or 1.0)
        for d in interior:
            bar = ynat[d]
            def cv(k):
                v = bar.get(k)
                return round(cc.to_usd(v, nccy, d) * scale, 6) if v else None
            fb = {"date": d, "open": cv("open"), "high": cv("high"),
                  "low": cv("low"), "close": round(yusd[d] * scale, 6),
                  "volume": bar.get("volume"), "_source": "yahoo-gapfill"}
            if d in series:   # convergence-anchor overwrite of a noisy resume bar (audited)
                fb["_overwrite"] = True
                fb["_orig_ms_close"] = series[d].get("close")
            fills.append(fb)
        n_ins = sum(1 for d in interior if d not in series)
        fill_windows.append({"window": [d_anchor_before, d_handback], "days": gd,
                             "n_fill": n_ins, "n_overwrite": len(interior) - n_ins,
                             "handback": (d_handback if d_handback != d_after else None),
                             "entry_anchor": (d_anchor_before if d_anchor_before != d_before else None),
                             "edge_scale": round(scale, 5),
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
    # Holes detected but nothing to fill: every gap is a real holiday Yahoo also lacks,
    # so the flat carry-forward is CORRECT (not a hole). Tracked so a material constituent
    # with a genuinely UNFILLED hole (errored/surfaced) is never silently left flat.
    noop = [r for r in results if not r.get("fills") and not r.get("surfaced") and not r.get("error")]
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
        print("\nERRORED — Yahoo/symbol fetch failed (hole left UNFILLED — surface if material):")
        for r in sorted(errored, key=lambda r: -(r["weight"] or 0)):
            print("  {:11} w={:>6.3f}  {}".format(r["ticker"], r["weight"] or 0, r["error"]))
    if noop:
        mx = max((r["weight"] or 0) for r in noop)
        print("\nHOLES but 0 fillable bars — every detected gap is a holiday Yahoo also lacks, so "
              "flat carry-forward is CORRECT (NOT an unfilled hole): {} names, max wt {:.3f}%".format(
                  len(noop), mx))
        for r in sorted(noop, key=lambda r: -(r["weight"] or 0))[:8]:
            print("  {:11} w={:>6.3f}  ({} holiday gaps)".format(r["ticker"], r["weight"] or 0, r["n_gaps"]))

    if args.apply:
        n = 0
        for r in fillable:
            hpath = HISTORY / (fn(r["ticker"]) + ".json")
            h = json.loads(hpath.read_text())
            by_date = {b["date"]: b for b in h.get("series", [])}
            for fb in r["fills"]:
                # Insert new bars; overwrite an existing MS bar ONLY when explicitly tagged
                # (a convergence-anchor noisy-resume overwrite — the orig MS close is retained
                # in fb["_orig_ms_close"] for audit). Plain interior fills never overwrite.
                if fb["date"] not in by_date or fb.get("_overwrite"):
                    by_date[fb["date"]] = fb
            h["series"] = [by_date[d] for d in sorted(by_date)]
            n_ovr = sum(1 for fb in r["fills"] if fb.get("_overwrite"))
            h["_gapfill"] = {"filled_bars": len(r["fills"]), "inserts": len(r["fills"]) - n_ovr,
                             "overwrites": n_ovr,
                             "source": "yahoo (ECB FX, edge-anchored; convergence-anchor handback)",
                             "windows": r["fill_windows"], "at": "#64+conv"}
            hpath.write_text(json.dumps(h, indent=2))
            n += 1
        print("\nAPPLIED: filled {} names. NEXT: calculate_index + verify_index_reconstruction (Δ=0) + §12.6.".format(n))
    else:
        # Per-name hole RECURRENCE registry (#64): MS holes are permanent, so a name that
        # recurs in this weekly surface is a chronic-holer → candidate for daily Yahoo-routing
        # (monitor-then-DECIDE; no auto-routing here). Only the standing --dry accrues it.
        from datetime import datetime, timezone
        REC = ROOT / "data" / "markets" / "ms_gap_recurrence.json"
        try:
            reg = json.loads(REC.read_text()) if REC.exists() else {"_meta": {"runs": 0}, "names": {}}
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            for r in results:
                if r.get("error"):
                    continue
                tk = r["ticker"]
                e = reg["names"].setdefault(tk, {"runs_with_hole": 0, "first_seen": today})
                e["runs_with_hole"] = e.get("runs_with_hole", 0) + 1
                e["last_seen"] = today
                e["weight_pct"] = r.get("weight")
            reg["_meta"] = {"runs": reg["_meta"].get("runs", 0) + 1, "last_run": today,
                            "chronic_threshold": 4,
                            "note": "runs_with_hole >= chronic_threshold = chronic-holer, "
                                    "candidate for daily Yahoo-routing (monitor-then-decide)"}
            REC.write_text(json.dumps(reg, indent=2))
            chronic = sorted(tk for tk, e in reg["names"].items()
                             if e.get("runs_with_hole", 0) >= reg["_meta"]["chronic_threshold"])
            if chronic:
                print("\nCHRONIC HOLERS (>={} weekly runs with a hole — Yahoo-routing candidates): {}".format(
                    reg["_meta"]["chronic_threshold"], ", ".join(chronic)))
        except Exception as exc:
            print("  recurrence registry update skipped ({})".format(str(exc)[:60]))
        print("\nDRY — nothing written to history. Checkpoint this scope, then --apply.")

    # ── LOUD UNFILLED-HOLE SURFACE (#64 follow-up) ───────────────────────────
    # A SURFACED (edge-scale mismatch) or ERRORED (no symbol/ccy, Yahoo fail) hole
    # is a constituent we could NOT fill. #64 printed these to stdout in --apply and
    # they were then LOST: 3037 TT / 3436 JP / ARU AU rode an unfilled 39d hole (a
    # +43% carry-forward blip) on the PUBLISHED track for a year, uncaught. Persist
    # the unfillable set durably (BOTH modes) and ERROR LOUDLY (exit 3) on any one at
    # >= MATERIAL_WT, so a material constituent's hole can never again be silently
    # left behind. (Filling them is a deliberate out-of-band step — anchor to the
    # clean edge + reconcile the off-edge resume bar — NOT an auto-fill here.)
    from datetime import datetime, timezone
    unfilled = []
    for r in surfaced:
        for s in r.get("surfaced", []):
            unfilled.append({"ticker": r["ticker"], "weight_pct": r.get("weight"),
                             "kind": "surfaced", "window": s.get("window"),
                             "reason": s.get("reason")})
    for r in errored:
        unfilled.append({"ticker": r["ticker"], "weight_pct": r.get("weight"),
                         "kind": "errored", "reason": r.get("error")})
    # Classify each unfillable hole: material (weight) AND persistent (still open > PERSIST_DAYS
    # after its resume date). The two gates are separate on purpose — a FRESH multi-day gap at
    # the tail (resume within PERSIST_DAYS) may self-heal on the next run, so it must not halt
    # the pipeline; an OLD one (the 3037/3436/ARU class) must. Errored = no window = hard fail,
    # always persistent. ALL unfilled holes are persisted regardless of either gate.
    today = datetime.now(timezone.utc).date()
    def _hole_age(u):
        w = u.get("window")
        if not w:
            return None  # errored: no resume date
        try:
            return (today - datetime.strptime(w[1], "%Y-%m-%d").date()).days
        except Exception:
            return None
    for u in unfilled:
        u["hole_age_days"] = _hole_age(u)
        u["material"] = (u.get("weight_pct") or 0) >= MATERIAL_WT
        u["persistent"] = (u["kind"] == "errored") or (
            u["hole_age_days"] is not None and u["hole_age_days"] > PERSIST_DAYS)
    UNFILLED_PATH = ROOT / "data" / "markets" / "ms_gap_unfilled.json"
    try:
        UNFILLED_PATH.write_text(json.dumps({
            "_meta": {"updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                      "mode": "apply" if args.apply else "dry",
                      "material_wt_threshold_pct": MATERIAL_WT, "persist_days": PERSIST_DAYS,
                      "note": "Every hole that could NOT be filled (surfaced edge-mismatch / "
                              "errored symbol|ccy|yahoo) is persisted here so none is ever "
                              "silently skipped. The run exits non-zero ONLY on a hole that is "
                              "BOTH material (>= threshold wt) AND persistent (open > persist_days "
                              "/ errored) — fresh gaps may self-heal and do not halt."},
            "unfilled": sorted(unfilled, key=lambda u: -(u.get("weight_pct") or 0)),
        }, indent=2))
    except Exception as exc:
        print("  WARN: could not persist ms_gap_unfilled.json ({})".format(str(exc)[:60]))
    material = [u for u in unfilled if u["material"]]
    halting = [u for u in material if u["persistent"]]
    fresh_material = [u for u in material if not u["persistent"]]
    if unfilled:
        print("\nUNFILLED HOLES (persisted to data/markets/ms_gap_unfilled.json): {} total, "
              "{} material, {} material+persistent".format(len(unfilled), len(material), len(halting)))
    if fresh_material:
        print("  {} material but FRESH hole(s) — reported, NOT halting (may self-heal next run): {}"
              .format(len(fresh_material), ", ".join(u["ticker"] for u in fresh_material)))
    if halting:
        print("!" * 76)
        print("MATERIAL + PERSISTENT UNFILLED HOLE(S) — {} constituent(s) >= {}% weight, open > {}d, "
              "could NOT be filled:".format(len(halting), MATERIAL_WT, PERSIST_DAYS))
        for u in sorted(halting, key=lambda u: -(u.get("weight_pct") or 0)):
            age = u.get("hole_age_days")
            print("  {:11} w={:>6.3f}  {:8} age={:>5}  {}".format(
                u["ticker"], u.get("weight_pct") or 0, u["kind"],
                ("{}d".format(age) if age is not None else "n/a"), (u.get("reason") or "")[:50]))
        print("Resolve out-of-band (anchor-to-clean-edge + resume-bar convergence), then re-run.")
        print("!" * 76)
        sys.exit(3)


if __name__ == "__main__":
    main()
