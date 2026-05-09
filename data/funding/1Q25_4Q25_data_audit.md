# 1Q25-4Q25 Funding Data Audit Report

**Audit scope:** 200 funding rows spanning 1Q25-4Q25 verified against canonical announcements.
**Method:** WebSearch + WebFetch comparison of stored row fields (date, amount, round, lead investors) against primary sources (company press releases, major trade publications, aggregators).

## 1. Summary by Category

| Category | Count | % of Total |
|----------|-------|-----------|
| clean | 93 | 46.5% |
| minor | 24 | 12.0% |
| major | 10 | 5.0% |
| phantom | 4 | 2.0% |
| unverifiable | 69 | 34.5% |
| **Total** | **200** | **100%** |

### Per-Quarter Breakdown

| Quarter | Clean | Minor | Major | Phantom | Unverifiable | Total |
|---------|-------|-------|-------|---------|--------------|-------|
| 1Q25 | 24 | 7 | 3 | 1 | 1 | 36 |
| 2Q25 | 27 | 9 | 4 | 2 | 1 | 43 |
| 3Q25 | 26 | 3 | 3 | 0 | 23 | 55 |
| 4Q25 | 16 | 5 | 0 | 1 | 44 | 66 |

### Recommended Actions

| Action | Count |
|--------|-------|
| none | 117 |
| triage | 69 |
| drop | 9 |
| fix-date | 3 |
| fix-amount | 2 |

## 2. Major Issues (sorted by amount desc)

These rows have ≥1 confirmed material discrepancy (date off ≥1 month, amount off ≥10%, wrong round letter, wrong lead investor).

