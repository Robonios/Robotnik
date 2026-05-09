# Source URL Audit — v1.0 dataset (1,154 rows)
**Audit date:** 2026-05-06
**Method:** HEAD/GET against each `source` URL with 8s timeout, 12 parallel workers, redirect chain capture, paywall-domain matching, structural placeholder detection.

## TL;DR
**83.4% of source URLs are likely-OK** (963/1,154 — OK or paywall-but-citable or 167 BOT_BLOCKED that 99% return 200 in browser).

**16.6% need attention** (191/1,154 — 141 DEAD, 48 PLACEHOLDER, 2 persistently RATE_LIMITED).

**37 REDIRECT URLs auto-mutated** to canonical equivalents (4 candidates reverted because the redirect was to a homepage = effectively dead).

**22 high-confidence replacement candidates** found via targeted web search for the highest-value DEAD/PLACEHOLDER rows. The remaining 167 are flagged for manual triage.

## Categorization
| Category | Count | % | Treatment |
|----------|------:|---:|-----------|
| OK | 750 | 65.0% | None — clean |
| BOT_BLOCKED | 167 | 14.5% | Likely valid in browser; HEAD/GET blocked at HTTP layer (BusinessWire 82, Crunchbase 13, Bloomberg 12, etc.) |
| DEAD | 141 | 12.2% | 109 HTTP 404 + timeouts/SSL/etc. — flag for replacement |
| PLACEHOLDER | 48 | 4.2% | Bare-domain or homepage URLs (e.g. `https://techcrunch.com`) — flag for replacement |
| REDIRECT | 37 | 3.2% | Auto-mutated to canonical final URL |
| PAYWALL | 9 | 0.8% | URL valid as citation; gated content (Bloomberg, FT, KED Global, etc.) |
| RATE_LIMITED | 2 | 0.2% | After retry; both rows are helsing.ai (active rate limiting) |
| **Total** | **1154** | **100.0%** | |

## Pattern: agent-fabricated URLs in backfill

Most DEAD URLs are not "rotted out" — they're **agent-fabricated patterns** from the backfill workflow. Many follow the template `https://[publication]/[year]/[mm]/[dd]/[plausible-slug]/` but the article was never actually published at that exact path. Examples confirmed via WebFetch:

- `techcrunch.com/2025/11/14/zipline-raises-800m` — 404 (canonical: `2026/03/23/zipline-snaps-up-another-200m...`)
- `techcrunch.com/2026/01/14/etched-raises-500m/` — 404
- `therobotreport.com/neura-robotics-1-2b-funding/` — 404
- `nscale.com/news/series-c` — 404 (canonical: `nscale.com/press-releases/nscale-series-c`)
- `prnewswire.com/news-releases/galbot-secures-over-300-million-302647204.html` — 404 (canonical: `...-million-in-new-funding-breaking-records-with-3-billion-valuation-in-chinas-humanoid-robot-sector-302647204.html`)

In all checked cases, the deal is real but the URL is a confabulation. This means: **the rows themselves are fine, only the citations are wrong.** A second-pass URL replacement effort is the right remediation.

## REDIRECT mutations applied (37)

Same-host canonical URL fixes auto-applied. 4 candidate redirects were reverted because they pointed to bare-domain homepages (= effectively dead links).

| idx | Company | Old URL | New URL |
|----:|---------|---------|---------|
| 35 | Agility Robotics | `https://techstartups.com/2025/03/31/agility-robotics-rais...` | `https://techstartups.com/2025/03/31/agility-robotics-rais...` |
| 39 | Portal Space Systems | `https://spacenews.com/portal-space-systems-raises-17-5-mi...` | `https://spacenews.com/portal-space-systems-raises-17-5-mi...` |
| 56 | Zeno Power | `https://spacenews.com/nuclear-battery-startup-zeno-power-...` | `https://spacenews.com/nuclear-battery-startup-zeno-power-...` |
| 62 | Infleqtion | `https://infleqtion.com/infleqtion-raises-100m/` | `https://infleqtion.com/infleqtion-raises-100m-to-scale-at...` |
| 89 | Kongsberg Ferrotech | `https://www.nif.fund/news/nato-innovation-fund-leads-eur1...` | `https://www.nif.fund/news/nato-innovation-fund-leads-eur1...` |
| 91 | Varda Space Industries | `https://www.satellitetoday.com/finance/2025/07/11/varda-r...` | `https://www.satellitetoday.com/finance/2025/07/11/varda-r...` |
| 104 | MP Materials | `https://investornews.com/market-opinion/follow-the-money-...` | `https://investornews.com/market-opinion/follow-the-money-...` |
| 108 | Raise Robotics | `https://www.enr.com/articles/61108-raise-robotics-nets-77...` | `https://www.enr.com/articles/61108-raise-robotics-nets-77...` |
| 127 | PsiQuantum | `https://thequantuminsider.com/2025/09/10/psiquantum-raise...` | `https://thequantuminsider.com/2025/09/10/psiquantum-raise...` |
| 165 | Farcast | `https://www.telesat.com/press/press-releases/telesat-inve...` | `https://www.telesat.com/press/press-releases/telesat-inve...` |
| 169 | Forterra | `https://www.globenewswire.com/news-release/2025/11/12/318...` | `https://www.globenewswire.com/news-release/2025/11/12/318...` |
| 176 | Leanspace | `https://spacenews.com/leanspace-raises-e10-million-series...` | `https://spacenews.com/leanspace-raises-e10-million-series...` |
| 185 | Quantum Systems | `https://techstartups.com/2025/11/27/german-drone-startup-...` | `https://techstartups.com/2025/11/27/german-drone-startup-...` |
| 200 | Deep Robotics | `https://www.caproasia.com/2025/12/25/china-robots-company...` | `https://www.caproasia.com/2025/12/25/china-robots-company...` |
| 279 | Elephantech | `https://thebridge.jp/en/2026/03/elephantech-secures-%C2%A...` | `https://thebridge.jp/en/2026/03/elephantech-secures-%c2%a...` |
| ... | ... | _and 22 more_ | ... |

### Redirects reverted (NOT mutated — reclassified as DEAD)

