#!/usr/bin/env python3
"""
MarketStack-vs-Yahoo Parity Guard  (ongoing production cross-check)
==================================================================
Replaces the one-time EODHD spot-check with a STANDING cross-vendor guard.
Rationale: RTX/Ibiden proved MarketStack can develop transient per-name faults
over time; a one-time comparison can't catch the NEXT one. This re-fetches the
current price from BOTH MarketStack and Yahoo, converts both to USD via the
shared daily-FX module, and flags any name whose two vendors disagree beyond a
threshold — the exact failure mode that caught ASML (routing) and RTX (corrupt).

Yahoo is the independent reference (more reliable than the deprecated EODHD;
also the override price source and the daily-FX source — see methodology §14).

Scope / cadence (within API budget):
  --daily    top-N weighted constituents (default 30)  — every EOD run
  --weekly   full eligible universe                    — Sundays
Flags |MS_usd / Yahoo_usd - 1| > THRESHOLD (default 4%). Writes a report and
exits non-zero when any flag fires (CI-visible), unless --report-only.

Usage:
  python scripts/parity_guard.py --daily
  python scripts/parity_guard.py --weekly [--report-only]
"""
import argparse, json, os, sys, time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import currency_convert as cc
from fetch_yahoo import fetch_yahoo_daily
from marketstack_client import (route_for_ticker, fetch_eod_latest, US_ADR_OVERRIDES,
                                 MARKETSTACK_UNSUPPORTED)
from fetch_prices import EQUITIES

WEIGHTS_PATH = ROOT / "data" / "index" / "weights.json"
OVERRIDES_PATH = ROOT / "data" / "registries" / "data_source_overrides.json"
OUT_PATH = ROOT / "data" / "index" / "parity_guard_report.json"
THRESHOLD = 0.04          # 4% MS-vs-Yahoo disagreement → flag


def _country(ticker):
    for t, n, s, c in EQUITIES:
        if t == ticker:
            return c
    return None


def _yahoo_symbol(ticker, country):
    """Yahoo symbol for a Robotnik ticker (override registry first, else map)."""
    try:
        ov = json.loads(OVERRIDES_PATH.read_text())
        if ticker in ov and ov[ticker].get("yahoo_symbol"):
            return ov[ticker]["yahoo_symbol"]
    except Exception:
        pass
    # Reuse the proven Bloomberg→Yahoo mapper from fetch_market_caps (it maps
    # the whole universe for the mcap pull); override registry covers the rest.
    from fetch_market_caps import ticker_to_yahoo
    try:
        return ticker_to_yahoo(ticker, country)
    except Exception:
        return ticker.split(" ")[0]


def ms_usd(ticker, country):
    """Returns (usd_price, date, err)."""
    is_adr = (ticker in US_ADR_OVERRIDES) or (ticker.split(" ", 1)[0] in US_ADR_OVERRIDES)
    sym, ver, ok = route_for_ticker(ticker, country)
    if not ok:
        return None, None, "ms_unsupported"
    rows = fetch_eod_latest([sym], limit=1, throttle=False, version=ver)
    if not rows:
        return None, None, "ms_empty"
    r = rows[0]; dt = str(r.get("date"))[:10]
    try:
        ccy = cc.currency_for_marketstack(sym, ticker, country, is_adr)
        return cc.to_usd(r.get("close"), ccy, dt), dt, None
    except Exception as e:
        return None, dt, "ms_ccy:" + str(e)[:40]


