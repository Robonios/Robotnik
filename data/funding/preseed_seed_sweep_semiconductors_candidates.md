# Pre-Seed / Seed Sweep — Semiconductors

**Sweep date:** 2026-05-13
**Scope:** Semiconductors sector, all 8 subsectors, 2025-01-01 → 2026-04-30 (16 months)
**Round types:** Pre-Seed + Seed (incl. Seed extension, Seed+, Seed II variants) ONLY
**Threshold override:** Pre-Seed ≥ $500K; Seed ≥ $1M
**Total candidates:** 27 (24 NEW + 3 DEDUP-CHECK)

---

## Sources Surveyed

**Sector pubs:** SemiEngineering (Q1–Q4 2025 + Q1 2026 startup-funding roundups; blocked WebFetch but used cross-referenced primaries), EE Times, Electronics Weekly, Semiconductor Today, eeNews Europe, Photonics Spectra, DCD, optics.org, SiliconANGLE, HPCwire, The Quantum Insider, Tom's Hardware, Compound Semiconductor Mag.

**General press:** TechCrunch, Bloomberg, Axios, VentureBeat, FT (paywalled, indirect).

**Regional:** Sifted (Europe), EU-Startups, Tech.eu, Ctech (Israel), Inc42 / YourStory / Entrepreneur India, Wamda (GCC), CnEVPost (China), KED Global (Korea), CTOL Digital.

**Investor/VC channels:** Sequoia Capital portfolio page, Mayfield, Eclipse Ventures, Earlybird, Founderful, Heartcore Capital, Engine Ventures, Entrada Ventures, Intel Capital, Khosla Ventures, Quantonation, Playground Global, NFX press.

**Accelerator / spinout:** Y Combinator W25/X25 directories, MIT / Caltech / UC Berkeley / ETH Zurich / University of Glasgow / Weizmann / Technion spinouts, imec.xpand portfolio.

**Aggregator (cross-check only, not primary citation):** Crunchbase News, PitchBook (titles only), Tracxn (excluded from `source`).

---

## Candidates

### ROW 1
- **entity_id:** snowcap-compute
- **company:** Snowcap Compute
- **sector:** Semiconductors
- **subsector:** Frontier Compute
- **company_description:** Develops superconducting compute chips using niobium-titanium nitride (NbTiN) cooled by standard helium cryogenic equipment, targeting AI, HPC, and quantum-classical hybrid workloads. Claims 25× performance-per-watt over leading CMOS chips, net of cooling overhead. First basic chip targeted for end of 2026.
- **round:** Seed
- **deal_type:** venture
- **amount_m:** 23.0
- **valuation_m:** null
- **date:** 2025-06-23
- **date_display:** 23-Jun-25
- **month_year:** Jun-25
- **quarter:** 2Q25
- **year:** 2025
- **location:** Palo Alto, USA
- **lead_investors:** Playground Global
- **co_investors:** Cambium Capital, Vsquared Ventures
- **related_tickers:** []
- **robotnik_take:** $23M seed for commercial-scale superconducting compute — first credible non-quantum cryogenic logic play since Northrop Grumman's RSFQ era stalled. Comp set is thin: closest public proxies are NVDA + INTC for power-per-watt benchmarks, with Pat Gelsinger on the board signaling pedigree but no near-term offtake. 25× efficiency claim is bench-only; full system economics depend on whether He cryo CAPEX scales with rack density. We're skeptical until 2026 chip tape-out.
- **source:** https://siliconangle.com/2025/06/23/superconducting-chip-startup-snowcap-compute-reels-23m/
- **source_status:** verified
- **policy_exposure:** US_CHIPS_Act
- **value_chain_tier:** ""
- **bottleneck_risk:** Pre-commercial
- **DEDUP STATUS:** NEW

### ROW 2
- **entity_id:** chipmind
- **company:** Chipmind
- **sector:** Semiconductors
- **subsector:** EDA & IP
- **company_description:** Develops "design-aware" AI agents that integrate with existing EDA workflows to automate RTL design, verification, and tape-out preparation tasks, with stated goal of cutting engineer time on repetitive low-level tasks by ~40%. Founded by two ETH Zurich PhDs with 20+ chip tape-outs combined. First European pure-play in agentic EDA.
- **round:** Pre-Seed
- **deal_type:** venture
- **amount_m:** 2.5
- **valuation_m:** null
- **date:** 2025-10-21
- **date_display:** 21-Oct-25
- **month_year:** Oct-25
- **quarter:** 4Q25
- **year:** 2025
- **location:** Zurich, Switzerland
- **lead_investors:** Founderful
- **co_investors:** Undisclosed
- **related_tickers:** [SNPS, CDNS]
- **robotnik_take:** $2.5M pre-seed for European-built agentic EDA — comp set is ChipAgents (now $50M Series A1 at scale) and Cognichip ($93M cumulative), both US-based. Chipmind is the smallest, latest, and most explicitly verification-focused. Strategic frame: SNPS and CDNS are racing to own this layer natively (ChipStack, Questa One); a $2.5M pre-seed has to ship product before incumbents close the gap. ETH founders + 20-tape-out track record is the moat.
- **source:** https://tech.eu/2025/10/21/chipmind-exits-stealth-with-25m-to-launch-ai-agents-for-faster-chip-design/
- **source_status:** verified
- **policy_exposure:** EU_Chips_Act
- **value_chain_tier:** ""
- **bottleneck_risk:** Pre-commercial
- **DEDUP STATUS:** NEW

### ROW 3
- **entity_id:** oxmiq-labs
- **company:** Oxmiq Labs
- **sector:** Semiconductors
- **subsector:** EDA & IP
- **company_description:** Founded by Raja Koduri (ex-Intel/AMD/Apple GPU architect), Oxmiq licenses modular GPU IP (OXCORE) and chiplet architecture (OXQUILT) with native Python/CUDA compatibility through OXPython, targeting edge-to-datacenter compute. First software revenue recorded in 2025. Positioned as "the Arm of GPUs."
- **round:** Seed
- **deal_type:** venture
- **amount_m:** 20.0
- **valuation_m:** null
- **date:** 2025-08-26
- **date_display:** 26-Aug-25
- **month_year:** Aug-25
- **quarter:** 3Q25
- **year:** 2025
- **location:** San Jose, USA
- **lead_investors:** MediaTek
- **co_investors:** Undisclosed
- **related_tickers:** [ARM, NVDA, AMD, INTC]
- **robotnik_take:** $20M seed at unicorn-grade ambition — Koduri's third act after Intel GPU exit, betting GPU IP licensing follows Arm's CPU playbook. Comp set is ARM (public, $130B+ mcap) and never-public competitors (Imagination). MediaTek as lead signals real customer intent for mobile/edge; the open question is whether OXPython actually runs CUDA workloads at competitive perf vs the native NVDA stack. Brand premium > tech maturity at this stage.
- **source:** https://www.hpcwire.com/off-the-wire/oxmiq-labs-emerges-from-stealth-with-software-defined-gpu-architecture-for-edge-to-data-center/
- **source_status:** verified
- **policy_exposure:** US_Export_Controls_China; US_CHIPS_Act
- **value_chain_tier:** IP & Design
- **bottleneck_risk:** Pre-commercial
- **DEDUP STATUS:** NEW

