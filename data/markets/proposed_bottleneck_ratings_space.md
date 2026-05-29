# Proposed Bottleneck Ratings — Space Batch (B4 Sector 3)

**Status:** Proposal for review. NOT YET WRITTEN to `enrichment_data.json`.

Workflow produced 27 ratings across 7 subsectors via parallel agents + adversarial verify on every elevated proposal. **No CRITICAL** — Space has no monopolies in the ASML/Lasertec sense. **2 HIGH** (BWXT, ASTS), both verifier-confirmed. **2 UNRATED** flagged as registry data-quality issues — cohort labels don't match actual public entities.

## Distribution

| Rating | Count |
|---|---:|
| HIGH | 2 |
| MEDIUM | 8 |
| LOW | 15 |
| UNRATED | 2 |
| **Total** | **27** |

## Combined coverage after this batch

Existing rated entities (post-Robotics): 193
Adding 25 new (UNRATED skipped): 218
Of 566 registry → ~38.5% universe coverage

## HIGH proposals — verifier verdicts

### BWXT — BWX Technologies | Proposed **HIGH** | Verifier: **✓ confirm**

**Description:** Sole US manufacturer of naval nuclear reactors and HEU fuel; designated DARPA DRACO partner for the only US in-space nuclear thermal propulsion program.

**Rationale:** BWXT is the sole-source supplier of naval nuclear reactors and HALEU/HEU fuel for US Navy submarines and aircraft carriers, with a $7.4B backlog and a $1.4B+ contract announced May 2026. For in-orbit/space relevance, BWXT is the prime nuclear reactor supplier for the DARPA DRACO nuclear thermal rocket and NASA/DOE space nuclear power programs, with no domestic competitor at the same TRL. Rated HIGH rather than CRITICAL within the In-Orbit Services subsector because space nuclear demand is still nascent and government-only — but the underlying technology and clearances are functionally irreplaceable for any US space nuclear mission.

**Key customers:** US Navy (Naval Nuclear Propulsion Program), DARPA (DRACO), NASA, DOE, US DoD, Rolls-Royce/UK Space Agency partnership
**Key suppliers:** Specialty zirconium alloy mills, HALEU enrichment (Centrus/Urenco/DOE), heavy-forging vendors
**Confidence:** HIGH

**Verifier reasoning:** HIGH stands despite the rationale being materially outdated. DRACO was cancelled in May 2025 and the FY2026 NASA budget zeroed out nuclear thermal propulsion, so the headline "DARPA DRACO partner" claim is obsolete. However, BWXT remains the only US entity with NRC Category-1 licensed HEU facilities, an active Erwin enrichment buildout, and decades of flight-qualified reactor hardware experience, which positions it as the most likely prime for the new SR-1 Freedom (Mars 2028) and NSTM-3 lunar reactor mandates. Competitors exist (Westinghouse with Aerojet Rocketdyne, IX/X-energy, USNC, General Atomics, SpaceNukes) and any of them could win individual contracts in 12-24 months, which is why HIGH not CRITICAL is correct — but no competitor can match the combined fuel + reactor + clearance stack on the timeline NASA/DoD now require.

**Refutation attempts considered:** (1) DRACO cancellation: Confirmed cancelled May 2025 (DARPA stop-work to Lockheed; FY26 NASA budget zeros NTP). This kills the rationale's core in-orbit anchor but does not kill the underlying capability — White House NSTM-3 (Apr 2026) and SR-1 Freedom (Mar 2026 announcement, Dec 2028 launch window) re-create demand BWXT is best positioned to capture. (2) Westinghouse substitution: Westinghouse has the deepest commercial nuclear base and won a 2022 FSP Phase 1 award alongside BWXT — credible competitor but lacks NRC Cat-1 HEU/HALEU processing license; would need 5+ years to replicate. (3) IX (Intuitive Machines + X-energy) and USNC also hold FSP contracts; both lack flight-qualified reactor hardware history. (4) SpaceX vertical-integration: Not relevant — SpaceX has no nuclear capability and the DRACO cancellation rationale (Starship cuts launch cost) actually undermines NTP demand thesis broadly. (5) China/India sovereign capability: ITAR/EAR + naval clearance moat means foreign capability does not substitute for US government customers (the only customers). (6) Could a customer switch in 1-2 quarters? No — HEU/HALEU handling licenses, NRC Cat-1 facility build, and Navy/Department of Energy classified clearances are 3-7 year barriers. (7) Naval claim ($7.4B backlog grew to $8.65B; $1.4B contract confirmed Q1 2026) is genuine sole-source but belongs to a Defense subsector, not In-Orbit Services — the rationale conflates two segments. Net: HIGH is defensible but the description/rationale should be rewritten to acknowledge DRACO cancellation and pivot to SR-1 Freedom / NSTM-3 / FSP as the in-orbit anchors.