def yahoo_usd(ticker, country):
    """Returns (usd_price, date, err)."""
    ys = _yahoo_symbol(ticker, country)
    data = fetch_yahoo_daily(ys, output_size="compact")
    ser = data.get("series") or {}
    if not ser:
        return None, None, "yahoo_empty"
    d = max(ser); pt = ser[d]
    try:
        return cc.to_usd(pt.get("close"), data.get("currency"), d), d, None
    except Exception as e:
        return None, d, "yahoo_ccy:" + str(e)[:40]


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--daily", action="store_true", help="top-N weighted names")
    g.add_argument("--weekly", action="store_true", help="full eligible universe")
    ap.add_argument("--topn", type=int, default=30)
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args()

    # CI guard-skip (honest, not silent). This is an MS-vs-Yahoo cross-check, but Yahoo
    # blocks the GitHub-Actions datacenter IP — the entire Yahoo leg is unreachable in CI
    # (the same block that degrades the mcap / FX / override fetches). A cross-check with
    # one leg dead would silently "pass" having compared zero names — a hidden weakening.
    # So skip explicitly in CI and run the real cross-check OUT-OF-BAND where Yahoo works
    # (alongside the cap refresh — see #48 / the decoupled refresh job). Detect via the
    # GITHUB_ACTIONS env var; locally / out-of-band this is unset and the guard runs fully.
    if os.environ.get("GITHUB_ACTIONS", "").lower() == "true":
        print("PARITY GUARD: SKIPPED in CI — Yahoo is unreachable from the runner IP, so the "
              "MS-vs-Yahoo cross-check cannot run here. It runs out-of-band where Yahoo works "
              "(the corruption check is NOT dropped — only relocated to where it can execute).")
        return

    weights = json.loads(WEIGHTS_PATH.read_text())["weights"]
    if args.daily:
        names = [w["ticker"] for w in weights[:args.topn]]
        scope = "daily/top{}".format(args.topn)
    else:
        names = [w["ticker"] for w in weights]
        scope = "weekly/full"

    cc.refresh_all(fetcher=fetch_yahoo_daily)
    print("PARITY GUARD ({}) — {} names, threshold {:.0%}".format(scope, len(names), THRESHOLD))

    corruption, lag, checked, errors = [], [], 0, []
    for tk in names:
        country = _country(tk)
        mv, md, me = ms_usd(tk, country)
        yv, yd, ye = yahoo_usd(tk, country)
        time.sleep(0.15)
        if mv is None or yv is None or not yv:
            errors.append({"ticker": tk, "ms_err": me, "yahoo_err": ye, "ms": mv, "yahoo": yv})
            continue
        checked += 1
        diff = mv / yv - 1
        if abs(diff) <= THRESHOLD:
            continue
        # Disagreement beyond threshold. Distinguish genuine vendor LAG (the two
        # vendors quote DIFFERENT dates — routine for the ~1-week-lagging
        # A-share / Taiwan / Korea names) from CORRUPTION (SAME date, prices
        # diverge — the RTX/ASML class). Only corruption gates CI; lag is
        # reported but expected, so the guard doesn't cry wolf every weekend.
        if md and yd and md == yd:
            corruption.append({"ticker": tk, "date": md, "ms_usd": round(mv, 4),
                               "yahoo_usd": round(yv, 4), "diff_pct": round(diff * 100, 2)})
            print("  CORRUPTION {:10s} [{}] MS ${:.2f} vs Yahoo ${:.2f} ({:+.1f}%)".format(
                tk, md, mv, yv, diff * 100))
        else:
            lag.append({"ticker": tk, "ms_date": md, "yahoo_date": yd,
                        "ms_usd": round(mv, 4), "yahoo_usd": round(yv, 4),
                        "diff_pct": round(diff * 100, 2)})
            print("  lag        {:10s} MS[{}] ${:.2f} vs Yahoo[{}] ${:.2f} ({:+.1f}%) — dates differ, not gated".format(
                tk, md, mv, yd, yv, diff * 100))

    report = {
        "scope": scope, "checked": checked,
        "corruption_flagged": len(corruption), "lag_flagged": len(lag),
        "errors": len(errors), "threshold_pct": THRESHOLD * 100,
        "corruption": corruption, "lag": lag, "error_detail": errors[:40],
        "run_at": datetime.now(timezone.utc).isoformat() + "Z",
    }
    OUT_PATH.write_text(json.dumps(report, indent=2))
    print("PARITY: {} checked | {} CORRUPTION | {} lag (expected) | {} errors → {}".format(
        checked, len(corruption), len(lag), len(errors), OUT_PATH.relative_to(ROOT)))

    if corruption and not args.report_only:
        print("PARITY GUARD FAILED — {} name(s) disagree >{:.0%} ON THE SAME DATE "
              "(RTX/ASML-class corruption, not lag). Investigate before trusting "
              "the index.".format(len(corruption), THRESHOLD), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
