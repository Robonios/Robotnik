# v1.0 URL Replacements Pending Approval
**Date:** 2026-05-06
**Scope:** 104 in-scope rows (per URL freshness rule: date within 365 days OR amount_m ≥ $500M)

## Summary
| Confidence | Rows | Treatment if approved |
|---|---:|---|
| HIGH | 84 | Mutate `source` → replacement URL; `source_status` → `verified` |
| MEDIUM | 6 | Mutate w/ caveat (paywall or aggregator) |
| LOW | 14 | Leave as-is; `source_status` stays `pending`; flag for manual triage |
| **Total** | **104** | |

## Data quality concerns

⚠️ **The agent surfaced 28 substantive data-quality issues** beyond just URL rot — wrong dates, wrong amounts, or rounds that don't correspond to any real announcement. See companion file [`v1_0_data_quality_issues.md`](v1_0_data_quality_issues.md) for the full triage list.

Some HIGH-confidence URL finds also have date/amount mismatches that should be fixed alongside the URL mutation.

## HIGH confidence — proposed URL mutations (84)

Sorted by `amount_m` descending. URL verified live by agent. **Approval recommended unless data-quality flag in last column.**

| idx | entity_id | Company | Date | $M | Sector | Round | Current → Proposed | DQ flag |
|----:|-----------|---------|------|---:|--------|-------|-------------------|---------|
| 593 | `LAC` | Lithium Americas | 2024-03-12 | $2260 | Materials | Government investment | `https://www.energy.gov/lpo/articles/l...` → `https://lithiumamericas.com/news/news-details/2...` | ⚠️ Company press release is more stable canonical source than DOE LPO link |
| 268 | `nscale` | Nscale | 2026-03-09 | $2000 | Semiconductors | Series C | `https://nscale.com/news/series-c` → `https://www.nscale.com/press-releases/nscale-se...` |  |
| 295 | `shield-ai` | Shield AI | 2026-03-26 | $2000 | Robotics | Series G | `https://techstartups.com/2026/03/26/d...` → `https://shield.ai/shield-ai-to-acquire-software...` |  |
| 265 | `neura-robotics` | NEURA Robotics | 2026-03-04 | $1200 | Robotics | Undisclosed | `https://www.therobotreport.com/neura-...` → `https://siliconangle.com/2026/03/04/humanoid-ro...` |  |
| 909 | `42dot` | 42dot | 2023-04-26 | $787 | Robotics | Strategic | `https://www.kedglobal.com/automobiles...` → `https://www.marketscreener.com/quote/stock/HYUN...` |  |
| 135 | `groq` | Groq | 2025-09-17 | $750 | Semiconductors | Series E | `https://techcrunch.com/2025/09/17/nvi...` → `https://groq.com/newsroom/groq-raises-750-milli...` |  |
| 74 | `helsing` | Helsing | 2025-06-17 | $692 | Robotics | Series D | `https://helsing.ai/newsroom/helsing-r...` → `https://helsing.ai/newsroom/helsing-raises-eur6...` | ⚠️ Original URL was incomplete slug; full canonical slug confirmed |
| 73 | `applied-intuition` | Applied Intuition | 2025-06-17 | $600 | Robotics | Series F | `https://techcrunch.com/2025/06/17/app...` → `https://www.appliedintuition.com/press-releases...` |  |
| 262 | `sierra-space` | Sierra Space | 2026-03-03 | $550 | Space | Series C | `https://spacenews.com/sierra-space-55...` → `https://www.sierraspace.com/press-releases/sier...` |  |
| 264 | `vast` | Vast | 2026-03-03 | $500 | Space | Series A | `https://spacenews.com/vast-500m-serie...` → `https://www.vastspace.com/updates/vast-secures-...` |  |
| 273 | `mind-robotics` | Mind Robotics | 2026-03-11 | $500 | Robotics | Series A | `https://www.therobotreport.com/mind-r...` → `https://techcrunch.com/2026/03/11/rivian-mind-r...` |  |
| 278 | `doe-cmei-program` | DOE CMEI Program | 2026-03-13 | $500 | Materials | Grant | `https://www.energy.gov/articles/doe-c...` → `https://www.energy.gov/articles/energy-departme...` | ⚠️ Full DOE article URL confirmed |
| 270 | `rhoda-ai` | Rhoda AI | 2026-03-10 | $450 | Robotics | Undisclosed | `https://www.therobotreport.com/rhoda-...` → `https://siliconangle.com/2026/03/10/rhoda-ai-ra...` | ⚠️ Round was Series A (not Undisclosed as recorded); 1.7B valuation |
| 155 | `redwood-materials` | Redwood Materials | 2025-10-23 | $350 | Materials | Series E | `https://techcrunch.com` → `https://www.redwoodmaterials.com/news/redwood-a...` |  |
| 196 | `castelion` | Castelion | 2025-12-05 | $350 | Space | Series B | `https://techcrunch.com` → `https://www.castelion.com/news/series-b/` |  |
| 244 | `axiom-space` | Axiom Space | 2026-02-12 | $350 | Space | Debt Financing | `https://spacenews.com/axiom-space-350...` → `https://www.axiomspace.com/release/axiom-space-...` | ⚠️ Round was mix of equity and debt, not pure debt financing |
| 211 | `galbot` | Galbot | 2025-12-19 | $300 | Robotics | Undisclosed | `https://www.prnewswire.com/news-relea...` → `https://www.prnewswire.com/news-releases/galbot...` |  |
| 88 | `geekplus` | Geekplus | 2025-07-09 | $281 | Robotics | IPO | `https://www.prnewswire.com/news-relea...` → `https://www.geekplus.com/resources/news/geekplu...` |  |
| 227 | `hadrian` | Hadrian | 2026-01-25 | $260 | Robotics | Undisclosed | `https://hadrian.co/news` → `https://www.washingtontechnology.com/companies/...` | ⚠️ DATA QUALITY: Hadrian 260M Series C was July 2025, not January 2026 |
| 201 | `k2-space` | K2 Space | 2025-12-11 | $250 | Space | Series C | `https://www.prnewswire.com/news-relea...` → `https://www.prnewswire.com/news-releases/k2-spa...` |  |
| 96 | `mujin` | Mujin | 2025-07-15 | $233 | Robotics | Series D | `https://techcrunch.com` → `https://mujin-corp.com/resources/news/seriesd-a...` | ⚠️ DATA QUALITY: Mujin 233M Series D announced December 2025, not July 2025 |
| 285 | `kandou-ai` | Kandou AI | 2026-03-23 | $225 | Semiconductors | Series A | `https://kandou.com/news/funding` → `https://siliconangle.com/2026/03/23/chip-interc...` |  |
| 266 | `pld-space` | PLD Space | 2026-03-04 | $209 | Space | Series C | `https://spacenews.com/pld-space-209m-...` → `https://spacenews.com/pld-space-raises-209-mill...` | ⚠️ Original SpaceNews URL was placeholder; full slug confirmed |
| 154 | `cmr-surgical` | CMR Surgical | 2025-10-20 | $200 | Robotics | Other | `https://cmrsurgical.com` → `https://us.cmrsurgical.com/news/cmr-surgical-se...` | ⚠️ DATA QUALITY: $200M was announced April 2025, not October 2025 |
| 269 | `eridu` | Eridu | 2026-03-10 | $200 | Semiconductors | Series A | `https://eridu.ai/news/series-a` → `https://techcrunch.com/2026/03/10/ai-network-st...` |  |
| 202 | `quantumdiamonds` | QuantumDiamonds | 2025-12-15 | $178 | Semiconductors | Government investment | `https://www.eu-startups.com/2025/12/q...` → `https://thequantuminsider.com/2025/12/15/qd-pla...` | ⚠️ 152M EUR (~178M USD) announced; partial government funding from Germany under EU... |
| 51 | `quantum-systems` | Quantum Systems | 2025-05-06 | $176 | Robotics | Series C | `https://dronelife.com/2025/05/06/quan...` → `https://quantum-systems.com/blog/2025/05/05/qua...` |  |
| 243 | `tomorrowio` | Tomorrow.io | 2026-02-03 | $175 | Space | Series F | `https://tomorrow.io/news/series-f` → `https://www.tomorrow.io/blog/tomorrow-io-announ...` |  |
| 300 | `starcloud` | Starcloud | 2026-03-30 | $170 | Space | Series A | `https://techcrunch.com/2026/03/30/sta...` → `https://techcrunch.com/2026/03/30/starcloud-rai...` | ⚠️ Original URL had similar but not exact slug; correct verbatim slug confirmed |
| 294 | `rebellions` | Rebellions | 2026-03-26 | $166 | Semiconductors | Government investment | `https://rebellions.ai/news/government...` → `https://www.thestar.com.my/tech/tech-news/2026/...` |  |
| 274 | `sunday` | Sunday | 2026-03-12 | $165 | Robotics | Series B | `https://techcrunch.com/2026/03/12/sun...` → `https://techcrunch.com/2026/03/12/humanoid-robo...` | ⚠️ Original URL had a placeholder slug; correct verbatim slug confirmed |
| 280 | `frore-systems` | Frore Systems | 2026-03-16 | $143 | Semiconductors | Series D | `https://froresystems.com/news/series-d` → `https://www.froresystems.com/media-room/frore-s...` |  |
| 183 | `robotera` | Robotera | 2025-11-25 | $140 | Robotics | Series A | `https://techcrunch.com` → `https://www.therobotreport.com/robotera-gets-se...` |  |
| 61 | `zap-energy` | Zap Energy | 2025-06-01 | $130 | Materials | Other | `https://fusionindustryassociation.org` → `https://www.zapenergy.com/news/zap-attracts-130...` | ⚠️ DATA QUALITY: $130M Series D announced October 2024, not June 2025 |
| 219 | `mytra` | Mytra | 2026-01-14 | $120 | Robotics | Series C | `https://www.therobotreport.com/mytra-...` → `https://fortune.com/2026/01/15/mytra-raises-120...` |  |
| 220 | `tulip-interfaces` | Tulip Interfaces | 2026-01-14 | $120 | Robotics | Series D | `https://tulip.co/press/series-d` → `https://tulip.co/press/tulip-secures-120m-serie...` | ⚠️ Original URL was incomplete slug; full slug confirmed |
| 119 | `aerospacelab` | Aerospacelab | 2025-08-26 | $110 | Space | Series B (extension) | `https://spacenews.com/aerospacelab-ey...` → `https://www.aerospacelab.com/blog/press-release...` | ⚠️ Original SpaceNews URL has IRIS-squared char issues; company release is more sta... |
| 301 | `starfish-space` | Starfish Space | 2026-03-31 | $110 | Space | Series B | `https://spacenews.com/starfish-space-...` → `https://www.starfishspace.com/press-release/sta...` | ⚠️ DATA QUALITY: Round announced April 2026, not March 31 2026 |
| 214 | `lyte` | Lyte | 2026-01-09 | $107 | Robotics | Undisclosed | `https://techcrunch.com/2026/01/09/lyt...` → `https://www.therobotreport.com/lyte-brings-in-1...` | ⚠️ DATA QUALITY: Lyte announced January 5, 2026 not Jan 9 |
| 72 | `xcimer-energy` | Xcimer Energy | 2025-06-15 | $100 | Materials | Series A | `https://xcimer.energy` → `https://xcimer.energy/news/100-million-raised-t...` |  |
| 77 | `infravision` | Infravision | 2025-06-20 | $100 | Robotics | Series B | `https://techcrunch.com` → `https://www.infravisioninc.com/insights/infravi...` | ⚠️ DATA QUALITY: Infravision $91M Series B was announced November 2025, not June 20... |
| 213 | `cambium` | Cambium | 2026-01-05 | $100 | Materials | Series B | `https://www.cambium.com/news/series-b` → `https://www.compositesworld.com/news/cambiums-1...` | ⚠️ Note: Cambium here is the advanced materials/composites company (8VC-led), NOT t... |
| 231 | `robco` | RobCo | 2026-01-28 | $100 | Robotics | Series C | `https://www.therobotreport.com/robco-...` → `https://www.rob.co/en-us/company/press/robco-se...` |  |
| 110 | `simaai` | SiMa.ai | 2025-08-01 | $85 | Semiconductors | Series C | `https://www.prnewswire.com/news-relea...` → `https://sima.ai/press-release/sima-ai-raises-85...` |  |
| 226 | `cyclic-materials` | Cyclic Materials | 2026-01-23 | $75 | Materials | Series C | `https://www.cyclicmaterials.earth/new...` → `https://cyclicmaterials.earth/resources/cyclic-...` |  |
| 100 | `qant` | Q.ANT | 2025-07-17 | $69 | Semiconductors | Series A | `https://tech.eu/2025/07/17/qant-raise...` → `https://qant.com/press-releases/qant-raises-62-...` | ⚠️ 62M EUR (~69M USD) |
| 180 | `flexion-robotics` | Flexion Robotics | 2025-11-20 | $50 | Robotics | Series A | `https://www.eu-startups.com/2025/11/z...` → `https://flexion.ai/news/flexion-raises-50m-to-b...` |  |
| 289 | `normal-computing` | Normal Computing | 2026-03-25 | $50 | Semiconductors | Undisclosed | `https://normalcomputing.ai/news/funding` → `https://fortune.com/2026/03/25/normal-computing...` |  |
| 98 | `firestorm-labs` | Firestorm Labs | 2025-07-16 | $47 | Robotics | Series A | `https://www.prnewswire.com/news-relea...` → `https://www.launchfirestorm.com/news/firestorm-...` |  |
| 160 | `constellr` | constellr | 2025-11-01 | $44 | Space | Series A | `https://spacenews.com` → `https://www.constellr.com/article/constellr-sec...` | ⚠️ DATA QUALITY: constellr's 37M EUR (~44M USD) Series A was announced February 202... |
| 176 | `infinite-orbits` | Infinite Orbits | 2025-11-17 | $44 | Space | Series A (extension) | `https://www.eu-startups.com/2025/11/f...` → `https://www.infiniteorbits.io/post/space-sovere...` |  |
| 204 | `satvu` | SatVu | 2025-12-15 | $41 | Space | Series B | `https://spacenews.com` → `https://spacenews.com/satvu-to-expand-thermal-i...` | ⚠️ DATA QUALITY: SatVu's $41M (30M GBP) round was announced February 2026, not Dece... |
| 103 | `xlight` | xLight | 2025-07-22 | $40 | Semiconductors | Series B | `https://www.xlight.com/company-news/x...` → `https://www.xlight.com/company-news/xlight-40m-...` | ⚠️ Original URL appears canonical and confirmed via search |
| 149 | `caracol` | Caracol | 2025-10-14 | $40 | Robotics | Series B | `https://www.prnewswire.com/news-relea...` → `https://www.caracol-am.com/press-and-media/pres...` |  |
| 286 | `lace` | Lace | 2026-03-23 | $40 | Semiconductors | Series A | `https://lace.ai/news/series-a` → `https://techstartups.com/2026/03/23/microsoft-b...` | ⚠️ Lace is Norwegian chipmaking equipment startup (atom-beam lithography); domain i... |
| 291 | `pave-space` | PAVE Space | 2026-03-25 | $40 | Space | Seed | `https://pavespace.com/news/seed` → `https://spacenews.com/pave-space-raises-40-mill...` |  |
| 275 | `xscape-photonics` | Xscape Photonics | 2026-03-12 | $37 | Semiconductors | Series A (extension) | `https://xscapephotonics.com/news/seri...` → `https://siliconangle.com/2026/03/11/xscape-debu...` |  |
| 181 | `point-one-navigation` | Point One Navigation | 2025-11-20 | $35 | Robotics | Series C | `https://www.prnewswire.com/news-relea...` → `https://pointonenav.com/news/point-one-navigati...` |  |
| 57 | `cognichip` | Cognichip | 2025-05-15 | $33 | Semiconductors | Seed | `https://techcrunch.com/2025/05/15/cog...` → `https://techcrunch.com/2025/05/15/cognichip-eme...` | ⚠️ Original URL had partial slug; full slug confirmed |
| 121 | `cambridge-gan-devices` | Cambridge GaN Devices | 2025-09-01 | $32 | Materials | Series C | `https://techcrunch.com` → `https://camgandevices.com/p/cambridge-gan-devic...` | ⚠️ DATA QUALITY: CGD's $32M Series C closed February 2025, not September 2025 |
| 95 | `xtend` | XTEND | 2025-07-15 | $30 | Robotics | Series B (extension) | `https://www.prnewswire.com/news-relea...` → `https://www.therobotreport.com/xtend-secures-ex...` |  |
| 105 | `4ag-robotics` | 4AG Robotics | 2025-07-29 | $29 | Robotics | Series B | `https://www.prnewswire.com/news-relea...` → `https://4ag.ai/4ag-robotics-raises-29m-usd-seri...` | ⚠️ Note: $29M USD = CAD 40M |
| 53 | `persona-ai` | Persona AI | 2025-05-14 | $27 | Robotics | Pre-Seed | `https://www.prnewswire.com/news-relea...` → `https://www.therobotreport.com/persona-ai-raise...` |  |
| 142 | `commcrete` | Commcrete | 2025-09-30 | $21 | Space | Series A | `https://spacenews.com` → `https://www.armadainternational.com/2025/10/com...` |  |
| 55 | `reflect-orbital` | Reflect Orbital | 2025-05-14 | $20 | Space | Series A | `https://www.prnewswire.com/news-relea...` → `https://payloadspace.com/reflect-orbital-raises...` |  |
| 290 | `lucid-bots` | Lucid Bots | 2026-03-25 | $20 | Robotics | Series B | `https://www.therobotreport.com/lucid-...` → `https://techcrunch.com/2026/03/25/lucid-bots-ra...` |  |
| 58 | `solestial` | Solestial | 2025-05-15 | $17 | Space | Series A | `https://www.prnewswire.com/news-relea...` → `https://solestial.com/solestial-series-a-ceo/` |  |
| 81 | `skynopy` | Skynopy | 2025-06-30 | $17 | Space | Series A | `https://www.eu-startups.com/2025/06/f...` → `https://spacenews.com/skynopy-lays-foundation-f...` |  |
| 172 | `hummink` | Hummink | 2025-11-17 | $16 | Semiconductors | Series A | `https://www.eu-startups.com/2025/11/f...` → `https://www.eu-startups.com/2025/11/french-deep...` | ⚠️ Original URL had partial slug; full slug confirmed |
| 282 | `kewazo` | KEWAZO | 2026-03-19 | $16 | Robotics | Series A (extension) | `https://kewazo.com/news/series-a-exte...` → `https://www.axios.com/pro/supply-chain-deals/20...` |  |
| 296 | `arkadia-space` | Arkadia Space | 2026-03-26 | $14 | Space | Grant | `https://www.eu-startups.com/2026/03/a...` → `https://arkadiaspace.com/arkadia-space-secures-...` |  |
| 80 | `lidrotec` | LIDROTEC | 2025-06-26 | $14 | Semiconductors | Series A | `https://tech.eu/2025/06/26/lidrotec-l...` → `https://www.zeiss.com/corporate/en/about-zeiss/...` | ⚠️ Tech.eu URL similar to original; ZEISS investor announcement is alternative cano... |
| 174 | `bone-ai` | Bone AI | 2025-11-17 | $12 | Robotics | Seed | `https://techcrunch.com/2025/11/17/bon...` → `https://techcrunch.com/2025/11/17/bone-ai-raise...` | ⚠️ Original URL was a partial slug; full slug confirmed |
| 267 | `elementium-materials` | Elementium Materials | 2026-03-06 | $11 | Materials | Seed | `https://elementium.com/news/seed` → `https://www.axios.com/pro/climate-deals/2026/03...` |  |
| 185 | `spacecomputer` | SpaceComputer | 2025-11-28 | $10 | Space | Seed | `https://blog.spacecomputer.io/spaceco...` → `https://blog.spacecomputer.io/spacecomputer-rai...` | ⚠️ Original URL had partial slug; full slug confirmed |
| 186 | `mastiska` | Mastiska | 2025-11-28 | $10 | Semiconductors | Seed | `https://www.eetimes.com/mastiska-rais...` → `https://www.eetimes.com/mastiska-raises-10m-see...` | ⚠️ Original URL appears canonical and confirmed via search |
| 233 | `nomagic` | Nomagic | 2026-01-28 | $10 | Robotics | Series B (extension) | `https://nomagic.ai/news/series-b-exte...` → `https://nomagic.ai/news/nomagic-secures-an-addi...` | ⚠️ Original URL was placeholder; full slug confirmed |
| 70 | `aethero` | Aethero | 2025-06-11 | $8 | Space | Seed | `https://spacenews.com` → `https://www.satellitetoday.com/finance/2025/06/...` |  |
| 194 | `mach` | MACH | 2025-12-04 | $7 | Robotics | Seed | `https://roboticsandautomationnews.com...` → `https://roboticsandautomationnews.com/2025/12/0...` | ⚠️ Original URL had partial slug; full slug confirmed |
| 190 | `ailos-robotics` | AILOS Robotics | 2025-12-02 | $4 | Robotics | Seed | `https://tech.eu/2025/12/02/ailos-robo...` → `https://tech.eu/2025/12/02/ailos-robotics-gets-...` | ⚠️ Original URL had partial slug; full slug confirmed. Amount in dataset 3.8M USD ~... |
| 276 | `amplisi` | AmpliSi | 2026-03-12 | $2 | Materials | Pre-Seed | `https://amplisi.com/news/pre-seed` → `https://sheffield.ac.uk/commercialisation/news/...` | ⚠️ DATA QUALITY: AmpliSi raised 2M GBP (~2.5M USD), not 2.5M USD |
| 130 | `hive-robotics` | Hive Robotics | 2025-09-11 | $2 | Robotics | Pre-Seed | `https://tech.eu/2025/09/11/hive-robot...` → `https://tech.eu/2025/09/11/hive-robotics-secure...` | ⚠️ Original URL had partial slug; full slug confirmed. Amount 2.2M USD ~ 2M EUR |
| 156 | `augmentus` | Augmentus | 2025-10-27 | $0 | Robotics | Undisclosed | `https://www.prnewswire.com/news-relea...` → `https://www.augmentus.tech/news/augmentus-appli...` |  |
| 283 | `rivr` | Rivr | 2026-03-19 | $0 | Robotics | M&A | `https://www.therobotreport.com/rivr-a...` → `https://techcrunch.com/2026/03/19/amazon-acquir...` |  |