### ASTS — AST SpaceMobile | Proposed **HIGH** | Verifier: **✓ confirm**

**Description:** Only commercial operator with FCC SCS authorization to deliver true broadband direct-to-standard-smartphone connectivity over licensed terrestrial MNO spectrum, protected by a large patent portfolio around large-aperture phased-array satellites.

**Rationale:** Matches the HIGH anchor directly. ASTS holds FCC priority access for nationwide direct-to-cellular SCS via partner MNO spectrum, a proprietary 64m^2 aperture phased-array architecture, and an exclusive patent moat that Starlink/T-Mobile has not been able to replicate at comparable performance (Starlink direct-to-cell is currently text/low-bandwidth only). Switching costs for MNO partners committing spectrum and revenue-share are multi-year, and FCC SCS framework is gated. Not CRITICAL because Starlink and future Kuiper/Lynk are viable, if inferior, substitutes for a subset of use cases.

**Key customers:** AT&T, Verizon, Vodafone, Rakuten, Bell Canada, Telefonica, ~60 MNO partners covering >3B subscribers, US Space Development Agency / DoD
**Key suppliers:** In-house BlueBird satellite manufacturing (Midland TX), launch partners (SpaceX Falcon 9, Blue Origin New Glenn, ISRO), L3Harris/Cubic for components, contract semiconductor partners for ASIC
**Confidence:** HIGH

**Verifier reasoning:** Confirm HIGH. ASTS holds genuinely differentiated position: full FCC SCS authorization (May 2026) for 248-satellite constellation enabling broadband-class direct-to-standard-smartphone over MNO-licensed spectrum, locked-in AT&T contract through 2030 plus Verizon commercial agreement, 3,400+ patent claims (1,240+ granted) around 2,400 sq ft phased-array aperture that competitors physically cannot match per-satellite (Starlink D2C antenna ~65 sq ft, still text/low-bandwidth only; Lynk pivoted to narrowband IoT post-Omnispace; Amazon Leo D2D still "in development"). The newly announced AT&T/T-Mobile/Verizon JV explicitly preserves existing partnerships rather than disintermediating ASTS, and spectrum coordination plus revenue-share integration genuinely take multi-year horizons to replicate. Not CRITICAL because Starlink (text/emergency), Amazon Leo, and Lynk provide inferior partial substitutes for narrowband use cases, and execution risk is elevated (Blue Origin New Glenn anomaly lost BlueBird-7 in April 2026, New Glenn explosion in late May threatens 45-satellite end-of-2026 goal) — but execution risk affects timing, not the structural moat the rating describes.