### ROW 4
- **entity_id:** maieutic-semiconductor
- **company:** Maieutic Semiconductor
- **sector:** Semiconductors
- **subsector:** EDA & IP
- **company_description:** Develops a generative-AI copilot specifically for analog integrated circuit design, targeting the still-manual portions of analog/mixed-signal layout that resist conventional EDA automation. Founders are veteran analog designers with 70+ semiconductor patents and >1B units shipped between them. India-headquartered with global commercial intent.
- **round:** Seed
- **deal_type:** venture
- **amount_m:** 4.15
- **valuation_m:** null
- **date:** 2025-07-30
- **date_display:** 30-Jul-25
- **month_year:** Jul-25
- **quarter:** 3Q25
- **year:** 2025
- **location:** Bengaluru, India
- **lead_investors:** Endiya Partners, Exfinity Venture Partners
- **co_investors:** Undisclosed
- **related_tickers:** [SNPS, CDNS]
- **robotnik_take:** $4.15M seed for analog-EDA copilot — comp set: Astrus (Canada, $8M Khosla seed, also physics-aware AI for analog) and Cognichip (US, $33M+$60M, broader scope). Maieutic is the cheapest entry point and India's first credible bet in EDA-AI; Endiya + Exfinity is a respectable domestic deeptech syndicate but lacks the US-VC distribution Cognichip enjoys. Analog automation remains the highest-value, lowest-penetration EDA segment — SNPS/CDNS have not cracked it natively.
- **source:** https://india.entrepreneur.com/news-and-trends/fabless-chip-startup-sensesemi-secures-inr-25-cr-seed/502074
- **source_status:** pending
- **policy_exposure:** None
- **value_chain_tier:** ""
- **bottleneck_risk:** Pre-commercial
- **DEDUP STATUS:** NEW
- **notes:** Source above is the Sensesemi article (used for cross-verification of canonical Bengaluru deeptech reporting); primary canonical Maieutic press release at https://www.maieuticsemi.com/news/maieutic-funding-news (WebFetch returned summary, no date). Yourstory.com primary blocked WebFetch but searched: confirms $4.15M July 2025. Set source_status pending pending replacement with canonical company URL on dedup pass.

### ROW 5
- **entity_id:** upscale-ai
- **company:** Upscale AI
- **sector:** Semiconductors
- **subsector:** Fabless Design
- **company_description:** Designs open-standard AI networking silicon, systems, and a SONiC/SAI-based network operating system for ultra-low-latency AI fabrics. Built on UALink and Ultra Ethernet open standards. Incubated by Auradine; led by Innovium/Cavium/Marvell veterans. Positioned as the open-stack alternative to NVIDIA Spectrum-X / Mellanox.
- **round:** Seed
- **deal_type:** venture
- **amount_m:** 100.0
- **valuation_m:** null
- **date:** 2025-09-17
- **date_display:** 17-Sep-25
- **month_year:** Sep-25
- **quarter:** 3Q25
- **year:** 2025
- **location:** Palo Alto, USA
- **lead_investors:** Mayfield, Maverick Silicon
- **co_investors:** StepStone Group, Celesta Capital, Xora Innovation, Qualcomm Ventures, Cota Capital, MVP Ventures, Stanford University
- **related_tickers:** [NVDA, AVGO, MRVL, ARM]
- **robotnik_take:** $100M "seed" is structural, not stage — closer to a stealth Series A with seed-style preferred. Comp set: NVDA Spectrum-X (proprietary, dominant), AVGO (Tomahawk silicon switching), MRVL (Innovium acquisition lineage). Upscale's open-standards thesis (UALink, UE) is a direct bet against NVDA lock-in; the syndicate (Mayfield + Qualcomm Ventures + StepStone) signals corporate-strategic intent. Already raised $200M Series A within months — round structure is more about capital-markets optics than capital need.
- **source:** https://upscaleai.com/press-release/
- **source_status:** verified
- **policy_exposure:** US_CHIPS_Act
- **value_chain_tier:** IP & Design
- **bottleneck_risk:** Pre-commercial
- **DEDUP STATUS:** NEW

### ROW 6
- **entity_id:** unconventional-ai
- **company:** Unconventional AI
- **sector:** Semiconductors
- **subsector:** Frontier Compute
- **company_description:** Founded by Naveen Rao (ex-Databricks AI head, MosaicML founder, Nervana → Intel) to build neuromorphic / analog-inspired computers targeting AI energy efficiency, modeled on biological systems' compute-per-joule envelope. First $475M tranche of planned $1B round; only public AI-hardware "seed" at $4.5B post-money valuation in 2025.
- **round:** Seed
- **deal_type:** venture
- **amount_m:** 475.0
- **valuation_m:** 4500.0
- **date:** 2025-12-09
- **date_display:** 09-Dec-25
- **month_year:** Dec-25
- **quarter:** 4Q25
- **year:** 2025
- **location:** USA (HQ not specified)
- **lead_investors:** Andreessen Horowitz, Lightspeed Venture Partners
- **co_investors:** Lux Capital, DCVC, Sequoia Capital, Future Ventures, Databricks, Jeff Bezos
- **related_tickers:** [NVDA, AMD, INTC]
- **robotnik_take:** $475M seed at $4.5B is the largest "seed" in semiconductor history — categorical noise; round label reflects pre-product status, not capital structure. Comp set is empty: closest analogs are Cerebras and Etched at later rounds, no neuromorphic incumbents at scale (Mythic wound down 2022). Rao's prior exits (MosaicML $1.3B to DDOG, Nervana to INTC) buy execution credibility; a16z+Lightspeed co-lead with $10M founder check signals conviction. Single-bet exposure for the sector — outcome binary.
- **source:** https://techcrunch.com/2025/12/09/unconventional-ai-confirms-its-massive-475m-seed-round/
- **source_status:** verified
- **policy_exposure:** US_CHIPS_Act
- **value_chain_tier:** ""
- **bottleneck_risk:** Pre-commercial
- **DEDUP STATUS:** NEW

### ROW 7
- **entity_id:** ricursive-intelligence
- **company:** Ricursive Intelligence
- **sector:** Semiconductors
- **subsector:** EDA & IP
- **company_description:** Frontier AI lab founded by Anna Goldie and Azalia Mirhoseini (creators of Google AlphaChip) targeting AI-driven automation across the full semiconductor design stack: architecture, RTL, verification, physical design. Built around recursive feedback loop where AI designs chips that train more advanced AI models. First product still pre-disclosure.
- **round:** Seed
- **deal_type:** venture
- **amount_m:** 35.0
- **valuation_m:** 750.0
- **date:** 2025-12-02
- **date_display:** 02-Dec-25
- **month_year:** Dec-25
- **quarter:** 4Q25
- **year:** 2025
- **location:** Palo Alto, USA
- **lead_investors:** Sequoia Capital
- **co_investors:** Undisclosed
- **related_tickers:** [SNPS, CDNS, NVDA]
- **robotnik_take:** $35M seed at $750M post — Sequoia paying full founder premium for the AlphaChip team. Comp set: Cognichip ($93M cumulative), Astrus ($8M Khosla), Chipmind ($2.5M); Ricursive is the deepest pedigree, broadest scope (architecture-to-PD), highest valuation. Series A ($300M / $4B post) closed within 8 weeks — fastest deeptech markup of 2025-26. SNPS / CDNS native AI is the structural competitor; whether incumbent-built or startup-built EDA-AI wins depends on data access, not models.
- **source:** https://www.prnewswire.com/news-releases/ricursive-intelligence-launches-frontier-ai-lab-to-transform-semiconductor-design-and-accelerate-path-toward-artificial-superintelligence-302630776.html
- **source_status:** verified
- **policy_exposure:** US_CHIPS_Act
- **value_chain_tier:** ""
- **bottleneck_risk:** Pre-commercial
- **DEDUP STATUS:** DEDUP-CHECK (Ricursive Series A already in dataset 2026-01-26; this Seed is a distinct round 8 weeks earlier — ADD as separate row)