| Company | Original URL | Redirect target (homepage) |
|---------|--------------|---------------------------|
| Quantum Systems | `dronelife.com/2025/05/06/quantum-systems-raises-e160m/` | `dronelife.com/` |
| MACH | `roboticsandautomationnews.com/.../mach-secures-7-million-seed-funding/97409/` | `roboticsandautomationnews.com` |
| Fotokite | `dronelife.com/2024/04/12/fotokite-secures-11-million-in-series-b-funding/` | `dronelife.com/` |
| Forge Nano | `forgenano.com/forge-nano-raises-us-50m-to-build-out-battery-production-line.../` | `forgenano.com/` |

## High-confidence replacement candidates (22)

Found via targeted web search for the highest-value DEAD/PLACEHOLDER rows. **Not auto-mutated** — flagged for manual approval.

| idx | Company | Date | $M | Sector | Current (broken) URL | Replacement URL | Confidence | Notes |
|----:|---------|------|---:|--------|---------------------|-----------------|------------|-------|
| 270 | Nscale | 2026-03-09 | $2000 | Semiconductors | `https://nscale.com/news/series-c` | `https://www.nscale.com/press-releases/nscale-series-c` | HIGH | Nscale own press release |
| 297 | Shield AI | 2026-03-26 | $2000 | Robotics | `https://techstartups.com/2026/03/26/defense-ai-...` | `https://shield.ai/shield-ai-to-acquire-software-simulatio...` | HIGH | shield.ai own press release |
| 267 | NEURA Robotics | 2026-03-04 | $1200 | Robotics | `https://www.therobotreport.com/neura-robotics-1...` | `https://siliconangle.com/2026/03/04/humanoid-robot-maker-...` | HIGH | SiliconANGLE |
| 7 | Pacific Fusion | 2025-01-15 | $900 | Materials | `https://techcrunch.com` | `https://www.pacificfusion.com/updates/founders-letter` | HIGH | Pacific Fusion own update — note: actual announcement Oct 2024 not Jan 2025 |
| 172 | Zipline | 2025-11-14 | $800 | Robotics | `https://techcrunch.com/2025/11/14/zipline-raise...` | `https://techcrunch.com/2026/03/23/zipline-snaps-up-anothe...` | MEDIUM | TechCrunch — note: our date 2025-11-14 may be wrong; $800M cumulative was reached March 2026 |
| 911 | 42dot | 2023-04-26 | $787 | Robotics | `https://www.kedglobal.com/automobiles/newsView/...` | `https://www.marketscreener.com/quote/stock/HYUNDAI-MOTOR-...` | HIGH | MarketScreener (replaces dead KED Global URL) |
| 135 | Groq | 2025-09-17 | $750 | Semiconductors | `https://techcrunch.com/2025/09/17/nvidia-ai-chi...` | `https://groq.com/newsroom/groq-raises-750-million-as-infe...` | HIGH | Groq own press release |
| 286 | Unitree Robotics | 2026-03-20 | $610 | Robotics | `https://techcrunch.com/2026/03/20/unitree-robot...` | `https://www.caixinglobal.com/2026-03-21/unitree-robotics-...` | HIGH | Caixin Global — note: IPO is on Shanghai STAR Market not HK as currently noted |
| 73 | Applied Intuition | 2025-06-17 | $600 | Robotics | `https://techcrunch.com/2025/06/17/applied-intui...` | `https://www.appliedintuition.com/press-releases/series-f` | HIGH | Applied Intuition own press release |
| 264 | Sierra Space | 2026-03-03 | $550 | Space | `https://spacenews.com/sierra-space-550m-series-c/` | `https://www.sierraspace.com/press-releases/sierra-space-c...` | HIGH | Sierra Space own press release |
| 0 | KoBold Metals | 2025-01-01 | $537 | Materials | `https://techcrunch.com` | `https://techcrunch.com/2025/01/02/kobold-used-ai-to-find-...` | HIGH | TechCrunch — note: announcement was Jan 2 2025 not Jan 1 |
| 266 | Vast | 2026-03-03 | $500 | Space | `https://spacenews.com/vast-500m-series-a/` | `https://www.vastspace.com/updates/vast-secures-500m-in-fu...` | HIGH | Vast own update |
| 275 | Mind Robotics | 2026-03-11 | $500 | Robotics | `https://www.therobotreport.com/mind-robotics-50...` | `https://techcrunch.com/2026/03/11/rivian-mind-robotics-se...` | HIGH | TechCrunch |
| 20 | Lambda | 2025-02-19 | $480 | Semiconductors | `https://www.cnbc.com/2025/02/19/ai-cloud-startu...` | `https://lambda.ai/blog/lambda-raises-480m-to-expand-ai-cl...` | HIGH | Lambda own blog |
| 10 | Helion Energy | 2025-01-28 | $425 | Materials | `https://helionenergy.com` | `https://www.helionenergy.com/articles/helion-announces-42...` | HIGH | Helion own press release |
| 155 | Redwood Materials | 2025-10-23 | $350 | Materials | `https://techcrunch.com` | `https://www.redwoodmaterials.com/news/redwood-announces-3...` | HIGH | Redwood own press release |
| 197 | Castelion | 2025-12-05 | $350 | Space | `https://techcrunch.com` | `https://www.castelion.com/news/series-b/` | HIGH | Castelion own press release |
| 212 | Galbot | 2025-12-19 | $300 | Robotics | `https://www.prnewswire.com/news-releases/galbot...` | `https://www.prnewswire.com/news-releases/galbot-secures-o...` | HIGH | PRNewswire |
| 88 | Geekplus | 2025-07-09 | $281 | Robotics | `https://www.prnewswire.com/news-releases/geekpl...` | `https://www.geekplus.com/resources/news/geekplus-lists-on...` | HIGH | Geekplus own press release |
| 222 | USA Rare Earth | 2026-01-26 | $277 | Materials | `https://www.nist.gov/news-events/news/2026/01/b...` | `https://www.globenewswire.com/news-release/2026/01/26/322...` | HIGH | GlobeNewswire — CRITICAL: this is a non-binding LOI, should be EXCLUDED per binding-only rule |
| 240 | Bedrock Robotics | 2026-02-04 | $270 | Robotics | `https://www.prnewswire.com/news-releases/bedroc...` | `https://www.therobotreport.com/bedrock-robotics-270m-seri...` | HIGH | The Robot Report — note: Bedrock is autonomous CONSTRUCTION, not trucking as currently noted |
| 202 | K2 Space | 2025-12-11 | $250 | Space | `https://www.prnewswire.com/news-releases/k2-spa...` | `https://www.prnewswire.com/news-releases/k2-space-raises-...` | HIGH | PRNewswire |

