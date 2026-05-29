# Proposed Commodities Cohort — Step 1 Surface

## Headline distribution

| Category | Proposed count | Notes |
|---|---:|---|
| Critical minerals (rare earths + battery + strategic) | 17 | Replaces REMX + LIT ETFs with underlying prices; adds Sm, HPMSM. |
| Semi inputs (wafer materials + process gases + specialty metals) | 24 | Largely new; covers polysilicon through fab consumables and noble gases. |
| Energy + propulsion + space stack | 5 | Uranium retained; Henry Hub repurposed as methalox proxy; LOX/hydrazine/N2O4 as narrative tiles. |
| Cross-stack / macro reference | (folded into critical minerals) | Cu, Al, Ag carried in critical minerals bucket. |
| **Total proposed (priced + narrative)** | **~46** | Compared to 10 in current `commodities.json`. |
| Explicitly excluded | 11 | Iron ore, coal, ag, RP-1, He-3, gold, platinum, crude WTI, etc. |
| Flagged for review | 16 | Ambiguous includes, thin-pricing markets, taxonomic borderline cases. |

---

## Final cohort (proposed)

### Critical minerals

| Commodity | Frontier-stack use | Include rationale |
|---|---|---|
| Neodymium (NdPr oxide) | NdFeB magnets in EV traction, humanoid actuators, servos, drones, HDDs, wind turbines | China ~85% mine + ~90% separation; 2025 magnet export licensing is core frontier-stack story. |
| Praseodymium | Co-substitutes with Nd in NdFeB magnets at ~20-25% of REE content | Co-mined/co-separated with Nd; industry trades the pair as NdPr/didymium. |
| Dysprosium | Heavy REE additive for high-temp NdFeB (EV, robotics, defense actuators) | ~100% China + Myanmar supply; April 2025 export controls were a supply shock. |
| Samarium | SmCo magnets for >200C aerospace/defense actuators (jet engines, missile guidance) | High-temp alternative to NdFeB; added to April 2025 China export-license regime. |
| Lithium (carbonate + hydroxide) | Cathode/electrolyte for every Li-ion battery (EV, robot, drone, satellite, grid) | Defining battery mineral; LME/GFEX/CME pricing; replaces LIT.US ETF. |
| Cobalt (metal + battery-grade sulfate) | NMC/NCA cathode in premium EVs/robotics/aerospace; superalloys | ~70% DRC, ~75% China refining; LME futures + Fastmarkets payable. |
| Nickel (Class 1 / battery-grade) | NMC/NCA cathode workhorse; aerospace superalloys | Battery-grade decoupled from Class 2 NPI; track LME + sulfate premium. |
| Manganese (HPMSM) | LMFP, LMR, manganese-rich cathodes for EVs and grid storage | HPMSM decoupled from steel ferromanganese; fastest-growing cathode segment. |
| Graphite (natural spherical + synthetic anode) | Anode in every Li-ion battery; ~50-100 kg per 100 kWh | China >90% spherical processing; December 2023 export controls. |
| Tantalum | Capacitors for high-reliability electronics (satellites, defense, datacenter) | Highest volumetric capacitance; DRC/Rwanda conflict-mineral choke point. |
| Niobium | Superconducting magnets (MRI/quantum), HSLA aerospace steel, NbTi accelerators, emerging Nb-anode | CBMM ~85% global supply — one of the most concentrated commodities tracked. |
| Antimony | Sb2O3 flame retardants; Sb-doped semis; emerging liquid-metal grid batteries | China September 2024 export controls tripled price in 12 months. |
| Tungsten (APT) + WF6 | Carbide tooling for precision/semi machining; CVD interconnects, 3D NAND wordlines | China ~80% mining; February 2025 export controls; WF6 ties to NAND layer growth. |
| Tin | Solder for every PCB, IC package, electronics assembly | Cleanest semi-supply commodity signal; LME-traded; Myanmar 2023 disruption demonstrated sensitivity. |
| Copper | Datacenter power, EV motors, BEOL Cu damascene, grid for AI compute | Structural deficit 2027-2030 driven by datacenter + EV; LME/COMEX-liquid. |
| Aluminum | Datacenter mechanicals, EV body-in-white, launch vehicle structures (Al-Li) | Real frontier-stack pull; China ~58% primary, Rusal sanctions risk. |
| Silver | PV cell paste; SiC/GaN die-attach; MLCC inner electrodes; brazing | PV is largest growth driver in industrial demand; XAG/USD already in universe. |

