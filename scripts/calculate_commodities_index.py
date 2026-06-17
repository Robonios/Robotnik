#!/usr/bin/env python3
"""
Robotnik Commodities Index — forward-only launch / base-date snapshot
=====================================================================
Builds the Commodities Index per `commodities_index_methodology v.3` §6.1 / §8
("Live index weights — forward-only launch"; v.3 price-basis routing).

Constituents (20 priced) — routed by the §8 price-basis rule
------------------------------------------------------------
  * 12 via MarketStack v2 /commodities:
      - exchange-traded global benchmarks: Copper, Nickel, Tin, Cobalt, Gold,
        Silver, Platinum, Palladium, Aluminium ("aluminum" on MS)
      - China-domestic-quoted (CNY, FX-converted), no free Western reference:
        Silicon (metallurgical), Titanium (sponge), Phosphorus (phosphate rock)
  * 8 via strategicmetalsinvest (USD/kg, METAL basis):
      - China-controlled chokepoints on the WESTERN/ex-China quote (where
        export-control stress shows up): Gallium, Germanium, Indium, Neodymium
      - other priced rare earths / minor metals: Praseodymium, Dysprosium,
        Terbium, Antimony
  * 9 PRICE-PENDING (disclosed, excluded until a source is secured):
      Tungsten, Tantalum, Arsenic, Cerium, Lanthanum, Erbium, Yttrium,
      Scandium, Boron.

Price-basis rule (§8): for the China-controlled chokepoint metals where a free
Western/ex-China reference exists (Ga, Ge, In, Nd) use the WESTERN quote — a
China-domestic basis would blind the index to the export-control shocks it
exists to register (gallium rose several-fold in the West on the 2023 controls
while the China-domestic price barely moved). Exchange-traded metals use their
global benchmark; China-domestic is used (and flagged) only where nothing else
is free (Si, Ti, P). Rare earths tracked on METAL basis (the free SMI form).

Weighting (§6.1 live weights)
-----------------------------
  * Start from the §6 REFERENCE weights (the full 29-name frontier-intensity
    statement).
  * RENORMALISE across the priced constituents (drop the price-pending share,
    redistributed pro-rata — the honest-gap discipline).
  * Apply a 12% SINGLE-NAME CAP with pro-rata redistribution of the excess.
    Identical cap algorithm to calculate_index.py /
    calculate_bottleneck_composite.py — divergence is weighting only.

Pricing / FX
------------
  * Every native price is converted to USD via the project's per-date FX path
    (scripts/currency_convert.to_usd), so future weekly relatives stay
    currency-consistent. BOTH native and USD base prices are stored.
  * The index is a FIXED-WEIGHT index of USD price relatives, based at
    1000.00 on the launch date. At base date every relative == 1.0, so the
    index == 1000.00 by construction. FORWARD-ONLY: no backfill.

Output:  data/index/commodities_index.json   (this script does NOT git-commit)

Usage
-----
    python scripts/calculate_commodities_index.py
        Live pull: MarketStack /v2/commodities is rate-limited to ~1 call per
        minute, so a full live pull of the 12 MarketStack names takes ~12 min
        (the script throttles 63s between calls, with rate-limit retry).
        strategicmetalsinvest is a single scrape (8 names).

    COMMODITIES_MS_CACHE=/path/spot.json python scripts/calculate_commodities_index.py
        Read MarketStack spot from a pre-fetched cache instead of live-pulling
        (used for the genesis base-date snapshot and for re-runs, to avoid
        re-spending the rate-limited budget). Cache schema:
            { "<commodity_name>": { "commodity_price": "..",
                                    "commodity_unit": "usd/t.oz",
                                    "datetime": "2026-06-17T..." }, ... }
"""

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from marketstack_client import get_api_key          # noqa: E402  (API key resolution only)
import currency_convert as cc                        # noqa: E402
from fetch_fx import fetch_fx_daily                  # noqa: E402  (ECB-primary FX)

# Output dir for the base record. Defaults to the live index tree; a dry-run
# sets COMMODITIES_INDEX_OUT to write elsewhere (mirrors ROBOTNIK_INDEX_OUT).
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

