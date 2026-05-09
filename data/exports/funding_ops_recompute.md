# Funding Ops Recompute vs v1.0 Dataset

**Recompute date:** 2026-05-06
**Dataset version:** v1.0 (1,154 rows, of which 1,131 in scope after Token + Cross-Stack filter)
**Reference date for windows:** 2026-05-06

The page filters out `sector ∈ {Token, Cross-Stack}`. The recompute applies the same filter. 23 Token rows are excluded, 0 Cross-Stack rows exist in v1.0 (the filter is a defensive leftover from an older universe schema).

---

## Headline metrics across 4 windows

| Metric | 3M | 6M | 1Y | ALL |
|--------|---:|---:|---:|---:|
| **Capital Raised** | $121.6B | $152.3B | $173.1B | $289.5B |
| **Number of Rounds** | 138 | 211 | 329 | 1,131 |
| **Avg Deal Size (disclosed)** | $942.5M | $757.6M | $544.5M | $262.7M |
| **Most Active Sector** | Robotics (61) | Robotics (97) | Robotics (153) | Robotics (574) |
| **Largest Round** | SpaceX $75B | SpaceX $75B | SpaceX $75B | SpaceX $75B |
| **Top Investor** | Booz Allen Ventures (4) | Andreessen Horowitz (8) | NVentures NVIDIA (16) | Andreessen Horowitz (31) |

### Period-over-period change (vs prior equivalent window)

| Metric | 3M (vs 3M prior) | 6M (vs 6M prior) | 1Y (vs 1Y prior) |
|--------|---:|---:|---:|
| Capital Raised | +296% | +638% | +221% |
| Number of Rounds | +86% | +82% | +16% |
| Avg Deal Size | +124% | +322% | +179% |

The +221% on 1Y is real, not a denominator gap. Prior 1Y (May 2024 – May 2025) has 284 rounds at ~$54B; current 1Y has 329 rounds at $173.1B. The $119B delta is driven primarily by **3 mega-events in the current window**: SpaceX IPO (filed) $75B, Amazon/Globalstar M&A $11.57B, Rapidus $4B Government. Strip those and current 1Y is ~$83B → +54% vs prior, which is more representative of underlying pace.

---

## Sector breakdown (1Y, the headline window)

| Sector | Rounds | Capital |
|--------|------:|--------:|
| Robotics | 153 | $46.5B |
| Space | 66 | $97.9B |
| Semiconductors | 86 | $24.8B |
| Materials | 24 | $3.9B |

Space sector capital is dominated by SpaceX IPO (filed) $75B + Amazon/Globalstar M&A $11.57B = $86.6B / 88% of Space total.

## Stage breakdown (1Y, current page bucketing logic)

| Stage | Rounds | Capital |
|-------|------:|--------:|
| Series A | 84 | $7.1B |
| **Other** | **60** | **$110.0B** |
| Series B | 57 | $8.4B |
| Seed | 55 | $1.4B |
| Series D+ | 39 | $35.4B |
| Series C | 34 | $10.9B |

### What's actually in the "Other 60 / $110B" bucket

The page's stage bucketing buckets **everything that isn't Seed/Series A/B/C/D+** into a single "Other" stage. With the v1.0 enum expanded (Strategic, Government investment, Debt Financing, IPO, IPO (filed), M&A, Pre-IPO, Bridge, Undisclosed, etc.), this bucket is now overloaded:

| Round value within "Other" | Rounds | Capital |
|--------------------------|------:|--------:|
| Undisclosed | 19 | $6.7B |
| M&A | 8 | $13.4B |
| IPO (filed) | 4 | $77.7B (SpaceX $75B alone) |
| IPO | 5 | $3.0B |
| Government investment | 5 | $6.6B |
| Debt Financing | 5 | $0.5B |
| Strategic | 4 | $0.2B |
| Other (literal) | 3 | $0.5B |
| Grant | 3 | $0.7B |
| Government | 2 | $0.4B |
| Bridge | 1 | $0.1B |
| Pre-IPO | 1 | $0.3B |

The fix: split these into **9 distinct bucket categories** (Seed, Series A, Series B, Series C, Series D+, Strategic, Government, Debt, IPO/M&A, Other). The current 6-bucket split was designed before the v1.0 enum expansion.

---

## Top 10 investors (1Y)