### Semi inputs

| Commodity | Frontier-stack use | Include rationale |
|---|---|---|
| Hyperpure polysilicon (semi grade) | Monocrystalline ingot feedstock for 300mm wafers in all CMOS chips | 11N+ purity foundation; Wacker/Hemlock/OCI/Tokuyama oligopoly; 2021-23 cycle choke point. |
| SiC substrates | Power semis in EV inverters, fast charging, datacenter PSUs, satellite power | Documented EV-electrification choke point; 150/200mm transition reshapes cost curve. |
| Gallium (metal + GaAs) | GaAs/GaN RF (5G/6G, radar, satcom), power electronics, LEDs | China ~98% primary; July 2023 export controls — opening salvo of semi materials trade war. |
| GaN substrates | Fast chargers, datacenter PSUs, 5G/6G RF, EV onboard chargers | Sumitomo/Mitsubishi Chemical dominate bulk GaN; same gallium concentration risk. |
| Indium (metal + InP) | InP for 100G/400G/800G optical transceivers; ITO displays; CIGS PV | InP is AI-datacenter optical-interconnect bottleneck; on China December 2024 dual-use list. |
| Germanium | SiGe RF, space-grade triple-junction PV, IR defense optics, Ge-on-Si photonics | Critical to every commercial satellite PV; July 2023 China export controls. |
| Tellurium | CdTe thin-film solar; HgCdTe IR detectors; thermoelectric generators | Byproduct of Cu electrorefining concentrated in China/Russia; PV-led demand. |
| Hafnium | HfO2 high-k gate dielectric in all advanced-node CMOS; aerospace superalloys | Tiny ~75 t/yr byproduct of Zr refining; foundational to every advanced logic device. |
| Zirconium | Nuclear fuel cladding (SMR/advanced reactor cycle); semi furnace ceramics; SOFC | Tied to AI-compute power buildout via nuclear; co-product source of Hf. |
| Ruthenium | Sub-3nm BEOL liner candidate (IMEC/Intel/TSMC); HDD PMR layers | ~30 t/yr market with ~90% Russia/SA supply; semi-pull moves price materially. |
| Palladium | MLCC plating, lead-frame finish, fuel-cell catalysts | NYMEX-traded; primary value is Russia (Nornickel) concentration signal. |
| Helium (high-purity) | MRI/quantum dilution cryo; semi wafer cooling, leak detection; rocket pressurant | Non-substitutable; chronic shortage cycles; bridges semi + space + quantum. |
| Neon (lithography grade) | KrF/ArF excimer laser buffer gas in every DUV-using fab | Canonical 2022 Ukraine supply-shock story; ~50% pre-war supply from Mariupol/Odesa. |
| Xenon | Hall thruster propellant for GEO comsats; excimer laser fill gas; EUV sub-systems | Dual-use space/fab; Ukrainian/Russian ASU concentration. |
| Krypton | KrF excimer lithography; Hall thruster propellant for Starlink v1.5 | Rare ASU byproduct; Starlink shift to Kr created new structural demand. |
| Argon (electronic grade) | PVD sputter, plasma etch carrier, CZ Si/SiC crystal growth | Workhorse inert gas; 6N+ specialty grades concentrated. |
| Tungsten hexafluoride (WF6) | CVD tungsten plug deposition; 3D NAND wordlines; EUV mask absorber | Sole precursor; volume scales with NAND layer count; concentrated specialty supply. |
| Photoresist (EUV + ArF immersion) | Lithography polymer films defining every transistor and metal layer | JSR/TOK/Shin-Etsu/Sumitomo/Fujifilm ~90% advanced-node share — Japan concentration. |
| CMP slurry | CMP at every metal layer; HBM/3D-IC TSV CMP | Cabot/Versum/Fujimi/Showa Denko dominate; advanced-node planarization enabler. |
| Sputtering targets (Ta, Ti, Cu, Co, Ru) | PVD interconnect barriers, seed layers, emerging liners | Honeywell/Materion/JX Nippon/Praxair Surface Tech control high-purity targets. |
| Synthetic fused silica / EUV mask blanks | EUV photomask blanks, DUV reticle substrates, fab quartzware | Heraeus/Shin-Etsu/AGC/Tosoh ultra-low-expansion quartz monopoly. |
| Silane (SiH4) / Disilane (Si2H6) | Poly-Si, a-Si, SiN/SiO CVD films; disilane for 3D NAND | REC Silicon/Linde/Air Liquide/Mitsui supply; disilane is quiet 3D NAND constraint. |
| Electronic-grade ammonia (NH3) | SiN/SiON dielectrics; GaN epi; plasma nitridation | 9N semi-grade is concentrated specialty market distinct from bulk fertilizer NH3. |
| Nitrogen trifluoride (NF3) | CVD chamber clean across logic, memory, display fabs | Korean (SK Specialty, Hyosung) / Japanese (Kanto Denka, Showa Denko) supply concentration. |
| Anhydrous HF (electronic grade) | Wafer cleaning, oxide etching, BOE solutions throughout fab | 2019 Korea-Japan dispute exposed chokepoint risk (Stella Chemifa, Morita, Solvay). |