# ── Constituents ───────────────────────────────────────────────────────────
# (commodity, reference_weight_pct, source, basis, fetch_key)
#   reference_weight_pct : §6 reference weight (full 29-name statement)
#   source               : "marketstack" | "smi"
#   fetch_key            : MarketStack commodity_name (lowercase) OR SMI label
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
    ~1-call/min live pull); otherwise live-pulls each name with a 63s throttle.
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


# ── strategicmetalsinvest (USD/kg table scrape) ─────────────────────────────
def fetch_smi(labels):
    """Scrape the current-prices table → (prices, last_updated, note).

    Anchors on the 'Current Price (USD/kg)' header and requires the '$' so we
    match the price table, never the metal names in the page's meta-description.
    """
    req = urllib.request.Request(SMI_URL, headers={"User-Agent": SMI_UA})
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)

    # Page wording is "updated Jun 16 2026" (lowercase, abbreviated month, no comma).
    upd = re.search(r"[Uu]pdated\s+([A-Z][a-z]{2,}\.?\s+\d{1,2},?\s+\d{4})", text)
    last_updated = upd.group(1).strip() if upd else None

    hdr = text.find("Current Price (USD/kg)")
    region = text[hdr: hdr + 4000] if hdr >= 0 else text
    prices = {label: _smi_scan(region, label) for label in labels}
    prices = {k: v for k, v in prices.items() if v is not None}
    return prices, last_updated, ("USD/kg header" if hdr >= 0 else "no header anchor")


# ── §6.1 live weights: renormalise across priced, then 12% cap ──────────────
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


