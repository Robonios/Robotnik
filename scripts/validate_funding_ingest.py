#!/usr/bin/env python3
"""Ingest validation guard for data/funding/rounds.json.

A standing, FLAG-ONLY check that turns the one-off fabrication audit into a
repeatable gate. It never edits a row; it reports. Four core rules, plus two
advisory checks that fall out of the same pass:

  R1  bare-domain      citation is a domain root with no article path
  R2  truncated-path   citation on a known newswire whose canonical shape is
                       broken (date-only stub / truncated slug / wrong id)
  R3  duplicate        a second row with the same company, round and amount
  R4  date-vs-source   the cited article's date diverges from the row's date
                       beyond tolerance  (4a offline from date-in-URL newswires;
                       4b online by fetching + parsing the article date)

  A5  weak-citation    (advisory) sole citation is a non-article aggregator /
                       company-profile page (CB Insights, Crunchbase org,
                       PitchBook, Tracxn, DePIN Hub project, ...)
  A6  null-amount      (advisory) an index-eligible round carries no amount

Severity:
  FAIL          hard defect, CI-blocking            (R1, R2, R3, R4-reliable)
  WARN          advisory, non-blocking              (A5, A6, R4-soft)
  UNVERIFIABLE  fetch blocked / no date parseable    never fails the build

Design notes
------------
* Fetch-blocked domains (SpaceNews 429, BusinessWire / PRNewswire timeouts,
  ~300 rows in the audit) are UNVERIFIABLE, never FAIL. A guard that fails the
  build on a bot-block gets switched off.
* R4a needs no network: BusinessWire and GlobeNewswire encode the release date
  in the URL, so their date-check is free, deterministic and unblockable.
* R4b (network) is opt-in (--online); default runs everything offline so the
  structural tier is safe for CI.

stdlib only (project convention). Reads rounds.json and rpci_scope.json.
"""
import argparse
import datetime
import json
import os
import re
import sys
import time
from collections import defaultdict
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROUNDS = os.path.join(ROOT, "data/funding/rounds.json")
SCOPE = os.path.join(ROOT, "data/index/rpci_scope.json")

# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

def load_rows(path=None):
    d = json.load(open(path or ROUNDS))
    return d["rounds"] if isinstance(d, dict) else d


def load_scope():
    """Index-eligibility, so we can label each flag INCLUDED vs excluded."""
    try:
        s = json.load(open(SCOPE))
    except FileNotFoundError:
        return None
    excluded = set(s.get("excluded_rounds", []))
    mna_incl = {(m["company"], m["date"]) for m in s.get("mna_included", [])}
    return excluded, mna_incl


def eligible(row, scope):
    if scope is None:
        return None
    excluded, mna_incl = scope
    rd = (row.get("round") or "").strip()
    if rd in excluded:
        return False
    if rd == "M&A":
        return (row.get("company"), row.get("date")) in mna_incl
    return True


def parse_date(s):
    try:
        y, m, d = str(s).split("-")
        return datetime.date(int(y), int(m), int(d))
    except Exception:
        return None


def norm_company(c):
    c = (c or "").strip().lower()
    c = re.sub(r"\s*\(.*?\)\s*", " ", c)      # drop parentheticals
    c = re.sub(r"\s+", " ", c).strip()
    return c


def netloc(url):
    return urlparse(url).netloc.lower().replace("www.", "")


# --------------------------------------------------------------------------- #
# R1  bare-domain
# --------------------------------------------------------------------------- #

def check_bare_domain(url):
    """True when the citation has no article path (domain root)."""
    p = urlparse(url)
    segs = [s for s in p.path.split("/") if s]
    return len(segs) == 0 and not p.query


# --------------------------------------------------------------------------- #
# R2  truncated-path on known newswires (canonical-shape validation)
# --------------------------------------------------------------------------- #

# A newswire link is truncated iff its stable RELEASE ID is absent. The ID is
# what resolves the page; the human slug is decorative and locale prefixes
# (/il/, /en/, /in/ ...) are legal, so we test for ID-presence, not full shape.
# Anti-FP note: an over-strict full-canonical match flags valid slug-less and
# locale-prefixed URLs (11 false positives on the current tree); ID-presence
# flags only the genuine date-only stubs and slug-only truncations the audit hit.
NEWSWIRE_ID = {
    "prnewswire.com": re.compile(r"-\d{7,}\.html"),           # ...-302440649.html
    "businesswire.com": re.compile(r"/news/home/\d{14}"),      # /news/home/20250430735778
    "globenewswire.com": re.compile(r"/news-release/\d{4}/\d{2}/\d{2}/\d+"),
}


