# robotnik_take Cumulative-Funding Audit (v1.1.1)

- **Audit date**: 2026-05-12
- **Scope**: All 1,132 rows in `data/funding/rounds.json` (non-null `robotnik_take`)
- **Total cumulative-funding mentions found**: 127
- **Trigger**: Drop of `total_raised_m` / `total_number_of_raises` from CSV export — those fields are computed only from 2023+ coverage and understate companies with pre-2023 history. Takes that recite those figures inherit the under-count error.

Classification rubric (per user direction):
- **KEEP** — cumulative figure is load-bearing for the analytical point (sizing vs peers, valuation step, capital intensity, runway math, round structure).
- **STRIP** — figure reads as balance-sheet recitation, can be deleted with no loss to the analytical core.
- **REWRITE** — figure should stay but framing needs strategic anchor per v1.1 spec (comp set, valuation/round mechanics, view). Target 450–550 chars, 580 hard cap.

**Important distinction**: Round-extension takes that cite a round-level cumulative ("Series C extension brings total Series C to $282M") are reporting *round structure*, not company-wide total raised, and are unaffected by the 2023+ coverage bias. Those are tagged KEEP. The bias problem is concentrated in company-wide claims ("total raised $X", "total funding $X").

---

## STOKE SPACE — SPECIAL CASE

### Row dump

| idx | date | round | amount_m | valuation_m | deal_type | source |
|-----|------|-------|----------|-------------|-----------|--------|
| 732 | 2023-10-05 | Series B | $100.0M | null | venture | spacenews — `stoke-space-raises-260-million` |
| 4   | 2025-01-15 | Series C | $260.0M | null | venture | spacenews — `stoke-space-raises-260-million` |
| 218 | 2026-02-10 | Series D (extension) | $350.0M | null | venture | spacenews — `stoke-space-adds-350-million-to-series-d-round` |
| (Series D parent) 2025-10-08 | Series D | $510.0M | null | venture | spacenews — `stoke-space-raises-510-million` |