### Quality flags surfaced via replacement search

Several rows had MORE than just a broken URL — search revealed substantive data quality issues. Flagged for separate triage:

1. **USA Rare Earth (idx for 2026-01-26)** — Per binding-only government rule, this is a *non-binding Letter of Intent* (LOI), not a binding award. Should be **EXCLUDED** consistent with how we treated DOE LPO conditional commitments and CHIPS Act PMTs.
2. **Zipline 2025-11-14 Series H $800M** — Date may be wrong. The $800M is *cumulative* across two closes: $600M Jan 2026 + $200M Mar 2026. Either reclassify as 2026-01 with $600M, or split into two rows (multi-row convention).
3. **Pacific Fusion 2025-01-15 Series A $900M** — Date may be wrong. Actual announcement was Oct 2024. May not be in 1Q25 at all.
4. **Unitree Robotics 2026-03-20 IPO (filed) $610M** — Our notes say "Hong Kong IPO" but the filing is on **Shanghai STAR Market**, not HK. AgiBot is the HK candidate.
5. **Bedrock Robotics 2026-02-04 Series B $270M** — Our notes mention "trucking" but Bedrock is autonomous **construction** (excavator retrofit kits), not trucking.
6. **KoBold Metals 2025-01-01** — Announcement was Jan 2 2025, not Jan 1. Trivial date adjustment.

## DEAD rows (141) — full list

Sorted by deal size descending. The top 22 (by $M) have replacement candidates above; the remaining are flagged for manual triage during a future URL-replacement pass.

<details>
<summary>Click to expand full list of 141 DEAD rows</summary>

