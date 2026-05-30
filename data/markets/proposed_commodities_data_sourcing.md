# Robotnik Commodities — Step 4: Surface for Review

**Universe:** 56 commodities | **Date:** 2026-05-29

This document proposes a per-commodity data sourcing plan for the Robotnik commodities surface. Each commodity is labelled with an honest `pricing_status` that reflects what is actually obtainable from public or subscription feeds, not what we would wish were available. The founder directive "no-public-price is acceptable; don't force a proxy where the proxy is misleading" has been applied throughout — seven commodities are flagged `no_public_price` rather than fitting a poor proxy.

---

## 1. Pricing Status Distribution

| Pricing Status | Count | Share | Definition |
|---|---|---|---|
| `exchange_proxy` | 22 | 39.3% | No exchange-traded futures; tracked via paywalled assessor (SMM, Fastmarkets, Argus, Asian Metal) or a related-but-imperfect exchange contract |
| `equity_proxy_only` | 16 | 28.6% | No transparent commodity price; tracked via listed producer/consumer equities |
| `live_market_price` | 11 | 19.6% | Daily settled price on a major exchange (LME, COMEX, CME, NYMEX, LBMA) with free-tier coverage |
| `no_public_price` | 7 | 12.5% | No public spot, no useful proxy — sold via bilateral LTAs or government allocation |

**Headline:** Only 19.6% of the Robotnik commodity universe has true live exchange-settled pricing. 68% requires either a subscription feed (Fastmarkets / Argus / Platts / SMM / Asian Metal / Benchmark Mineral Intelligence) or an equity-basket construction. The remaining 12.5% cannot be tracked in real time at all.

---

## 2. Cross-Tab: Pricing Status × Rating Tier

| Rating | live_market_price | exchange_proxy | equity_proxy_only | no_public_price | Total |
|---|---|---|---|---|---|
| **CRITICAL** | 0 | 5 | 0 | 0 | 5 |
| **HIGH** | 0 | 5 | 2 | 0 | 7 |
| **MEDIUM** | 6 | 9 | 11 | 6 | 32 |
| **LOW** | 5 | 1 | 2 | 0 | 8 |
| **UNRATED / Pre-commercial** | 0 | 0 | 0 | 1 | 1 |
| Other (Pre-commercial He-3 + UNRATED Sc) | 0 | 0 | 1 | 1 | 2 |

**Critical methodology note:** **Every CRITICAL-rated commodity (5/5) lacks a live exchange-settled price.** All five (Dysprosium, Samarium, Antimony, Tungsten/APT, Yttrium, Terbium) sit in `exchange_proxy` and depend on paywalled Chinese spot assessments (SMM, Asian Metal) or Western assessor benchmarks (Fastmarkets Rotterdam). This is the central data-procurement problem for the platform: the commodities Robotnik most needs to track are the ones with the worst public price discovery.

---

## 3. Per-Commodity Sourcing — by Pricing Status

### 3a. `live_market_price` (11 commodities)

