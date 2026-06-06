#!/usr/bin/env python3
"""
Dry-run before/after USD diff for the #55 v2-short cutover — NO live changes.
=============================================================================
For each resolved-fresh constituent, compute the NEW USD price (v2-short symbol +
the new suffix→ccy / minor-unit currency layer) and compare to the CURRENTLY
COMMITTED USD price. This is a staged before/after diff, not an in-place swap.

WHY a temporal-continuity diff is the gate: the independent-reconstruction Δ=0
parity CANNOT catch a currency error — both reconstructions read the same (wrong)
price. Only continuity vs the last-known USD catches a 100x pence/agorot-class
mistake. So we flag every constituent whose USD jumps >2x or <0.5x (absent a real
corporate action) for INDIVIDUAL explanation before any re-baseline. A large
legitimate shift (OVZON/IMI/SCC native-vs-crosslisting/agorot corrections) must
not be blanket-accepted — each flagged move is itemised.

Read-only: fetches v2 prices + reads the committed all_prices/weights. Writes
nothing to the live tree.
"""
import sys, json, base64, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from fetch_prices import EQUITIES
from marketstack_client import _api_get
import currency_convert as cc

COUNTRY = {t: c for t, _, _, c in EQUITIES}


def gh_json(path):
    u = "https://api.github.com/repos/Robonios/Robotnik/contents/{}?ref=main".format(path)
    return json.loads(base64.b64decode(json.load(urllib.request.urlopen(u, timeout=30))["content"]))


def v2_price_date(sym):
    try:
        d = _api_get("eod", {"symbols": sym, "limit": 8}, version="v2")
        for x in (d.get("data") or []):
            c = x.get("close")
            if c and float(c) > 0:
                return float(c), str(x.get("date"))[:10]
    except Exception:
        pass
    return None, None


def main():
    res = json.loads((ROOT / "data/registries/marketstack_symbols.json").read_text())["symbols"]
    # Reference USD from the local committed tree (avoids a GitHub round-trip; the
    # only network calls that matter are the MS v2 price fetches below).
    old_usd = {p["ticker"]: p.get("price")
               for p in json.loads((ROOT / "data/prices/all_prices.json").read_text()).get("prices", [])}
    try:
        w = json.loads((ROOT / "data/index/weights.json").read_text())
        weights = {x["ticker"]: x.get("weight", 0) for x in (w.get("weights") or w.get("constituents") or [])}
    except Exception:
        weights = {}

    rows = []
    fresh = [(tk, i) for tk, i in res.items() if i.get("status") == "fresh"]
    for n, (tk, info) in enumerate(fresh, 1):
        sym = info["symbol"]
        px, dt = v2_price_date(sym)
        time.sleep(0.05)
        new = None; ccy = None; note = ""
        if px is None:
            note = "v2_no_price"
        else:
            try:
                ccy = cc.currency_for_marketstack(sym, tk, COUNTRY.get(tk), False)
                new = cc.to_usd(px, ccy, dt)
            except Exception as e:
                note = "ccy_err:" + str(e)[:24]
        o = old_usd.get(tk)
        ratio = (new / o) if (new and o) else None
        rows.append((tk, sym, o, new, ratio, ccy or note))
        if n % 60 == 0:
            print("  [{}/{}] priced".format(n, len(fresh)))

    flagged = [r for r in rows if r[4] and (r[4] > 2.0 or r[4] < 0.5)]
    ok = [r for r in rows if r[4] and 0.5 <= r[4] <= 2.0]
    noprice = [r for r in rows if r[3] is None]
    shift = sum(weights.get(r[0], 0) * (r[4] - 1) for r in rows if r[4])

    print("\n=== DRY-RUN v2 diff: {} resolved-fresh constituents ===".format(len(rows)))
    print("within tolerance (0.5-2x): {} | FLAGGED discontinuity: {} | no v2 price/err: {}".format(
        len(ok), len(flagged), len(noprice)))
    print("weighted composite price shift  sum(w*(ratio-1)) = {:+.3%}  (weights cover {} names)".format(
        shift, len([r for r in rows if weights.get(r[0])]))) if weights else print("(no weights loaded)")
    print("\nFLAGGED (>2x or <0.5x) — EXPLAIN each before re-baseline:")
    for tk, sym, o, new, ratio, ccy in sorted(flagged, key=lambda x: -(x[4] or 0)):
        print("   {:11} {:13} {:>11} -> {:>11}  x{:>7.2f}  w={:>7.3%}  [{}]".format(
            tk, sym, round(o, 4) if o else o, round(new, 4) if new else new, ratio, weights.get(tk, 0), ccy))
    print("\nNO v2 PRICE / err ({}) — fall to Yahoo-override or surface:".format(len(noprice)))
    for tk, sym, o, _, _, note in noprice[:40]:
        print("   {:11} {:13} old_usd={} [{}]".format(tk, sym, o, note))


if __name__ == "__main__":
    main()