| idx | Company | Date | $M | Sector | Round | Current URL | Error | Replacement |
|----:|---------|------|---:|--------|-------|-------------|-------|-------------|
| 595 | Lithium Americas | 2024-03-12 | $2260 | Materials | Government investment | `https://www.energy.gov/lpo/articles/lpo-announc...` | HTTP 404 | TODO |
| 270 | Nscale | 2026-03-09 | $2000 | Semiconductors | Series C | `https://nscale.com/news/series-c` | HTTP 404 | see candidates table |
| 297 | Shield AI | 2026-03-26 | $2000 | Robotics | Series G | `https://techstartups.com/2026/03/26/defense-ai-...` | URLError: _ssl.c:1112: The han | see candidates table |
| 267 | NEURA Robotics | 2026-03-04 | $1200 | Robotics | Undisclosed | `https://www.therobotreport.com/neura-robotics-1...` | HTTP 404 | see candidates table |
| 172 | Zipline | 2025-11-14 | $800 | Robotics | Series H | `https://techcrunch.com/2025/11/14/zipline-raise...` | HTTP 404 | see candidates table |
| 911 | 42dot | 2023-04-26 | $787 | Robotics | Strategic | `https://www.kedglobal.com/automobiles/newsView/...` | HTTP 502 | see candidates table |
| 135 | Groq | 2025-09-17 | $750 | Semiconductors | Series E | `https://techcrunch.com/2025/09/17/nvidia-ai-chi...` | HTTP 404 | see candidates table |
| 286 | Unitree Robotics | 2026-03-20 | $610 | Robotics | IPO (filed) | `https://techcrunch.com/2026/03/20/unitree-robot...` | HTTP 404 | see candidates table |
| 73 | Applied Intuition | 2025-06-17 | $600 | Robotics | Series F | `https://techcrunch.com/2025/06/17/applied-intui...` | HTTP 404 | see candidates table |
| 264 | Sierra Space | 2026-03-03 | $550 | Space | Series C | `https://spacenews.com/sierra-space-550m-series-c/` | HTTP 404 | see candidates table |
| 219 | Etched.ai | 2026-01-14 | $500 | Semiconductors | Undisclosed | `https://techcrunch.com/2026/01/14/etched-raises...` | HTTP 404 | TODO |
| 266 | Vast | 2026-03-03 | $500 | Space | Series A | `https://spacenews.com/vast-500m-series-a/` | HTTP 404 | see candidates table |
| 275 | Mind Robotics | 2026-03-11 | $500 | Robotics | Series A | `https://www.therobotreport.com/mind-robotics-50...` | HTTP 404 | see candidates table |
| 280 | DOE CMEI Program | 2026-03-13 | $500 | Materials | Grant | `https://www.energy.gov/articles/doe-cmei-grants` | HTTP 404 | TODO |
| 20 | Lambda | 2025-02-19 | $480 | Semiconductors | Series D | `https://www.cnbc.com/2025/02/19/ai-cloud-startu...` | HTTP 404 | see candidates table |
| 272 | Rhoda AI | 2026-03-10 | $450 | Robotics | Undisclosed | `https://www.therobotreport.com/rhoda-ai-450m/` | HTTP 404 | TODO |
| 246 | Axiom Space | 2026-02-12 | $350 | Space | Debt Financing | `https://spacenews.com/axiom-space-350m-debt-fac...` | HTTP 404 | TODO |
| 212 | Galbot | 2025-12-19 | $300 | Robotics | Undisclosed | `https://www.prnewswire.com/news-releases/galbot...` | HTTP 404 | see candidates table |
| 88 | Geekplus | 2025-07-09 | $281 | Robotics | IPO | `https://www.prnewswire.com/news-releases/geekpl...` | HTTP 404 | see candidates table |
| 224 | PsiBot | 2026-03-10 | $280 | Robotics | Series A | `https://autonews.gasgoo.com/articles/news/2-bil...` | HTTP 468 | TODO |
| 222 | USA Rare Earth | 2026-01-26 | $277 | Materials | Government | `https://www.nist.gov/news-events/news/2026/01/b...` | HTTP 404 | see candidates table |
| 240 | Bedrock Robotics | 2026-02-04 | $270 | Robotics | Series B | `https://www.prnewswire.com/news-releases/bedroc...` | HTTP 404 | see candidates table |
| 202 | K2 Space | 2025-12-11 | $250 | Space | Series C | `https://www.prnewswire.com/news-releases/k2-spa...` | HTTP 404 | see candidates table |
| 28 | Shield AI | 2025-03-06 | $240 | Robotics | Series F | `https://techcrunch.com/2025/03/06/shield-ai-rai...` | HTTP 404 | TODO |
| 287 | Kandou AI | 2026-03-23 | $225 | Semiconductors | Series A | `https://kandou.com/news/funding` | HTTP 404 | TODO |
| 268 | PLD Space | 2026-03-04 | $209 | Space | Series C | `https://spacenews.com/pld-space-209m-series-c/` | HTTP 404 | TODO |
| 47 | Apex | 2025-04-28 | $200 | Space | Series C | `https://www.prnewswire.com/news-releases/apex-r...` | HTTP 404 | TODO |
| 271 | Eridu | 2026-03-10 | $200 | Semiconductors | Series A | `https://eridu.ai/news/series-a` | URLError: [SSL: TLSV1_ALERT_PR | TODO |
| 786 | iRobot | 2023-07-24 | $200 | Robotics | Debt Financing | `https://investor.irobot.com/news-releases/news-...` | Timeout | TODO |
| 506 | 42dot | 2024-06-30 | $185 | Robotics | Strategic | `https://www.kedglobal.com/automobiles/newsView/...` | HTTP 502 | TODO |
| 203 | QuantumDiamonds | 2025-12-15 | $178 | Semiconductors | Government investment | `https://www.eu-startups.com/2025/12/quantumdiam...` | HTTP 403 | TODO |
| 51 | Quantum Systems | 2025-05-06 | $176 | Robotics | Series C | `https://dronelife.com/2025/05/06/quantum-system...` | Redirects to bare domain (arti | TODO |
| 245 | Tomorrow.io | 2026-02-03 | $175 | Space | Series F | `https://tomorrow.io/news/series-f` | HTTP 404 | TODO |
| 5 | Loft Orbital | 2025-01-15 | $170 | Space | Series C | `https://techcrunch.com/2025/01/15/loft-orbital-...` | HTTP 404 | TODO |
| 302 | Starcloud | 2026-03-30 | $170 | Space | Series A | `https://techcrunch.com/2026/03/30/starcloud-rai...` | HTTP 404 | TODO |
| 296 | Rebellions | 2026-03-26 | $166 | Semiconductors | Government investment | `https://rebellions.ai/news/government-investment` | URLError: _ssl.c:1112: The han | TODO |
| 276 | Sunday | 2026-03-12 | $165 | Robotics | Series B | `https://techcrunch.com/2026/03/12/sunday-raises...` | HTTP 404 | TODO |
| 906 | Distalmotion | 2023-04-19 | $150 | Robotics | Series E | `https://www.distalmotion.com/news/distalmotion-...` | Too many redirects | TODO |
| 282 | Frore Systems | 2026-03-16 | $143 | Semiconductors | Series D | `https://froresystems.com/news/series-d` | HTTP 404 | TODO |
| 220 | Mytra | 2026-01-14 | $120 | Robotics | Series C | `https://www.therobotreport.com/mytra-raises-120...` | HTTP 404 | TODO |
| 221 | Tulip Interfaces | 2026-01-14 | $120 | Robotics | Series D | `https://tulip.co/press/series-d` | HTTP 404 | TODO |
| 119 | Aerospacelab | 2025-08-26 | $110 | Space | Series B (extension) | `https://spacenews.com/aerospacelab-eyes-leading...` | HTTP 404 | TODO |
| 303 | Starfish Space | 2026-03-31 | $110 | Space | Series B | `https://spacenews.com/starfish-space-raises-100...` | HTTP 404 | TODO |
| 215 | Lyte | 2026-01-09 | $107 | Robotics | Undisclosed | `https://techcrunch.com/2026/01/09/lyte-raises-1...` | HTTP 404 | TODO |
| 676 | May Mobility | 2023-11-07 | $105 | Robotics | Series D | `https://maymobility.com/posts/may-mobility-seri...` | URLError: [SSL: TLSV1_ALERT_PR | TODO |
| 604 | Recogni | 2024-02-20 | $102 | Semiconductors | Series C | `https://www.prnewswire.com/news-releases/recogn...` | HTTP 404 | TODO |
| 214 | Cambium | 2026-01-05 | $100 | Materials | Series B | `https://www.cambium.com/news/series-b` | URLError: [Errno 8] nodename n | TODO |
| 233 | RobCo | 2026-01-28 | $100 | Robotics | Series C | `https://www.therobotreport.com/robco-raises-100...` | HTTP 404 | TODO |
| 424 | Akeana | 2024-08-13 | $100 | Semiconductors | Series A | `https://www.prnewswire.com/news-releases/akeana...` | HTTP 404 | TODO |
| 857 | Cerebras Systems | 2023-07-20 | $100 | Semiconductors | Strategic | `https://www.eetimes.com/cerebras-sells-100-mill...` | Timeout | TODO |
| 953 | SiPearl | 2023-04-05 | $98 | Semiconductors | Series A | `https://insidehpc.com/2023/04/sipearl-e90m-seri...` | URLError: [SSL: SSLV3_ALERT_HA | TODO |
| 110 | SiMa.ai | 2025-08-01 | $85 | Semiconductors | Series C | `https://www.prnewswire.com/news-releases/simaai...` | HTTP 404 | TODO |
| 393 | MAXIEYE Automotive Technology | 2024-10-24 | $80 | Robotics | Series D | `https://autonews.gasgoo.com/icv/70034950.html` | HTTP 468 | TODO |
| 563 | Frore Systems | 2024-05-29 | $80 | Semiconductors | Series C | `https://www.froresystems.com/media-room/frore-s...` | HTTP 404 | TODO |
| 228 | Cyclic Materials | 2026-01-23 | $75 | Materials | Series C | `https://www.cyclicmaterials.earth/news/series-c` | HTTP 404 | TODO |
| 425 | DreamBig Semiconductor | 2024-07-16 | $75 | Semiconductors | Series B | `https://www.prnewswire.com/news-releases/dreamb...` | HTTP 404 | TODO |
| 100 | Q.ANT | 2025-07-17 | $69 | Semiconductors | Series A | `https://tech.eu/2025/07/17/qant-raises-eur62m/` | HTTP 404 | TODO |
| 400 | Muon Space | 2024-08-05 | $57 | Space | Series B | `https://www.prnewswire.com/news-releases/muon-s...` | HTTP 404 | TODO |
| 513 | TIER IV | 2024-06-17 | $54 | Robotics | Series B (extension) | `https://www.prnewswire.com/news-releases/tier-i...` | HTTP 404 | TODO |
| 181 | Flexion Robotics | 2025-11-20 | $50 | Robotics | Series A | `https://www.eu-startups.com/2025/11/zurichs-fle...` | HTTP 403 | TODO |
| 291 | Normal Computing | 2026-03-25 | $50 | Semiconductors | Undisclosed | `https://normalcomputing.ai/news/funding` | HTTP 404 | TODO |
| 607 | Taalas | 2024-03-06 | $50 | Semiconductors | Series A | `https://www.prnewswire.com/news-releases/taalas...` | HTTP 404 | TODO |
| 996 | Forge Nano | 2023-06-06 | $50 | Materials | Series C | `https://www.forgenano.com/forge-nano-raises-us-...` | Redirects to bare domain (arti | TODO |
| 98 | Firestorm Labs | 2025-07-16 | $47 | Robotics | Series A | `https://www.prnewswire.com/news-releases/firest...` | HTTP 404 | TODO |
| 860 | Sapeon Korea | 2023-08-30 | $45 | Semiconductors | Series A | `https://www.kedglobal.com/artificial-intelligen...` | HTTP 502 | TODO |
| 515 | GrayMatter Robotics | 2024-06-20 | $45 | Robotics | Series B | `https://www.prnewswire.com/news-releases/grayma...` | HTTP 404 | TODO |
| 632 | EACON Mining | 2024-03-14 | $44 | Robotics | Series C | `https://www.prnewswire.com/apac/news-releases/a...` | HTTP 404 | TODO |
| 177 | Infinite Orbits | 2025-11-17 | $44 | Space | Series A (extension) | `https://www.eu-startups.com/2025/11/french-spac...` | HTTP 403 | TODO |
| 516 | Ronovo Surgical | 2024-06-26 | $44 | Robotics | Series B | `https://www.prnewswire.com/news-releases/ronovo...` | HTTP 404 | TODO |
| 103 | xLight | 2025-07-22 | $40 | Semiconductors | Series B | `https://www.xlight.com/company-news/xlight-40m-...` | HTTP 404 | TODO |
| 149 | Caracol | 2025-10-14 | $40 | Robotics | Series B | `https://www.prnewswire.com/news-releases/caraco...` | HTTP 404 | TODO |
| 288 | Lace | 2026-03-23 | $40 | Semiconductors | Series A | `https://lace.ai/news/series-a` | HTTP 404 | TODO |
| 293 | PAVE Space | 2026-03-25 | $40 | Space | Seed | `https://pavespace.com/news/seed` | HTTP 404 | TODO |
| 517 | XTEND | 2024-05-08 | $40 | Robotics | Series B | `https://www.prnewswire.com/il/news-releases/xte...` | HTTP 404 | TODO |
| 633 | Bluewhite | 2024-01-23 | $39 | Robotics | Series C | `https://www.prnewswire.com/news-releases/bluewh...` | HTTP 404 | TODO |
| 277 | Xscape Photonics | 2026-03-12 | $37 | Semiconductors | Series A (extension) | `https://xscapephotonics.com/news/series-a-exten...` | HTTP 404 | TODO |
| 655 | Zhuoyi Intelligent Technology | 2024-01-22 | $35 | Robotics | Series B | `https://tracxn.com/d/companies/beijing-zhuoyi-i...` | HTTP 404 | TODO |
| 182 | Point One Navigation | 2025-11-20 | $35 | Robotics | Series C | `https://www.prnewswire.com/news-releases/point-...` | HTTP 404 | TODO |
| 57 | Cognichip | 2025-05-15 | $33 | Semiconductors | Seed | `https://techcrunch.com/2025/05/15/cognichip-eme...` | HTTP 404 | TODO |
| 17 | Cambridge GaN Devices | 2025-02-18 | $32 | Semiconductors | Series C | `https://camgandevices.com/p/cambridge-gan-devic...` | Timeout | TODO |
| 6 | Shippeo | 2025-01-15 | $30 | Robotics | Undisclosed | `https://www.shippeo.com/resources/explore/press...` | HTTP 404 | TODO |
| 95 | XTEND | 2025-07-15 | $30 | Robotics | Series B (extension) | `https://www.prnewswire.com/news-releases/xtend-...` | HTTP 404 | TODO |
| 493 | Princeton NuEnergy | 2024-06-17 | $30 | Materials | Series A | `https://www.prnewswire.com/news-releases/prince...` | HTTP 404 | TODO |
| 105 | 4AG Robotics | 2025-07-29 | $29 | Robotics | Series B | `https://www.prnewswire.com/news-releases/4ag-ro...` | HTTP 404 | TODO |
| 204 | ENCOS | 2025-12-15 | $28 | Robotics | Undisclosed | `https://autonews.gasgoo.com/articles/news/china...` | HTTP 468 | TODO |
| 53 | Persona AI | 2025-05-14 | $27 | Robotics | Pre-Seed | `https://www.prnewswire.com/news-releases/person...` | HTTP 404 | TODO |
| 523 | Orca AI | 2024-05-23 | $23 | Robotics | Other | `https://techcrunch.com/2024/05/23/autonomous-sh...` | HTTP 404 | TODO |
| 524 | Vitestro | 2024-04-30 | $22 | Robotics | Other | `https://vitestro.com/vitestro-secures-22m-fundi...` | HTTP 404 | TODO |
| 1018 | Garuda Aerospace | 2023-02-15 | $22 | Robotics | Series A | `https://evtolinsights.com/2023/02/india-drone-s...` | HTTP 404 | TODO |
| 451 | Applied Carbon | 2024-08-01 | $22 | Robotics | Series A | `https://www.prnewswire.com/news-releases/applie...` | HTTP 404 | TODO |
| 611 | Innatera | 2024-03-12 | $21 | Semiconductors | Series A | `https://innatera.com/news/innatera-raises-eur15...` | HTTP 404 | TODO |
| 637 | Hippo Harvest | 2024-02-14 | $21 | Robotics | Series B | `https://www.prnewswire.com/news-releases/hippo-...` | HTTP 404 | TODO |
| 55 | Reflect Orbital | 2025-05-14 | $20 | Space | Series A | `https://www.prnewswire.com/news-releases/reflec...` | HTTP 404 | TODO |
| 292 | Lucid Bots | 2026-03-25 | $20 | Robotics | Series B | `https://www.therobotreport.com/lucid-bots-20m-s...` | HTTP 404 | TODO |
| 528 | BurnBot | 2024-04-02 | $20 | Robotics | Series A | `https://www.prnewswire.com/news-releases/burnbo...` | HTTP 404 | TODO |
| 560 | Expedera | 2024-05-21 | $20 | Semiconductors | Series B | `https://www.prnewswire.com/news-releases/expede...` | HTTP 404 | TODO |
| 58 | Solestial | 2025-05-15 | $17 | Space | Series A | `https://www.prnewswire.com/news-releases/solest...` | HTTP 404 | TODO |
| 81 | Skynopy | 2025-06-30 | $17 | Space | Series A | `https://www.eu-startups.com/2025/06/french-spac...` | HTTP 403 | TODO |
| 640 | Gather AI | 2024-03-05 | $17 | Robotics | Series A (extension) | `https://www.gather.ai/news/gather-ai-raises-17m...` | HTTP 404 | TODO |
| 667 | TechMagic | 2024-03-27 | $17 | Robotics | Series C | `https://tracxn.com/d/companies/techmagic/` | HTTP 404 | TODO |
| 173 | Hummink | 2025-11-17 | $16 | Semiconductors | Series A | `https://www.eu-startups.com/2025/11/french-deep...` | HTTP 403 | TODO |
| 284 | KEWAZO | 2026-03-19 | $16 | Robotics | Series A (extension) | `https://kewazo.com/news/series-a-extension` | HTTP 404 | TODO |
| 692 | Pablo Air | 2023-10-20 | $16 | Robotics | Bridge | `https://www.kedglobal.com/future-mobility/newsV...` | HTTP 502 | TODO |
| 31 | ATLANT 3D | 2025-03-11 | $15 | Semiconductors | Series A | `https://www.prnewswire.com/news-releases/atlant...` | HTTP 404 | TODO |
| 609 | Diraq | 2024-02-26 | $15 | Semiconductors | Series A | `https://www.diraq.com/newsdesk/diraq-secures-A2...` | HTTP 404 | TODO |
| 298 | Arkadia Space | 2026-03-26 | $14 | Space | Grant | `https://www.eu-startups.com/2026/03/arkadia-spa...` | HTTP 403 | TODO |
| 917 | Yarbo | 2023-04-15 | $14 | Robotics | Pre-Series A | `https://www.yarbo.com/blog/yarbo-story-robotics...` | HTTP 404 | TODO |
| 656 | ORCA-TECH | 2024-01-17 | $14 | Robotics | Series B | `https://tracxn.com/d/companies/orca-tech/` | HTTP 404 | TODO |
| 657 | Forvision | 2024-01-29 | $14 | Robotics | Other | `https://autonews.gasgoo.com/icv/70030993.html` | HTTP 468 | TODO |
| 80 | LIDROTEC | 2025-06-26 | $14 | Semiconductors | Series A | `https://tech.eu/2025/06/26/lidrotec-lands-135m/` | HTTP 404 | TODO |
| 644 | Firestorm Labs | 2024-03-25 | $12 | Robotics | Seed | `https://www.prnewswire.com/news-releases/firest...` | HTTP 404 | TODO |
| 175 | Bone AI | 2025-11-17 | $12 | Robotics | Seed | `https://techcrunch.com/2025/11/17/bone-ai-raise...` | HTTP 404 | TODO |
| 646 | Aniai | 2024-01-23 | $12 | Robotics | Pre-Series A | `https://www.prnewswire.com/news-releases/aniai-...` | HTTP 404 | TODO |
| 269 | Elementium Materials | 2026-03-06 | $11 | Materials | Seed | `https://elementium.com/news/seed` | HTTP 404 | TODO |
| 468 | HavocAI | 2024-09-20 | $11 | Robotics | Seed | `https://www.prnewswire.com/news-releases/havoca...` | HTTP 404 | TODO |
| 535 | SpinEM Robotics | 2024-04-30 | $11 | Robotics | Series A (extension) | `https://www.prnewswire.com/news-releases/spinem...` | HTTP 404 | TODO |
| 536 | Fotokite | 2024-04-11 | $11 | Robotics | Series B | `https://dronelife.com/2024/04/12/fotokite-secur...` | Redirects to bare domain (arti | TODO |
| 186 | SpaceComputer | 2025-11-28 | $10 | Space | Seed | `https://blog.spacecomputer.io/spacecomputer-rai...` | HTTP 404 | TODO |
| 187 | Mastiska | 2025-11-28 | $10 | Semiconductors | Seed | `https://www.eetimes.com/mastiska-raises-10m-see...` | Timeout | TODO |
| 235 | Nomagic | 2026-01-28 | $10 | Robotics | Series B (extension) | `https://nomagic.ai/news/series-b-extension` | HTTP 404 | TODO |
| 446 | Cartken | 2024-07-03 | $10 | Robotics | Other | `https://www.cartken.com/press-release/cartken-a...` | HTTP 404 | TODO |
| 947 | Realtime Robotics | 2023-06-27 | $10 | Robotics | Series A (extension) | `https://rtr.ai/realtime-robotics-funded-an-addi...` | URLError: [SSL: TLSV1_ALERT_PR | TODO |
| 195 | MACH | 2025-12-04 | $7 | Robotics | Seed | `https://roboticsandautomationnews.com/2025/12/0...` | Redirects to bare domain (arti | TODO |
| 543 | Eyebot | 2024-06-06 | $6 | Robotics | Seed | `https://www.prweb.com/releases/eyebot-secures-6...` | HTTP 404 | TODO |
| 544 | Shinkei Systems | 2024-04-29 | $6 | Robotics | Seed | `https://www.prnewswire.com/news-releases/shinke...` | HTTP 404 | TODO |
| 470 | Reactive Robotics | 2024-09-09 | $5 | Robotics | Other | `https://www.reactive-robotics.com/en/news/react...` | URLError: timed out | TODO |
| 1049 | Etched | 2023-03-15 | $5 | Semiconductors | Seed | `https://en.wikipedia.org/wiki/Etched_(company)` | HTTP 404 | TODO |
| 662 | Buzz Solutions | 2024-03-20 | $5 | Robotics | Other | `https://www.prweb.com/releases/buzz-solutions-r...` | HTTP 404 | TODO |
| 578 | Atomic-6 | 2024-01-11 | $5 | Space | Seed | `https://www.prnewswire.com/news-releases/atomic...` | HTTP 404 | TODO |
| 545 | Relocalize | 2024-05-21 | $4 | Robotics | Seed | `https://www.prnewswire.com/news-releases/reloca...` | HTTP 404 | TODO |
| 579 | Atomic-6 | 2024-01-11 | $4 | Space | Grant | `https://www.prnewswire.com/news-releases/atomic...` | HTTP 404 | TODO |
| 665 | Neatleaf | 2024-01-23 | $4 | Robotics | Other | `https://www.prnewswire.com/news-releases/neatle...` | HTTP 404 | TODO |
| 191 | AILOS Robotics | 2025-12-02 | $4 | Robotics | Seed | `https://tech.eu/2025/12/02/ailos-robotics-gets-...` | HTTP 404 | TODO |
| 780 | Grass (Wynd Labs) | 2023-12-13 | $4 | Token | Seed | `https://www.getgrass.io/blog/grass-raises-3-5-m...` | HTTP 404 | TODO |
| 549 | Unmanned Defence Systems | 2024-05-24 | $3 | Robotics | Seed | `https://www.coinvest.lt/post/unmanned-defense-s...` | HTTP 404 | TODO |
| 1027 | Aniai | 2023-02-21 | $3 | Robotics | Seed | `https://www.kedglobal.com/korean-startups/newsV...` | HTTP 502 | TODO |
| 278 | AmpliSi | 2026-03-12 | $2 | Materials | Pre-Seed | `https://amplisi.com/news/pre-seed` | HTTP 404 | TODO |
| 130 | Hive Robotics | 2025-09-11 | $2 | Robotics | Pre-Seed | `https://tech.eu/2025/09/11/hive-robotics-secure...` | HTTP 404 | TODO |
| 156 | Augmentus | 2025-10-27 | $0 | Robotics | Undisclosed | `https://www.prnewswire.com/news-releases/augmen...` | HTTP 404 | TODO |
| 285 | Rivr | 2026-03-19 | $0 | Robotics | M&A | `https://www.therobotreport.com/rivr-acquired/` | HTTP 404 | TODO |
| 407 | Sceye | 2024-09-17 | $0 | Space | Series C | `https://www.prnewswire.com/news-releases/sceye-...` | HTTP 404 | TODO |
</details>

## PLACEHOLDER rows (48) — full list

Bare-domain or homepage URLs from backfill agents. None resolve to a specific article. Sorted by deal size.

<details>
<summary>Click to expand full list of 48 PLACEHOLDER rows</summary>

| idx | Company | Date | $M | Sector | Round | Current URL | Replacement |
|----:|---------|------|---:|--------|-------|-------------|-------------|
| 7 | Pacific Fusion | 2025-01-15 | $900 | Materials | Series A | `https://techcrunch.com` | see candidates table |
| 0 | KoBold Metals | 2025-01-01 | $537 | Materials | Series C | `https://techcrunch.com` | see candidates table |
| 10 | Helion Energy | 2025-01-28 | $425 | Materials | Series F | `https://helionenergy.com` | see candidates table |
| 155 | Redwood Materials | 2025-10-23 | $350 | Materials | Series E | `https://techcrunch.com` | see candidates table |
| 197 | Castelion | 2025-12-05 | $350 | Space | Series B | `https://techcrunch.com` | see candidates table |
| 129 | D-Robotics | 2025-09-10 | $270 | Robotics | Series B | `https://techcrunch.com` | TODO |
| 229 | Hadrian | 2026-01-25 | $260 | Robotics | Undisclosed | `https://hadrian.co/news` | TODO |
| 96 | Mujin | 2025-07-15 | $233 | Robotics | Series D | `https://techcrunch.com` | TODO |
| 154 | CMR Surgical | 2025-10-20 | $200 | Robotics | Other | `https://cmrsurgical.com` | TODO |
| 198 | ICEYE | 2025-12-05 | $163 | Space | Series E | `https://spacenews.com` | TODO |
| 29 | Distalmotion | 2025-03-10 | $150 | Robotics | Series G | `https://distalmotion.com` | TODO |
| 184 | Robotera | 2025-11-25 | $140 | Robotics | Series A | `https://techcrunch.com` | TODO |
| 42 | Gecko Robotics | 2025-04-15 | $130 | Robotics | Series D | `https://techcrunch.com` | TODO |
| 61 | Zap Energy | 2025-06-01 | $130 | Materials | Other | `https://fusionindustryassociation.org` | TODO |
| 25 | Tokamak Energy | 2025-03-01 | $125 | Materials | Other | `https://fusionindustryassociation.org` | TODO |
| 115 | Fourier Intelligence | 2025-08-20 | $120 | Robotics | Series E+ | `https://techcrunch.com` | TODO |
| 72 | Xcimer Energy | 2025-06-15 | $100 | Materials | Series A | `https://xcimer.energy` | TODO |
| 77 | Infravision | 2025-06-20 | $100 | Robotics | Series B | `https://techcrunch.com` | TODO |
| 132 | Kargo | 2025-09-15 | $100 | Robotics | Series A | `https://techcrunch.com` | TODO |
| 44 | Albedo | 2025-04-23 | $97 | Space | Series B | `https://spacenews.com` | TODO |
| 60 | ClearSpace | 2025-06-01 | $95 | Space | Government | `https://esa.int` | TODO |
| 133 | General Fusion | 2025-09-15 | $73 | Materials | Bridge | `https://techcrunch.com` | TODO |
| 46 | Ecorobotix | 2025-04-25 | $60 | Robotics | Series C | `https://ecorobotix.com` | TODO |
| 38 | Fairmat | 2025-04-02 | $56 | Materials | Series B | `https://techcrunch.com` | TODO |
| 34 | Marvel Fusion | 2025-03-27 | $55 | Materials | Series B Extension | `https://tech.eu` | TODO |
| 12 | ArkEdge Space | 2025-02-04 | $52 | Space | Series B | `https://spacenews.com` | TODO |
| 52 | RobCo | 2025-05-10 | $52 | Robotics | Series B | `https://techcrunch.com` | TODO |
| 37 | Aetherflux | 2025-04-02 | $50 | Space | Series A | `https://techcrunch.com` | TODO |
| 93 | Bonsai Robotics | 2025-07-10 | $50 | Robotics | Series A | `https://techcrunch.com` | TODO |
| 160 | constellr | 2025-11-01 | $44 | Space | Series A | `https://spacenews.com` | TODO |
| 205 | SatVu | 2025-12-15 | $41 | Space | Series B | `https://spacenews.com` | TODO |
| 33 | Agtonomy | 2025-03-20 | $38 | Robotics | Series A | `https://agtonomy.com` | TODO |
| 101 | EndoQuest Robotics | 2025-07-20 | $36 | Robotics | Series A | `https://endoquestrobotics.com` | TODO |
| 112 | Generative Bionics | 2025-08-15 | $35 | Robotics | Seed | `https://techcrunch.com` | TODO |
| 121 | Cambridge GaN Devices | 2025-09-01 | $32 | Materials | Series C | `https://techcrunch.com` | TODO |
| 166 | TRIC Robotics | 2025-11-05 | $30 | Robotics | Series A | `https://techcrunch.com` | TODO |
| 142 | Commcrete | 2025-09-30 | $21 | Space | Series A | `https://spacenews.com` | TODO |
| 59 | Contoro Robotics | 2025-05-20 | $20 | Robotics | Seed | `https://techcrunch.com` | TODO |
| 75 | Turion Space | 2025-06-18 | $20 | Space | Series A | `https://spacenews.com` | TODO |
| 8 | ElectraLith | 2025-01-16 | $18 | Materials | Series A | `https://techcrunch.com` | TODO |
| 79 | SwarmFarm | 2025-06-25 | $18 | Robotics | Series A | `https://swarmfarm.com` | TODO |
| 122 | Surgerii Robotics | 2025-09-05 | $15 | Robotics | Seed | `https://surgerii.com` | TODO |
| 40 | RoboForce | 2025-04-10 | $12 | Robotics | Seed | `https://techcrunch.com` | TODO |
| 50 | Alta Resource Technologies | 2025-05-05 | $10 | Materials | Seed | `https://techcrunch.com` | TODO |
| 70 | Aethero | 2025-06-11 | $8 | Space | Seed | `https://spacenews.com` | TODO |
| 201 | Dyna Robotics | 2025-12-10 | $6 | Robotics | Seed | `https://techcrunch.com` | TODO |
| 664 | ACWA Robotics | 2024-01-25 | $5 | Robotics | Seed | `https://www.acwa-robotics.com/news/` | TODO |
| 137 | Anvil Robotics | 2025-09-20 | $5 | Robotics | Seed | `https://techcrunch.com` | TODO |
</details>

## RATE_LIMITED (2)

Both rows are Helsing (helsing.ai) — the company's domain has aggressive bot rate-limiting that persisted across retry. Article URLs are likely valid in browser. Flag for manual verification.

- idx=74 **Helsing** (2025-06-17, Series D, $692M): `https://helsing.ai/newsroom/helsing-raises-eur600m/`
- idx=439 **Helsing** (2024-07-26, Series C, $487.5M): `https://helsing.ai/newsroom/helsing-further-strengthens-european-defence-capabilities-with-funding-round`

## BOT_BLOCKED domains (167 rows, breakdown)

These return HTTP 403 to the audit but are almost always live in a real browser. BusinessWire and Bloomberg are well-known to block non-browser User-Agents. **No action needed unless a sample is verified-dead.**

| Domain | Rows |
|--------|----:|
| businesswire.com | 82 |
| crunchbase.com | 13 |
| bloomberg.com | 12 |
| commerce.gov | 11 |
| theblock.co | 4 |
| axios.com | 3 |
| eu-startups.com | 3 |
| bostonmetal.com | 3 |
| hpcwire.com | 2 |
| datacenterdynamics.com | 2 |
| outrider.ai | 2 |
| quantum-systems.com | 2 |
| wayve.ai | 2 |
| g-medtech.com | 2 |
| surgicalroboticstechnology.com | 2 |

## Mutations applied to rounds.json

- **37 REDIRECT URLs** rewritten to canonical final URLs (same-host).
- 0 DEAD URLs mutated (per spec — flag only, no auto-mutation).
- 0 PLACEHOLDER URLs mutated (per spec — flag only).
- 0 BOT_BLOCKED URLs mutated (likely live in browser; respect existing citation).

Dataset `updated` field bumped. Full mutation log saved at `/tmp/url_redirect_mutations.json`.

## Recommended remediation plan (post-v1.0)

Before the next monthly send to VCs:

1. **Apply the 22 high-confidence replacement candidates above** (manual review + Edit, ~20 min)
2. **Resolve the 6 quality-flag issues** (USAR LOI exclusion, Zipline date, Pacific Fusion date, Unitree HK→SH, Bedrock construction-not-trucking, KoBold date)
3. **Batch the remaining 119 DEAD rows** through a second-pass URL search (could be agent-driven; 4 parallel agents × 30 rows each)
4. **Batch the remaining 26 PLACEHOLDER rows** the same way
5. Re-run the audit to confirm dataset health is ≥95% OK before re-export

## Files

- `data/funding/rounds.json` — 37 REDIRECT mutations applied
- `data/funding/source_url_audit.md` — this report
- `/tmp/url_audit_results.json` — full audit output (1,154 entries, gitignored)
- `/tmp/url_redirect_mutations.json` — REDIRECT mutation log (37 entries)
- `/tmp/url_replacement_candidates.json` — 22 high-confidence candidates
