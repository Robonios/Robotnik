# Funding Dataset — Documentation Notes

**v1.1.2 (2026-05-13)**

This document captures the schema, methodology, known limitations, and acceptance criteria for downstream consumers (VCs, analysts).

## Schema (v1.1.2 — 23 columns in CSV export, unchanged from v1.1.1)

CSV export column order:

```
entity_id, company, company_description, sector, subsector,
value_chain_tier, bottleneck_risk, policy_exposure, round,
deal_type, amount_m, valuation_m, date, date_display,
month_year, quarter, year, location, lead_investors,
co_investors, related_tickers, robotnik_take, source
```

23 columns. The internal JSON (`rounds.json`) retains additional fields not exported to CSV:
- `source_status` (verified | archived | pending) — audit field
- `total_raised_m` and `total_number_of_raises` — computed values; dropped from CSV at v1.1.1 because they compute only from 2023+ coverage and understate companies with pre-2023 funding history (e.g., ForSight Robotics shows $125M vs actual ~$195M; Lambda shows $480M vs actual ~$863M). Selective cumulative-funding context now moves into `robotnik_take` where load-bearing for the analytical point.

### New fields in v1.1

| Field | Type | Definition |
|-------|------|------------|
| `company_description` | str \| null | 1-3 sentence factual description of what the company makes/does, who it's for, technical approach if distinctive. No strategic framing. No investor info. Plain prose. |
| `value_chain_tier` | str \| null | One of 8 tiers; describes where the company creates value in the frontier-tech stack. Backfilled for Jan 2025 → Apr 2026 only; older rows leave empty. |
| `bottleneck_risk` | str \| null | Five-value risk score on the company's supply-chain position. Backfilled for Jan 2025 → Apr 2026 only. |
| `policy_exposure` | str \| null | Semicolon-separated tags from a controlled vocabulary identifying the policy regimes the deal is exposed to. Backfilled across full dataset. |
| `total_number_of_raises` | int | (Internal-only at v1.1.1) Count of rounds matching the same `entity_id`. Dropped from CSV export at v1.1.1 due to coverage bias. |

### Renamed fields in v1.1

| Old name | New name | Display name |
|----------|----------|--------------|
| `other_investors` | `co_investors` | Co-Investors |
| `robotnik_notes` | `robotnik_take` | Robotnik's Take |

### Removed fields in v1.1

| Field | Reason |
|-------|--------|
| `public_market_link` | Dormant — only 2/1,133 populated at v1.0.1. No analytical use. |
| `source_status` (from CSV) | Internal audit field; retained in JSON, dropped from export |

### Removed fields in v1.1.1 (CSV export only — retained internally)

| Field | Reason |
|-------|--------|
| `total_raised_m` | Computes only from 2023+ coverage; under-counts companies with pre-2023 history. Selective cumulative context moves into `robotnik_take` where load-bearing. |
| `total_number_of_raises` | Same coverage-bias issue (e.g., Cerebras shows 6 raises vs actual ~10). |

### `company_description` vs `robotnik_take` distinction

- **`company_description`** answers: *What does the company make/do? Who is it for? What's distinctive?*
  - Factual, plain prose, 1-3 sentences
  - No strategic frame, no comp set, no thesis fit
  - No investor info
  - Readable in isolation
- **`robotnik_take`** answers: *Why does this round matter? Where does the company sit competitively? What's the read-through?*
  - Analytical commentary, 2-4 sentences typically
  - Includes comp set with real tickers/companies
  - Has a view — not hedged
  - Assumes sector-aware reader

## Controlled vocabularies

### `policy_exposure` (semicolon-separated tags allowed)

```
US_CHIPS_Act
US_Export_Controls_China
US_Critical_Minerals_List
US_DOE_LPO_Eligible
US_DPA_Title_III
EU_Chips_Act
EU_CRMA              (Critical Raw Materials Act)
EU_NZIA              (Net-Zero Industry Act)
UK_NSI_Act           (National Security and Investment Act)
Japan_METI_Semi_Strategy
South_Korea_K-CHIPS_Act
China_Big_Fund
China_Made_In_China_2025
None                 (no material policy exposure)
```