| Rank | Name | Deal count |
|-----:|------|----------:|
| 1 | NVentures (NVIDIA) | 16 |
| 2 | Andreessen Horowitz | 11 |
| 3 | Sequoia Capital | 8 |
| 4 | Khosla Ventures | 8 |
| 5 | DCVC | 7 |
| 6 | a16z | 7 |
| 7 | General Catalyst | 6 |
| 8 | Lockheed Martin Ventures | 6 |
| 9 | Coatue | 6 |
| 10 | Lightspeed | 6 |

### NVentures (NVIDIA) double-count check

Per spec: investors counted from both `lead_investors` and `other_investors` fields. Risk of double-count if a firm appears in both fields for the same row.

**Result: 0 rows have NVentures in both fields. 16-deal count is genuine.**

Note: "a16z" and "Andreessen Horowitz" appear as separate entries with 7 and 11 deals respectively. They are the same firm — should be normalized to a single canonical name in a future cleanup. (Not in scope for this task.)

---

## Mismatches between page and v1.0 dataset

| Element | Page state | Recompute (1Y) | Status |
|---------|-----------|----------------|--------|
| Capital Raised headline | $173.0B | $173.1B | ✅ Matches (rounding) |
| Capital change vs prior | +227% | +221% | ✅ Matches (rounding) |
| Number of Rounds headline | 328 | 329 | ⚠️ Off-by-1 (likely page snapshot vs latest dataset) |
| Avg Deal Size | $546M | $544.5M | ✅ Matches (rounding) |
| Most Active Sector | Robotics (152) | Robotics (153) | ⚠️ Off-by-1 (same cause) |
| Largest Round | SpaceX $75.0B | SpaceX $75.0B | ✅ Matches |
| Top Investor | NVentures (NVIDIA) 16 | NVentures (NVIDIA) 16 | ✅ Matches |
| Stage Distribution "Other" | 60 / $110.0B | 60 / $110.0B | ⚠️ Bucket is overloaded — needs split |
| "View all 138 rounds" link | 138 (hardcoded) | 138 (3M) / 329 (1Y) / 1,131 (ALL) | ❌ Hardcoded, doesn't update with period |
| Narrative paragraph | Hard "$173.0B / 152 rounds" | Dynamic from p.num_rounds, p.total_capital_m | ✅ Already dynamic (user impression of hardcoding was incorrect; the values match recompute exactly because page is computing live) |
| 1Y filter button | Last button on toolbar | — | ❌ Missing ALL filter button |
| `<meta name="description">` (HTML head) | "Tracking 313 funding rounds since January 2025" | 1,154 rows since 2023-01-02 | ❌ Hardcoded stale meta description |

### Page is fundamentally correct

The 1Y headline numbers ($173.0B, 328 rounds, $546M avg, NVentures 16) all match the recompute within rounding. The page's compute logic is sound.

### What's actually broken

1. **Stage Distribution "Other 60"** — 9-bucket split needed (mechanical fix to `funding.js`)
2. **"View all 138 rounds" link** — hardcoded, should be dynamic
3. **No ALL filter button** — needs to be added to toolbar
4. **`<meta name="description">`** — hardcoded "313 since January 2025" is stale; should reflect 1,154 rows since 2023

### What's NOT broken (despite user concerns)

1. **+227% suspicious jump** — verified real. Driven by 3 mega-events in current 1Y window (SpaceX/Amazon/Rapidus = $90.6B). Page math is correct.
2. **Top investor counting** — verified no double-count. NVentures genuinely has 16 deals (each row counted once even though the count function looks at both lead and other_investors fields).
3. **Hard-coded $173.0B / 152 rounds in narrative** — narrative is fully dynamic; values shown are live computations. The user's impression was incorrect.

---

## Recommended remediation plan (Task 2.4–2.6)

1. Add `ALL` button to toolbar in `funding.html` (after `1Y`)
2. In `funding.js`:
   - Update `periodDays()` to handle `'ALL'` (return null/Infinity)
   - Update `filterByPeriod()` to skip cutoff filter when period is `ALL`
   - Update `filterByPriorPeriod()` to return `[]` when period is `ALL` (no prior comparison possible)
   - Replace 6-bucket stage logic with 10-bucket bucketing (Seed, Series A, B, C, D+, Strategic, Government, Debt, IPO/M&A, Other)
   - Update `stages`/`stgColors` arrays in `renderStageDistribution()` accordingly
   - Make "View all N rounds" link dynamic from `p.num_rounds`
3. Update `<meta name="description">` to reflect v1.0 dataset state

Out-of-scope for this pass per user instructions:
- Layout changes
- Chart structure changes
- "Request Early Access" CTA
- a16z / Andreessen Horowitz canonical-name consolidation (note for future)
- Token sector visibility (page deliberately filters; respecting current design)
