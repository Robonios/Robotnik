#!/usr/bin/env python3
"""
MarketStack v1-vs-v2 EOD freshness probe  (RUN LOCALLY — CI/sandbox can't reach MS).
====================================================================================
Run #247 (2026-06-03) showed 68 international names — ALL source=MarketStack,
ALL version=v1 — stuck at 2026-05-22 (~12d) while US/JP names were fresh
(Jun-2/Jun-3). They are the China A-share / Taiwan / Korea / European listings.
This probe answers the decisive question for #55:

    Does MarketStack's v2 endpoint return FRESHER EOD for those names than v1?

DECISION TREE (act on the SUMMARY this prints):
  • v2 fresher for most          → route the cohort to v2 in the routing table.
                                    The fix — zero licensing cost.
  • v2 same/older for most       → STRUCTURAL MarketStack international-EOD limit →
                                    escalate to #48 (the replacement provider must
                                    cover FRESH intl EOD, not just shares). Yahoo-
                                    for-the-68 is last resort (CI-surviving, heavy
                                    licensing).
  • v2 'unknown_symbol'          → v2 needs a DIFFERENT symbol format for that name;
                                    a manual symbology check, NOT a freshness verdict.

A [v2-CONTROL] row (a currently-fresh, natively-v2-routed name) is probed first to
prove the v2 endpoint itself is live — so "v2 stale on the cohort" can't be confused
with "v2 is down".

TIME-SENSITIVE: the all_prices price age-floor FAILs the pipeline once the 05-22
cohort crosses 14d (~Mon Jun 8). Resolve the source before then, or add a documented
floor-exclusion for the known-lag cohort as a stopgap.

Usage (LOCAL, with MARKETSTACK_API_KEY in .env — git pull first so the cohort is current):
    python3 scripts/probe_marketstack_v1_v2.py                # auto-detect lagged cohort
    python3 scripts/probe_marketstack_v1_v2.py "2308 TT" "SIE GR"   # explicit names
    python3 scripts/probe_marketstack_v1_v2.py --sample       # representative subset, fast
"""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from fetch_prices import EQUITIES
from marketstack_client import route_for_ticker, fetch_eod_latest

COUNTRY = {t: c for t, _, _, c in EQUITIES}
ALL_PRICES = ROOT / "data" / "prices" / "all_prices.json"

SAMPLE = ["002050", "002472", "688297 C1",          # China A-share (CNY)
          "1590 TT", "2308 TT", "2317 TT",           # Taiwan (TWD)
          "010060 KS", "108490 KS",                  # Korea (KRW)
          "SIE GR", "IFX GR", "ETL FP", "ABBN SW"]   # Europe (EUR/CHF)


def _age(d):
    try:
        return (datetime.now(timezone.utc).date()
                - datetime.strptime(str(d)[:10], "%Y-%m-%d").date()).days
    except Exception:
        return None


def _published():
    if not ALL_PRICES.exists():
        return []
    return json.loads(ALL_PRICES.read_text()).get("prices", [])


def lagged_cohort(min_age=7):
    """MS-sourced equity names whose published date is older than min_age days."""
    out = [r["ticker"] for r in _published()
           if r.get("source") == "MarketStack" and (_age(r.get("date")) or 0) > min_age]
    return sorted(out)


def v2_control():
    """A natively-v2-routed name to prove the v2 endpoint is live. Prefer a
    currently-fresh one; fall back to any v2-routed universe name (the probe row
    then still reveals whether v2 returns a fresh date for it)."""
    fresh = [r["ticker"] for r in _published() if (_age(r.get("date")) or 99) <= 3]
    for tk in fresh:
        try:
            _, ver, ok = route_for_ticker(tk, COUNTRY.get(tk))
        except Exception:
            continue
        if ok and ver == "v2":
            return tk
    for tk, _, _, ctry in EQUITIES:        # fallback: any v2-routed universe name
        try:
            _, ver, ok = route_for_ticker(tk, ctry)
        except Exception:
            continue
        if ok and ver == "v2":
            return tk
    return None