### ROW 8
- **entity_id:** vertical-compute
- **company:** Vertical Compute
- **sector:** Semiconductors
- **subsector:** Frontier Compute
- **company_description:** imec spin-off (Belgium) developing 3D-integrated memory stacked directly on compute logic within a single 300mm wafer manufacturing process. Reduces memory–compute distance from cm to nm scale, targeting AI inference / HBM-class workloads with chiplet form factor. First test chip taped-out in 2025.
- **round:** Seed (extension)
- **deal_type:** venture
- **amount_m:** 42.9
- **valuation_m:** null
- **date:** 2026-03-04
- **date_display:** 04-Mar-26
- **month_year:** Mar-26
- **quarter:** 1Q26
- **year:** 2026
- **location:** Louvain-la-Neuve, Belgium
- **lead_investors:** Quantonation
- **co_investors:** Flanders Future Techfund, Wallonie Entreprendre, Sambrinvest, Noshaq, InvestBW, Drysdale Ventures, Kima Ventures, Eurazeo, XAnge, Vector Gestion, imec.xpand, imec
- **related_tickers:** [TSM, NVDA]
- **robotnik_take:** €37M ($42.9M) seed extension brings total seed to €57M — comp set: SK hynix HBM stacked memory (incumbent), Niobium ($23M Seed, cryo memory), AheadComputing (compute layer only). Vertical Compute is the only credible European 3D memory-on-logic play. imec lineage is the moat: process integration access most startups can't replicate. Strategic frame: memory bandwidth is now the binding constraint on AI training, and HBM is supply-constrained through 2027 — any credible alternative architecture commands premium even pre-product.
- **source:** https://sifted.eu/articles/vertical-compute-ai-chips-memory-37m
- **source_status:** verified
- **policy_exposure:** EU_Chips_Act
- **value_chain_tier:** ""
- **bottleneck_risk:** Pre-commercial
- **native_currency:** EUR
- **native_amount:** 37.0
- **fx_source:** ECB reference 2026-03-04 (~1.16 USD/EUR)
- **fx_rate_used:** 0.862
- **DEDUP STATUS:** NEW

### ROW 9
- **entity_id:** quamcore
- **company:** QuamCore
- **sector:** Semiconductors
- **subsector:** Frontier Compute
- **company_description:** Israeli quantum compute startup developing superconducting quantum processor architecture engineered to integrate up to 1 million qubits in a single cryostat, reducing inter-qubit cabling by >1000× via on-chip control electronics. Founded by Mobileye / Technion / Weizmann veterans. Out of stealth March 2025.
- **round:** Seed
- **deal_type:** venture
- **amount_m:** 9.0
- **valuation_m:** null
- **date:** 2025-03-13
- **date_display:** 13-Mar-25
- **month_year:** Mar-25
- **quarter:** 1Q25
- **year:** 2025
- **location:** Herzliya, Israel
- **lead_investors:** Viola Ventures
- **co_investors:** Earth & Beyond, Surround Ventures, Israel Innovation Authority
- **related_tickers:** [IBM, IONQ, RGTI]
- **robotnik_take:** $9M seed for superconducting million-qubit cryo-integration — comp set: IBM Quantum (incumbent, integrated stack), IONQ + RGTI (public, sub-1k physical qubits), QuEra, PsiQuantum (private $1B+). QuamCore's distinct claim is on-chip control electronics that eliminate the cabling explosion that plagues IBM's roadmap past 1k qubits. Series A ($26M Aug 2025) closed within 5 months — pace of pull suggests technical milestone, not just narrative. Single-bet, binary.
- **source:** https://thequantuminsider.com/2025/03/12/quamcore-emerges-from-stealth-with-9-million-in-seed-funding-to-build-worlds-first-scalable-1-million-qubit-quantum-computer/
- **source_status:** verified
- **policy_exposure:** None
- **value_chain_tier:** ""
- **bottleneck_risk:** Pre-commercial
- **DEDUP STATUS:** NEW

### ROW 10
- **entity_id:** isentroniq
- **company:** Isentroniq
- **sector:** Semiconductors
- **subsector:** Silicon & Substrates
- **company_description:** Paris-based quantum infrastructure startup developing dense, low-thermal-load cryogenic interconnects that enable 1000× more qubits per dilution refrigerator. Targets the wiring bottleneck that caps superconducting quantum systems at a few hundred qubits today. Founded May 2025 by ETH Zürich quantum PhD and ex-Bain consultant.
- **round:** Pre-Seed
- **deal_type:** venture
- **amount_m:** 8.7
- **valuation_m:** null
- **date:** 2025-10-14
- **date_display:** 14-Oct-25
- **month_year:** Oct-25
- **quarter:** 4Q25
- **year:** 2025
- **location:** Paris, France
- **lead_investors:** Heartcore Capital
- **co_investors:** OVNI Capital, Kima Ventures, IXCORE Group, Better Angle, EPSL VC, Bpifrance
- **related_tickers:** [IBM, IONQ, RGTI]
- **robotnik_take:** €7.5M ($8.7M) pre-seed at 5 months old — French quantum-supply-chain play that complements QuamCore's on-chip approach from the other direction (rack-level wiring vs. control-electronics integration). Comp set: Bluefors (cryostat incumbent, private), Quantcore (UK, niobium components). Heartcore lead with full France 2030 / Bpifrance ecosystem support is structurally similar to how Pasqal scaled. Pre-commercial; binding constraint is whether IBM/Rigetti/Google adopt third-party cryo wiring or keep in-house.
- **source:** https://thequantuminsider.com/2025/10/14/isentroniq-raises-e7-5m-to-fix-quantum-computings-scalabilityproblem/
- **source_status:** verified
- **policy_exposure:** EU_Chips_Act
- **value_chain_tier:** ""
- **bottleneck_risk:** Pre-commercial
- **native_currency:** EUR
- **native_amount:** 7.5
- **fx_source:** ECB reference 2025-10-14 (~1.16 USD/EUR)
- **fx_rate_used:** 0.862
- **DEDUP STATUS:** NEW

### ROW 11
- **entity_id:** quantcore
- **company:** Quantcore
- **sector:** Semiconductors
- **subsector:** Silicon & Substrates
- **company_description:** University of Glasgow spin-out building the only UK-domestic manufacturing line for niobium-based superconducting components (processors, resonators, sensors) for quantum computing, secure comms, and medical imaging. Operates from James Watt Nanofabrication Centre. Sovereign-supply-chain positioning under UK National Quantum Strategy.
- **round:** Seed
- **deal_type:** venture
- **amount_m:** 3.4
- **valuation_m:** null
- **date:** 2026-02-24
- **date_display:** 24-Feb-26
- **month_year:** Feb-26
- **quarter:** 1Q26
- **year:** 2026
- **location:** Glasgow, United Kingdom
- **lead_investors:** PXN Ventures, Blackfinch Ventures, Scottish Enterprise
- **co_investors:** Quantum Exponential, STAC
- **related_tickers:** [IBM, IONQ, RGTI]
- **robotnik_take:** £2.5M ($3.4M) seed for UK-sovereign superconducting components — comp set: Quantum Motion, Oxford Instruments NanoScience (Imperial-adjacent), no direct US/EU analog. Strategic frame is post-CHIPS / post-EU Chips Act: every major bloc now wants domestic quantum supply. Quantcore is the smallest pure-play but the only one with active fab output at Glasgow JWNC. Government-grant ratio (Scottish Enterprise co-lead) signals policy-grade derisking, not commercial pull.
- **source:** https://thequantuminsider.com/2026/02/24/quantcore-raises-2-5m-uk-quantum-manufacturing/
- **source_status:** verified
- **policy_exposure:** UK_National_Quantum_Strategy
- **value_chain_tier:** ""
- **bottleneck_risk:** Pre-commercial
- **native_currency:** GBP
- **native_amount:** 2.5
- **fx_source:** BoE reference 2026-02-24 (~1.36 USD/GBP)
- **fx_rate_used:** 0.735
- **DEDUP STATUS:** NEW

