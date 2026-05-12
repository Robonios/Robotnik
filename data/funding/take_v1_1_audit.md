# Robotnik Funding Dataset — `robotnik_take` v1.1.1 Audit

**Dataset:** `/Users/robertosborne-ov/Projects/Robotnik/data/funding/rounds.json`
**Audit date:** 2026-05-12
**Scope:** v1.1.1 release — three weak-take rewrites (Task A) + 30-row sample audit of 2025-01-01 → 2026-04-30 window (Task B).
**Window total:** 356 rows. Sample: every 11th row (n=30) after sorting by `(date, entity_id)`. Read-only on `rounds.json`.

## v1.1 spec recap

- **Length:** 2–4 sentences; 450–550 char target; 580 hard cap.
- **Density:** comp set with real public-market tickers + strategic frame + articulated view.
- **Voice:** Anduril-style — terse, opinionated, specific. No fragments, no balance-sheet recitation, no batch refs, no idx refs, no self-references in comp sets.
- **Verified ticker rules:** Cerebras = (IPO filed) / was CRBR / currently unlisted; AspenTech = (now part of Emerson, EMR) / was AZPN, taken private; BYD HK = (2533 HK); Horizon Robotics HK = (9660 HK); Alphawave Semi = (delisting in progress, Qualcomm acquisition) / was AWE LN; Globalstar pre-2026-04-14 = (GSAT), post = (delisting in progress, Amazon acquisition).

---

## Section A — Three weak-take rewrites

### A1. Anduril Industries — 2025-06-02, Series G, $2.5B at $30.5B post

**`entity_id`:** `anduril-industries`
**Current take (98 chars):**
> Arsenal-1 autonomous weapons factory; AI-powered defense platforms; largest Founders Fund check ever

**Issue:** three semicolon-separated fragments, no comp set, no strategic frame, no view. Below 450-char floor.

**Proposed rewrite (464 chars):**
> Founders Fund's largest check ever, at $30.5B post, prices Anduril above AeroVironment (AVAV) and within striking range of L3Harris (LHX) — a software-defined defense prime rerating. Comp set: Palantir (PLTR) on the data layer, RTX (RTX) and Lockheed (LMT) as legacy integrators, Helsing private-side. Arsenal-1 bets autonomous-weapons production scales like consumer hardware. The pricing reads as conviction the next DoD budget cycle reshapes prime-vendor share.

- **Comp set used:** AVAV, LHX, PLTR, RTX, LMT (public); Helsing (private).
- **Strategic frame:** $30.5B post vs public prime-vendor caps — Anduril is now mid-tier prime by market value before first major DoD program-of-record runs.
- **View articulated:** Founders Fund's record check is a conviction call on next-cycle prime-vendor share reshape; Arsenal-1 is the production-scaling thesis test.

---

### A2. Saronic — 2025-02-19, Series C, $600M at $4.0B post

**`entity_id`:** `saronic`
**Current take (108 chars):**
> Autonomous surface vessels for US Navy; building Port Alpha shipyard; valuation 4x from prior round

**Issue:** thin, three fragments, no comp set, no articulation of why Port Alpha matters.

**Proposed rewrite (480 chars):**
> Port Alpha is the load-bearing piece — first new US Navy-grade greenfield shipyard in decades positions Saronic as the domestic shipbuilding picks-and-shovels play, not just an ASV vendor. Comp set: Huntington Ingalls (HII) and Austal (ASB AU) on hulls, Leidos (LDOS) and L3Harris (LHX) on integration, HavocAI and Anduril Marine private-side. $4B post is 4x prior round — pricing the unmanned-fleet thesis ahead of Replicator volume contracts and CHIPS-of-the-sea capacity build.

- **Comp set used:** HII, ASB AU, LDOS, LHX (public); HavocAI, Anduril Marine (private).
- **Strategic frame:** Port Alpha repositions Saronic from ASV vendor to domestic-shipbuilding infrastructure — picks-and-shovels exposure to US naval sovereignty cycle.
- **View articulated:** 4x markup prices the unmanned-fleet thesis ahead of DoD Replicator volume contracts and capacity-build subsidies (the "CHIPS-of-the-sea" parallel to semiconductor reshoring).

