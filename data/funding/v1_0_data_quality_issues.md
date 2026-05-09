# v1.0 Data Quality Issues — Surfaced During URL Audit
**Date:** 2026-05-06

During the bulk URL replacement search, the research agent flagged **28 rows** with substantive data-quality issues that go beyond URL rot. These are likely fabricated or mislabeled rows from the original backfill agents. Each needs a triage decision: **fix** (correct date/amount/round), **drop** (no real announcement matches), or **leave** (low confidence in agent's correction).

## Category summary

| Category | Count | Recommended action |
|---|---:|---|
| No real announcement matches stored row | 11 | DROP — likely fabricated by backfill agent |
| Wrong date or amount (real event exists) | 10 | FIX — correct date/amount, keep row |
| Other manual triage | 7 | Case-by-case review |
| **Total** | **28** | |

## Detailed list

| # | Company | Stored date | Stored $M | Confidence | Issue | Recommended action |
|---|---------|-------------|----------:|------------|-------|--------------------|
| 1 | **PsiBot** | 2026-03-10 | $280 | low | no canonical source found in Western trade press recommend manual triage | DROP |
| 2 | **D-Robotics** | 2025-09-10 | $270 | medium | DATA QUALITY: 270M Series B total reached April 2026 (B2 round), not September 2025 | TRIAGE |
| 3 | **Hadrian** | 2026-01-25 | $260 | high | DATA QUALITY: Hadrian 260M Series C was July 2025, not January 2026 | TRIAGE |
| 4 | **Mujin** | 2025-07-15 | $233 | high | DATA QUALITY: Mujin 233M Series D announced December 2025, not July 2025 | FIX (date/amount) |
| 5 | **CMR Surgical** | 2025-10-20 | $200 | high | DATA QUALITY: $200M was announced April 2025, not October 2025 | FIX (date/amount) |
| 6 | **Zap Energy** | 2025-06-01 | $130 | high | DATA QUALITY: $130M Series D announced October 2024, not June 2025 | FIX (date/amount) |
| 7 | **Fourier Intelligence** | 2025-08-20 | $120 | low | no canonical Western press article found for August 2025 CNY 300M Series E+ — recommend manual triage | DROP |
| 8 | **Starfish Space** | 2026-03-31 | $110 | high | DATA QUALITY: Round announced April 2026, not March 31 2026 | FIX (date/amount) |
| 9 | **Lyte** | 2026-01-09 | $107 | high | DATA QUALITY: Lyte announced January 5, 2026 not Jan 9 | FIX (date/amount) |
| 10 | **Infravision** | 2025-06-20 | $100 | high | DATA QUALITY: Infravision $91M Series B was announced November 2025, not June 2025 — and the amount in dataset (100M) is rounded from $91M | FIX (date/amount) |
| 11 | **Kargo** | 2025-09-15 | $100 | low | no canonical source found for $100M Kargo Series A in September 2025. Most recent confirmed funding is $42M Series B in Dec 2025. Recommend manual triage — possibly wrong company or amount | DROP |
| 12 | **ClearSpace** | 2025-06-01 | $95 | medium | Original ClearSpace contract was 86M EUR signed November 2020. Could not find new June 2025 funding — recommend manual triage as date/amount may be off | TRIAGE |
| 13 | **General Fusion** | 2025-09-15 | $73 | low | no canonical source found for $73M bridge funding in September 2025. Search shows General Fusion raised $30M CAD in Aug 2025 and $36.3M on Nov 27 2025. Recommend manual triage — amount/date may not... | DROP |
| 14 | **RobCo** | 2025-05-10 | $52 | low | Best matches are RobCo's $42.5M Series B (2024). No $52M round in May 2025 found. Recommend manual triage — amount or date may be off | DROP |
| 15 | **Bonsai Robotics** | 2025-07-10 | $50 | low | DATA QUALITY: Bonsai Series A was $15M in January 2025, not $50M in July 2025. The July 2025 event was the farm-ng acquisition, not a funding round. Recommend manual triage | TRIAGE |
| 16 | **constellr** | 2025-11-01 | $44 | high | DATA QUALITY: constellr's 37M EUR (~44M USD) Series A was announced February 2026, not November 2025 | FIX (date/amount) |
| 17 | **SatVu** | 2025-12-15 | $41 | high | DATA QUALITY: SatVu's $41M (30M GBP) round was announced February 2026, not December 2025 | FIX (date/amount) |
| 18 | **EndoQuest Robotics** | 2025-07-20 | $36 | low | No $36M Series A in July 2025 found. EndoQuest closed a $59M round in July 2025 (lifting valuation to $319M). Recommend manual triage | DROP |
| 19 | **Generative Bionics** | 2025-08-15 | $35 | low | DATA QUALITY: Generative Bionics is Italian humanoid robotics (IIT spinoff), not prosthetics. The 70M EUR (~81M USD) seed round was announced December 2025, not August 2025 with $35M. Recommend man... | FIX (date/amount) |
| 20 | **Cambridge GaN Devices** | 2025-09-01 | $32 | high | DATA QUALITY: CGD's $32M Series C closed February 2025, not September 2025 | TRIAGE |
| 21 | **TRIC Robotics** | 2025-11-05 | $30 | low | DATA QUALITY: TRIC Robotics' most recent funding is $5.5M seed in July 2025 — no $30M Series A in November 2025 found. Recommend manual triage | DROP |
| 22 | **Contoro Robotics** | 2025-05-20 | $20 | low | DATA QUALITY: Contoro $12M Series A was announced March 2025, not May 2025. No $20M round in May 2025 found. Recommend manual triage | DROP |
| 23 | **Turion Space** | 2025-06-18 | $20 | medium | DATA QUALITY: Turion Space's $20M Series A actually closed December 2024, not June 2025. Recommend manual triage on date | TRIAGE |
| 24 | **SwarmFarm** | 2025-06-25 | $18 | low | No $18M round in June 2025 found. SwarmFarm's Series B was $19.85M in October 2025. Recommend manual triage on date/amount | DROP |
| 25 | **Surgerii Robotics** | 2025-09-05 | $15 | low | DATA QUALITY: Surgerii Robotics' $100M Series D was December 2025; no $15M seed in September 2025 found. September 2025 was when they obtained CE approval, not a funding round. Recommend manual triage | DROP |
| 26 | **Dyna Robotics** | 2025-12-10 | $6 | low | DATA QUALITY: No $6M round in December 2025 for Dyna Robotics found. Their Series A was $120M in September 2025, seed was $23.5M in March 2025. Recommend manual triage | DROP |
| 27 | **Anvil Robotics** | 2025-09-20 | $5 | low | DATA QUALITY: Anvil Robotics' $5.5M seed was announced April 2026, not September 2025. Recommend manual triage on date | FIX (date/amount) |
| 28 | **AmpliSi** | 2026-03-12 | $2 | high | DATA QUALITY: AmpliSi raised 2M GBP (~2.5M USD), not 2.5M USD | TRIAGE |

## High-confidence DROP candidates

Rows where the agent found NO canonical announcement matching the stored amount/date. Likely fabricated by backfill agents. **Recommend dropping after spot-check.**

| Company | Date | $M |
|---------|------|---:|
| PsiBot | 2026-03-10 | $280 |
| Fourier Intelligence | 2025-08-20 | $120 |
| Kargo | 2025-09-15 | $100 |
| General Fusion | 2025-09-15 | $73 |
| RobCo | 2025-05-10 | $52 |
| EndoQuest Robotics | 2025-07-20 | $36 |
| TRIC Robotics | 2025-11-05 | $30 |
| Contoro Robotics | 2025-05-20 | $20 |
| SwarmFarm | 2025-06-25 | $18 |
| Surgerii Robotics | 2025-09-05 | $15 |
| Dyna Robotics | 2025-12-10 | $6 |

## High-confidence FIX candidates

Rows where a real funding event exists but the stored date/amount is wrong. **Recommend correcting date/amount + applying URL replacement.**

| Company | Stored date | Real date | $M | What needs fixing |
|---------|-------------|-----------|---:|-------------------|
| Mujin | 2025-07-15 | (see notes) | $233 | DATA QUALITY: Mujin 233M Series D announced December 2025, not July 2025 |
| CMR Surgical | 2025-10-20 | (see notes) | $200 | DATA QUALITY: $200M was announced April 2025, not October 2025 |
| Zap Energy | 2025-06-01 | (see notes) | $130 | DATA QUALITY: $130M Series D announced October 2024, not June 2025 |
| Starfish Space | 2026-03-31 | (see notes) | $110 | DATA QUALITY: Round announced April 2026, not March 31 2026 |
| Lyte | 2026-01-09 | (see notes) | $107 | DATA QUALITY: Lyte announced January 5, 2026 not Jan 9 |
| Infravision | 2025-06-20 | (see notes) | $100 | DATA QUALITY: Infravision $91M Series B was announced November 2025, not June 2025 — and the amount in dataset (100M) is |
| constellr | 2025-11-01 | (see notes) | $44 | DATA QUALITY: constellr's 37M EUR (~44M USD) Series A was announced February 2026, not November 2025 |
| SatVu | 2025-12-15 | (see notes) | $41 | DATA QUALITY: SatVu's $41M (30M GBP) round was announced February 2026, not December 2025 |
| Generative Bionics | 2025-08-15 | (see notes) | $35 | DATA QUALITY: Generative Bionics is Italian humanoid robotics (IIT spinoff), not prosthetics. The 70M EUR (~81M USD) see |
| Anvil Robotics | 2025-09-20 | (see notes) | $5 | DATA QUALITY: Anvil Robotics' $5.5M seed was announced April 2026, not September 2025. Recommend manual triage on date |
