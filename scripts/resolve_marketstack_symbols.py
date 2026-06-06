#!/usr/bin/env python3
"""
Resolve each routable entity's MarketStack v2 symbol — verify-gated (#55 Stage 2).
==================================================================================
WHY: MarketStack v1 international EOD is stale (frozen ~2026-05-22); v2 + short-suffix
(Yahoo-style) symbols are current. We were querying v1 + MIC-suffix → stale. The fix
is to standardise on v2 with the correct short symbol per entity, RESOLVED and VERIFIED
rather than MIC-constructed-and-trusted (the trap that hid this for days).

METHOD (no silent auto-map):
  • US/ADR (bare routed symbol) → the bare symbol itself.
  • Native listings → <code> + a country short-suffix candidate list (ambiguous markets
    carry several, e.g. Korea [.KS,.KQ], Germany [.DE,.F]); a small code-alias map fixes
    Robotnik-code ≠ market-code cases (e.g. MRSN→MRN).
  • VERIFY each candidate on v2 by VALIDITY — does eod/latest return a coherent bar —
    NOT strict freshness-to-today (a correctly-resolved but legitimately-stale name —
    holiday/halt/recent-listing — must not be mis-surfaced as unresolved; ongoing
    freshness is the all_prices floor's job). Keep the first VALID candidate.
  • status = fresh (<=7d) | stale (valid symbol, MS data old — recent-listing lag, route
    elsewhere) | unresolved (no valid v2 symbol — SURFACE, never blind-construct).

Writes data/registries/marketstack_symbols.json {ticker: {symbol, version, status,
last_date, candidates_tried}}. Run locally / in CI (MS reachable both). One-time +
re-runnable; the completeness guard (in the fetcher) consumes it.
"""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from fetch_prices import EQUITIES
from marketstack_client import route_for_ticker, _api_get

OUT = ROOT / "data" / "registries" / "marketstack_symbols.json"
FRESH_DAYS = 7

# Country → ordered short-suffix candidates (Yahoo-style; verify keeps the first valid).
COUNTRY_SUFFIX = {
    "Taiwan": [".TW", ".TWO"], "South Korea": [".KS", ".KQ"],
    "Germany": [".DE", ".F"], "France": [".PA"], "Italy": [".MI"],
    "Netherlands": [".AS"], "Belgium": [".BR"], "Finland": [".HE"],
    "Spain": [".MC"], "Austria": [".VI"], "Ireland": [".IR"], "Portugal": [".LS"],
    "Switzerland": [".SW"], "Sweden": [".ST"], "Norway": [".OL"], "Denmark": [".CO"],
    "United Kingdom": [".L"], "Israel": [".TA"], "Australia": [".AX"],
    "Canada": [".TO", ".V"], "Hong Kong": [".HK"], "Japan": [".T"],
}
# Bloomberg exchange suffix (the part after the space in a Robotnik ticker) → Yahoo
# short-suffix candidates. This keys off the actual LISTING venue, not the HQ country
# (GomSpace is Danish-HQ but Stockholm-listed → SS→.ST, not .CO). Ambiguous markets
# carry several; the verify step keeps the first valid.
BBG_SUFFIX = {
    "GR": [".DE", ".F"], "GY": [".DE", ".F"], "FP": [".PA"], "IM": [".MI"],
    "NA": [".AS"], "BB": [".BR"], "FH": [".HE"], "SM": [".MC"], "SQ": [".MC"],
    "AV": [".VI"], "ID": [".IR"], "SW": [".SW"], "VX": [".SW"], "SS": [".ST"],
    "NO": [".OL"], "DC": [".CO"], "LN": [".L"], "TT": [".TW", ".TWO"],
    "KS": [".KS", ".KQ"], "HK": [".HK"], "JP": [".T"], "JT": [".T"],
    "CN": [".TO", ".V"], "AU": [".AX"], "IT": [".TA", ".MI"],  # SCC IT = Tel Aviv
}
CLASS_MARKERS = {"C1", "C2", "C3"}            # Robotnik share-class markers, not exchanges
# Robotnik code ≠ market code (discovered via surfaced-unresolved; extend as found).
CODE_ALIAS = {"MRSN": "MRN", "HEXAB": "HEXA-B"}


