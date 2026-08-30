#!/usr/bin/env python3
"""
Entity-lifecycle check — surveillance for entity transitions the pipeline doesn't watch.
========================================================================================
Four incidents in one month shared a cause: nothing verified that the steps which should
follow an entity change actually happened. This closes the unwatched transitions:

  E2  route optimality  — a name on a Yahoo override that MarketStack v2 now serves fresh
                          (GlobalFoundries: admitted, never probed, fell to an override v2
                          carried). WARN, hygiene / migration backlog.
  E3  resolution regression — a resolver change flips an active-public name fresh -> stale
                          / unresolved, or overwrites a good symbol (Melexis: caught by
                          luck). Runs POST-hoc (default) OR PRE-commit (--validate), so a
                          proposed map can be vetted before it is applied.
  E4  frozen series + exit — a constituent that stopped trading (SkyWater: delisted, frozen
                          two and a half weeks, then a FATAL). Lone freeze = candidate;
                          corroboration promotes it to an auto-quarantine escalation.
  E10 graduation         — a company listed in our own funding data but never admitted to
                          the public universe (the ten IPOs).

NOT re-implemented here (already guarded — do not rebuild): E1 route-existence (the
completeness gate in fetch_prices_marketstack), E5 weights / E6 market_caps / E7 history
(reverse-parity guard in calculate_index), E8 search_index / E9 cik_map (the two
`--check` drift guards).

Severity: WARN. Actionable findings (E3 regressions, E4 escalations, E10 gaps) set exit 1
so the workflow goes RED and the warning is seen; E4 escalations are also written to
data/quarantine/auto_quarantine_candidates.json, which the weekly quarantine report reads.
The E2 migration backlog is reported but, being standing debt, does not by itself red the
daily run unless --strict.

Modes:
  (default)         daily sweep: E2, E4 (+exit), E10.
  --validate [MAP]  E3 only: compare a proposed map (default: the working-tree
                    marketstack_symbols.json) against the COMMITTED map (git HEAD) and
                    exit 1 on any regression. For use right after resolve_marketstack_symbols
                    and BEFORE committing.
  --strict          E2 findings also count toward the red exit.
  --json            machine-readable output.
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone, date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

REGISTRY = os.path.join(ROOT, "data", "registries", "entity_registry.json")
MAP_PATH = os.path.join(ROOT, "data", "registries", "marketstack_symbols.json")
OVERRIDES = os.path.join(ROOT, "data", "registries", "data_source_overrides.json")
ROUNDS = os.path.join(ROOT, "data", "funding", "rounds.json")
HISTORY_DIR = os.path.join(ROOT, "data", "prices", "history")
AUTO_CANDIDATES = os.path.join(ROOT, "data", "quarantine", "auto_quarantine_candidates.json")
ACK_PATH = os.path.join(ROOT, "data", "quarantine", "lifecycle_acknowledged.json")

FROZEN_TOLERANCE_TDAYS = 10   # trading days a series may legitimately go without a new bar
                              # (thin frontier names skip days; >10 is a real freeze). A lone
                              # freeze is a candidate; corroboration (below) promotes it.

# Override `reason` keywords meaning the override exists for a COVERAGE gap (removable once
# v2 carries the name) vs a correctness reason (KEEP even when v2 is "fresh": wrong
# instrument, currency cap, corrupt series, ticker reuse — v2 returning a bar is not proof
# the bar is right). Correctness reasons take precedence.
KEEP_REASONS = ("wrong instrument", "sciclone", "jl mag", "double-convert", "bounces",
                "bad instrument", "ticker-reuse", "ticker reuse", "corrupt", "alternating",
                "cap", "₩", "plausibility", "legacy entity", "raw-jpy", "wrong-instrument",
                "predecessor")


# ── shared helpers ─────────────────────────────────────────────────────────
def load_json(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return default


def active_public(reg):
    """{public_ticker: entry} for lifecycle-public, non-excluded, non-quarantined names."""
    out = {}
    for k, v in reg.items():
        if not isinstance(v, dict):
            continue
        if v.get("lifecycle_status") == "public" and v.get("status") not in (
                "excluded", "data_quarantine") and v.get("type") == "public":
            pt = v.get("public_ticker") or k
            out[pt] = v
    return out


def hist_path(ticker):
    return os.path.join(HISTORY_DIR, ticker.replace(" ", "_") + ".json")


def hist_last_date(ticker):
    d = load_json(hist_path(ticker))
    if not d:
        return None
    series = d.get("series") or []
    if isinstance(series, dict):
        ks = list(series.keys())
        return max(ks)[:10] if ks else None
    if isinstance(series, list) and series:
        return max(str(p.get("date"))[:10] for p in series if p.get("date"))
    return None


def _d(s):
    y, m, dd = map(int, str(s)[:10].split("-"))
    return date(y, m, dd)


def business_days_between(d0, d1):
    """Weekday count in (d0, d1] — a trading-day proxy (ignores holidays, so it slightly
    over-counts, which only makes a freeze WARN marginally more sensitive)."""
    from datetime import timedelta
    n, cur = 0, _d(d0)
    end = _d(d1)
    while cur < end:
        cur += timedelta(days=1)
        if cur.weekday() < 5:
            n += 1
    return n


# ── E2: route optimality ───────────────────────────────────────────────────
def check_route_optimality(ap):
    """Yahoo-override names that MS v2 now serves fresh. Classified: a coverage-gap
    override that v2 now carries is REMOVABLE (migration candidate); a correctness
    override (wrong instrument / currency / reuse) is KEPT even if v2 is fresh."""
    from resolve_marketstack_symbols import candidates_for, v2_latest, FRESH_DAYS
    import time
    ov = load_json(OVERRIDES, {})
    overrides = {k: v for k, v in ov.items()
                 if not k.startswith("_") and isinstance(v, dict) and v.get("provider") == "yahoo"}
    findings, kept = [], []
    for tk, meta in sorted(overrides.items()):
        if tk not in ap:                       # only active-public names
            continue
        country = ap[tk].get("country", "")
        cands = candidates_for(tk, country, None)
        v2_fresh = None
        for c in cands:
            dt, close, err = v2_latest(c)
            time.sleep(0.2)
            if dt:
                from datetime import datetime as _dtm
                age = (datetime.now(timezone.utc).date() - _d(dt)).days
                if age <= FRESH_DAYS:
                    v2_fresh = (c, dt)
                break
        if not v2_fresh:
            continue                            # v2 still absent/stale -> override justified
        reason = (meta.get("reason") or "").lower()
        if any(k in reason for k in KEEP_REASONS):
            kept.append((tk, v2_fresh[0], "correctness override (v2 bar not trustworthy)"))
        else:
            findings.append((tk, v2_fresh[0], v2_fresh[1]))
    return findings, kept


# ── E3: resolution regression (post-hoc OR pre-commit --validate) ───────────
def _committed_map():
    try:
        raw = subprocess.check_output(
            ["git", "show", "HEAD:data/registries/marketstack_symbols.json"],
            cwd=ROOT, stderr=subprocess.DEVNULL).decode()
        return (json.loads(raw).get("symbols") or {})
    except Exception:
        return {}


def check_regression(ap, proposed_path=None):
    """Compare a PROPOSED map (proposed_path, default working-tree) against the COMMITTED
    map (git HEAD). Flag active-public names that regressed fresh -> stale/unresolved, were
    dropped, or had a fresh symbol overwritten. In --validate this runs BEFORE a commit."""
    committed = _committed_map()
    proposed = (load_json(proposed_path or MAP_PATH, {}) or {}).get("symbols", {})
    regressions = []
    for tk in sorted(ap):
        c = committed.get(tk)
        p = proposed.get(tk)
        if not c or c.get("status") != "fresh":
            continue                            # only names that WERE fresh can regress
        if p is None:
            regressions.append((tk, "dropped", c.get("symbol"), None))
        elif p.get("status") != "fresh":
            regressions.append((tk, "fresh->" + str(p.get("status")), c.get("symbol"), p.get("symbol")))
        elif p.get("symbol") != c.get("symbol"):
            regressions.append((tk, "symbol-overwrite", c.get("symbol"), p.get("symbol")))
    return regressions


# ── E4: frozen series + exit signals, with corroboration ────────────────────
def check_frozen(ap):
    """Per active-public name: trading days since its last bar. > tolerance = candidate;
    corroboration (both vendors frozen, or the map flipped fresh->stale) escalates it to an
    auto-quarantine, the delisting signal. Returns (candidates, escalations)."""
    from resolve_marketstack_symbols import candidates_for, v2_latest
    from fetch_yahoo import fetch_yahoo_daily, YahooFetchError
    import time
    mp = (load_json(MAP_PATH, {}) or {}).get("symbols", {})
    last = {tk: hist_last_date(tk) for tk in ap}
    latest_session = max((v for v in last.values() if v), default=None)
    candidates, escalations = [], []
    if not latest_session:
        return candidates, escalations
    for tk, ld in sorted(last.items()):
        if not ld:
            continue                            # no history -> reverse-parity's job, not ours
        frozen_td = business_days_between(ld, latest_session)
        if frozen_td <= FROZEN_TOLERANCE_TDAYS:
            continue
        # corroboration
        map_flip = mp.get(tk, {}).get("status") == "stale"    # fresh->stale vendor flag
        both_frozen = None
        country = ap[tk].get("country", "")
        v2_last = ylast = None
        for c in candidates_for(tk, country, None):
            dt, _c, _e = v2_latest(c); time.sleep(0.2)
            if dt:
                v2_last = dt; break
        ysym = (mp.get(tk, {}) or {}).get("symbol") or None
        # best-effort Yahoo probe via the override symbol if present, else the code
        yq = None
        try:
            ov = load_json(OVERRIDES, {})
            yq = (ov.get(tk) or {}).get("yahoo_symbol")
        except Exception:
            pass
        if yq:
            try:
                yd = fetch_yahoo_daily(yq, output_size="compact"); time.sleep(0.2)
                ylast = max(yd["series"].keys()) if yd.get("series") else None
            except Exception:
                ylast = None
        both_frozen = bool((v2_last and _d(v2_last) <= _d(ld)) and (ylast and _d(ylast) <= _d(ld)))
        rec = {"ticker": tk, "last_bar": ld, "frozen_tdays": frozen_td,
               "v2_last": v2_last, "yahoo_last": ylast, "map_flip": map_flip,
               "both_frozen": both_frozen}
        if map_flip or both_frozen:
            escalations.append(rec)
        else:
            candidates.append(rec)
    return candidates, escalations


# ── E10: graduation (funding IPO -> public universe) ────────────────────────
def _norm(s):
    return "".join(ch for ch in str(s).lower() if ch.isalnum())


def _zero_strip(t):
    """'02533 HK' -> '2533 HK' (drop a leading-zero pad on a numeric code); non-numeric
    codes are left alone. Funding entity_ids pad HK codes; the registry key does not."""
    parts = str(t).split()
    if parts and parts[0].isdigit():
        parts[0] = str(int(parts[0]))
    return " ".join(parts)


def check_graduation(reg):
    """A COMPLETED listing (funding round == 'IPO', not 'IPO (filed)' / 'Pre-IPO') whose
    company is NOT an active-public registry entity — a listed company never admitted (the
    ten IPOs). Resolves the funding row to the registry across every identifier (id,
    entity_id, public_ticker, name, aliases, leading-zero-normalised code, related_tickers,
    and an alias substring) so an admitted name keyed by ticker is not falsely flagged;
    a row resolving to a public / pre_ipo / excluded entity is not a gap."""
    ident = {}          # normalised identifier -> (key, lifecycle, status)
    aliases = []        # (normalised alias >=6 chars, key, lifecycle, status) for fuzzy
    for k, v in reg.items():
        if not isinstance(v, dict):
            continue
        life, st = v.get("lifecycle_status"), v.get("status")
        for x in [k, v.get("public_ticker"), v.get("entity_id"), v.get("name")] + (v.get("aliases") or []):
            if not x:
                continue
            for form in (x, _zero_strip(x)):
                ident[_norm(form)] = (k, life, st)
            if len(_norm(x)) >= 6:
                aliases.append((_norm(x), k, life, st))
    rounds = load_json(ROUNDS, {})
    rows = rounds if isinstance(rounds, list) else (rounds.get("rounds") or rounds.get("data") or [])
    gaps, seen = [], set()
    for r in rows:
        if str(r.get("round", "")).strip().lower() != "ipo":      # COMPLETED listing only
            continue
        company, eid = r.get("company"), r.get("entity_id")
        key = eid or company
        if key in seen:
            continue
        # resolve across strong identifiers, then a bounded alias-substring fallback
        res = None
        for ck in [_norm(eid), _norm(_zero_strip(eid)), _norm(company)] + \
                  [_norm(t) for t in (r.get("related_tickers") or [])]:
            if ck and ck in ident:
                res = ident[ck]
                break
        if res is None:
            nc = _norm(company)
            for na, k, life, st in aliases:
                if na and (na in nc or nc in na):
                    res = (k, life, st)
                    break
        if res is not None:
            k, life, st = res
            if life == "public" or (life and str(life).startswith("pre_ipo")) \
                    or st in ("excluded", "data_quarantine"):
                continue                       # admitted / tracked-pre-IPO / deliberately out
            seen.add(key)
            gaps.append({"company": company, "entity_id": eid, "resolved_to": k,
                         "lifecycle": life or "private", "date": r.get("date"),
                         "note": "private in registry but funding shows a completed IPO"})
        else:
            seen.add(key)
            gaps.append({"company": company, "entity_id": eid, "resolved_to": None,
                         "lifecycle": "ABSENT", "date": r.get("date"),
                         "note": "listed in funding, absent from registry"})
    return gaps


# ── candidate feed (weekly report reads this file) ──────────────────────────
def feed_candidates(escalations):
    if not escalations:
        return
    cand = load_json(AUTO_CANDIDATES, {}) or {}
    now = datetime.now(timezone.utc).isoformat() + "Z"
    for e in escalations:
        sig = "both-vendors-frozen" if e["both_frozen"] else "map-fresh->stale"
        cand[e["ticker"]] = {
            "source": "entity_lifecycle_check",
            "reason": "frozen {} trading days; corroborated ({}) -> suspected delisting".format(
                e["frozen_tdays"], sig),
            "signal": sig, "last_bar": e["last_bar"], "flagged_date": now,
        }
    os.makedirs(os.path.dirname(AUTO_CANDIDATES), exist_ok=True)
    with open(AUTO_CANDIDATES, "w") as f:
        json.dump(cand, f, indent=2)


# ── main ────────────────────────────────────────────────────────────────────
def main():
    args = sys.argv[1:]
    as_json = "--json" in args
    strict = "--strict" in args
    reg = load_json(REGISTRY, {})
    ap = active_public(reg)

    # E3 --validate: pre-commit gate, exits on regression, runs nothing else.
    if "--validate" in args:
        i = args.index("--validate")
        proposed = args[i + 1] if i + 1 < len(args) and not args[i + 1].startswith("-") else None
        regs = check_regression(ap, proposed)
        src = proposed or "working-tree marketstack_symbols.json"
        if as_json:
            print(json.dumps({"mode": "validate", "source": src, "regressions": regs}, indent=2))
        else:
            print("E3 VALIDATE — proposed: {}  vs committed HEAD".format(src))
            if regs:
                for tk, kind, old, new in regs:
                    print("  [REGRESSION] {:14} {:18} {} -> {}".format(tk, kind, old, new))
            else:
                print("  no regressions (every fresh active-public name stays fresh).")
        return 1 if regs else 0

    e2, e2_kept = check_route_optimality(ap)
    e4_cand, e4_esc = check_frozen(ap)
    e10 = check_graduation(reg)
    feed_candidates(e4_esc)

    # Acknowledgment baseline (data/quarantine/lifecycle_acknowledged.json = {"E2": [...],
    # "E4": [...], "E10": [...]}): a listed finding is still reported but does not red the
    # run, so a red workflow always means an UNADDRESSED finding. Absent the file, nothing
    # is acknowledged and every finding reds — the E2 migration backlog can be baselined
    # here instead of reddening the daily run forever (a warning nobody reads is worthless).
    ack = load_json(ACK_PATH, {}) or {}
    def _new(inv, items, keyfn):
        acked = set(ack.get(inv) or [])
        return [x for x in items if keyfn(x) not in acked]
    e2_new = _new("E2", e2, lambda f: f[0])
    e4_new = _new("E4", e4_esc, lambda e: e["ticker"])
    e10_new = _new("E10", e10, lambda g: g.get("entity_id") or g.get("company"))
    actionable = bool(e2_new or e4_new or e10_new)

    if as_json:
        print(json.dumps({
            "active_public": len(ap),
            "E2_route_optimality": [{"ticker": t, "v2_symbol": s, "v2_last": d} for t, s, d in e2],
            "E2_kept_false_positive": [{"ticker": t, "v2_symbol": s, "why": w} for t, s, w in e2_kept],
            "E4_frozen_candidates": e4_cand,
            "E4_escalations": e4_esc,
            "E10_graduation_gaps": e10,
            "actionable": actionable,
        }, indent=2))
        return 1 if actionable else 0

    print("=" * 78)
    print("ENTITY-LIFECYCLE CHECK  —  {}  ({} active-public names)".format(
        datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), len(ap)))
    print("=" * 78)
    print("\nE2 route optimality (Yahoo override that v2 now serves fresh — migration backlog):")
    if e2:
        for tk, sym, d in e2:
            print("   [WARN] {:14} v2 {:14} fresh {} — migration candidate (verify history seam before removing)".format(tk, sym, d))
    else:
        print("   none.")
    if e2_kept:
        print("   (kept, v2 fresh but override retained for correctness:")
        for tk, sym, why in e2_kept:
            print("      {:14} {} — {}".format(tk, sym, why))
        print("   )")
    print("\nE4 frozen series / exit signals (tolerance {} trading days):".format(FROZEN_TOLERANCE_TDAYS))
    if e4_esc:
        for e in e4_esc:
            sig = "both vendors frozen" if e["both_frozen"] else "map fresh->stale"
            print("   [ESCALATE] {:14} frozen {}td since {} — {} — AUTO-QUARANTINE CANDIDATE".format(
                e["ticker"], e["frozen_tdays"], e["last_bar"], sig))
    if e4_cand:
        for e in e4_cand:
            print("   [watch]    {:14} frozen {}td since {} — no corroboration yet".format(
                e["ticker"], e["frozen_tdays"], e["last_bar"]))
    if not (e4_esc or e4_cand):
        print("   none.")
    print("\nE10 graduation (funding IPO not admitted to the public universe):")
    if e10:
        for g in e10:
            print("   [WARN] {:26} lifecycle={:8} — {} ({})".format(
                str(g["company"])[:26], g["lifecycle"], g["note"], g["date"]))
    else:
        print("   none — every IPO'd name in funding is admitted.")
    n_ack = (len(e2) - len(e2_new)) + (len(e4_esc) - len(e4_new)) + (len(e10) - len(e10_new))
    print("\n" + "-" * 78)
    print("RESULT: {} unaddressed finding(s) — E2={} E4={} E10={}{} (exit {})".format(
        len(e2_new) + len(e4_new) + len(e10_new), len(e2_new), len(e4_new), len(e10_new),
        "  [{} acknowledged]".format(n_ack) if n_ack else "", 1 if actionable else 0))
    return 1 if actionable else 0


if __name__ == "__main__":
    sys.exit(main())
