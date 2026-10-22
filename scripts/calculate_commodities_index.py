#!/usr/bin/env python3
"""
Robotnik Commodities Index — forward-only launch + weekly forward-append
========================================================================
Builds / advances the Commodities Index per `commodities_index_methodology v.3`
(§6.1 live weights; §8 price-basis routing).

Two modes (auto-detected from the existing record):
  * GENESIS  (no record / empty series, or COMMODITIES_GENESIS=1 to re-baseline):
      pull current prices, compute the §6.1 live weights (reference renormalised
      across priced constituents, 12% single-name cap), set each constituent's
      base price = its current USD price, and emit a single point at 1000.00.
  * WEEKLY   (record with constituents + series present):
      pull current prices, and using the STORED base prices + STORED fixed live
      weights (never recomputed; price-pending names never auto-added — weights
      change only at a review), compute
          index = 1000 * Σ_i [ live_weight_i * (usd_price_i,current / base_i) ]
      and forward-APPEND the new weekly point. Prior points are never recomputed.

Idempotency: a re-run in the same ISO week updates that week's point in place;
it never double-appends, and the genesis/base point is immutable. A constituent
with no fresh price this run holds its last observation (§8) and is flagged.

Raw prices are never published or printed (CLAUDE.md served-data rule; Actions
logs of a public repository are public). The record carries no usd_price and no
base_price_usd:
  * Base prices come from the COMMODITIES_BASE_PRICES environment variable (the
    repository secret of that name in CI): a JSON object {commodity:
    base_price_usd}. Read order on a weekly run: the secret if set; else the
    base_price_usd still on the published constituents (the first run after the
    change only); else stop before any fetch. The secret must name exactly the
    published constituents, with positive numbers, and must equal any base_price_usd
    still published.
  * The record binds the bases: every run publishes base_prices_sha256, the
    SHA-256 of canonical_base_prices() (see there for the exact form). A later run
    stops before any fetch unless the bases it reads hash to that value, so a
    mistyped or stale secret (e.g. after a re-baseline) can never be used.
  * A constituent with no fresh price carries its PRIOR PUBLISHED relative_to_base,
    which is published at full float precision so the carry is exact.
  * A genesis run (no usable prior record, or COMMODITIES_GENESIS=1) writes its new
    base prices, as the canonical string, only to COMMODITIES_GENESIS_BASES_OUT,
    which must name a file inside the gitignored data/private/.

Constituents (20 priced) — §8 routing
  * 12 via MarketStack v2 /commodities (exchange benchmarks + China-domestic
    CNY for Silicon/Titanium/Phosphorus, FX-converted)
  * 8  via strategicmetalsinvest (USD/kg, metal): the China-controlled
    chokepoints Ga/Ge/In/Nd (Western quote) + Pr/Dy/Tb/Antimony
  * 9 PRICE-PENDING — disclosed, excluded until a source is secured.

Output: data/index/commodities_index.json   (this script does NOT git-commit)

Usage / env affordances
    python scripts/calculate_commodities_index.py
        Live: MarketStack /v2/commodities is ~1 call/min, so a 12-name pull is
        ~12 min (63s throttle, rate-limit retry). SMI is one scrape.
    COMMODITIES_MS_CACHE=<json>     read MarketStack spot from a cache (skip pull)
    COMMODITIES_SMI_CACHE=<json>    read SMI prices {label: usd_per_kg} from a cache
    COMMODITIES_INDEX_OUT=<path>    read-and-write this record elsewhere (dry-run)
    COMMODITIES_MARK_DATE=<YYYY-MM-DD>  pin the weekly mark (sim/test)
    COMMODITIES_GENESIS=1           force a genesis re-baseline (weights review)
    COMMODITIES_BASE_PRICES=<json>  base prices {commodity: base_price_usd} (secret)
    COMMODITIES_GENESIS_BASES_OUT=<path>  where a genesis run writes its new base
                                    prices; required for genesis, must be a file in
                                    data/private/ (relative paths: from the repo root)
"""

import bisect
import hashlib
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from marketstack_client import get_api_key          # noqa: E402  (API key resolution only)
import currency_convert as cc                        # noqa: E402
from fetch_fx import fetch_fx_daily                  # noqa: E402  (ECB-primary FX)

# Output / load path; a dry-run redirects via COMMODITIES_INDEX_OUT (read+write).
OUT_PATH = Path(os.environ.get("COMMODITIES_INDEX_OUT")
                or (ROOT / "data" / "index" / "commodities_index.json"))

