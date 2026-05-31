#!/usr/bin/env python3
"""
INDEPENDENT INDEX RECONSTRUCTION  (verification gate, not the production path)
=============================================================================
A second, from-scratch implementation of the Robotnik Composite methodology,
written to AGREE-OR-DISAGREE with scripts/calculate_index.py. It deliberately
uses different internal machinery than production:

  production            this reconstruction
  ----------            -------------------
  date-keyed defaultdict price_matrix   ->  per-ticker {date: close} series
  incremental last_known carry-forward  ->  dense forward-filled arrays over
                                            the trading-day axis
  in-place sub-series mutation          ->  pure functions returning arrays

If two independent implementations of the same methodology agree to <0.01 on
every point of the composite and all four sub-indices, the production code is
corroborated. Any divergence is a bug in one of them and is reported loudly.

It re-derives EVERY transform from the methodology spec rather than importing
production helpers — the only shared inputs are the on-disk data files (the
USD/split-adjusted history, market caps, registry), which are the fetch-layer
artifacts both the production index and this check must consume.

Usage:  python scripts/verify_index_reconstruction.py
Exit 0 = reconstruction matches production within tolerance; non-zero = drift.
"""
import json, sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

ROOT = Path(__file__).resolve().parent.parent
IDX  = ROOT / "data" / "index"
HIST = ROOT / "data" / "prices" / "history"

# ── methodology constants (must equal production) ────────────────────────
MIN_MCAP        = 10_000_000
CAP             = 0.05
MAX_LOAD_USD    = 10_000
NORMALISE_DATE  = "2025-03-31"
BASE_VALUE      = 1000.0
TRADING_COVER   = 0.50          # trading-day filter (eligible coverage)
SUB_COVER       = 0.30          # base-date coverage threshold
LOOKBACK_DAYS   = 1825          # ~5y for the raw sub-index base
REORG_EVENTS    = {"WOLF": "2025-09-29"}   # bankruptcy/wipeout reorgs == production
COMPOSITE_SECTORS = ["semiconductor", "robotics", "space", "materials"]
SECTOR_MAP = {
    "Semiconductor":"Semiconductor","Semiconductors":"Semiconductor","Semis":"Semiconductor",
    "Cross-stack":"Semiconductor","Cross-Stack":"Semiconductor",
    "Robotics":"Robotics","Space":"Space",
    "Materials":"Materials","Materials & Inputs":"Materials",
    "Token":"Token","Tokens":"Token",
}

def load(p): return json.loads(Path(p).read_text())

def capped_weights(items):
    """5% cap with iterative proportional redistribution. items: {tk: mcap}."""
    tot = sum(items.values())
    if tot <= 0: return {t: 0.0 for t in items}
    w = {t: m / tot for t, m in items.items()}
    for _ in range(100):
        over = {t: x for t, x in w.items() if x > CAP + 1e-15}
        if not over: break
        excess = sum(x - CAP for x in over.values())
        under  = {t: x for t, x in w.items() if x <= CAP + 1e-15}
        ut = sum(under.values())
        if ut <= 0: break
        for t in over:  w[t] = CAP
        for t in under: w[t] += excess * (under[t] / ut)
    return w

