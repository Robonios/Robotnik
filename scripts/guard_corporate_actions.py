#!/usr/bin/env python3
"""
Standing corporate-action guard (#55) — v2 split_factor misses bonus/scrip/rights.
==================================================================================
MarketStack v2's `split_factor` adjusts stock splits but NOT bonus-share / scrip /
rights attributions. Yahoo treats those as splits and back-adjusts them into its
(split-adjusted, non-dividend-adjusted) `close`. So a corporate action that v2 misses
shows up as a single-day JUMP in the v2 split-adjusted series that Yahoo does NOT share
(Yahoo is smooth there). A real price move, by contrast, appears in BOTH; and a cash
dividend appears in NEITHER (both are price-return) — so the cross-check targets exactly
the v2 miss and ignores real moves and dividends.

This is a STANDING guard, not a one-time list: the v2 miss is permanent, so a name clean
today regresses silently on its NEXT scrip event. It fires ONLY on jumps (no daily
all-names Yahoo load): a v2 jump past JUMP_PCT → cross-check Yahoo → if Yahoo is smooth
there, it's a confirmed missed corporate action → record to the route registry + surface.
The history fetcher / re-backfill consult that registry to Yahoo-route the name's HISTORY
(the latest price is post-all-events, so the DAILY book is unaffected — history only).

The Yahoo cross-check IS the verification, so recording is not a blind auto-map (no
York-type identity risk): a name is only routed once Yahoo concretely contradicts v2 at
a specific dated jump.

Registry: data/registries/corporate_action_route.json
CLI:
    python scripts/guard_corporate_actions.py --sweep    # jump-scan all v2-staged names
    python scripts/guard_corporate_actions.py --report   # show the route registry
"""
import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from fetch_yahoo import fetch_yahoo_daily, YahooFetchError
import currency_convert as cc

ROUTE_PATH = ROOT / "data" / "registries" / "corporate_action_route.json"
STAGING = ROOT / "data" / "prices" / "history_v2_staging"
MANIFEST = ROOT / "data" / "prices" / "history_v2_staging_manifest.json"

JUMP_PCT = 0.07        # a split-adjusted single-day move past this triggers a Yahoo cross-check.
                       # 7% sits BELOW a 1-for-10 bonus ex-date drop (~9%, the Air Liquide case),
                       # so the guard catches that class. Smaller gradual scrips (1-for-20 ≈ 5%)
                       # are caught by the periodic sustained-ratio sweep (sweep_v2_vs_yahoo.py),
                       # the backstop. Yahoo is fetched only ON a jump, so this stays cheap on a
                       # 45-day refresh window (jumps are rare); the 5Y --sweep is a one-time census.
SHARE_TOL = 0.40       # Yahoo's same-day move within 40% of v2's ⇒ a SHARED real move (not a miss)


# ── route registry ────────────────────────────────────────────────────────
def load_route():
    """{ticker: {...evidence}} of names whose HISTORY must come from Yahoo (v2 misses
    a corporate action). Consulted by the history fetcher + re-backfill."""
    try:
        return json.loads(ROUTE_PATH.read_text()).get("tickers", {})
    except Exception:
        return {}


def is_routed(ticker):
    return ticker in load_route()


def add_route(ticker, evidence):
    """Record (idempotently) a confirmed corporate-action-miss → Yahoo-route. Surfaced
    by the caller; the registry is the durable artifact the fetchers consult."""
    data = {"_meta": {}, "tickers": {}}
    if ROUTE_PATH.exists():
        try:
            data = json.loads(ROUTE_PATH.read_text())
        except Exception:
            pass
    data.setdefault("tickers", {})[ticker] = {**evidence,
                                              "recorded_at": datetime.now(timezone.utc).isoformat() + "Z"}
    data["_meta"] = {"updated_at": datetime.now(timezone.utc).isoformat() + "Z",
                     "count": len(data["tickers"]),
                     "purpose": "v2 split_factor misses bonus/scrip/rights; these names' HISTORY routes to Yahoo"}
    ROUTE_PATH.parent.mkdir(parents=True, exist_ok=True)
    ROUTE_PATH.write_text(json.dumps(data, indent=2))


# ── jump-triggered detector ─────────────────────────────────────────────────
def find_unexplained_jumps(series_by_date, jump_pct=JUMP_PCT):
    """Single-day moves > jump_pct in the SPLIT-ADJUSTED series. Splits are already
    removed by apply_split_adjustment, so a residual jump is NOT a split — it is a real
    move OR a corporate action v2 missed; the Yahoo cross-check separates the two."""
    dates = sorted(series_by_date)
    out = []
    for i in range(1, len(dates)):
        d0, d1 = dates[i - 1], dates[i]
        c0, c1 = series_by_date[d0], series_by_date[d1]
        if c0 and c1 and c0 > 0:
            r = c1 / c0 - 1.0
            if abs(r) > jump_pct:
                out.append((d0, d1, round(r, 4)))
    return out


def _nearest_on_or_before(series, d):
    ks = [k for k in series if k <= d]
    return max(ks) if ks else None