def check_truncated_newswire(url):
    """Return a reason string if the newswire link lacks its release ID, else None."""
    dom = netloc(url)
    path = urlparse(url).path
    for base, has_id in NEWSWIRE_ID.items():
        if dom == base or dom.endswith("." + base):
            if not has_id.search(path):
                return (f"{base} link missing release id "
                        f"(date-only stub / truncated slug): {path!r}")
            return None
    return None


# --------------------------------------------------------------------------- #
# R4a  date encoded in the newswire URL  (offline, unblockable)
# --------------------------------------------------------------------------- #

def date_from_url(url):
    """Extract the release date encoded in the URL, or None."""
    dom = netloc(url)
    path = urlparse(url).path
    if dom.endswith("businesswire.com"):
        m = re.search(r"/news/home/(\d{4})(\d{2})(\d{2})\d{6}/", path)
        if m:
            return _mkdate(*m.groups())
    if dom.endswith("globenewswire.com"):
        m = re.search(r"/news-release/(\d{4})/(\d{2})/(\d{2})/", path)
        if m:
            return _mkdate(*m.groups())
    return None


def _mkdate(y, m, d):
    try:
        return datetime.date(int(y), int(m), int(d))
    except ValueError:
        return None


# --------------------------------------------------------------------------- #
# R4b  date parsed from the fetched article  (online, may be blocked)
# --------------------------------------------------------------------------- #

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

DATE_META_PATTERNS = [
    re.compile(r'"datePublished"\s*:\s*"(\d{4}-\d{2}-\d{2})'),
    re.compile(r'property=["\']article:published_time["\']\s+content=["\'](\d{4}-\d{2}-\d{2})'),
    re.compile(r'content=["\'](\d{4}-\d{2}-\d{2})[^"\']*["\']\s+property=["\']article:published_time'),
    re.compile(r'name=["\']date["\']\s+content=["\'](\d{4}-\d{2}-\d{2})'),
    re.compile(r'<time[^>]+datetime=["\'](\d{4}-\d{2}-\d{2})'),
    re.compile(r'"dateCreated"\s*:\s*"(\d{4}-\d{2}-\d{2})'),
]


def fetch_article_date(url, timeout=20):
    """Return (date, status). status in {ok, dead, blocked, nodate, error}."""
    req = Request(url, headers={"User-Agent": UA,
                                "Accept": "text/html,application/xhtml+xml"})
    try:
        with urlopen(req, timeout=timeout) as r:
            raw = r.read(400_000).decode("utf-8", "replace")
    except HTTPError as e:
        if e.code in (404, 410):
            return None, "dead"
        if e.code in (401, 403, 429) or 500 <= e.code < 600:
            return None, "blocked"
        return None, "error"
    except (URLError, TimeoutError, OSError):
        return None, "blocked"
    dates = []
    for pat in DATE_META_PATTERNS:
        for m in pat.finditer(raw):
            d = parse_date(m.group(1))
            if d:
                dates.append(d)
    if not dates:
        return None, "nodate"
    return min(dates), "ok"      # earliest plausible => the announcement


# --------------------------------------------------------------------------- #
# A5  weak citation: non-article aggregator / profile page
# --------------------------------------------------------------------------- #

AGGREGATOR_PROFILE = [
    ("cbinsights.com", "/company/"),
    ("crunchbase.com", "/organization/"),
    ("pitchbook.com", "/profiles/"),
    ("tracxn.com", "/companies/"),
    ("depinhub.io", "/projects/"),
    ("dealroom.co", "/companies/"),
    ("owler.com", "/company/"),
]


def check_weak_citation(url):
    dom = netloc(url)
    path = urlparse(url).path.lower()
    for base, marker in AGGREGATOR_PROFILE:
        if (dom == base or dom.endswith("." + base)) and marker in path:
            return f"non-article profile page on {base} (no dated round evidence)"
    return None


# --------------------------------------------------------------------------- #
# run
# --------------------------------------------------------------------------- #