---

### A3. ForSight Robotics — 2025-06-24, Series B, $125M at $500M post

**`entity_id`:** `forsight-robotics`
**Current take (86 chars):**
> Ophthalmic robotic surgery (ORYOM platform); total funding $195M; FDA trials underway

**Issue:** thin + cumulative funding claim ($195M) without analytical purpose (the row's own `total_raised_m` is $125M, suggesting the $195M figure is inconsistent or stale).

**Proposed rewrite (458 chars):**
> $125M Series B at $500M post pricing the FDA pathway, not the platform. Ophthalmic robotics has no public pure-play — exits route through Alcon (ALC), J&J (JNJ), or Stryker (SYK), with Intuitive Surgical (ISRG) the only standalone surgical-robotics comp. Eclipse Ventures leading after Adani strategic signals US clinical readout is the binary; Optos (parent Nikon, 7731 JP) is the imaging benchmark. Clinical milestones reset M&A pricing across the segment.

- **Comp set used:** ALC, JNJ, SYK, ISRG, 7731 JP (Nikon, Optos parent) — all public.
- **Strategic frame:** ophthalmic surgical robotics is M&A-exit driven; FDA clinical readout is the binary that anchors comp-set valuations across the segment.
- **View articulated:** Eclipse Ventures leading post-Adani strategic is a clinical-readout conviction call, and FDA milestones will reset M&A pricing across Alcon/J&J/Stryker.

---

## Section B — 30-row sample audit

Sample rule: filtered rounds where `2025-01-01 ≤ date ≤ 2026-04-30` (n=356), sorted by `(date, entity_id)`, then every 11th row taken (n=30).

| # | entity_id | Company | Date | Round | Chars | Score | Notes / Recommendation |
|---|---|---|---|---|---|---|---|
| 1 | `kobold-metals` | KoBold Metals | 2025-01-02 | Series C | 187 | **TOO SHORT, FRAGMENT** | Three fragments + investor list. Missing comp set (MP Materials MP, Lynas LYC AU, Freeport FCX, Rio Tinto RIO; private peers like Earth AI). No view on AI-driven exploration vs traditional juniors. Rewrite. |
| 2 | `arkedge-space` | ArkEdge Space | 2025-02-04 | Series B | 86 | **TOO SHORT, MISSING COMP SET, MISSING VIEW** | One-line descriptor. Missing comp set (Planet PL, BlackSky BKSY, Spire SPIR; private Synspective, iQPS as Japan-domestic peers). Highest-priority rewrite. |
| 3 | `puzhao-materials` | Puzhao Materials | 2025-02-20 | Series B | 59 | **TOO SHORT, FRAGMENT, MISSING COMP SET** | Two fragments. Missing comp set (Photronics PLAB, Toppan 7911 JP, DNP 7912 JP, HOYA 7741 JP). China-domestic photomask thesis is high-density — critical rewrite. |
| 4 | `cmr-surgical` | CMR Surgical | 2025-04-02 | Undisclosed | 77 | **TOO SHORT, BALANCE SHEET RECITATION, MISSING COMP SET** | Cumulative $1.4B without analytical purpose. Missing comp set (ISRG, Medtronic MDT, Stryker SYK; private Vicarious, Distalmotion, Asensus ASXC). Rewrite. |
| 5 | `quantum-systems` | Quantum Systems | 2025-05-06 | Series C | 154 | **TOO SHORT, FRAGMENT, OTHER (batch ref)** | Four fragments + forbidden batch ref ("also has Nov-25 Series C extension"). Missing comp set (AVAV, Kratos KTOS, Elbit ESLT; private Helsing, Tekever). Rewrite, drop batch ref. |
| 6 | `impulse-space` | Impulse Space | 2025-06-03 | Series C | 90 | **TOO SHORT, BALANCE SHEET RECITATION, FRAGMENT** | Three fragments + cumulative $525M. Missing comp set (Rocket Lab RKLB, Astroscale 186A JP; private D-Orbit, Momentus MNTS). Rewrite. |
| 7 | `torngat-metals` | Torngat Metals | 2025-06-17 | Debt Financing | 382 | **TOO SHORT** | Below 450 floor but otherwise solid — has Lynas (LYC AU) comp, REE sovereignty frame. Modest expansion would pass. Lowest-effort fix in the sample. |
| 8 | `galaxea-ai` | Galaxea AI | 2025-07-09 | Series A | 144 | **FRAGMENT, BALANCE SHEET RECITATION, OTHER (batch ref)** | Three fragments + cumulative $210M + explicit batch ref ("Galaxea also has a Feb-26 Series B entry"). Comp set hinted in description (Galbot, Unitree, Agibot) but absent from take. Rewrite, drop batch ref. |
| 9 | `qant` | Q.ANT | 2025-07-17 | Series A | 115 | **TOO SHORT, FRAGMENT, MISSING COMP SET** | Four fragments. Missing comp set (private Lightmatter, Ayar Labs; benchmark vs NVDA digital, MRVL on optical-interconnect). No strategic frame on photonic-compute thesis. Rewrite. |
| 10 | `spinlaunch` | SpinLaunch | 2025-08-18 | Series C | 111 | **TOO SHORT, BALANCE SHEET RECITATION, FRAGMENT** | Pivot from kinetic launch to constellation operator is the story; take doesn't articulate it. Missing comp set (Eutelsat ETL FP, Iridium IRDM, AST SpaceMobile ASTS; SpaceX/Starlink private). Rewrite. |
| 11 | `scintil-photonics` | Scintil Photonics | 2025-09-09 | Series B | 184 | **TOO SHORT, MISSING COMP SET, MISSING VIEW** | Reads as descriptor only. Missing comp set (Coherent COHR, Lumentum LITE, MACOM MTSI; private Ayar Labs, Avicena). No view on CPO supply chain. Rewrite. |
| 12 | `cerebras-systems` | Cerebras Systems | 2025-09-30 | Series G | 122 | **TOO SHORT, FRAGMENT, OTHER (batch ref)** | Fragments + batch ref ("also has Feb-26 Series H entry"). Ticker note: per verified rules, Cerebras itself should never appear as a ticker — use "(IPO filed)" form when referenced. Missing comp set (NVDA, AMD; private Groq, SambaNova, Tenstorrent). Rewrite. |
| 13 | `starship-technologies` | Starship Technologies | 2025-10-15 | Series C | 293 | **TOO SHORT** | Has comp (AMZN Scout, Serve Robotics SERV) and view. ~160 chars below floor; closest-to-PASS with expansion (add Uber UBER, DoorDash DASH on the demand side, Nuro private as adjacent). |
| 14 | `sunflower-labs` | Sunflower Labs | 2025-11-04 | Series B | 282 | **TOO SHORT** | Sequoia signal articulated, comp (Ring/AMZN) + view present. ~170 chars below floor. Close-to-PASS — expand on prosumer-vs-municipal use-case bifurcation. |
| 15 | `powerlattice` | PowerLattice | 2025-11-17 | Series A | 181 | **TOO SHORT, MISSING COMP SET, MISSING VIEW** | Technical descriptor only. Missing comp set (Vicor VICR, Monolithic Power MPWR, Empower private; Enpirion is now Altera under INTC). No strategic frame on chiplet power-delivery thesis. Rewrite. |
| 16 | `tutor-intelligence` | Tutor Intelligence | 2025-12-01 | Series A | 330 | **TOO SHORT** | USV signal articulated, comp (Covariant, Dexterity) + view present. ~120 chars below floor. Close-to-PASS — expand on demonstration-learning vs sim-to-real bifurcation. |
| 17 | `iceye` | ICEYE | 2025-12-05 | Series E | 175 | **TOO SHORT, MISSING COMP SET, MISSING VIEW** | Descriptor + investor list. Missing comp set (Planet PL, BlackSky BKSY, Spire SPIR; private Capella, Umbra). No view on SAR vs optical defense demand cycle. Rewrite. |
| 18 | `moore-threads` | Moore Threads | 2025-12-18 | IPO | 385 | **TOO SHORT** | Has NVDA/AMD comp and view (China semi self-sufficiency). ~65 chars below floor — closest-to-PASS in the sample. Expand on STAR Market multiple vs HK comparables (e.g., Horizon Robotics 9660 HK). |
| 19 | `spinq-technology` | SpinQ Technology | 2026-01-21 | Series C | 538 | **PASS** | In range. Comp set (688027, IBM, IONQ, RGTI). Strategic frame (15th Five-Year Plan parallel to power-semis Big Fund). Articulated view. Model row. |
| 20 | `waymo` | Waymo | 2026-02-02 | Series D | 420 | **TOO SHORT** | Below 450 floor by 30 chars. Strong comp (TSLA, PONY, Wayve/Waabi) and view (crossover syndicate as IPO conditioning). Add a sentence on operating-city economics; passes. |
| 21 | `axiom-space` | Axiom Space | 2026-02-12 | Debt Financing | 461 | **PASS** | In range. Strategic frame (debt-cost premium vs Vast/Sierra mark-down avoidance). Sovereign-capital read (QIA optionality). Binary call on CLD Phase 2. Comp set is light on tickers but acceptable given commercial-station segment has no public pure-play. |
| 22 | `spirit-ai` | Spirit AI | 2026-02-24 | Series A | 529 | **PASS** | In range. Comp set (Unitree, Galbot, XPEV robotics, Agibot). Strategic frame (China deployment-capital phase vs US foundation phase). View on valuation richness vs procurement pull-through. Model row. |
| 23 | `pld-space` | PLD Space | 2026-03-04 | Series C | 501 | **PASS** | In range. Comp set (RKLB on small-lift; ArianeGroup, Avio state-aligned). Strategic frame (Asian customer pull via Mitsubishi anchor; sovereignty + strategic hybrid). Explicit bottleneck call (MIURA 5 maiden flight). |
| 24 | `sunday` | Sunday | 2026-03-12 | Series B | 523 | **PASS** | In range. Comp set (1X, The Bot Company, Figure). Strategic frame (consumer-vs-industrial humanoid bifurcation). Articulated view on Coutue solo-leading at $1.15B as unusual sizing. Model row. |
| 25 | `zipline` | Zipline | 2026-03-23 | Series H (extension) | 509 | **PASS** | In range. Comp set framed (no public pure-play; Wing under GOOGL, Matternet private). Strategic frame (Paradigm crossover as IPO-prep tell). US suburban-economics test articulated. |
| 26 | `physical-intelligence` | Physical Intelligence | 2026-03-27 | Series C | 479 | **PASS** | In range. Comp set (Skild AI, Rhoda AI, TSLA Optimus, Google DeepMind RT-X). Strategic frame (brain-vs-body capital split, now decisively brain-heavy). Valuation-pricing view. Model row. |
| 27 | `spinq-technology` | SpinQ Technology | 2026-04-03 | Series C (extension) | 543 | **PASS** | In range. Comp set (688027, IBM, IONQ, RGTI). Strategic frame (Big Fund parallel for quantum). Tempo-of-follow-on as primary signal. Articulated view on SpinQ as best-capitalized Chinese superconducting pure-play. Strong. |
| 28 | `pixel-photonics` | Pixel Photonics | 2026-04-10 | Seed | 541 | **PASS** | In range. Comp set (Single Quantum, ID Quantique, Quantum Opus; KEYS on T&M, KLAC as picks-and-shovels analogue). Strategic frame (modality-agnostic SNSPD play). View on EU Chips Act non-dilutive grant as cost-of-capital lever. |
| 29 | `general-robotics` | General Robotics | 2026-04-15 | Strategic | 524 | **PASS** | In range. Comp set (Formant, Freedom Robotics, InOrbit, Cogniteam; NVDA as Isaac Sim platform). Strategic frame (channel-not-capital play, Accenture SI rolodex load-bearing). Explicit call on strategic-not-financial. Model row. |
| 30 | `orbital-chenguang-beijing-orbital-twilight` | Orbital Chenguang (Beijing Orbital Twilight) | 2026-04-20 | Pre-Series A | 512 | **PASS** | In range. Comp set (Sophia Space, Lonestar, Lumen Orbit, Starcloud; EQIX as terrestrial counter). Strategic frame (sovereign-scale industrial policy as AI-compute counter to Starlink). Articulated geopolitical risk (export controls). Model row. |

---

## Section C — Summary

### Pass rate

- **PASS:** 11 / 30 = **36.7%**
- **FAIL:** 19 / 30 = 63.3%

### Pass-rate by half-period

- **2025-01-01 → 2025-12-31 (rows 1–18):** 0 PASS / 18 = **0.0%**
- **2026-01-01 → 2026-04-30 (rows 19–30):** 11 PASS / 12 = **91.7%**

The 1.1 spec is clearly being applied to Jan-Apr 2026 entries (per the v1.1 refresh in commit `0a7828e`), but pre-2026 entries still carry pre-spec drafts. **The audit identifies that v1.1 quality is a cliff at the 2026-01-01 boundary, not a gradient.**

### Common failure modes (by frequency, fail rows only)

| Rank | Failure mode | Count | Share of fails |
|---|---|---|---|
| 1 | **TOO SHORT** (<450 chars) | 18 | 94.7% |
| 2 | **FRAGMENT** (semicolon-separated, no analytical view) | 8 | 42.1% |
| 3 | **MISSING COMP SET** (no public-market tickers cited) | 7 | 36.8% |
| 4 | **MISSING VIEW** (descriptor only, no analytical frame) | 4 | 21.1% |
| 5 | **BALANCE SHEET RECITATION** (cumulative funding without purpose) | 4 | 21.1% |
| 6 | **OTHER — batch references** ("also has X entry", "Note: …") | 3 | 15.8% |

No INVALID TICKER violations were found in the sample (Cerebras row 12 doesn't currently use the ticker, but a rewrite must follow the (IPO filed) rule).

### Recommendations for broader cleanup

1. **Prioritize the pre-2026 half of the dataset.** All 18 sampled rows in 2025 are below v1.1 spec. Project the failure rate to the full window: of 189 rows in 2025, expect ≈170–185 to need rewrites. Of 167 rows in Jan-Apr 2026, expect ≈15 to need rewrites — predominantly TOO SHORT / close-to-PASS.

2. **Tackle TOO-SHORT-but-close rows first.** Rows 7 (Torngat), 13 (Starship), 14 (Sunflower), 16 (Tutor), 18 (Moore Threads), 20 (Waymo) already have comp sets and a view; they're 30–170 chars below the 450 floor. These are low-effort fixes — expand existing analytical content rather than starting from scratch.

3. **Eliminate all batch references in pre-2026 takes.** Rows 5 (Quantum Systems), 8 (Galaxea AI), 12 (Cerebras Systems) explicitly violate the no-batch-ref rule. Grep for `\bNote:\s+(also|Galaxea|Cerebras)\b` and similar `also has` patterns across the window for a full sweep.

4. **Drop cumulative-funding line items unless analytically purposeful.** Rows 4 (CMR Surgical $1.4B), 6 (Impulse $525M), 8 (Galaxea $210M), 10 (SpinLaunch $203M) recite `total_raised_m` without a comp-set or pricing argument. Cumulative numbers are already captured in the `total_raised_m` field; only repeat in the take when the cumulative ratio drives a thesis (e.g., burn-rate vs revenue traction).

5. **Standardize ticker style for the verified set.** Cerebras, AspenTech, BYD HK, Horizon Robotics HK, Alphawave Semi, and Globalstar each have specific required forms (see spec recap). Worth one global grep before the v1.1.1 cut to catch any pre-2026 takes that may carry stale tickers (e.g., bare `AZPN`, `CRBR`, or `AWE LN` references).

6. **Use rows 22 (Spirit AI), 24 (Sunday), 26 (Physical Intelligence), 29 (General Robotics), 30 (Orbital Chenguang) as voice exemplars.** They each carry a strategic frame ("X is the load-bearing piece", "X is the tell"), a comp set with mixed public + private tickers, and an articulated view on what the round signals about the broader market structure. Train the next batch of rewrites against these.

### Process note

`total_raised_m` for ForSight Robotics is recorded as $125M in the row, but the current take cites "$195M total funding." Worth checking whether the take figure is stale or the field is undercounted before the v1.1.1 cut (out of scope for this audit — read-only on `rounds.json`).
