#!/usr/bin/env python3
"""
Reject raw vendor fields in published JSON (CLAUDE.md served-data rule).
=======================================================================
GitHub Pages serves every tracked file, so a raw vendor price, % change, market
cap, P/E or sparkline in ANY tracked JSON is published, whether or not a page
renders it. This check reads every tracked *.json / *.webmanifest file in the
repository. Untracked and gitignored files are never read: they are not served.

  * --staged: only the JSON files staged for commit. The daily pipeline
    (fetch-data.yml, fetch-prices job) and the weekly pipeline
    (weekly-commodities-composite.yml) run it after `git add` and before
    `git commit`, so a failure stops those two commits. Transitional allowances
    never apply in this mode.
  * default: every tracked JSON file. conflict-marker-check.yml runs it on every
    push and pull request. It reports on commits that already exist; it blocks a
    merge only if branch protection makes the check required.

Detection (case-insensitive):
  * key names: FORBIDDEN_KEYS and FORBIDDEN_PATTERNS (prices, closes, spot and
    *_usd prices, cross-vendor samples, market caps, vendor % changes such as
    MarketStack's percentage_week, P/E, sparklines, OHLC);
  * key-less price series: lists of [date, number, ...] or {date, number} rows
    under a ticker-like key, under a generic series key (series, history, data,
    ...) of an object that names an instrument (ticker, symbol, isin, ...), or at
    the top level of a file whose path names prices or history.

Not flagged, on purpose: high / low (bottleneck grade counts use HIGH / LOW), mcap
(an index LEVEL in bottleneck_weighted_composite.json), fx_rate_to_usd (ECB
reference rate), price_unit_usd (a unit label), price_pending*, priced_*,
relative_to_base (a price relative, which the rule permits), and [date, value]
rows of returns or index levels outside a price context.

Allowances warn instead of failing until ALLOWANCE_EXPIRY (inclusive, UTC) and
fail after it. A notice says when an allowance is no longer needed.

Stdlib only. Exits 1 (listing file, key and first JSON path) on any violation.

Usage:
    python scripts/check_published_vendor_fields.py            # every tracked JSON (CI)
    python scripts/check_published_vendor_fields.py --staged   # staged JSON (pipeline)
    python scripts/check_published_vendor_fields.py --strict   # no allowances at all
CHECK_VENDOR_FIELDS_TODAY=YYYY-MM-DD overrides today's date (tests only).
"""
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

SUFFIXES = (".json", ".webmanifest")

FORBIDDEN_KEYS = {
    "price", "prices", "spot", "last_price", "current_price", "base_price", "base_prices",
    "price_history", "change_pct", "pct_change", "change_percent", "percent_change",
    "price_change", "price_change_pct", "pe", "pe_ratio", "trailing_pe", "forward_pe",
    "sparkline", "ohlc", "ohlcv", "candles", "mcap_usd", "mkt_cap", "mktcap",
}
FORBIDDEN_PATTERNS = [re.compile(p) for p in (
    r"(^|_)closes?$",                          # close, closes, last_close, adj_close, ms_close ...
    r"(^|_)close_usd$",                        # close_usd
    r"(^|_)prices?(_usd|_native|_history)?$",  # usd_price, native_price, price_usd, base_prices ...
    r"(^|_)spot(_price)?(_usd)?$",             # spot_usd, spot_price, native_spot ...
    r"^(ms|yahoo|yh|eodhd|marketstack|vendor)_(usd|open|high|low|volume)$",  # ms_usd, yahoo_usd
    # MarketStack vendor % change windows: percentage_day, percentage_week, percentage_month ...
    r"^percentage_(day|daily|week|weekly|month|monthly|quarter|year|yearly|ytd|[0-9]+[dwmy])$",
    r"^market_?caps?(_usd|_native|_local)?$",  # market_cap, market_caps, marketcap, market_cap_usd
)]
GENERIC_SERIES_KEYS = {"series", "history", "data", "points", "values", "rows", "bars", "quotes"}
INSTRUMENT_KEYS = {"ticker", "symbol", "isin", "marketstack_symbol", "yahoo_symbol",
                   "eodhd_ticker", "eodhd_symbol", "coingecko_id", "commodity"}
TICKER_LIKE = re.compile(r"^[A-Z0-9][A-Z0-9 .\-]{0,14}$")
PRICE_PATH = re.compile(r"price|close|ohlc|spark|history", re.I)
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}")
SERIES_LABEL = "(price series)"

# Allowances apply up to and including this date (UTC), then fail.
ALLOWANCE_EXPIRY = "2026-10-31"
# Legacy fields the next run of their writer removes: calculate_index.py (daily) for
# base_date.json, calculate_commodities_index.py (weekly) for commodities_index.json.
# Full-tree mode only: a file the pipeline stages was written by the current code.
TRANSITIONAL = {
    "data/index/base_date.json": {"base_prices"},
    "data/index/commodities_index.json": {"usd_price", "base_price_usd"},
}
# Raw fields already present in files this change does not touch. Both modes.
KNOWN_EXPOSURES = {
    # last close per symbol; removed on branch claude/remove-exposed-items-20261021.
    "data/registries/marketstack_symbols.json": {"last_close"},
}


