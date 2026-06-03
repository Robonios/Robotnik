#!/usr/bin/env python3
"""
Assemble all_prices.json — the FINAL step of the MarketStack EOD price pipeline.
================================================================================
In the legacy EODHD pipeline, `fetch_prices.py` fetched equities AND tokens AND
assembled `all_prices.json` in one script. The MarketStack pipeline splits the
fetch across vendors, so the assembly must be its own step:

  fetch_prices_marketstack.py        -> data/prices/equities.json  (MarketStack)
  fetch_yahoo_overrides.py --overrides -> merges Yahoo override names INTO it
  (tokens.json                        -> CoinGecko; legacy watchlist, NOT in any
                                          equity aggregation — kept for the feed)
  THIS SCRIPT                          -> data/prices/all_prices.json (combined)

`all_prices.json` is what calculate_index.py, calculate_bottleneck_composite.py
and calculate_metrics.py read. Without this step the MarketStack YAML would leave
nothing producing it — the assembly gap the cutover dry-run is designed to catch.

Tokens are a legacy content watchlist (type=="token"), excluded from every equity
index by construction, so their freshness is non-critical: we fold in the most
recent tokens.json if present and never block on it.

Usage:  python scripts/assemble_all_prices.py
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EQ_PATH  = ROOT / "data" / "prices" / "equities.json"
TK_PATH  = ROOT / "data" / "prices" / "tokens.json"
OUT_PATH = ROOT / "data" / "prices" / "all_prices.json"

# ── Baseline-age floor constants (price-specific calibration) ──
# Prices refresh daily on weekdays; a still-current EOD price is at most a few
# days old (Fri close seen Mon/Tue, plus holiday runs). 14d absorbs weekends and
# holidays yet catches a multi-week freeze.
# The FAIL fraction is tuned BELOW the international book's share of the universe,
# NOT mirrored from the cap floor (.60). Non-US names are ~22% of the equity book
# and all convert via FX, so an FX-source-wide freeze (ECB unreachable → fallback
# to the CI-blocked Yahoo, or the parser breaking) re-freezes ALL of them at once
# → ~19-22% stale. A 22%-stale index is DISTORTED — frozen names post zero daily
# return, so the day's move is misattributed — so we block-and-serve-last-good
# rather than publish a mixed-as-of index. FAIL=0.15 sits below that 22% (the
# freeze trips it) and above the post-fix normal (TWD-only via Yahoo fallback,
# ~3%; up to ~10-12% if the Yahoo overrides are ALSO CI-blocked — the open #48
# probe), so a healthy run passes. WARN=0.10 is the pre-alarm step below it.
STALE_DAYS      = 14
STALE_WARN_FRAC = 0.10
STALE_FAIL_FRAC = 0.15


def _row(e):
    return {
        "ticker":   e.get("ticker"),
        "price":    e.get("price"),
        "currency": e.get("currency", "USD"),
        "date":     e.get("date"),
        "sector":   e.get("sector"),
        "source":   e.get("source"),
    }


def main():
    if not EQ_PATH.exists():
        print("FATAL: {} missing — run fetch_prices_marketstack.py first".format(
            EQ_PATH.name), file=sys.stderr)
        sys.exit(1)
    eq = json.loads(EQ_PATH.read_text())
    prices = [_row(e) for e in eq.get("equities", []) if e.get("price") is not None]
    n_eq = len(prices)

    n_tok = 0
    if TK_PATH.exists():
        try:
            tk = json.loads(TK_PATH.read_text())
            for t in tk.get("tokens", []):
                if t.get("price") is not None:
                    prices.append(_row(t)); n_tok += 1
        except Exception as exc:
            print("  WARN: tokens.json unreadable ({}); assembling equities only".format(exc))

    # ── Resilience: keep prior price for any in-universe name this assembly missed ──
    # MarketStack can return a null close, and the Yahoo-override fetch is blocked on CI
    # datacenter IPs — either drops a name from all_prices, which then trips the index
    # reverse-parity guard (the run #241 failure mode; same pattern as fetch_market_caps).
    # Keep the prior committed price (stale-flagged) so a transient vendor gap degrades to
    # a slightly-stale price, not a failed index. A name removed from the universe drops.
    kept_stale = 0
    if OUT_PATH.exists():
        try:
            from fetch_prices import EQUITIES, TOKENS
            universe = {e[0] for e in EQUITIES} | set(TOKENS.keys())
            fresh_tickers = {p["ticker"] for p in prices}
            for p in json.loads(OUT_PATH.read_text()).get("prices", []):
                t = p.get("ticker")
                if t in universe and t not in fresh_tickers and p.get("price") is not None:
                    row = dict(p); row["stale"] = True
                    prices.append(row); kept_stale += 1
        except Exception as exc:
            print("  WARN: prior all_prices merge skipped ({})".format(exc))

    # ── Baseline-age floor (sibling to the fetch_market_caps cap-age floor) ──
    # Gate on how OLD the equity prices are, NOT on this-run coverage. A blanket
    # vendor block (e.g. Yahoo FX unreachable from the CI runner IP → non-USD
    # prices can't convert → retained-stale by the merge above) must not let the
    # index publish on silently-ageing prices forever. Fail only when the equity
    # price baseline is genuinely old — refresh has not succeeded ANYWHERE (CI or
    # out-of-band) in too long. Tokens are excluded (non-index, CoinGecko-sourced,
    # freshness non-critical). Same constants/semantics as the cap floor.
    today = datetime.now(timezone.utc).date()
    def _age_days(p):
        d = str(p.get("date") or "")[:10]
        try:    return (today - datetime.strptime(d, "%Y-%m-%d").date()).days
        except Exception: return 10**6
    eq_universe = set()
    try:
        from fetch_prices import EQUITIES as _EQ
        eq_universe = {e[0] for e in _EQ}
    except Exception as exc:
        print("  WARN: price age-floor universe load failed ({}) — floor not enforced".format(exc))
    eq_prices = [p for p in prices if p.get("ticker") in eq_universe and p.get("price") is not None]

    # ── Documented known-lag exclusion (#55, STOPGAP) ──────────────────────────
    # data/markets/known_lag_cohort.json lists names MarketStack eod/latest has
    # frozen at ~2026-05-22 (mostly China-A/TW/KR/EU; feed-gap vs rolling-lag is
    # UNDER DIAGNOSIS — NOT plan-gated). Only cohort names that are STILL stale are
    # exempted from the gate (a refreshed cohort name re-enters automatically);
    # they still PUBLISH and are LOGGED every run — documented degradation, not a
    # silent quieting. Staleness in any name NOT on the list gates normally.
    # Remove the list when MS catches up or #48 sources these fresh.
    cohort = set()
    try:
        _cf = ROOT / "data" / "markets" / "known_lag_cohort.json"
        if _cf.exists():
            cohort = set(json.loads(_cf.read_text()).get("tickers", []))
    except Exception as exc:
        print("  WARN: known_lag_cohort load failed ({}) — no exclusion applied".format(exc))

    def _excluded(p):
        return p.get("ticker") in cohort and _age_days(p) > STALE_DAYS
    excluded = [p for p in eq_prices if _excluded(p)]
    gated = [p for p in eq_prices if not _excluded(p)]
    raw_stale = sum(1 for p in eq_prices if _age_days(p) > STALE_DAYS)
    gated_stale = sum(1 for p in gated if _age_days(p) > STALE_DAYS)
    stale_frac = (gated_stale / len(gated)) if gated else 0.0
    ages = sorted(_age_days(p) for p in eq_prices)

    out = {
        "fetched_at": datetime.now(timezone.utc).isoformat() + "Z",
        "count": len(prices),
        "kept_stale_count": kept_stale,
        "equity_count": len(eq_prices),
        "equity_stale_over_{}d".format(STALE_DAYS): raw_stale,
        "known_lag_excluded": len(excluded),
        "equity_stale_frac": round(stale_frac, 4),   # gated (excludes #55 known-lag)
        "source": "MarketStack + Yahoo overrides + CoinGecko (assembled)",
        "prices": prices,
    }
    OUT_PATH.write_text(json.dumps(out, indent=2))
    from collections import Counter
    mix = dict(Counter(p.get("source") for p in prices))
    print("Assembled all_prices.json: {} equities + {} tokens + {} kept-stale = {} rows  {}".format(
        n_eq, n_tok, kept_stale, len(prices), mix))
    if kept_stale > 0.05 * max(1, n_eq):
        print("  WARNING: {} prices retained from prior (stale) — a vendor likely failed this "
              "run; index still publishes on retained prices.".format(kept_stale))

    # Age line — printed EVERY run, so a partially-stale publish is never silent.
    print("  price baseline age: newest {}d, median {}d | raw {}/{} (>{}d); excluded {} known-lag "
          "(#55); GATED {}/{} = {:.0%} stale".format(
        ages[0] if ages else -1, ages[len(ages) // 2] if ages else -1,
        raw_stale, len(eq_prices), STALE_DAYS, len(excluded),
        gated_stale, len(gated), stale_frac))
    if excluded:
        names = sorted(p.get("ticker") for p in excluded)
        print("  #55 known-lag EXCLUDED from floor ({} names, publishing STALE pending diagnosis): "
              "{}{}".format(len(names), ", ".join(names[:30]), " …" if len(names) > 30 else ""))
    if gated and stale_frac > STALE_FAIL_FRAC:
        print("  FATAL: {:.0%} of NON-excluded equity prices are >{}d old (floor {:.0%}) — staleness "
              "BEYOND the documented #55 known-lag cohort. A partial-as-of index misattributes the "
              "day's move, so the run is blocked to serve last-good. Investigate the fetch/FX path, "
              "run where the vendors are reachable, then commit the baseline.".format(
                  stale_frac, STALE_DAYS, STALE_FAIL_FRAC), file=sys.stderr)
        sys.exit(1)
    if stale_frac > STALE_WARN_FRAC:
        print("  WARNING: {:.0%} of non-excluded equity prices are >{}d old — refresh overdue.".format(
              stale_frac, STALE_DAYS))


if __name__ == "__main__":
    main()