## MEDIUM confidence — paywall / aggregator URLs (6)

Replacement found but source is paywalled (Bloomberg, FT) or aggregator. Citation valid but content gated. **Approval recommended unless DQ flag.**

| idx | entity_id | Company | Date | $M | Current → Proposed | DQ flag |
|----:|-----------|---------|------|---:|-------------------|---------|
| 218 | `etchedai` | Etched.ai | 2026-01-14 | $500 | `https://techcrunch.com/2026/01/14/etc...` → `https://www.bloomberg.com/news/articles/2026-01...` | ⚠️ Original TechCrunch URL appears synthesized; Bloomberg has scoop dated 2026-01-1... |
| 129 | `d-robotics` | D-Robotics | 2025-09-10 | $270 | `https://techcrunch.com` → `https://www.yicaiglobal.com/news/chinas-d-robot...` | ⚠️ DATA QUALITY: 270M Series B total reached April 2026 (B2 round), not September 2... |
| 197 | `iceye` | ICEYE | 2025-12-05 | $163 | `https://spacenews.com` → `https://breakingdefense.com/2025/12/germany-awa...` | ⚠️ Best available source — could not find a clean ICEYE press release for Dec 2025 ... |
| 60 | `clearspace` | ClearSpace | 2025-06-01 | $95 | `https://esa.int` → `https://www.esa.int/Space_Safety/ESA_purchases_...` | ⚠️ Original ClearSpace contract was 86M EUR signed November 2020. Could not find ne... |
| 203 | `encos` | ENCOS | 2025-12-15 | $28 | `https://autonews.gasgoo.com/articles/...` → `https://pandaily.com/encos-raises-nearly-28-m-t...` |  |
| 75 | `turion-space` | Turion Space | 2025-06-18 | $20 | `https://spacenews.com` → `https://www.veteranventures.us/news1/announcing...` | ⚠️ DATA QUALITY: Turion Space's $20M Series A actually closed December 2024, not Ju... |