def confirm_via_yahoo(ticker, yahoo_symbol, jumps, output_size="5y"):
    """For each v2 jump, does Yahoo's price-return series SHARE the move (real) or stay
    smooth (v2 missed a corporate action)? Returns the list of MISSED jumps. Compares in
    USD (Yahoo→USD via the same FX) so the day's FX move is common and cancels."""
    try:
        y = fetch_yahoo_daily(yahoo_symbol, output_size=output_size)
        yccy = y.get("currency")
        yusd = {}
        for d, bar in (y.get("series") or {}).items():
            c = bar.get("close")
            if c:
                try:
                    yusd[d] = cc.to_usd(c, yccy, d)
                except cc.CurrencyError:
                    pass
    except (YahooFetchError, Exception):
        return None  # undetermined — cannot reach Yahoo
    missed = []
    for d0, d1, v2r in jumps:
        y0 = _nearest_on_or_before(yusd, d0)
        y1 = _nearest_on_or_before(yusd, d1)
        if not (y0 and y1) or not yusd[y0]:
            continue  # can't adjudicate this jump
        yr = yusd[y1] / yusd[y0] - 1.0
        shared = abs(yr - v2r) <= abs(v2r) * SHARE_TOL
        if not shared:
            missed.append({"date": d1, "v2_return": v2r, "yahoo_return": round(yr, 4)})
    return missed


def guard_name(ticker, adj_series_usd, yahoo_symbol, output_size="5y", record=True):
    """Full check for one name: detect unexplained jumps, cross-check Yahoo, record +
    return a verdict. verdict ∈ {clean, missed_corporate_action, undetermined, no_jumps}.
    Fires a Yahoo fetch ONLY when there is at least one jump."""
    jumps = find_unexplained_jumps(adj_series_usd)
    if not jumps:
        return {"ticker": ticker, "verdict": "no_jumps"}
    missed = confirm_via_yahoo(ticker, yahoo_symbol, jumps, output_size)
    if missed is None:
        return {"ticker": ticker, "verdict": "undetermined", "jumps": jumps}
    if missed:
        if record:
            add_route(ticker, {"reason": "v2 split_factor missed a corporate action "
                                          "(bonus/scrip/rights); Yahoo smooth where v2 jumped",
                               "yahoo_symbol": yahoo_symbol, "evidence": missed[:5],
                               "detected_by": "guard_corporate_actions"})
        return {"ticker": ticker, "verdict": "missed_corporate_action", "missed": missed}
    return {"ticker": ticker, "verdict": "clean"}   # jumps existed but Yahoo shared them (real moves)


# ── CLI ─────────────────────────────────────────────────────────────────────
def _load_staged(tk):
    p = STAGING / (tk.replace(" ", "_").replace("/", "_") + ".json")
    if not p.exists():
        return None, None
    d = json.loads(p.read_text())
    return ({r["date"]: float(r["close"]) for r in d.get("series", [])
             if r.get("close") is not None}, d.get("marketstack_symbol"))


def cmd_sweep():
    manifest = json.loads(MANIFEST.read_text()).get("names", {})
    v2 = [(tk, info.get("symbol")) for tk, info in manifest.items()
          if info.get("source") == "MarketStack v2" and info.get("symbol")]
    print("JUMP-SCAN {} v2-staged names (Yahoo fetched only when a jump is present)...".format(len(v2)))
    missed, undet, scanned = [], [], 0
    for i, (tk, sym) in enumerate(sorted(v2), 1):
        series, ssym = _load_staged(tk)
        if not series:
            continue
        v = guard_name(tk, series, sym or ssym, output_size="5y", record=True)
        if v["verdict"] == "missed_corporate_action":
            missed.append((tk, v["missed"][0]))
            print("  MISS {:11} {} (v2 {:+.1%} vs Yahoo {:+.1%})".format(
                tk, v["missed"][0]["date"], v["missed"][0]["v2_return"], v["missed"][0]["yahoo_return"]))
        elif v["verdict"] == "undetermined":
            undet.append(tk)
        if v["verdict"] != "no_jumps":
            scanned += 1
        if i % 40 == 0:
            print("  [{}/{}] yahoo-checked={} missed={} undet={}".format(i, len(v2), scanned, len(missed), len(undet)))
        time.sleep(0.03)
    print("\nJUMP-SWEEP: {} names Yahoo-checked, {} confirmed missed corporate action, {} undetermined".format(
        scanned, len(missed), len(undet)))
    print("route registry: {}  ({} names)".format(ROUTE_PATH.relative_to(ROOT), len(load_route())))
    if undet:
        print("undetermined (Yahoo unreachable for the jump):", ", ".join(undet[:20]))


def cmd_report():
    r = load_route()
    print("CORPORATE-ACTION ROUTE REGISTRY — {} names (HISTORY → Yahoo):".format(len(r)))
    for tk, info in sorted(r.items()):
        ev = (info.get("evidence") or [{}])[0]
        print("  {:11} {}  e.g. {} v2 {} vs Yahoo {}".format(
            tk, info.get("yahoo_symbol", ""), ev.get("date", ""),
            ev.get("v2_return"), ev.get("yahoo_return")))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sweep", action="store_true", help="jump-scan all v2-staged names")
    ap.add_argument("--report", action="store_true", help="show the route registry")
    a = ap.parse_args()
    if a.sweep:
        cmd_sweep()
    elif a.report:
        cmd_report()
    else:
        ap.error("specify --sweep or --report")