New regimes added only with explicit user approval — silent enum drift is banned.

### `value_chain_tier` (one value per row)

```
Upstream Materials               — raw materials extraction, refining, substrates
IP & Design                      — chip designers, EDA tooling, foundation models
Capital Equipment                — fab tools (lithography, etch, deposition, metrology)
Fabrication & Manufacturing      — foundries, OSAT, contract manufacturing
Components & Subsystems          — sensors, actuators, modules, terminals
System Integration               — full vehicles, robots, satellites, weapons systems
Deployment & Operation           — launch services, satellite operators, ride-hail
Software & Services              — AI cloud, robotics middleware, DePIN networks
```

Backfilled for Jan 2025 → Apr 2026 only.

### `bottleneck_risk` (one value per row)

```
Critical          — sole-source, no alternative
High              — limited alternatives, system-wide impact if disrupted
Medium            — alternatives exist but switching costly
Low               — competitive market, multiple suppliers
Pre-commercial    — early-stage company not yet in supply chain
```

When in doubt for a private company, default to `Pre-commercial` rather than guessing. Backfilled for Jan 2025 → Apr 2026 only.

### Calibration examples
- ASML EUV → `Critical`
- TSMC leading-edge → `Critical`
- NdFeB magnet manufacturers → `High`
- Series A humanoid robotics startup pre-product → `Pre-commercial`
- US lithium refiner with 3 competitors → `Medium`

## Backfill scope notes

| Field | Scope |
|-------|-------|
| `policy_exposure` | Full dataset (Jan 2023 → Apr 2026) |
| `value_chain_tier` | Jan 2025 → Apr 2026 only |
| `bottleneck_risk` | Jan 2025 → Apr 2026 only |
| `company_description` | Full dataset; 6 entities null (see below) |
| `robotnik_take` | Full dataset; v1.1 refreshed Jan-Apr 2026; v1.1.1 refreshed all of calendar 2025 (172 rows in 4 batches); pre-2025 rows carry pre-v1.1 content except 2 transposition fixes (Impulse Space 2024-10, Hanyang Tech 2023-05) |
| `total_raised_m` / `total_number_of_raises` | Computed internally; dropped from CSV at v1.1.1 |

## Filename convention (v1.1+)

Monthly CSV exports use the pattern:

```
data/exports/Robotnik Frontier Private Rounds <Month-YYYY>.csv
```

Where `<Month-YYYY>` reflects the latest month of data in the export (e.g., `April-2026`, `May-2026`).

Prior monthly exports are archived in `data/exports/archive/` for diffing. The unversioned `robotnik_private_rounds_v1_0_1.csv` is preserved as the v1.0.1 snapshot.

## Coverage window

- **Earliest dated row:** 2023-01-02
- **Latest dated row:** 2026-04-30
- **Total rows:** 1,243 (v1.1.2: +112 pre-seed/seed sweep additions; v1.1.1: −1 Infravision duplicate; v1.1: −1 Humans& as out-of-universe consumer software)

### Pre-seed / seed coverage (added v1.1.2)

| Round type | Jan 2025 – Apr 2026 | Notes |
|---|---:|---|
| Pre-Seed (+ extensions) | 37 | Added via dedicated sweep at v1.1.2 |
| Seed (+ Seed II, Seed+, extensions) | 131 | Same sweep |

Sweep methodology: 4 parallel sector agents (Robotics, Semis, Space, Materials+Token) with broadened source mix (accelerators, university tech-transfer, VC firm portfolio pages). Sweep-specific threshold override: $500K pre-seed / $1M seed (vs standard monthly $5M robotics / $3M space). See [`preseed_seed_sweep_summary.md`](preseed_seed_sweep_summary.md) and [`v1_1_2_remediation_log.md`](v1_1_2_remediation_log.md).