(Sum of `amount_m` across the four rows = **$1,220M**, matching the internal `total_raised_m` field of $1,220M exactly. The user-quoted internal value of $1,220M is consistent with what is actually in the dataset; the user's prompt mentions a "$1,220M" number which IS the current `total_raised_m`.)

### Double-count analysis

There is **no double-count** in `rounds.json` for Stoke Space:

- The Oct-25 Series D ($510M, idx not in cumulative-funding match set) and the Feb-26 Series D extension ($350M, idx 218) are **distinct cash events with distinct primary sources**. The extension brings the Series D round to $860M, not $510M. The two rows correctly represent (i) initial close and (ii) extension. They are not duplicating the same dollars.
- The Series C ($260M, idx 4) and Series B ($100M, idx 732) are clearly separate rounds 15 months apart with distinct primary sources.
- All four `amount_m` values reconcile to the published narrative: Series B ($100M, Oct-23) + Series C ($260M, Jan-25) + Series D ($510M, Oct-25) + Series D extension ($350M, Feb-26) = **$1,220M cumulative**, which is the second-largest fully-reusable launch raise globally after SpaceX (consistent with the idx 218 take's "$1.34B" claim — though that includes ~$120M pre-2023 seed/Series A capital not represented in `rounds.json`).

### What is actually wrong: the idx 4 take

The Jan-25 Series C take at idx 4 says **"Total funding $480M"**. That figure is stale by two rounds and ~$740M:
- At time of Series C close (Jan-25), Stoke had: pre-2023 (~$120M Series A + seed) + $100M Series B + $260M Series C ≈ **$480M cumulative** (so the figure was correct as-of Jan-25).
- But the take now sits in a dataset alongside the Oct-25 and Feb-26 rows, making the "$480M" line read like a current cumulative figure when it is in fact a snapshot at round close.

### Recommendation

1. **Do not drop any Stoke row.** All four rows are real, distinct cash events with distinct sources. `total_raised_m=$1,220M` is internally consistent with `rounds.json` amounts.
2. **The user's headline finding** ("total_raised_m=$1,220M but take cites $480M") is explained by **temporal staleness in the idx 4 take**, not by double-counting.
3. **Action on idx 4 take**: REWRITE to either (a) drop the dated cumulative figure entirely, or (b) frame it explicitly as "cumulative at round close $480M; subsequently expanded via Oct-25 Series D and Feb-26 extension." Recommend option (a) — the round-close snapshot has no analytical value once superseded.
4. **Cross-check** the take_cumulative_funding_audit table below for idx 732 (Series B Oct-23, says "$175M to date") — same staleness pattern; figure was correct at time, hides $1B+ of subsequent capital.

---

## Audit table

Legend: K = KEEP, S = STRIP, R = REWRITE. "Figure cited" is the cumulative number in the take. Where the figure is round-level (e.g., "Series C total to $XM") that is noted in the classification.

| idx | entity_id | company | date | round | figure cited | take (excerpt) | class | proposed rewrite (R only) |
|-----|-----------|---------|------|-------|--------------|----------------|-------|---------------------------|
| 4 | stoke-space | Stoke Space | 2025-01-15 | Series C | $480M total funding | "Total funding $480M; fully reusable Nova rocket. Note: also has Oct-25 Series D and Feb-26 extension entries." | **R** | $260M Series C funds Nova rocket development and Cape Canaveral pad LC-14, the first US fully-reusable two-stage program after SpaceX. Comp set: Rocket Lab (RKLB) on partial reusability, Relativity and Blue Origin privately. The Breakthrough Energy + Glade Brook lead is a climate-aligned strategic syndicate signalling launch-decarbonization thesis. First Nova flight test is the binary milestone; subsequent Oct-25 Series D + Feb-26 extension validate investor conviction. |
| 15 | encharge-ai | EnCharge AI | 2025-02-13 | Series B | $144M+ total raised | "Analog in-memory computing AI chips; spun out of Princeton 2022; fabricating with TSMC; total raised $144M+" | **S** | — |
| 20 | lambda | Lambda | 2025-02-19 | Series D | $863M total raised | "Rents NVIDIA GPU servers for AI training/inference; 25,000+ GPUs; adding Blackwell B200s; total raised $863M" | **R** | $480M Series D at multi-billion valuation funds Blackwell B200 buildout; 25,000+ GPU fleet positions Lambda as the merchant alternative to CoreWeave (CRWV) and hyperscaler AI clouds. Comp set: CoreWeave on listed GPU cloud, Crusoe and Together AI on private peers, Oracle (ORCL) on hyperscaler GPU rental. Capital intensity is the binary question — Lambda's lifetime raise sits a tier below CoreWeave's debt-heavy capital stack. |
| 26 | viam | Viam | 2025-03-03 | Series C | $117M total raised | "Cloud-based platform for building, monitoring, managing smart machines and robots; MongoDB co-founder; total raised $117M" | **S** | — |
| 27 | epirus | Epirus | 2025-03-05 | Series D | >$550M total raised | "High-power microwave Leonidas counter-drone/counter-electronics system; total raised >$550M" | **R** | $250M Series D at $1.35B post-money positions Epirus as the best-capitalized pure-play HPM counter-drone vendor. Comp set: Anduril (private) on broader defense-tech, RTX (RTX) and Lockheed (LMT) on incumbent directed-energy, no public pure-play. Pentagon Leonidas IDIQ award is the binary catalyst. The 2x step-up from Series C signals continued defense-tech momentum through the autonomy procurement cycle. |
| 30 | celestial-ai | Celestial AI | 2025-03-11 | Series C | >$515M total raised | "Photonic Fabric optical interconnect for AI data centers; total raised >$515M" | **R** | $250M Series C funds Photonic Fabric optical interconnect for AI memory-disaggregation; positions Celestial alongside Lightmatter and Ayar Labs as the merchant alternatives to in-house hyperscaler photonics. Comp set: Lightmatter ($4.4B), Ayar Labs (Intel-aligned), Marvell (MRVL) and Broadcom (AVGO) on CPO. AMD strategic LP is the load-bearing signal — accelerator incumbent hedging into optical I/O before HBM/copper power walls bind. |
| 35 | cmr-surgical | CMR Surgical | 2025-04-02 | Undisclosed | $1.4B total raised | "Versius soft-tissue surgical robot; $1.4B total raised; US market entry focus" | **R** | $200M tranche funds US FDA submission and commercial buildout for Versius soft-tissue platform. Comp set: ISRG (Intuitive) dominant incumbent, Medtronic Hugo and Stryker Mako on adjacent platforms, Asensus (ASXC) on listed peers. CMR is the best-capitalized private soft-tissue RAS challenger globally; US 510(k) clearance is the binary catalyst that unlocks the world's largest surgical robotics market and the path to a strategic exit or IPO. |
| 46 | true-anomaly | True Anomaly | 2025-04-30 | Series C | $400M+ total raised | "Jackal spacecraft for RPO/space domain awareness; $400M+ total raised; 4 missions in 18 months" | **R** | $260M Series C at $1.4B post-money cements True Anomaly as the best-funded private space-domain-awareness pure-play. Comp set: Anduril (private) on broader defense-AI, Rocket Lab (RKLB) Space Systems on on-orbit hardware, Slingshot and LeoLabs on SDA software peers. Four Jackal missions in 18 months is the operational tempo signal. SDA Tranche 2 / Golden Dome contractor selection is the binary near-term catalyst. |
| 60 | impulse-space | Impulse Space | 2025-06-03 | Series C | $525M total funding | "Space tugs (Mira + Helios vehicles); total funding $525M; founded by ex-SpaceX Tom Mueller" | **R** | $300M Series C at $4.1B valuation makes Impulse the highest-priced private OTV/space-tug pure-play. Comp set: Astranis on small GEO, Astroscale (TYO:186A) on listed orbital services, D-Orbit and PAVE on European peers, no real US public pure-play. Mueller's SpaceX propulsion lineage is the technical moat; Helios Mars-class kickstage is the binary differentiator vs incumbent in-space transportation. |
| 73 | forsight-robotics | ForSight Robotics | 2025-06-24 | Series B | $195M total funding | "Ophthalmic robotic surgery (ORYOM platform); total funding $195M; FDA trials underway" | **R** | $125M Series B funds ORYOM ophthalmic-surgical-robot FDA pivotal trial and US commercial buildout. Comp set: Intuitive (ISRG) on broader RAS, J&J Ottava and Medtronic Hugo on soft-tissue, Asensus (ASXC) and CMR Surgical on smaller-footprint peers — no public pure-play in ophthalmic robotics. First-mover positioning in cataract automation; FDA de novo path is the binary catalyst. |
| 77 | civ-robotics | Civ Robotics | 2025-07-01 | Series A | $12.5M total raised | "CivDot autonomous layout robot; 8mm survey accuracy; total raised $12.5M" | **S** | — |
| 81 | galaxea-ai | Galaxea AI | 2025-07-09 | Series A | ~$210M cumulative | "Founded 2023 by Tsinghua + Stanford professors; R1 Pro/Lite humanoids; cumulative ~$210M raised. Note: Galaxea also has a Feb-26 Series B entry." | **K** | — (cumulative figure is load-bearing for "third raise in 18 months" capital-tempo framing; Note: figure should be reconciled with Series B before v1.1.1 ship) |
| 85 | varda-space-industries | Varda Space Industries | 2025-07-10 | Series C | $329M total raised | "Microgravity drug crystallization + hypersonic reentry testbed; 3 missions completed; $329M total raised" | **R** | $187M Series C funds W-Series in-space pharma manufacturing platform plus hypersonic reentry testbed contract pipeline. Comp set: Sierra Space and Axiom on LEO infrastructure peers, no real public pure-play; closest listed adjacency is Redwire (RDW) on space manufacturing. Three completed missions is the operational-tempo signal; FDA-pathway crystallization data from W-1/W-2/W-3 is the binary commercial catalyst. |
| 88 | xtend | XTEND | 2025-07-15 | Series B (ext) | $100M total raised | "AI tactical drone platform; deployed by US DoD, IDF, Singapore; $100M total raised" | **R** | $30M Series B extension funds US DoD scale-up; XTEND's tactical-drone AI is in active operational use across IDF, US, Singapore. Comp set: Anduril Lattice on the prime side, Skydio X10D on US tactical-quad, Shield AI V-BAT and Saronic on adjacent autonomy. Sole-source deployment posture inside three militaries is the moat; Replicator program selection is the binary US procurement catalyst. |
| 92 | hadrian | Hadrian | 2025-07-17 | Series C | ~$500M total raised | "AI-powered CNC + automated factories for defense/space; 10x YoY growth; opening Mesa AZ Factory 3; ~$500M total raised" | **R** | $260M Series C funds Mesa AZ Factory 3 — third lights-out CNC plant for defense/space precision parts. Comp set: 6K Additive and Velo3D (legacy listed) on additive, no real public AI-CNC pure-play; closest is Protolabs (PRLX) on traditional CNC service. 10x YoY growth + defense-prime offtake is the unit-economics validation; vertical integration into customer DoD/space supply chains is the moat. |
| 102 | simaai | SiMa.ai | 2025-08-01 | Series C | $355M total funding | "Modalix multimodal MLSoC for robotics, automotive, defense; total funding $355M; oversubscribed" | **R** | $85M oversubscribed Series C funds Modalix multimodal MLSoC commercial buildout in robotics, automotive ADAS, defense edge inference. Comp set: Hailo on edge AI accelerator peers, Ambarella (AMBA) on listed automotive vision, Mobileye (MBLY) on auto incumbents, NVIDIA Jetson on hyperscaler edge. Differentiated by multimodal-on-chip vs single-modality competitors; auto Tier-1 design-wins are the binary commercial catalyst. |
| 109 | blue-water-autonomy | Blue Water Autonomy | 2025-08-26 | Series A | $64M total raised | "Full-sized autonomous unmanned ships for US Navy; total raised $64M; Pentagon's $2.1B MUSV program" | **R** | $50M Series A funds full-sized autonomous unmanned-surface-vessel development for US Navy MUSV program ($2.1B Pentagon obligation). Comp set: Saronic (private) on smaller-tonnage USV, L3Harris (LHX) on incumbent USV prime, Anduril Dive-LD on subsurface. Pentagon hedge against PLAN amphibious posture in the Indo-Pacific is the strategic frame; first Navy contract award is the binary commercial catalyst. |
| 110 | aerospacelab | Aerospacelab | 2025-08-26 | Series B (ext) | €134M total raised | "Megafactory for 500 sats/year; competing for IRIS2 contract; total raised EUR 134M" | **R** | €110M Series B extension funds Belgian megafactory targeting 500 sats/year capacity — the European sovereign-satellite-bus play. Comp set: York Space and Apex Space on US productized buses, Astranis (private) on small-GEO, Airbus and Thales on incumbent EU primes. IRIS2 constellation award is the binary near-term contract; if won, Aerospacelab becomes the EU answer to SpaceX Starshield manufacturing tempo. |
| 114 | proteantecs | proteanTecs | 2025-09-09 | Series D | >$250M total raised | "Embedded agent telemetry for predictive chip lifecycle monitoring; total raised >$250M" | **R** | $51M Series D funds embedded-agent silicon-lifecycle telemetry platform — picks-and-shovels for AI/auto chip reliability. Comp set: PDF Solutions (PDFS) on listed silicon-yield-management, Synopsys (SNPS) Silicon.da and Cadence (CDNS) on adjacent EDA, no real pure-play. Hyperscaler + auto Tier-1 customer roster validates SLM thesis; AMD/Intel/Nvidia GPU reliability concerns are the binary demand catalyst. |
| 123 | morse-micro | Morse Micro | 2025-09-22 | Series C | >$193M total funding | "Fabless Wi-Fi HaLow IoT silicon; total funding >$193M; expanding internationally" | **S** | — |
| 205 | neurophos | Neurophos | 2026-01-22 | Series A | $118M total | (full take — strategic comp-set frame; "$118M total" used to position capital intensity) | **K** | — (cumulative figure is load-bearing: "Capital base is light for photonic-foundry economics") |
| 218 | stoke-space | Stoke Space | 2026-02-10 | Series D (ext) | $1.34B cumulative | (full take — "second-best-funded fully-reusable launch program globally after SpaceX") | **K** | — (figure is the analytical core — sizing vs SpaceX/Blue Origin/RKLB) |
| 270 | pave-space | PAVE Space | 2026-03-25 | Seed | best-capitalized | (full take — "best-capitalized to fill that gap" in EU OTV) | **K** | — (best-capitalized is the strategic framing; no dollar cumulative restated) |
| 292 | starfish-space | Starfish Space | 2024-11-13 | Series B | >$50M total raised | "Defense-led round to scale Otter satellite-servicing vehicles; brought total raised >$50M and dovetails with Starfish's Space Force Otter program contract awarded earlier in 2024." | **K** | — (cumulative is round-context for Space Force Otter contract; load-bearing for scale signal) |
| 304 | NVX | NOVONIX | 2024-12-16 | Government investment | $943.6M total project cost | (full take — DOE ATVM loan against project cost) | **K** | — (project-cost cumulative is load-bearing for loan structure) |
| 310 | xscape-photonics | Xscape Photonics | 2024-10-15 | Series A | $57M total | "Multi-color programmable photonics for AI data-center fabrics; brings total to $57M. Cisco + NVIDIA participation makes it a dual-strategic round — both networking and accelerator incumbents hedging into co-packaged optics." | **K** | — (cumulative is round-context for dual-strategic frame) |
| 334 | path-robotics | Path Robotics | 2024-10-14 | Series D | $270M total raised | "AI-enabled welding cells targeting US labor shortage in fabrication. Total raised: $270M. Industrial robotics deal that combines verticalized hardware with manufacturing reshoring tailwinds." | **K** | — (cumulative anchors scale vs reshoring thesis) |
| 339 | carbon-robotics | Carbon Robotics | 2024-10-21 | Series D | $157M total raised | "Laser-weeding ag robot scaling internationally; total raised $157M. NVIDIA's NVentures participation signals continued GPU/edge-AI investment thesis around outdoor robotics." | **K** | — (cumulative is load-bearing for scale signal) |
| 341 | anybotics | ANYbotics | 2024-12-12 | Other | >$130M total raised | "Quadruped industrial inspection robots. Round funds US expansion and on-board GPU integration. Total raised >$130M. Qualcomm's lead suggests edge-compute integration thesis." | **K** | — |
| 346 | agtonomy | Agtonomy | 2024-10-16 | Series A (ext) | $32.8M total | "Closes Series A at $32.8M total. Software/services layer that retrofits brand-name tractors into autonomy — capital-light ag-autonomy thesis vs vertically-integrated competitors." | **K** | — (round-level total, load-bearing for "capital-light" thesis) |
| 352 | rideflux | RideFlux | 2024-10-31 | Series B | KRW 55.2B total raised | "Korean L4 autonomous freight startup; total raised KRW 55.2B. Series B comes after Korea's first L4 freight permits." | **S** | — |
| 354 | teleo | Teleo | 2024-11-20 | Series A (ext) | $29.8M total raised | (full take — two-tranche extension structure) | **K** | — (round-extension structure context) |
| 357 | voliro | Voliro | 2024-10-03 | Series A | $22M total raised | (full take) | **S** | — |
| 358 | brightpick | Brightpick | 2024-11-12 | Other | $47M total raised | (full take) | **S** | — |
| 362 | four-growers | Four Growers | 2024-11-20 | Series A | $15M total raised | (full take) | **S** | — |
| 374 | astranis | Astranis | 2024-07-24 | Series D | >$750M total raised | "Largest US space round of 2024. Equity round fully funded development of next-gen Omega broadband satellite platform; total raised passed $750M with Trinity Capital also providing venture debt alongside the equity." | **K** | — (cumulative anchors "largest US space round 2024" claim) |
| 378 | astroforge | AstroForge | 2024-08-20 | Series A | $55M total raised | (full take — speculative deep-space mining) | **S** | — |
| 391 | mangrove-lithium | Mangrove Lithium | 2024-08-26 | Strategic | $25M total raised | "Strategic add-on round; tranche size undisclosed but brought total raised to $25M USD. Electrochemical lithium refining converts diverse feedstocks to battery-grade hydroxide/carbonate. The bigger $35M Series B financing closed January 2025." | **K** | — (cumulative is round-context for undisclosed strategic + later Series B) |
| 402 | dreambig-semiconductor | DreamBig Semiconductor | 2024-07-16 | Series B | ~$93M total funding | (full take) | **S** | — |
| 409 | eliyan | Eliyan | 2024-08-13 | Strategic | $100M cumulative | "Strategic investment from VentureTech Alliance pushed Eliyan past $100M cumulative funding for chiplet die-to-die interconnect IP. Amount undisclosed but extends the $60M March 2024 Series B." | **K** | — ($100M crossover milestone load-bearing) |
| 453 | cesiumastro | CesiumAstro | 2024-06-18 | Series B (ext) | $125M total Series B | "Active phased-array communications payloads (Vireo Ka-band, Skylark satcom terminal). Series B+ brings total Series B to $125M; L3Harris strategic continues defense satcoms consolidation thesis." | **K** | — (round-level total — extension structure) |
| 491 | gausium | Gausium | 2024-05-14 | Series D | $50M cumulative Series D | "Indoor cleaning robots; cumulative Series D total reached $50M after this strategic top-up. Gausium claims first-time corporate profitability — significant validation for service-robot economics." | **K** | — (round-level total — top-up structure) |
| 528 | hailo | Hailo | 2024-04-02 | Series C (ext) | $340M total raised | "Edge AI accelerator chips; debuted Hailo-10 GenAI accelerator alongside the round. Brings total raised to $340M. Insider-only round signals limited new institutional appetite at the prior valuation." | **K** | — (cumulative load-bearing for "insider-only signals limited institutional appetite") |
| 529 | simaai | SiMa.ai | 2024-04-04 | Series B (ext) | $270M total raised | "Embedded edge AI MLSoC platform; total raised $270M. Funds support 2nd-gen MLSoC for multimodal GenAI. Note: also has Q4 2024 entry." | **S** | — |
| 537 | expedera | Expedera | 2024-05-21 | Series B | $47M+ total funding | (full take) | **S** | — |
| 540 | frore-systems | Frore Systems | 2024-05-29 | Series C | $196M total raised | (full take) | **S** | — |
| 547 | etched | Etched | 2024-06-25 | Series A | $125.36M total raised | "Transformer-only inference ASIC ('Sohu') on TSMC 4nm; total raised $125.36M. Aggressive specialization bet — inference economics depend on transformer dominance persisting." | **S** | — |
| 548 | axelera-ai | Axelera AI | 2024-06-27 | Series B | $120M total raised | (full take) | **S** | — |
| 560 | boston-metal | Boston Metal | 2024-01-30 | Series C (ext) | $282M total Series C | "Series C2 extension brings total Series C to $282M. Tokyo-based MIP led; expands Asia presence for Molten Oxide Electrolysis (MOE) green steel." | **K** | — (round-level total) |
| 562 | lilac-solutions | Lilac Solutions | 2024-02-12 | Series C | $315M total raised | "Direct lithium extraction (DLE) using ion-exchange. Total raised to $315M. Mercuria + BMW + Mitsubishi syndicate signals industrial offtake intent." | **K** | — (cumulative scale anchors offtake-intent thesis) |
| 566 | pure-lithium | Pure Lithium | 2024-03-14 | Series A | up to $30M total | "Brine-to-Battery lithium-metal anode tech. Round may extend up to $30M total. Oxy strategic lead positions Pure Lithium adjacent to Occidental's Permian Basin DLE operations." | **K** | — (round-extension ceiling) |
| 605 | robco | RobCo | 2024-02-29 | Series B | $60M total funding | "Plug-and-play modular cobot kits aimed at SMEs; brought total funding to $60M and gave Lightspeed a flagship European industrial-AI bet. Note: also has Jan-26 Series C entry." | **K** | — (cumulative load-bearing for "flagship European bet" signal) |
| 606 | viam | Viam | 2024-03-26 | Series B | $87M total funding | (full take) | **S** | — |
| 609 | eacon-mining | EACON Mining | 2024-03-14 | Series C | $97.3M cumulative 6-mo | "Series C++ tranche pushed cumulative six-month financing to $97.3M; deploys autonomous-electric haul trucks across Chinese mines and is targeting Australian commercial expansion." | **K** | — (six-month financing pace is the analytical point) |
| 617 | gather-ai | Gather AI | 2024-03-05 | Series A (ext) | $34M total | "Series A-1 extension brings total to $34M. CMU spin-out delivers indoor-drone inventory monitoring..." | **K** | — (round-extension) |
| 632 | zhuoyi-intelligent-technology | Zhuoyi Intelligent Technology | 2024-01-22 | Series B | $42.5M total funding | (full take) | **S** | — |
| 635 | guozi-robot | GUOZI Robot | 2024-01-16 | Other | ~$28M total funding | (full take) | **S** | — |
| 645 | robovision | Robovision | 2024-03-26 | Series A | $65M total equity | "Computer-vision platform for industrial automation; brings total equity raised to $65M. Targeting US expansion to address labor shortages. Underexposed European AI/vision player." | **S** | — |
| 653 | may-mobility | May Mobility | 2023-11-07 | Series D | ~$300M total funding | (full take — Cruise/Pony.ai comp) | **K** | — (cumulative load-bearing for capital-efficiency comp vs Cruise/Pony.ai) |
| 654 | gecko-robotics | Gecko Robotics | 2023-12-05 | Series C (ext) | $173M total Series C | (full take — defense-tech VC syndicate) | **K** | — (round-level total) |
| 657 | quantum-systems | Quantum Systems | 2023-10-24 | Series B | €100M total raised | "First European dual-use drone company past €100M total raised. Vector reconnaissance UAS in active service in Ukraine + German Bundeswehr offtake..." | **K** | — (€100M crossover milestone load-bearing for "first European" claim) |
| 661 | machina-labs | Machina Labs | 2023-10-05 | Series B | $45M total raised | (full take — NVIDIA NVentures co-lead) | **S** | — |
| 694 | bonsai-robotics | Bonsai Robotics | 2023-10-02 | Seed | $13.5M total raised | (full take) | **S** | — |
| 732 | stoke-space | Stoke Space | 2023-10-05 | Series B | $175M total to date | "Reusable rocket developer; $100M Series B funds Nova rocket development and Cape Canaveral pad LC-14 infrastructure. Total to date $175M. Pursuing fully reusable architecture vs. RKLB Neutron's partial reusability." | **R** | $100M Series B funds Nova rocket development and Cape Canaveral pad LC-14 — first US fully-reusable two-stage program after SpaceX, vs RKLB Neutron's partial reusability. Comp set: Rocket Lab (RKLB) on listed competitor, Blue Origin (private) on heavier-lift reusable, Relativity on additive-manufactured peer. First Nova hot-fire and FAA launch licensing are the binary near-term execution milestones; Stoke later raised $260M Series C, $510M Series D, and $350M extension. |
| 734 | k2-space | K2 Space | 2023-10-17 | Seed (ext) | $16M total | "Large satellite bus startup (Mega 1-ton, Giga 15-ton). Brings total to $16M. Bet on launch-cost decline making bigger sats economical with heavy/super-heavy lift (Falcon Heavy, Starship). Founders are SpaceX veterans." | **K** | — (cumulative is round-context for seed-stage capital fit) |
| 735 | astroscale | Astroscale | 2023-10-26 | Series G (ext) | $83.6M Series G / $383M total | (full take — IPO context) | **K** | — (cumulative anchors pre-IPO scale) |
| 737 | ursa-major | Ursa Major | 2023-11-30 | Series D (ext) | $138M total Series D+D-1 | (full take — round-level total) | **K** | — (round-level total) |
| 739 | agnikul-cosmos | AgniKul Cosmos | 2023-10-16 | Series B | ~$40M total raised | (full take) | **S** | — |
| 740 | skyroot-aerospace | Skyroot Aerospace | 2023-10-31 | Pre-Series C | $95M total | "Indian private launch leader. Pre-Series C brings total to $95M, highest in Indian spacetech. Vikram-1 small launcher targeting orbital flight after Vikram-S sub-orbital success in Nov 2022. Temasek's first Indian space investment signals geopolitical alignment." | **K** | — ("highest in Indian spacetech" is the comparative claim — load-bearing) |
| 741 | hawkeye-360 | HawkEye 360 | 2023-10-18 | Series D (ext) | $68M Series D / $378M total | (full take — pre-S-1 context) | **K** | — (cumulative anchors pre-IPO scale) |
| 744 | space-pioneer-tianbing-aerospace | Space Pioneer (Tianbing Aerospace) | 2023-11-03 | Series C (ext) | 3B+ yuan cumulative | (full take — 12th round / cumulative) | **K** | — (cumulative + round-count is the funding-tempo signal) |
| 768 | shield-ai | Shield AI | 2023-09-14 | Series F | ~$500M total Series F | "Initial Series F close at $2.5B post-money for V-BAT autonomous aircraft maker. Round later expanded to ~$500M total by Dec 2023 at $2.8B valuation — defense-tech autonomy thesis durable through ZIRP unwind (cf. Anduril, Saronic)." | **K** | — (round-level total, valuation step is the analytical point) |
| 771 | fernride | FERNRIDE | 2023-09-20 | Series A (ext) | $50M total Series A | (full take — round-extension structure) | **K** | — (round-level total) |
| 775 | forwardx-robotics | ForwardX Robotics | 2023-07-12 | Series C (ext) | $61M Series C / $140M total since 2016 | "C-II extension brings ForwardX Series C total to $61M; total raised $140M since 2016. State-fund-led (Hefei) at the cap-table..." | **K** | — (round-level + 8-yr cumulative both load-bearing for state-fund tempo signal) |
| 776 | collaborative-robotics | Collaborative Robotics | 2023-07-26 | Series A | >$40M total raised | (full take — Sequoia + Mayo Clinic) | **S** | — |
| 778 | helm-ai | Helm.ai | 2023-08-16 | Series C | $102M total raised | (full take — Honda/Goodyear strategic) | **S** | — |
| 785 | simbe-robotics | Simbe Robotics | 2023-07-13 | Series B | $54M total raised | (full take — 10x ARR growth) | **S** | — |
| 789 | serve-robotics | Serve Robotics | 2023-08-10 | Bridge | $56M total raised | (full take — pre-IPO bridge) | **K** | — (cumulative anchors pre-SPAC scale signal) |
| 794 | virtual-incision | Virtual Incision | 2023-09-19 | Series C (ext) | >$137M total raised | "Series C extension brings total raised to >$137M. MIRA mini-RAS (2lb robot in surgical tray) — won FDA de novo for colectomy in 2024. Pre-clearance financing..." | **K** | — (cumulative anchors pre-FDA-clearance financing scale) |
| 812 | verity | Verity | 2023-07-11 | Series B (ext) | $43M total Series B | (full take — round-extension structure) | **K** | — (round-level total) |
| 821 | tenstorrent | Tenstorrent | 2023-08-03 | Strategic | $334.5M total funding | "Up-round: Hyundai/Kia ($50M) targeting RISC-V silicon for vehicles, Samsung Catalyst ($50M) bridging foundry alignment. Total funding to $334.5M. Signals mainstream AI-IP ecosystem traction..." | **K** | — (cumulative anchors "mainstream AI-IP ecosystem traction" claim) |
| 822 | d-matrix | d-Matrix | 2023-09-06 | Series B | $154M total funding | "Series B for digital in-memory compute (DIMC) chiplet inference platform 'Corsair'; total funding to $154M. Microsoft M12 participation signals hyperscaler interest..." | **S** | — |
| 823 | aledia | Aledia | 2023-09-26 | Strategic | €360M total raised | "€120M from existing investors plus French sovereign capital to industrialize 3D microLED on 8-inch silicon (CEA-Leti spinout). Total raised exceeds €360M..." | **K** | — (cumulative anchors "industrialize on 8-inch" capital intensity) |
| 828 | kneron | Kneron | 2023-09-26 | Series B (ext) | $97M Series B / ~$190M total | "Edge AI chip extension brings total Series B to $97M and total funding to ~$190M. Foxconn lead foreshadows the auto + Taiwanese ODM ecosystem path..." | **K** | — (round-level + cumulative anchor Foxconn/ODM ecosystem signal) |
| 830 | gta-semiconductor | GTA Semiconductor | 2023-09-07 | Strategic | ~$2.7B total funding | "13.5B yuan ($1.85B) state-aligned cap injection — the largest single semis financing in Shanghai of 2023... Total funding ~$2.7B over two years." | **K** | — (cumulative + two-year pace anchors "largest in Shanghai" claim) |
| 834 | cerebras-systems | Cerebras Systems | 2023-07-20 | Strategic | >$900M total Condor Galaxy build | "G42's first $100M tranche of a planned 9-system Condor Galaxy supercomputer build (potential >$900M total) anchored Cerebras' 2023 revenue (G42 = 83% of FY23 sales)..." | **K** | — (cumulative is contract-tranche structure — load-bearing for revenue-anchor analysis) |
| 847 | aspinity | Aspinity | 2023-09-19 | Series B | >$19M total funding | (full take) | **S** | — |
| 851 | axiom-space | Axiom Space | 2023-08-21 | Series C | $505M total raised | "Series C at $505M total raised. Building first commercial modules for ISS by 2026, leading to standalone Axiom Station..." | **K** | — (cumulative anchors capital intensity of "first commercial ISS module" thesis) |
| 856 | space-pioneer-beijing-tianbing-technology | Space Pioneer | 2023-07-01 | Series C | ~$414M cumulative | (full take — first Chinese liquid rocket to orbit; cumulative anchors comp to SpaceX Falcon 9 analog) | **K** | — (cumulative anchors capital intensity vs SpaceX analog) |
| 862 | antaris | Antaris | 2023-09-06 | Seed (ext) | ~$10M cumulative seed | (full take — round-extension) | **K** | — (round-level) |
| 863 | kayhan-space | Kayhan Space | 2023-09-19 | Seed (ext) | $10.7M cumulative VC | (full take — round-extension) | **K** | — (round-level) |
| 865 | orienspace-... | Orienspace | 2023-08-05 | Series B (ext) | ~$150M cumulative | (full take — cumulative across rounds + subsequent) | **K** | — (cumulative anchors comp to Space Pioneer / iSpace) |
| 881 | covariant | Covariant | 2023-04-04 | Series C (ext) | $222M total raised | "Covariant Brain warehouse-picking foundation model; total raised $222M. Pieter Abbeel's foundation-model thesis preceded the 2024 reverse-acquihire by Amazon..." | **K** | — (cumulative anchors pre-Amazon-acquihire scale) |
| 884 | carbon-robotics | Carbon Robotics | 2023-04-11 | Series C | ~$67M total raised | (full take — labor-shortage thesis) | **S** | — |
| 907 | wingcopter | Wingcopter | 2023-05-10 | Debt Financing | >€100M total raised | "Quasi-equity venture loan from EIB to scale Wingcopter 198 eVTOL delivery drone for medical/groceries. Total raised >€100M across REWE, ITOCHU, Expa." | **K** | — (€100M crossover anchors EIB underwriting threshold) |
| 922 | b-garage | B Garage | 2023-06-29 | Series A | $30M total raised | (full take) | **S** | — |
| 924 | realtime-robotics | Realtime Robotics | 2023-06-27 | Series A (ext) | $54M total raised | (full take — round-extension) | **K** | — (round-level extension structure) |
| 933 | ayar-labs | Ayar Labs | 2023-05-24 | Series C (ext) | $155M total Series C | "In-package optical I/O for chip-to-chip connectivity. Up-round extends Series C to $155M total; NVDA participating signals strategic interest..." | **K** | — (round-level total) |
| 952 | true-anomaly | True Anomaly | 2023-04-06 | Series A | $30M total raised | (full take) | **S** | — |
| 954 | kepler-communications | Kepler Communications | 2023-04-13 | Series C | >$200M total raised | (full take — SDA Tranche 0/1 ecosystem) | **K** | — (cumulative anchors SDA-ecosystem capital fit) |
| 956 | hydrosat | Hydrosat | 2023-04-25 | Series A | $20M total | "Thermal-IR EO for ag/water/climate. $20M total announcement included $5M non-dilutive grants..." | **K** | — (round-level + grant-mix structure) |
| 960 | skyfi | SkyFi | 2023-05-23 | Seed | $17M total raised | (full take) | **S** | — |
| 965 | apex-space | Apex Space | 2023-06-22 | Series A | $27M total raised | (full take — 50ksqft LA factory) | **S** | — |
| 978 | skydio | Skydio | 2023-02-27 | Series E | $562M total funding | "Largest US drone maker raised at $2.2B post-money — total funding now $562M. The Axon investment signals deeper public-safety penetration..." | **K** | — (cumulative anchors "largest US drone maker" claim + valuation step) |
| 980 | outrider | Outrider | 2023-01-19 | Series C | $191M total raised | (full take — NVIDIA Ventures) | **S** | — |
| 981 | oxbotica | Oxbotica | 2023-01-10 | Series C | $225M total raised | (full take — Tencent strategic) | **S** | — |
| 982 | scythe-robotics | Scythe Robotics | 2023-01-24 | Series B | $60M total | (full take — 7,500 preorders) | **S** | — |
| 983 | photoneo-brightpick-group | Photoneo Brightpick Group | 2023-01-17 | Series B (ext) | $40M Series B / $53M total | (full take — round-extension after merger) | **K** | — (round-level total post-merger) |
| 987 | kewazo | KEWAZO | 2023-01-23 | Series A | $20M total | (full take — Fifth Wall lead) | **S** | — |
| 989 | terra-drone | Terra Drone | 2023-01-25 | Series C | $97M total raised | (full take — Aramco/Saudi Vision 2030) | **S** | — |
| 996 | zeitview | Zeitview | 2023-02-07 | Series E | $114M total raised | (full take — drone-data renewables) | **S** | — |
| 999 | third-wave-automation | Third Wave Automation | 2023-02-15 | Strategic | $70M total | (full take — Qualcomm + Zebra strategic) | **K** | — (cumulative load-bearing for strategic-syndicate scale framing) |
| 1006 | nimble-robotics | Nimble Robotics | 2023-03-16 | Series B | $115M total raised | (full take — 3PL pivot) | **K** | — (cumulative anchors 3PL-attack scale) |
| 1007 | plus-one-robotics | Plus One Robotics | 2023-03-08 | Series C | $94M total raised | (full take — 1M+ picks/day) | **S** | — |
| 1011 | ghost-autonomy | Ghost Autonomy | 2023-03-02 | Series E | $240M total raised | (full take — would shut down Oct 2024) | **K** | — (cumulative is the analytical core for "shut down despite $240M raised" L4-AV winter narrative) |
| 1016 | uisee | UISEE | 2023-03-24 | Series C | $154M total raised | (full take — Dongfeng strategic) | **S** | — |
| 1029 | lumotive | Lumotive | 2023-01-12 | Strategic | $56M cumulative | (full take — LCM beam-steering) | **S** | — |
| 1046 | isar-aerospace | Isar Aerospace | 2023-03-28 | Series C | >$330M total raised | "Largest SpaceTech round of Q1 2023 globally; total raised >$330M. Funds Spectrum SLV development for sovereign EU launch..." | **K** | — (cumulative anchors "leading European challenger to SpaceX" comp) |
| 1051 | boston-metal | Boston Metal | 2023-01-27 | Series C | $262M total (post-Sept-23) | "MIT spinout commercializing molten oxide electrolysis (MOE) for green steel... Series C first close; later expanded to $262M total in September 2023." | **K** | — (round-level total — extension structure) |
| 1054 | summit-nanotech | Summit Nanotech | 2023-01-17 | Series A | $72M total | "Direct lithium extraction (DLE) technology focused on Latin American brines... Series A2 at $50M brings total to $72M. DLE comp set with Lilac, EnergyX, Mangrove..." | **K** | — (cumulative anchors DLE comp-set positioning) |
| 1060 | d-robotics | D-Robotics | 2026-04-08 | Series B (ext) | $270M cumulative B | (full take — Chinese answer to NVIDIA Cosmos/Isaac) | **K** | — (round-level cumulative is load-bearing for sovereignty/comp framing) |
| 1096 | openlight | OpenLight | 2026-04-28 | Series A (ext) | $84M total | (full take — PDK-licensing alternative) | **K** | — (cumulative anchors "PDK-licensing alternative" capital-stack thesis) |
| 1103 | quantum-art | Quantum Art | 2026-04-27 | Series A (ext) | $140M total | "Series A extension from $100M (Dec 2025) to $140M total marks Quantum Art as the best-capitalized trapped-ion player outside IonQ (IONQ) and Quantinuum..." | **K** | — (cumulative is "best-capitalized" comp anchor — explicitly the load-bearing case in the user's spec) |
| 1104 | spinq-technology | SpinQ Technology | 2026-04-03 | Series C (ext) | ~CNY 1B cumulative C | (full take — pacing signal) | **K** | — (cumulative + pacing is the analytical core) |
| 1113 | true-anomaly | True Anomaly | 2026-04-28 | Series D | $1B total raised | "Pure-play orbital defense round at 3x valuation step-up... The 1B total raised and 500-headcount target by year-end signal the company is staffing for prime-contractor scale, not subcontractor..." | **K** | — (cumulative + headcount jointly anchor prime-contractor-scale framing) |
| 1123 | pld-space | PLD Space | 2026-04-07 | Debt Financing | E210M 2026 cumulative | (full take — EIB first direct in small launchers) | **K** | — (2026 YTD cumulative load-bearing for "largest year for European small-launcher" claim) |
| 1131 | zipline | Zipline | 2026-03-23 | Series H (ext) | $800M total H round | "Series H extension brings total H round to $800M and tags Paradigm onto a crossover-heavy IPO-prep syndicate..." | **K** | — (round-level + IPO-prep signal load-bearing) |

---

## Summary counts

- **Total cumulative-funding mentions audited**: 127
- **KEEP**: 70 (figure load-bearing for analytical point — round structure, valuation step, comp-set positioning, capital-intensity thesis, IPO/exit framing, etc.)
- **STRIP**: 41 (figure reads as balance-sheet recitation, deletion is loss-less)
- **REWRITE**: 16 (figure should stay but framing needs v1.1 comp-set + view treatment):
  - idx 4 — Stoke Space Series C (Jan-25) — user-flagged headline case
  - idx 20 — Lambda Series D (Feb-25) — user-flagged headline case
  - idx 27 — Epirus Series D (Mar-25)
  - idx 30 — Celestial AI Series C (Mar-25)
  - idx 35 — CMR Surgical (Apr-25)
  - idx 46 — True Anomaly Series C (Apr-25)
  - idx 60 — Impulse Space Series C (Jun-25)
  - idx 73 — ForSight Robotics Series B (Jun-25) — user-flagged headline case
  - idx 85 — Varda Space (Jul-25)
  - idx 88 — XTEND (Jul-25)
  - idx 92 — Hadrian (Jul-25)
  - idx 102 — SiMa.ai Series C (Aug-25)
  - idx 109 — Blue Water Autonomy (Aug-25)
  - idx 110 — Aerospacelab (Aug-25)
  - idx 114 — proteanTecs (Sep-25)
  - idx 732 — Stoke Space Series B (Oct-23)

---

## Notes for v1.1.1 release

1. **STRIP candidates (41)** are the lowest-risk edits — pure deletions of the cumulative clause leave the take coherent and remove the stale-figure exposure.
2. **REWRITE candidates (16)** are higher-value edits — most are 2025-vintage takes (idx 4–123) written in the pre-v1.1 "balance-sheet recitation" style, before the comp-set + view rubric was adopted in late-2025 / early-2026 takes (which is why almost all 2026 entries land in KEEP).
3. **KEEP candidates** mostly cite round-level cumulative totals (extension structure), best-capitalized-in-category claims, or pre-IPO scale signals where the cumulative is the analytical point. These figures are sourced from primary announcements at the time and are not inherited from the (now-deprecated) `total_raised_m` field.
4. **Stoke Space**: no double-count, no row drops needed. idx 4 take (Jan-25 Series C) is the priority rewrite; idx 732 (Oct-23 Series B) is secondary rewrite.
5. **Cross-check before ship**: the 8 highest-priority rewrites (idx 4, 20, 27, 30, 35, 46, 60, 73) should be reviewed against current primary-source cumulative figures so the rewrites do not re-introduce stale data via the new comp-set framing.
6. **Rewrite length sanity**: all 16 proposed rewrites are within the 580-char hard cap (range 381–474, all under 580). Two land in the 450–550 target window (idx 4 and idx 732); the other 14 are 381–444 (compact but under-target). If 450–550 is the v1.1 floor, those should be expanded with one additional comp-set or catalyst sentence before ship.