| Commodity | Rating | Tier | Primary Source | Backup | Caveats | Confidence |
|---|---|---|---|---|---|---|
| Copper | LOW | 1 | LME — LMCADS03 (Grade A 99.99%) | COMEX HG front-month | Most liquid base metal globally; free-tier coverage excellent | HIGH |
| Aluminum | LOW | 1 | LME — LMAHDS03 (P1020A 99.7%) | SHFE AL front-month | Russian-metal LME ban (Apr 2024) created two-tier basis but LMAHDS03 remains canonical | HIGH |
| Silver | LOW | 1 | LBMA Silver Price (12:00 London fix) | COMEX SI front-month | LBMA fix is global benchmark; 4N/5N grade premiums paywalled | HIGH |
| Tin | MEDIUM | 1 | LME — LMSND (99.85%) | SHFE SN front-month | Transparent global benchmark; supply concentration (Indonesia, Myanmar) drives spot volatility | HIGH |
| Cobalt | MEDIUM | 1 | LME Cobalt Cash (CO 99.8%) | Fastmarkets — Co sulphate 20.5% EXW China | LME illiquid (stale fixings); sulfate basis paywalled and not = LME | HIGH |
| Nickel (Class 1) | MEDIUM | 1 | LME — LMNIDY Class 1 cathode | SHFE NI front-month | March 2022 LME credibility crisis; Class 1/Class 2 and sulfate basis paywalled | HIGH |
| Lithium (carbonate + hydroxide) | MEDIUM | 1 | CME LTH / LIT futures (vs Fastmarkets) | GFEX LC futures | CME open interest modest; GFEX China-domestic; spodumene priced separately (paywalled) | HIGH |
| Ruthenium | MEDIUM | 1 | Johnson Matthey daily PGM Base Price (USD/oz) | Heraeus PGM trading desk | JM dealer quote functions as a daily fix; free public access | HIGH |
| Palladium | MEDIUM | 1 | NYMEX PA (Palladium Futures) front-month | LBMA Pd AM/PM Fix | Highly liquid; rocket-grade catalytic premium minor | HIGH |
| Uranium (U3O8) | MEDIUM | 1 | NYMEX UX Futures (settled vs UxC) | UxC Weekly Spot / TradeTech Weekly | Spot only 15-20% of volume; 80%+ via utility LTAs; NYMEX UX gives a daily transparent reference | HIGH |
| Henry Hub natural gas | LOW | 1 | NYMEX NG front-month | EIA Henry Hub Spot (RNGWHHD) | Most liquid global gas benchmark; basis to rocket-grade LNG/CH4 (purity, cryogenics) not captured | HIGH |

### 3b. `exchange_proxy` (22 commodities)