def run(online=False, tol_url=14, tol_fetch=30, tol_embargo=30, limit_online=None,
        only_companies=None, advisory=False, path=None):
    # tol_url : R4a, date encoded in newswire URL (reliable) -> FAIL. Calibrated
    #           to +/-14d: catches 11/11 labelled index-movers at ~1% false pos.
    # tol_embargo: R4a embargo asymmetry. Newswire IDs are stamped at UPLOAD, so
    #           an embargoed release carries an ID EARLIER than its publication /
    #           announcement (the row date). A URL-ID up to tol_embargo days
    #           EARLIER than the row is therefore embargo-plausible -> WARN, not
    #           FAIL. A URL-ID LATER than the row (cannot embargo into the future)
    #           or EARLIER beyond the window stays a FAIL. Trade-off: a window
    #           wide enough to pass a long embargo (Manna, 22d) also downgrades a
    #           same-direction "recorded-too-late" error of smaller gap (Archetype,
    #           15d) from FAIL to WARN -- both are url-earlier and 15 < 22, so no
    #           window separates them. WARN still surfaces it. See calibration.
    # tol_fetch: R4b, publish date parsed from a fetched page (lags variably,
    #           noisier) -> WARN at +/-30d.
    # path    : validate a candidate file (e.g. a pre-merge monthly-sweep shard)
    #           instead of the committed rounds.json. Eligibility (scope) always
    #           comes from the repo's rpci_scope.json.
    rows = load_rows(path)
    scope = load_scope()
    findings = []      # dicts: rule, severity, company, date, round, amount, source, detail

    def add(rule, sev, r, detail):
        findings.append({
            "rule": rule, "severity": sev,
            "company": r.get("company"), "date": r.get("date"),
            "round": (r.get("round") or "").strip(), "amount_m": r.get("amount_m"),
            "included": eligible(r, scope), "source": r.get("source"),
            "detail": detail,
        })

    # ---- R1, R2, A5, A6 : per-row structural (offline) --------------------- #
    for r in rows:
        url = (r.get("source") or "").strip()
        if not url:
            add("R1-bare", "FAIL", r, "empty source")
            continue
        if not url.lower().startswith("http"):
            add("R1-bare", "FAIL", r, f"non-URL source: {url!r}")
            continue
        if check_bare_domain(url):
            add("R1-bare", "FAIL", r, f"domain-root citation, no article path: {url}")
        t = check_truncated_newswire(url)
        if t:
            add("R2-truncated", "FAIL", r, t)
        if advisory:
            w = check_weak_citation(url)
            if w:
                add("A5-weak", "WARN", r, w)
            if r.get("amount_m") in (None, "", 0) and eligible(r, scope):
                add("A6-nullamount", "WARN", r,
                    "index-eligible round with no amount (cannot contribute capital)")

    # ---- R3 : duplicate (company, round, amount) -------------------------- #
    buckets = defaultdict(list)
    for r in rows:
        if r.get("amount_m") in (None, ""):
            continue
        k = (norm_company(r.get("company")), (r.get("round") or "").strip().lower(),
             r.get("amount_m"))
        buckets[k].append(r)
    for k, grp in buckets.items():
        if len(grp) < 2:
            continue
        ds = sorted(filter(None, (parse_date(x["date"]) for x in grp)))
        span = (ds[-1] - ds[0]).days if len(ds) >= 2 else None
        same_src = len({(x.get("source") or "").strip() for x in grp}) == 1
        for r in grp:
            detail = (f"{len(grp)}x same company/round/amount; dates="
                      f"{[x['date'] for x in grp]}; span={span}d; "
                      f"same_source={same_src}")
            add("R3-duplicate", "FAIL", r, detail)

    # ---- R4a : date-in-URL newswires (offline, embargo-asymmetric) -------- #
    for r in rows:
        url = (r.get("source") or "").strip()
        u = date_from_url(url)
        rd = parse_date(r.get("date"))
        if u and rd:
            signed = (u - rd).days          # <0 => URL-ID earlier than row
            delta = abs(signed)
            if delta <= tol_url:
                pass                        # within reliable tolerance
            elif signed < 0 and delta <= tol_embargo:
                add("R4a-date-url", "WARN", r,
                    f"row date {rd} vs URL-encoded release date {u} = {delta}d EARLIER "
                    f"(embargo-plausible, within {tol_embargo}d; ID stamped pre-publication) "
                    f"-- verify the announcement date")
            else:
                where = "LATER than row" if signed > 0 else f"EARLIER, beyond {tol_embargo}d embargo window"
                add("R4a-date-url", "FAIL", r,
                    f"row date {rd} vs URL-encoded release date {u} = {delta}d {where} "
                    f"(> {tol_url}d tolerance)")

    # ---- R4b : online fetch (opt-in) -------------------------------------- #
    if online:
        targets = rows
        if only_companies:
            names = {c.lower() for c in only_companies}
            targets = [r for r in rows
                       if any(n in (r.get("company") or "").lower() for n in names)]
        # skip rows already checkable offline via R4a
        targets = [r for r in targets if not date_from_url((r.get("source") or ""))]
        if limit_online:
            targets = targets[:limit_online]
        stats = defaultdict(int)
        for r in targets:
            url = (r.get("source") or "").strip()
            if not url.lower().startswith("http"):
                continue
            d, status = fetch_article_date(url)
            stats[status] += 1
            rd = parse_date(r.get("date"))
            if status == "dead":
                add("R4b-deadlink", "FAIL", r, f"citation 404/gone: {url}")
            elif status == "ok" and rd:
                delta = abs((d - rd).days)
                if delta > tol_fetch:
                    add("R4b-date-fetch", "WARN", r,
                        f"row date {rd} vs article date {d} = {delta}d "
                        f"(> {tol_fetch}d; publish-date, soft signal)")
            elif status in ("blocked", "nodate", "error"):
                add("R4b-unverifiable", "UNVERIFIABLE", r,
                    f"{status}: could not read article date from {netloc(url)}")
            time.sleep(0.4)
        print(f"[R4b online] fetched {sum(stats.values())} rows: "
              f"{dict(stats)}", file=sys.stderr)

    return findings