def china_suffix(code):
    return ".SS" if code[:1] == "6" else ".SZ"   # 6xxxxx Shanghai, else Shenzhen


def candidates_for(tk, country, routed_sym):
    """Ordered v2-symbol candidates for an entity (no network).

    Listing venue (Bloomberg ticker suffix) is the PRIMARY key — country is only a
    fallback — because a name can list outside its HQ country, and codes collide
    (Korea + China both use 6-digit codes; BBG 'SS' = Stockholm, not Shanghai).
    """
    if routed_sym and "." not in routed_sym:      # bare = US / ADR
        return [routed_sym]
    parts = tk.split()
    code = CODE_ALIAS.get(parts[0], parts[0])
    bbg = parts[1] if len(parts) > 1 else None
    if bbg in CLASS_MARKERS:
        bbg = None
    if bbg and bbg in BBG_SUFFIX:                 # listing-venue suffix (authoritative)
        return [code + s for s in BBG_SUFFIX[bbg]]
    if code.isdigit():                            # bare numeric code (no venue suffix)
        if country == "Japan":      return [code + ".T"]            # Japan also 4-digit
        if country == "Hong Kong":  return [code + ".HK"]
        if country == "Taiwan":     return [code + ".TW", code + ".TWO"]
        if country == "China" or len(code) == 6:
            return [code + china_suffix(code)]    # China A-share
        if len(code) == 4:
            return [code + ".TW", code + ".TWO"]  # default 4-digit → Taiwan
    sufs = COUNTRY_SUFFIX.get(country)            # last resort: HQ-country guess
    if sufs:
        return [code + s for s in sufs]
    return [routed_sym] if routed_sym else []


def v2_latest(sym):
    """Most-recent bar with a NON-ZERO close in the last ~10 days on v2 →
    (date, close, None); else (None, None, err).

    eod/latest's `close` is unreliable — 0 for the unsettled current day — and a
    dead/no-trade listing (e.g. SIE.DE) returns all-zero. So we scan a short window
    (eod returns most-recent-first) and accept the first real close. This both
    rejects dead listings and tolerates a zero latest-bar on a live one (AI.PA,
    SIE.F)."""
    try:
        d = _api_get("eod", {"symbols": sym, "limit": 10}, version="v2")
        rows = d.get("data") or []
        for r in rows:
            c = r.get("close")
            if c and float(c) > 0:
                return (str(r.get("date"))[:10], float(c), None)
        return (None, None, "no_nonzero_close" if rows else "no_rows")
    except Exception as e:
        return (None, None, type(e).__name__ + ":" + str(e)[:24])


