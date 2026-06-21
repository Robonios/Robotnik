#!/usr/bin/env python3
"""
Build the served Material-Nodes layer (Phase 0)
===============================================
Promotes the STAGED commodities bottleneck-rating proposal into a first-class,
served dataset of material nodes — the node-level supply-risk layer the
company-level model lacks.

Source (staging, never altered):
    data/markets/proposed_commodities_bottleneck_ratings.json   (56 rated commodities)

Output (served tree):
    data/markets/material_nodes.json

What this does (additive, non-destructive):
  * copies every rating field VERBATIM (ratings are not re-judged here),
  * assigns each node a stable slug `key`,
  * links the node to the Commodities Index by normalised name where the
    priced/price-pending universe overlaps (`commodities_index_key` +
    `commodities_index_status`).

Honest-join policy: the link is a NORMALISED-NAME join only — there is no
shared key in the source data. Two basis-conflict names are intentionally left
UNLINKED rather than force-matched:
  * Silicon (index basis = metallurgical) vs rated "Hyperpure polysilicon" — different basis.
  * Praseodymium (index, standalone) vs rated "Neodymium (NdPr oxide)" — Pr bundled with Nd.

The Commodities-Index constituent names mirror scripts/calculate_commodities_index.py
(PRICED + PENDING). If that universe changes, re-sync the two lists below.

This script does NOT git-commit. stdlib only.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "markets" / "proposed_commodities_bottleneck_ratings.json"
SRC_PHASE1 = ROOT / "data" / "markets" / "phase1_chokepoint_nodes.json"  # 3 sourced chokepoint nodes
OUT = ROOT / "data" / "markets" / "material_nodes.json"

# Commodities Index universe — mirrors calculate_commodities_index.py PRICED/PENDING
# (bare display names; the join normalises these against the rated commodity names).
PRICED_NAMES = [
    "Gallium", "Silicon", "Titanium", "Dysprosium", "Germanium", "Copper",
    "Nickel", "Tin", "Neodymium", "Terbium", "Cobalt", "Silver", "Antimony",
    "Praseodymium", "Indium", "Aluminium", "Platinum", "Phosphorus", "Gold",
    "Palladium",
]
PENDING_NAMES = [
    "Scandium", "Tantalum", "Arsenic", "Cerium", "Erbium", "Yttrium",
    "Tungsten", "Lanthanum", "Boron",
]

# Honest-gap note (not a mechanism — these simply have no matching rated node):
# two priced index constituents have NO rated counterpart by design, so they
# never link: Silicon (index basis = metallurgical; the nearest rated node is the
# DIFFERENT material "Hyperpure polysilicon") and Praseodymium (priced standalone;
# the rated layer only carries Pr bundled inside "Neodymium (NdPr oxide)").


def norm(name: str) -> str:
    """Normalise a commodity display name for the name-join."""
    s = (name or "").strip().lower()
    s = s.replace("aluminium", "aluminum")  # index uses -ium, ratings use -um
    return s


def base_name(commodity: str) -> str:
    """Strip the parenthetical sub-field context: 'Gallium (metal + GaAs...)' -> 'gallium'."""
    return norm(re.sub(r"\s*\(.*?\)\s*", "", commodity or "").strip())


def slugify(commodity: str, seen: set) -> str:
    base = re.sub(r"\s*\(.*?\)\s*", " ", commodity or "").strip()
    slug = re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-") or "node"
    candidate, n = slug, 2
    while candidate in seen:
        candidate = f"{slug}-{n}"
        n += 1
    seen.add(candidate)
    return candidate


def main() -> int:
    src = json.loads(SRC.read_text())
    ratings = src.get("ratings", [])

    # Build the normalised-name -> (index_name, status) join table.
    index_status = {}
    for nm in PRICED_NAMES:
        index_status[norm(nm)] = (nm, "priced")
    for nm in PENDING_NAMES:
        index_status[norm(nm)] = (nm, "pending")

    seen_slugs: set = set()
    nodes = []
    counts = {"priced": 0, "pending": 0, "unlinked": 0}

    for r in ratings:
        commodity = r.get("commodity", "")
        key = slugify(commodity, seen_slugs)
        bn = base_name(commodity)

        link_key, link_status = None, None
        if bn in index_status:
            link_key, link_status = index_status[bn]

        if link_status == "priced":
            counts["priced"] += 1
        elif link_status == "pending":
            counts["pending"] += 1
        else:
            counts["unlinked"] += 1

        # key first, then every original rating field VERBATIM, then the type /
        # verification / link fields. These 56 went through the Phase-0 adversarial
        # verifier (they carry verifier_verdict/evidence) -> verification="verified".
        node = {"key": key}
        node.update(r)
        node["node_type"] = "material"
        node["verification"] = "verified"
        node["commodities_index_key"] = link_key
        node["commodities_index_status"] = link_status
        nodes.append(node)

    # Phase 1: append the three sourced chokepoint nodes (CoWoS, ABF, quartz).
    # These are NOT adversarially verified — they carry verification="pending" and
    # a `sources` list, kept visibly distinct from the 56. Appended verbatim.
    phase1 = json.loads(SRC_PHASE1.read_text())
    phase1_nodes = phase1.get("nodes", [])
    for pn in phase1_nodes:
        seen_slugs.add(pn["key"])
        nodes.append(pn)

    def _dist(field):
        out = {}
        for n in nodes:
            out[n.get(field)] = out.get(n.get(field), 0) + 1
        return dict(sorted(out.items(), key=lambda kv: -kv[1]))

    out = {
        "meta": {
            "layer": "material_nodes",
            "generated_by": "scripts/build_material_nodes.py",
            "generated_from": [str(SRC.relative_to(ROOT)), str(SRC_PHASE1.relative_to(ROOT))],
            "source_step": src.get("step"),
            "source_produced": src.get("produced"),
            "framework": src.get("framework"),
            "node_count": len(nodes),
            "node_type_distribution": _dist("node_type"),
            "verification_distribution": _dist("verification"),
            "rating_distribution": src.get("distribution"),
            "price_link": {
                "priced": counts["priced"],
                "pending": counts["pending"],
                "unlinked": counts["unlinked"],
            },
            "note": (
                "56 ratings copied verbatim from the source proposal (verification="
                "'verified'); 3 Phase-1 chokepoint nodes (CoWoS, ABF substrate, "
                "high-purity quartz) appended with verification='pending' + sourced "
                "`sources` — visibly distinct, NOT merged into the verified set. "
                "commodities_index_key joins data/index/commodities_index.json by "
                "normalised name. Silicon and Praseodymium have no rated counterpart "
                "by design. See scripts/build_material_nodes.py."
            ),
        },
        "nodes": nodes,
    }

    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")

    print(f"[material_nodes] wrote {OUT.relative_to(ROOT)}")
    print(f"  nodes: {len(nodes)}  ({len(phase1_nodes)} Phase-1 pending appended)")
    print(f"  node_type: {_dist('node_type')}")
    print(f"  verification: {_dist('verification')}")
    print(f"  price-linked: priced={counts['priced']} pending={counts['pending']} "
          f"unlinked={counts['unlinked']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
