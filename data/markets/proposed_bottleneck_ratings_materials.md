# Proposed Bottleneck Ratings — Materials Batch (B4 Sector 4 — FINAL)

**Status:** Proposal for review. NOT YET WRITTEN to `enrichment_data.json`.

Workflow produced 33 ratings across 6 subsectors via parallel subsector agents + adversarial verify on every elevated proposal. **12 elevated proposals all verifier-confirmed** — no downgrades, no upgrades. **Materials has the highest elevated-rating density of any sector** (1 CRIT + 11 HIGH = 36% of cohort vs Semi 12%, Robotics 3%, Space 8%) — consistent with the sector's upstream supply-chain position where geopolitical concentration is the norm rather than the exception.

## Distribution

| Rating | Count |
|---|---:|
| CRITICAL | 1 |
| HIGH | 11 |
| MEDIUM | 12 |
| LOW | 8 |
| UNRATED | 1 |
| **Total** | **33** |

## Combined coverage after this batch

Existing rated entities (post-Space): 215
Adding (UNRATED skipped): 32
Combined: 247 / 566 = 43.6% of universe rated

## CRITICAL proposal

### SOI FP — Soitec | Verifier: **✓ confirm**

**Description:** Sole-source supplier of RF-SOI wafers for 5G smartphone front-ends and the only volume-qualified supplier of photonics-grade SOI wafers used in AI photonics chips, protected by ~4,300 Smart Cut patents.

**Rationale:** Soitec holds ~80% of total SOI wafers and BofA estimates >95% in photonics-grade SOI; >70% RF-SOI share for 5G smartphones. Smart Cut process is patent-protected (4,300 patents) with no equivalent process at volume. Photonics-SOI for AI optical transceivers is a sole-source dependency for the AI scale-up roadmap with no qualified second source today. RF-SOI and photonics-SOI together meet the calibration bar for CRITICAL (sole-source, no viable substitute today).

**Key customers:** Qualcomm, Skyworks, Qorvo, Broadcom (RF-SOI); STMicroelectronics, GlobalFoundries (FD-SOI); TSMC, Intel, Tower (photonics-SOI for AI optical transceivers)
**Key suppliers:** Shin-Etsu/SUMCO (bulk silicon wafers as substrate), captive Smart Cut process
**Confidence:** HIGH

**Verifier reasoning:** Confirm CRITICAL. The photonics-SOI position is a genuine sole-source dependency for the AI optical/CPO scale-up — Soitec is the only volume-qualified supplier (~>95% share), Tower Semi's photonics chips map 1:1 to Soitec wafer orders, and neither Shin-Etsu (royalty license, no meaningful volume) nor Simgui (200mm only, China domestic, sales managed by Soitec, March 2026 NSIG extension explicitly added no tech transfer) is a viable second source today. The Smart Cut patent moat (3,500-4,300 patents) is reinforced by GlobalWafers' license termination (Oct 2023, exits 2027), and customer qualification of an alternative SOI supplier is a 2-5 year process — far beyond the 1-2 quarter switching test. While RF-SOI has substitutes (bulk CMOS, GaAs, GaN-on-Si) and is currently in a cyclical inventory correction, switching FEM designs is still multi-year, and the photonics-SOI sole-source alone satisfies the CRITICAL bar regardless.

## HIGH proposals

All 11 verifier-confirmed. Compact summary below; full rationale + key_customers + key_suppliers retained in the structured JSON applied at write time.