BASE_VALUE       = 1000.0
SINGLE_NAME_CAP  = 0.12                  # §6.1 live single-name cap
MS_BASE_URL      = "https://api.marketstack.com/v2/commodities"
MS_RATE_SLEEP    = 63                    # ~1 call/min on the commodities endpoint
SMI_URL          = "https://strategicmetalsinvest.com/current-strategic-metals-prices/"
SMI_UA           = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36")
FX_STALE_WARN_DAYS = 7

MARK_DATE_OVERRIDE = os.environ.get("COMMODITIES_MARK_DATE")   # sim/test: pin the mark
FORCE_GENESIS      = os.environ.get("COMMODITIES_GENESIS") == "1"
BASE_PRICES_ENV    = "COMMODITIES_BASE_PRICES"                 # secret: {commodity: base_price_usd}
GENESIS_BASES_OUT  = os.environ.get("COMMODITIES_GENESIS_BASES_OUT")
BASE_HASH_KEY      = "base_prices_sha256"                       # published binding of the bases
PRIVATE_DIR        = ROOT / "data" / "private"                  # gitignored

# ── Constituents ───────────────────────────────────────────────────────────
# (commodity, reference_weight_pct, source, basis, fetch_key)
# v.3 routing (§8): chokepoints Ga/Ge/In/Nd → strategicmetalsinvest (Western,
# USD/kg, metal). Exchange-traded → MarketStack benchmark. China-domestic
# (CNY, flagged) only where no free Western reference exists: Si, Ti, P.
PRICED = [
    ("Gallium",      16.37, "smi",         "metal, Western/ex-China (USD/kg)",      "Gallium"),
    ("Silicon",       9.21, "marketstack", "metallurgical, China-domestic (CNY/t)", "silicon"),
    ("Titanium",      8.18, "marketstack", "sponge, China-domestic (CNY/kg)",       "titanium"),
    ("Dysprosium",    8.18, "smi",         "metal (USD/kg)",                        "Dysprosium"),
    ("Germanium",     4.60, "smi",         "metal, Western/ex-China (USD/kg)",      "Germanium"),
    ("Copper",        4.60, "marketstack", "Grade A benchmark (USD/lb)",            "copper"),
    ("Nickel",        4.60, "marketstack", "benchmark (USD/t)",                     "nickel"),
    ("Tin",           4.60, "marketstack", "benchmark (USD/t)",                     "tin"),
    ("Neodymium",     4.60, "smi",         "metal, Western/ex-China (USD/kg)",      "Neodymium"),
    ("Terbium",       4.60, "smi",         "metal (USD/kg)",                        "Terbium"),
    ("Cobalt",        4.09, "marketstack", "metal benchmark (USD/t)",               "cobalt"),
    ("Silver",        2.30, "marketstack", "benchmark (USD/t.oz)",                  "silver"),
    ("Antimony",      2.30, "smi",         "metal (USD/kg)",                        "Antimony"),
    ("Praseodymium",  2.30, "smi",         "metal (USD/kg)",                        "Praseodymium"),
    ("Indium",        1.53, "smi",         "metal, Western/ex-China (USD/kg)",      "Indium"),
    ("Aluminium",     0.77, "marketstack", "benchmark (USD/t)",                     "aluminum"),  # US spelling on MS
    ("Platinum",      0.77, "marketstack", "benchmark (USD/t.oz)",                  "platinum"),
    ("Phosphorus",    0.77, "marketstack", "phosphate-rock proxy, China-domestic (CNY/t)", "phosphorus"),
    ("Gold",          0.38, "marketstack", "benchmark (USD/t.oz)",                  "gold"),
    ("Palladium",     0.38, "marketstack", "benchmark (USD/t.oz)",                  "palladium"),
]

# (commodity, reference_weight_pct, reason) — disclosed, excluded until priced
PENDING = [
    ("Scandium",   4.09, "no free public spot (USGS annual range only)"),
    ("Tantalum",   2.30, "subscription/login-walled (Asian Metal); no free spot"),
    ("Arsenic",    1.53, "no free-retrievable spot"),
    ("Cerium",     1.53, "subscription/login-walled (SMM / Asian Metal)"),
    ("Erbium",     1.53, "subscription/login-walled (SMM / Asian Metal)"),
    ("Yttrium",    1.53, "subscription/login-walled (Asian Metal)"),
    ("Tungsten",   0.77, "subscription/login-walled (Fastmarkets APT)"),
    ("Lanthanum",  0.77, "subscription/login-walled (SMM / Asian Metal)"),
    ("Boron",      0.77, "no public spot market"),
]

SOURCE_LABEL = {"marketstack": "MarketStack v2 /commodities", "smi": "strategicmetalsinvest"}


def parse_currency_unit(unit):
    """'usd/t.oz' -> ('USD','t.oz'); 'cny/kg' -> ('CNY','kg')."""
    cur, _, per = (unit or "").partition("/")
    return cur.strip().upper(), per.strip()


