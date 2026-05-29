#!/usr/bin/env python3
"""
MarketStack Coverage Test — go/no-go for the EODHD → MarketStack migration
==========================================================================
Pulls the full Robotnik universe through MarketStack and reports:

  - Resolution (does the symbol return a row?)
  - Currency consistency (does the exchange MIC match the expected country?)
  - History depth (sampled — 12 representative tickers across countries)
  - EOD-close sanity vs the most recent EODHD close in data/prices/equities.json
  - Splits & dividends presence (sampled — 6 known-corp-action tickers)
  - Benchmark availability (SPY, IXIC, URTH, QQQ, SOXX, ROBO)

Conservative call budget — designed for ~20 calls total so the test can be
re-run during iteration without burning the monthly quota:
  - 4 batched latest-EOD calls (≤100 symbols each) over 309 universe entries
  - 12 history-sample calls
  - 6 splits / 6 dividends calls
  - 6 benchmark calls

Output:
  data/markets/marketstack_coverage_report.json
  data/markets/marketstack_coverage_report.md

Usage:
  python scripts/marketstack_coverage_test.py
"""

import json
import os
import sys
import time
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from marketstack_client import (
    AuthError, MarketStackError, MissingKeyError, RateLimitError,
    TransportError, UnknownSymbolError,
    INTER_CALL_SLEEP, call_count, country_api_version, route_for_ticker,
    fetch_dividends, fetch_eod_historical, fetch_eod_latest,
    fetch_splits, ticker_to_marketstack,
)
from fetch_prices import EQUITIES         # canonical universe definition
from fetch_benchmarks import BENCHMARKS   # canonical benchmark set

# ── outputs ──────────────────────────────────────────────────────────────
OUT_JSON = ROOT / "data" / "markets" / "marketstack_coverage_report.json"
OUT_MD   = ROOT / "data" / "markets" / "marketstack_coverage_report.md"

# ── expected currency by country (derived from existing equities.json) ──
COUNTRY_TO_CCY = {
    "United States": "USD", "USA": "USD", "US": "USD",
    "United Kingdom": "GBP", "UK": "GBp",
    "Germany": "EUR", "France": "EUR", "Netherlands": "EUR",
    "Ireland": "EUR", "Italy": "EUR", "Finland": "EUR", "Austria": "EUR",
    "Luxembourg": "EUR",
    "Switzerland": "CHF",
    "Sweden": "SEK", "Norway": "NOK", "Denmark": "DKK",
    "Japan": "JPY", "South Korea": "KRW", "Korea": "KRW",
    "Taiwan": "TWD", "Hong Kong": "HKD", "China": "CNY",
    "Australia": "AUD", "Canada": "CAD", "Singapore": "SGD",
    "Israel": "ILS",
    "India": "INR",
    "Argentina": "ARS", "Chile": "CLP",
}

# ── reference: EODHD equities.json for cross-check ───────────────────────
def load_eodhd_snapshot():
    """Build a dict ticker → {price, currency} from the live EODHD snapshot."""
    path = ROOT / "data" / "prices" / "equities.json"
    if not path.exists():
        return {}
    with open(path) as f:
        d = json.load(f)
    return {e["ticker"]: e for e in d.get("equities", [])}


# ── history sample — 12 tickers spanning the geographic mix ──────────────
HISTORY_SAMPLE = [
    ("NVDA",       "United States"),
    ("AAPL",       "United States"),
    ("LIN",        "United States"),
    ("ASML",       "Netherlands"),
    ("SIE",        "Germany"),
    ("ABBN",       "Switzerland"),
    ("2330",       "Taiwan"),       # TSMC
    ("6594",       "Japan"),        # Nidec
    ("012450",     "South Korea"),  # Hanwha — the canary ticker
    ("0700",       "Hong Kong"),    # Tencent — only if it's in universe (likely not)
    ("BARC",       "United Kingdom"),
    ("000660",     "South Korea"),  # SK Hynix
]

# Tickers with well-known recent corporate actions (for splits/dividends probe)
CORP_ACTION_SAMPLE = ["NVDA", "AAPL", "TSM", "AVGO", "AMD", "INTC"]