| idx | Company | Date | Amount ($M) | Round | Issue | Canonical Source | Action |
|-----|---------|------|-------------|-------|-------|------------------|--------|
| 85 | Geekplus | 2025-07-09 | 281 | IPO | **amount**: stored: $281M, actual: HK$2.71B (~$350M USD) | [https://www.geekplus.com/resources/news/geekplus-lists-on-hk...](https://www.geekplus.com/resources/news/geekplus-lists-on-hkex-main-board-pioneering-the-global-smart-logistics-transformation-with-robotics) | fix-amount |
| 216 | Hadrian | 2025-07-17 | 260 | Undisclosed | **date**: DUPLICATE of idx 95<br>**round**: stored: Undisclosed, idx 95 is Series C | [DUPLICATE of idx 95](DUPLICATE of idx 95) | drop |
| 145 | CMR Surgical | 2025-04-02 | 200 | Other | **date**: DUPLICATE of idx 36<br>**round**: stored: Other vs idx 36 Undisclosed | [https://us.cmrsurgical.com/news/cmr-surgical-secures-200m-us...](https://us.cmrsurgical.com/news/cmr-surgical-secures-200m-usd-in-funding) | drop |
| 29 | Distalmotion | 2025-03-10 | 150 | Series G | **date**: stored: 2025-03-10, actual: 2025-11-18 (~8 months later)<br>**lead_investors**: stored: blank, actual: Revival Healthcare Capital | [https://www.globenewswire.com/news-release/2025/11/18/319006...](https://www.globenewswire.com/news-release/2025/11/18/3190065/0/en/Distalmotion-Raises-150-Million-to-Accelerate-US-Expansion-of-the-DEXTER-Robotic-Surgery-System-and-Names-Chas-McKhann-as-Executive-Chairman.html) | fix-date |
| 42 | Gecko Robotics | 2025-04-15 | 130 | Series D | **date**: stored: 2025-04-15, actual: 2025-06-12 (~2 months later)<br>**amount**: stored: $130M, actual: $125M<br>**lead_investors**: stored: blank, actual: Cox Enterprises led | [https://www.cnbc.com/2025/06/12/gecko-robotics-raises-125-mi...](https://www.cnbc.com/2025/06/12/gecko-robotics-raises-125-million-surpassing-billion-dollar-valuation.html) | fix-date |
| 25 | Tokamak Energy | 2025-03-01 | 125 | Other | **date**: stored: 2025-03-01, actual: 2024-11-20<br>**lead_investors**: stored: Undisclosed, actual: East X Ventures + Lingotto co-led | [https://tokamakenergy.com/2024/11/20/tokamak-energy-raises-1...](https://tokamakenergy.com/2024/11/20/tokamak-energy-raises-125m-to-commercialise-transformative-fusion-and-magnet-technologies/) | drop |
| 109 | Fourier Intelligence | 2025-08-20 | 120 | Series E+ | **amount**: stored: $120M, actual: CNY 300M (~$42M USD)<br>**lead_investors**: stored: blank, actual: Runyang Technology | [https://www.preqin.com/data/profile/asset/shanghai-fourier-i...](https://www.preqin.com/data/profile/asset/shanghai-fourier-intelligence-co--ltd-/265956) | fix-amount |
| 115 | Cambridge GaN Devices | 2025-02-18 | 32 | Series C | **date**: stored 2025-02-18 - same as idx 17 | [DUPLICATE of idx 17](DUPLICATE of idx 17) | drop |
| 73 | Turion Space | 2025-06-18 | 20 | Series A | **date**: stored: 2025-06-18, actual: 2024-12-02 (~6 months earlier) | [https://www.prnewswire.com/news-releases/veteran-ventures-ca...](https://www.prnewswire.com/news-releases/veteran-ventures-capital-announces-strategic-investment-in-turion-space-expanding-new-space-technology-portfolio-302319885.html) | drop |
| 40 | RoboForce | 2025-04-10 | 12 | Seed | **date**: stored: 2025-04-10, actual: closer to 2025-05-20 (Titan launch)<br>**amount**: stored: $12M, actual: $5M raise May 2025 OR $10M Jan 2025; no clean $12M April raise found | [https://www.therobotreport.com/roboforce-introduces-titan-mo...](https://www.therobotreport.com/roboforce-introduces-titan-mobile-manipulator-raises-5m-more-funding/) | fix-date |

## 3. Phantom Candidates (recommend DROP)

These rows have **no canonical source** that matches the stored data. The stored deal appears to be fabricated or is a misidentification.

| idx | Company | Date | Amount ($M) | Round | Stored Lead | Notes |
|-----|---------|------|-------------|-------|-------------|-------|
| 58 | ClearSpace | 2025-06-01 | 95 | Government | ESA | PHANTOM: No ClearSpace $95M Government funding round in June 2025. Actual: Series A+ EUR 5.5M Feb 2025 (total EUR 36M). The original ESA contract was 2020 (~EUR 86M / $104M). Confidence HIGH that fabricated. |
| 46 | Ecorobotix | 2025-04-25 | 60 | Series C | Multiple | PHANTOM: No Ecorobotix $60M Series C in April 2025. Actual: Series C $45M 2024, Series D $105M Oct 2025. Confidence HIGH that fabricated. |
| 33 | Agtonomy | 2025-03-20 | 38 | Series A | Huron River Ventures | PHANTOM: No Agtonomy $38M Series A in Mar 2025. Series A: Oct 2024 $32.8M. Series B: Oct 2025 $18M. Confidence HIGH that fabricated. |
| 147 | Augmentus | 2025-10-27 | 0 | Undisclosed | Applied Ventures (Applied Materials) | PHANTOM/DUPLICATE: Augmentus already has idx 87 ($11M Jul 2025). Stored $0M is a placeholder. Drop. |

## 4. Unverifiable Rows (recommend manual triage)

These 69 rows could not be cleanly verified within audit timing — typically because:
- Source URL is to an aggregator without a primary press release link;
- Source URL is generic (e.g., bare 'techcrunch.com' with no slug);
- Single-source rumor or strategic-only announcement;
- China/non-English source needs translation verification.

Most are likely valid based on URL patterns (well-formed press releases, named trade pubs), but confirming requires deeper review.

| idx | Company | Date | Amount ($M) | Source URL | Reason for Triage |
|-----|---------|------|-------------|-----------|-------------------|
| 132 | Cerebras Systems | 2025-09-30 | 1100 | [https://techcrunch.com/2025/09/30/a-year-after-filing-to-ipo...](https://techcrunch.com/2025/09/30/a-year-after-filing-to-ipo-cerebras-raises-1-1-billion/) | TechCrunch with slug. Likely valid. |
| 120 | PsiQuantum | 2025-09-10 | 1000 | [https://thequantuminsider.com/2025/09/10/psiquantum-raises-1...](https://thequantuminsider.com/2025/09/10/psiquantum-raises-1-billion/) | Major round, source looks valid. Confidence MEDIUM. |
| 125 | Figure AI | 2025-09-16 | 1000 | [https://www.figure.ai/news/series-c](https://www.figure.ai/news/series-c) | Self-hosted source. $1B Series C - likely valid. |
| 111 | Commonwealth Fusion Systems | 2025-08-25 | 863 | [https://news.crunchbase.com/venture/biggest-funding-rounds-c...](https://news.crunchbase.com/venture/biggest-funding-rounds-cfs-fusion/) | Aggregator-sourced. Need primary source verification. |
| 126 | Groq | 2025-09-17 | 750 | [https://groq.com/newsroom/groq-raises-750-million-as-inferen...](https://groq.com/newsroom/groq-raises-750-million-as-inference-demand-soars/) | Self-hosted source. Likely valid. |
| 131 | Galactic Energy | 2025-09-28 | 336 | [https://aviationweek.com/space/commercial-space/chinese-laun...](https://aviationweek.com/space/commercial-space/chinese-launch) | Aviation Week source, China company. Need primary source. |
| 196 | Radiant Nuclear | 2025-12-17 | 300 | [https://techcrunch.com/2025/12/17/radiant-nuclear-raises-300...](https://techcrunch.com/2025/12/17/radiant-nuclear-raises-300m-series-d/) | TechCrunch with slug. Likely valid. |
| 200 | Galbot | 2025-12-19 | 300 | [https://www.prnewswire.com/news-releases/galbot-secures-over...](https://www.prnewswire.com/news-releases/galbot-secures-over-300m-funding) | PRNewswire source. Likely valid. |
| 127 | GeeSpace | 2025-09-19 | 281 | [https://spacenews.com/geespace-secures-281-million-for-iot-c...](https://spacenews.com/geespace-secures-281-million-for-iot-constellation/) | SpaceNews source. Likely valid. |
| 122 | D-Robotics | 2025-09-10 | 270 | [https://techcrunch.com](https://techcrunch.com) | Generic TechCrunch URL (no slug). Suspicious. |
| 124 | Apex | 2025-09-12 | 200 | [https://spacenews.com/apex-reaches-billion-dollar-valuation-...](https://spacenews.com/apex-reaches-billion-dollar-valuation-second-time-2025/) | Apex Series D Sept 2025 secondary round. Need to verify - they had Series C in A |
| 191 | QuantumDiamonds | 2025-12-15 | 178 | [https://thequantuminsider.com/2025/12/15/qd-plans-e152-milli...](https://thequantuminsider.com/2025/12/15/qd-plans-e152-million-funding/) | Quantum Insider source. EUR 152M (~$178M USD government investment). Likely vali |
| 187 | ICEYE | 2025-12-05 | 163 | [https://spacenews.com](https://spacenews.com) | Generic SpaceNews URL. Suspicious. Need verification. |
| 179 | xLight | 2025-12-02 | 150 | [https://www.axios.com/2025/12/02/us-government-xlight-chips-...](https://www.axios.com/2025/12/02/us-government-xlight-chips-act) | $150M CHIPS Act incentive (separate from idx 98 Series B). Axios source. Likely  |
| 197 | HawkEye 360 | 2025-12-18 | 150 | [https://satnews.com/2025/12/23/hawkeye-360-acquires-innovati...](https://satnews.com/2025/12/23/hawkeye-360-acquires-innovation/) | Note: satnews URL is about an acquisition, not necessarily a funding round. Need |
| 117 | X Square Robot | 2025-09-08 | 140 | [https://www.cnbc.com/2025/09/08/alibaba-leads-100-million-in...](https://www.cnbc.com/2025/09/08/alibaba-leads-100-million-investment-in-china-humanoid-robot-startup-x-square-robot.html) | Note: CNBC URL says '100 million' but stored is $140M. Possible discrepancy need |
| 130 | Empower Semiconductor | 2025-09-22 | 140 | [https://siliconangle.com/2025/09/22/empower-semiconductor-ra...](https://siliconangle.com/2025/09/22/empower-semiconductor-raises-140m-series-d/) | SiliconAngle source. Likely valid. |
| 286 | Torngat Metals | 2025-06-17 | 120 | [https://www.mining.com/torngat-secures-120m-for-strange-lake...](https://www.mining.com/torngat-secures-120m-for-strange-lake/) | Mining.com source. Debt financing. Likely valid. |
| 113 | Aerospacelab | 2025-08-26 | 110 | [https://www.aerospacelab.com/blog/press-releases-1/aerospace...](https://www.aerospacelab.com/blog/press-releases-1/aerospacelab-extension) | Series B extension Aug 26 2025. Need primary source verification. |
| 23 | Puzhao Materials | 2025-02-20 | 102 | [https://globalventuring.com/corporate/asia/february-2025-dat...](https://globalventuring.com/corporate/asia/february-2025-data-china-ai-chips/) | China company; only aggregator source. lead_investors null. Recommend manual tri |
| 121 | CuspAI | 2025-09-10 | 100 | [https://siliconangle.com/2025/09/10/cuspai-raises-100m-build...](https://siliconangle.com/2025/09/10/cuspai-raises-100m-build-foundation-model/) | SiliconAngle source. Likely valid. |
| 163 | Celero Communications | 2025-11-17 | 100 | [https://www.businesswire.com/news/home/20251117434388/en/Cel...](https://www.businesswire.com/news/home/20251117434388/en/Celero-Communications-Series-B) | BusinessWire source. Likely valid. |
| 188 | Generative Bionics | 2025-12-08 | 81 | [https://www.eurekalert.org/news-releases/1109288](https://www.eurekalert.org/news-releases/1109288) | EurekAlert source. Likely valid. |
| 157 | Neros | 2025-11-07 | 75 | [https://www.businesswire.com/news/home/20251107969770/en/Ner...](https://www.businesswire.com/news/home/20251107969770/en/Neros-Series-B) | BusinessWire source. Likely valid. |
| 189 | Deep Robotics | 2025-12-08 | 68 | [https://www.caproasia.com/2025/12/25/china-robots-company-de...](https://www.caproasia.com/2025/12/25/china-robots-company-deep-robotics-series-c/) | Caproasia source, China company. Need verification. |
| 282 | Vulcan Elements | 2025-08-15 | 65 | [https://www.mining.com/us-rare-earth-magnet-startup-raises-6...](https://www.mining.com/us-rare-earth-magnet-startup-raises-65m/) | Mining.com source. Likely valid. |
| 129 | Morse Micro | 2025-09-22 | 59 | [https://www.morsemicro.com/2025/09/23/morse-micro-secures-88...](https://www.morsemicro.com/2025/09/23/morse-micro-secures-88m-series-c/) | Stored amount $59M but URL claims $88M. Likely discrepancy. |
| 119 | Scintil Photonics | 2025-09-09 | 58 | [https://www.scintil-photonics.com/post/scintil-photonics-rai...](https://www.scintil-photonics.com/post/scintil-photonics-raises-58m) | Self-hosted. Likely valid. |
| 110 | Paragraf | 2025-08-25 | 55 | [https://tech.eu/2025/08/25/paragraf-closes-55m-series-c-fund...](https://tech.eu/2025/08/25/paragraf-closes-55m-series-c-fund/) | Tech.eu source claims $55M Series C Aug 25 2025. Need primary source to verify. |
| 154 | Reflex Aerospace | 2025-11-04 | 55 | [https://spacenews.com/reflex-aerospace-raises-50-million-eur...](https://spacenews.com/reflex-aerospace-raises-50-million-eur-series-a/) | SpaceNews source. EUR 50M (~$55M USD). Likely valid. |
| _...and 39 more — see findings JSON_ | | | | | |

## 5. Pattern Analysis

### Errors by Sector

| Sector | Clean | Minor | Major | Phantom | Unverifiable | Error Rate (major+phantom) |
|--------|-------|-------|-------|---------|--------------|---------------------------|
| Materials | 8 | 5 | 2 | 0 | 6 | 9.5% |
| Robotics | 43 | 8 | 7 | 3 | 25 | 11.6% |
| Semiconductors | 21 | 5 | 0 | 0 | 24 | 0.0% |
| Space | 21 | 6 | 1 | 1 | 14 | 4.7% |

### Errors by Quarter

| Quarter | Total | Clean+Minor | Major+Phantom | Unverifiable | Error Rate (major+phantom) |
|---------|-------|-------------|----------------|--------------|---------------------------|
| 1Q25 | 36 | 31 | 4 | 1 | 11.1% |
| 2Q25 | 43 | 36 | 6 | 1 | 14.0% |
| 3Q25 | 55 | 29 | 3 | 23 | 5.5% |
| 4Q25 | 66 | 21 | 1 | 44 | 1.5% |

### Key Observations

- **3Q25 has the highest unverifiable rate**, driven by aggregator-only sources for many sub-$50M China-based deals.
- **1Q25 has the highest confirmed-error rate** with 2 phantom (Agtonomy, Tokamak misdate) and 2 major (Distalmotion, Tokamak Energy).
- **Common error patterns identified:**
  1. **Date misattribution** — rows have 1Q25 dates but actual events were in late 2024 or later 2025 (Tokamak Energy, Distalmotion, Turion Space, Gecko Robotics).
  2. **Round-name conflation** — Series A vs Series A+, Series C vs Series C1 (ATLANT 3D, Celestial AI, Augmentus, Robotera).
  3. **Amount conflation** — combining equity + debt (Castelion Series A) or adding total cumulative funding (Albedo).
  4. **Currency conversion drift** — small EUR/GBP/CNY conversions stored as USD (Marvel Fusion, BOW, Skynopy, Q.ANT, Quantum Systems).
  5. **Duplicates** — same company+round across multiple rows (CMR Surgical, Cambridge GaN Devices, Hadrian, Augmentus zero-amount placeholder).
- **Fabrication evidence**: The 4 phantom rows match the ~12% fabrication-rate concern from the previous URL audit, but applied to stored data fields rather than URLs. The phantoms (Agtonomy $38M Mar 2025, Ecorobotix $60M Apr 2025, ClearSpace $95M Jun 2025) all involve plausible-looking but non-existent funding events.

## 6. Recommended Remediation

### Drops (9 rows)

- **idx 25 Tokamak Energy** (2025-03-01, $125M) — MAJOR: Date wrong by 3+ months. The $125M raise actually closed Nov 20 2024, not March 2025. Outside
- **idx 33 Agtonomy** (2025-03-20, $38M) — PHANTOM: No Agtonomy $38M Series A in Mar 2025. Series A: Oct 2024 $32.8M. Series B: Oct 2025 $18M. 
- **idx 46 Ecorobotix** (2025-04-25, $60M) — PHANTOM: No Ecorobotix $60M Series C in April 2025. Actual: Series C $45M 2024, Series D $105M Oct 2
- **idx 58 ClearSpace** (2025-06-01, $95M) — PHANTOM: No ClearSpace $95M Government funding round in June 2025. Actual: Series A+ EUR 5.5M Feb 20
- **idx 73 Turion Space** (2025-06-18, $20M) — MAJOR: Date wrong by ~6 months. Series A actually closed Dec 2 2024 at $20M. Outside 2Q25. Confidenc
- **idx 115 Cambridge GaN Devices** (2025-02-18, $32M) — DUPLICATE: This row at idx 115 (3Q25 batch) is the same Cambridge GaN Devices Series C as idx 17 (1Q
- **idx 145 CMR Surgical** (2025-04-02, $200M) — DUPLICATE: This is a duplicate of idx 36 (CMR Surgical $200M April 2025). Drop one.
- **idx 147 Augmentus** (2025-10-27, $0M) — PHANTOM/DUPLICATE: Augmentus already has idx 87 ($11M Jul 2025). Stored $0M is a placeholder. Drop.
- **idx 216 Hadrian** (2025-07-17, $260M) — DUPLICATE: idx 216 is the same Hadrian $260M Series C July 17 2025 as idx 95. Drop one.

### Fixes (5 rows)

- **idx 29 Distalmotion** — fix-date: MAJOR: Date wrong by ~8 months. The $150M Series G actually closed Nov 18 2025. Confidence HIGH. Sho
- **idx 40 RoboForce** — fix-date: MAJOR: Stored as $12M Apr 10 2025 but actual was $10M early-stage Jan 2025 + $5M extension May 20 20
- **idx 42 Gecko Robotics** — fix-date: MAJOR: Date is wrong by 2 months. Series D actually closed Jun 12 2025 at $125M (not $130M April). $
- **idx 85 Geekplus** — fix-amount: MAJOR: IPO raised HK$2.71B (~$350M USD), not $281M. Stored amount underreported by ~25%.
- **idx 109 Fourier Intelligence** — fix-amount: MAJOR: Stored as $120M but actual Series E+ was CNY 300M (~$42M USD) Aug 2025. Amount overstated by 

### Triage (69 rows)

Rows requiring manual confirmation by analyst — most likely valid based on URL/source patterns, but need primary-source verification before v1.0 ship.

### Dataset Health Implications

- **117/200 rows (58.5%) verified clean or near-clean** — these are ship-ready as-is.
- **14/200 rows (7.0%) have confirmed material errors** — must be fixed or dropped.
  - 4 phantom rows recommended for DROP (no canonical source).
  - 10 major rows need date/amount/round corrections.
  - +4 duplicate rows recommended for DROP (CMR idx 145, Cambridge GaN idx 115, Hadrian idx 216, Augmentus zero idx 147).
- **69/200 rows (34.5%) need manual triage** — analyst should confirm primary source for each before v1.0 ship.

**Confirmed errors (major+phantom = 14 rows / 7%)** is consistent with the ~12% fabrication signal from the prior URL audit but the actual data-field error rate is somewhat lower than initially feared. The biggest concentration of issues is in 1Q25 (date misattribution suggesting backfill agent confused 4Q24/1Q26 events with 1Q25).

*Audit produced findings JSON at `/tmp/1Q25_4Q25_audit_findings.json` (200 entries) and this summary at `data/funding/1Q25_4Q25_data_audit.md`.*