### Energy + propulsion + space stack

| Commodity | Frontier-stack use | Include rationale |
|---|---|---|
| Uranium (U3O8) | Nuclear fuel for SMRs powering AI datacenters; naval/space NTP/NEP | Hyperscaler PPAs + SMR developers tie U directly to AI compute; SRUUF NAV as transparent proxy. |
| Natural Gas (Henry Hub — methalox proxy) | Methalox for Starship, New Glenn, Neutron, Terran R, Vulcan; fab/datacenter baseload | HIGH strategic relevance for next-decade launch architecture; only tradeable methane proxy. |
| Liquid Oxygen (LOX) — narrative | Universal oxidizer for Falcon 9, Starship, Vulcan, New Glenn, Electron, Neutron, SLS | Single most-consumed propellant by mass; industrial-gas supply is launch-cadence bottleneck. |
| Hydrazine + MMH/UDMH — narrative | Satellite monoprop/biprop; crewed capsule abort; Russian/Chinese launchers | Concentrated supply + REACH regulation; real choke point for satellite manufacturers. |
| Nitrogen tetroxide (N2O4) / MON — narrative | Hypergolic oxidizer for satellite RCS, AKMs, Dragon Draco/SuperDraco, legacy launchers | Irreplaceable for storable-propellant satellite ops despite green-propellant push. |

---

## Added from omissions sweep

Commodities not present in current `commodities.json` (10 entries: gold, silver, platinum, palladium, copper, lithium ETF, oil WTI, natural gas, REMX, uranium ETF).