## Known limitation 1: sub-$25M long-tail rounds in 3Q25–4Q25

**24 rows** in 3Q25 (n=4) and 4Q25 (n=20) where `amount_m < 25` were flagged as `unverifiable` by the v1.0.1 bulk data audit. These are mostly small early-stage rounds across mixed geographies (USA n=8, France n=3, Belgium n=2, Switzerland n=2, plus singles from Norway, Germany, Israel, Italy, South Korea, India, UAE, UK).

The pattern is **aggregator-only sourcing** — primary press (TechCrunch, Reuters, etc.) typically don't cover sub-$25M rounds outside flagship cases. Sources like Pulse 2, EU-Startups, FinSMEs, RoboticsTomorrow are the surface, but the bulk audit couldn't independently verify against company-direct primary sources within timing.

**Acceptance:** Per user decision (2026-05-06), these rows are accepted as-is.

## Known limitation 2: company_description nulls (6 entities)

Six entities in v1.1 have `company_description: null` and acceptance from the user that this is the right call:

| Entity | Date | $M | Reason |
|--------|------|---:|--------|
| True Health | 2023-11-15 | $14.1 | Chinese surgical robotics; single-source tracker mention, no investor/product specifics |
| Blue Ocean Robot | 2023-09-15 | $13.7 | Chinese surgical robotics; same pattern |
| Ruizhu Technology | 2023-10-15 | $13.7 | Chinese sensors; thin reporting |
| Clodot | 2023-12-15 | $8.5 | Korean social-robot maker; limited English-source detail |
| Strata Robotics | 2026-04-15 | $5.2 | Single-source Substack roundup — same fabrication pattern remediated at v1.0.1; null per anti-fabrication policy |
| DOE CMEI Program | 2026-03-13 | $500 | Government program, not a single operating company; recipients vary |

**Policy:** Better an empty cell than a hedged sentence we can't defend. Same anti-fabrication logic as the URL ruleset.

**Exception for `robotnik_take`:** Government-program rows (e.g., DOE CMEI Program) can carry `robotnik_take` content even when `company_description` is null. The take is about the policy event, not about an operating company. This is explicitly acceptable.

## Out-of-universe exclusions tightened in v1.1

In addition to the v1.0 exclusion categories (see below), v1.1 drops:

- **Humans&** ($480M seed Jan 2026) — "AI version of IM," pure consumer/social software, not embodied AI or robotics infrastructure. Inclusion at v1.0.1 reflected investor overlap with the embodied-AI capital pool but didn't fit the hardware-anchored thesis. Same logic as the v1.0.1 crypto-software exclusions (RISC Zero, Flashbots, BitGo, EigenLayer, Friend.tech, ZetaChain).

## Duplicate-row drop at v1.1.1

- **Infravision** Series B 2025-11-03 $91M (GIC-led) — two rows ingested at v1.0 from different sources (company press release + BusinessWire), never deduped. Kept the richer record (BusinessWire source with co-investors named: Activate Capital, Hitachi Ventures, Energy Impact Partners), dropped the bare press-release row.

## Transposition findings + remediation (v1.1.1)

Two pattern types caught during v1.1.1 work — both are paste-style errors during prior ingestion passes:

**TAKE-WRONG (transposition into `robotnik_take`, 5 rows fixed):**
- `neros` 2025-11-07 — take described AI compute infrastructure / Groq + Cerebras + NVDA; company actually makes NDAA-compliant FPV combat drones (caught by Batch 3 agent, fixed in v1.1.1)
- `mach` 2025-12-15 — take described aerial defence drone; company actually does autonomous off-road systems for military (caught by Batch 4 agent)
- `impulse-space` 2024-10-01 — take described RISC-V / SiFive IPO; company is in-space transportation (caught by pre-2025 audit)
- `hanyang-technology` 2023-05-12 — take described generic service-robot R&D vs Pudu/Keenon; company is Yarbo yard-robot OEM (caught by pre-2025 audit; sibling row 2023-03-15 had correct content)