| Commodity | Rating | Tier | Primary Source | Backup | Caveats | Confidence |
|---|---|---|---|---|---|---|
| Antimony | CRITICAL | 1 | Fastmarkets — MMTA Std Grade II, Rotterdam (weekly) | Asian Metal — Sb 99.65% China FOB | No exchange contract; China Sep 2024 export controls drove $13k→$40k+ Rotterdam; paywalled; thin Western equity proxies (PPTA, UAMY) | HIGH |
| Dysprosium | CRITICAL | 1 | SMM — Dy Oxide 99.5% FOB China (daily) | Asian Metal — Dy2O3 99.5% China spot | China controls ~85% heavy REE refining; Dec 2023 export controls; paywalled FOB China; Lynas (LYC.AX) only ex-China equity proxy | HIGH |
| Samarium | CRITICAL | 1 | Asian Metal — Sm2O3 99.9% China FOB (weekly) | SMM — Sm Oxide spot China | Thin weekly fixings; Apr 2025 China export controls; paywalled; no Western proxy except REE baskets | MEDIUM |
| Terbium | CRITICAL | 1 | SMM — Tb4O7 99.99% FOB China (daily) | Asian Metal — Tb4O7 99.99% spot | Tightest China export controls (Apr 2025); ~$1000/kg; ~90% China refined; only Lynas (LYC.AX) + REMX as basket proxy | HIGH |
| Tungsten (APT) | CRITICAL | 1 | Fastmarkets — APT 88.5% WO3 CIF Rotterdam (weekly) | Asian Metal — APT 88.5% FOB China | No futures; WF6 downstream has no public price (LTA); equity proxies: ALMTF, 600549.SS, SAND.ST | HIGH |
| Yttrium | CRITICAL | 1 | Asian Metal — Y2O3 99.999% China FOB (weekly) | SMM — Y2O3 spot China | China Apr 2025 export controls; ~99% China refined; high-purity (5N/6N) premiums not published; REE basket equities only | MEDIUM |
| Neodymium (NdPr) | HIGH | 1 | SMM — NdPr Oxide 99.5% FOB China (daily) | Asian Metal — Nd2O3 99.5% China spot | Subscription-gated FOB China; REMX (NYSE Arca) + MP Materials (MP) tradeable equity proxies for free-tier | HIGH |
| Manganese (HPMSM) | HIGH | 1 | Fastmarkets — Mn sulphate 32% Mn battery-grade EXW China (weekly) | CME MAU Mn Ore 44% CIF Tianjin (bulk only) | No terminal for battery grade; CME MAU is metallurgical ore not battery; equity proxies S32.AX, ERA.PA, E25.AX | MEDIUM |
| Graphite (anode) | HIGH | 1 | Benchmark Mineral Intelligence — Spherical 99.95% FOB China; Synthetic Anode (monthly) | Fastmarkets — Flake 94-97% C -100 mesh FOB China | No futures; paywalled monthly only; China dominates synthetic (>95%); Dec 2023 export controls; equity proxies SYR.AX, NMG, NGC.V, 003670.KS | HIGH |
| Magnesium | HIGH | 1 | Fastmarkets — Mg 99.8% Pidgeon FOB China (weekly) | Asian Metal — Mg 99.9% FOB China | No futures; ~85% China supply; paywalled; EU AD duties add basis; Western (US Mg UT, WMG.V) sub-scale | HIGH |
| Gallium | HIGH | 1 | SMM — Ga 99.99% spot (CNY/kg, daily) | Argus Minor Metals — Ga 4N Rotterdam | China ~98% supply; Aug 2023 export controls create CN vs ex-CN two-tier; SMM subscription-gated but de facto reference | HIGH |
| Vanadium | MEDIUM | 1 | Fastmarkets — FeV 78-82% Rotterdam; V2O5 98% China (weekly) | Asian Metal — V2O5 98% China FOB | No futures; FeV/V2O5 paywalled; 90% demand steel alloy, growing VRFB share; equity proxies LGO, BMN.L (distressed), UUUU | MEDIUM |
| Bismuth | MEDIUM | 1 | Fastmarkets — Bi 99.99% Rotterdam (weekly) | Asian Metal — Bi 99.99% FOB China | No futures; ~80% China byproduct supply; Feb 2025 China export controls; no clean Western producer equity at scale | MEDIUM |
| Indium | MEDIUM | 1 | Fastmarkets — In 99.99% Rotterdam (weekly) | SMM — In 99.995% spot China | No LME; Fastmarkets/Argus weekly assessed; InP wafers are bilateral LTAs; equity proxies 010130.KS, TECK, Nyrstar | HIGH |
| Germanium | MEDIUM | 1 | SMM — GeO2 99.999% / Ge 5N spot (daily) | Argus Minor Metals — Ge Rotterdam | China ~60% supply; Aug 2023 export controls; SMM subscription; USGS publishes annual lagged price | HIGH |
| Tellurium | MEDIUM | 1 | SMM — Te 99.99% spot (daily) | Argus Minor Metals — Te 99.99% Rotterdam | Byproduct of Cu refining; SMM/Argus weekly only transparent; equity exposure VNP.TO, FSLR (downstream CdTe) | MEDIUM |
| Hafnium | MEDIUM | 1 | Argus Minor Metals — Hf nuclear-grade (monthly USD/kg) | SMM — Hf 99.9% spot China | Byproduct of nuclear Zr separation; supply constrained (Framatome/CEZUS, ATI, China Nuclear); monthly only; equity proxy ATI | MEDIUM |
| Zirconium | MEDIUM | 1 | SMM — Zircon sand 66% spot (weekly) | TZMI / Iluka (ILU.AX) Zircon Reference Price | Mineral sand vs nuclear-grade Zr metal are separate markets; nuclear-grade Zr metal is bilateral; equity proxies ILU.AX, TROX, Rio Tinto | MEDIUM |
| Anhydrous HF (electronic) | MEDIUM | 1 | Argus / IM — Acidspar 97% CaF2 FOB China (weekly, upstream feedstock) | Soulbrain 357780.KS + Stella Chemifa 4109.T + 002407.SZ | Fluorspar upstream is transparent; electronic-grade HF (10-50x premium) is LTA-bilateral; Japan-Korea 2019 export-control flashpoint | MEDIUM |
| Electronic-grade NH3 | LOW | 1 | Argus / ICIS / Fertecon — Ammonia FOB Tampa / CFR NW Europe (weekly) | CME NH3 Tampa Ammonia futures (low liquidity) | Bulk ammonia transparent; electronic-grade 8N/9N carries 50-200x premium and is LTA-bilateral; bulk is directional only | MEDIUM |
| GOES (electrical steel) | MEDIUM | 4 | CME HRC US Midwest HRC Steel Futures (daily) | CLF + 5401.T + 005490.KS + TKA.DE | GOES carries 4-8x premium over HRC; AD/CVD trade-protected; Cleveland-Cliffs (CLF) sole US producer is cleanest equity | HIGH |
| RP-1 (rocket kerosene) | LOW | 1 | NYMEX HO (NY Harbor ULSD/Heating Oil) front-month | Platts Jet Fuel USGC / Argus Kerosene A1 | RP-1 (MIL-DTL-25576) sold sole-source (SpaceX, ULA via Calumet); 3-5x premium over Jet-A for olefin-free spec; basis opaque | MEDIUM |

