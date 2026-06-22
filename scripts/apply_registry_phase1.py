#!/usr/bin/env python3
"""
Apply the Phase 1 registry expansion (additive, index-inert)
============================================================
Reads data/registries/phase1_registry_patch.json and applies it to
entity_registry.json:

  1. ADDITIONS — expand each compact record to the full registry structure and
     insert. Every addition is status='excluded', exclude_reason='supply_chain_node',
     enrichment='pending', so it RESOLVES dependency edges but is INERT to the index
     (the reverse-parity guard requires non-excluded *public* names to be in the
     index; these are excluded -> exempt). CORE fields only; curated fields null.
  2. MANUAL ALIASES — subsidiary/renamed prose names -> existing parent entity
     (e.g. "Aerojet Rocketdyne" -> LHX, "OneWeb" -> eutelsat).
  3. AUTO ALIAS-FIXES — clean company tokens in the dependency-edge unresolved
     bucket that match an existing entity by relaxed (alias-startswith) matching
     get added as an exact alias. Product-suffix cases ("AMD CPUs") are NOT
     aliased here — the resolver tweak in build_dependency_edges.py handles those.

Idempotent: re-running skips ids/aliases already present. Writes the registry with
the file's exact serializer (json.dumps indent=2 ensure_ascii=True, NO trailing
newline) so the diff touches only added entities + grown alias lists.

Does NOT git-commit. stdlib only.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "data" / "registries" / "entity_registry.json"
PATCH = ROOT / "data" / "registries" / "phase1_registry_patch.json"
ENRICH = ROOT / "data" / "markets" / "enrichment_data.json"

# words that disqualify an unresolved name from being auto-aliased to a company
NONCOMPANY = (
    "vendors", "suppliers", "manufacturers", "providers", "integrators", "oems",
    "customers", "clients", "operators", "data centre", "data center", "hospital",
    "automotive", "aerospace", "academic", "government", "defense", "military",
    "agriculture", "enterprise", "consumer", "retail", "logistics", "fleet",
    "components", "materials", "specialty", "foundries", "globally", "worldwide",
    "for", "with", "via", "including", "added", "using", "plus", "internal",
    "internally", "vertically", "primarily", "historically",
)
PRODUCT_TAIL = ("cpus", "gpus", "socs", "soc", "ics", "chips", "controllers",
                "plcs", "foundry", "peers", "fulfillment", "integrations",
                "ecosystem", "deployments", "crucibles", "gamesa", "partners")
# Single-word tokens that are common English words OR collide with a DIFFERENT
# well-known entity than the one a name-prefix match would pick. These are
# ambiguous -> never auto-aliased; flagged for human review instead.
# (e.g. "Delta" = Delta Air Lines not Delta Electronics; "Aurora" = Aurora
#  Innovation not Aurora Flight Sciences; "NIO" = the EV maker not a startup.)
AMBIGUOUS_SINGLE = {
    "alpha", "delta", "leader", "aurora", "nio", "tower", "charger", "gulf",
    "pony", "green", "best", "gree", "apex", "summit", "horizon", "vision",
    "unity", "atlas", "nova", "orbit",
    # generic English / component words that collide with a company name prefix
    "auto", "motor", "motors", "drive", "drives", "sensor", "sensors",
    "control", "controls", "power", "laser", "optics", "battery", "batteries",
    "materials", "components", "systems", "solutions", "technologies",
    "semiconductor", "semiconductors", "micro", "robotics", "electronics",
    "precision", "digital", "smart", "advanced", "industrial",
}


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower()).strip(" .,-")


def build_alias_index(reg):
    idx, first = {}, {}
    for rid, r in reg.items():
        for t in [r.get("id"), r.get("entity_id"), r.get("public_ticker"),
                  r.get("name")] + (r.get("aliases") or []):
            k = norm(t)
            if k:
                idx.setdefault(k, rid)
    return idx


def main() -> int:
    reg = json.loads(REGISTRY.read_text())
    patch = json.loads(PATCH.read_text())

    added, skipped, skip_merged = [], [], []
    for rec in patch["additions"]:
        rid = rec["id"]
        if rid in reg:
            # already present -> don't re-add, but merge the patch's prose aliases
            # so its prose name (e.g. "Texas Instruments") still resolves to it.
            existing = reg[rid]["aliases"]
            have = {norm(x) for x in existing}
            merged = [a for a in rec.get("aliases", []) if norm(a) not in have]
            existing.extend(merged)
            skipped.append(rid)
            if merged:
                skip_merged.append((rid, merged))
            continue
        # build aliases: patch aliases + id + name + lowercased name, deduped
        aliases, seen = [], set()
        for a in (rec.get("aliases", []) + [rid, rec["name"], rec["name"].lower()]):
            if a and a not in seen:
                seen.add(a)
                aliases.append(a)
        is_public = rec["lifecycle_status"] == "public"
        reg[rid] = {
            "id": rid,
            "name": rec["name"],
            "type": rec["type"],
            "sector": rec["sector"],
            "subsector": None,
            "country": rec.get("country"),
            "city": None,
            "eodhd_ticker": None,
            "coingecko_id": None,
            "description": None,
            "aliases": aliases,
            "value_chain": None,
            "entity_id": rid,
            "lifecycle_status": rec["lifecycle_status"],
            "public_ticker": rid if is_public else None,
            "status": "excluded",
            "exclude_reason": "supply_chain_node",
            "enrichment": "pending",
            "phase1_status_note": rec.get("status_note"),
        }
        if rec.get("universe_review"):
            # major absent semis flagged for a SEPARATE universe-inclusion review
            # (added as index-inert supply-chain nodes now; not auto-admitted)
            reg[rid]["universe_review"] = rec["universe_review"]
        added.append(rid)

    # manual subsidiary/renamed aliases onto existing parents
    manual = []
    for m in patch.get("manual_aliases", []):
        eid = m["entity_id"]
        if eid not in reg:
            manual.append((eid, "PARENT-ABSENT", m["add_aliases"]))
            continue
        al = reg[eid]["aliases"]
        new = [a for a in m["add_aliases"] if a not in al and norm(a) not in {norm(x) for x in al}]
        al.extend(new)
        if new:
            manual.append((eid, "added", new))

    # auto alias-fixes: derive unresolved candidate names DIRECTLY from the
    # enrichment prose (paren-aware top-level split), NOT from a generated edges
    # file — so the result is independent of run order / a stale edges artifact.
    auto, flagged = [], []
    if ENRICH.exists():
        enr = json.loads(ENRICH.read_text())
        idx = build_alias_index(reg)
        cands = set()
        for r in enr.values():
            for field in ("key_suppliers", "key_customers"):
                text = r.get(field) or ""
                parts, buf, depth = [], [], 0
                for ch in text:
                    if ch == "(":
                        depth += 1
                    elif ch == ")":
                        depth = max(0, depth - 1)
                    if ch in ",;" and depth == 0:
                        parts.append("".join(buf)); buf = []
                    else:
                        buf.append(ch)
                parts.append("".join(buf))
                for p in parts:
                    # harvest BOTH the paren-stripped head AND paren-inner tokens
                    # (the latter recovers names like "Lam" in "... OEMs (Lam, AMAT)")
                    pieces = [re.sub(r"\(.*?\)", "", p)] + re.findall(r"\(([^()]*)\)", p)
                    for piece in pieces:
                        for sub in re.split(r"\s*[,/]\s*|\s+and\s+", piece):
                            sub = sub.strip(" .,;")
                            if sub and norm(sub) not in idx:
                                cands.add(sub)
        unresolved = sorted(cands, key=lambda s: (s.lower(), s))
        # alias_list for startswith matching
        alias_pairs = [(norm(t), rid) for rid, r in reg.items()
                       for t in [r.get("name")] + (r.get("aliases") or []) if norm(t)]
        for name in unresolved:
            nn = norm(name)
            if not nn or nn in idx:
                continue  # empty or already resolves exactly
            low = name.lower()
            words = name.split()
            if len(words) > 4 or not re.search(r"[A-Za-z]", name):
                continue
            if any(w in low for w in NONCOMPANY) or any(low.endswith(w) for w in PRODUCT_TAIL):
                continue
            # unique alias-startswith match
            hits = {rid for a, rid in alias_pairs if a.startswith(nn + " ")}
            if len(hits) != 1:
                continue
            rid = next(iter(hits))
            # a single common/colliding word is too ambiguous to assert -> flag it
            if len(words) == 1 and low in AMBIGUOUS_SINGLE:
                flagged.append((name, rid))
                continue
            if name not in reg[rid]["aliases"]:
                reg[rid]["aliases"].append(name)
                auto.append((name, rid))

    REGISTRY.write_text(json.dumps(reg, indent=2, ensure_ascii=True))

    print(f"[registry_phase1] additions: {len(added)} added, {len(skipped)} skipped (already present)")
    print(f"  added ids: {added}")
    if skip_merged:
        print(f"  alias-merged onto already-present ids: {skip_merged}")
    print(f"  manual aliases: {[(e, a) for e, s, a in manual if s == 'added']}")
    print(f"  auto alias-fixes: {len(auto)}")
    for name, rid in sorted(auto, key=lambda x: x[0].lower()):
        print(f"     {name!r} -> {rid}")
    print(f"  FLAGGED ambiguous (NOT auto-applied — review): {len(flagged)}")
    for name, rid in sorted(flagged, key=lambda x: x[0].lower()):
        print(f"     {name!r} ~ would-match {rid} (ambiguous single word — left unresolved)")
    uni = [rid for rid, r in reg.items() if r.get("universe_review") == "pending"]
    print(f"  universe-inclusion review flags (separate workstream): {uni}")
    print(f"  registry size now: {len(reg)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
