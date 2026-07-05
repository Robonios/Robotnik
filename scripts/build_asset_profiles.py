#!/usr/bin/env python3
"""
Robotnik Frontier Assets — per-entity profile shard generator
=============================================================
Emits data/assets/{slug}.json for every ACTIVE registry entity except the
disputed Resonac/Hodogaya/Daicel constituent (registry key "4112 JP", or
Resonac's "4004" if a parallel re-key has landed — matched on both, skipped).

One shard per entity, nine-layer schema (identity, classification, bottleneck,
dependency, market_context, capital, policy, geographic, editorial) under a meta
wrapper. Explicit states everywhere; null is written in preference to omission.

Sources (read-only):
  data/registries/entity_registry.json   active universe + identity/classification
  data/markets/enrichment_data.json       bottleneck ratings + dependency map (public)
  data/index/weights.json                 index membership + weight (band + rank only)
  data/registries/cik_map.json            SEC CIK for matched active-public tickers

HARD CONSTRAINT (ToS): shards carry no raw vendor field. Weight appears only as a
band and a sector rank, never as a number. A per-shard guard aborts on any leak.

Join key (public): public_ticker, falling back to the registry id. Cerebras is the
sole id != ticker case (id "cerebras-systems", ticker "CBRS"); enrichment/weights
are ticker-keyed, so the ticker join is authoritative.

Output: data/assets/{slug}.json. This script does NOT git-commit or git-add.
"""
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REG_PATH = ROOT / "data" / "registries" / "entity_registry.json"
ENR_PATH = ROOT / "data" / "markets" / "enrichment_data.json"
WEIGHTS_PATH = ROOT / "data" / "index" / "weights.json"
CIK_PATH = ROOT / "data" / "registries" / "cik_map.json"
OUT_DIR = ROOT / "data" / "assets"

SCHEMA_VERSION = "asset-profile/1.0"

# Disputed constituent — excluded entirely, matched on both possible registry keys.
EXCLUDE_IDS = {"4112 JP", "4004"}

# weights.json sector label -> published sub-index name
SECTOR_INDEX = {
    "Semiconductor": "Robotnik Semiconductors Sub-Index",
    "Robotics": "Robotnik Robotics Sub-Index",
    "Space": "Robotnik Space Sub-Index",
    "Materials": "Robotnik Materials Sub-Index",
}

# Guard: none of these vendor field keys may ever appear in a shard. weight_pct is
# included because weight is published only as a band + rank, never a number.
BANNED_KEYS = ('"weight_pct"', '"market_cap"', '"market_cap_usd"', '"price"',
               '"pe_ratio"', '"sparkline', '"native_price"', '"native_unit"',
               '"change_24h', '"change_7d', '"change_30d', '"change_ytd',
               '"volume"')


def weight_band(w):
    """weight_pct -> categorical band. No raw number leaves this function."""
    if w is None:
        return None
    if w < 0.25:
        return "<0.25"
    if w < 0.5:
        return "0.25-0.5"
    if w < 1:
        return "0.5-1"
    if w < 2:
        return "1-2"
    if w < 3.5:
        return "2-3.5"
    if w < 5:
        return "3.5-5"
    return "5-capped"


def slugify(rid):
    """Registry id -> URL-safe slug. Pure-alphanumeric ids are used verbatim;
    ids with spaces or other characters are lowercased and hyphen-collapsed.
    Deterministic; the caller detects collisions."""
    if re.fullmatch(r"[A-Za-z0-9]+", rid):
        return rid
    return re.sub(r"[^a-z0-9]+", "-", rid.lower()).strip("-")


def clean(x):
    """null / empty-string / empty-collection -> None (explicit null)."""
    if x is None:
        return None
    if isinstance(x, str) and x.strip() == "":
        return None
    if isinstance(x, (list, dict)) and len(x) == 0:
        return None
    return x