### 3c. `equity_proxy_only` (16 commodities)

| Commodity | Rating | Tier | Primary Source | Backup | Caveats | Confidence |
|---|---|---|---|---|---|---|
| Photoresist (EUV + ArF) | HIGH | 4 | TSE — JSR (4185.T, delisted 2024 to JIC) + TOK (4186.T) + Shin-Etsu (4063.T) + Sumitomo Chem (4005.T) + Fujifilm (4901.T) | TECHCET / TrendForce reports (subscription) | EUV resist ~$1.5B/yr oligopoly under fab LTAs (NDA pricing); JSR delisting reduces pure-play; TOK + Shin-Etsu best remaining | HIGH |
| Synthetic fused silica / EUV mask blanks | HIGH | 4 | TSE — Hoya (7741.T) + Shin-Etsu (4063.T) + AGC (5201.T) + Tosoh (4042.T) | Heraeus (private) / Corning GLW Display Tech segment | EUV mask blank is Hoya (~70%) / AGC (~30%) duopoly; ~$30K/mask; multi-year supply agreements w/ ASML mask ecosystem | HIGH |
| Tantalum | MEDIUM | 1 | Asian Metal — Ta2O5 30% CIF China; Ta metal 99.95% (weekly) | AMG Critical Materials (AMG.AS) equity | No terminal; bilateral sales (Global Advanced Metals private, AMG, Chinese refiners); ~40% mine supply Central Africa conflict-mineral overhead | HIGH |
| Niobium | MEDIUM | 1 | CBMM via shareholder filings (5411.T, 8001.T, 0267.HK consortium) | USGS Mineral Commodity Summaries (annual) | CBMM ~80% global supply but private; annual contract pricing; USGS annual is only public benchmark | HIGH |
| Hyperpure polysilicon | MEDIUM | 1 | TSE/XETRA — Wacker (WCH.DE) + Tokuyama (4043.T) + GCL Tech (3800.HK) | Bernreuter Research Polysilicon Price Index (monthly subscription) | Semi-grade 11N is 10-20x solar-grade; PVInsights/BNEF solar-grade prints are misleading for semi; Wacker/Tokuyama best | HIGH |
| SiC substrates | MEDIUM | 4 | NYSE/TSE — Wolfspeed (WOLF) + Coherent (COHR) + SiCrystal-Resonac (4004.T) + SICC (688234.SS) + TanKeBlue (688275.SS) | Yole / TrendForce / Omdia quarterly ASP reports (subscription) | 150mm/200mm wafer ASP via Yole subscription; Wolfspeed cleanest pure-play; SICC/TanKeBlue newer CN listings | HIGH |
| GaN substrates | MEDIUM | 4 | TSE/Nasdaq — Sumitomo Electric (5802.T) + Mitsubishi Chemical (4188.T) + Soitec (SOI.PA) + Sumco (3436.T) | Yole quarterly GaN wafer ASP reports (subscription) | Bulk GaN market small (~$200M/yr); Sumitomo + Mitsubishi private subsidiary dominate; partial equity proxy (small revenue share) | MEDIUM |
| CMP slurry | MEDIUM | 4 | NYSE/TSE/KRX — Entegris (ENTG, post-CMC acq 2022) + Fujimi (5384.T) + Resonac (4004.T) + Merck KGaA (MRK.DE) + KCTech (281820.KS) + Soulbrain (357780.KS) | TECHCET Critical Materials Report (annual) | ~$2.5B/yr market; CMC was pure-play, now diversified inside Entegris; fab LTAs | HIGH |
| Sputtering targets (Ta, Ti, Cu, Co, Ru) | MEDIUM | 4 | TSE/NYSE — JX Advanced Metals (5020.T, ENEOS spin 2024) + Materion (MTRN) + Honeywell (HON) + Plansee (private) + 3674.TWO | LME + JM upstream metal feedstock (Cu LMCADS03, Co LMCO, Ru JM, Ta MB) | Consolidated market; targets carry 5-20x premium over raw metal; upstream metal gives directional baseline | HIGH |
| Helium (high-purity) | MEDIUM | 1 | NYSE/Nasdaq — Air Products (APD) + Linde (LIN) + Air Liquide (AI.PA) | BLM Helium In-Kind crude price (legacy; auction wound down 2024) | 5-10 year take-or-pay LTAs; BLM auction ended; remaining prints are commentary (Gasworld) not feed | HIGH |
| WF6 (Tungsten Hexafluoride) | MEDIUM | 1 | TSE/HKEX — Resonac (4004.T) + Kanto Denka (4047.T) + SK Materials (036490.KQ) | Argus / SMM — Tungsten APT 88.5% (upstream input) | Specialty electronic gas via fab LTAs; APT tracks upstream metal but not WF6 purification premium | HIGH |
| Silane / Disilane | MEDIUM | 1 | NYSE/SGX — Linde (LIN) + REC Silicon (RECSI legacy) + Air Liquide (AI.PA) + Mitsui Chemicals (4183.T) | (none) | Silane captive at poly producers; disilane ~$5,000+/kg niche under fab LTAs; no public spot | MEDIUM |
| NF3 (Nitrogen trifluoride) | MEDIUM | 1 | KRX/TSE — SK Materials (036490.KQ) + Kanto Denka (4047.T) + Hyosung Chemical (298000.KS) + Foosung (093370.KS) | (none) | ~80% Korean-controlled; $25-50/kg via fab LTAs; equity proxy via four primary producers most direct | HIGH |
| Argon (electronic grade) | LOW | 1 | NYSE/Euronext — Linde (LIN) + Air Liquide (AI.PA) + Air Products (APD) | (none) | 1% of atmosphere; 6N/9N electronic grade small premium over bulk; CRU bulk-gas reports subscription | HIGH |
| Liquid Oxygen (LOX) | LOW | 1 | NYSE/Euronext/TSE — LIN + APD + AI.PA + 4091.T (Nippon Sanso) | USGS Industrial Gases (annual) | Multi-year bilateral supply (SpaceX/ULA/Blue Origin); no spot or futures; tracked via gas-major segment earnings | HIGH |
| Liquid Hydrogen | MEDIUM | 1 | NYSE/Euronext/TSE — LIN + APD + AI.PA + PLUG + 4091.T | DOE Hydrogen Shot / IEA Global Hydrogen Review (annual) | LH2 (20K, 6N) via bilateral LTAs; gaseous H2 hub indexes emerging but LH2 carries 2-3x liquefaction premium | HIGH |

