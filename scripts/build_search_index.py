#!/usr/bin/env python3
"""
Build data/registries/search_index.json — the global-search / resolver index.
=============================================================================
WHY THIS EXISTS
  search_index.json is served live and read by two surfaces:
    - js/nav.js            global search (matches id / ticker / name / aliases;
                           displays name and "ticker · sector"; routes to
                           assets.html?q=<ticker|id>)
    - js/asset-profile.js  edge-label -> profile-slug resolver (maps the
                           normalised name and each alias to the entity's slug)
  Until now NO script produced it: it was last written by hand inside a bulk
  commit on 2026-07-03 and then hand-patched in place (the Resonac 4004 JP entry
  sits out of id-sort order, physical proof of a manual edit). A served file with
  no reproducible build drifts silently from the registry. This is that build.

CONTRACT (superset-safe: emits every field either consumer reads)
  top level : {generated_at, source, note, count, entities[]}
  entity    : {id, name, ticker, sector, type, aliases}   (this exact key order)
  ordering  : entities sorted by id (the committed file's canonical order; its
              only deviation is the hand-patched 4004 JP). Order is cosmetic to
              both consumers - nav.js re-ranks its own matches, and the resolver
              map flips key collisions to unresolved regardless of insertion
              order - so a stable sort simply keeps future diffs minimal.

SOURCE - every field is a direct projection of data/registries/entity_registry.json;
         nothing is derived or hand-authored, so nothing is unreproducible:
    id      <- registry key
    name    <- name
    ticker  <- public_ticker        (null for tokens / private)
    sector  <- sector
    type    <- type                 (public | token | private)
    aliases <- aliases              (verbatim; the registry is the alias authority)
  Selection: active universe only, i.e. status == null (the excluded 143 are
  omitted, exactly as the served file does).

No vendor fields are read or emitted (ToS). Standard library only.

Usage:  python scripts/build_search_index.py [--check]
        --check  build in memory and report the delta vs the committed file
                 WITHOUT writing (exit 1 if it would change).
"""
import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY_PATH = os.path.join(ROOT, "data", "registries", "entity_registry.json")
OUT_PATH      = os.path.join(ROOT, "data", "registries", "search_index.json")

# The six fields each entity carries, in the order the served file uses.
FIELDS = ("id", "name", "ticker", "sector", "type", "aliases")


def build_entities(registry):
    """Project the active universe (status == null) to the served entity shape."""
    entities, malformed = [], []
    for rid, r in registry.items():
        if r.get("status") is not None:
            continue  # excluded / non-active
        ent = {
            "id":      rid,
            "name":    r.get("name"),
            "ticker":  r.get("public_ticker"),   # null for tokens / private
            "sector":  r.get("sector"),
            "type":    r.get("type"),
            "aliases": r.get("aliases") or [],
        }
        # Guard: these three feed live display / routing / resolution. A null here
        # would ship a broken search row, so stop rather than emit it silently.
        missing = [f for f in ("name", "sector", "type") if not ent[f]]
        if missing or not isinstance(ent["aliases"], list):
            malformed.append((rid, missing or "aliases-not-list"))
        entities.append(ent)
    if malformed:
        raise SystemExit(
            "STOP: {} active entit(ies) malformed for search_index "
            "(missing required field): {}".format(len(malformed), malformed[:20]))
    entities.sort(key=lambda e: e["id"])
    return entities


def build_index(registry):
    entities = build_entities(registry)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "entity_registry.json (active universe; status == null)",
        "note": ("Global-search index (nav.js) and asset-profile edge-label resolver "
                 "(asset-profile.js). Derived from the registry; contains no vendor fields."),
        "count": len(entities),
        "entities": entities,
    }


def main():
    check = "--check" in sys.argv
    with open(REGISTRY_PATH) as f:
        registry = json.load(f)
    index = build_index(registry)

    by_type = {}
    for e in index["entities"]:
        by_type[e["type"]] = by_type.get(e["type"], 0) + 1

    if check:
        try:
            with open(OUT_PATH) as f:
                old = json.load(f)
        except Exception:
            old = None
        old_ids = {e["id"] for e in old["entities"]} if old else set()
        new_ids = {e["id"] for e in index["entities"]}
        added, removed = sorted(new_ids - old_ids), sorted(old_ids - new_ids)
        # content changes on retained ids (ignore the top-level timestamp)
        old_map = {e["id"]: e for e in (old["entities"] if old else [])}
        changed = [i for i in sorted(new_ids & old_ids)
                   if {k: v for k, v in old_map[i].items()} !=
                      {k: e for k, e in next(x for x in index["entities"] if x["id"] == i).items()}]
        print("search_index --check:  committed={} -> rebuilt={}".format(
            old["count"] if old else "?", index["count"]))
        print("  added   ({}): {}".format(len(added), added))
        print("  removed ({}): {}".format(len(removed), removed))
        print("  content-changed on retained ids ({}): {}".format(len(changed), changed))
        drift = bool(added or removed or changed)
        print("RESULT:", "WOULD CHANGE (exit 1)" if drift else "up to date (exit 0)")
        return 1 if drift else 0

    with open(OUT_PATH, "w") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("Wrote {} ({} entities: {})".format(
        os.path.relpath(OUT_PATH, ROOT), index["count"],
        ", ".join("{} {}".format(v, k) for k, v in sorted(by_type.items()))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