def main():
    reg = json.loads(REG_PATH.read_text())
    enr = json.loads(ENR_PATH.read_text())
    weights = json.loads(WEIGHTS_PATH.read_text())["weights"]
    cik = json.loads(CIK_PATH.read_text())

    weights_by = {w["ticker"]: w for w in weights}
    cik_by = {m["ticker"]: m["cik"] for m in cik.get("matched", [])}

    # sector rank within the index (by weight_pct desc, ticker tiebreak). Computed
    # over ALL constituents including the excluded one — it stays an index member;
    # only its profile shard is withheld.
    rank_by = {}
    by_sector = defaultdict(list)
    for w in weights:
        by_sector[w["sector"]].append(w)
    for rows in by_sector.values():
        for i, w in enumerate(sorted(rows, key=lambda r: (-r["weight_pct"], r["ticker"])), start=1):
            rank_by[w["ticker"]] = i

    active = {k: v for k, v in reg.items() if v.get("status") != "excluded"}
    now = datetime.now(timezone.utc).isoformat()

    # ── Pre-pass: slugs + collision detection (case-insensitive; macOS) ──
    slug_map = {}          # id -> slug
    seen = {}              # slug.lower() -> id
    collisions = []
    for rid in sorted(active):
        if rid in EXCLUDE_IDS:
            continue
        s = slugify(rid)
        if s.lower() in seen:
            collisions.append((rid, seen[s.lower()], s))
        else:
            seen[s.lower()] = rid
        slug_map[rid] = s
    if collisions:
        print("SLUG COLLISIONS (aborting, no shards written):", file=sys.stderr)
        for a, b, s in collisions:
            print("  {!r} and {!r} -> {!r}".format(a, b, s), file=sys.stderr)
        sys.exit(2)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    written = 0
    skipped = []
    states = defaultdict(int)

    for rid, v in sorted(active.items()):
        if rid in EXCLUDE_IDS:
            skipped.append(rid)
            continue
        typ = v["type"]
        slug = slug_map[rid]
        join_key = v.get("public_ticker") or rid    # ticker for public; id otherwise

        e = enr.get(join_key) if isinstance(enr.get(join_key), dict) else None

        # ── identity ──
        identity = {
            "name": v.get("name"),
            "aliases": v.get("aliases") or [],
            "type": typ,
            "lifecycle_status": clean(v.get("lifecycle_status")),
            "description": None,
            "identifiers": {
                "ticker": clean(v.get("public_ticker")),
                "coingecko_id": clean(v.get("coingecko_id")),
                "cik": cik_by.get(join_key),
            },
        }

        # ── classification ──
        universe_status = ("active_token" if typ == "token"
                           else "active_private" if typ == "private"
                           else "index_constituent")
        classification = {
            "sector": clean(v.get("sector")),
            "subsector": clean(v.get("subsector")),
            "value_chain": clean(v.get("value_chain")),
            "universe_status": universe_status,
        }

        # ── bottleneck (enrichment store; registry provisional as fallback) ──
        if e and clean(e.get("bottleneck_risk")):
            bn_rating = clean(e.get("bottleneck_risk"))
            bn_desc = clean(e.get("bottleneck_description"))
            bn_conf = clean(e.get("confidence"))
        elif clean(v.get("bottleneck_risk")):        # rare provisional (2 private)
            bn_rating = clean(v.get("bottleneck_risk"))
            bn_desc = clean(v.get("rating_note"))
            bn_conf = "provisional" if v.get("rating_provisional") else None
        else:
            bn_rating = bn_desc = bn_conf = None
        bottleneck = {
            "rating": bn_rating,
            "description": bn_desc,
            "confidence": bn_conf,
            "state": "rated" if bn_rating else "unrated",
        }

        # ── dependency ──
        kc = clean(e.get("key_customers")) if e else None
        ks = clean(e.get("key_suppliers")) if e else None
        dependency = {
            "key_customers": kc,
            "key_suppliers": ks,
            "state": "mapped" if (kc or ks) else "unmapped",
        }

        # ── market_context (band + rank only; never a raw weight) ──
        if typ == "public" and join_key in weights_by:
            wrow = weights_by[join_key]
            market_context = {
                "member": True,
                "sector_index": SECTOR_INDEX.get(wrow["sector"], wrow["sector"]),
                "weight_band": weight_band(wrow["weight_pct"]),
                "sector_rank": rank_by.get(join_key),
                "state": "live",
            }
        elif typ == "token":
            market_context = {"member": False, "sector_index": None,
                              "weight_band": None, "sector_rank": None,
                              "state": "token_isolated"}
        elif typ == "private":
            market_context = {"member": False, "sector_index": None,
                              "weight_band": None, "sector_rank": None,
                              "state": "private_capital_index"}
        else:  # active public not in the index (not expected in current data)
            market_context = {"member": False, "sector_index": None,
                              "weight_band": None, "sector_rank": None,
                              "state": "live"}

        # ── capital (private funding; not a vendor field) ──
        last_round = clean(v.get("last_round"))
        traised = clean(v.get("total_raised_m"))
        if typ == "private":
            cap_state = "live" if traised else "sparse"
        else:
            cap_state = "forthcoming"       # public + token
        capital = {"last_round": last_round, "total_raised_m": traised, "state": cap_state}

        # ── editorial ──
        notes = clean(e.get("robotnik_notes")) if e else None
        editorial = {"notes": notes, "state": "authored" if notes else "forthcoming"}

        shard = {
            "meta": {"id": rid, "slug": slug, "schema_version": SCHEMA_VERSION, "generated_at": now},
            "identity": identity,
            "classification": classification,
            "bottleneck": bottleneck,
            "dependency": dependency,
            "market_context": market_context,
            "capital": capital,
            "policy": {"state": "forthcoming"},
            "geographic": {
                "hq_country": clean(v.get("country")),
                "hq_city": clean(v.get("city")),
                "exposure": {"state": "forthcoming"},
            },
            "editorial": editorial,
        }

        # ── ToS guard: no raw vendor field / raw weight may leak ──
        blob = json.dumps(shard)
        leaks = [b for b in BANNED_KEYS if b in blob]
        if leaks:
            print("ToS VIOLATION in {}: {}".format(slug, leaks), file=sys.stderr)
            sys.exit(3)

        (OUT_DIR / "{}.json".format(slug)).write_text(
            json.dumps(shard, indent=2, ensure_ascii=False) + "\n")
        written += 1

        # tallies for the run report
        states["bottleneck:" + bottleneck["state"]] += 1
        states["dependency:" + dependency["state"]] += 1
        states["market:" + market_context["state"]] += 1
        if typ == "private":
            states["capital:" + cap_state] += 1
        states["universe:" + universe_status] += 1

    # ── run report ──
    print("=" * 64)
    print("ROBOTNIK ASSET PROFILE SHARDS")
    print("=" * 64)
    print("active entities:      {}".format(len(active)))
    print("skipped (disputed):   {}".format(skipped))
    print("shards written:       {}  -> {}".format(written, OUT_DIR.relative_to(ROOT)))
    print("\nstate distribution:")
    for k in sorted(states):
        print("  {:32s} {}".format(k, states[k]))
    dirty = {i: s for i, s in slug_map.items() if i != s}
    print("\nslug rewrites (id != slug): {} (the other {} use the id verbatim)".format(
        len(dirty), written - len(dirty)))
    for i in sorted(dirty):
        print("  {:16s} -> {}".format(i, dirty[i]))


if __name__ == "__main__":
    main()