def _git(args):
    out = subprocess.run(["git", *args], capture_output=True, text=True)
    if out.returncode != 0:
        print("ERROR: git {} failed: {}".format(" ".join(args), out.stderr.strip()),
              file=sys.stderr)
        sys.exit(1)
    return [f for f in out.stdout.split("\0") if f]


def _files(staged):
    if staged:
        names = _git(["diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR"])
    else:
        names = _git(["ls-files", "-z"])
    return [f for f in names if f.endswith(SUFFIXES)]


def _forbidden(key):
    k = key.lower()
    return k in FORBIDDEN_KEYS or any(p.search(k) for p in FORBIDDEN_PATTERNS)


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _dated_rows(v):
    """A non-empty list of [date, number, ...] rows or {date, number...} rows."""
    if not isinstance(v, list) or not v:
        return False
    rows = v[:25]
    if all(isinstance(r, list) and 2 <= len(r) <= 7 and isinstance(r[0], str)
           and DATE.match(r[0]) and all(_num(x) for x in r[1:]) for r in rows):
        return True
    return all(isinstance(r, dict) and isinstance(r.get("date"), str) and DATE.match(r["date"])
               and any(_num(x) for k, x in r.items() if k != "date") for r in rows)


def _note(found, label, here):
    n, first = found.get(label, (0, here))
    found[label] = (n + 1, first)


def _scan(node, path, found):
    """Collect {key or series label: (count, first JSON path)} at any depth."""
    if isinstance(node, dict):
        instrument = any(isinstance(k, str) and k.lower() in INSTRUMENT_KEYS for k in node)
        for k, v in node.items():
            here = "{}.{}".format(path, k) if path else str(k)
            if isinstance(k, str) and _forbidden(k):
                _note(found, k, here)
            elif isinstance(k, str) and _dated_rows(v) and (
                    TICKER_LIKE.match(k) or (instrument and k.lower() in GENERIC_SERIES_KEYS)):
                _note(found, SERIES_LABEL, here)
            _scan(v, here, found)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            _scan(v, "{}[{}]".format(path, i), found)


def main():
    staged = "--staged" in sys.argv
    strict = "--strict" in sys.argv
    today = os.environ.get("CHECK_VENDOR_FIELDS_TODAY") or \
        datetime.now(timezone.utc).strftime("%Y-%m-%d")
    expired = today > ALLOWANCE_EXPIRY
    files = _files(staged)
    failures, warnings, unreadable, seen = [], [], [], {}
    for f in files:
        try:
            with open(f, encoding="utf-8") as fh:
                doc = json.load(fh)
        except (OSError, ValueError) as e:
            unreadable.append((f, str(e)[:80]))
            continue
        found = {}
        if PRICE_PATH.search(f) and _dated_rows(doc):
            _note(found, SERIES_LABEL, "<top level>")
        _scan(doc, "", found)
        seen[f] = {k.lower() for k in found}
        for k, (n, first) in sorted(found.items()):
            line = "{}: {} x{} (first at {})".format(f, k, n, first)
            allowed = k.lower() in KNOWN_EXPOSURES.get(f, ()) or (
                not staged and k.lower() in TRANSITIONAL.get(f, ()))
            if allowed and not strict and not expired:
                warnings.append(line)
            elif allowed and expired and not strict:
                failures.append(line + "  [allowance expired after {}]".format(ALLOWANCE_EXPIRY))
            else:
                failures.append(line)

    prefix = "::warning::" if os.environ.get("GITHUB_ACTIONS") == "true" else "WARN "
    for line in warnings:
        print("{}raw vendor field allowed until {}: {}".format(prefix, ALLOWANCE_EXPIRY, line))
    if not staged and not strict:
        for table in (TRANSITIONAL, KNOWN_EXPOSURES):
            for f, keys in table.items():
                if f not in seen and f not in dict(unreadable):
                    print("NOTICE: allowance for {} is no longer needed (not tracked); remove it "
                          "from scripts/check_published_vendor_fields.py.".format(f))
                elif f in seen and not (keys & seen[f]):
                    print("NOTICE: allowance for {} ({}) is no longer needed; remove it from "
                          "scripts/check_published_vendor_fields.py.".format(f, ", ".join(sorted(keys))))

    if failures or unreadable:
        print("ERROR: raw vendor fields in published JSON - REJECTED (served-data rule).",
              file=sys.stderr)
        for line in failures:
            print("  " + line, file=sys.stderr)
        for f, why in unreadable:
            print("  {}: unreadable JSON, cannot verify ({})".format(f, why), file=sys.stderr)
        print("Raw prices, market caps, % changes, P/E and sparklines must not be published; "
              "published files carry derived figures only (see docs/RAW_PRICE_HANDLING.md).",
              file=sys.stderr)
        sys.exit(1)
    print("vendor-field check: clean ({} {} JSON files{})".format(
        len(files), "staged" if staged else "tracked",
        ", {} allowed until {}".format(len(warnings), ALLOWANCE_EXPIRY) if warnings else ""))


if __name__ == "__main__":
    main()
