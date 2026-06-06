#!/usr/bin/env python3
"""
Staged-v2 vs Yahoo price-return sweep (#55) — enumerate the corporate-action-miss class.
========================================================================================
MarketStack v2's `split_factor` captures stock splits but MISSES bonus / scrip /
rights attributions that Yahoo back-adjusts into its (split-adjusted, NOT
dividend-adjusted) `close`. The staged v2 history therefore UNDER-adjusts those
names. This sweep compares every v2-staged name to Yahoo's price-return close —
converting BOTH to USD via the SAME ECB FX so the FX layer CANCELS in the ratio,
isolating the pure corporate-action (price) difference — and classifies:

  corporate_action_miss : ratio CONVERGES (old ≠ 1, recent ≈ 1) → v2 missed a past
                          action, Yahoo is correct → ROUTE THIS NAME'S HISTORY TO YAHOO.
  persistent_divergence : ratio ~constant ≠ 1 (currency-label / instrument diff) →
                          REVIEW, do NOT auto-route (e.g. the agorot SCC, where v2 is
                          the CORRECT side — routing to a mislabelled Yahoo would regress it).
  recent_divergence     : recent ratio off → a recent action / recent staged error → review.
  clean                 : ratio ≈ 1.0 throughout → keep v2.

Twofold job (per the Option-B directive): (1) DEFINITIVELY enumerate the class — the
hand-confirmed names are NOT assumed complete; (2) RESOLVE the ambiguous-direction
names against Yahoo truth, especially 300124 (0.34% weight). Ships nothing — read-only;
writes data/prices/corporate_action_class.json for the Yahoo-restage step.

Usage:  python scripts/sweep_v2_vs_yahoo.py
"""
import json
import statistics as st
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from fetch_prices import EQUITIES
from fetch_yahoo import fetch_yahoo_daily, YahooFetchError
import currency_convert as cc

STAGING = ROOT / "data" / "prices" / "history_v2_staging"
MANIFEST = ROOT / "data" / "prices" / "history_v2_staging_manifest.json"
WEIGHTS = ROOT / "data" / "index" / "weights.json"
OUT = ROOT / "data" / "prices" / "corporate_action_class.json"

CONVERGE_TOL = 0.025   # |old ratio − 1| over this AND recent ≈ 1 ⇒ converging ⇒ v2 missed an action
RECENT_TOL = 0.02      # |recent ratio − 1| under this ⇒ staged & Yahoo agree NOW


def fname(t):
    return t.replace(" ", "_").replace("/", "_")


def load_series(path):
    if not path.exists():
        return {}
    try:
        d = json.loads(path.read_text())
        return {r["date"]: float(r["close"]) for r in d.get("series", [])
                if r.get("close") is not None and r.get("date")}
    except Exception:
        return {}


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


def med(xs):
    return st.median(xs) if xs else None