def main():
    print("=" * 64)
    print("ROBOTNIK COMMODITIES INDEX — base-date snapshot (forward-only)")
    print("=" * 64)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # ── 1. Refresh the FX currencies we will need (USD is a no-op) ──────────
    needed_ccy = {"CNY"}    # the only non-USD quote currency in the priced set
    for ccy in sorted(needed_ccy):
        cc.ensure_fx(ccy, fetcher=fetch_fx_daily)

    # ── 2. Fetch spot ───────────────────────────────────────────────────────
    ms_keys = [c[4] for c in PRICED if c[2] == "marketstack"]
    smi_keys = [c[4] for c in PRICED if c[2] == "smi"]
    print("\nFetching MarketStack ({} names) ...".format(len(ms_keys)))
    ms_rows, ms_provenance = fetch_marketstack(ms_keys)
    print("  source: {}".format(ms_provenance))
    print("Scraping strategicmetalsinvest ({} names) ...".format(len(smi_keys)))
    smi_prices, smi_updated, smi_note = fetch_smi(smi_keys)
    print("  last updated: {} ({}); resolved {}/{}".format(
        smi_updated, smi_note, len(smi_prices), len(smi_keys)))

    # ── 3. Build constituent records (native + USD via per-date FX) ─────────
    constituents = []
    missing = []
    flags = []
    for commodity, ref_w, source, basis, key in PRICED:
        native_price = native_unit = native_ccy = quote_date = src_ts = None
        if source == "marketstack":
            row = ms_rows.get(key)
            if not row or row.get("commodity_price") in (None, ""):
                missing.append((commodity, "marketstack", "no row/price for '{}'".format(key)))
                continue
            try:
                native_price = float(str(row["commodity_price"]).replace(",", ""))
            except (ValueError, KeyError):
                missing.append((commodity, "marketstack", "unparseable price"))
                continue
            native_ccy, native_unit = parse_currency_unit(row.get("commodity_unit", ""))
            src_ts = row.get("datetime")
            quote_date = str(src_ts)[:10] if src_ts else today
        else:  # smi
            if key not in smi_prices:
                missing.append((commodity, "smi", "not found in table"))
                continue
            native_price = smi_prices[key]
            native_ccy, native_unit = "USD", "kg"
            src_ts = smi_updated
            quote_date = today    # FX is a no-op for USD; date kept for record

        # Convert to USD via the project per-date FX path.
        try:
            usd_price = cc.to_usd(native_price, native_ccy, quote_date)
        except cc.CurrencyError as ce:
            missing.append((commodity, source, "currency:{}".format(str(ce)[:80])))
            continue
        fx_used = 1.0 if native_ccy == "USD" else cc.fx_rate(native_ccy, quote_date)

        # FX staleness flag (CNY series can lag; data/prices/fx is gitignored).
        fx_date = None
        if native_ccy != "USD":
            entry = cc._FX_CACHE.get(native_ccy if native_ccy not in ("GBp", "GBX") else "GBP")
            if entry and entry["dates"]:
                import bisect
                idx = bisect.bisect_right(entry["dates"], quote_date)
                fx_date = entry["dates"][idx - 1] if idx > 0 else entry["dates"][0]
                gap = (datetime.strptime(quote_date, "%Y-%m-%d")
                       - datetime.strptime(fx_date, "%Y-%m-%d")).days
                if gap > FX_STALE_WARN_DAYS:
                    flags.append("FX STALE: {} converted with {} FX dated {} ({}d old vs quote {})".format(
                        commodity, native_ccy, fx_date, gap, quote_date))

        constituents.append({
            "commodity": commodity,
            "source": "MarketStack v2 /commodities" if source == "marketstack" else "strategicmetalsinvest",
            "basis": basis,
            "native_price": native_price,
            "native_unit": native_unit,
            "native_currency": native_ccy,
            "fx_rate_to_usd": round(fx_used, 8),
            "fx_date_used": fx_date,
            "usd_price": round(usd_price, 6),
            "price_unit_usd": "USD/{}".format(native_unit) if native_unit else "USD",
            "base_price_usd": round(usd_price, 6),     # the immutable launch base price
            "quote_date": quote_date,
            "source_timestamp": src_ts,
            "reference_weight_pct": ref_w,
        })

    # ── 4. §6.1 live weights over the ACTUALLY-priced set ───────────────────
    priced_names = [c["commodity"] for c in constituents]
    ref_by_name = {c["commodity"]: c["reference_weight_pct"] for c in constituents}
    priced_ref_sum = sum(ref_by_name.values())
    live = compute_capped_weights(ref_by_name)

    for c in constituents:
        renorm = c["reference_weight_pct"] / priced_ref_sum * 100.0
        c["renormalised_weight_pct"] = round(renorm, 4)
        c["live_weight_pct"] = round(live[c["commodity"]] * 100.0, 4)
        c["capped"] = abs(live[c["commodity"]] - SINGLE_NAME_CAP) < 1e-9
    constituents.sort(key=lambda x: x["live_weight_pct"], reverse=True)

    weight_sum = round(sum(c["live_weight_pct"] for c in constituents), 4)
    gallium_w = next((c["live_weight_pct"] for c in constituents if c["commodity"] == "Gallium"), None)
    max_w = max((c["live_weight_pct"] for c in constituents), default=0.0)

    # ── 5. Index value: fixed-weight USD price relatives, base 1000.00 ──────
    # At base date every relative == 1.0, so value == BASE_VALUE structurally.
    index_value = round(sum((live[c["commodity"]]) * 1.0 for c in constituents) * BASE_VALUE, 2)

    # ── 6. Curated anomaly flags for review (do not block) ──────────────────
    if missing:
        for name, src, why in missing:
            flags.append("MISSING: {} ({}) — {}".format(name, src, why))

    # 6b. Stale-fixing flag: a MarketStack name flat over BOTH week and month is
    #     an illiquid/stale fixing (e.g. LME cobalt) — its base price is a stale
    #     print. Informational. (Only fires when percentage fields are present.)
    for commodity, ref_w, source, basis, key in PRICED:
        if source != "marketstack":
            continue
        row = ms_rows.get(key) or {}
        flat = ("0.00%", "0%", "0", 0, 0.0)
        if row.get("percentage_week") in flat and row.get("percentage_month") in flat:
            flags.append("STALE FIXING: {} flat 0.00% over week & month "
                         "(illiquid/stale fixing — base price is a stale print).".format(commodity))

    # ── 7. Assemble base record ─────────────────────────────────────────────
    record = {
        "name": "Robotnik Commodities Index",
        "version": "1.1 — forward-only launch (genesis base); v.3 price-basis routing",
        "methodology": "commodities_index_methodology v.3",
        "method": ("fixed-weight index of USD price relatives; §6.1 live weights "
                   "(reference weights renormalised across priced constituents, then "
                   "12% single-name cap with pro-rata redistribution); forward-only, no backfill"),
        "price_basis_routing": (
            "§8: chokepoints Ga/Ge/In/Nd priced from strategicmetalsinvest (Western/ex-China, "
            "USD/kg, metal) so the index registers export-control stress; exchange-traded metals "
            "from MarketStack benchmarks; China-domestic (MarketStack CNY, flagged) only where no "
            "free Western reference exists — Silicon, Titanium, Phosphorus; rare earths on metal basis"),
        "frequency": "weekly",
        "base_date": today,
        "base_value": BASE_VALUE,
        "current_value": index_value,
        "current_date": today,
        "priced_count": len(constituents),
        "price_pending_count": len(PENDING),
        "priced_reference_weight_pct": round(priced_ref_sum, 2),
        "excluded_reference_weight_pct": round(100.0 - priced_ref_sum, 2),
        "single_name_cap_pct": SINGLE_NAME_CAP * 100.0,
        "weights_check": {
            "sum_live_weight_pct": weight_sum,
            "gallium_live_weight_pct": gallium_w,
            "max_weight_pct": round(max_w, 4),
            "cap_binds_on": [c["commodity"] for c in constituents if c["capped"]],
        },
        "fx": {
            "path": "scripts/currency_convert.to_usd (project per-date FX; ECB-primary)",
            "non_usd_currencies": sorted({c["native_currency"] for c in constituents
                                          if c["native_currency"] != "USD"}),
        },
        "sources": {
            "marketstack": {"endpoint": "v2/commodities", "provenance": ms_provenance,
                            "names": len(ms_keys)},
            "strategicmetalsinvest": {"url": SMI_URL, "last_updated": smi_updated,
                                      "names": len(smi_keys)},
        },
        "constituents": constituents,
        "price_pending": [{"commodity": n, "reference_weight_pct": w, "reason": r}
                          for (n, w, r) in PENDING],
        "flags": flags,
        "series": [{"date": today, "value": index_value}],
        "calculated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "") + "Z",
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(record, f, indent=2)

    # ── 8. Surface ───────────────────────────────────────────────────────────
    print("\n{:14s} {:>14s} {:>6s} {:>16s}  {:>7s} {:>7s} {:>7s}".format(
        "COMMODITY", "NATIVE", "CCY", "USD (base)", "REF%", "RENRM%", "LIVE%"))
    print("-" * 80)
    for c in constituents:
        print("{:14s} {:>14.4f} {:>6s} {:>16.4f}  {:>6.2f}% {:>6.2f}% {:>6.2f}%{}".format(
            c["commodity"], c["native_price"], c["native_currency"], c["usd_price"],
            c["reference_weight_pct"], c["renormalised_weight_pct"], c["live_weight_pct"],
            "  <cap>" if c["capped"] else ""))
    print("-" * 80)
    print("Priced: {}/{}   priced ref-weight: {:.2f}%   excluded (9 pending): {:.2f}%".format(
        len(constituents), len(PRICED), priced_ref_sum, 100.0 - priced_ref_sum))
    print("Weights check  ->  sum: {:.4f}%   Gallium: {}%   max: {:.4f}%".format(
        weight_sum, gallium_w, max_w))
    print("INDEX VALUE (base {}):  {:.2f}".format(today, index_value))
    if missing:
        print("\nMISSING / UNPRICED (would shrink the priced set):")
        for name, src, why in missing:
            print("  - {} ({}): {}".format(name, src, why))
    if flags:
        print("\nFLAGS ({}):".format(len(flags)))
        for fl in flags:
            print("  ! {}".format(fl))
    print("\nPrice-pending (9, disclosed/excluded): {}".format(
        ", ".join(n for n, _, _ in PENDING)))
    try:
        _shown = OUT_PATH.relative_to(ROOT)
    except ValueError:
        _shown = OUT_PATH      # dry-run path outside the repo (COMMODITIES_INDEX_OUT)
    print("\nWrote -> {}".format(_shown))
    print("=" * 64)


if __name__ == "__main__":
    main()