| Ticker | Name | Bottleneck (one-line) |
|---|---|---|
| MTRN | Materion | Only vertically integrated Western producer of primary beryllium from US mine-to-mill, plus advanced thin-film deposition materials and EUV/optical coatings for defense and semis. |
| ENTG | Entegris | Dominant supplier of high-purity contamination-control consumables (filters, FOUPs, liquid delivery, CMP slurries, advanced deposition materials) with single-sourced positions on multiple advanced-… |
| WCH GR | Wacker Chemie | One of two Western producers of semiconductor-grade hyperpure polysilicon (with Hemlock); supplies high-purity poly used at leading-edge logic and memory fabs. |
| HXL | Hexcel | Qualified sole/dual-source prepreg and carbon fiber composite supplier on Airbus A350 (all composite primary structures) and Boeing 787 nacelle systems; aerospace qualification is multi-year and pr… |
| MP | MP Materials | Only scaled US mine-to-magnet NdPr producer; sole operator of Mountain Pass (the only US rare earth mine) with DoD-backed integrated separation and Fort Worth/Independence magnet build-out. |
| LYC AU | Lynas Rare Earths | Only scaled rare-earth separator outside China and the first commercial producer of separated heavy rare earths (dysprosium, terbium) ex-China. |
| CCJ | Cameco | World's second-largest uranium miner (~14-20% global share) and Western-aligned alternative to Kazatomprom; 49% Westinghouse owner gives the only US-aligned fuel-cycle and reactor-services integrat… |
| CRS | Carpenter Technology | Premium-melt (VIM/VAR/ESR) nickel/cobalt/titanium superalloys for rotating aircraft engine parts — capacity is the binding constraint of the Western aero-engine alloy chain. |
| ATI | ATI Inc | Aerospace-grade titanium ingot/billet/plate and nickel superalloys with long-term Boeing supply agreement; ITAR-compliant qualified source for engines and airframes. |
| 5706 JP | Mitsui Kinzoku (Mitsui Mining & Smelting) | ~95%+ global share of MicroThin ultra-thin copper foil with carrier — the enabling input for HDI substrates, ABF/IC substrates, and advanced packaging (CoWoS/SLP/MSAP) used in AI accelerators. |
| OLED | Universal Display Corporation | Near-monopoly licensor and supplier of phosphorescent red/green OLED emitter materials and IP, with a patent estate of 7,000+ issued/pending worldwide that gates panel-maker bills of materials. |

## UNRATED — registry data-quality flag

- **BREW** — Public-record ticker BREW historically belonged to Craft Brew Alliance (acquired by AB InBev 2020) and currently to the Corgi Coffee & Energy Drinks ETF — neither is a specialty materials issuer. The private specialty materials firm Brewer Science (Rolla, MO) is not publicly listed. In the project's

**Recommendation:** remove from Materials sector, add to registry-hygiene cleanup task.

## Full ratings by subsector

### Unknown (15 tickers)

| Ticker | Name | Proposed | Confidence | Bottleneck |
|---|---|---|---|---|
| CCJ | Cameco | **HIGH** | HIGH | World's second-largest uranium miner (~14-20% global share) and Western-aligned alternative to Kazatomprom; 49% Westinghouse owner gives the only US-aligned fuel-cycle and reactor-services integrat… |
| OLED | Universal Display Corporation | **HIGH** | HIGH | Near-monopoly licensor and supplier of phosphorescent red/green OLED emitter materials and IP, with a patent estate of 7,000+ issued/pending worldwide that gates panel-maker bills of materials. |
| 4063 JP | Shin-Etsu Chemical | **MEDIUM** | HIGH | Largest global silicon wafer manufacturer (~30% share) plus leading photoresist supplier (~20%), with deep entrenchment in Japanese semiconductor materials oligopoly. |
| MRSN FP | Mersen | **MEDIUM** | MEDIUM | Number-one global supplier of isostatic graphite and carbon brushes; key supplier of SiC-coated graphite hot-zone components for SiC crystal growth and power-electronics manufacturing. |
| ALB | Albemarle | **MEDIUM** | HIGH | Top-3 global lithium producer with 49% stake in Greenbushes (highest-grade spodumene globally) plus Salar de Atacama brine and Kemerton hydroxide. |
| SQM | Sociedad Quimica y Minera (ADR) | **MEDIUM** | HIGH | Lowest-cost lithium brine producer at Salar de Atacama, top-3 global with Albemarle and Tianqi; new Codelco JV (Novandino) preserves Chilean access post-2030. |
| NN | NEXTracker | **LOW** | HIGH | Number-one global solar tracker manufacturer (~26% global share, 10 consecutive years) but competing in a commoditising racking market with viable alternatives. |
| KAI | Kadant | **LOW** | HIGH | Specialty industrial process consumables (doctor blades, fluid handling, stock prep, fiber granules) for pulp/paper/tissue and adjacent process industries. |
| NATIX | NATIX Network | **LOW** | MEDIUM | Solana-based DePIN token for crowdsourced mapping/navigation data; no semiconductor-supply chokepoint despite the 'Wafer Manufacturer' label in the universe file. |
| TEL | TE Connectivity plc | **LOW** | HIGH | Broad-line connector and sensor manufacturer in a competitive landscape with credible substitutes from Amphenol, Molex, Aptiv, and Yazaki; no single sole-source chokepoint. |
| 6502 JP | Toshiba | **LOW** | HIGH | Diversified manufacturing conglomerate (energy solutions, digital infrastructure, devices/power semiconductors) facing peer competition across all segments with no sole-source choke-point in roboti… |
| SU FP | Schneider Electric | **LOW** | HIGH | Electrical equipment / energy management major (~18% low-voltage share, ~25% data center critical power) with strong but peer-competitive position against Siemens, ABB, Eaton. |
| AOSL | Alpha and Omega Semiconductor | **LOW** | HIGH | Mid-cap discrete power semiconductor supplier (MOSFETs, IGBTs, SiC/GaN, power ICs) competing in a deeply contested market versus Infineon, Onsemi, STMicro, Vishay, Rohm, Toshiba, Renesas. |
| 6971 JP | Kyocera Corporation | **LOW** | HIGH | Diversified components conglomerate (ceramic packages, capacitors, connectors, solar, telecoms) with peer-competitive positions across most product lines; no single irreplaceable choke point. |
| BREW | Brewer Materials | **UNRATED** | HIGH | Identity of $0.1B 'Brewer Materials' equity not confirmable from public record under ticker BREW; project data file maps BREW to 'Homebrew Robotics Club' (CoinGecko token), not a specialty material… |