### 3d. `no_public_price` (7 commodities)

| Commodity | Rating | Tier | Primary "Source" (rationale only) | Caveats | Confidence |
|---|---|---|---|---|---|
| Scandium | UNRATED | 1 | USGS Mineral Commodity Summaries (annual) + SCY.TO equity | ~25 t/yr global consumption; no spot, no exchange; bilateral contracts (Rio Tinto Sorel-Tracy, Sumitomo, NioCorp pre-prod); USGS lists range only; equity proxies mostly pre-production | HIGH |
| Neon (litho-grade) | MEDIUM | 1 | Gasworld / SemiAnalysis commentary + LIN / AI.PA / Iwatani (8088.T) equity | LTAs to ~10 global customers (TSMC, Samsung, Intel); 2022 Russia/Ukraine spike $350→$2,500/m3 are commentary numbers; no daily feed | HIGH |
| Xenon | MEDIUM | 1 | Gasworld / Edelhoff commentary + LIN / AI.PA / Iwatani / Praxair-Messer equity | ~70 m3/day global ASU yield; bilateral; Edelhoff German distributor quotes only published reference | HIGH |
| Krypton | MEDIUM | 1 | Gasworld commentary + LIN / AI.PA / Iwatani equity | Co-produced w/ Xe; ~6-8 global producers, all LTA; Russia/Ukraine impact (Iceblick, Cryoin) via Gasworld only | HIGH |
| Hydrazine + MMH/UDMH | MEDIUM | 1 | Argus / Tecnon OrbiChem (subscription) + OCI.AS + 4205.T + AKE.PA equity | Rocket-grade sold cost-plus to Arianespace/Roscosmos/US DoD; only hydrazine hydrate precursor has paywalled Argus prints | MEDIUM |
| Nitrogen tetroxide (N2O4) / MON | MEDIUM | 1 | TKA.DE + 600291.SS equity + aerospace contractor disclosures | MON-3/MON-25 sold via long-term allocation to satellite/launch providers; nitric acid precursor has Argus prints but bridge to MON-grade is opaque | MEDIUM |
| Helium-3 | Pre-commercial | 1 | DOE NIDC periodic price lists / GAO Helium-3 Reports | DOE Isotope Program allocation + US tritium-decay stockpile; ~$3000-$5000/L STP in GAO reports; emerging private (Helion, Pacific Fusion) pre-commercial | HIGH |

