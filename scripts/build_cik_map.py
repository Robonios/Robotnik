#!/usr/bin/env python3
"""
Build data/registries/cik_map.json — the registry x SEC CIK join.
=================================================================
WHY THIS EXISTS
  cik_map.json is read by build_asset_profiles.py to stamp each active-public
  asset profile with its SEC CIK (cik_by[join_key], join_key = public_ticker or
  id). Until now NO script produced it: it was written by hand on 2026-07-04 and
  drifted from the registry exactly as search_index.json did - 24 active-public
  names missing (ten of them US filers that should carry a CIK), 18 excluded
  names still listed. A served join with no reproducible build goes stale
  silently. This is that build.

CONTRACT (the shape the committed file uses; build_asset_profiles reads only the
matched ticker -> cik pairs, so a superset is safe, a dropped field is not):
  top level : {generated_at, source, matched[], unmatched[]}
  matched   : {ticker, cik, sec_title, matched_by}   (sorted by ticker)
  unmatched : {ticker, name, country}                (sorted by ticker)

THE JOIN (reverse-engineered from the committed data, verified exact on retained
entities):
  universe : entity_registry.json active-public (status == null AND type ==
             "public") - 203 today.
  ticker   : each output "ticker" is the CONSUMER'S key, public_ticker or id.
             The committed file used the registry id, which silently misses for
             the one entity whose id != public_ticker (cerebras-systems, id
             "cerebras-systems" vs ticker "CBRS"): build_asset_profiles looks up
             "CBRS" and finds nothing. Emitting public_ticker-or-id fixes that.
  lookup   : public_ticker.upper() against SEC company_tickers.json. Found ->
             matched {cik = cik_str zero-padded to 10, sec_title = SEC title,
             matched_by = "public_ticker"}. Not found (all non-US listings) ->
             unmatched {name, country from the registry}.

SEC SOURCE - unlike search_index (a pure registry projection), this map is a
  function of the registry AND an external file, https://www.sec.gov/files/
  company_tickers.json. fetch_filings.py fetches that file live and does NOT
  cache it, so there is no stored copy to read; this generator fetches it live
  too (same descriptive User-Agent the SEC requires). Consequence: the map can
  drift from the SEC side (a private name IPOs and gains a CIK) as well as the
  registry side - see the cadence note where this is surfaced.

Standard library only.

Usage:  python scripts/build_cik_map.py [--check] [--sec-file PATH]
        --sec-file PATH  read SEC company_tickers.json from disk instead of
                         fetching live (offline builds, tests, deterministic diff).
        --check          build in memory and report drift vs the committed file
                         (registry-set + CIK changes) WITHOUT writing; exit 1 if
                         it would change, 0 if up to date, 0 (with a notice) if
                         SEC is unreachable so a transient outage is not a false
                         alarm.
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY_PATH = os.path.join(ROOT, "data", "registries", "entity_registry.json")
OUT_PATH      = os.path.join(ROOT, "data", "registries", "cik_map.json")
SEC_URL       = "https://www.sec.gov/files/company_tickers.json"
# SEC requires a descriptive User-Agent with contact; mirrors fetch_filings.py.
USER_AGENT    = "Robotniks/1.0 (robotniks.com, data@robotniks.com)"


class SECUnavailable(Exception):
    pass


def load_sec(sec_file=None):
    """Return {TICKER_UPPER: (cik_zfill10, title)} from SEC company_tickers.json."""
    if sec_file:
        raw = json.load(open(sec_file))
    else:
        req = urllib.request.Request(SEC_URL, headers={
            "User-Agent": USER_AGENT, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw = json.loads(resp.read().decode())
        except Exception as e:
            raise SECUnavailable("{}: {}".format(type(e).__name__, str(e)[:120]))
    sec = {}
    for entry in raw.values():
        t = str(entry.get("ticker", "")).upper()
        if t:
            sec[t] = (str(entry.get("cik_str", "")).zfill(10), entry.get("title"))
    return sec


def build_index(registry, sec):
    """Join active-public entities against the SEC map into the served shape."""
    matched, unmatched = [], []
    for rid, r in registry.items():
        if r.get("status") is not None or r.get("type") != "public":
            continue
        key = r.get("public_ticker") or rid          # the consumer's join_key
        hit = sec.get(str(r.get("public_ticker") or "").upper())
        if hit:
            matched.append({"ticker": key, "cik": hit[0],
                            "sec_title": hit[1], "matched_by": "public_ticker"})
        else:
            unmatched.append({"ticker": key, "name": r.get("name"),
                              "country": r.get("country")})
    matched.sort(key=lambda e: e["ticker"])
    unmatched.sort(key=lambda e: e["ticker"])
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "entity_registry.json (active-public) x " + SEC_URL,
        "matched": matched,
        "unmatched": unmatched,
    }


def _diff(old, new):
    """Compare two cik_maps by ticker; ignore timestamp. Returns dict of deltas."""
    def cikof(doc):
        return {m["ticker"]: m["cik"] for m in doc.get("matched", [])}
    def titleof(doc):
        return {m["ticker"]: m.get("sec_title") for m in doc.get("matched", [])}
    def tickers(doc):
        return {e["ticker"] for e in doc.get("matched", [])} | {e["ticker"] for e in doc.get("unmatched", [])}
    ot, nt = tickers(old), tickers(new)
    oc, nc = cikof(old), cikof(new)
    added, removed = sorted(nt - ot), sorted(ot - nt)
    # CIK change OR matched<->unmatched transition (gained/lost a cik) on retained
    cik_changed = sorted(t for t in (nt & ot) if oc.get(t) != nc.get(t))
    ot_, nt_ = titleof(old), titleof(new)
    title_changed = sorted(t for t in (nt & ot)
                           if t in oc and t in nc and oc[t] == nc[t] and ot_.get(t) != nt_.get(t))
    return {"added": added, "removed": removed,
            "cik_changed": cik_changed, "title_changed": title_changed}


def main():
    argv = sys.argv[1:]
    check = "--check" in argv
    sec_file = None
    if "--sec-file" in argv:
        sec_file = argv[argv.index("--sec-file") + 1]

    with open(REGISTRY_PATH) as f:
        registry = json.load(f)
    try:
        sec = load_sec(sec_file)
    except SECUnavailable as e:
        # Fail open: a transient SEC outage must not read as drift.
        print("cik_map: SEC unreachable ({}) - cannot verify/build.".format(e))
        return 0 if check else 1
    index = build_index(registry, sec)

    if check:
        try:
            old = json.load(open(OUT_PATH))
        except Exception:
            old = {"matched": [], "unmatched": []}
        d = _diff(old, index)
        drift = bool(d["added"] or d["removed"] or d["cik_changed"])
        print("cik_map --check:  committed matched/unmatched=%d/%d -> rebuilt=%d/%d (SEC entries=%d)" % (
            len(old.get("matched", [])), len(old.get("unmatched", [])),
            len(index["matched"]), len(index["unmatched"]), len(sec)))
        print("  added   (%d): %s" % (len(d["added"]), d["added"]))
        print("  removed (%d): %s" % (len(d["removed"]), d["removed"]))
        print("  cik changed / matched<->unmatched (%d): %s" % (len(d["cik_changed"]), d["cik_changed"]))
        print("  sec_title changed only (info, not drift) (%d): %s" % (len(d["title_changed"]), d["title_changed"]))
        print("RESULT:", "WOULD CHANGE (exit 1)" if drift else "up to date (exit 0)")
        return 1 if drift else 0

    with open(OUT_PATH, "w") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("Wrote %s (%d matched, %d unmatched; SEC entries=%d)" % (
        os.path.relpath(OUT_PATH, ROOT), len(index["matched"]), len(index["unmatched"]), len(sec)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
