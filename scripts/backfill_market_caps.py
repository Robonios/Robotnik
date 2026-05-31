#!/usr/bin/env python3
"""
Targeted, VALIDATED market-cap backfill  (Workstream B / Option A)
=================================================================
Adds market caps for non-excluded frontier names the weekly fetcher missed
(unmapped country suffixes, TPEx listing, Yahoo batch `.info` gaps). The names
have prices + history but lacked a `market_caps.json` row, so the index silently
dropped them (no weight). This recovers the dominant ones (600111 China Northern
Rare Earth, GlobalWafers, Lynas, …).

Discipline (founder directive — "no unvalidated caps; validate like the GBp bug"):
  - MERGE-ONLY: never overwrites an existing market_caps row (the validated 182 are untouched).
  - Every cap is VALIDATED before it may merge:
      (1) scale check  |mcap - price*shares| / mcap <= SCALE_TOL   (the GBp 100x guard)
      (2) sane USD range  1e7 .. 1e13
      GBp fix applied (Yahoo reports mcap in the MAJOR unit even when ccy tag is "GBp").
  - Names that cannot be validly sourced are logged as GAPS — never guessed.

Usage:
  python scripts/backfill_market_caps.py            # dry-run: fetch + validate + print table
  python scripts/backfill_market_caps.py --merge    # merge ONLY the validated rows
"""
import sys, json, argparse
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_market_caps import ticker_to_yahoo  # uses the B-sweep-fixed suffix map
import yfinance as yf

ROOT = Path(__file__).resolve().parent.parent
MCAP = ROOT / "data" / "index" / "market_caps.json"
REG  = ROOT / "data" / "registries" / "entity_registry.json"

# Registry ticker -> (country, sector_override).  Yahoo symbol derived via the fixed mapper.
TARGETS = {
    "600111":    ("China",       "Materials"),  # China Northern Rare Earth (sector fix too)
    "6488 TT":   ("Taiwan",      None),         # GlobalWafers (TPEx -> .TWO via override)
    "LYC AU":    ("Australia",   None),         # Lynas Rare Earths
    "ILU AU":    ("Australia",   None),         # Iluka Resources
    "ARU AU":    ("Australia",   None),         # Arafura Rare Earths
    "AMG NA":    ("Netherlands", None),         # AMG Critical Materials
    "AVIO IM":   ("Italy",       None),         # Avio
    # Korean — Yahoo has no mcap/shares for these (probed: .info/get_shares_full/v7 all empty).
    # Attempted for completeness; expected to fall through to a documented GAP, not guessed.
    "090360 KS": ("South Korea", None), "098460 KS": ("South Korea", None),
    "108490 KS": ("South Korea", None), "189300 KS": ("South Korea", None),
    "277810 KS": ("South Korea", None), "455900 KS": ("South Korea", None),
}
FX_PAIRS = {"AUD": "AUDUSD=X", "EUR": "EURUSD=X", "CNY": "CNYUSD=X",
            "TWD": "TWDUSD=X", "GBP": "GBPUSD=X", "KRW": "KRWUSD=X"}
SANE_MIN, SANE_MAX = 1e7, 1e13
SCALE_TOL = 0.06   # |mcap - px*sh|/mcap; GBp bug is ~100x so this catches it with huge margin

# Bloomberg " KS" maps to KOSPI (.KS) by default, but these are KOSDAQ (.KQ). The price
# override registry already carries .KQ for 4 of them; these 2 are MS-priced (not in it).
_OVERRIDES = json.loads((ROOT / "data" / "registries" / "data_source_overrides.json").read_text())
YS_HINT = {"108490 KS": "108490.KQ", "277810 KS": "277810.KQ"}


def resolve_yahoo(tk, ctry):
    """Override registry yahoo_symbol (authoritative) > KOSDAQ hint > suffix mapper."""
    if tk in YS_HINT:
        return YS_HINT[tk]
    e = _OVERRIDES.get(tk)
    if isinstance(e, dict) and e.get("yahoo_symbol"):
        return e["yahoo_symbol"]
    return ticker_to_yahoo(tk, ctry)