| Name | Category | Reason to include | Frontier-stack use |
|---|---|---|---|
| Neodymium | Critical minerals | Magnet supply chain headline; replaces REMX ETF | NdFeB magnets in EV/robotics/wind |
| Praseodymium | Critical minerals | Industry-standard NdPr trading unit | Co-substitute in NdFeB magnets |
| Dysprosium | Critical minerals | April 2025 China export shock | High-temp NdFeB additive |
| Samarium | Critical minerals | SmCo aerospace/defense magnets; April 2025 license regime | High-temp permanent magnets |
| Cobalt (metal + sulfate) | Critical minerals | DRC concentration + battery-grade sulfate premium | NMC/NCA cathode |
| Nickel (Class 1) | Critical minerals | Battery-grade signal distinct from LME bulk | NMC/NCA cathode |
| Manganese (HPMSM) | Critical minerals | LMFP/LMR cathode growth segment | Manganese-rich Li-ion |
| Graphite (anode-grade) | Critical minerals | China export controls; FEOC watch list | Li-ion anode |
| Tantalum | Critical minerals | Conflict mineral; capacitor choke point | Hi-rel electronics capacitors |
| Niobium | Critical minerals | CBMM ~85% concentration | Superconducting magnets, HSLA, NbTi |
| Antimony | Critical minerals | 2024 export controls tripled price | Sb-doped semis, flame retardants |
| Tungsten (APT) | Critical minerals | February 2025 export controls | Carbide tooling, semi interconnects |
| Tin | Critical minerals | Cleanest semi-supply signal | Solder for all electronics |
| Aluminum | Critical minerals | Aerospace, EV bodies, datacenter mech | Al-Li alloys, structural |
| Hyperpure polysilicon | Semi inputs | Substrate of every CMOS chip | Monocrystalline wafer feedstock |
| SiC substrates | Semi inputs | EV power-electronics choke point | Wide-bandgap power semis |
| Gallium (metal + GaAs) | Semi inputs | China ~98% primary; July 2023 controls | GaAs/GaN RF and power |
| GaN substrates | Semi inputs | Fast chargers, datacenter PSUs, 5G RF | Wide-bandgap power and RF |
| Indium (metal + InP) | Semi inputs | AI optical-interconnect bottleneck | InP transceivers, ITO displays |
| Germanium | Semi inputs | July 2023 China controls; space PV | SiGe RF, space PV, IR optics |
| Tellurium | Semi inputs | Byproduct economy; CdTe + HgCdTe | Thin-film PV, IR defense |
| Hafnium | Semi inputs | High-k gate dielectric in all advanced CMOS | HfO2 gate stack |
| Zirconium | Semi inputs | SMR build cycle; Hf co-product | Nuclear cladding, semi ceramics |
| Ruthenium | Semi inputs | Sub-3nm BEOL liner candidate | Advanced-node interconnect |
| Helium (high-purity) | Semi inputs | Non-substitutable; chronic shortages | Cryo for MRI/quantum/semi |
| Neon (litho grade) | Semi inputs | 2022 Ukraine supply shock | DUV excimer buffer gas |
| Xenon | Semi inputs / Space | Hall thrusters + excimer + EUV | Ion propulsion + lithography |
| Krypton | Semi inputs / Space | KrF DUV + Starlink Hall thrusters | DUV + electric propulsion |
| Argon (electronic) | Semi inputs | PVD/plasma/crystal-growth workhorse | 6N+ specialty inert gas |
| WF6 | Semi inputs | Sole tungsten CVD precursor | 3D NAND wordlines, plug deposition |
| Photoresist (EUV + ArF) | Semi inputs | ~90% Japan-controlled; binds N2/A14 yields | Lithography polymer films |
| CMP slurry | Semi inputs | Advanced-node planarization enabler | Metal-layer CMP, HBM TSV |
| Sputtering targets | Semi inputs | High-purity PVD source materials | Interconnect barriers/seeds/liners |
| Synthetic fused silica | Semi inputs | EUV mask blanks; quartzware | Photomask substrates, fab tubes |
| Silane / Disilane | Semi inputs | Si CVD/ALD source gas | Poly-Si, SiN/SiO, 3D NAND |
| Electronic-grade ammonia | Semi inputs | SiN/GaN deposition | Dielectric and epi N source |
| NF3 | Semi inputs | Dominant CVD chamber clean | PECVD chamber clean |
| Anhydrous HF | Semi inputs | 2019 Korea-Japan choke-point story | FEOL wafer cleaning, BOE |
| LOX | Energy + propulsion | Universal launch oxidizer | Kerolox/methalox/hydrolox |
| Hydrazine + MMH/UDMH | Energy + propulsion | Satellite propulsion + REACH constraint | Satellite mono/biprop |
| N2O4 / MON | Energy + propulsion | Storable-propellant choke point | Hypergolic satellite/capsule oxidizer |

---

## Explicitly excluded

| Name | Reason |
|---|---|
| Bulk steel (HRC / rebar) | Construction-driven; no frontier signal. GOES electrical steel flagged separately. |
| Iron ore | Chinese property-cycle driven; no semi/robotics/space relevance. |
| Coal (thermal + metallurgical) | Fuel/steelmaking; grid signal better captured by uranium. |
| Crude Oil (WTI) — **currently in universe** | Macro/OPEC+ signal; petrochemical derivatives behave independently. Recommend removal. |
| Gold — **currently in universe** | Investment/monetary signal; electronics is <5-8% demand. Recommend removal or relabel as macro hedge. |
| Platinum — **currently in universe** | No distinct frontier-stack use vs auto-cat/jewelry. Recommend removal. |
| Rare Earths ETF (REMX.US) — **currently in universe** | Replace with underlying Nd/Pr/Dy/Sm series. |
| Lithium ETF (LIT.US) — **currently in universe** | Replace with direct lithium carbonate + hydroxide pricing. |
| Agricultural commodities | No frontier-stack supply-chain relevance. |
| RP-1 (rocket kerosene) | No tradeable market; methalox is structurally displacing it. |
| Helium-3 | No commercial market; speculative fusion/quantum use; administered DOE pricing. |