**DESC-WRONG (transposition into `company_description`, 2 entities fixed across rows):**
- `xlight` (×2 rows) — description said "photonic IC manufacturing competing with GlobalFoundries / AIM Photonics"; actually builds FEL EUV light sources for semiconductor lithography (ASML alternative); fixed
- `ncodin` (×2 rows) — description said "neuromorphic AI processors vs Intel Loihi"; actually builds optical interposer + nanolasers for chiplet interconnect; fixed (the Batch 4 take for the 2025-11-19 row had also propagated the wrong content and was redrafted)

**Audits:** [`v111_transposition_audit.md`](v111_transposition_audit.md) (2025 backlog scope, 172 rows; 2 take-wrong + 1 desc-wrong found) and [`v111_pre2025_transposition_audit.md`](v111_pre2025_transposition_audit.md) (pre-2025 scope, ~942 rows; 2 take-wrong + 1 desc-wrong found). Total rate: 7 / 1,131 = 0.62%. No clustering by sector, source, or date. Mitigation in monthly ingestion template: add take↔description cross-check as final QA step.

## Investor canonicalization (v1.1.1)

- **Applied:** 179 mappings, 219 field-level edits across `lead_investors` and `co_investors`. See [`investor_name_map.csv`](investor_name_map.csv).
- **Policy:** corporate vs venture-arm kept distinct globally (AMD ≠ AMD Ventures, Bosch ≠ Bosch Ventures, etc.).
- **Deferred:** 151 USER-VERIFY candidates split HIGH (71) / MEDIUM (23) / LOW (13) / REJECT (44) — see [`investor_canonical_followup.md`](investor_canonical_followup.md). Will be reviewed in a separate pass.
- **Placeholder rule (added to monthly ingestion template):** unknown lead → `Undisclosed`; unknown co → empty string. Never use "Multiple", "Various", "Existing investors", "Other existing and new investors", etc.

## Source URL audit summary

| Status | Count | % |
|--------|------:|---:|
| `verified` — URL confirmed live or paywall-citable | 1,153 | 92.8% |
| `archived` — out-of-scope per freshness rule (date >365d AND amount <$500M) | 75 | 6.0% |
| `pending` — awaiting spot-check approval | 15 | 1.2% |
| **Total** | **1,243** | **100%** |

The 15 `pending` rows are from the v1.1.2 pre-seed/seed sweep — primarily eu-startups.com and uktechnews.info 403s during WebFetch verification. Content was cross-verified via secondary sources but the cited primary URL remained un-fetchable. To be re-checked next monthly cycle.

## URL freshness rule (in scope vs out of scope)

A row's `source` URL must be valid (returns 200/301/302) if either:
- `date` falls within the last 365 days from current date, OR
- `amount_m >= 500` (i.e., ≥ $500M, regardless of age)

Out-of-scope rows can have dead URLs and are marked `source_status: archived`. They remain in the dataset because the deal is verified; only the citation is stale.

## Anti-fabrication rules (locked at v1.0.1)

Every URL in the dataset must:
1. Be HEAD-requested and confirmed to return 200/301/302 before being recorded
2. Prefer canonical company press release pages > trade publications > aggregators
3. Be **verbatim** from search results — never constructed from URL patterns
4. Use `source_status: pending` instead of fabricating a URL

Date / currency / round-naming rules added at v1.0.1:
5. **Date verification:** match canonical announcement date stated in cited source — no synthesis from URL slugs or secondary references
6. **Currency capture:** every non-USD raise records native currency, amount, FX rate, and FX source — USD conversion uses announcement-date rate
7. **Round naming verbatim:** `round` uses exact name stated by company — "Series A+", "Series B-1", "Series C extension" stay as-is

See [`prompts/monthly_ingestion_template.md`](../../prompts/monthly_ingestion_template.md).

## Deal-type classifier convention