---

## 4. Methodology Observations

### 4.1 CRITICAL commodities cannot be tracked in real time at the public-data tier

All 5 CRITICAL-rated commodities (Antimony, Dysprosium, Samarium, Terbium, Tungsten APT, Yttrium — 6 if Tungsten counted separately) sit in `exchange_proxy` and rely on subscription assessors. Without subscriptions to **Fastmarkets**, **Asian Metal**, and **SMM**, Robotnik can only offer:
- Weekly/monthly assessor lag commentary (free press releases)
- Equity proxies (REMX, LYC.AX, MP, PPTA, UAMY, ALMTF, 600549.SS, SAND.ST)

This is the **central data-procurement problem** of the platform.

### 4.2 Weakest proxies (flagged for founder review)

| Commodity | Proposed Primary | Why it's weak |
|---|---|---|
| Manganese (HPMSM) | CME MAU Mn Ore 44% Tianjin futures (backup) | MAU tracks metallurgical bulk ore; battery-grade HPMSM is a different product with no useful basis to ore. Fastmarkets weekly is the only honest read. |
| Niobium | CBMM via JFE/ITOCHU/POSCO consortium filings | Quarterly stakeholder filings are 1-3 months lagged. USGS annual is even slower. No daily signal possible. |
| RP-1 | NYMEX HO (Heating Oil) | 3-5x premium for MIL-DTL-25576 spec is opaque; basis adjustment is guesswork |
| Henry Hub as methalox proxy | NYMEX NG | HH is liquid but the basis to rocket-grade LNG (purity, cryogenics, transport) is large and unmodeled |
| Electronic-grade NH3 | Bulk Tampa/CFR NW Europe | Bulk to 8N/9N electronic carries 50-200x premium; LTA-only |
| Anhydrous HF (electronic) | Acidspar (CaF2) upstream feedstock | Two steps removed from the actual fab-grade HF customer pays |
| GaN substrates | Sumitomo Electric + Mitsubishi Chemical | GaN is a small revenue share at each diversified producer; signal is noisy |