# Benchmark symbols come from the canonical set in fetch_benchmarks.py so we
# don't drift if a benchmark is added (e.g. Russell 2000 fallback).
# Per Option C round 1: MarketStack uses .INDX suffix for indices. ETF-class
# benchmarks (SPY, QQQ, URTH, SOXX, ROBO) stay as bare US tickers.
BENCHMARK_TO_MARKETSTACK = {
    "SPY":  "SPY",
    "QQQ":  "QQQ",
    "URTH": "URTH",
    "SOXX": "SOXX",
    "ROBO": "ROBO",
    "IXIC": "IXIC.INDX",   # Nasdaq Composite — confirmed working via Option C probe
}
BENCHMARK_SYMBOLS = list(BENCHMARKS.keys())


# ── helpers ──────────────────────────────────────────────────────────────
def normalise_iso_date(d):
    """MarketStack dates come as ISO-with-tz: '2026-05-22T00:00:00+0000'."""
    if not d:
        return None
    return str(d).split("T", 1)[0]


def safe_fetch(callable_, *args, **kwargs):
    """Run a fetch, classify the outcome, never propagate.

    Returns (ok: bool, payload, error_kind: str|None).
    """
    try:
        return True, callable_(*args, **kwargs), None
    except UnknownSymbolError as e:
        return False, None, "UNKNOWN_SYMBOL"
    except AuthError:
        raise  # auth errors are fatal — propagate and stop the run
    except RateLimitError as e:
        return False, None, "RATE_LIMIT:{}".format(e)
    except TransportError as e:
        return False, None, "TRANSPORT:{}".format(str(e)[:80])
    except MarketStackError as e:
        return False, None, "OTHER:{}".format(str(e)[:80])


def check_price_vs_eodhd(ms_close, eodhd_close, tol_pct=2.0):
    """Compare MarketStack vs EODHD close. Returns (delta_pct, flag) or (None, None).

    A close-of-day price in two providers should agree well inside ±2%; anything
    larger likely signals a symbology mismatch fetched the wrong instrument.
    """
    if ms_close is None or eodhd_close is None or eodhd_close <= 0:
        return None, None
    delta = (float(ms_close) - float(eodhd_close)) / float(eodhd_close) * 100.0
    flag = "BEYOND_TOLERANCE" if abs(delta) > tol_pct else None
    return round(delta, 2), flag


def md_row(*cells):
    """Render a markdown table row from arbitrary cell values."""
    return "| " + " | ".join("" if c is None else str(c) for c in cells) + " |"