**Refutation attempts considered:** Attempted downgrades that failed: (1) "Starlink will eat ASTS via vertical integration" — refuted: Starlink D2C antenna is ~35-40x smaller per satellite (~65 sq ft vs 2,400 sq ft), physically limiting bandwidth; current service is text/emergency only via T-Mobile, and the T-Mobile/Starlink deal does not extend to AT&T or Verizon spectrum. (2) "AT&T/T-Mobile/Verizon JV (announced 2026) commoditizes satellite providers" — refuted: JV explicitly preserves existing carrier-satellite partnerships (AT&T/Verizon with ASTS, T-Mobile with Starlink, Verizon with Amazon Leo/Skylo) and is designed to standardize integration, not redistribute spectrum exclusivity. (3) "MNOs could switch in 1-2 quarters" — refuted: AT&T contract runs through 2030, spectrum coordination plus revenue-share renegotiation is multi-year, and there is no broadband-capable substitute commercially available today. (4) "Amazon Leo/Kuiper rapidly displaces ASTS" — refuted: Amazon D2D is "in development," constellation launches just beginning Q1 2026 commercial, smartphone service not deployed. (5) "China Guowang/Qianfan undermines monopoly" — refuted: sovereign Chinese constellation is geopolitically siloed, cannot operate over US/EU/Japan MNO spectrum, addresses different market. (6) "Lynk Global competes" — refuted: Lynk pivoted to narrowband IoT/messaging post-Omnispace merger, not broadband. (7) "Launch failures could kill the thesis" — execution risk is real and material but does not change the structural moat (FCC priority, MNO contracts, patent IP, large-aperture architecture); affects timing of commercial ramp, not the rating anchor.

## UNRATED entries (registry data-quality flags)

### ATNM — registry mismatch

**Cohort label:** Astrana Holdings (cohort label)

**Issue:** The ticker ATNM in publicly available equity records refers to Actinium Pharmaceuticals (oncology biotech), which has no in-orbit services exposure. There is no publicly traded 'Astrana Holdings' or 'Astranis' equity matching the $0.8B mcap operator description (Astranis is a private high-orbit satellite manufacturer that raised a $450M Series E in May 2026 but remains private). The local Robotnik entity registry classifies ATNM as 'Autonoma Network', a CoinGecko token. Given the inability to defensibly identify the intended entity, I propose UNRATED pending parent-orchestrator clarification.

**Recommendation:** registry hygiene audit — either correct the entity mapping or remove from the universe.

### SLC — registry mismatch

**Cohort label:** Superloop Ltd (ASX:SLC) — cohort label says Spirit Realty Capital

**Issue:** Cannot defensibly rate this as a satellite-communications bottleneck because the identified company (Superloop) is a terrestrial fiber/ISP business with effectively zero satellite exposure, and the descriptive label 'Spirit Realty Capital' refers to a defunct net-lease REIT that was never in satellite communications. Either interpretation puts the entity outside the cohort framework. Proposing UNRATED rather than guessing; the universe entry should be reviewed and either reclassified to Telecom or removed.

**Recommendation:** registry hygiene audit — either correct the entity mapping or remove from the universe.

## Full ratings by subsector

### Unknown (10 tickers)

| Ticker | Name | Proposed | Confidence | Bottleneck |
|---|---|---|---|---|
| BWXT | BWX Technologies | **HIGH** | HIGH | Sole US manufacturer of naval nuclear reactors and HEU fuel; designated DARPA DRACO partner for the only US in-space nuclear thermal propulsion program. |
| ASTS | AST SpaceMobile | **HIGH** | HIGH | Only commercial operator with FCC SCS authorization to deliver true broadband direct-to-standard-smartphone connectivity over licensed terrestrial MNO spectrum, protected by a large patent portfoli… |
| GOGO | Gogo Inc | **MEDIUM** | HIGH | Post-Satcom Direct merger, sole provider of end-to-end multi-orbit (ATG + GEO + LEO Galileo) connectivity for business aviation with ~90% combined share; switching constrained by aircraft certifica… |
| RKLB | Rocket Lab USA | **MEDIUM** | HIGH | Electron is the second-most-flown US orbital launcher and the clear leader for dedicated small-satellite missions, with Neutron medium-lift in development to challenge Falcon 9 for constellation de… |
| PL | Planet Labs | **LOW** | HIGH | Daily global optical imaging is a competitive market with multiple substitutes (BlackSky, Maxar, Airbus, Satellogic) and no irreplaceable input. |
| 288A JP | Synspective | **LOW** | HIGH | Commercial SAR imaging is a competitive market with ICEYE, Capella Space, Umbra and Airbus as direct substitutes; Synspective is the Japan-anchored SAR provider but not sole-source. |
| TRMB | Trimble Inc. | **LOW** | HIGH | Leading but not sole-source supplier of high-precision GNSS receivers, RTK base stations, and geospatial software in a multi-vendor market. |
| GEOD | GEODNET | **LOW** | MEDIUM | Decentralized RTK/GNSS correction network competing with incumbent centralized providers (Trimble, Hexagon, Swift Navigation, u-blox PointPerfect) that offer fully substitutable precision-positioni… |
| ATNM | Astrana Holdings (cohort label) | **UNRATED** | LOW | Ticker assignment ambiguous: cohort label is 'Astrana Holdings, $0.8B mcap, Operator' but US-listed ATNM (Actinium Pharmaceuticals) is biotech, not space; private 'Astranis' is not publicly traded;… |
| SLC | Superloop Ltd (ASX:SLC) — cohort label says Spirit Realty Capital | **UNRATED** | LOW | Ticker appears mis-classified: ASX:SLC is Superloop, an Australian fiber/NBN wholesale and retail ISP with no satellite communications operations; legacy 'Spirit Realty Capital' was net-lease REIT … |

