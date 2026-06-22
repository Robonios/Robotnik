# Phase 1 — chokepoint nodes + registry expansion + tag cleanup: coverage report

**Branch:** `phase0-material-layer-edges` (continues) · **Scope:** additive only. No live metrics, no facilities, no UI. Index untouched (new entities are index-inert — see §2).

## 1. Three chokepoint nodes promoted (Task 1)

`material_nodes.json` is now **59 nodes** (56 verified + **3 pending**), authored from [phase1_chokepoint_nodes.json](data/markets/phase1_chokepoint_nodes.json) with sourced figures + citations. They are visibly distinct: `verification:"pending"`, `verifier_verdict:"pending"`, a `sources` list, and **never merged** into the adversarially-verified 56.

| Node | key | node_type | rating | Sourced concentration (verbatim basis) | Confidence |
|---|---|---|---|---|---|
| CoWoS | `cowos` | **process_capacity** | CRITICAL | TSMC-dominant; ~75–80k→120–130k wafers/mo; OSAT (ASE/Amkor/JCET) ~59% of *broader* adv-packaging. Capacity-basis, no clean single %. | MEDIUM |
| ABF substrate | `abf-substrate` | material | HIGH | Ajinomoto film ~90–95% (near-monopoly); substrate top-3 ~61%. Market-research-sourced. | MEDIUM |
| High-purity quartz | `high-purity-quartz` | material | CRITICAL | >90% from Spruce Pine NC; top-2 (Sibelco, The Quartz Corp) ~75–85%. Helene 2024 exposed it. | HIGH |

**Anti-fabrication:** every figure is sourced (3 citations each); no concentration %, share, or supplier was invented. CoWoS is a `process_capacity` node — its concentration is a *capacity* basis, not a country-supply share (flagged in-node).

`node_type` (`material`×58, `process_capacity`×1) and `verification` (`verified`×56, `pending`×3) were added to **all 59**.

## 2. Registry expansion + re-resolve (Task 2)

**Backbone (entity↔entity edges): 165 → 263 (+98, +59%).**

- **39 entities added** (TXN + Hon Hai already present → alias-merged). Every addition is **`status:"excluded"`, `exclude_reason:"supply_chain_node"`, `enrichment:"pending"`** — index-inert (per your "do NOT alter membership" guardrail; verified: 0 leak into the index, none in the reverse-parity required set).
  - **25 public** (verified tickers): SK Hynix `000660 KS`, MediaTek `2454 TT`, GlobalFoundries `GFS`, Nikon `7731 JP`, Hoya, DNP, Toppan, Nan Ya PCB, AT&S, JCET, Chemours, Tronox, PPG, Daikin, Sojitz, NSK, SKF, Bystronic, Ningbo Yunsheng, Zhongke Sanhuan — **+ 5 EMS/assembly** (see below).
  - **14 private/delisted** (type-correct, no ticker): Carl Zeiss SMT, VDL, Hemlock, Schott, Traxys, maxon, TRUMPF, ArianeGroup, Thales Alenia Space, ULA, **Shinko** (delisted 2025), **KUKA** (delisted), **Proterial** (ex-Hitachi Metals, delisted), **Maxar** (private).
- **EMS/assembly — added only where edges reference them** (per your refinement): Quanta Computer `2382 TT`, Pegatron `4938 TT`, Luxshare `002475`, Huaqin `603296`, Flex `FLEX` (Foxconn/Hon Hai `2317 TT` already in registry → alias-merged; Jabil already in). **Construction-robotics (Sany, Zoomlion, XCMG) left external** — not in registry, not added.
- **Listing verification caught 17 traps** — none added as a phantom public ticker: subsidiaries aliased to in-registry parents (**Aerojet Rocketdyne→LHX**, **Aurora Flight Sciences/Spectrolab→BA**, **OneWeb→Eutelsat**); private/delisted added with correct type.
- **28 auto alias-fixes** to existing entities (Amkor, Ibiden, Infineon, Linde, Renesas, Skyworks, Siltronic, Unimicron, Wacker, Lam, NXP, Mobileye, Palantir, Sumitomo, SES, …) + a **resolver product-suffix tweak** (`AMD CPUs`→AMD, `NVIDIA GPUs`→NVDA, `Intel Foundry`→Intel).
- **Parent absent → kept external** (not added; flagged): Snecma (→Safran), Intelsat (→SES), Azur Space (→5N Plus), LeoStella (→BlackSky).

**Universe-inclusion review flag (separate workstream):** SK Hynix, MediaTek, GlobalFoundries carry `universe_review:"pending"` — major public semis added as index-inert supply-chain nodes; whether they belong in the investable universe/index is flagged for your separate review (TXN was already a non-excluded index member → no flag).

## 3. Tag cleanup (Task 3)

- **47 fragment edges dropped** (each listed in `dependency_edges.json` → `meta.dropped_fragments.all`) — all genuine non-counterparties: "Vertically integrated", "Internal Mountain Pass concentrate", "added for EyeQ6", "Japanese and Korean fabs primarily", etc. **No clean company name was dropped.**
- Residual `external_company` reclassified → `geography` (10), `descriptor` (45), `material`/`market` re-tags. No blunt length/numeric filter (Phase 0 proved that deletes real tickers); `*_raw` preserved on every edge.
- **9 ambiguous single-word matches flagged, NOT asserted** (Alpha, Aurora, auto, Delta, Leader, Motor, motor, NIO, Tower) — generic/colliding tokens: "Delta" = Delta *Air Lines* not Delta Electronics; "Aurora" = Aurora *Innovation* not Aurora Flight Sciences; "auto"/"motor" are component words, not the firms "AUTO"/"Motor AI". Left unresolved rather than mis-linked.

Net edges 1,243 → 1,191; unresolved `external_company` 563 → 378.

## 4. Five chokepoints — final status

| Chokepoint | Node | Wired edges |
|---|---|---|
| Photoresist | ✅ (verified) | — |
| Neon | ✅ (verified) | — |
| **CoWoS** | ✅ (pending) | 1 (`Unimicron→TSM`) |
| **ABF substrate** | ✅ (pending) | 2 (`Ibiden/Unimicron→NVDA`) |
| **High-purity quartz** | ✅ (pending) | 2 (`quartz crucibles→GlobalWafers/Siltronic`) |

**All five now have first-class nodes** (up from 2/5 in Phase 0); CoWoS/ABF/quartz also carry correctly-wired edges (no SiC/GaN false-links).

## New files / generators

- `scripts/build_material_nodes.py` (extended), `scripts/build_dependency_edges.py` (extended), `scripts/apply_registry_phase1.py` (new).
- `data/markets/phase1_chokepoint_nodes.json` (sourced), `data/registries/phase1_registry_patch.json` (additions + aliases).
- Outputs idempotent (byte-identical across `PYTHONHASHSEED`); registry serialized with the file's exact `ensure_ascii=True` serializer (minimal diff).
