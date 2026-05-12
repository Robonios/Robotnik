# v1.1.1 Remediation Log

**Date:** 2026-05-12
**Predecessor:** v1.1 (1,132 rows)
**Result:** v1.1.1 (1,131 rows, 100% in-scope verified)

This log captures every mutation applied between v1.1 and v1.1.1. Total: **1 row drop + extensive in-place edits**, plus schema change (CSV exports drop `total_raised_m` and `total_number_of_raises`).

## Summary

| Mutation class | Count |
|---|---:|
| CSV schema columns dropped | 2 (`total_raised_m`, `total_number_of_raises`) |
| Investor placeholder fixes (Issue 2) | 26 (12 lead + 14 co) |
| Investor name canonicalizations (Issue 3) | 179 mappings → 219 field-level edits |
| Cumulative-funding take edits (Issue 4) | 16 rewrites + 41 strips |
| Weak-take rewrites (Issue 5) | 3 (Anduril, Saronic, ForSight) |
| Bottleneck Critical reclassifications (Issue 6) | 2 (MP Materials, SpaceX) |
| 2025 take backlog rewrites (4 batches) | 172 |
| Transposition / inverse fixes | 4 takes + 3 description rows |
| Duplicate row drop | 1 (Infravision idx 72) |

**Net row delta:** 1,132 → 1,131 (−1 for Infravision dup).
**Final source_status:** 1,056 verified / 75 archived / 0 pending = 100% in-scope verified.

## Schema changes

### CSV export schema (23 columns; was 25 at v1.1)

Dropped from CSV:
- **`total_raised_m`** — computed only from 2023+ coverage; understates companies with pre-2023 history (e.g., ForSight Robotics shows $125M vs actual ~$195M; Lambda shows $480M vs actual ~$863M). Footnote in dataset_notes can't fix the per-row error. Both fields retained in internal `rounds.json` but excluded from CSV.
- **`total_number_of_raises`** — same coverage-bias problem (Cerebras shows 6 raises vs actual ~10).

Cumulative-funding context now moves into `robotnik_take` selectively (only where load-bearing for an analytical point).

### New v1.1.1 CSV column order (23 cols)

```
entity_id, company, company_description, sector, subsector,
value_chain_tier, bottleneck_risk, policy_exposure, round,
deal_type, amount_m, valuation_m, date, date_display,
month_year, quarter, year, location, lead_investors,
co_investors, related_tickers, robotnik_take, source
```

## Issue 2 — Investor placeholder fixes (26 rows)

**Spec:** [`investor_placeholder_fixes.md`](investor_placeholder_fixes.md). New rule (added to monthly ingestion template): never use vague placeholders like "Multiple", "Various", "Existing investors", "Other existing and new investors", "Multiple state-backed investors". Unknown lead → `Undisclosed`; unknown co → empty string.

### lead_investors fixes (12)

| entity_id | date | proposed | resolution path |
|---|---|---|---|
| electralith | 2025-01-16 | Undisclosed | source 404, fall back |
| fairmat | 2025-04-02 | Undisclosed | source 404/403, fall back |
| roboforce | 2025-05-20 | Undisclosed | source explicitly "new and existing investors" |
| albedo | 2025-04-23 | Undisclosed | source paywalled/429 |
| aethero | 2025-06-11 | Kindred Ventures | confirmed via Satellite Today |
| turion-space | 2024-12-02 | Undisclosed | source names VVC investor but not lead |
| infravision | 2025-11-03 | GIC | confirmed via company press release |
| mujin | 2025-12-02 | NTT Group, Qatar Investment Authority | confirmed via Mujin press |
| commcrete | 2025-09-30 | Undisclosed | source 403 |
| constellr | 2026-02-10 | Alpine Space Ventures, Lakestar | confirmed via constellr press |
| hailo | 2024-04-02 | Undisclosed | named participants migrated to co_investors |
| skydio | 2026-04-23 | Undisclosed | parenthetical stripped |

### co_investors fixes (14)

