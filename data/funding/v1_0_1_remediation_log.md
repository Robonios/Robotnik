# v1.0.1 Remediation Log

**Date:** 2026-05-06
**Predecessor:** v1.0 (pre-remediation, 1,154 rows)
**Result:** v1.0.1 (1,134 rows, 99.4% in-scope verified)

This log captures every mutation applied to the dataset between v1.0 and v1.0.1. Total: **20 row deltas + 14 in-place updates**, plus schema additions (Pre-IPO, Series B2 round values; `source_status` field).

## Summary

| Mutation kind | Count |
|---------------|------:|
| Quality-flag fixes (Task 1) | 6 (5 updates + 1 drop + 1 add — Zipline) |
| URL replacements applied | 84 (high-confidence) + 3 (re-audit redirects) |
| Drops from no-match DQ list | 11 |
| FIXes (date/amount + URL) | 10 (with 9 quarter migrations) |
| Fix-created duplicates dropped | 3 |
| Phantom drops (1Q25-4Q25 bulk audit) | 4 |
| Major fixes (1Q25-4Q25 bulk audit) | 7 (with 3 more quarter migrations) |
| Second-pass mutations | 2 (CFS fix + D-Robotics drop) |

**Net row delta:** 1,154 → 1,134 (−20: 22 drops minus 2 adds)

## Schema changes

- **Added field:** `source_status` ∈ {`verified`, `archived`, `pending`}
- **Added round value:** `Pre-IPO` (first use: DeepWay $310M, 2026-04-21)
- **Added round value:** `Series B2` (first use: Commonwealth Fusion Systems $863M, 2025-08-28)
- **Added round value:** `Series H (extension)` (first use: Zipline $200M, 2026-03-23 — Task 1 fix; Zipline Series H first close was 2026-01-21)

## Quarter migrations (12 rows changed quarter)

| Company | Old → New | $M | Sector |
|---------|----------|---:|--------|
| Pacific Fusion (Task 1) | 1Q25 → 4Q24 | $900 | Materials |
| Hadrian (Task 2-3) | 1Q26 → 3Q25 | $260 | Robotics |
| Mujin (Task 2-3) | 3Q25 → 4Q25 | $233 | Robotics |
| CMR Surgical (Task 2-3) | 4Q25 → 2Q25 | $200 | Robotics |
| Zap Energy (Task 2-3) | 2Q25 → 4Q24 | $130 | Materials |
| Starfish Space (Task 2-3) | 1Q26 → 2Q26 | $110 | Space |
| Infravision (Task 2-3) | 2Q25 → 4Q25 | $91 | Robotics |
| constellr (Task 2-3) | 4Q25 → 1Q26 | $44 | Space |
| SatVu (Task 2-3) | 4Q25 → 1Q26 | $41 | Space |
| Cambridge GaN Devices (Task 2-3) | 3Q25 → 1Q25 | $32 | Semis |
| Distalmotion (1Q25-4Q25 audit) | 1Q25 → 4Q25 | $150 | Robotics |
| Tokamak Energy (1Q25-4Q25 audit) | 1Q25 → 4Q24 | $125 | Materials |
| Turion Space (1Q25-4Q25 audit) | 2Q25 → 4Q24 | $20 | Space |

## Phantom drops (15 total)

### Task 1 — Zipline phantom (1)
- Zipline 2025-11-14 Series H $800M — $800M was cumulative across $600M Jan 2026 + $200M Mar 2026 closes. Replaced with one corrected row + one new row (Mar 2026 extension).

### Task 2 — No-match DQ (11)
| Company | Date | $M | Reason |
|---------|------|---:|--------|
| Kargo | 2025-09-15 | $100 | No canonical $100M Series A; most recent confirmed is $42M Series B Dec 2025 |
| General Fusion | 2025-09-15 | $73 | Actuals: $30M CAD Aug 2025, $36.3M Nov 2025 |
| RobCo | 2025-05-10 | $52 | Best match RobCo $42.5M Series B 2024 |
| Bonsai Robotics | 2025-07-10 | $50 | Series A was $15M Jan 2025; July was acquisition not raise |
| EndoQuest Robotics | 2025-07-20 | $36 | Actual: $59M July 2025 (different amount) |
| Generative Bionics | 2025-08-15 | $35 | Actual: €70M (~$81M) seed Dec 2025; sector miscategorized |
| TRIC Robotics | 2025-11-05 | $30 | Most recent is $5.5M seed July 2025 |
| Contoro Robotics | 2025-05-20 | $20 | Actual: $12M Series A March 2025 |
| SwarmFarm | 2025-06-25 | $18 | Actual: $19.85M Oct 2025 |
| Surgerii Robotics | 2025-09-05 | $15 | Actual: $100M Series D Dec 2025; Sept was CE approval |
| Dyna Robotics | 2025-12-10 | $6 | Actual: $120M Series A Sept 2025 |

### Task 1 — USA Rare Earth (1)
- USA Rare Earth 2026-01-26 Government $277M — non-binding LOI, violates binding-only rule.

### 1Q25-4Q25 bulk audit phantoms (4)
| Company | Date | $M | Reason |
|---------|------|---:|--------|
| ClearSpace | 2025-06-01 | $95 | No canonical source; actual round was €5.5M Feb 2025 |
| Ecorobotix | 2025-04-25 | $60 | Actual: Series C $45M 2024, Series D $105M Oct 2025 |
| Agtonomy | 2025-03-20 | $38 | Actual: Series A $32.8M Oct 2024, Series B $18M Oct 2025 |
| Augmentus | 2025-10-27 | $0 | $None placeholder; duplicate of idx 87 ($11M Jul 2025) |