```python
def classify(r):
    if r['sector'] == 'Token':
        return 'token'
    if r['round'] == 'Strategic':
        return 'strategic_corporate'
    if r['round'] in ('Government investment', 'Government', 'Grant'):
        return 'government'
    if r['round'] == 'Debt Financing':
        return 'debt'
    return 'venture'
```

`venture` includes IPO and IPO (filed) and M&A by classifier convention. For "true venture" comparisons, exclude `round in ('IPO', 'IPO (filed)', 'M&A', 'Pre-IPO')` from the venture bucket.

## `total_raised_m` computation

Per entity_id, sum of `amount_m` across all matching rows, **excluding** rounds where:
- `round` in (`IPO`, `IPO (filed)`, `M&A`) — exits, not private capital
- `deal_type` == `government` — sovereign capital, distorts the private-capital figure

Null amounts treated as 0. For entities with only excluded rounds (e.g., an IPO-only row), `total_raised_m` is null.

## Excluded categories (rules locked at v1.0, tightened at v1.1)

- **Public secondaries / PIPEs at already-listed companies** (Aurora rule)
- **Pure-software crypto plays** (zkVM, MEV, custody, social platforms, cross-chain L1) — don't fit hardware-anchored thesis
- **Pure consumer / social software with no embodied-AI anchor** (Humans& exclusion at v1.1) — same logic as crypto-software
- **Conditional government commitments** (CHIPS Act PMTs, DOE LPO conditional, DPA LOIs) — only binding awards count
- **Parent-corporate capex commitments** without a discrete equity/debt raise
- **M&A divestitures** of business units from non-universe parents (e.g., Honeywell W&WS carve-out)
- **Routine procurement contracts** (SBIR awards, OTAs, etc. — only meaningful capital events)

## Version history

- **v1.0** (2026-05-06 AM): Pre-remediation snapshot. 1,154 rows. ~12% of source URLs were agent-fabricated.
- **v1.0.1** (2026-05-06 PM): Post-remediation. 1,133 rows. 99.4% in-scope verified. Anti-fabrication rules locked. URL audit + bulk data audit complete.
- **v1.1** (2026-05-11): Schema expansion. 5 new fields, 2 rename, 1 removal. 1,132 rows (Humans& dropped). Filename convention adopted. New CSV exports use the `Robotnik Frontier Private Rounds <Month-YYYY>.csv` pattern.
- **v1.1.1** (2026-05-12): CSV review fixes. Schema simplification (dropped `total_raised_m` and `total_number_of_raises` from CSV → 23 cols). 26 investor placeholder fixes. 179 investor name canonicalizations applied (151 USER-VERIFY deferred). 41 cumulative-funding strips + 16 rewrites + 3 weak-take rewrites. 2 bottleneck reclassifications to Critical (MP Materials, SpaceX). Full 2025 take backlog refresh to v1.1 spec (172 rows in 4 batches). 7 transposition findings caught + fixed. 1 duplicate row dropped (Infravision). 1,131 rows. 100% in-scope verified. See [`v1_1_1_remediation_log.md`](v1_1_1_remediation_log.md).
- **v1.1.2** (2026-05-13): Pre-seed / seed sweep across Jan 2025 – Apr 2026. +112 new rows (29 Robotics + 26 Semis + 40 Space + 11 Materials + 6 Token). Sweep-specific threshold override ($500K pre-seed / $1M seed) — monthly template unchanged. 1 in-place lead-investor correction (Alta Resource). 1,243 rows. 92.8% verified / 1.2% pending (sweep aggregator 403s, re-check next cycle). 1 row held pending spot-check (Mind Robotics Seed $115M). Future-review queue logged for ~30 Token candidates excluded under current pure-software-crypto rule (potential DePIN scope re-evaluation). See [`v1_1_2_remediation_log.md`](v1_1_2_remediation_log.md) and [`preseed_seed_sweep_summary.md`](preseed_seed_sweep_summary.md).