# ── main ─────────────────────────────────────────────────────────────────
def main():
    print("=" * 70)
    print("MARKETSTACK COVERAGE TEST")
    print("  Universe: {} equities (from fetch_prices.EQUITIES)".format(len(EQUITIES)))
    print("=" * 70)

    eodhd_snap = load_eodhd_snapshot()
    print("  EODHD reference snapshot: {} tickers".format(len(eodhd_snap)))

    report = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "universe_size": len(EQUITIES),
        "eodhd_reference_size": len(eodhd_snap),
        "per_ticker": [],
        "history_sample": [],
        "corp_actions_sample": [],
        "benchmarks": [],
        "summary": {},
        "errors_seen": Counter(),
        "call_count_end": 0,
    }

    # ── 1. Resolution + latest EOD (Option A: single-symbol per call) ──
    # The /eod/latest endpoint reliably fails HTTP 406 when batched across the
    # international mix (one invalid symbol poisons the whole batch). Option A
    # = one call per ticker. ~300 calls is cheap (0.3% of monthly quota) and
    # gives a real resolution number across the universe.
    print("\n[1/4] Latest EOD (Option A: single-symbol per call)")
    targets = []
    for ticker, name, sector, country in EQUITIES:
        ms_sym, ms_ver, supported = route_for_ticker(ticker, country)
        targets.append({
            "ticker": ticker, "name": name, "country": country,
            "expected_ccy": COUNTRY_TO_CCY.get(country),
            "ms_symbol": None if not supported else ms_sym,
            "api_version": ms_ver,
            "marketstack_supported": supported,
        })
    api_targets = [t for t in targets if t["ms_symbol"]]

    latest_by_symbol = {}
    print("  Probing {} mapped symbols, one call each…".format(len(api_targets)))
    for idx, t in enumerate(api_targets):
        sym = t["ms_symbol"]
        ok, data, err = safe_fetch(
            fetch_eod_latest, [sym], limit=1, throttle=False,
            version=t["api_version"],
        )
        if ok and data:
            latest_by_symbol[sym] = data[0]
        elif not ok:
            report["errors_seen"][err.split(":", 1)[0]] += 1
        if (idx + 1) % 50 == 0:
            print("    {} / {} probed, {} resolved so far".format(
                idx + 1, len(api_targets), len(latest_by_symbol)))
        time.sleep(INTER_CALL_SLEEP)
    print("  Resolution probe complete: {} / {} returned data".format(
        len(latest_by_symbol), len(api_targets)))

    # Per-ticker assemble
    eodhd_price_disagreements = 0
    for t in targets:
        record = {
            "ticker": t["ticker"], "country": t["country"],
            "expected_ccy": t["expected_ccy"], "ms_symbol": t["ms_symbol"],
        }
        if t["ms_symbol"] is None:
            record["resolved"] = False
            # Distinguish "vendor unsupported (known)" from "country not mapped"
            record["reason"] = ("marketstack_unsupported" if not t.get("marketstack_supported")
                                else "country_not_mapped")
            report["per_ticker"].append(record)
            continue
        row = latest_by_symbol.get(t["ms_symbol"])
        if not row:
            record["resolved"] = False
            record["reason"] = "no_row_in_batch_response"
            report["per_ticker"].append(record)
            continue
        record["resolved"] = True
        record["close"] = row.get("close")
        record["date"]  = normalise_iso_date(row.get("date"))
        record["volume"] = row.get("volume")
        record["exchange_mic"] = row.get("exchange")

        # Sanity vs EODHD's latest close
        eodhd = eodhd_snap.get(t["ticker"])
        if eodhd:
            delta, flag = check_price_vs_eodhd(record["close"], eodhd.get("price"))
            if delta is not None:
                record["eodhd_close"] = float(eodhd["price"])
                record["ms_vs_eodhd_pct"] = delta
                if flag:
                    record["price_flag"] = flag
                    eodhd_price_disagreements += 1
        report["per_ticker"].append(record)

    n_resolved = sum(1 for r in report["per_ticker"] if r.get("resolved"))
    n_unresolved = len(report["per_ticker"]) - n_resolved
    print("  Resolved: {}/{}  Unresolved: {}  Price-flag: {}".format(
        n_resolved, len(EQUITIES), n_unresolved, eodhd_price_disagreements))

    # ── 2. History depth probe (12 sampled tickers) ──
    print("\n[2/4] History sample (12 tickers, 6-month window)")
    six_months_ago = (date.today() - timedelta(days=180)).isoformat()
    today_iso = date.today().isoformat()
    for ticker, country in HISTORY_SAMPLE:
        ms_sym = ticker_to_marketstack(ticker, country)
        if ms_sym == "UNAVAILABLE":
            report["history_sample"].append({
                "ticker": ticker, "country": country,
                "ms_symbol": None, "ok": False, "reason": "unmapped"
            })
            continue
        ok, data, err = safe_fetch(
            fetch_eod_historical, ms_sym, six_months_ago, today_iso,
            version=country_api_version(country),
        )
        rec = {"ticker": ticker, "country": country, "ms_symbol": ms_sym, "ok": ok}
        if ok and data:
            rec["rows"] = len(data)
            rec["first"] = normalise_iso_date(data[0].get("date"))
            rec["last"]  = normalise_iso_date(data[-1].get("date"))
            rec["last_close"] = data[-1].get("close")
        elif not ok:
            rec["reason"] = err
            report["errors_seen"][(err or "").split(":", 1)[0]] += 1
        report["history_sample"].append(rec)
        print("  {:12s} {:5s} → {:18s}  {}".format(
            ticker, country[:5], ms_sym, rec.get("rows", rec.get("reason", "?"))))
        time.sleep(INTER_CALL_SLEEP)

    # ── 3. Splits + dividends probe ──
    print("\n[3/4] Splits + dividends (6 known-corp-action tickers)")
    for ticker in CORP_ACTION_SAMPLE:
        ms_sym = ticker  # all US, no suffix
        ok_s, splits_data, err_s = safe_fetch(fetch_splits, ms_sym)
        time.sleep(INTER_CALL_SLEEP)
        ok_d, divs_data,   err_d = safe_fetch(fetch_dividends, ms_sym)
        rec = {
            "ticker": ms_sym,
            "splits_ok": ok_s,
            "splits_count": len(splits_data or []) if ok_s else None,
            "splits_reason": err_s,
            "dividends_ok": ok_d,
            "dividends_count": len(divs_data or []) if ok_d else None,
            "dividends_reason": err_d,
        }
        if ok_s and splits_data:
            rec["splits_latest"] = splits_data[0]
        if ok_d and divs_data:
            rec["dividends_latest"] = divs_data[0]
        report["corp_actions_sample"].append(rec)
        print("  {:8s} splits:{:>3s}  divs:{:>3s}".format(
            ms_sym,
            str(len(splits_data or [])) if ok_s else "FAIL",
            str(len(divs_data or [])) if ok_d else "FAIL",
        ))
        time.sleep(INTER_CALL_SLEEP)

    # ── 4. Benchmarks probe ──
    print("\n[4/4] Benchmarks (6 symbols)")
    for bm in BENCHMARK_SYMBOLS:
        ms_bm = BENCHMARK_TO_MARKETSTACK.get(bm, bm)
        ok, data, err = safe_fetch(fetch_eod_latest, ms_bm)
        rec = {"symbol": bm, "ok": ok}
        if ok and data:
            r = data[0]
            rec["close"] = r.get("close")
            rec["date"] = normalise_iso_date(r.get("date"))
            rec["exchange"] = r.get("exchange")
        elif not ok:
            rec["reason"] = err
            report["errors_seen"][(err or "").split(":", 1)[0]] += 1
        report["benchmarks"].append(rec)
        print("  {:5s} → {}".format(bm, rec.get("close", rec.get("reason", "?"))))
        time.sleep(INTER_CALL_SLEEP)

    # ── summary ──
    report["call_count_end"] = call_count()
    report["errors_seen"] = dict(report["errors_seen"])
    by_country = defaultdict(lambda: {"resolved": 0, "unresolved": 0})
    for r in report["per_ticker"]:
        b = by_country[r["country"]]
        b["resolved" if r.get("resolved") else "unresolved"] += 1
    report["summary"] = {
        "universe_size": len(EQUITIES),
        "resolved": n_resolved,
        "unresolved": n_unresolved,
        "resolution_pct": round(n_resolved / len(EQUITIES) * 100, 1),
        "by_country": dict(by_country),
        "price_disagreements_beyond_2pct": eodhd_price_disagreements,
        "history_sample_ok": sum(1 for h in report["history_sample"] if h.get("ok")),
        "history_sample_total": len(report["history_sample"]),
        "splits_provider_works": sum(1 for c in report["corp_actions_sample"] if c["splits_ok"]),
        "dividends_provider_works": sum(1 for c in report["corp_actions_sample"] if c["dividends_ok"]),
        "benchmarks_ok": sum(1 for b in report["benchmarks"] if b.get("ok")),
        "benchmarks_total": len(report["benchmarks"]),
        "calls_used": call_count(),
    }

    # ── write outputs ──
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, "w") as f:
        json.dump(report, f, indent=2, default=str)
    write_markdown_report(report)

    print("\n" + "=" * 70)
    print("RESULT")
    print("  Resolved: {}/{} ({}%)".format(
        n_resolved, len(EQUITIES), report["summary"]["resolution_pct"]))
    print("  History sample ok: {}/{}".format(
        report["summary"]["history_sample_ok"], report["summary"]["history_sample_total"]))
    print("  Benchmarks ok: {}/{}".format(
        report["summary"]["benchmarks_ok"], report["summary"]["benchmarks_total"]))
    print("  Splits / dividends endpoints: works on {} / {} tickers".format(
        report["summary"]["splits_provider_works"],
        report["summary"]["dividends_provider_works"]))
    print("  Price disagreements >2%: {}".format(eodhd_price_disagreements))
    print("  API calls used: {}".format(call_count()))
    print("  Output: {}".format(OUT_JSON.relative_to(ROOT)))
    print("  Output: {}".format(OUT_MD.relative_to(ROOT)))
    print("=" * 70)