13 reductions to empty string + Runpeng partial retain (`China Resources Microelectronics` kept as named entity) + Hailo enrichment (11 named investors migrated from old lead string: Zisapel family, Gil Agmon, Delek Motors, Alfred Akirov, DCLBA, Vasuki, OurCrowd, Talcar, Comasco, Automotive Equipment, Poalim Equity).

## Issue 3 — Investor name canonicalization (179 mappings)

**Map:** [`investor_name_map.csv`](investor_name_map.csv). **Follow-up doc:** [`investor_canonical_followup.md`](investor_canonical_followup.md) — 151 USER-VERIFY rows (71 HIGH / 23 MEDIUM / 13 LOW / 44 REJECT) deferred for separate review.

Applied in v1.1.1:
- All user-listed high-occurrence canonicalizations (Fidelity family → Fidelity Management & Research; Sequoia → Sequoia Capital; Lightspeed → Lightspeed Venture Partners; Tiger Global → Tiger Global Management; T. Rowe Price; Altimeter Capital; BOND; US Innovative Technology Fund; JPMorgan).
- 34 case/spacing variants (10X → 10x Founders, ARK Invest, BAM Elevate, etc.).
- Eclipse → Eclipse Ventures merge.
- Mayfield / Mayfield Capital → Mayfield Fund merge.
- **Corporate-vs-venture-arm distinctions kept globally** per user policy (AMD ≠ AMD Ventures, Bosch ≠ Bosch Ventures, Qualcomm ≠ Qualcomm Ventures, etc.).

Total: **179 mappings → 219 field-level edits** across `lead_investors` and `co_investors`.

## Issue 4 — Cumulative-funding take audit (57 edits)

**Spec:** [`take_cumulative_funding_audit.md`](take_cumulative_funding_audit.md). 127 cumulative-funding mentions audited.

- **70 KEEP** — figure load-bearing for analytical point (round-extension structure, "best-capitalized" framing, IPO/exit scale signals).
- **41 STRIP** — figure was balance-sheet recitation; clause removed surgically with surrounding punctuation cleaned (new take length range: 52-342 chars, median 169).
- **16 REWRITE** — figure should stay but framing needed v1.1 spec (comp set + view); rewritten range 392-480 chars.

### Stoke Space investigation

User flagged `total_raised_m=$1,220M` but take cited "$480M". **No double-count**: all four rows (Series B Oct-23 $100M, Series C Jan-25 $260M, Series D Oct-25 $510M, Series D extension Feb-26 $350M) are distinct cash events summing to exactly $1,220M. The "$480M" anomaly was **temporal staleness in the Series C take** (correct as of Jan-25 close, not updated as subsequent rounds landed). Same pattern caught in Series B take ("$175M to date"). Both takes rewritten.

## Issue 5 — Three weak-take rewrites

- **Anduril Industries** 2025-06-02 Series G $2.5B at $30.5B post — 464 chars; comp set AVAV / LHX / PLTR / RTX / LMT + Helsing; frame = software-defined defense prime rerating.
- **Saronic** 2025-02-19 Series C $600M at $4.0B post — 480 chars; comp set HII / ASB AU / LDOS / LHX + HavocAI / Anduril Marine private; frame = "CHIPS-of-the-sea" + Port Alpha picks-and-shovels.
- **ForSight Robotics** 2025-06-24 Series B $125M at $500M post — 458 chars; comp set ALC / JNJ / SYK / ISRG / 7731 JP (Nikon Optos); frame = ophthalmic robotics M&A-exit driven, FDA readout resets segment pricing.

## Issue 6 — Bottleneck Critical reclassification

**Spec:** [`bottleneck_critical_audit.md`](bottleneck_critical_audit.md). User direction: keep bar high (sole-source / no alternative). Recommended 2 of 36 High rows → Critical.