# ── MarketStack /v2/commodities ─────────────────────────────────────────────
def _ms_get(name, key):
    qs = urllib.parse.urlencode({"commodity_name": name, "access_key": key})
    url = "{}?{}".format(MS_BASE_URL, qs)
    req = urllib.request.Request(url, headers={"User-Agent": "Robotnik/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        try:
            return json.loads(body)
        except Exception:
            return {"error": {"code": "http_{}".format(e.code), "message": body[:160]}}
    except Exception as e:
        return {"error": {"code": "transport", "message": str(e)[:160]}}


def fetch_marketstack(fetch_keys):
    """Return {fetch_key: row|None}, plus a provenance string.

    Reads a pre-fetched cache when COMMODITIES_MS_CACHE is set (avoids the
    ~1-call/min live pull); otherwise live-pulls each name with a 63s throttle
    and rate-limit retry.
    """
    cache_path = os.environ.get("COMMODITIES_MS_CACHE")
    if cache_path:
        raw = json.loads(Path(cache_path).read_text())
        out = {}
        for k in fetch_keys:
            out[k] = raw.get(k) or raw.get(k.lower()) or raw.get(k.capitalize())
        return out, "cache:{}".format(cache_path)

    key = get_api_key()
    out = {}
    for i, name in enumerate(fetch_keys):
        if i:
            time.sleep(MS_RATE_SLEEP)               # respect ~1 call/min
        row = None
        for attempt in range(3):                    # rate-limit retry (65s backoff)
            data = _ms_get(name, key)
            rows = data.get("data") if isinstance(data, dict) else None
            if rows:
                row = rows[0]
                break
            err = (data.get("error") or {}) if isinstance(data, dict) else {}
            code = (err.get("code") or "").lower() if isinstance(err, dict) else ""
            if ("rate" in code or "limit" in code) and attempt < 2:
                sys.stderr.write("[commodities] rate-limit on {} — backoff 65s "
                                 "(attempt {}/2)\n".format(name, attempt + 1))
                time.sleep(65)
                continue
            sys.stderr.write("[commodities] MarketStack MISS {}: {}\n".format(name, err))
            break
        out[name] = row
    return out, "live"


def _smi_scan(region, label):
    m = re.search(re.escape(label) + r"\s*\$\s*([\d,]+\.\d+)", region)
    return float(m.group(1).replace(",", "")) if m else None


def fetch_smi(labels):
    """Scrape the current-prices table → (prices, last_updated, note).

    Honours COMMODITIES_SMI_CACHE ({label: usd_per_kg}) for sim/test, else
    scrapes live. Anchors on the 'Current Price (USD/kg)' header and requires
    the '$' so we match the price table, never the page's meta-description.
    """
    cache_path = os.environ.get("COMMODITIES_SMI_CACHE")
    if cache_path:
        raw = json.loads(Path(cache_path).read_text())
        return ({k: float(raw[k]) for k in labels if k in raw},
                raw.get("_last_updated", "cache"), "cache:{}".format(cache_path))

    req = urllib.request.Request(SMI_URL, headers={"User-Agent": SMI_UA})
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    upd = re.search(r"[Uu]pdated\s+([A-Z][a-z]{2,}\.?\s+\d{1,2},?\s+\d{4})", text)
    last_updated = upd.group(1).strip() if upd else None
    hdr = text.find("Current Price (USD/kg)")
    region = text[hdr: hdr + 4000] if hdr >= 0 else text
    prices = {label: _smi_scan(region, label) for label in labels}
    prices = {k: v for k, v in prices.items() if v is not None}
    return prices, last_updated, ("USD/kg header" if hdr >= 0 else "no header anchor")


# ── §6.1 live weights (genesis only): renormalise across priced, then 12% cap ─
def compute_capped_weights(ref_by_name, cap=SINGLE_NAME_CAP):
    """Renormalise reference weights to 1.0, then iterative single-name cap with
    pro-rata redistribution (pattern lifted from calculate_index.py)."""
    total = sum(ref_by_name.values())
    if total <= 0:
        return {k: 0.0 for k in ref_by_name}
    w = {k: v / total for k, v in ref_by_name.items()}
    for _ in range(50):
        capped = {k: x for k, x in w.items() if x > cap + 1e-12}
        if not capped:
            break
        excess = sum(x - cap for x in capped.values())
        uncapped = {k: x for k, x in w.items() if x <= cap + 1e-12}
        uncapped_total = sum(uncapped.values())
        if uncapped_total == 0:
            break
        for k in capped:
            w[k] = cap
        for k in uncapped:
            w[k] += excess * (uncapped[k] / uncapped_total)
    return w


def normalize_weights(weight_by, cap=SINGLE_NAME_CAP):
    """Force Σ weights = exactly 1.0 at full precision. Pin any capped name at `cap`
    and absorb the residual UNIFORMLY across the uncapped names — a ~0.0001% scale-up
    of the uncapped set, NOT a redistribution (a capped name stays pinned at 12.00%).

    Root cause of the 99.9999% sum: compute_capped_weights already returns full-precision
    weights summing to 1.0, but they are STORED rounded to 4dp (live_weight_pct), so the
    weekly path reads a set summing to 0.999999 — which left the formula at 999.999 at
    parity. Re-normalising the computed/loaded weights here makes the LIVE weight sum
    exactly 1.0 in both the genesis and weekly paths.
    """
    capped = {k for k, v in weight_by.items() if v >= cap - 1e-9}
    uncapped_sum = sum(v for k, v in weight_by.items() if k not in capped)
    target = 1.0 - cap * len(capped)
    if uncapped_sum <= 0 or target <= 0:
        return dict(weight_by)
    scale = target / uncapped_sum
    return {k: (cap if k in capped else v * scale) for k, v in weight_by.items()}


# ── per-constituent current snapshot (shared by genesis + weekly) ───────────
def build_snapshot(source, key, ms_rows, smi_prices, smi_updated, today):
    """Return (snapshot|None, fx_stale_flag|None, miss_reason|None)."""
    if source == "marketstack":
        row = ms_rows.get(key)
        if not row or row.get("commodity_price") in (None, ""):
            return None, None, "no row/price for '{}'".format(key)
        try:
            native_price = float(str(row["commodity_price"]).replace(",", ""))
        except (ValueError, KeyError):
            return None, None, "unparseable price"
        native_ccy, native_unit = parse_currency_unit(row.get("commodity_unit", ""))
        src_ts = row.get("datetime")
        quote_date = str(src_ts)[:10] if src_ts else today
    else:  # smi
        if key not in smi_prices:
            return None, None, "not found in table"
        native_price = smi_prices[key]
        native_ccy, native_unit = "USD", "kg"
        src_ts = smi_updated
        quote_date = today

    try:
        usd_price = cc.to_usd(native_price, native_ccy, quote_date)
    except cc.CurrencyError as ce:
        return None, None, "currency:{}".format(str(ce)[:80])
    fx_used = 1.0 if native_ccy == "USD" else cc.fx_rate(native_ccy, quote_date)

    fx_date, fx_flag = None, None
    if native_ccy != "USD":
        entry = cc._FX_CACHE.get(native_ccy if native_ccy not in ("GBp", "GBX") else "GBP")
        if entry and entry["dates"]:
            i = bisect.bisect_right(entry["dates"], quote_date)
            fx_date = entry["dates"][i - 1] if i > 0 else entry["dates"][0]
            gap = (datetime.strptime(quote_date, "%Y-%m-%d")
                   - datetime.strptime(fx_date, "%Y-%m-%d")).days
            if gap > FX_STALE_WARN_DAYS:
                fx_flag = ("FX STALE: {} converted with {} FX dated {} ({}d old vs quote {})"
                           .format(key, native_ccy, fx_date, gap, quote_date))
    snap = {
        "native_price": native_price, "native_unit": native_unit, "native_currency": native_ccy,
        "fx_rate_to_usd": round(fx_used, 8), "fx_date_used": fx_date,
        "usd_price": round(usd_price, 6),
        "price_unit_usd": "USD/{}".format(native_unit) if native_unit else "USD",
        "quote_date": quote_date, "source_timestamp": src_ts,
    }
    return snap, fx_flag, None


# ── idempotent forward-append (ISO-week keyed; base point immutable) ─────────
def _iso_week(d):
    y, m, dd = map(int, str(d)[:10].split("-"))
    return date(y, m, dd).isocalendar()[:2]


def append_or_update(series, mark, value, base_date):
    """Forward-append {mark, value}. The base point (date == base_date) is
    immutable. If the LAST point is a NON-base point in the same ISO week as
    `mark` (a re-run within the week), update it in place; otherwise append.
    Prior weeks are never recomputed. Returns the action taken (for logging)."""
    if not series:
        series.append({"date": mark, "value": value})
        return "appended (empty series)"
    last = series[-1]
    # base guard INLINE (matches composite advance() :117): the base point is never
    # updated in place, even when the mark shares its ISO week. Behaviour-equivalent to
    # the prior `last["date"] != base_date and same_week` that was consumed in the if.
    last_in_week = (last["date"] != base_date) and (
        (last["date"] == mark) or (_iso_week(last["date"]) == _iso_week(mark)))
    if last_in_week:
        series[-1] = {"date": mark, "value": value}
        return "updated-in-place (current week re-run)"
    series.append({"date": mark, "value": value})
    return "appended"


def load_existing(path):
    try:
        return json.loads(Path(path).read_text())
    except Exception:
        return None


# ── base prices: secret -> published fields (first run only) -> stop ────────
SECRET_HINT = ("Set the {} repository secret to the JSON object {{commodity: base_price_usd}} "
               "(see docs/RAW_PRICE_HANDLING.md).".format(BASE_PRICES_ENV))


def _stop(lines, fetched=False):
    """Fail loudly. Messages name commodities only, never a price (logs are public)."""
    sys.stderr.write("\nERROR: commodities index not advanced; {}nothing written.\n".format(
        "" if fetched else "nothing fetched, "))
    for line in lines:
        sys.stderr.write("  {}\n".format(line))
    sys.exit(1)


def _is_pos_num(v):
    return (isinstance(v, (int, float)) and not isinstance(v, bool)
            and math.isfinite(v) and v > 0)


def canonical_base_prices(bases):
    """The exact string base_prices_sha256 covers: JSON with keys sorted, no
    whitespace (separators "," and ":"), ASCII only, every value converted to a
    float and written in Python's shortest round-trip repr (as json.dumps writes
    floats, e.g. 17980 -> 17980.0), UTF-8 encoded. Pasting this string into the
    secret is valid; so is any JSON with the same names and values."""
    return json.dumps({k: float(v) for k, v in bases.items()}, sort_keys=True,
                      separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def base_prices_sha256(bases):
    return hashlib.sha256(canonical_base_prices(bases).encode("utf-8")).hexdigest()


def genesis_bases_path():
    """COMMODITIES_GENESIS_BASES_OUT as a resolved path, confined to a file inside
    the gitignored data/private/ (relative paths are taken from the repo root, and
    symlinks are resolved, so nothing can point outside it). Stops otherwise."""
    if not GENESIS_BASES_OUT:
        _stop(["This run would re-baseline the index (genesis: no usable prior record, or "
               "COMMODITIES_GENESIS=1).",
               "Its new base prices are never published, so set COMMODITIES_GENESIS_BASES_OUT "
               "to a file in data/private/ to receive them, then replace the {} secret.".format(
                   BASE_PRICES_ENV)])
    p = Path(GENESIS_BASES_OUT)
    p = (p if p.is_absolute() else ROOT / p).resolve()
    private = PRIVATE_DIR.resolve()
    if private not in p.parents or p.is_dir():
        _stop(["COMMODITIES_GENESIS_BASES_OUT must name a file inside data/private/ "
               "(gitignored); refusing {}.".format(GENESIS_BASES_OUT)])
    return p


def resolve_base_prices(prior):
    """{commodity: base_price_usd} for every constituent of the prior record, and
    the source used. Read order: the COMMODITIES_BASE_PRICES secret; else the
    base_price_usd still on the published constituents (the first run after the
    change only); else stop. The bases must then hash to the record's
    base_prices_sha256 when it carries one; a record with neither the hash nor the
    legacy fields cannot vouch for any bases, so the run stops. Every check runs
    before any fetch, and no message contains a value."""
    names = [c["commodity"] for c in prior["constituents"]]
    published = {c["commodity"]: c["base_price_usd"] for c in prior["constituents"]
                 if "base_price_usd" in c}
    bases, source = _read_base_prices(names, published)
    record_hash = prior.get(BASE_HASH_KEY)
    if record_hash is not None:
        if base_prices_sha256(bases) != record_hash:
            _stop(["The base prices from {} do not match the {} in the published record.".format(
                       source, BASE_HASH_KEY),
                   "The secret is mistyped or stale (for example, not replaced after a "
                   "re-baseline). It must hold the bases this record was built on.",
                   SECRET_HINT])
    elif not published:
        _stop(["The published record carries neither base_price_usd nor {}, so no base "
               "prices can be verified against it.".format(BASE_HASH_KEY),
               "Restore the record's {} (see docs/RAW_PRICE_HANDLING.md).".format(BASE_HASH_KEY)])
    return bases, source


def _read_base_prices(names, published):
    raw = os.environ.get(BASE_PRICES_ENV, "").strip()
    if raw:
        try:
            secret = json.loads(raw)
        except ValueError:
            _stop(["{} is set but is not valid JSON.".format(BASE_PRICES_ENV), SECRET_HINT])
        if not isinstance(secret, dict):
            _stop(["{} must be a JSON object, not a {}.".format(
                BASE_PRICES_ENV, type(secret).__name__), SECRET_HINT])
        problems = []
        missing = sorted(set(names) - set(secret))
        extra = sorted(set(secret) - set(names))
        invalid = sorted(n for n in names if n in secret and not _is_pos_num(secret[n]))
        if missing:
            problems.append("missing: {}".format(", ".join(missing)))
        if extra:
            problems.append("not a published constituent: {}".format(", ".join(extra)))
        if invalid:
            problems.append("not a positive number: {}".format(", ".join(invalid)))
        if published and not problems:
            # First run after the change: the record still carries the bases, so the
            # secret must reproduce them exactly.
            differ = sorted(n for n in names if published.get(n) != secret[n])
            if differ:
                problems.append("differs from the published base_price_usd: {}".format(
                    ", ".join(differ)))
        if problems:
            _stop(["{} does not match the published record ({} constituents):".format(
                BASE_PRICES_ENV, len(names))] + problems + [SECRET_HINT])
        return {n: secret[n] for n in names}, "secret {}".format(BASE_PRICES_ENV)
    if published:
        invalid = sorted(n for n in names if not _is_pos_num(published.get(n)))
        if invalid:
            _stop(["the published base_price_usd is missing or invalid for: {}".format(
                ", ".join(invalid)), SECRET_HINT])
        return ({n: published[n] for n in names},
                "published record (first run after the change; base_price_usd is now dropped)")
    _stop(["{} is not set, and the published record no longer carries base_price_usd.".format(
        BASE_PRICES_ENV), SECRET_HINT])


def main():
    print("=" * 64)
    print("ROBOTNIK COMMODITIES INDEX")
    print("=" * 64)

    today = MARK_DATE_OVERRIDE or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "") + "Z"

    # ── 0. Prior record + base prices, resolved BEFORE any fetch, so a run that
    #       cannot advance stops without spending the MarketStack pull ──────────
    prior = None if FORCE_GENESIS else load_existing(OUT_PATH)
    genesis = not (prior and prior.get("constituents") and prior.get("series"))
    if genesis:
        bases_out = genesis_bases_path()            # confined to data/private/, else stop
        stored_base, base_source = {}, "genesis (new bases from this run's prices)"
    else:
        stored_base, base_source = resolve_base_prices(prior)
    print("\nBase prices from: {}".format(base_source))

    # ── 1. Refresh FX, fetch current spot ───────────────────────────────────
    for ccy in ("CNY",):                 # only non-USD quote currency in the set
        cc.ensure_fx(ccy, fetcher=fetch_fx_daily)
    ms_keys = [c[4] for c in PRICED if c[2] == "marketstack"]
    smi_keys = [c[4] for c in PRICED if c[2] == "smi"]
    print("\nFetching MarketStack ({} names) ...".format(len(ms_keys)))
    ms_rows, ms_provenance = fetch_marketstack(ms_keys)
    print("  source: {}".format(ms_provenance))
    print("Scraping strategicmetalsinvest ({} names) ...".format(len(smi_keys)))
    smi_prices, smi_updated, smi_note = fetch_smi(smi_keys)
    print("  last updated: {} ({}); resolved {}/{}".format(
        smi_updated, smi_note, len(smi_prices), len(smi_keys)))

    # ── 2. Current snapshot per constituent ─────────────────────────────────
    snaps, missing, flags = {}, [], []
    for commodity, ref_w, source, basis, key in PRICED:
        snap, fx_flag, miss = build_snapshot(source, key, ms_rows, smi_prices, smi_updated, today)
        if miss:
            missing.append((commodity, source, miss))
            continue
        if fx_flag:
            flags.append(fx_flag.replace(key, commodity, 1))
        snaps[commodity] = snap

    # Stale-fixing flag (MarketStack flat over week & month) — informational.
    for commodity, ref_w, source, basis, key in PRICED:
        if source != "marketstack":
            continue
        row = ms_rows.get(key) or {}
        flat = ("0.00%", "0%", "0", 0, 0.0)
        if row.get("percentage_week") in flat and row.get("percentage_month") in flat:
            flags.append("STALE FIXING: {} flat 0.00% over week & month "
                         "(illiquid/stale fixing).".format(commodity))

    # ── 3. Resolve base prices + fixed live weights ─────────────────────────
    if genesis:
        priced = [(c, w) for (c, w, s, b, k) in PRICED if c in snaps]
        ref_by = {c: w for c, w in priced}
        priced_ref_sum = sum(ref_by.values())
        live = compute_capped_weights(ref_by)                 # {commodity: fraction}
        weight_by = normalize_weights({c: live[c] for c in ref_by})   # Σ → exactly 1.0
        base_by = {c: snaps[c]["usd_price"] for c in ref_by}
        base_date = today
    else:
        base_date = prior["base_date"]
        weight_by = normalize_weights(
            {c["commodity"]: c["live_weight_pct"] / 100.0 for c in prior["constituents"]})  # un-round stored 4dp → Σ exactly 1.0
        base_by = stored_base                          # secret, or the legacy fields (step 0)
        priced_ref_sum = prior.get("priced_reference_weight_pct", 0.0)

    # ── 4. Build constituent records + index = 1000 * Σ(w * cur/base) ────────
    prior_by = {c["commodity"]: c for c in (prior["constituents"] if not genesis else [])}
    constituents = []
    idx_sum = 0.0    # full-precision Σ(weight × relative) — the index basis (no intermediate rounding)
    for commodity, ref_w, source, basis, key in PRICED:
        if commodity not in weight_by:        # not in the priced set (genesis miss)
            continue
        base_usd = base_by[commodity]
        snap = snaps.get(commodity)
        carried = False
        if snap is None:
            # No fresh price: hold the last observation (§8) by carrying the PRIOR
            # PUBLISHED relative_to_base (derived, already public), never a raw price.
            pc = prior_by.get(commodity)
            if not pc:
                missing.append((commodity, source, "no fresh price and no prior to carry"))
                continue
            rel = pc.get("relative_to_base")
            if not (isinstance(rel, (int, float)) and not isinstance(rel, bool)
                    and math.isfinite(rel)):
                _stop(["{} has no fresh price and the prior record has no usable "
                       "relative_to_base to carry.".format(commodity)], fetched=True)
            carried = True
            snap = {k: pc.get(k) for k in ("native_currency", "fx_rate_to_usd", "fx_date_used",
                                           "price_unit_usd", "quote_date", "source_timestamp")}
            flags.append("CARRIED: {} held last observation (no fresh price this run).".format(commodity))
        else:
            rel = snap["usd_price"] / base_usd if base_usd else 1.0
        contrib_fp = weight_by[commodity] * rel        # full precision (the index basis)
        idx_sum += contrib_fp
        c = {
            "commodity": commodity,
            "source": SOURCE_LABEL[source],
            "basis": basis,
            # Raw prices (native spot, USD spot, base) are never published (ToS;
            # CLAUDE.md served-data rule). relative_to_base is derived and published
            # at full float precision, so next week's carry of it is exact.
            "native_currency": snap["native_currency"],
            "fx_rate_to_usd": snap["fx_rate_to_usd"], "fx_date_used": snap["fx_date_used"],
            "price_unit_usd": snap["price_unit_usd"],
            "relative_to_base": rel,
            "live_weight_pct": round(weight_by[commodity] * 100.0, 6),
            "reference_weight_pct": ref_w,
            "weight_contribution": round(contrib_fp, 8),
            "quote_date": snap["quote_date"], "source_timestamp": snap["source_timestamp"],
            "carried_last_observation": carried,
        }
        if genesis:
            c["renormalised_weight_pct"] = round(ref_w / priced_ref_sum * 100.0, 4)
            c["capped"] = abs(weight_by[commodity] - SINGLE_NAME_CAP) < 1e-9
        else:
            pc = prior_by.get(commodity, {})
            c["renormalised_weight_pct"] = pc.get("renormalised_weight_pct")
            c["capped"] = pc.get("capped", False)
        constituents.append(c)

    constituents.sort(key=lambda x: x["live_weight_pct"], reverse=True)
    index_value = round(BASE_VALUE * idx_sum, 2)        # full-precision basis → exactly 1000.0 at genesis
    weight_sum = round(sum(weight_by[c["commodity"]] for c in constituents) * 100.0, 6)  # normalized → 100.0
    gallium_w = next((c["live_weight_pct"] for c in constituents if c["commodity"] == "Gallium"), None)
    max_w = max((c["live_weight_pct"] for c in constituents), default=0.0)
    if missing:
        for name, src, why in missing:
            flags.append("MISSING: {} ({}) — {}".format(name, src, why))

    # ── 5. Series (genesis = single base point; weekly = idempotent append) ──
    if genesis:
        series = [{"date": base_date, "value": index_value}]
        action = "genesis"
    else:
        series = [dict(p) for p in prior["series"]]
        action = append_or_update(series, today, index_value, base_date)

    # ── 6. Assemble record ──────────────────────────────────────────────────
    sources = {
        "marketstack": {"endpoint": "v2/commodities", "provenance": ms_provenance, "names": len(ms_keys)},
        "strategicmetalsinvest": {"url": SMI_URL, "last_updated": smi_updated, "names": len(smi_keys)},
    }
    if genesis:
        record = {
            "name": "Robotnik Commodities Index",
            "code": "RCMI",
            "version": "1.1 — forward-only launch (genesis base); v.3 price-basis routing",
            "methodology": "commodities_index_methodology v.3",
            "method": ("fixed-weight index of USD price relatives; index = 1000 * Σ(live_weight_i * "
                       "usd_price_i/base_i); §6.1 live weights (reference renormalised across priced "
                       "constituents, 12% single-name cap); forward-only, no backfill"),
            "price_basis_routing": (
                "§8: chokepoints Ga/Ge/In/Nd from strategicmetalsinvest (Western/ex-China, USD/kg, "
                "metal); exchange-traded from MarketStack benchmarks; China-domestic (MarketStack CNY, "
                "flagged) only where no free Western reference exists — Silicon, Titanium, Phosphorus; "
                "rare earths on metal basis"),
            "frequency": "weekly",
            "base_date": base_date, "base_value": BASE_VALUE,
            "priced_count": len(constituents), "price_pending_count": len(PENDING),
            "priced_reference_weight_pct": round(priced_ref_sum, 2),
            "excluded_reference_weight_pct": round(100.0 - priced_ref_sum, 2),
            "single_name_cap_pct": SINGLE_NAME_CAP * 100.0,
            "weights_check": {"sum_live_weight_pct": weight_sum, "gallium_live_weight_pct": gallium_w,
                              "max_weight_pct": round(max_w, 4),
                              "cap_binds_on": [c["commodity"] for c in constituents if c["capped"]]},
            "fx": {"path": "scripts/currency_convert.to_usd (project per-date FX; ECB-primary)",
                   "non_usd_currencies": sorted({c["native_currency"] for c in constituents
                                                 if c["native_currency"] != "USD"})},
            "price_pending": [{"commodity": n, "reference_weight_pct": w, "reason": r}
                              for (n, w, r) in PENDING],
        }
    else:
        record = dict(prior)             # carry all genesis-fixed fields
    record["current_value"] = series[-1]["value"]    # always the latest published point
    record["current_date"] = series[-1]["date"]
    record["constituents"] = constituents
    record["sources"] = sources
    record["flags"] = flags
    record["series"] = series
    record["last_update"] = {"action": action, "mark": today, "value": index_value, "at": now_iso}
    record["calculated_at"] = now_iso
    # Bind the record to the bases it was built on (every run; see canonical_base_prices).
    used_bases = {c["commodity"]: base_by[c["commodity"]] for c in constituents}
    record[BASE_HASH_KEY] = base_prices_sha256(used_bases)

    if genesis:
        # New bases go only to the confined private path, as the canonical string
        # (never printed or published), and before the record, so a published
        # genesis record always has its bases somewhere.
        bases_out.parent.mkdir(parents=True, exist_ok=True)
        bases_out.write_text(canonical_base_prices(used_bases))
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(record, f, indent=2)

    # ── 7. Surface ──────────────────────────────────────────────────────────
    # Relatives and weights only (both published); no raw price is printed.
    print("\nMODE: {}   base {} = {:.2f}".format("GENESIS" if genesis else "WEEKLY", base_date, BASE_VALUE))
    print("{:14s} {:>5s} {:>9s} {:>7s}".format("COMMODITY", "CCY", "REL", "LIVE%"))
    print("-" * 52)
    for c in constituents:
        print("{:14s} {:>5s} {:>9.5f} {:>6.2f}%{}".format(
            c["commodity"], c["native_currency"], c["relative_to_base"], c["live_weight_pct"],
            "  <cap>" if c["capped"] else ("  carry" if c["carried_last_observation"] else "")))
    print("-" * 52)
    print("Priced: {}/{}   weights sum: {:.4f}%   Gallium: {}%   max: {:.4f}%".format(
        len(constituents), len(PRICED), weight_sum, gallium_w, max_w))
    print("INDEX VALUE: {:.2f}   ({:+.2f} vs base 1000.00)   series action: {}".format(
        index_value, index_value - BASE_VALUE, action))
    print("series points: {} ({} → {})".format(len(series), series[0]["date"], series[-1]["date"]))
    if flags:
        print("\nFLAGS ({}):".format(len(flags)))
        for fl in flags:
            print("  ! {}".format(fl))
    try:
        _shown = OUT_PATH.relative_to(ROOT)
    except ValueError:
        _shown = OUT_PATH
    print("\nWrote -> {}".format(_shown))
    if genesis:
        print("New base prices -> {} (not printed). Paste that file's contents into the {} "
              "secret before the next weekly run.".format(GENESIS_BASES_OUT, BASE_PRICES_ENV))
    print("=" * 64)


if __name__ == "__main__":
    main()
