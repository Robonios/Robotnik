#!/usr/bin/env python3
"""
Build the structured dependency-edge dataset (Phase 0)
======================================================
Converts the FREE-TEXT supplier/customer prose on enriched companies into a
structured, entity-resolved edge dataset — replacing prose with a graph the
code can traverse.

Sources:
    data/markets/enrichment_data.json        (key_suppliers / key_customers prose)
    data/registries/entity_registry.json     (alias table, for resolution)

Output:
    data/registries/dependency_edges.json

Schema (confirmed canonical form — physical flow, supplier -> consumer):
    supplier_id   : resolved entity id, or null
    supplier_raw  : verbatim token from the prose (ground truth, always present)
    supplier_type : entity | external_company | market | category | material | in_house
    consumer_id / consumer_raw / consumer_type : same, for the downstream party
    supplied_item : verbatim parenthetical good/role, else null (NOT linked to a
                    material node in Phase 0)
    single_source : "unknown"   (never inferred in Phase 0)
    share_pct     : null        (NEVER estimated)
    confidence    : "derived-from-prose"
    parsed_from   : ["<TICKER>.key_suppliers" | ".key_customers", ...]  (two-sided merge)
    provenance    : ["<verbatim source substring>", ...]

Honesty / anti-fabrication:
  * `*_raw` is always the verbatim prose token — the audit-able ground truth.
  * `*_type` tags are HEURISTIC (lexicon + side-of-relationship). They classify,
    they do not assert facts; correct them against `*_raw` if needed.
  * single_source / share_pct are deliberately left unpopulated (Phase 0 policy:
    no inference). The chokepoint/concentration signal lives on the material
    nodes, where it is a structured source field.
  * Null markers ("n/a", "none") and list-continuations ("etc.") yield NO edge —
    they are not counterparties; emitting them would fabricate a node.
  * Commas inside numbers ("3,400+") are NOT treated as separators; leading
    conjunctions ("and X", "plus Y") and trailing punctuation are stripped so no
    fragment node is invented. Short/numeric tickers (MP, MU, ON, 600111) are
    preserved — never length-filtered.

stdlib only. Does NOT git-commit.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENRICH = ROOT / "data" / "markets" / "enrichment_data.json"
REGISTRY = ROOT / "data" / "registries" / "entity_registry.json"
OUT = ROOT / "data" / "registries" / "dependency_edges.json"

# ── Skip lists (genuinely not counterparties) ───────────────────────────────
NULL_MARKERS = {"n/a", "na", "none", "not applicable", "-", "—", "tbd", "unknown"}
STOPWORDS = {"etc", "others", "and others", "various", "multiple", "other"}
GEO = {"us", "uk", "eu", "china", "japan", "europe", "asia", "india", "korea", "taiwan"}

# ── Heuristic lexicons (type tags only; raw is always preserved) ─────────────
GENERIC_PLURAL = (
    "vendors", "vendor", "suppliers", "supplier", "manufacturers", "manufacturer",
    "providers", "provider", "integrators", "makers", "oems", "oem",
)
MARKET_KW = (
    "data centre", "data center", "datacenter", "hospital", "factory", "factories",
    "government", "agriculture", "insurance", "gaming", "embedded", "automotive",
    "enterprise", "defense", "defence", "consumer", "retail", "telecom",
    "broadband", "networking", "hyperscaler", "utility", "utilities",
    "mobile operator", "operators", "end user", "end-user", "commercial",
    "aerospace", "academic", "navy", "navies", "army", "armies", "naval",
    "military", "maritime", "customers", "clients", "deployments", "globally",
    "worldwide", "north american",
)
MATERIAL_KW = (
    "magnet", "wafer", "substrate", "composite", "gas", "gases", "sensor",
    "optic", "motor", "actuator", "battery", "batteries", "structure",
    "propellant", "steel", "rare earth", "component",
)


def norm(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s.strip(" .,-")


# Phase-1 resolver tweak: trailing product/role words let "AMD CPUs" -> AMD,
# "NVIDIA GPUs" -> NVIDIA, "Intel Foundry" -> Intel, "Fanuc controllers" -> Fanuc.
RESOLVE_TAIL = {"cpus", "gpus", "socs", "soc", "ics", "chips", "controllers",
                "plcs", "foundry", "gpu", "cpu", "modules", "backhaul",
                "fulfillment", "integrations", "ecosystem", "deployments"}


def resolve(token: str, resolver: dict):
    """Exact normalised match, else strip trailing product/role words and retry."""
    k = norm(token)
    if k in resolver:
        return resolver[k]
    words = k.split()
    while len(words) > 1 and words[-1] in RESOLVE_TAIL:
        words = words[:-1]
        cand = " ".join(words)
        if cand in resolver:
            return resolver[cand]
    return None


# Phase-1 material-node wiring (CoWoS / ABF substrate / high-purity quartz)
ABF_MAKERS = {"ibiden", "unimicron", "shinko", "shinko electric", "at&s",
              "nan ya pcb", "dnp", "dai nippon printing", "toppan",
              "4062 jp", "3037 tt", "8046 tt", "shinko-electric"}

# Phase-1 Task-3 residual cleanup lexicons
GEO_SET = {"us", "uk", "eu", "china", "japan", "europe", "asia", "india", "korea",
           "taiwan", "albania", "atlanta", "chicago", "miami", "australia",
           "brazil", "luxembourg", "middle east", "western europe",
           "south america", "gulf", "dallas-fort worth"}
COMPONENT_ACRONYM = {"hbm", "vcsel", "vcsels", "mems", "soc", "socs", "fpga",
                     "asic", "mcu", "mcus", "sram", "dram", "spad", "imu", "pcb",
                     "cmos", "rffe", "pmic", "lnb", "buc", "nand", "ssd", "fog"}
FRAGMENT_WORDS = (" for ", " with ", " via ", " including ", "added ", " using ",
                  " plus ", " primarily", " historically", "integrated",
                  "requiring", " designs ", " across ", "internal", "captive",
                  "vertically", "largely", "reducer ", " on export")


def reclassify_residual(raw: str, side: str):
    """Refine an unresolved external_company tag, or return 'DROP' for a true
    non-counterparty fragment. raw is always preserved on the edge regardless."""
    low = " " + raw.lower() + " "
    nn = norm(raw)
    words = raw.split()
    if any(w in low for w in FRAGMENT_WORDS) or len(words) >= 5:
        return "DROP"
    if nn in GEO_SET:
        return "geography"
    if nn in COMPONENT_ACRONYM:
        return "material"
    if any(w in raw.lower() for w in MARKET_KW) or re.search(r"\d\+", raw):
        return "market"
    if any(w in raw.lower() for w in MATERIAL_KW):
        return "material"
    if re.fullmatch(r"[A-Z0-9&/-]{2,5}", raw):
        return "descriptor"
    return "external_company"


def build_resolver(registry: dict):
    """norm(token) -> entity id, from id/entity_id/public_ticker/name/aliases."""
    lookup, collisions = {}, set()
    records = registry.values() if isinstance(registry, dict) else registry
    for rec in records:
        eid = rec.get("id") or rec.get("entity_id")
        if not eid:
            continue
        tokens = [rec.get("id"), rec.get("entity_id"), rec.get("public_ticker"),
                  rec.get("name")] + (rec.get("aliases") or [])
        for tok in tokens:
            k = norm(tok)
            if not k:
                continue
            if k in lookup and lookup[k] != eid:
                collisions.add(k)
                continue  # first-wins; ambiguous token recorded
            lookup.setdefault(k, eid)
    return lookup, collisions


def split_top_level(s: str):
    """Split on commas/semicolons NOT inside parentheses and NOT inside a number."""
    parts, buf, depth = [], [], 0
    for i, ch in enumerate(s):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        if ch in ",;" and depth == 0:
            prevc = s[i - 1] if i > 0 else ""
            nextc = s[i + 1] if i + 1 < len(s) else ""
            if ch == "," and prevc.isdigit() and nextc.isdigit():
                buf.append(ch)            # "3,400" — keep the number intact
                continue
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    parts.append("".join(buf))
    return [p.strip() for p in parts if p.strip()]


def split_co_entities(head: str):
    """Split co-listed parties on '/' and ' plus ' (NOT ' and '/'&' — keeps AT&T,
    and avoids Oxford-comma fragments)."""
    pieces = re.split(r"\s*/\s*|\s+plus\s+", head)
    return [p.strip() for p in pieces if p.strip()]


def clean_party(raw: str):
    """Strip leading conjunctions + trailing punctuation; drop non-counterparties.
    Returns a cleaned token, or None to skip (never length/numeric-filtered)."""
    r = re.sub(r"^(and|plus|or|&|incl\.?|including)\s+", "", raw.strip(), flags=re.I).strip()
    r = r.strip(" .;,")
    if not r:
        return None
    lr = r.lower()
    if lr in NULL_MARKERS or lr.startswith("n/a") or lr in STOPWORDS:
        return None
    if len(r) == 1 and r.isalpha():     # 'a','n' fragments — but keep numerics
        return None
    return r


def looks_like_name(tok: str) -> bool:
    return bool(re.search(r"[A-Z]", tok)) and not tok.islower()


def classify(raw: str, resolver: dict, side: str, in_house: bool):
    """Return (type, entity_id). side is 'supplier' or 'customer'."""
    eid = resolve(raw, resolver)
    if eid:
        return "entity", eid
    low = raw.lower()
    if in_house or "in-house" in low or "in house" in low:
        return "in_house", None
    # generic plural FIRST: a vendor-class on the supply side, an end-market on the buy side
    if any(low.endswith(w) or (" " + w) in (" " + low) for w in GENERIC_PLURAL):
        return ("category" if side == "supplier" else "market"), None
    # materials are inputs -> only meaningful on the supplier side
    if side == "supplier" and any(w in low for w in MATERIAL_KW):
        return "material", None
    if any(w in low for w in MARKET_KW) or re.search(r"\d\+", low) or low in GEO:
        return "market", None
    return "external_company", None     # neutral default; raw preserved for audit


def parse_field(text: str, resolver: dict, side: str):
    """Yield (party_raw, party_type, party_id, supplied_item, provenance_token)."""
    if norm(text) in NULL_MARKERS or norm(text).startswith("n/a"):
        return
    for token in split_top_level(text):
        prov = token
        m = re.search(r"\(([^()]*)\)\s*$", token)
        paren = m.group(1).strip() if m else None
        head = (token[: m.start()] if m else token).strip(" ,;")
        if norm(head) in NULL_MARKERS or norm(head).startswith("n/a"):
            continue
        in_house = bool(paren and ("in-house" in paren.lower() or "in house" in paren.lower()))

        # Decide whether the parenthetical is an ENTITY LIST or a SUPPLIED ITEM.
        paren_as_entities, cand = False, []
        if paren and not in_house:
            cand = [c.strip() for c in re.split(r"\s*[,/]\s*|\s+and\s+", paren) if c.strip()]
            resolved_any = any(resolve(c, resolver) for c in cand)
            capitalised = sum(1 for c in cand if looks_like_name(c))
            looks_like_list = len(cand) >= 2 and capitalised >= max(1, len(cand) // 2)
            paren_as_entities = resolved_any or looks_like_list

        if paren_as_entities:
            for c in cand:                       # parties are inside the parens
                c = clean_party(c)
                if not c:
                    continue
                t, eid = classify(c, resolver, side, in_house=False)
                yield c, t, eid, None, prov
        else:
            supplied = None if (in_house or not paren) else paren
            for party in split_co_entities(head) or [head]:
                party = clean_party(party)
                if not party:
                    continue
                t, eid = classify(party, resolver, side, in_house=in_house)
                yield party, t, eid, supplied, prov


def edge_key(sup_id, sup_raw, con_id, con_raw):
    s = sup_id or ("raw:" + norm(sup_raw))
    c = con_id or ("raw:" + norm(con_raw))
    return (s, c)


def main() -> int:
    enrich = json.loads(ENRICH.read_text())
    registry = json.loads(REGISTRY.read_text())
    resolver, collisions = build_resolver(registry)

    edges = {}
    companies_parsed = 0

    def add(sup_raw, sup_type, sup_id, con_raw, con_type, con_id,
            supplied, parsed_from, prov):
        if sup_id and con_id and sup_id == con_id:
            return  # drop self-loop (vertical integration of a resolved entity)
        key = edge_key(sup_id, sup_raw, con_id, con_raw)
        e = edges.get(key)
        if e is None:
            edges[key] = {
                "supplier_id": sup_id, "supplier_raw": sup_raw, "supplier_type": sup_type,
                "consumer_id": con_id, "consumer_raw": con_raw, "consumer_type": con_type,
                "supplied_item": supplied,
                "single_source": "unknown",
                "share_pct": None,
                "confidence": "derived-from-prose",
                "parsed_from": [parsed_from],
                "provenance": [prov],
            }
        else:
            if parsed_from not in e["parsed_from"]:
                e["parsed_from"].append(parsed_from)
            if prov not in e["provenance"]:
                e["provenance"].append(prov)
            if e["supplied_item"] is None and supplied:
                e["supplied_item"] = supplied
            if e["supplier_id"] is None and sup_id:        # prefer a resolved end
                e["supplier_id"], e["supplier_type"] = sup_id, sup_type
            if e["consumer_id"] is None and con_id:
                e["consumer_id"], e["consumer_type"] = con_id, con_type

    for ticker, rec in enrich.items():
        rid = resolve(ticker, resolver)
        anchor_id = rid                                    # None if unresolved (no raw fallback)
        anchor_type = "entity" if rid else "external_company"
        touched = False

        for raw, ptype, pid, supplied, prov in parse_field(
                rec.get("key_suppliers") or "", resolver, side="supplier"):
            touched = True
            add(raw, ptype, pid, ticker, anchor_type, anchor_id,
                supplied, f"{ticker}.key_suppliers", prov)

        for raw, ptype, pid, supplied, prov in parse_field(
                rec.get("key_customers") or "", resolver, side="customer"):
            touched = True
            add(ticker, anchor_type, anchor_id, raw, ptype, pid,
                supplied, f"{ticker}.key_customers", prov)

        if touched:
            companies_parsed += 1

    # Total sort key (case-insensitive primary, exact-string tie-break) so the
    # output is deterministic regardless of dict/set iteration order.
    edge_list = sorted(
        edges.values(),
        key=lambda e: (e["supplier_raw"].lower(), e["consumer_raw"].lower(),
                       e["supplier_raw"], e["consumer_raw"],
                       e["supplier_id"] or "", e["consumer_id"] or ""),
    )

    # ── Phase 1: wire CoWoS / ABF / quartz edges to material-node keys ──
    wired = {"cowos": 0, "abf-substrate": 0, "high-purity-quartz": 0}
    for e in edge_list:
        text = " ".join(filter(None, [e["supplied_item"], e["supplier_raw"],
                                      e["consumer_raw"]])).lower()
        si = (e["supplied_item"] or "").lower()
        node = None
        if "cowos" in text:
            node = "cowos"
        elif "quartz" in text:
            node = "high-purity-quartz"
        elif "abf" in text:
            node = "abf-substrate"
        elif ("substrate" in si and not any(x in text for x in ("sic", "gan", "glass"))
              and (norm(e["supplier_raw"]) in ABF_MAKERS
                   or e["supplier_id"] in {"4062 JP", "3037 TT", "8046 TT", "shinko-electric"})):
            node = "abf-substrate"
        e["material_node"] = node
        if node:
            wired[node] += 1

    # ── Phase 1 Task 3: reclassify residual external_company ends; drop true
    #    non-counterparty fragments (recorded, never silently). *_raw preserved. ──
    dropped, cleaned = [], []
    for e in edge_list:
        frags = []
        for side in ("supplier", "consumer"):
            if e[f"{side}_type"] == "external_company" and not e[f"{side}_id"]:
                nt = reclassify_residual(e[f"{side}_raw"], side)
                if nt == "DROP":
                    frags.append(e[f"{side}_raw"])
                elif nt != "external_company":
                    e[f"{side}_type"] = nt
        if frags:
            dropped.append({"fragment": frags[0],
                            "edge": f'{e["supplier_raw"]} -> {e["consumer_raw"]}',
                            "parsed_from": e["parsed_from"]})
        else:
            cleaned.append(e)
    edge_list = cleaned

    def dist(field):
        out = {}
        for e in edge_list:
            out[e[field]] = out.get(e[field], 0) + 1
        return dict(sorted(out.items(), key=lambda kv: -kv[1]))

    both = sum(1 for e in edge_list if e["supplier_id"] and e["consumer_id"])
    sup_only = sum(1 for e in edge_list if e["supplier_id"] and not e["consumer_id"])
    con_only = sum(1 for e in edge_list if e["consumer_id"] and not e["supplier_id"])
    neither = sum(1 for e in edge_list if not e["supplier_id"] and not e["consumer_id"])

    unresolved_named = sorted({
        e["supplier_raw"] for e in edge_list
        if e["supplier_type"] == "external_company" and not e["supplier_id"]
    } | {
        e["consumer_raw"] for e in edge_list
        if e["consumer_type"] == "external_company" and not e["consumer_id"]
    }, key=lambda s: (s.lower(), s))   # total key — deterministic under case-variant ties

    out = {
        "meta": {
            "layer": "dependency_edges",
            "generated_by": "scripts/build_dependency_edges.py",
            "generated_from": str(ENRICH.relative_to(ROOT)),
            "resolver": str(REGISTRY.relative_to(ROOT)) + " (id/ticker/name/aliases, first-wins)",
            "schema": ("canonical supplier->consumer flow; single_source/share NOT "
                       "inferred (Phase 0); *_type heuristic, *_raw verbatim ground truth"),
            "companies_with_prose_parsed": companies_parsed,
            "edges_total": len(edge_list),
            "resolution": {
                "both_resolved": both,
                "supplier_only": sup_only,
                "consumer_only": con_only,
                "neither_resolved": neither,
            },
            "supplier_type_distribution": dist("supplier_type"),
            "consumer_type_distribution": dist("consumer_type"),
            "material_node_wiring": wired,
            "dropped_fragments": {"count": len(dropped), "all": dropped},
            "ambiguous_alias_tokens": len(collisions),
            "unresolved_named_externals": unresolved_named,
        },
        "edges": edge_list,
    }
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")

    print(f"[dependency_edges] wrote {OUT.relative_to(ROOT)}")
    print(f"  companies parsed: {companies_parsed}")
    print(f"  edges: {len(edge_list)}  "
          f"(both_resolved={both} supplier_only={sup_only} "
          f"consumer_only={con_only} neither={neither})")
    print(f"  BACKBONE (entity<->entity): {both}")
    print(f"  supplier_type: {dist('supplier_type')}")
    print(f"  consumer_type: {dist('consumer_type')}")
    print(f"  material-node wiring: {wired}")
    print(f"  dropped fragments: {len(dropped)}")
    print(f"  unresolved named externals: {len(unresolved_named)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