### ROW 12
- **entity_id:** photon-ip
- **company:** PHOTON IP
- **sector:** Semiconductors
- **subsector:** Frontier Compute
- **company_description:** Eindhoven-based silicon photonics startup developing process to integrate active III-V materials (indium phosphide) onto silicon substrates for energy-efficient photonic engines used in datacenter optical interconnects and sensing. Founded 2020; €2M+ in prior EIC grants. Later rebranded to Photon Bridge in Sep 2025.
- **round:** Seed
- **deal_type:** venture
- **amount_m:** 4.9
- **valuation_m:** null
- **date:** 2025-01-13
- **date_display:** 13-Jan-25
- **month_year:** Jan-25
- **quarter:** 1Q25
- **year:** 2025
- **location:** Eindhoven, Netherlands
- **lead_investors:** Innovation Industries
- **co_investors:** Faber, BOM, PhotonDelta
- **related_tickers:** [ASML, NVDA, MRVL]
- **robotnik_take:** €4.75M ($4.9M) seed for III-V-on-silicon photonics integration — comp set: Ayar Labs (US, $300M Series D), Lightmatter (US, growth), Aledia (FR, microLED-adjacent). PHOTON IP is the smallest in the photonic-integration cohort but sits in the Eindhoven PhotonDelta cluster, the only EU silicon-photonics ecosystem at scale. Rebrand to Photon Bridge 9 months later suggests pivot or refocus; rate of derisking remains pre-commercial.
- **source:** https://tech.eu/2025/01/14/netherlands-startup-photon-ip-raises-4-75m-for-low-energy-optical-chips/
- **source_status:** verified
- **policy_exposure:** EU_Chips_Act
- **value_chain_tier:** ""
- **bottleneck_risk:** Pre-commercial
- **native_currency:** EUR
- **native_amount:** 4.75
- **fx_source:** ECB reference 2025-01-13 (~1.04 USD/EUR)
- **fx_rate_used:** 0.962
- **DEDUP STATUS:** NEW

### ROW 13
- **entity_id:** volantis
- **company:** Volantis
- **sector:** Semiconductors
- **subsector:** Frontier Compute
- **company_description:** California silicon-photonics startup developing photonic interconnects using directly-modulated VCSELs (vertical cavity surface-emitting lasers) integrated with on-chip optical waveguides — explicitly positioned as a departure from conventional silicon photonics. Targets AI datacenter inter-chip bandwidth bottleneck. Sam Altman has backed since April 2022 (pre-stealth).
- **round:** Seed
- **deal_type:** venture
- **amount_m:** 9.0
- **valuation_m:** null
- **date:** 2025-06-11
- **date_display:** 11-Jun-25
- **month_year:** Jun-25
- **quarter:** 2Q25
- **year:** 2025
- **location:** San Mateo, USA
- **lead_investors:** Undisclosed
- **co_investors:** Sam Altman, Alex Wang (Scale AI), Trevor Blackwell (Y Combinator)
- **related_tickers:** [AVGO, MRVL, NVDA]
- **robotnik_take:** $9M seed for VCSEL-based photonic compute — divergent bet vs. the dominant silicon-photonics path (Ayar Labs, Lightmatter, NcodiN). Comp set is mostly negative: every other photonic-interconnect startup uses heterogeneous Si + III-V; Volantis claims VCSEL direct modulation is the path forward. Founder-backed by Altman pre-public commitment to the AI infra thesis (2022) signals high-conviction angel layer, but the round lacks a named institutional lead — a structural risk flag for Series A pricing.
- **source:** https://www.optica-opn.org/home/industry/2025/july/volantis_snags_us$9_million_for_photonic_interconnects/
- **source_status:** verified
- **policy_exposure:** US_CHIPS_Act
- **value_chain_tier:** ""
- **bottleneck_risk:** Pre-commercial
- **DEDUP STATUS:** NEW

### ROW 14
- **entity_id:** pseudolithic
- **company:** PseudolithIC
- **sector:** Semiconductors
- **subsector:** Fabless Design
- **company_description:** UCSB-rooted RF chiplet startup integrating compound-semiconductor (GaN, GaAs, InP) chiplets with silicon substrates for high-performance wireless products — millimeter-wave power amplifiers, low-noise amplifiers — targeting 5G/6G, satellite communications, aerospace. ~15-person team in Santa Barbara.
- **round:** Seed
- **deal_type:** venture
- **amount_m:** 6.0
- **valuation_m:** null
- **date:** 2025-01-27
- **date_display:** 27-Jan-25
- **month_year:** Jan-25
- **quarter:** 1Q25
- **year:** 2025
- **location:** Santa Barbara, USA
- **lead_investors:** Entrada Ventures
- **co_investors:** Foothill Ventures, Uncork Capital
- **related_tickers:** [QCOM, MRVL, AVGO]
- **robotnik_take:** $6M seed for compound-semi chiplet integration in RF — comp set: MACOM (public), Qorvo (public), and emerging private MMICs (Skywater, Wolfspeed RF). PseudolithIC's positioning is the chiplet-era response to fully-integrated MMICs: silicon for digital + III-V chiplets for RF front-end. UCSB lineage and Entrada (semi-specialist) lead suggests technical proof; the win condition is GaN-on-Si yield economics at scale. Pre-commercial.
- **source:** https://www.entradaventures.com/post/pseudolithic-inc-raises-6m-in-seed-funding-to-revolutionize-wireless-chips-with-proprietary-chiple
- **source_status:** verified
- **policy_exposure:** US_CHIPS_Act
- **value_chain_tier:** ""
- **bottleneck_risk:** Pre-commercial
- **DEDUP STATUS:** NEW

### ROW 15
- **entity_id:** oso-semiconductor
- **company:** Oso Semiconductor
- **sector:** Semiconductors
- **subsector:** Fabless Design
- **company_description:** UC Berkeley spinout designing low-loss beamforming chipsets for phased-array antennas targeting SATCOM, 5G mmWave, and radar systems. Proprietary "Combiner-First" architecture for phase shifting and signal combining claims up to 4× efficiency improvement vs. conventional phased-array silicon. Founded 2022.
- **round:** Seed
- **deal_type:** venture
- **amount_m:** 5.2
- **valuation_m:** null
- **date:** 2025-02-12
- **date_display:** 12-Feb-25
- **month_year:** Feb-25
- **quarter:** 1Q25
- **year:** 2025
- **location:** Berkeley, USA
- **lead_investors:** Engine Ventures
- **co_investors:** Entrada Ventures, Berkeley SkyDeck, J-Ventures
- **related_tickers:** [QCOM, MRVL, ASTS, IRDM]
- **robotnik_take:** $5.2M seed for satcom beamforming silicon — comp set: Qualcomm (incumbent), Anokiwave (acquired by Qorvo), and the public satcom names (IRDM, ASTS) that consume this kind of phased-array IC. Oso's edge is academic — Berkeley's phased-array research lineage produced Sapient Networks (acq Broadcom) and others. Engine Ventures lead signals real DoD/dual-use overlap. 4× efficiency claim depends on production yield, not architecture; pre-commercial.
- **source:** https://www.satellitetoday.com/finance/2025/02/12/oso-semiconductor-secures-5-2m-in-seed-funding-for-phased-array-chipsets/
- **source_status:** verified
- **policy_exposure:** US_CHIPS_Act
- **value_chain_tier:** ""
- **bottleneck_risk:** Pre-commercial
- **DEDUP STATUS:** NEW