## LOW confidence — no replacement found (14)

Agent could not find a verifiable canonical URL. **No mutation applied; row stays `source_status: pending`.** Many of these have data-quality issues suggesting the rows themselves may be fabricated and should be triaged or dropped.

| idx | entity_id | Company | Date | $M | Current URL | Issue |
|----:|-----------|---------|------|---:|-------------|-------|
| 222 | `psibot` | PsiBot | 2026-03-10 | $280 | `https://autonews.gasgoo.com/articles/news/2-billion-yuan-...` | no canonical source found in Western trade press recommend manual triage |
| 115 | `fourier-intelligence` | Fourier Intelligence | 2025-08-20 | $120 | `https://techcrunch.com` | no canonical Western press article found for August 2025 CNY 300M Series E+ — recommend manual triage |
| 132 | `kargo` | Kargo | 2025-09-15 | $100 | `https://techcrunch.com` | no canonical source found for $100M Kargo Series A in September 2025. Most recent confirmed funding is $42M Series B in ... |
| 133 | `general-fusion` | General Fusion | 2025-09-15 | $73 | `https://techcrunch.com` | no canonical source found for $73M bridge funding in September 2025. Search shows General Fusion raised $30M CAD in Aug ... |
| 52 | `robco` | RobCo | 2025-05-10 | $52 | `https://techcrunch.com` | Best matches are RobCo's $42.5M Series B (2024). No $52M round in May 2025 found. Recommend manual triage — amount or da... |
| 93 | `bonsai-robotics` | Bonsai Robotics | 2025-07-10 | $50 | `https://techcrunch.com` | DATA QUALITY: Bonsai Series A was $15M in January 2025, not $50M in July 2025. The July 2025 event was the farm-ng acqui... |
| 101 | `endoquest-robotics` | EndoQuest Robotics | 2025-07-20 | $36 | `https://endoquestrobotics.com` | No $36M Series A in July 2025 found. EndoQuest closed a $59M round in July 2025 (lifting valuation to $319M). Recommend ... |
| 112 | `generative-bionics` | Generative Bionics | 2025-08-15 | $35 | `https://techcrunch.com` | DATA QUALITY: Generative Bionics is Italian humanoid robotics (IIT spinoff), not prosthetics. The 70M EUR (~81M USD) see... |
| 166 | `tric-robotics` | TRIC Robotics | 2025-11-05 | $30 | `https://techcrunch.com` | DATA QUALITY: TRIC Robotics' most recent funding is $5.5M seed in July 2025 — no $30M Series A in November 2025 found. R... |
| 59 | `contoro-robotics` | Contoro Robotics | 2025-05-20 | $20 | `https://techcrunch.com` | DATA QUALITY: Contoro $12M Series A was announced March 2025, not May 2025. No $20M round in May 2025 found. Recommend m... |
| 79 | `swarmfarm` | SwarmFarm | 2025-06-25 | $18 | `https://swarmfarm.com` | No $18M round in June 2025 found. SwarmFarm's Series B was $19.85M in October 2025. Recommend manual triage on date/amou... |
| 122 | `surgerii-robotics` | Surgerii Robotics | 2025-09-05 | $15 | `https://surgerii.com` | DATA QUALITY: Surgerii Robotics' $100M Series D was December 2025; no $15M seed in September 2025 found. September 2025 ... |
| 200 | `dyna-robotics` | Dyna Robotics | 2025-12-10 | $6 | `https://techcrunch.com` | DATA QUALITY: No $6M round in December 2025 for Dyna Robotics found. Their Series A was $120M in September 2025, seed wa... |
| 137 | `anvil-robotics` | Anvil Robotics | 2025-09-20 | $5 | `https://techcrunch.com` | DATA QUALITY: Anvil Robotics' $5.5M seed was announced April 2026, not September 2025. Recommend manual triage on date |

## Process for approval

Spot-check the HIGH and MEDIUM tables (90 rows total) for any URLs that look suspicious. Once approved, run the mutation script:

```python
# Apply approved URL replacements + flip source_status to verified
# script: /tmp/apply_url_replacements.py (will be generated post-approval)
```

Mutations applied: 90 (84 high + 6 medium)
Rows staying pending: 14
Rows requiring separate data-quality triage: 28 (see [v1_0_data_quality_issues.md](v1_0_data_quality_issues.md))