### In-Orbit Services (8 tickers)

| Ticker | Name | Proposed | Confidence | Bottleneck |
|---|---|---|---|---|
| GSAT | Globalstar | **MEDIUM** | MEDIUM | MSS L/S-band spectrum and Band 53/n53 licenses underpinning Apple's iPhone Emergency SOS service; substitute D2D paths exist but lock-in is multi-year. |
| IRDM | Iridium Communications | **MEDIUM** | HIGH | Only truly global LEO L-band MSS constellation with cross-linked 66 satellites and globally allocated L-band spectrum at 1616-1626.5 MHz. |
| BKSY | BlackSky | **LOW** | HIGH | High-revisit sub-meter optical earth-imaging constellation competing in a peer-competitive market with Planet, Maxar, Airbus, and emerging Asian operators. |
| LUNR | Intuitive Machines | **LOW** | HIGH | Commercial Lunar Payload Services (CLPS) lander provider in a peer-competitive NASA program alongside Firefly, Astrobotic, Draper, and others. |
| MNTS | Momentus | **LOW** | MEDIUM | Vigoride orbital transfer vehicle in a competitive in-space transportation market with D-Orbit, Launcher (Vast), Impulse Space, Exolaunch, and Spaceflight. |
| SPIR | Spire Global | **LOW** | HIGH | 100+ satellite RO/AIS/RF data constellation competing with PlanetiQ, GeoOptics, Kleos, HawkEye 360, and Unseenlabs in weather and RF-geolocation data services. |
| VOYG | Voyager Technologies | **LOW** | MEDIUM | Defense and space-station component supplier (signals intelligence, GNC, life-support) leading Starlab commercial LEO station consortium - one of three competing NASA CLD bidders alongside Axiom an… |
| OVZON SS | Ovzon AB | **LOW** | HIGH | Small Ku-band GEO SATCOM-as-a-service operator (one owned satellite Ovzon 3, plus leased Intelsat capacity) with proprietary mobile terminals serving defense/NATO customers in a crowded competitive… |

### Space Components (3 tickers)

| Ticker | Name | Proposed | Confidence | Bottleneck |
|---|---|---|---|---|
| RDW | Redwire Corp | **MEDIUM** | MEDIUM | Sole supplier of Roll-Out Solar Array (ROSA/iROSA) deployable solar wings powering the ISS, Lunar Gateway PPE, and Axiom Station, with 300+ patents and 100% on-orbit success across 1,000+ missions. |
| MOG.A | Moog Inc | **MEDIUM** | HIGH | Market-share leader in flight control servovalves, electrohydraulic servoactuators (EHSAs/EHAs), and launch-vehicle thrust-vector control on military/commercial aircraft and most US launch vehicles… |
| DCO | Ducommun | **LOW** | HIGH | Tier-1 structural assemblies and electronic interconnects for 737/787, A320/A220, F-35, F/A-18, Apache, Black Hawk, and multiple missile platforms (AMRAAM, PAC-3, SM-2/3/6, Tomahawk). |

### Launch (2 tickers)