### ROW 16
- **entity_id:** astrus
- **company:** Astrus
- **sector:** Semiconductors
- **subsector:** EDA & IP
- **company_description:** Toronto/Waterloo AI startup building physics-aware reinforcement-learning models specifically for analog chip layout — generates thousands of candidate layouts in seconds against months of manual engineering today. Co-founders include former satellite-sensor chip designer and reinforcement-learning researcher trained by AlphaGo's Martin Müller.
- **round:** Seed
- **deal_type:** venture
- **amount_m:** 8.0
- **valuation_m:** null
- **date:** 2025-09-09
- **date_display:** 09-Sep-25
- **month_year:** Sep-25
- **quarter:** 3Q25
- **year:** 2025
- **location:** Toronto, Canada
- **lead_investors:** Khosla Ventures
- **co_investors:** Pradeep Sindhu, 1517 Fund, Drive Capital, Alumni Ventures
- **related_tickers:** [SNPS, CDNS]
- **robotnik_take:** $8M seed for physics-aware analog-EDA — direct comp: Maieutic ($4.15M, India) and Cognichip ($93M cumulative, US, broader scope). Astrus's claim is the deepest RL training pedigree (Müller-trained) targeting the hardest unautomated EDA segment (analog layout). Khosla lead is structurally bullish for AI-on-EDA; Pradeep Sindhu (Juniper founder) adds chip-industry credibility. Strategic frame: analog layout is where SNPS+CDNS revenue per design is highest and incumbent tools are weakest — biggest white-space in EDA.
- **source:** https://pulse2.com/astrus-8-million-raised-to-transform-analog-chip-design-with-physics-aware-ai/
- **source_status:** verified
- **policy_exposure:** US_CHIPS_Act
- **value_chain_tier:** ""
- **bottleneck_risk:** Pre-commercial
- **DEDUP STATUS:** NEW

### ROW 17
- **entity_id:** sensesemi-technologies
- **company:** Sensesemi Technologies
- **sector:** Semiconductors
- **subsector:** Fabless Design
- **company_description:** Bengaluru-based fabless designer of integrated edge-AI silicon combining AI inferencing, wireless mesh connectivity, and precision analog signal processing on a single chip. Targets industrial IoT, automotive ADAS, and medical devices (cardiac monitoring, smart drug delivery). DLI-approved under India's Design Linked Incentive scheme. First two test chips tape-out planned 2026.
- **round:** Seed
- **deal_type:** venture
- **amount_m:** 2.75
- **valuation_m:** null
- **date:** 2026-01-21
- **date_display:** 21-Jan-26
- **month_year:** Jan-26
- **quarter:** 1Q26
- **year:** 2026
- **location:** Bengaluru, India
- **lead_investors:** Piper Serica
- **co_investors:** LetsVenture Angel Fund, Sun Icon Ventures, MyAsiaVC, Whitepine Investments, Jain Oncor
- **related_tickers:** [QCOM, NXPI, STM]
- **robotnik_take:** ₹25 Cr ($2.75M) seed for edge-AI silicon at Indian fabless rate card — comp set: Mindgrove (India, $10M cumulative), BigEndian ($9M cumulative), HrdWyr ($13M Series A). Sensesemi's edge is multi-modal integration (AI + wireless + analog) for medical/industrial verticals where DLI subsidies move volume. Founded 2014 but first capital raise — atypical late seed for an 11-year-old company suggests prior bootstrapping + DLI grant runway; commercial chip not yet taped out.
- **source:** https://india.entrepreneur.com/news-and-trends/fabless-chip-startup-sensesemi-secures-inr-25-cr-seed/502074
- **source_status:** verified
- **policy_exposure:** India_DLI_Scheme
- **value_chain_tier:** ""
- **bottleneck_risk:** Pre-commercial
- **native_currency:** INR
- **native_amount:** 250.0
- **fx_source:** RBI reference 2026-01-21 (~91 INR/USD)
- **fx_rate_used:** 91.0
- **DEDUP STATUS:** NEW

### ROW 18
- **entity_id:** mueon
- **company:** Mueon
- **sector:** Semiconductors
- **subsector:** Fabless Design
- **company_description:** Portland Oregon startup developing modular stackable "Cubelets" that integrate compute, memory, power delivery, and thermal management into a single physical unit — replacing rack-of-servers form factor for AI datacenters. Team includes shipped-billions-of-units veterans in CPU, GPU, memory architecture, power delivery, and IO design from prior Intel/AMD generations.
- **round:** Seed
- **deal_type:** venture
- **amount_m:** 15.5
- **valuation_m:** null
- **date:** 2025-09-17
- **date_display:** 17-Sep-25
- **month_year:** Sep-25
- **quarter:** 3Q25
- **year:** 2025
- **location:** Portland, USA
- **lead_investors:** Intel Capital
- **co_investors:** Geodesic Alliance Fund, Oregon Venture Fund
- **related_tickers:** [NVDA, AMD, INTC, AVGO]
- **robotnik_take:** $15.5M seed for system-level chiplet form-factor — comp set: NVIDIA NVL72 (productized rack-scale, $30k+ per node), AMD MI300X racks, no startup analog at this integration level. Mueon's "Cubelet" framing is system-scale chiplet, closer to a custom motherboard architecture than a chip — value capture depends on whether hyperscalers buy modular units or just custom-design their own. Intel Capital lead is a clear strategic-corp signal; team pedigree (Intel/AMD veterans) carries the round.
- **source:** https://www.prnewswire.com/news-releases/mueon-emerges-from-stealth-with-15-5m-seed-to-redefine-data-centers-for-the-ai-era-302558448.html
- **source_status:** verified
- **policy_exposure:** US_CHIPS_Act
- **value_chain_tier:** ""
- **bottleneck_risk:** Pre-commercial
- **DEDUP STATUS:** NEW

### ROW 19
- **entity_id:** cnuic
- **company:** Cnuic
- **sector:** Semiconductors
- **subsector:** Equipment
- **company_description:** Edinburgh, Scotland startup developing reconfigurable, light-based photolithography device — a working prototype that uses structured-light properties to enable rapid 3D-controlled production of photonic chips, metalenses, AR/VR waveguides, and 3D photonic crystals. Targets the photonic-chip manufacturing bottleneck.
- **round:** Pre-Seed
- **deal_type:** venture
- **amount_m:** 3.0
- **valuation_m:** null
- **date:** 2026-04-28
- **date_display:** 28-Apr-26
- **month_year:** Apr-26
- **quarter:** 2Q26
- **year:** 2026
- **location:** Edinburgh, United Kingdom
- **lead_investors:** Tensor Ventures, Blank Space Ventures
- **co_investors:** Silicon Roundabout Ventures, Phasechange, SANDS, Superlative
- **related_tickers:** [ASML, AMAT, KLAC]
- **robotnik_take:** $3M pre-seed for reconfigurable photolithography — comp set: ASML (incumbent, photolith but for silicon), Heidelberg Instruments (private, maskless lithography). Cnuic's claim is reconfigurable / 3D / multi-material photonic-chip patterning at scale — adjacent rather than competitive to ASML's silicon EUV. Tensor + Blank Space lead signals high-conviction seed, but the address-market (photonic-chip fabs) is still small in 2026. Pre-commercial; binding constraint is fab adoption, not technology.
- **source:** https://tech.eu/2026/04/28/cnuic-secures-eur3m-pre-seed-to-unlock-next-generation-photonic-chip-production/
- **source_status:** verified
- **policy_exposure:** UK_National_Quantum_Strategy
- **value_chain_tier:** ""
- **bottleneck_risk:** Pre-commercial
- **native_currency:** USD
- **native_amount:** 3.0
- **fx_source:** N/A
- **fx_rate_used:** null
- **DEDUP STATUS:** NEW