def latest(sym, version, limit=3):
    """(latest_date, error) from MS for `sym` on `version`."""
    try:
        rows = fetch_eod_latest([sym], limit=limit, throttle=False, version=version)
        if not rows:
            return None, "no_rows"
        return max(str(r.get("date"))[:10] for r in rows), None
    except Exception as e:
        return None, "{}:{}".format(type(e).__name__, str(e)[:34])


def probe(tk, label=""):
    ctry = COUNTRY.get(tk)
    try:
        sym, ver, ok = route_for_ticker(tk, ctry)
    except Exception as e:
        print("{:13} route error: {}".format(tk, str(e)[:50]))
        return "skip"
    if not ok:
        print("{:13} {:14} {:11} {:11} {}".format(tk, "(unrouted)", "-", "-", "skip (not MS-routable)"))
        return "skip"
    v1d, v1e = latest(sym, "v1"); time.sleep(0.12)
    v2d, v2e = latest(sym, "v2"); time.sleep(0.12)
    if v2d and v1d:
        dd = (datetime.strptime(v2d, "%Y-%m-%d") - datetime.strptime(v1d, "%Y-%m-%d")).days
        verdict = ("V2 FRESHER (+{}d)".format(dd) if dd > 0
                   else "same date" if dd == 0 else "v1 fresher ({}d)".format(-dd))
        cat = "fresher" if dd > 0 else "same"
    elif v2d and not v1d:
        verdict, cat = "V2 only (v1 {})".format(v1e), "fresher"
    elif not v2d:
        verdict, cat = "v2 unavailable ({})".format(v2e), "v2err"
    else:
        verdict, cat = "both unavailable", "v2err"
    print("{:13} {:14} {:11} {:11} {}{}".format(
        tk, sym, v1d or "-", v2d or "-", (label + " ") if label else "", verdict))
    return cat


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    names = SAMPLE if "--sample" in flags else (args or lagged_cohort())
    if not names:
        print("No lagged MS names in all_prices.json (git pull first?) and none passed. "
              "Try --sample or pass tickers explicitly.")
        return

    print("MarketStack v1-vs-v2 EOD freshness probe — {} name(s)\n".format(len(names)))
    ctrl = v2_control()
    hdr = "{:13} {:14} {:11} {:11} {}".format("ticker", "ms_symbol", "v1_latest", "v2_latest", "verdict")
    print(hdr); print("-" * (len(hdr) + 4))
    if ctrl:
        probe(ctrl, label="[v2-CONTROL]")
        print("-" * (len(hdr) + 4))

    tally = {"fresher": 0, "same": 0, "v2err": 0, "skip": 0}
    for tk in names:
        cat = probe(tk)
        tally[cat] = tally.get(cat, 0) + 1

    print("\nSUMMARY: {} names | v2 fresher: {} | same/older: {} | v2 unavailable: {} | skipped: {}".format(
        len(names), tally["fresher"], tally["same"], tally["v2err"], tally["skip"]))
    print("\nDECISION (#55):")
    print("  • v2 fresher for most         → route the cohort to v2 (routing table). The fix, no licensing.")
    print("  • v2 same/older for most      → STRUCTURAL MS intl-EOD limit → escalate to #48 (provider")
    print("                                   must cover fresh intl EOD); Yahoo-for-the-68 = last resort.")
    print("  • v2 unavailable (unknown_symbol) → v2 needs a different symbol format; manual check, not a verdict.")
    if ctrl:
        print("\n([v2-CONTROL] {} confirms the v2 endpoint is live for v2-routed names — so a stale".format(ctrl))
        print(" cohort on v2 means MS lacks the DATA, not that v2 is down.)")
    print("\nNOTE: v2 is probed with the SAME symbol v1 uses; a v2 'unknown_symbol' means the v2")
    print("      endpoint expects a different symbol format, not necessarily that v2 data is missing.")


if __name__ == "__main__":
    main()