### Rare Earths & Critical Minerals (6 tickers)

| Ticker | Name | Proposed | Confidence | Bottleneck |
|---|---|---|---|---|
| MP | MP Materials | **HIGH** | HIGH | Only scaled US mine-to-magnet NdPr producer; sole operator of Mountain Pass (the only US rare earth mine) with DoD-backed integrated separation and Fort Worth/Independence magnet build-out. |
| LYC AU | Lynas Rare Earths | **HIGH** | HIGH | Only scaled rare-earth separator outside China and the first commercial producer of separated heavy rare earths (dysprosium, terbium) ex-China. |
| 5706 JP | Mitsui Kinzoku (Mitsui Mining & Smelting) | **HIGH** | HIGH | ~95%+ global share of MicroThin ultra-thin copper foil with carrier — the enabling input for HDI substrates, ABF/IC substrates, and advanced packaging (CoWoS/SLP/MSAP) used in AI accelerators. |
| ARU AU | Arafura Rare Earths | **MEDIUM** | MEDIUM | Future NdPr producer at Nolans (NT) with multi-sovereign ECA financing and binding offtakes to Hyundai/Kia/Siemens Gamesa/Traxys; first production mid-2029. |
| ILU AU | Iluka Resources | **MEDIUM** | MEDIUM | World's largest zircon producer (~20% global share) and developer of Australia's first integrated rare earths refinery at Eneabba (2027 start) under a A$1.65B Australian Government Critical Mineral… |
| AMG NA | AMG Critical Materials | **MEDIUM** | MEDIUM | Largest US ferrovanadium producer + global #1 spent-catalyst recycler (V-CYCLE) + titanium aluminide / aluminum master alloys to aerospace engines + AMG Technologies vacuum furnace equipment to eng… |

### Process Chemicals (4 tickers)

| Ticker | Name | Proposed | Confidence | Bottleneck |
|---|---|---|---|---|
| MTRN | Materion | **HIGH** | HIGH | Only vertically integrated Western producer of primary beryllium from US mine-to-mill, plus advanced thin-film deposition materials and EUV/optical coatings for defense and semis. |
| ENTG | Entegris | **HIGH** | HIGH | Dominant supplier of high-purity contamination-control consumables (filters, FOUPs, liquid delivery, CMP slurries, advanced deposition materials) with single-sourced positions on multiple advanced-… |
| WCH GR | Wacker Chemie | **HIGH** | HIGH | One of two Western producers of semiconductor-grade hyperpure polysilicon (with Hemlock); supplies high-purity poly used at leading-edge logic and memory fabs. |
| SGL GR | SGL Carbon | **MEDIUM** | MEDIUM | Top-tier ultra-high-purity isostatic graphite supplier for SiC crystal growth, semiconductor furnaces, and TRISO nuclear fuel; one of five global majors with Toyo Tanso, Mersen, Superior, GrafTech. |

