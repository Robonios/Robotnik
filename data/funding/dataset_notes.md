# Funding Dataset — Documentation Notes

**v1.1 (2026-05-11)**

This document captures the schema, methodology, known limitations, and acceptance criteria for downstream consumers (VCs, analysts).

## Schema (v1.1 — 24 columns in CSV export)

CSV export column order:

```
entity_id, company, company_description, sector, subsector,
value_chain_tier, bottleneck_risk, policy_exposure, round,
deal_type, amount_m, valuation_m, total_raised_m,
total_number_of_raises, date, date_display, month_year,
quarter, year, location, lead_investors, co_investors,
related_tickers, robotnik_take, source
```

24 columns. The internal JSON (`rounds.json`) additionally retains `source_status` (verified | archived | pending) for audit purposes — not exported.

### New fields in v1.1

| Field | Type | Definition |
|-------|------|------------|
| `company_description` | str \| null | 1-3 sentence factual description of what the company makes/does, who it's for, technical approach if distinctive. No strategic framing. No investor info. Plain prose. |
| `value_chain_tier` | str \| null | One of 8 tiers; describes where the company creates value in the frontier-tech stack. Backfilled for Jan 2025 → Apr 2026 only; older rows leave empty. |
| `bottleneck_risk` | str \| null | Five-value risk score on the company's supply-chain position. Backfilled for Jan 2025 → Apr 2026 only. |
| `policy_exposure` | str \| null | Semicolon-separated tags from a controlled vocabulary identifying the policy regimes the deal is exposed to. Backfilled across full dataset. |
| `total_number_of_raises` | int | Count of rounds in the dataset matching the same `entity_id`. Computed; recomputed each monthly regeneration. |

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
| `robotnik_take` | Full dataset; refreshed for Jan-Apr 2026 only (older rows carry the v1.0.1 `robotnik_notes` content as-is) |
| `total_raised_m` / `total_number_of_raises` | Computed across full dataset every monthly regeneration |

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
- **Total rows:** 1,132 (post-v1.1: Humans& dropped as out-of-universe consumer software)

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

## Source URL audit summary

| Status | Count | % |
|--------|------:|---:|
| `verified` — URL confirmed live or paywall-citable | 1,048 | 92.6% |
| `archived` — out-of-scope per freshness rule (date >365d AND amount <$500M) | 75 | 6.6% |
| `pending` — awaiting spot-check approval | 9 | 0.8% |
| **Total** | **1,132** | **100%** |

(Counts will refresh in v1.1 final CSV regeneration; figures shown reflect post-Humans&-drop state.)

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
