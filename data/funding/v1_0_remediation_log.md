# v1.0 Remediation Log
**Date:** 2026-05-06

Quality-flag fixes from the Source URL Audit follow-up. Each fix corresponds to a substantive data error (not just a URL replacement).

## Summary
| # | Kind | Company | Date | $M | Reason |
|---|------|---------|------|---:|--------|
| 1 | DROP | USA Rare Earth | 2026-01-26 | 277 | Non-binding LOI — violates binding-only government rule. Same logic as DOE LP... |
| 2 | DROP | Zipline | 2025-11-14 | 800 | Phantom row — $800M is cumulative across Series H first close ($600M Jan 2026... |
| 2 | UPDATE | Zipline | 2026-01-21 |  | Series H first close — was mislabeled "Undisclosed". Replaced with verified c... |
| 2 | ADD | Zipline | 2026-03-23 | 200.0 | Series H extension of $200M closed March 23 2026 (Paradigm-led), bringing cum... |
| 3 | UPDATE | Pacific Fusion |  |  | Stealth-emergence and $900M Series A announcement actually occurred Oct 25 20... |
| 4 | UPDATE | Unitree Robotics |  |  | Filing venue is Shanghai STAR Market, not Hong Kong. Notes now reflect canoni... |
| 5 | UPDATE | Bedrock Robotics |  |  | Bedrock is autonomous construction (excavator retrofit kits), not trucking. N... |
| 6 | UPDATE | KoBold Metals |  |  | Announcement was Jan 2 2025 (TechCrunch dateline), not Jan 1. Trivial date ad... |

## Fix details

### Fix 1 — USA Rare Earth $277M (2026-01-26): DROP

Per binding-only government rule (added during 1Q23 backfill). The Jan 26 announcement was a *non-binding Letter of Intent* to provide up to $277M direct funding + $1.3B senior secured loan under CHIPS Program. Same logic as DOE LPO conditional commitments and CHIPS Act PMTs we excluded earlier.

Future binding award disbursement (when finalized) would be eligible for inclusion at that close date.

### Fix 2 — Zipline phantom row + extension reconciliation

Three-part fix:

1. **DROP** idx=172 (2025-11-14 Series H $800M) — phantom row. The $800M figure was cumulative across two real closes, mistakenly recorded as a single Nov 2025 event.
2. **UPDATE** idx=226 (2026-01-21 Undisclosed $600M) — relabel round to Series H, fill investors (Fidelity, Baillie Gifford, Valor, Tiger Global), set valuation $7.6B post-money, replace placeholder URL with canonical TechCrunch URL.
3. **ADD** new row 2026-03-23 Series H (extension) $200M — Paradigm-led extension closing the cumulative Series H at $800M. Was missing from dataset.

### Fix 3 — Pacific Fusion: date 2025-01-15 → 2024-10-25, 1Q25 → 4Q24

Stealth-emergence and $900M Series A announcement actually occurred Oct 25 2024 (Bloomberg, ImpactAlpha, Pacific Fusion own update). Row moves quarter from 1Q25 to 4Q24. Notes rewritten with full investor list (General Catalyst lead + Andrew Forrest, Breakthrough Energy Ventures, Eric Schmidt, John Doerr, Ken Griffin, Reid Hoffman, Mustafa Suleyman, Patrick Collison, Lightspeed, Lowercarbon Capital, etc.). URL replaced with canonical pacificfusion.com.

Cross-quarter implication: 4Q24 deal count goes from 89 → 90; 1Q25 from 36 → 35.

### Fix 4 — Unitree Robotics IPO (filed): location and notes corrected

Filing venue is Shanghai STAR Market (688-prefix Chinese A-share board), not Hong Kong. Location updated to "China (Hangzhou; Shanghai STAR Market listing)". Notes rewritten with verified Caixin Global details: CNY 4.2B (~$610M) raise at ~$7B valuation, net income CNY 105M, revenue CNY 1.2B, humanoid robots = 51.5% of revenue. Source URL replaced with Caixin Global canonical.

### Fix 5 — Bedrock Robotics: autonomous construction, not trucking

Bedrock is an autonomous-construction startup founded by ex-Waymo engineers; builds the Bedrock Operator retrofit kit that transforms 20-80 ton excavators into autonomous earth-moving machines. Notes rewritten to reflect actual product category. Subsector kept as Industrial Robots (broadest fit). Lead investors corrected to CapitalG + Valor Atreides AI Fund (the actual co-lead structure). Other investors filled (Xora, 8VC, Eclipse, Emergence, Perry Creek, NVentures, Tishman Speyer, MIT, Georgian, Incharge, C4 Ventures). Valuation set to $1.75B post-money. Source URL replaced with The Robot Report canonical.

### Fix 6 — KoBold Metals: date 2025-01-01 → 2025-01-02

Announcement was Jan 2 2025 (TechCrunch dateline), not Jan 1. Trivial date adjustment (1Q25 unchanged). URL placeholder (`techcrunch.com`) replaced with canonical full TechCrunch article URL. Lead investors filled (Durable Capital Partners + T. Rowe Price). Other investors filled (a16z, Bond, BEV, Earthshot, Equinor, Mitsubishi, etc.). Valuation set to $2.96B post-money.

## Dataset state after Fix 1-6

- Row count: 1,154 → **1,153** (-2 drops + 1 add)
- Quarter rebalance: 1Q25 -1, 4Q24 +1 (Pacific Fusion move); 1Q26 +0 net (Zipline phantom drop -1, Zipline extension add +1, both in 1Q26)
- Dataset `updated`: 2026-05-06