def reverify_symbol(ticker, country):
    """Best-effort re-resolution for the all_prices staleness-floor guard (#55).

    When a name trips the staleness floor, two very different causes look
    identical from the stored book: a GENUINE feed gap (serve last-good is
    correct) versus a RE-TICKER — the class we hit repeatedly this session
    (SHA→SHA0, JBT→JBTM, Hiab spinoff) where the company changed listing/ticker,
    our resolved-symbol map now points at a dead symbol, and a DIFFERENT symbol
    is live. Misreading a re-ticker as a feed gap freezes the name forever; this
    re-resolves it so the operator sees "fix the map", not "wait for the vendor".

    Returns {ticker, map_symbol, map_last, rer_symbol, rer_last, verdict} with
    verdict ∈ {reticker, symbol_ok_fetch_stale, genuine_gap}. Makes live v2
    calls; the CALLER wraps this best-effort so a network/key failure can never
    alter the floor's own (purely local) FATAL/WARN decision.
    """
    from marketstack_client import route_for_ticker
    today = datetime.now(timezone.utc).date()

    def _age(d):
        try:
            return (today - datetime.strptime(d, "%Y-%m-%d").date()).days
        except Exception:
            return 10 ** 6

    def _fresh(d):
        return d is not None and _age(d) <= FRESH_DAYS

    # The symbol our production map currently routes this name to (if any).
    try:
        sym, _ver, ok = route_for_ticker(ticker, country)
    except Exception:
        sym, ok = None, False
    map_symbol = sym if ok else None
    map_last = None
    if map_symbol:
        map_last, _c, _e = v2_latest(map_symbol)

    # Re-resolve from scratch off the candidate ladder — the first VALID hit.
    rer_symbol = rer_last = None
    for c in candidates_for(ticker, country, map_symbol):
        d, _close, _err = v2_latest(c)
        time.sleep(0.08)
        if d:
            rer_symbol, rer_last = c, d
            break

    # A fresh symbol DIFFERENT from the map's = re-ticker (the actionable class).
    # Map symbol still fresh = the symbol is fine; our stored price is stale for a
    # non-symbol reason (a transient fetch/FX miss — re-run the fetch). Neither
    # fresh = a genuine feed gap (delisting/vendor outage) → last-good is correct.
    if rer_symbol and _fresh(rer_last) and rer_symbol != map_symbol:
        verdict = "reticker"
    elif map_symbol and _fresh(map_last):
        verdict = "symbol_ok_fetch_stale"
    elif rer_symbol and _fresh(rer_last):
        verdict = "reticker"
    else:
        verdict = "genuine_gap"
    return {"ticker": ticker, "map_symbol": map_symbol, "map_last": map_last,
            "rer_symbol": rer_symbol, "rer_last": rer_last, "verdict": verdict}


def main():
    today = datetime.now(timezone.utc).date()
    def age(d):
        try: return (today - datetime.strptime(d, "%Y-%m-%d").date()).days
        except Exception: return 10**6

    out = {}
    n_fresh = n_stale = n_unres = 0
    unresolved, stale = [], []
    for i, (tk, name, sector, country) in enumerate(EQUITIES, 1):
        try:
            sym, ver, ok = route_for_ticker(tk, country)
        except Exception:
            sym, ok = None, False
        cands = candidates_for(tk, country, sym if ok else None)
        chosen = last = last_close = None; tried = []
        for c in cands:
            tried.append(c)
            d, close, err = v2_latest(c)
            time.sleep(0.08)
            if d:
                chosen, last, last_close = c, d, close
                break
        if chosen is None:
            status = "unresolved"; n_unres += 1; unresolved.append((tk, country, tried))
        elif age(last) <= FRESH_DAYS:
            status = "fresh"; n_fresh += 1
        else:
            status = "stale"; n_stale += 1; stale.append((tk, chosen, last))
        out[tk] = {"symbol": chosen, "version": "v2", "status": status,
                   "last_date": last, "last_close": last_close,
                   "candidates_tried": tried, "country": country}
        if i % 50 == 0:
            print("  [{}/{}] fresh={} stale={} unresolved={}".format(
                i, len(EQUITIES), n_fresh, n_stale, n_unres))

    OUT.write_text(json.dumps({
        "_meta": {"resolved_at": datetime.now(timezone.utc).isoformat() + "Z",
                  "criterion": "validity (eod/latest returns a bar) on v2; freshness is the floor's job",
                  "fresh": n_fresh, "stale": n_stale, "unresolved": n_unres,
                  "total": len(EQUITIES)},
        "symbols": out}, indent=2))
    print("\n=== RESOLUTION: {} entities | fresh={} stale={} unresolved={} ===".format(
        len(EQUITIES), n_fresh, n_stale, n_unres))
    print("\nSTALE (valid v2 symbol, MS data old — recent-listing lag → route to Yahoo/review):")
    for tk, sym, last in stale:
        print("   {:10} {:12} last={}".format(tk, sym, last))
    print("\nUNRESOLVED (no valid v2 symbol — SURFACE, do not blind-construct):")
    for tk, country, tried in unresolved:
        print("   {:10} [{}] tried {}".format(tk, country, tried))
    print("\nWrote {}".format(OUT.relative_to(ROOT)))


if __name__ == "__main__":
    main()