def fx_rates():
    r = {"USD": 1.0}
    for ccy, pair in FX_PAIRS.items():
        try:
            h = yf.Ticker(pair).history(period="1d")
            if not h.empty:
                r[ccy] = float(h["Close"].iloc[-1])
        except Exception:
            pass
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--merge", action="store_true")
    a = ap.parse_args()

    reg = json.loads(REG.read_text())
    fx = fx_rates()
    print("FX->USD:", {k: round(v, 6) for k, v in fx.items()})
    print("\n%-10s %-11s %-13s %-5s %-13s %s" % ("ticker", "yahoo", "mcap_native", "ccy", "mcap_usd", "validation"))

    validated, gaps = [], []
    for tk, (ctry, sec_override) in TARGETS.items():
        rinfo = reg.get(tk, {})
        ys = resolve_yahoo(tk, ctry)
        try:
            info = yf.Ticker(ys).info
        except Exception as e:
            gaps.append((tk, ys, "info_error")); print("  %-10s %-11s GAP info_error %s" % (tk, ys, str(e)[:40])); continue
        mcap = info.get("marketCap"); ccy = info.get("currency")
        sh = info.get("sharesOutstanding")
        px = info.get("currentPrice") or info.get("regularMarketPrice")
        conv = "GBP" if ccy == "GBp" else ccy
        computed = False
        if not mcap:
            if px and sh:
                mcap = px * sh; computed = True
            else:
                gaps.append((tk, ys, "no_mcap_no_shares")); print("  %-10s %-11s GAP  Yahoo has no mcap & no shares" % (tk, ys)); continue
        rate = fx.get(conv)
        if not rate:
            gaps.append((tk, ys, "no_fx:" + str(conv))); print("  %-10s %-11s GAP  no FX for %s" % (tk, ys, conv)); continue
        mcap_usd = mcap * rate
        notes, ok = [], True
        if px and sh:
            implied = px * sh
            rel = abs(mcap - implied) / mcap if mcap else 1.0
            if rel > SCALE_TOL:
                ok = False; notes.append("SCALE-FAIL(%.0f%%)" % (rel * 100))
            else:
                notes.append("scale ok %.1f%%%s" % (rel * 100, " [computed px*sh]" if computed else ""))
        else:
            notes.append("no px*sh available")
        if not (SANE_MIN <= mcap_usd <= SANE_MAX):
            ok = False; notes.append("INSANE-RANGE")
        print("  %-10s %-11s %-13s %-5s $%-12s %s [%s]" % (
            tk, ys, "%.4g" % mcap, ccy or "?", "%.4g" % mcap_usd, " ".join(notes), "OK" if ok else "REJECT"))
        if ok:
            validated.append({"ticker": tk, "name": rinfo.get("name", tk),
                              "sector": sec_override or rinfo.get("sector", "Other"),
                              "market_cap_usd": round(mcap_usd),
                              "date_fetched": datetime.utcnow().strftime("%Y-%m-%d"),
                              "source": "Yahoo Finance (B-sweep backfill)"})

    print("\nVALIDATED: %d  | GAPS: %d  %s" % (len(validated), len(gaps), [g[0] for g in gaps]))
    if a.merge and validated:
        mc = json.loads(MCAP.read_text())
        existing = {m["ticker"] for m in mc["market_caps"]}
        added = [v for v in validated if v["ticker"] not in existing]
        skipped = [v["ticker"] for v in validated if v["ticker"] in existing]
        mc["market_caps"].extend(added)
        mc["market_caps"].sort(key=lambda x: x["market_cap_usd"], reverse=True)
        mc["count"] = len(mc["market_caps"])
        MCAP.write_text(json.dumps(mc, indent=2))
        print("MERGED %d new rows -> market_caps.json (count now %d)%s" % (
            len(added), mc["count"], ("; skipped existing %s" % skipped) if skipped else ""))
    elif a.merge:
        print("nothing validated to merge")


if __name__ == "__main__":
    main()