### 4.3 Subscription feeds Robotnik would need to procure

To upgrade pricing_status from `exchange_proxy` to authoritative daily data, the following commercial feeds are the dominant references:

| Vendor | Coverage in Robotnik universe | Estimated commodities served |
|---|---|---|
| **Shanghai Metals Market (SMM)** | China daily REE, gallium, germanium, tellurium, terbium, yttrium, zircon, hafnium, indium, bismuth | ~12 |
| **Fastmarkets MB** | Rotterdam-warehouse assessments: antimony, APT, magnesium, vanadium, manganese sulphate, indium, bismuth, cobalt sulphate, dysprosium derivatives, etc. | ~10 |
| **Asian Metal** | China FOB backup for SMM coverage + tantalum | ~10 (mostly overlap with SMM as backup) |
| **Argus Media** | Minor metals (Ge, Te, Hf), specialty chemicals (Hydrazine, RP-1), fluorspar, electronic-grade ammonia | ~8 |
| **Benchmark Mineral Intelligence** | Graphite (spherical + synthetic anode), battery materials | ~1-2 (high cost-per-commodity, paywalled monthly only) |
| **Bernreuter Research** | Polysilicon (semi-grade adjacent) | 1 |
| **Platts (S&P Global)** | RP-1 (Jet-A USGC backup), spodumene | 2-3 |
| **TZMI** | Zircon, titanium minerals | 1 |
| **TECHCET / TrendForce / Yole / Omdia** | Photoresist, CMP slurry, SiC/GaN wafer ASPs | ~4 |
| **UxC / TradeTech** | Uranium weekly spot indicator | 1 |
| **Tecnon OrbiChem** | Hydrazine derivatives | 1 |

The dominant subscriptions (Fastmarkets, SMM, Argus, Asian Metal) would together cover ~70% of the `exchange_proxy` commodities. Benchmark Mineral Intelligence and TECHCET/Yole would extend coverage to the battery and semi-fab specialty bucket.

### 4.4 Equity proxies that need explicit basket construction

For the 16 `equity_proxy_only` commodities, Robotnik needs to define explicit weighted baskets so the "commodity price" displayed on the site has a deterministic methodology. Flagging the baskets that are non-trivial:

- **Photoresist:** 5 producers (JSR delisted, TOK, Shin-Etsu, Sumitomo Chem, Fujifilm) — Shin-Etsu and Sumitomo are conglomerates so basket weighting needs revenue-share haircuts
- **Sputtering targets:** 5 producers across 3 exchanges (JX Advanced Metals just spun out 2024, Materion, Honeywell, Plansee private, 3674.TWO) — need market-share weights from TECHCET/IndustryARC
- **CMP slurry:** Entegris (now diversified post-CMC), Fujimi, Resonac, Merck KGaA, KCTech, Soulbrain — same diversification problem
- **Industrial gases (He, LOX, LH2, Ar):** LIN + APD + AI.PA + 4091.T — these four overlap across all gas commodities; need careful product-segment isolation
- **Helium-3:** No equity exposure exists today; Helion and Pacific Fusion are pre-IPO. This is genuinely untrackable.
- **Niobium:** CBMM stake held by JFE/ITOCHU/Nippon Steel/POSCO/CITIC consortium — pull niobium revenue from quarterly disclosures, NOT consolidated parent stock prices
- **GaN substrates:** Sumitomo Electric + Mitsubishi Chemical + Soitec + Sumco — Sumitomo Electric and Mitsubishi are large conglomerates; GaN is single-digit revenue percent. Basket fidelity is poor and should be labeled "directional indicator only" on the front-end.
- **WF6:** Resonac + Kanto Denka + SK Materials — narrow enough to be a clean basket
- **NF3:** SK Materials + Kanto Denka + Hyosung Chemical + Foosung — narrow basket, four pure-ish Korean/Japan electronic-gas producers

---

## 5. Open Questions for Founder Review