def main():
    import argparse
    from guard_corporate_actions import add_route, load_route
    ap = argparse.ArgumentParser()
    ap.add_argument("--history-dir", default=str(ROOT / "data" / "prices" / "history"),
                    help="history dir to audit (default: LIVE history — the STANDING weekly job; "
                         "pass the staging dir for a one-time pre-cutover enumeration)")
    ap.add_argument("--no-record", action="store_true",
                    help="analyse only; do NOT auto-maintain corporate_action_route.json")
    args = ap.parse_args()
    HDIR = Path(args.history_dir)
    weights = load_weights()
    already = set(load_route())   # already Yahoo-routed → correct source, skip

    # Enumerate v2-sourced names from each history file's `source` field, so this runs on the
    # LIVE history post-cutover (no staging manifest needed). Yahoo-sourced names (overrides +
    # already-routed corporate-action names) are already correct → skipped.
    v2_names = []
    for f in sorted(HDIR.glob("*.json")):
        try:
            d = json.loads(f.read_text())
        except Exception:
            continue
        tk, src, sym = d.get("ticker"), d.get("source", ""), d.get("marketstack_symbol")
        if tk and sym and src.startswith("MarketStack") and tk not in already:
            v2_names.append((tk, sym))
    print("=" * 72)
    print("v2-vs-YAHOO SWEEP — corporate-action-miss audit  [{} v2 names in {}/ | {} already routed]".format(
        len(v2_names), HDIR.name, len(already)))
    print("=" * 72)

    results = {}
    n_clean = n_ca = n_persist = n_recent = n_err = 0
    for i, (tk, sym) in enumerate(sorted(v2_names), 1):
        stg = load_series(HDIR / (fname(tk) + ".json"))
        if not stg:
            results[tk] = {"class": "no_staged"}
            continue
        try:
            y = fetch_yahoo_daily(sym, output_size="5y")
            yccy = y.get("currency")
            yusd = {}
            for d, bar in (y.get("series") or {}).items():
                c = bar.get("close")
                if c:
                    try:
                        yusd[d] = cc.to_usd(c, yccy, d)
                    except cc.CurrencyError:
                        pass
        except (YahooFetchError, Exception) as e:
            n_err += 1
            results[tk] = {"class": "yahoo_error", "err": str(e)[:80]}
            continue

        ov = sorted(set(stg) & set(yusd))
        if len(ov) < 80:
            results[tk] = {"class": "short_overlap", "n_overlap": len(ov)}
            continue
        ratios = [stg[d] / yusd[d] for d in ov if yusd[d]]
        old = med(ratios[:30])
        new = med(ratios[-30:])
        sr = sorted(ratios)
        disp = (sr[int(0.95 * len(sr))] / sr[int(0.05 * len(sr))]) if sr and sr[int(0.05 * len(sr))] else None

        recent_agree = new is not None and abs(new - 1.0) < RECENT_TOL
        old_off = old is not None and abs(old - 1.0) > CONVERGE_TOL
        if recent_agree and old_off:
            cls = "corporate_action_miss"; n_ca += 1
        elif old is not None and new is not None and abs(old - 1.0) < CONVERGE_TOL and abs(new - 1.0) < RECENT_TOL:
            cls = "clean"; n_clean += 1
        elif not recent_agree and old is not None and abs(old - 1.0) < CONVERGE_TOL:
            cls = "recent_divergence"; n_recent += 1
        else:
            cls = "persistent_divergence"; n_persist += 1   # constant ≠1 (currency-label/instrument)
        results[tk] = {"class": cls, "symbol": sym, "old_ratio": round(old, 4) if old else None,
                       "recent_ratio": round(new, 4) if new else None,
                       "dispersion": round(disp, 4) if disp else None,
                       "weight_pct": weights.get(tk), "n_overlap": len(ov),
                       "yahoo_currency": yccy}
        if i % 40 == 0:
            print("  [{}/{}] clean={} CA-miss={} persistent={} recent={} err={}".format(
                i, len(v2_names), n_clean, n_ca, n_persist, n_recent, n_err))
        time.sleep(0.05)

    route = sorted([tk for tk, r in results.items() if r.get("class") == "corporate_action_miss"],
                   key=lambda t: -((results[t].get("weight_pct") or 0)))
    # SELF-MAINTAIN the route registry (the standing-job behaviour): a newly-detected miss is
    # recorded so the next history refresh Yahoo-routes it. Idempotent. The detection IS the
    # Yahoo cross-check, so this is verified, not a blind auto-map. --no-record disables it.
    if not args.no_record:
        for tk in route:
            r = results[tk]
            add_route(tk, {"reason": "corporate_action_miss — v2 under-adjusts vs Yahoo (sustained-ratio sweep)",
                           "yahoo_symbol": r.get("symbol"),
                           "evidence": [{"old_ratio": r.get("old_ratio"), "recent_ratio": r.get("recent_ratio")}],
                           "detected_by": "sweep_v2_vs_yahoo"})
        if route:
            print("  registry self-maintained: {} corporate-action-miss name(s) recorded → "
                  "Yahoo history on next refresh".format(len(route)))
    OUT.write_text(json.dumps({
        "_meta": {"swept_at": datetime.now(timezone.utc).isoformat() + "Z",
                  "v2_names": len(v2_names),
                  "counts": {"clean": n_clean, "corporate_action_miss": n_ca,
                             "persistent_divergence": n_persist, "recent_divergence": n_recent,
                             "yahoo_error": n_err},
                  "yahoo_route": route},
        "names": results}, indent=2))

    print("\nCLASS COUNTS: clean={} | CA-miss={} | persistent={} | recent={} | err={}".format(
        n_clean, n_ca, n_persist, n_recent, n_err))
    print("\n>>> CORPORATE-ACTION-MISS → YAHOO-ROUTE ({}):  Σweight = {:.3f}%".format(
        len(route), sum((results[t].get("weight_pct") or 0) for t in route)))
    print("  {:11} {:>8} {:>8} {:>9} {:>6}".format("ticker", "old_r", "recent_r", "weight%", "ndays"))
    for tk in route:
        r = results[tk]
        print("  {:11} {:>8} {:>8} {:>9} {:>6}".format(
            tk, r.get("old_ratio"), r.get("recent_ratio"),
            r.get("weight_pct") if r.get("weight_pct") is not None else "n/c", r.get("n_overlap")))

    print("\nPERSISTENT-DIVERGENCE (review — NOT routed; v2 may be the correct side e.g. agorot):")
    for tk, r in sorted(results.items(), key=lambda kv: -(kv[1].get("dispersion") or 0)):
        if r.get("class") == "persistent_divergence":
            print("  {:11} old={} recent={} disp={} yccy={}  w={}".format(
                tk, r.get("old_ratio"), r.get("recent_ratio"), r.get("dispersion"),
                r.get("yahoo_currency"), r.get("weight_pct")))

    # Explicit resolution of the flagged-ambiguous high-weight names.
    print("\nAMBIGUOUS-NAME RESOLUTION:")
    for tk in ["300124 C2", "2395 TT", "688169 C1", "010060 KS", "6680 HK", "AI FP", "189300 KS", "MRSN FP"]:
        r = results.get(tk, {})
        verdict = ("YAHOO-ROUTE (v2 missed an action)" if r.get("class") == "corporate_action_miss"
                   else "KEEP v2 (clean vs Yahoo)" if r.get("class") == "clean"
                   else "REVIEW ({})".format(r.get("class")))
        print("  {:11} old={} recent={} → {}".format(
            tk, r.get("old_ratio"), r.get("recent_ratio"), verdict))
    print("\nWrote {}".format(OUT.relative_to(ROOT)))


if __name__ == "__main__":
    main()