### ROW 20
- **entity_id:** skycore-semiconductors
- **company:** Skycore Semiconductors
- **sector:** Semiconductors
- **subsector:** Power & Analog
- **company_description:** Danish startup with silicon-validated Power IC platform engineered for emerging 800V High-Voltage DC (HVDC) AI datacenter architectures — addresses the physical limits of 54VDC distribution when racks exceed 200kW. First focus is rack-level power conversion for hyperscale AI racks.
- **round:** Seed
- **deal_type:** venture
- **amount_m:** 5.8
- **valuation_m:** null
- **date:** 2025-11-13
- **date_display:** 13-Nov-25
- **month_year:** Nov-25
- **quarter:** 4Q25
- **year:** 2025
- **location:** Copenhagen, Denmark
- **lead_investors:** Amadeus APEX Technology Fund
- **co_investors:** First Momentum Ventures, Mätch VC, Balnord
- **related_tickers:** [WOLF, AVGO, NVDA, MRVL]
- **robotnik_take:** €5M ($5.8M) seed for 800V HVDC power ICs targeting AI datacenter racks — comp set: Empower Semiconductor ($140M+ Series D, IVR incumbent), Navitas (NVTS, GaN power), Vertical Semiconductor ($11M seed, vGaN). Skycore is the only Denmark-domiciled power-semi seed in 2025, leveraging Northern European wind-power-conversion expertise. Strategic frame: 800V HVDC is the rack-architecture transition NVDA/AMD will force across hyperscalers post-2026; first credible power-IC vendors win 2-3 year incumbency.
- **source:** https://arcticstartup.com/skycore-semiconductors-raises-e5m-seed/
- **source_status:** verified
- **policy_exposure:** EU_Chips_Act
- **value_chain_tier:** ""
- **bottleneck_risk:** Pre-commercial
- **native_currency:** EUR
- **native_amount:** 5.0
- **fx_source:** ECB reference 2025-11-13 (~1.16 USD/EUR)
- **fx_rate_used:** 0.862
- **DEDUP STATUS:** NEW