def main():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    mc  = load(IDX / "market_caps.json")["market_caps"]
    ap  = load(ROOT / "data" / "prices" / "all_prices.json")["prices"]
    reg = load(ROOT / "data" / "registries" / "entity_registry.json")
    prod = load(IDX / "robotnik_index.json")
    prod_sub = load(IDX / "sub_indices.json")

    price_now = {p["ticker"]: p["price"] for p in ap if p.get("price") is not None}
    tokens = {k for k, v in reg.items()
              if isinstance(v, dict) and (v.get("type") == "token"
              or v.get("sector") in ("Token", "Tokens"))}
    registry_excluded = {k for k, v in reg.items()
                         if isinstance(v, dict)
                         and v.get("status") in ("excluded", "data_quarantine")}
    # Lifecycle mirror (Workstream C): resolve market_caps ticker -> entity_id via the
    # public_ticker field (identity for native-public); only lifecycle_status=="public"
    # is index-eligible. Mirrors calculate_index so the two implementations agree even
    # across private→public / delisted transitions.
    pubtkr2eid = {v.get("public_ticker"): k for k, v in reg.items()
                  if isinstance(v, dict) and v.get("public_ticker")}
    lifecycle = {k: v.get("lifecycle_status") for k, v in reg.items() if isinstance(v, dict)}
    _eid = lambda t: pubtkr2eid.get(t, t)

    # ── eligible universe (replicated filter — registry is source of truth) ──
    for e in mc:
        e["sector"] = SECTOR_MAP.get(e.get("sector", ""), e.get("sector", "Other"))
    elig = [e for e in mc
            if e["market_cap_usd"] >= MIN_MCAP
            and e["ticker"] in price_now
            and _eid(e["ticker"]) not in registry_excluded
            and e.get("status") not in ("excluded", "data_quarantine")
            and _eid(e["ticker"]) not in tokens
            and e["sector"] != "Token"
            and lifecycle.get(_eid(e["ticker"])) == "public"]
    elig_tk = {e["ticker"] for e in elig}
    N = len(elig)

    # ── per-ticker USD close series (independent representation) ──────────
    series = {}  # tk -> {date: close}
    for f in HIST.glob("*.json"):
        try: d = json.loads(f.read_text())
        except Exception: continue
        tk = d.get("ticker", f.stem)
        s = {}
        for pt in d.get("series", []):
            dt, c = pt.get("date"), pt.get("close")
            if dt and c is not None and c > 0 and c <= MAX_LOAD_USD:
                s[dt] = c
        if s: series[tk] = s

    all_dates = sorted({dt for s in series.values() for dt in s})

    # ── trading-day filter: >=50% eligible real-bar coverage ─────────────
    def cover(dt):
        m = 0
        for tk in elig_tk:
            if tk in series and dt in series[tk]: m += 1
        return m
    need = max(1, int(N * TRADING_COVER))
    trading = [dt for dt in all_dates if cover(dt) >= need]

    # ── dense forward-filled price ararray per ticker over trading axis ──
    ffill = {}  # tk -> list aligned to `trading`
    for tk, s in series.items():
        arr, last = [], None
        for dt in trading:
            if dt in s: last = s[dt]
            arr.append(last)         # None until first real bar, then carried
        ffill[tk] = arr
    didx = {dt: i for i, dt in enumerate(trading)}

    # ── raw sub-index base date: first trading day >= today-1825d with
    #    >=30% eligible coverage (production uses full-eligible coverage) ──
    target5 = (datetime.strptime(today, "%Y-%m-%d") - timedelta(days=LOOKBACK_DAYS)).strftime("%Y-%m-%d")
    sub_base = trading[0]
    for dt in trading:
        if dt >= target5 and cover(dt) >= N * SUB_COVER:   # float compare, == production
            sub_base = dt; break
    bi = didx[sub_base]

    # ── build one sub-index (independent backfill) ───────────────────────
    def sub_index(sector):
        ents = {e["ticker"]: e["market_cap_usd"] for e in elig if e["sector"] == sector}
        if not ents: return None
        w = capped_weights(ents)
        # Chain-linked daily-return (enter-at-first-price), matching production's
        # backfill_index_chained: idx[k] = idx[k-1] * weighted-avg daily ratio over
        # constituents live on BOTH k-1 and k; idx rounded each step to 2dp. ffill
        # is None until a constituent's first real bar, so a late IPO contributes
        # no return on its entry day (no dilution jump).
        raw = []
        idx = 1.0
        for k in range(len(trading)):
            if k == 0:
                raw.append(round(idx, 2)); continue
            num = den = 0.0
            for tk, wt in w.items():
                arr = ffill.get(tk)
                if not arr: continue
                pp, pc = arr[k - 1], arr[k]
                if pp is not None and pc is not None and pp > 0:
                    r = pc / pp
                    if REORG_EVENTS.get(tk) == trading[k]:   # wipeout reorg == production
                        r = 0.0
                    elif r > 5.0 or r < 0.2:                  # reverse-split/bad print -> flat
                        r = 1.0
                    num += wt * r; den += wt
            idx *= (num / den) if den > 0 else 1.0
            raw.append(round(idx, 2))
        # normalise to 1000 on NORMALISE_DATE (exact match; 2025-03-31 present)
        if NORMALISE_DATE in didx:
            base_v = raw[didx[NORMALISE_DATE]]
        else:
            j = next((k for k, dt in enumerate(trading) if dt >= NORMALISE_DATE), len(trading)-1)
            base_v = raw[j]
        factor = BASE_VALUE / base_v if base_v else 1.0
        # emit only from sub_base (chain warmed up over earlier dates) — == production
        return {dt: round(v * factor, 2)
                for dt, v in zip(trading, raw) if dt >= sub_base}, w

    subs = {}
    sub_w = {}
    for sec in ["Semiconductor", "Robotics", "Space", "Materials", "Token"]:
        r = sub_index(sec)
        if r: subs[sec.lower()] = r[0]; sub_w[sec.lower()] = r[1]

    # ── composite: mcap-share-weighted average of the 4 equity sub-indices
    shares = {}
    sector_of = {}
    for e in elig:
        cp = price_now.get(e["ticker"]); m = e.get("market_cap_usd") or 0
        if cp and cp > 0 and m > 0:
            shares[e["ticker"]] = m / cp
            sector_of[e["ticker"]] = e["sector"].lower()
    edates = trading[bi:]            # emit from sub_base (chain warmed up earlier) == production
    comp_raw = []
    for dt in edates:
        i = didx[dt]
        smcap = {k: 0.0 for k in COMPOSITE_SECTORS}
        for tk, sh in shares.items():
            sec = sector_of.get(tk)
            if sec in smcap:
                p = ffill.get(tk, [None]*len(trading))[i]
                if p is not None and p > 0: smcap[sec] += sh * p
        tot = sum(smcap.values())
        if tot <= 0: continue
        val = 0.0; contrib = 0
        for k in COMPOSITE_SECTORS:
            sv = subs.get(k, {}).get(dt)
            if sv is None: continue
            val += (smcap[k]/tot) * sv; contrib += 1
        if contrib: comp_raw.append((dt, round(val, 2)))   # production rounds composite raw (line 648)
    # renormalise composite to 1000 on NORMALISE_DATE (defensive, as production)
    cmap = dict(comp_raw)
    base_v = cmap.get(NORMALISE_DATE) or next((v for dt, v in comp_raw if dt >= NORMALISE_DATE), None)
    cf = BASE_VALUE / base_v if base_v else 1.0
    comp = [(dt, round(v * cf, 2)) for dt, v in comp_raw]

    # ── COMPARE to production ────────────────────────────────────────────
    def compare(name, recon_pairs, prod_series):
        pm = {p["date"]: p["value"] for p in prod_series}
        rm = dict(recon_pairs)
        common = sorted(set(pm) & set(rm))
        only_p = set(pm) - set(rm); only_r = set(rm) - set(pm)
        worst = (0.0, None)
        for dt in common:
            diff = abs(pm[dt] - rm[dt])
            if diff > worst[0]: worst = (diff, dt)
        last = sorted(common)[-1] if common else None
        print(f"  {name:14s} pts recon={len(rm)} prod={len(pm)} common={len(common)} "
              f"| max|Δ|={worst[0]:.4f} @ {worst[1]} "
              f"| last {last}: recon={rm.get(last)} prod={pm.get(last)}")
        if only_p or only_r:
            print(f"       date-set mismatch: only_prod={len(only_p)} only_recon={len(only_r)} "
                  f"{sorted(only_p)[:3]}{sorted(only_r)[:3]}")
        return worst[0], len(only_p) + len(only_r)

    print("="*72)
    print("INDEPENDENT RECONSTRUCTION vs PRODUCTION  (tol: |Δ|<0.01, same date set)")
    print(f"  eligible={N}  trading_days={len(trading)}  sub_base={sub_base}  norm={NORMALISE_DATE}")
    print("="*72)
    worst_all = 0.0; setmiss = 0
    w, m = compare("composite", comp, prod["series"]); worst_all=max(worst_all,w); setmiss+=m
    for k in COMPOSITE_SECTORS + ["token"]:
        if k in subs and k in prod_sub:
            w, m = compare(k, sorted(subs[k].items()), prod_sub[k]["series"])
            worst_all=max(worst_all,w); setmiss+=m
    print("-"*72)
    rc = round(comp[-1][1], 2); pc = prod["current_value"]
    print(f"  RECON composite current = {rc}   PROD current = {pc}   Δ={abs(rc-pc):.4f}")
    ok = worst_all < 0.01 and setmiss == 0 and abs(rc - pc) < 0.01
    print(f"  VERDICT: {'MATCH ✓' if ok else 'DRIFT ✗ — investigate'}  (worst |Δ|={worst_all:.4f}, set-mismatch={setmiss})")
    print("="*72)
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
