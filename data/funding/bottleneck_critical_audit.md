# Bottleneck Risk — Critical Reclassification Audit

**Date:** 2026-05-12
**Scope:** Funding dataset `data/funding/rounds.json` (v1.1), in-scope window Jan 2025 – Apr 2026
**Total in-scope rounds:** 356
**Reviewed:** 36 rounds rated `High` + 1 rated `Critical` (baseline)
**Output:** Audit only — no mutations applied to `rounds.json`

---

## Critical baseline — reference point

The single existing `Critical` entry sets the bar:

| Entity | Round | Date | Rationale for Critical |
|---|---|---|---|
| **PsiQuantum** (`psiquantum`, Semiconductors / Fabless Design) | Series E, $1,000M | 2025-09-10 | Photonic fault-tolerant quantum hardware is pre-commercial and has effectively no peer at the million-qubit scale. The supply chain choke is the cryogenic dilution-refrigeration stack itself — Bluefors-class systems plus PsiQuantum's in-house Daresbury facility represent the only path-to-scale infrastructure. No near-term substitute exists, and downstream industry capability (utility-scale fault-tolerant QC) is gated on this stack. |

**Bar interpretation:** `Critical` = sole-source or near-single-source for a capability that, if disrupted, materially halts or sets back an industry segment, with no near-term substitute. The bar is intentionally narrow.

---

## Recommended for reclassification to `Critical`

| # | Entity ID | Company | Sector / Subsector | Current | Proposed | Rationale |
|---|---|---|---|---|---|---|
| 1 | `MP` | **MP Materials** | Materials / Rare Earths & Critical Minerals | High | **Critical** | Only operating integrated US rare-earth mine (Mountain Pass) **and** the only US NdPr-to-finished-magnet operator at scale via the 10X facility. The US government took a $400M preferred stake plus $150M loan with a 10-year NdPr price floor — an unambiguous sole-source designation. No near-term Western alternative exists for primary NdPr separation outside China at MP's scale; Phoenix Tailings/Vulcan Elements/Cyclic Materials are at <10% of MP's effective capacity and remain pre-scale. |
| 2 | `spacex` | **SpaceX** | Space / Launch | High | **Critical** | Functionally sole-source for US crewed orbital launch (Boeing Starliner remains unreliable), for ISS resupply heavy cargo, and for NSSL Phase 3 Lane 2 heavy-lift class. For LEO megaconstellation bandwidth at consumer scale (Starlink), no comparable operator exists or will exist inside the audit horizon. Disruption to SpaceX launch cadence would halt US human spaceflight and degrade DoD orbital replenishment — the textbook industry-capability choke point. Rocket Lab/ULA/Blue Origin exist but cannot substitute at the relevant payload/cadence tier. |
| 3 | `rapidus` | **Rapidus** (consolidated — applies to both 2026-02-27 and 2026-04-11 government investment rows) | Semiconductors / Foundry | High | **Critical** | The sole-source case here is geographic, not technical: Rapidus is the **only** non-TSMC, non-Samsung, non-Intel-Foundry path to 2nm-class production for a sovereignty-sensitive customer base (Fujitsu, NTT, SoftBank, Sony, plus the DBJ-anchored 32-company industrial consortium). If the goal is Japanese-sovereign access to leading-edge logic, there is no alternative — the entire Japanese semiconductor industrial policy is funnelled through this single fab. Note: this is the most contestable Critical of the three; the conservative read is that 2nm output isn't yet flowing, so the "sole-source" status is prospective. **Surfacing as judgment call below.** |

**Recommended Critical count: 2 high-confidence (MP Materials, SpaceX) + 1 judgment call (Rapidus).**

If the audit must hold strictly to *currently delivering* sole-source status, drop Rapidus and stay at 2. If the field is intended to capture *structurally locked-in* choke points including those still ramping, include Rapidus and stay at 3.

---

## Considered but rejected — staying as `High`

These were evaluated against the Critical bar and held back:

### Semiconductors / Compute
- **Etched.ai** — TSMC 4nm customer, but Etched itself is a transformer-ASIC architectural bet with peer alternatives (Groq, Cerebras, Tenstorrent). Not sole-source.
- **Groq, Cerebras (Series G, Series H, IPO filing), SiFive, Rebellions** — all have direct competitors (NVIDIA, AMD, ARM, Tenstorrent). Strategic but not sole-source.
- **Celestial AI, Ayar Labs, DustPhotonics, Polariton** — silicon photonics / CPO. Multiple players (Ayar, Lightmatter, Coherent, Lumentum, Marvell, Broadcom). Bottleneck-adjacent but not single-source.
- **Lace Lithography** — *challenger* to ASML's EUV monopoly, not itself a choke point. Pre-commercial 2029 pilot. ASML would be the Critical entity, but ASML has no funding round in the window.

### Materials / Rare Earths
- **Phoenix Tailings, Cyclic Materials (both rounds), Vulcan Elements** — all part of the Western REE rebuild thesis, but each has at least 1–2 direct peers (Noveon Magnetics, Energy Fuels, USA Rare Earth, Lynas) and none has the integrated mine-to-magnet scale of MP. The category-level choke is real; the individual-company sole-source status is not.
- **Redwood Materials** — battery recycling has multiple Western and Asian alternatives (Li-Cycle, Ascend Elements, Umicore, BASF). Not sole-source.
- **KoBold Metals** — AI-driven exploration. Pre-production at flagship Mingomba; not yet a choke point.

### Space
- **Stoke Space (Series C, Series D, extension), Firefly Aerospace, Sierra Space** — emerging launch / in-orbit services. All are *challengers* to incumbents (SpaceX, ULA, Northrop). None is sole-source itself.

### Robotics
- **NEURA (both rounds), Apptronik (both rounds), Galbot, Unitree, Helsing, Shield AI (both rounds)** — humanoid and defense-AI system integrators. The humanoid category has 8+ funded competitors; defense AI has Anduril/Palantir/Kratos. None is sole-source; all sit in competitive segments where customer switching cost is high but supply substitution exists.

---

## Sector distribution of recommendations

| Sector | Critical recommended |
|---|---|
| Materials / Rare Earths & Critical Minerals | 1 (MP Materials) |
| Space / Launch | 1 (SpaceX) |
| Semiconductors / Foundry | 1 (Rapidus — judgment call) |

The PsiQuantum baseline (Semiconductors / Fabless Design) is unchanged.

**Post-audit projected `Critical` count (if all 3 recommendations adopted): 4 of 356 in-scope rounds (~1.1%). With only the 2 high-confidence recommendations: 3 of 356 (~0.8%).** Both are well within the "narrow signal" target — the field continues to surface only true single-source/choke-point exposures, with the rest of the supply-chain risk distribution carried by the `High` tier.

---

## Note on entities outside the funding-round dataset

The most canonical choke points named in the brief (TSMC leading-edge nodes, ASML EUV, Unimicron/Ibiden/Nan Ya advanced ABF substrates) **do not appear as funding rounds** in the Jan 2025 – Apr 2026 window, so they cannot be reclassified through this audit. If the platform needs to surface those entities' choke-point status, that signal will have to come from a non-funding-round data source (e.g., a separate supply-chain ledger or the equities/index dataset).