---

## Flagged for review

| Name | Nature of ambiguity | Suggested handling |
|---|---|---|
| Terbium | HIGH strategic relevance but thinnest pricing of any tracked commodity | FLAG: include via Lynas/Energy Fuels equity proxies + Asian Metal reference |
| Dysprosium | Strong policy signal but EODHD coverage gap | Include with equity-proxy fallback; episodic Asian Metal data |
| Niobium | CBMM contract pricing; 90% of demand is HSLA steel | Include for concentration completeness; flag muted frontier-stack signal |
| Scandium | No primary mine; Al-Sc rocket adoption pre-scale | Watchlist narrative tile only |
| Yttrium | YSZ + YAG real but thin market overlapping other REE pricing | Defer to v2 unless user wants low-confidence REE coverage |
| Bismuth | Bi2Te3 Peltier cooling; small volumes; December 2024 export controls | FLAG — include if export-control policy tracking warrants |
| Silicon metal (met grade) | Upstream of polysilicon; bulk market conflated with PV/ferrosilicon | Decide: track separately vs consolidate under semi-grade polysilicon |
| Magnesium | Kroll-process Ti aerospace + EV lightweight alloys; China ~85% | Strong case to include — confirm |
| Vanadium | VRFB grid storage + Ti-6Al-4V aerospace | Defer to v2 unless VRFB ramp accelerates |
| Liquid Hydrogen | Space upper stages + semi fab UHP H2; no tradeable spot | Narrative tile via industrial-gas-equity proxy |
| Helium-3 | Pre-commercial; administered pricing | Watchlist-only |
| GOES electrical steel | Datacenter/EV/wind exposure; contract pricing opaque | Track as supply-chain narrative; promote if pricing access emerges |
| Tellurium | CdTe-PV-led demand; behaves PV-adjacent more than semi | Keep with PV-demand caveat or move to materials/PV bucket |
| Palladium | Auto-cat dominates demand; semi use is minority | Retain as Russia-concentration signal with caveat |
| Aluminum | Frontier share small vs construction/transport | Include as macro reference; do not over-weight in composites |
| Methane (Henry Hub) | Bulk pricing dominated by US power/heating | Retain as space-stack proxy with explicit tag |

---

## Open questions

1. **Headline vs sub-categories.** For Lithium (carbonate + hydroxide), Nickel (Class 1 + sulfate premium), Cobalt (metal + sulfate), Tungsten (APT + WF6), Gallium (metal + GaAs/GaN): single headline with sub-fields or separate top-level entries?
2. **NdPr consolidation.** Track neodymium + praseodymium as a single 'NdPr oxide' line item (how the magnet supply chain trades) or keep as two separate entries?
3. **Drop from starting universe.** Confirm removal of Gold, Platinum, Crude Oil (WTI), LIT.US, and REMX.US from `commodities.json`, or push back per item.
4. **Specialty fab chemicals/gases scope.** ~12 process-gas and chemical inputs have no public spot pricing (WF6, photoresist, CMP slurry, sputtering targets, silane, NH3, NF3, HF, neon, xenon, krypton, argon). Accept opaque-pricing entries via equity-proxy/vendor-disclosure tracking, or trim to publicly-priced inputs only?
5. **Energy + propulsion narrative tiles.** LOX, hydrazine/MMH/UDMH, N2O4 have no tradeable price. Carry as qualitative supply-chain narrative tiles or exclude until pricing exists?
6. **Borderline v1 vs v2.** Which of these merit v1 inclusion vs deferred expansion: Magnesium (Ti-aerospace), Vanadium (VRFB), Yttrium (YSZ/YAG), Bismuth (Bi2Te3), Scandium (Al-Sc rocket), GOES electrical steel, Tellurium (CdTe)?