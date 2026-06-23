# Phase 0 — Material layer + dependency edges: coverage report

**Branch:** `phase0-material-layer-edges` · **Scope:** additive only (2 generators + 2 served datasets). No existing file altered; no live metrics, facilities, or new chokepoint nodes built.

## What now exists

| Artifact | Path | Generator |
|---|---|---|
| Material nodes (served) | `data/markets/material_nodes.json` | `scripts/build_material_nodes.py` |
| Dependency edges | `data/registries/dependency_edges.json` | `scripts/build_dependency_edges.py` |

Both generators are stdlib-only, idempotent (byte-identical across `PYTHONHASHSEED` values), and do not git-commit.

## 1. Material layer (promoted from staging → served)

- **56 material nodes** live, every rating field copied **verbatim** from `proposed_commodities_bottleneck_ratings.json` (ratings not re-judged). Each node gains a stable slug `key` + a price-index link.
- **Price-index linkage** (normalised-name join into `data/index/commodities_index.json`):
  - **14 priced-linked** (live USD price): Gallium, Dysprosium, Germanium, Copper, Nickel, Tin, Neodymium, Terbium, Cobalt, Silver, Antimony, Indium, Aluminium, Palladium.
  - **4 pending-linked** (in index, awaiting a price source): Scandium, Tantalum, Yttrium, Tungsten.
  - **38 unlinked** — node-level supply-risk reach the price index does *not* cover (gases, substrates, photoresist, propellants, etc.).
- **Honest gap:** two priced constituents have **no rated counterpart by design** and therefore no node — Silicon (index = metallurgical; nearest rated node is the *different* material "Hyperpure polysilicon") and Praseodymium (priced standalone; rated layer bundles Pr into "Neodymium (NdPr oxide)"). Not force-linked.

## 2. Dependency edges (prose → structured graph)

- **161 companies** parsed; **1,243 edges** (deduped, canonical supplier → consumer flow, two-sided assertions merged).
- **193 distinct registry entities** participate in the graph.

**Resolution quality:**

| Tier | Count | Meaning |
|---|---|---|
| Entity ↔ entity (both resolved) | **165** | High-confidence backbone — both ends are registry IDs |
| Anchor + `category` | 99 | resolved company ↔ a vendor-class (e.g. "equipment vendors") |
| Anchor + `material` | 68 | resolved company ↔ a material input (e.g. "rare earth magnets") |
| Anchor + `market` | 226 | resolved company ↔ an end-market (e.g. "data centres") |
| Anchor + `in_house` | 8 | vertical integration (e.g. "Rutherford engine (in-house)") |
| Anchor + `external_company` | 677 | resolved company ↔ a named, **out-of-registry** company |

Every edge is anchored on a resolved entity (`neither_resolved = 0`). `single_source` and `share_pct` are deliberately left `unknown`/`null` (Phase-0 no-inference policy).

**Unresolved counterparties — flagged, not dropped:** the **563 distinct `external_company` names** (full list in the JSON `meta.unresolved_named_externals`) are a **mixed, noisy bucket**:
- Genuine out-of-universe companies — registry-expansion candidates: Samsung, Apple, Airbus, Bosch, Foxconn, Sony, Carl Zeiss, Amkor, Aerojet Rocketdyne, Amada, …
- Residual non-company phrases the heuristic could not classify (end-markets / materials / fragments): "AI inference at edge", "airport baggage handlers", "advanced packaging", "accelerometers", "Albania", …

`*_raw` is verbatim on every edge, so this bucket is fully auditable and is the natural input to a later cleanup / registry-expansion pass. **Type tags are heuristic; raw is ground truth.**

## 3. The five named chokepoints — node vs edge

| Chokepoint | Material node? | Surfaces as edges? | Notes |
|---|---|---|---|
| **Photoresist** | ✅ node (HIGH) | — | rated node; suppliers not item-tagged in prose |
| **Neon** | ✅ node (MEDIUM) | 3 edges | rated node + gas-supplier edges |
| **CoWoS** | ❌ no node | ✅ 1 edge | `3037 TT (Unimicron) → TSM`, supplied_item = "CoWoS substrates" |
| **ABF substrate** | ❌ no node | ✅ 11 edges | Ibiden/Unimicron → NVDA/TSM, supplied_item = "substrates" |
| **High-purity quartz** | ❌ no node | ✅ 2 edges | "quartz crucibles → 6488 TT (GlobalWafers)" |

**Net:** 2 of 5 gain a first-class material node; the other 3 are no longer prose-only — they now surface as **structured supply edges** with the chokepoint named in `supplied_item`/`*_raw`. Promoting CoWoS / ABF / quartz to first-class nodes is out of Phase-0 scope (no net-new nodes) and is the obvious Phase-1 candidate.

## Out of scope (untouched, as instructed)

Live/time-series metrics (prices, capacity, lead-times); facilities/fab layer; net-new chokepoint nodes; front-end UI (the served material dataset is fetchable; no consuming page built — `commodities.html` remains a placeholder).