### Silicon & Substrates (3 tickers)

| Ticker | Name | Proposed | Confidence | Bottleneck |
|---|---|---|---|---|
| SOI FP | Soitec | **CRITICAL** | HIGH | Sole-source supplier of RF-SOI wafers for 5G smartphone front-ends and the only volume-qualified supplier of photonics-grade SOI wafers used in AI photonics chips, protected by ~4,300 Smart Cut pat… |
| WAF GR | Siltronic AG | **MEDIUM** | HIGH | #4 global 300mm silicon wafer supplier (~12% revenue share) inside a 5-player oligopoly (Shin-Etsu/SUMCO/GlobalWafers/Siltronic/SK Siltron) controlling ~85% of 300mm capacity. |
| 6488 TT | GlobalWafers Co Ltd | **MEDIUM** | HIGH | #3 global 300mm silicon wafer supplier (~17% revenue share) inside the 5-player Shin-Etsu/SUMCO/GlobalWafers/Siltronic/SK Siltron oligopoly that controls ~85% of capacity. |

### Structural Materials (3 tickers)

| Ticker | Name | Proposed | Confidence | Bottleneck |
|---|---|---|---|---|
| HXL | Hexcel | **HIGH** | HIGH | Qualified sole/dual-source prepreg and carbon fiber composite supplier on Airbus A350 (all composite primary structures) and Boeing 787 nacelle systems; aerospace qualification is multi-year and pr… |
| CRS | Carpenter Technology | **HIGH** | HIGH | Premium-melt (VIM/VAR/ESR) nickel/cobalt/titanium superalloys for rotating aircraft engine parts — capacity is the binding constraint of the Western aero-engine alloy chain. |
| ATI | ATI Inc | **HIGH** | HIGH | Aerospace-grade titanium ingot/billet/plate and nickel superalloys with long-term Boeing supply agreement; ITAR-compliant qualified source for engines and airframes. |

### Industrial & Specialty Gases (2 tickers)

| Ticker | Name | Proposed | Confidence | Bottleneck |
|---|---|---|---|---|
| 4091 JP | Nippon Sanso Holdings | **MEDIUM** | MEDIUM | Number-four global industrial gas major and largest Japanese supplier with leadership in specific electronic specialty gases and MOCVD precursors for compound semiconductor manufacturing. |
| 4043 JP | Tokuyama | **MEDIUM** | MEDIUM | Top global producer of high-purity TMAH photoresist developer for EUV/advanced-node lithography plus semiconductor-grade polysilicon (~12,500 MT capacity, 7nm-and-below grade). |

## Open questions for reviewer

1. **600111 vs 600111 C1 duplicate** — same entity (China Northern Rare Earth) with two registry keys and conflicting ratings (HIGH from Robotics batch vs CRITICAL existing). Materials workflow saw the conflict in calibration. Pick canonical: keep CRITICAL on the 600111 C1 key and drop the 600111 HIGH from Robotics, OR consolidate both into 600111 with a unified rating. CNRE's case for CRITICAL is defensible (~90% global NdPr refining concentration + 2024-2025 Chinese export controls + irreplaceable Bayan Obo position). Recommend: **keep CRITICAL, consolidate under 600111 (drop _C1 suffix as registry hygiene)**.

2. **Materials elevated-rating density** — 12 of 33 (36%) elevated vs Semi 12%, Robotics 3%, Space 8%. This is structural to the upstream sector (rare earths, beryllium, semi poly, aerospace alloys, OLED IP are all genuinely concentrated). Not a calibration drift. Confirm interpretation: materials sector legitimately carries more bottleneck risk per constituent.

3. **BREW (Brewer Materials) UNRATED** — registry data-quality: ticker BREW historically maps to Craft Brew Alliance / Corgi ETF, neither is a materials company. Same pattern as ATNM/SLC. Add to registry hygiene cleanup task.

4. **Schema fields** — same as Semi/Robotics/Space: `bottleneck_description`, `confidence` on all 32 written entries. No going-concern flags this batch.
