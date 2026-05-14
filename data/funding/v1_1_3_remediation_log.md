# v1.1.3 Remediation Log

**Date:** 2026-05-13
**Predecessor:** v1.1.2 (1,243 rows)
**Result:** v1.1.3 (1,244 rows)

This log captures every mutation applied between v1.1.2 and v1.1.3. Total: **1 row addition**.

## Summary

| Mutation class | Count |
|---|---:|
| New rows added | 1 (Mind Robotics Seed, previously held pending spot-check) |

**Net row delta:** 1,243 → 1,244 (+1).

## Mind Robotics Seed $115M (held from v1.1.2, approved at v1.1.3)

**Why held in v1.1.2:** Mind Robotics had a Stark-pattern transposition history flagged during the v1.1.1 audit cycle, so the v1.1.2 spot-check surfaced the row for user review before adding.

**Spot-check outcome:** Take ↔ description content verified internally consistent (Rivian spinout, RJ Scaringe-led, Eclipse Ventures anchor, $2B Series A four months later with Accel + a16z aligning with the existing 2026-03-11 row). No transposition signal. Approved for v1.1.3.

**Row applied:**
- `entity_id`: `mind-robotics`
- `company`: Mind Robotics
- `sector` / `subsector`: Robotics / Industrial Robots
- `round`: Seed
- `deal_type`: venture
- `amount_m`: 115.0
- `valuation_m`: null
- `date`: 2025-11-04 · 4Q25 · 2025
- `location`: Palo Alto, USA
- `lead_investors`: **Eclipse Ventures** (canonicalized on write per Rule 9; agent draft had `Eclipse`)
- `co_investors`: (empty)
- `related_tickers`: []
- `robotnik_take` (557 chars): "$115M is an outlier seed — Eclipse Ventures anchoring an RJ Scaringe-led Rivian spinout with proprietary auto-manufacturing data. Comp set: Symbotic (SYM) on warehouse automation, Rockwell (ROK) on industrial automation, plus private peers Apptronik and Figure AI on the humanoid side. The Rivian-data-flywheel pitch is unique in the seed cohort — closest analog is Tesla's Optimus internal program. Four months later the Series A priced at $2B valuation with Accel and a16z, validating the seed thesis but pricing in the entire data-advantage moat upfront."
- `source`: https://techcrunch.com/2025/11/04/rivian-creates-another-spinoff-company-called-mind-robotics/
- `source_status`: verified
- `policy_exposure`: None
- `value_chain_tier`: (empty — pre-commercial seed-stage)
- `bottleneck_risk`: Pre-commercial
- `company_description`: "Mind Robotics is a Rivian spinout building AI-enabled robotic systems for complex manufacturing tasks requiring dexterity, adaptability, and real-time decision-making, leveraging Rivian operations data as a foundation. Led by Rivian CEO RJ Scaringe."

## Mind Robotics now has 2 rows in the dataset

| Date | Round | Amount | Lead |
|---|---|---:|---|
| 2025-11-04 | Seed | $115M | Eclipse Ventures |
| 2026-03-11 | Series A | $500M | Andreessen Horowitz, Accel |

Total raised tracked: $615M across the two rounds.

## Final dataset state

| Metric | Value |
|---|---:|
| Rows | **1,244** |
| `verified` | 1,154 (92.8%) |
| `archived` | 75 (6.0%) |
| `pending` | 15 (1.2%) |
| Pre-seed in Jan 2025 – Apr 2026 | 37 |
| Seed in Jan 2025 – Apr 2026 | 132 (+1 Mind Robotics) |
| CSV columns | 23 (unchanged) |
| schema_version | v1.1.3 |
| updated | 2026-05-13 |

## Dataset lock for first VC outreach wave

Per user direction, **dataset is locked at v1.1.3** for the first VC outreach wave. No further schema or content changes until after the initial sends generate feedback. Future iterations:
- Feedback-driven follow-ups expected after VC reads
- Monthly ingestion cycle continues against the locked v1.1.3 base
- Future-review queue items (Mind Robotics review-pending: now closed; Token DePIN audit; 151 USER-VERIFY canonical-name candidates; pre-2025 take refresh) all remain deferred pending feedback signal

## Files

- [`rounds.json`](rounds.json) — final v1.1.3 dataset (1,244 rows)
- `data/exports/Robotnik Frontier Private Rounds April-2026.csv` — 23 cols × 1,244 rows
- [`v1_1_2_remediation_log.md`](v1_1_2_remediation_log.md) — predecessor log
- [`preseed_seed_sweep_summary.md`](preseed_seed_sweep_summary.md) — sweep that surfaced this row
- [`dataset_notes.md`](dataset_notes.md) — updated for v1.1.3