### Second-pass phantom (1)
- D-Robotics 2025-09-10 Series B $270M — same cumulative-recorded-as-discrete pattern as Zipline. $270M is cumulative Series B total reached April 2026 (Series A $100M May 2025 + Series B1 $120M Mar 2026 + Series B2 $150M Apr 2026).

### Fix-created duplicates (3)
- Hadrian, CMR Surgical, Cambridge GaN Devices duplicates — created when Task 2-3 fixes moved wrong-date rows onto dates that already had correct rows.

## Major fixes (in-place updates)

### Task 1 — 6 quality-flag fixes
- Zipline 2026-01-21 ($600M, Series H first close — relabeled from "Undisclosed", filled investors, corrected URL)
- Pacific Fusion (date 2025-01-15 → 2024-10-25, full investor list, canonical URL)
- Unitree IPO (filed) (location + notes corrected: Shanghai STAR Market, not HK)
- Bedrock Robotics (notes rewritten: autonomous construction, not trucking; full syndicate)
- KoBold Metals (date 2025-01-01 → 2025-01-02; investors filled; valuation $2.96B)

### Task 2-3 — 10 FIXes (date/amount corrections + URL)
See [v1_0_remediation_log.md](v1_0_remediation_log.md) for full detail.

### 1Q25-4Q25 bulk audit — 7 majors
| Company | Fix | Notes |
|---------|-----|-------|
| Geekplus | Amount $281M → $350M (HK$2.71B) + FX captured | Was off by 24% due to USD/HKD conversion drift |
| Distalmotion | Date Mar 10 → Nov 18 2025; lead Revival Healthcare added | 8-month date error |
| Gecko Robotics | Date Apr 15 → Jun 12 2025; $130M → $125M; lead Cox Enterprises | 2-month date + amount + lead errors |
| Tokamak Energy | Date Mar 1 2025 → Nov 20 2024; leads East X + Lingotto | 1Q25 → 4Q24 migration |
| Fourier Intelligence | Amount $120M → $42M (CNY 300M) + FX captured | Currency conversion drift; off by 286% |
| Turion Space | Date Jun 18 2025 → Dec 2 2024 | 2Q25 → 4Q24 migration |
| RoboForce | $12M → $5M Seed (extension); date → May 20 2025 | No canonical $12M raise found; matched to $5M Titan launch |

### Second-pass — Commonwealth Fusion Systems
- Round: "Series B" → **"Series B2"** (per new Rule 7, verbatim naming)
- Date: 2025-08-25 → **2025-08-28** (canonical announcement)
- `lead_investors`: NVentures (NVIDIA) → null (no sole lead per CFS press release)
- `other_investors`: appended Brevan Howard, Counterpoint Global, Druckenmiller, NVentures (NVIDIA)
- `source`: → `cfs.energy/news-and-media/commonwealth-fusion-systems-raises-863-million-series-b2-round-...`

## Spot-check decisions applied (post-second-pass)

After v1.0.1 tag was created, 6 spot-check decisions were applied to clear the pending queue:

| Row | Decision |
|-----|----------|
| Etched.ai $500M | URL → Bloomberg (paywall, cite-worthy) |
| ICEYE $163M | URL → tesi.fi (Finnish state investor news, user-provided); lead → General Catalyst; FX captured (EUR 150M) |
| PsiBot $280M | Verified (Gasgoo URL is canonical English-language source — agent false negative) |
| Fourier Intelligence $42M | URL → stcn.com (Securities Times Network, Mandarin primary; user accepted Mandarin acceptance) |
| ENCOS $27.5M | URL → Pandaily (deal-specific, replaces generic monthly recap) |
| Anvil Robotics $5M (Sep 2025) | DROP — phantom (only real event is April 2026 row already in dataset) |

Net: 4 URL replacements + 1 verify + 1 phantom drop. Dataset 1,134 → 1,133.

## Final dataset state

| Metric | Value |
|--------|------:|
| Rows | **1,133** |
| `verified` | 1,058 (93.4%) |
| `archived` (out-of-scope per freshness rule) | 75 (6.6%) |
| `pending` | 0 (0.0%) |
| **In-scope verified** | **1,058 / 1,058 = 100.0%** ✅ |

## Robotics 1Q26 vs 4Q25 ratio (final)

- 4Q25: 32 deals, **$2,945M**
- 1Q26: 39 deals, **$31,461M**
- **Ratio: 10.68×**

The published "9× prior quarter" framing remains conservative — actual is 10.7×. Per user decision, no copy update.

## Files

- [`rounds.json`](rounds.json) — final v1.0.1 dataset (1,134 rows)
- [`dataset_notes.md`](dataset_notes.md) — coverage docs, limitations, methodology
- [`v1_0_remediation_log.md`](v1_0_remediation_log.md) — earlier Task 1 quality-flag fixes
- [`v1_0_data_quality_issues.md`](v1_0_data_quality_issues.md) — earlier Task 2-3 DQ findings
- [`1Q25_4Q25_data_audit.md`](1Q25_4Q25_data_audit.md) — bulk audit findings
- [`v1_0_url_replacements_spot_check.md`](v1_0_url_replacements_spot_check.md) — pending 6 medium + 3 low spot-checks (still open)
- [`source_url_audit.md`](source_url_audit.md) — original URL audit report