| Ticker | Name | Proposed | Confidence | Bottleneck |
|---|---|---|---|---|
| AVIO IM | Avio SpA | **MEDIUM** | MEDIUM | Sole European prime for Vega-C small/medium launch and solid-rocket-motor propulsion (P120C boosters shared with Ariane 6), positioning Avio as the only ESA-funded sovereign small-launch and tactic… |
| SPCE | Virgin Galactic Holdings | **LOW** | HIGH | Suborbital space-tourism operator (SpaceShipTwo / Delta-class), not a satellite communications provider; no supply-chain bottleneck role — service is a discretionary consumer experience with multip… |

### Satellite Communications (1 tickers)

| Ticker | Name | Proposed | Confidence | Bottleneck |
|---|---|---|---|---|
| VSAT | Viasat | **LOW** | HIGH | GEO Ka/L-band broadband (combined with Inmarsat) facing aggressive substitution from Starlink LEO and Eutelsat OneWeb across aviation, maritime, and government verticals. |

### Satellite Comms (1 tickers)

| Ticker | Name | Proposed | Confidence | Bottleneck |
|---|---|---|---|---|
| TSAT | Telesat | **LOW** | HIGH | Legacy GEO FSS operator pivoting to Lightspeed LEO constellation; capacity and customer set is substitutable with SES, Intelsat, Eutelsat OneWeb, and Starlink. |

### Ground Systems & Antennas (1 tickers)

| Ticker | Name | Proposed | Confidence | Bottleneck |
|---|---|---|---|---|
| GILT | Gilat Satellite Networks | **MEDIUM** | HIGH | Tier-1 supplier of VSAT ground-segment platforms (SkyEdge IV/II-c) and electronically steered antennas for LEO/multi-orbit networks; Gogo exclusive ESA antenna provider for Galileo business aviatio… |

### Earth Observation (1 tickers)

| Ticker | Name | Proposed | Confidence | Bottleneck |
|---|---|---|---|---|
| SATL | Satellogic | **LOW** | HIGH | Sub-meter optical earth imaging where Satellogic competes directly against Maxar, Airbus, Planet, BlackSky and emerging sovereign constellations - no irreplaceable position. |

## Going-concern flags

- **TSAT** — Telesat: Telesat's existing GEO fleet competes directly with SES, Intelsat, Eutelsat, and ABS in fixed satellite services with no unique bottleneck position. The Lightspeed LEO constellation full-service date 
- **SPCE** — Virgin Galactic Holdings: SPCE is mis-cohorted as satellite communications — it operates a suborbital tourism vehicle with no satcom function. Bottleneck rating is LOW: no supply-chain criticality, tourism is fully substitutab

## Open questions for reviewer

1. **BWXT HIGH** — verifier confirmed despite the DRACO cancellation (May 2025) and FY26 NASA budget zeroing nuclear thermal propulsion. The HIGH rating now rests on NRC Cat-1 HEU licenses + Erwin enrichment buildout + SR-1 Freedom (Mar 2026, Mars 2028 launch) + NSTM-3 mandates. The original rationale text mentions DRACO; should the entry be applied with a refreshed rationale that drops DRACO and leads with SR-1/NSTM-3?
2. **ASTS HIGH** — verifier confirmed FCC SCS authorization (May 2026) for 248-satellite constellation as a structural moat. Apply at HIGH.
3. **UNRATED ATNM & SLC** — registry data-quality issues. ATNM in public records is Actinium Pharmaceuticals (oncology biotech, not space). SLC is Superloop / Spirit Realty Capital depending on registry — neither is satellite. **Recommendation: remove both from Space sector, flag for next registry hygiene pass.**
4. **Going-concern flags** — TSAT (Telesat — competitive pressure flagged as solvency risk) and SPCE (Virgin Galactic — suborbital tourism, mis-cohorted as Satellite Communications). Apply MEDIUM/LOW ratings as proposed but carry the flags forward. SPCE may also warrant a subsector retag (Space Tourism vs Satellite Communications).
5. **Schema fields** — same as Semi/Robotics: `bottleneck_description`, `confidence` on all 25 written entries. Going-concern only on TSAT/SPCE.