### ROW 21
- **entity_id:** chiral
- **company:** Chiral
- **sector:** Semiconductors
- **subsector:** Equipment
- **company_description:** ETH Zurich + Empa spin-off (Switzerland) developing robotic wafer-scale nanomaterial integration platform — automated, contamination-free placement of 2D materials (graphene, transition-metal dichalcogenides, hexagonal boron nitride) into silicon wafers for post-silicon transistors. Sub-micron alignment, room-temperature transfer. Founded 2023.
- **round:** Seed
- **deal_type:** venture
- **amount_m:** 12.0
- **valuation_m:** null
- **date:** 2026-02-06
- **date_display:** 06-Feb-26
- **month_year:** Feb-26
- **quarter:** 1Q26
- **year:** 2026
- **location:** Zurich, Switzerland
- **lead_investors:** Crane Venture Partners
- **co_investors:** Quantonation, HCVC, Founderful, Innosuisse
- **related_tickers:** [ASML, AMAT, LRCX, KLAC]
- **robotnik_take:** $12M seed for wafer-scale 2D-material integration — comp set: ASML / AMAT / LRCX as deposition+lithography incumbents (none of which directly handle nanomaterial transfer at wafer scale). Chiral is positioned as the "next ASML" for post-silicon (Sifted's framing), which is overclaim — but the underlying equipment niche is real: every credible post-CMOS transistor candidate requires sub-micron precise 2D-material placement, and nobody has automated it. ETH+Empa lineage is genuine deep-tech moat; commercial timeline is 5+ years out.
- **source:** https://www.globenewswire.com/news-release/2026/02/06/3233564/0/en/Chiral-raises-12M-to-unlock-post-silicon-computing-beyond-Moore-s-Law.html
- **source_status:** verified
- **policy_exposure:** EU_Chips_Act
- **value_chain_tier:** Equipment & Tools
- **bottleneck_risk:** Pre-commercial
- **DEDUP STATUS:** NEW

### ROW 22
- **entity_id:** uviquity
- **company:** Uviquity
- **sector:** Semiconductors
- **subsector:** Fabless Design
- **company_description:** Develops solid-state far-UVC (200-230nm) semiconductor light sources via proprietary photonic integrated circuit that couples blue laser into frequency-doubling waveguides — single-chip alternative to bulb-based far-UVC for chemical-free disinfection of air, food, water. Founded 2022.
- **round:** Seed
- **deal_type:** venture
- **amount_m:** 6.6
- **valuation_m:** null
- **date:** 2025-05-07
- **date_display:** 07-May-25
- **month_year:** May-25
- **quarter:** 2Q25
- **year:** 2025
- **location:** USA (HQ not specified)
- **lead_investors:** Emerald Development Managers
- **co_investors:** AgFunder, MANN+HUMMEL
- **related_tickers:** []
- **robotnik_take:** $6.6M seed for far-UVC PIC — adjacent semiconductor application; closest comp is GE Current and the bulk far-UVC bulb incumbents (Ushio), no fabless-chip analog. Uviquity's positioning straddles photonics + life-sciences supply chain; MANN+HUMMEL (filtration) as strategic co-investor signals industrial-offtake intent. Thin comp set — true niche bet. Pre-commercial; binding constraint is regulatory adoption (FDA, EPA), not silicon.
- **source:** https://www.semiconductor-today.com/news_items/2025/may/uviquity-090525.shtml
- **source_status:** verified
- **policy_exposure:** None
- **value_chain_tier:** ""
- **bottleneck_risk:** Pre-commercial
- **DEDUP STATUS:** NEW

### ROW 23
- **entity_id:** lucidean
- **company:** Lucidean
- **sector:** Semiconductors
- **subsector:** Frontier Compute
- **company_description:** Santa Barbara, CA AI interconnect company developing 3.2 / 6.4 Tbps coherent optical transceivers for AI datacenter fabrics. CohZero platform is a "coherent-lite" architecture targeting coherent-class reach and signal integrity at IMDD-class power and cost. Founded by UCSB compound-semiconductor / optical-link veterans (Schow, Coldren academic co-founders).
- **round:** Seed
- **deal_type:** venture
- **amount_m:** 18.0
- **valuation_m:** null
- **date:** 2025-12-23
- **date_display:** 23-Dec-25
- **month_year:** Dec-25
- **quarter:** 4Q25
- **year:** 2025
- **location:** Santa Barbara, USA
- **lead_investors:** Entrada Ventures, Koch Disruptive Technologies
- **co_investors:** Foothill Ventures, M Ventures, Cerberus Ventures, Raptor Group
- **related_tickers:** [AVGO, MRVL, INFN, COHR]
- **robotnik_take:** $18M seed for coherent-lite AI datacenter optics — comp set: Marvell ($24M DustPhotonics acq for ~$1.3B in 2025), Broadcom Tomahawk-class silicon, Coherent + Lumentum (legacy coherent). Lucidean's framing is the gap between high-power coherent (long-haul) and low-power IMDD (datacenter intra-rack) — a $5-10B addressable market once 1.6T+ AI fabrics scale. KDT (Koch family deeptech) lead signals patient capital for fab-process roadmap.
- **source:** https://www.businesswire.com/news/home/20251223818151/en/Lucidean-Raises-Series-Seed-Funding-to-Accelerate-Next-Gen-Coherent-Optical-Links-for-Data-Centers-Announces-Dr.-James-Raring-as-Chief-Executive-Officer
- **source_status:** verified
- **policy_exposure:** US_CHIPS_Act
- **value_chain_tier:** ""
- **bottleneck_risk:** Pre-commercial
- **DEDUP STATUS:** NEW

### ROW 24
- **entity_id:** claros
- **company:** Claros
- **sector:** Semiconductors
- **subsector:** Power & Analog
- **company_description:** Los Angeles startup commercializing integrated voltage regulator (IVR) ICs and a DC-native Power Gateway for AI datacenters — claims 30% power-loss reduction vs. typical IVRs. Three IVR designs already fabbed (Samsung partnership), fourth in development. Founded 2024 by ex-Red Cell Partners alumni.
- **round:** Seed
- **deal_type:** venture
- **amount_m:** 30.0
- **valuation_m:** null
- **date:** 2026-03-19
- **date_display:** 19-Mar-26
- **month_year:** Mar-26
- **quarter:** 1Q26
- **year:** 2026
- **location:** Los Angeles, USA
- **lead_investors:** General Catalyst, Red Cell Partners
- **co_investors:** Systemiq Capital, Aero X Ventures, Trenches Capital
- **related_tickers:** [NVDA, AVGO, MPWR, MRVL]
- **robotnik_take:** $30M seed for chip-to-grid datacenter power architecture — comp set: Empower Semiconductor ($140M+ Series D), Monolithic Power Systems (MPWR public), Vicor (VICR public), emerging private IVR (Vertical Semi, Skycore). Claros differentiates by spanning IVR (silicon) + Power Gateway (DC distribution) — full-stack approach to data-center efficiency. Red Cell + General Catalyst lead at $30M is unusually large for Seed naming; comparable to Mueon ($15.5M Intel-led) in form-factor ambition. Pre-commercial.
- **source:** https://www.datacenterdynamics.com/en/news/power-management-company-claros-raises-30m-seed-round/
- **source_status:** pending
- **policy_exposure:** US_CHIPS_Act
- **value_chain_tier:** ""
- **bottleneck_risk:** Pre-commercial
- **DEDUP STATUS:** NEW
- **notes:** DCD URL returned 403 on direct WebFetch; primary canonical confirmed via Axios (https://www.axios.com/2026/03/19/claros-seed-data-center-energy-loss) and BusinessWire press (https://www.businesswire.com/news/home/20260319469046/en/...) which both 200'd on cross-check. source_status pending pending swap to verified canonical on next pass.

### ROW 25
- **entity_id:** pinc-technologies
- **company:** PINC Technologies
- **sector:** Semiconductors
- **subsector:** Frontier Compute
- **company_description:** Caltech spin-out (Pasadena, CA) developing integrated nonlinear photonic devices and circuits for quantum information processing, optical communications, biomedical sensing, and industrial photonics. Founded 2023. Seed+ round closes a multi-tranche $6.8M raise.
- **round:** Seed (extension)
- **deal_type:** venture
- **amount_m:** 6.8
- **valuation_m:** null
- **date:** 2025-10-01
- **date_display:** 01-Oct-25
- **month_year:** Oct-25
- **quarter:** 4Q25
- **year:** 2025
- **location:** Pasadena, USA
- **lead_investors:** Quantonation
- **co_investors:** Wilson Hill Ventures, Freeflow Ventures, Hamamatsu Ventures, Qubits Ventures, Santec, Caltech Seed Fund
- **related_tickers:** [HCKHF, IPGP]
- **robotnik_take:** $6.8M seed+ for nonlinear photonics — comp set: NcodiN ($16M seed, also nonlinear-photonic interposer); Lightium, Akhetonics, Enlightra (all photonic-compute adjacents). PINC's distinct positioning is nonlinear (vs. linear) photonics — frequency conversion, parametric amplification — that unlocks quantum + industrial sensing applications closed to standard silicon photonics. Quantonation lead aligns with quantum-thesis discipline; Hamamatsu + Santec corporate participation signals real off-take pipeline.
- **source:** https://thequantuminsider.com/2025/10/02/pinc-technologies-emerges-from-stealth-with-6-8m-in-funding-to-unlock-scalable-nonlinear-photonics/
- **source_status:** verified
- **policy_exposure:** US_CHIPS_Act
- **value_chain_tier:** ""
- **bottleneck_risk:** Pre-commercial
- **DEDUP STATUS:** NEW

### ROW 26
- **entity_id:** euqlid
- **company:** EuQlid
- **sector:** Semiconductors
- **subsector:** Equipment
- **company_description:** College Park, MD startup commercializing Qu-MRI — a quantum diamond-microscope platform using synthetic-diamond nitrogen-vacancy centers for non-destructive 3D imaging of buried currents in semiconductor devices and battery cells. One-micron resolution, AI-driven magnetic-field analysis. Founded by Harvard/Yale/UMD physicists.
- **round:** Seed
- **deal_type:** venture
- **amount_m:** 3.0
- **valuation_m:** null
- **date:** 2025-11-04
- **date_display:** 04-Nov-25
- **month_year:** Nov-25
- **quarter:** 4Q25
- **year:** 2025
- **location:** College Park, USA
- **lead_investors:** QDNL Participations
- **co_investors:** Quantonation
- **related_tickers:** [KLAC, AMAT, ONTO]
- **robotnik_take:** $3M seed for quantum metrology — comp set: KLAC ($90B+ mcap), Onto Innovation, none with NV-center-based imaging at semiconductor scale. EuQlid is the first commercial quantum-diamond microscope startup to apply NV magnetometry to inline semiconductor inspection — adjacent to the SEM/X-ray inspection workflow rather than replacing it. $1.5M early revenue at announce is rare for a $3M seed; indicates traction with research labs. Pre-commercial for inline fab adoption.
- **source:** https://siliconangle.com/2025/11/04/quantum-diamond-microscope-startup-euqlid-launches-3m/
- **source_status:** verified
- **policy_exposure:** US_CHIPS_Act
- **value_chain_tier:** Equipment & Tools
- **bottleneck_risk:** Pre-commercial
- **DEDUP STATUS:** NEW

### ROW 27 (DEDUP-CHECK candidate held for flag review)
- **entity_id:** vinci
- **company:** Vinci
- **sector:** Semiconductors
- **subsector:** EDA & IP
- **company_description:** Stealth-era hardware-engineering AI startup announcing both Seed (Eclipse-led) and Series A (Xora-led) simultaneously on emergence Dec 2 2025. Builds physics-foundation model for semiconductor thermal/EM/CFD/mechanical/manufacturability simulation. Founded by Stanford computational-geometry PhD (Kabaria). First commercial focus on thermal engineering ($24B addressable).
- **round:** Seed
- **deal_type:** venture
- **amount_m:** 10.0
- **valuation_m:** null
- **date:** 2025-12-02
- **date_display:** 02-Dec-25
- **month_year:** Dec-25
- **quarter:** 4Q25
- **year:** 2025
- **location:** Palo Alto, USA
- **lead_investors:** Eclipse Ventures
- **co_investors:** Undisclosed
- **related_tickers:** [SNPS, CDNS, ANSS]
- **robotnik_take:** $10M-est seed (split from $46M total raise: $36M Series A in dataset, residual ~$10M Seed). Eclipse-led seed for physics-foundation-model EDA — comp set: Ansys (ANSS, public CAE incumbent), SNPS/CDNS (acquiring physics-AI capability), Cognichip / Astrus / Ricursive (chip-design-side). Vinci's differentiation is simulation-side (thermal, EM, CFD) rather than layout-side; closer to Ansys disruption than EDA-tool replacement. Both rounds announced same day signals Series A oversubscription, not seed underfunding.
- **source:** https://www.getvinci.ai/news/vinci-emerges-from-stealth-to-transform-semiconductor-design-and-simulation/
- **source_status:** pending
- **policy_exposure:** US_CHIPS_Act
- **value_chain_tier:** ""
- **bottleneck_risk:** Pre-commercial
- **DEDUP STATUS:** DEDUP-CHECK (Vinci Series A 2025-12-02 $36M already in dataset; Seed amount inferred from $46M total — $36M Series A = ~$10M. Withhold from rounds.json until canonical Seed amount confirmed via Eclipse Capital or company secondary source.)
- **notes:** Amount inferred; not directly disclosed. Both Seed and Series A closed same calendar day per BusinessWire / company release. Flag for canonical split confirmation. If split cannot be confirmed, recommend rolling into existing Series A row as "Seed + Series A combined" rather than dual rows.

---

## Held / Excluded (not added)

- **Substrate** — $100M Seed 2025-10-28: ALREADY in dataset (recorded as "Series A" 2025-10-28 $100M). Press uses both labels; canonical company release calls it Seed. Recommend dataset-side relabel separately, not new row.
- **Vertical Semiconductor** — $11M Seed 2025-10-15: ALREADY in dataset. Skip.
- **Cognichip** — $33M Seed 2025-05-15: ALREADY in dataset. Skip.
- **Niobium** — $23M Seed 2025-12-03: ALREADY in dataset. Skip (different company than Quantcore; both niobium-themed).
- **NcodiN** — €16M Seed 2025-11-19: ALREADY in dataset. Skip.
- **Q-Factor** — $24M Seed 2026-04-06: ALREADY in dataset. Skip.
- **Groove Quantum** — €10M Seed 2026-04-30: ALREADY in dataset. Skip.
- **OrangeQS** — €15M Seed ext 2026-04-21: ALREADY in dataset. Skip.
- **Pixel Photonics** — €5M Seed 2026-04: ALREADY in dataset. Skip.
- **Enlightra** — $15M Seed 2025-12-18: ALREADY in dataset. Skip.
- **Mastiska** — $10M Seed 2025-11-28: ALREADY in dataset. Skip.
- **AheadComputing** — $21.5M Seed 2025-02-19: ALREADY in dataset. Skip.
- **Arago** — $26M Seed 2025-07-08: ALREADY in dataset. Skip.
- **Nuvacore** — Sequoia-led Seed 2026-04-15: ALREADY in dataset. Skip.
- **Hummink** — €15M 2025-11-17: ALREADY in dataset (recorded as Series A $16M). Source ambiguity; dataset version (Series A) likely correct given €15M = Hummink's third raise. Skip.
- **Opticore** — Initial Seed Dec 2024 ($5M) out of window; Sep 2025 $7.5M extension brings total to $14.5M. Already in 2024 dataset coverage; the 2025 extension is a Seed extension, but minimum threshold and net-new criteria don't strongly merit additional row. Hold.
- **Ubitium** — $3.7M Seed Nov 2024: out of window (pre 2025-01-01). Skip.
- **Akhetonics** — €6M Seed Nov 2024: out of window. Skip.
- **Lightium** — $7M Seed Sep 2024: out of window. Skip.
- **Quantum Source Seed extension** — Dell-led $12M ext, 2024: out of window. Skip.
- **Atum Works** — YC X25 ($500K seed): below $1M Seed minimum threshold. Hold.
- **Wave Photonics** — £4.5M Seed Jun 2024: out of window. Skip.
- **Quintessent** — $11.5M Seed Mar 2024: out of window. Skip.
- **Volantis date disambiguation** — Optica reports Jul 7 2025, BusinessWire / company Jun 11 2025 — using Jun 11 as canonical (company-press date).
- **Vinci Seed amount uncertainty** — see Row 27.
- **BigEndian Semiconductors** $6M Pre-Series A 2026-05: out of round scope (not Pre-Seed or Seed).
- **iVP Semi** $5M Pre-Series A Jul 2024: out of window + out of round scope.

---

## Summary

### Totals
- **NEW:** 25 (Rows 1-26 minus DEDUP-CHECK Row 7 (Ricursive Seed, NEW pending DEDUP confirmation), Row 27 (Vinci Seed, DEDUP-CHECK))
- **DEDUP-CHECK:** 2 (Ricursive Intelligence Seed — distinct round from existing Series A; Vinci Seed — same date as existing Series A)
- **Total candidates surfaced:** 27

### Subsector distribution (top 3)
1. **Frontier Compute:** 10 (Snowcap, Unconventional AI, Vertical Compute, QuamCore, PHOTON IP, Volantis, Lucidean, PINC, plus Q-Factor & Groove Quantum from existing dataset)
2. **EDA & IP:** 7 (Chipmind, Oxmiq, Maieutic, Ricursive, Astrus, Vinci, plus Cognichip from existing dataset)
3. **Fabless Design:** 5 (Upscale AI, PseudolithIC, Oso, Sensesemi, Mueon, Uviquity)
4. **Equipment:** 3 (Cnuic, Chiral, EuQlid)
5. **Power & Analog:** 2 (Skycore, Claros)
6. **Silicon & Substrates:** 2 (Isentroniq, Quantcore)
7. **Foundry:** 0
8. **OSAT / Packaging & Test:** 0

### Geographic distribution (top 3)
1. **USA:** 12 (Snowcap, Oxmiq, Upscale, Unconventional, Ricursive, Volantis, PseudolithIC, Oso, Mueon, Lucidean, Claros, PINC, EuQlid, Uviquity, Vinci) — includes 14 if Uviquity + Vinci counted
2. **Europe:** 10 (Chipmind CH, Vertical Compute BE, Isentroniq FR, Quantcore UK, PHOTON IP NL, Cnuic UK, Skycore DK, Chiral CH)
3. **Israel:** 2 (QuamCore, plus Q-Factor in existing)
4. **India / Canada:** 2 (Maieutic + Sensesemi India; Astrus Canada)
5. **Other (Asia):** 0 net-new (most Asian seed activity concentrated in China — language barrier suppressed)

### Source-status breakdown
- **verified:** 24
- **pending:** 3 (Maieutic — sourcing canonical company press; Claros — DCD 403'd, BusinessWire confirmed; Vinci — amount inference)

### Patterns worth flagging
1. **"Seed" inflation:** 3 candidates at $100M+ "Seed" (Substrate, Upscale AI, Unconventional AI) — round labeling has decoupled from stage; these are de facto Series A with seed-equity structure. Dataset should flag rather than relabel.
2. **EDA-AI surge:** 6 net-new EDA-AI seeds (Chipmind, Oxmiq, Maieutic, Ricursive, Astrus, Vinci) in 13 months — clear secular shift. SNPS/CDNS competitive response (ChipStack, Questa One) is happening in parallel; sweep captures the startup side comprehensively.
3. **Quantum semiconductor stack:** QuamCore (on-chip control), Isentroniq (cryo wiring), Quantcore (niobium components), EuQlid (NV-imaging metrology), PINC (nonlinear photonics) form a coherent quantum-hardware supply chain in the seed cohort — strategic mapping opportunity for thesis page.
4. **China underrepresented:** Single confirmed Chinese semi seed in window (Huanjingxin Technology, ~$6.87M pre-seed, semiconductor reuse) — likely under-sampling due to language constraints. Synapx was flagged but its $50M Seed close date is January 2026 ambiguously sourced; recommend manual triage.
5. **Israeli quantum cluster:** QuamCore + Q-Factor (existing) both $9M+ Seed for million-qubit superconducting / neutral-atom architectures within 12 months — concentration suggests Israel-specific cryo + atomic-physics talent pool; worth thesis-page note.
6. **No Foundry / OSAT seed activity in window:** Zero pure-play Foundry-subsector seeds, zero OSAT seeds at this stage — capital-intensity threshold rules out these subsectors at Seed scale; dataset gap is structural, not search-failure.

### Anti-fabrication holdbacks
- **Vinci Seed amount** inferred ($46M total − $36M Series A = ~$10M); flagged source_status pending (Row 27 DEDUP-CHECK).
- **Maieutic Semiconductor** source URL canonical (yourstory.com) returned 403 on WebFetch; substituted entrepreneur.com cross-reference URL with source_status pending pending swap.
- **Claros** DCD URL returned 403 on WebFetch; BusinessWire + Axios cross-verified content; source_status pending pending canonical replacement.
- **Volantis date** Optica reports differ from BusinessWire by 27 days — using earlier (BusinessWire) date per Rule 5 (canonical announcement = company press).
- **Substrate, Hummink** dataset already records canonical entries — held to avoid duplicate entries; flag for dataset-side review (Substrate round label; Hummink round name).
- **Subsector for cross-stack** (e.g., Unconventional AI neuromorphic): placed in Frontier Compute per CLAUDE.md note that cross-stack AI-for-robotics → Software & Simulation only applies to robotics-platform companies; Unconventional AI's neuromorphic chip is hardware.