- **MP Materials** (idx 96, 2025-07-10) → Critical. Only US integrated NdPr mine-to-magnet operator at scale; USG took preferred equity with 10-yr price floor.
- **SpaceX** (idx 1120, 2026-04-01) → Critical. Sole-source for US crewed orbital launch, ISS heavy cargo, NSSL Phase 3 Lane 2.
- **Rapidus** → stays High (sole-source-prospective doesn't meet the bar; reclassify if/when 2nm volume production materializes).

Post-audit Critical count: **3** (PsiQuantum + MP Materials + SpaceX) of 357 in-scope rounds = 0.8%.

## 2025 take backlog rewrites (172 rows, 4 batches)

The 30-row sample audit found 0% v1.1 pass rate for 2025 takes vs 91.7% for Jan-Apr 2026. All 172 pre-v1.1 takes in 2025 (excluding 17 already-rewritten via Issues 4/5) were redrafted to v1.1 spec.

| Batch | Date range | Rows | Char min / median / mean / max |
|---|---|---:|---|
| 1 | 2025-01-02 to 2025-05-15 | 43 | 426 / 533 / 528 / 580 |
| 2 | 2025-05-15 to 2025-08-18 | 43 | 436 / 553 / 537 / 579 |
| 3 | 2025-08-20 to 2025-11-12 | 42* | 451 / 510 / 509 / 565 |
| 4 | 2025-11-12 to 2025-12-19 | 43 | 486 / 539 / 538 / 572 |

\* Batch 3 = 42 after Infravision dedup (idx 72 dropped — see below).

**Quality:** 0 idx refs, 0 batch refs, 0 self-references in own comp sets, 0 bare CRBR/AZPN/AWE LN across all 172 drafts.

**Review docs:** [`v111_take_backlog_batch1.md`](v111_take_backlog_batch1.md), [`v111_take_backlog_batch2.md`](v111_take_backlog_batch2.md), [`v111_take_backlog_batch3.md`](v111_take_backlog_batch3.md), [`v111_take_backlog_batch4.md`](v111_take_backlog_batch4.md).

## Transposition findings (7 total)

Pattern caught: **content paste errors during v1.0 ingestion (take-wrong) or v1.1 description backfill (description-wrong)**. Rate: 7 / 1,131 rows = 0.62% (below systemic threshold).

**Audits:** [`v111_transposition_audit.md`](v111_transposition_audit.md) (2025 backlog scope, 172 rows) + [`v111_pre2025_transposition_audit.md`](v111_pre2025_transposition_audit.md) (pre-2025 scope, ~942 rows).

### TAKE-WRONG (transposition into take, 5 rows total)

| Entity | Date | Wrong content | Correct content | Source caught | Fix |
|---|---|---|---|---|---|
| `neros` | 2025-11-07 | "AI compute infrastructure ... custom silicon for inference workloads. Competes with Groq, Cerebras, NVIDIA" | "NDAA-compliant FPV combat drones for US Army; LA factory" | Batch 3 agent | Batch 3 redraft |
| `mach` | 2025-12-15 | "aerial defence drone" | "autonomous off-road systems for military applications" (ground autonomy) | Batch 4 agent | Batch 4 redraft |
| `impulse-space` | 2024-10-01 | "Final private round before RISC-V IPO ... SiFive challenger" | In-space transportation (Mira tug + Helios kickstage) | pre-2025 audit | v1.1 redraft applied |
| `hanyang-technology` | 2023-05-12 | "Intelligent service-robot R&D vs Pudu, Keenon" | Yarbo yard-robot OEM (sibling row 2023-03-15 had correct content) | pre-2025 audit | v1.1 redraft applied |

### DESCRIPTION-WRONG (inverse case, 2 rows total)

| Entity | Wrong description | Correct description | Source caught | Fix |
|---|---|---|---|---|
| `xlight` (×2 rows) | "advanced photonic integrated circuit manufacturing capacity ... competes with GlobalFoundries and AIM Photonics" | "Free-electron-laser (FEL) EUV light sources for semiconductor lithography. Spun out of SLAC and Stanford 2022; ASML alternative" | 2025 audit borderline section | description fixed on both rows |
| `ncodin` (×2 rows) | "neuromorphic AI processors for edge computing; competes with Intel Loihi, BrainChip, SynSense" | "Optical interposer technology using nanolasers for chiplet-to-chiplet interconnect; targets AI/HPC packaging bottleneck addressed by Ayar Labs and Lightmatter" | pre-2025 audit | description fixed on both rows + 2025-11-19 take redrafted (Batch 4 take was based on wrong description, propagated error) |

### Pattern observations

- No clustering by sector, date, or source.
- Pre-2025 rate: 3 / 942 = 0.32%.
- 2025 rate: 2 / 172 take-wrong = 1.16%; 2 / 172 desc-wrong = 1.16%.
- Both error types are paste-style errors during agent ingestion passes. Mitigation: monthly ingestion template should add take↔description cross-check as final QA step.

## Infravision duplicate drop

Two rows for the same Series B Nov 3, 2025 $91M led by GIC — different ingestion sources cited (company press release vs BusinessWire), never deduped at v1.0.

| idx | source | co_investors |
|---|---|---|
| 72 | infravisioninc.com | (empty) |
| 145 | businesswire.com | Activate Capital, Hitachi Ventures, Energy Impact Partners |

Kept idx 145 (richer co-investor set), dropped idx 72. **Net row delta: 1,132 → 1,131.**

## Spot-checks / out-of-scope finds

These are quality observations surfaced during v1.1.1 work, **not addressed** in v1.1.1 (logged for v1.1.2 or later):

1. **151 USER-VERIFY canonical-name candidates** ([`investor_canonical_followup.md`](investor_canonical_followup.md)) — corporate-vs-venture-arm rejected per policy; remaining HIGH/MEDIUM/LOW deferred.
2. **ForSight Robotics `total_raised_m=$125M` vs primary-source cumulative ~$195M** — the field is dropped from CSV in v1.1.1 so user-facing impact is removed; internal field still under-counts.
3. **Pre-2025 takes not refreshed to v1.1 spec** — only v1.1.1 transposition fixes touched 2024/2023 rows. Full v1.1 refresh of pre-2025 is a future release.

## Final dataset state

| Metric | Value |
|---|---:|
| Rows | **1,131** |
| `verified` | 1,056 (93.4%) |
| `archived` (out-of-scope per freshness rule) | 75 (6.6%) |
| `pending` | 0 (0.0%) |
| **In-scope verified** | **1,056 / 1,056 = 100.0%** ✅ |
| CSV columns | 23 (was 25 at v1.1) |
| Internal JSON fields | 26 (unchanged; `total_raised_m` and `total_number_of_raises` retained internally) |
| Critical bottleneck rows | 3 |
| schema_version | v1.1.1 |

## Robotics 1Q26 vs 4Q25 ratio (final)

Unchanged from v1.1: 4Q25 = $2,945M (32 deals); 1Q26 = $31,461M (39 deals); ratio = **10.68×**. Published "9× prior quarter" framing remains conservative.

## Files

- [`rounds.json`](rounds.json) — final v1.1.1 dataset (1,131 rows)
- [`dataset_notes.md`](dataset_notes.md) — coverage docs, methodology, v1.1.1 schema
- [`investor_placeholder_fixes.md`](investor_placeholder_fixes.md) — Issue 2 spec
- [`investor_name_map.csv`](investor_name_map.csv) — canonical name map (179 applied)
- [`investor_canonical_followup.md`](investor_canonical_followup.md) — 151 USER-VERIFY deferred
- [`take_cumulative_funding_audit.md`](take_cumulative_funding_audit.md) — Issue 4 spec
- [`take_v1_1_audit.md`](take_v1_1_audit.md) — Issue 5 audit + 3 rewrites
- [`bottleneck_critical_audit.md`](bottleneck_critical_audit.md) — Issue 6 spec
- [`v111_take_backlog_batch1.md`](v111_take_backlog_batch1.md) through [`v111_take_backlog_batch4.md`](v111_take_backlog_batch4.md) — 2025 backlog drafts
- [`v111_transposition_audit.md`](v111_transposition_audit.md) — 2025 transposition findings
- [`v111_pre2025_transposition_audit.md`](v111_pre2025_transposition_audit.md) — pre-2025 transposition findings
- [`v1_0_remediation_log.md`](v1_0_remediation_log.md) — v0.x → v1.0 changes (historical)
- [`v1_0_1_remediation_log.md`](v1_0_1_remediation_log.md) — v1.0 → v1.0.1 changes (historical)