### 5.1 Borderline pricing_status calls
1. **Lithium** — currently `live_market_price` via CME LTH/LIT. CME open interest is modest. Should we downgrade to `exchange_proxy` until daily volume thickens, or keep `live_market_price` because it is exchange-settled? Recommendation: keep, but show open interest as a confidence indicator.
2. **Cobalt** — `live_market_price` via LME, but LME Cobalt is illiquid with frequent stale fixings. Honest? Recommendation: keep `live_market_price` but flag illiquidity badge on the UI.
3. **Henry Hub as methalox** — `live_market_price` is honest for HH itself, but the connection to methalox propellant is so loose it's almost misleading. Should this commodity be relabeled `exchange_proxy` to be honest about the basis problem?
4. **Anhydrous HF (electronic)** — currently `exchange_proxy` via upstream fluorspar (Acidspar). Two steps removed from the actual product. Could honestly be `equity_proxy_only` (Soulbrain, Stella Chemifa, Do-Fluoride). Founder pick?
5. **GoES (Grain-Oriented Electrical Steel)** — `exchange_proxy` via CME HRC, but the 4-8x premium for high-permeability silicon alloy is not modeled. Cleveland-Cliffs (CLF) is the sole US producer — should this lean to `equity_proxy_only` via CLF as primary?

### 5.2 Subscription procurement decisions
1. **Tier-1 priority:** Should Robotnik procure **Fastmarkets MB** as the first subscription? It covers the most CRITICAL Rotterdam assessments (Antimony, APT, Magnesium) plus Vanadium, Bismuth, Manganese sulphate.
2. **Tier-1 priority:** **SMM** covers the most CRITICAL China-side REE feeds (Dysprosium, Terbium, Samarium oxide, NdPr, Yttrium) plus Gallium, Germanium. Most expensive of the assessor subscriptions. Worth it for the heavy-REE basket?
3. **Asian Metal vs SMM** — these largely overlap as Chinese spot. Is one sufficient as primary + the other as backup, or do we need both for redundancy?
4. **Benchmark Mineral Intelligence** — expensive (paywalled monthly battery-materials reports). Only critical for graphite/anode coverage. Acceptable to leave graphite as `exchange_proxy` with a monthly stale-data warning?
5. **TECHCET / Yole / TrendForce** — needed for SiC wafer, GaN wafer, EUV resist, CMP slurry ASP data. Do we subscribe to one (Yole probably best aggregator) or stay on equity proxies?

### 5.3 Equity basket construction decisions
1. For the 16 `equity_proxy_only` commodities, do we want **price baskets** (weighted average of stock prices, normalized to 100 at base date) or **revenue-segment baskets** (weighted by disclosed segment revenue)? Revenue-segment is harder to build but more honest for diversified producers.
2. Industrial gas commodities (He, LOX, LH2, Ar) all share the same four equities (LIN, APD, AI.PA, 4091.T). Do we show the same equity basket on four different commodity pages with different labels, or build a single "Industrial Gas Producers Index" and link all four commodity pages to it with an explanation?
3. Helium-3 has no equity proxy at all. Display the GAO/DOE price list as the ONLY public datapoint, even though it updates only every few years? Or remove He-3 from the surface entirely until Helion's offtake matures?

### 5.4 Honest labelling on the front-end
1. Should `no_public_price` commodities be visible on the site at all, or hidden until a feed becomes available? Pro for visible: completeness of universe. Con: user might mistake equity-proxy-only or commentary numbers for real prices.
2. For all `exchange_proxy` commodities, do we display the upstream/backup data with a visible "subscription required for primary feed" badge, or rely on the equity backup as the user-facing data?
3. For CRITICAL commodities under China export controls (Antimony, Dy, Sm, Tb, Y, Bismuth) the FOB-China assessor prices have diverged sharply from any Western-warehouse prices. Should we show **both** (CN spot + Rotterdam warehouse where Fastmarkets covers it), with the spread as a sub-indicator of export-control tightness?

---

*End of Step 4 proposal. Awaiting founder review before applying to `data/commodities/*.json` and the commodities page rendering layer.*