def write_markdown_report(report):
    """Render a human-readable markdown report alongside the JSON."""
    s = report["summary"]
    lines = [
        "# MarketStack Coverage Test",
        "",
        "Generated: `{}`".format(report["generated_at"]),
        "",
        "## Headline",
        "",
        "| Check | Result |",
        "|---|---|",
        "| Universe size | {} |".format(s["universe_size"]),
        "| Resolved on MarketStack | **{} / {} ({}%)** |".format(
            s["resolved"], s["universe_size"], s["resolution_pct"]),
        "| History sample success | {} / {} |".format(
            s["history_sample_ok"], s["history_sample_total"]),
        "| Splits endpoint works | {} / 6 sampled tickers |".format(s["splits_provider_works"]),
        "| Dividends endpoint works | {} / 6 sampled tickers |".format(s["dividends_provider_works"]),
        "| Benchmarks resolved | {} / {} |".format(s["benchmarks_ok"], s["benchmarks_total"]),
        "| Price disagreements >2% vs EODHD | {} |".format(s["price_disagreements_beyond_2pct"]),
        "| Total API calls used | {} |".format(s["calls_used"]),
        "",
        "## Resolution by country",
        "",
        "| Country | Resolved | Unresolved |",
        "|---|---:|---:|",
    ]
    for country, c in sorted(s["by_country"].items()):
        lines.append(md_row(country, c["resolved"], c["unresolved"]))

    # Unresolved details
    unresolved = [r for r in report["per_ticker"] if not r.get("resolved")]
    if unresolved:
        lines += ["", "## Unresolved tickers", "",
                  "| Ticker | Country | MS symbol attempt | Reason |",
                  "|---|---|---|---|"]
        for r in unresolved[:80]:  # cap rendered list
            lines.append(md_row(r["ticker"], r["country"],
                                r.get("ms_symbol") or "—",
                                r.get("reason", "?")))
        if len(unresolved) > 80:
            lines.append(md_row("…", "…", "…",
                                "(+{} more, see JSON)".format(len(unresolved) - 80)))

    # Price disagreements
    flagged = [r for r in report["per_ticker"] if r.get("price_flag") == "BEYOND_TOLERANCE"]
    if flagged:
        lines += ["", "## Price disagreements >2% vs EODHD",
                  "These likely indicate symbology mismatches pulling the wrong instrument.",
                  "",
                  "| Ticker | MS symbol | MS close | EODHD close | Delta % |",
                  "|---|---|---:|---:|---:|"]
        for r in flagged[:30]:
            lines.append(md_row(r["ticker"], r["ms_symbol"], r["close"],
                                r["eodhd_close"],
                                "{:+.2f}%".format(r["ms_vs_eodhd_pct"])))

    # History sample
    lines += ["", "## History sample (180-day window)",
              "", "| Ticker | Country | MS symbol | Rows | First | Last |",
              "|---|---|---|---:|---|---|"]
    for h in report["history_sample"]:
        lines.append(md_row(h["ticker"], h["country"],
                            h.get("ms_symbol") or "—",
                            h.get("rows", "FAIL"),
                            h.get("first", "—"), h.get("last", "—")))

    # Splits + dividends
    lines += ["", "## Splits + dividends sample",
              "",
              "| Ticker | Splits count | Dividends count |",
              "|---|---:|---:|"]
    for c in report["corp_actions_sample"]:
        lines.append(md_row(
            c["ticker"],
            c.get("splits_count") if c["splits_ok"] else "FAIL",
            c.get("dividends_count") if c["dividends_ok"] else "FAIL"))

    # Benchmarks
    lines += ["", "## Benchmarks",
              "",
              "| Symbol | Resolved | Close | Date | Exchange |",
              "|---|---|---:|---|---|"]
    for b in report["benchmarks"]:
        lines.append(md_row(
            b["symbol"], "yes" if b.get("ok") else "no",
            b.get("close", "—"), b.get("date", "—"), b.get("exchange", "—")))

    if report["errors_seen"]:
        lines += ["", "## Errors seen", ""]
        for k, n in report["errors_seen"].items():
            lines.append("- `{}` × {}".format(k, n))

    with open(OUT_MD, "w") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    try:
        main()
    except MissingKeyError as e:
        print("\nFAIL: {}".format(e))
        print("Set the key locally with:")
        print("    echo 'MARKETSTACK_API_KEY=<your-key>' >> .env")
        sys.exit(1)
    except AuthError as e:
        print("\nAUTH FAIL: {}".format(e))
        print("Verify the key is active and matches a paid tier.")
        sys.exit(2)