def report(findings, as_json=False):
    if as_json:
        print(json.dumps(findings, indent=1, ensure_ascii=False))
        return
    order = {"FAIL": 0, "WARN": 1, "UNVERIFIABLE": 2}
    by_sev = defaultdict(list)
    for f in findings:
        by_sev[f["severity"]].append(f)
    print(f"\n{'='*72}\nFUNDING INGEST GUARD — {len(findings)} findings\n{'='*72}")
    for sev in sorted(by_sev, key=lambda s: order.get(s, 9)):
        fs = by_sev[sev]
        print(f"\n### {sev}: {len(fs)}")
        for f in sorted(fs, key=lambda x: (x["rule"], not x["included"])):
            inc = "INCL" if f["included"] else ("excl" if f["included"] is False else "?")
            print(f"  [{f['rule']:15}] [{inc}] {f['company']} | {f['date']} | "
                  f"{f['round']} | ${f['amount_m']}M")
            print(f"      {f['detail']}")
    nfail = len(by_sev.get("FAIL", []))
    print(f"\n{'='*72}\nFAIL={nfail}  WARN={len(by_sev.get('WARN',[]))}  "
          f"UNVERIFIABLE={len(by_sev.get('UNVERIFIABLE',[]))}\n{'='*72}")
    return nfail


def main():
    ap = argparse.ArgumentParser(description="Flag-only ingest guard for rounds.json")
    ap.add_argument("--online", action="store_true",
                    help="enable R4b network fetches (default: offline only)")
    ap.add_argument("--tol-url", type=int, default=14,
                    help="R4a FAIL tolerance, days, for date-in-URL newswires (default 14)")
    ap.add_argument("--tol-fetch", type=int, default=30,
                    help="R4b WARN tolerance, days, for fetched publish dates (default 30)")
    ap.add_argument("--tol-embargo", type=int, default=30,
                    help="R4a embargo window, days: URL-ID up to this many days EARLIER "
                         "than the row is WARN not FAIL (default 30)")
    ap.add_argument("--limit-online", type=int, default=None,
                    help="cap R4b fetches (for demos)")
    ap.add_argument("--only", nargs="*", default=None,
                    help="restrict R4b to companies matching these substrings")
    ap.add_argument("--advisory", action="store_true",
                    help="also run advisory checks A5 (weak citation) + A6 (null amount)")
    ap.add_argument("--path", default=None,
                    help="validate a candidate file instead of the committed rounds.json "
                         "(e.g. a pre-merge monthly-sweep shard)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    findings = run(online=args.online, tol_url=args.tol_url, tol_fetch=args.tol_fetch,
                   tol_embargo=args.tol_embargo, limit_online=args.limit_online,
                   only_companies=args.only, advisory=args.advisory, path=args.path)
    if args.json:
        report(findings, as_json=True)
        nfail = sum(1 for f in findings if f["severity"] == "FAIL")
    else:
        nfail = report(findings)
    sys.exit(1 if nfail else 0)


if __name__ == "__main__":
    main()
