# Proposed Bottleneck Ratings — Robotics Batch (B4 Sector 2)

**Status:** Proposal for review. NOT YET WRITTEN to `enrichment_data.json`.

Workflow generated 93 ratings across 11 subsectors via parallel subsector agents + adversarial verifier pass on every elevated proposal. **No CRITICAL** proposed for Robotics — calibration with the Semi batch (where ASML and Lasertec are the only two genuine monopolies) holds. **3 HIGH** proposals: Nabtesco (RV reducers), Harmonic Drive (strain-wave gears), and CNRE 600111 (rare-earth feedstock). One verifier-suggested downgrade (Harmonic Drive HIGH → MEDIUM) for your call.

## Headline distribution (93 new entries)

| Rating | Count |
|---|---:|
| HIGH | 3 |
| MEDIUM | 26 |
| LOW | 64 |
| **Total** | **93** |

## Calibration check

Combined with existing 100 rated entities (post-Semi batch):

| Rating | Pre-existing | This batch | Combined | % of 193 |
|---|---:|---:|---:|---:|
| CRITICAL | 3 | 0 | 3 | 1.6% |
| HIGH | 11 | 3 | 14 | 7.3% |
| MEDIUM | 37 | 26 | 63 | 32.6% |
| LOW | 49 | 64 | 113 | 58.5% |

## HIGH proposals — verifier verdicts

### 6324 — Harmonic Drive Systems | Proposed **HIGH** | Verifier: **⚠ DOWNGRADE → MEDIUM**

**Description:** Inventor and dominant supplier of strain-wave (harmonic) gears used in robot wrist/elbow joints and humanoid-robot dexterous joints; standard-class incumbent across global cobot/industrial robot designs.

**Rationale:** Harmonic Drive Systems holds dominant share in high-precision strain-wave gears - the standard small-joint reducer in cobots (UR, FANUC CRX), industrial robot wrists, and humanoid robot designs (Tesla Optimus, Figure 02, Apptronik). Switching to alternatives (Sumitomo, Leaderdrive) requires gear-class re-qualification and the precision class remains the gold standard. HIGH (not CRITICAL) because Chinese alternatives (Leaderdrive especially) have been validated for cost-sensitive applications and the moat is eroding, but global premium share remains highly concentrated.

**Key customers:** FANUC, Yaskawa, Universal Robots, ABB, Tesla, Figure AI, Apptronik, satellite/space programs
**Key suppliers:** Bearing steel mills, precision grinding/honing equipment suppliers, gear-cutting tool suppliers
**Confidence:** HIGH

**Verifier reasoning:** The HIGH rating overstates HDS's bottleneck status given that documented dual-sourcing has already occurred at the highest-profile humanoid programs cited in the rationale: Suzhou Green Harmonic (688017) is now Tesla Optimus's primary harmonic reducer supplier at 30-40% lower price, and Leaderdrive is the sole supplier to Tesla's Mexico factory and validated at Agibot/UBTech. Leaderdrive's humanoid revenue ramped from negligible to 30% of Q1 2025 revenue within quarters, and Jefferies downgraded 6324 to Underperform in 2025 specifically citing competitive erosion in cobots and humanoids — evidence that switching is happening in 1-2 quarters, not multi-year, for the growth segment. HDS retains genuine pricing power in legacy industrial robot/cobot wrist joints where requalification IS multi-year, but the "humanoid gold standard" framing is empirically outdated as of 2026. MEDIUM better captures a dual-sourced incumbent losing primary-supplier status in the highest-growth segment while retaining legacy share.

**Refutation attempts considered:** Substitutes considered: (1) Suzhou Green Harmonic (688017) - now Tesla Optimus primary supplier, 25% Chinese market share, 500k unit/year capacity by 2026, 30-40% price discount. (2) Leaderdrive - 30-40% of Chinese market per JPM, sole supplier to Tesla Mexico, Q1 2025 humanoid revenue at 30% of total, validated at Agibot/UBTech, 40-60% price discount. (3) Zhejiang Laifual, Beijing CTKM, Nidec-Shimpo - additional credible alternatives in the market reports. Dual-sourcing: explicitly confirmed at Tesla Optimus (HDS + Green Harmonic). New entrants: Honpine, BENRUN actively competing. Switching speed: Leaderdrive's revenue growth pattern (47% YoY in 2025, humanoid share jumping to 30% in one quarter) demonstrates that humanoid OEMs are qualifying alternatives in quarters not years. Misclassification: HDS likely belongs in MEDIUM - it's a dual-sourced premium incumbent with eroding share at the marginal growth customer, not a true HIGH bottleneck. The strongest counter-argument for keeping HIGH is that HDS still owns >70% of global premium-class share and Western/Japanese industrial robot OEMs (FANUC, Yaskawa, UR) have not switched - but this is the mature segment, not the growth narrative the rating is anchored on.

### 6268_JP — Nabtesco Corp | Proposed **HIGH** | Verifier: **✓ confirm**

**Description:** Dominant global supplier of RV (cycloidal) reducers used in the base, shoulder, and elbow joints of articulated industrial robots; ~35-60% global share in robot RV reducers.

**Rationale:** Nabtesco RV reducers and Harmonic Drive strain-wave gears together form the de-facto duopoly enabling global industrial robot production. Nabtesco holds 35-60% share in RV reducers with top-3 (Nabtesco/Sumitomo/Spinea) collectively above 80%. RV reducer qualification at robot OEMs spans multi-year validation cycles and the precision class remains hard to match. HIGH (not CRITICAL) reflects credible alternatives (Sumitomo, Spinea, emerging Chinese suppliers like Shuanghuan) but with prohibitive switching cost in premium robot platforms.

**Key customers:** FANUC, Yaskawa, ABB, KUKA, Kawasaki, Mitsubishi Electric, humanoid robot OEMs, Boeing/Airbus (aerospace actuators), railway brake market
**Key suppliers:** Specialty bearing steel suppliers, precision grinding equipment, casting foundries
**Confidence:** HIGH

**Verifier reasoning:** The HIGH rating is well-calibrated. Nabtesco's 35-60% global RV reducer share is verified, and premium industrial robot OEMs (FANUC, Yaskawa, ABB, KUKA) have product lines designed around Nabtesco components with multi-year qualification cycles, supporting prohibitive switching costs. CRITICAL is correctly avoided because Sumitomo (~18% share), Spinea (Slovakia), Wittenstein, and increasingly viable Chinese suppliers (Zhongda Leader, Zhenkang, Shuanghuan — now in Tesla Optimus) represent commercial alternatives, particularly at mid-tier and in humanoid applications. Downgrade to MEDIUM is unwarranted because the premium-tier lock-in at the global big-four robot OEMs persists and dual-sourcing remains concentrated in Chinese domestic production rather than the global premium fleet.

**Refutation attempts considered:** (1) Substitutes overlooked: Wittenstein SE (Germany) and Nidec-Shimpo were not named in rationale but exist as smaller premium alternatives; both are niche and don't undermine HIGH. (2) Chinese new entrants: Zhongda Leader + Zhenkang have crossed 30% of Chinese-assembled robot production by 2025, and Shuanghuan is in Tesla Optimus and Unitree G1 — a real disruption signal, but limited to China domestic OEMs and nascent humanoid, not the global premium fleet. (3) Dual sourcing: Non-Japanese OEMs are actively qualifying Chinese suppliers to reduce supply chain risk, accelerating share erosion at the margin, but qualification cycles remain multi-year. (4) Switching cost test: Sources confirm OEM-supplier relationships are described as "harsh" with exclusivity-style cooperation; premium platforms cannot realistically re-qualify in 1-2 quarters. (5) Misclassification check: Not CRITICAL because Sumitomo at ~18% global share is a credible commercial substitute; not MEDIUM because premium platform lock-in and 80%+ top-3 concentration preserve pricing power and strategic position. HIGH is correctly calibrated.

### 600111 — China Northern Rare Earth (Group) High-Tech | Proposed **HIGH** | Verifier: **✓ confirm**

**Description:** World's largest producer of NdPr oxide from the Bayan Obo deposit, supplying the rare earth feedstock for sintered NdFeB permanent magnets used in every servo motor and robot joint.

**Rationale:** CNRE controls the Bayan Obo complex - the world's largest light rare earth resource - and is the dominant single producer of separated NdPr oxide globally. China collectively produces ~90% of refined rare earth magnet inputs and CNRE is the largest single operator, with its production quotas materially moving global NdPr prices within weeks. Combined with China's October 2024/2025 export controls on rare earths, the supply position is geopolitically gated. HIGH (not CRITICAL) because Mountain Pass (MP Materials), Lynas, and emerging Western processing capacity provide eventual alternative paths, but near-term substitution is highly constrained.

**Key customers:** NdFeB magnet makers (JL Mag, Ningbo Yunsheng, Zhongke Sanhuan, Proterial/Hitachi Metals), downstream EV motor, robotics, and wind turbine supply chains
**Key suppliers:** Baogang Group (parent, Bayan Obo mining), separation chemical suppliers
**Confidence:** HIGH

**Verifier reasoning:** CNRE legitimately deserves HIGH, not CRITICAL or MEDIUM. The bottleneck description correctly scopes the moat to NdPr (light rare earths from Bayan Obo) where CNRE is the dominant single global producer — multiple sources confirm Bayan Obo holds ~37.8% of global REE reserves and is the primary source of global NdPr supply. Commercially viable alternatives exist but are sub-scale: Lynas produces ~7,200 tpa NdPr (10,500 tpa capacity) and MP Materials produced just 1,300 tons in 2024 — combined a small fraction of CNRE's output, ruling out CRITICAL. Switching costs are genuinely multi-year because ferrite substitutes require ~3x larger motors (non-viable for humanoid robot servos at ~2-4 kg NdFeB per unit), Western processing capacity cannot absorb a CNRE shock in 1-2 quarters, and April/October 2025 export controls already caused >90% YoY drops in US magnet imports — confirming the real-world switching cost is years, not quarters.

**Refutation attempts considered:** (1) Ferrite magnet substitution — rejected: requires 3x motor size, incompatible with weight-constrained humanoid robot servos. (2) Lynas as full alternative — partial counter: 10,500 tpa NdPr capacity is the largest non-China plant but still only ~10% of global supply, cannot displace CNRE's volume near-term. (3) MP Materials scaling — rejected as near-term substitute: only 1,300 tons NdPr in 2024, Q2 2025 = 597 tons, magnet production still ramping with DoD support. (4) Misclassification to CRITICAL — rejected: Lynas and MP exist as real, scaling producers, so CNRE is not the sole commercial path. (5) Misclassification to MEDIUM — rejected: China=~90% of NdFeB magnet manufacturing, CNRE is the dominant single NdPr producer, and Oct 2024/2025 export controls demonstrate the bottleneck is geopolitically gated. (6) October 2025 export control suspension until Nov 2026 — does not change the bottleneck because April 2025 controls remain in force and the structural production concentration is unchanged. (7) Heavy rare earth misattribution — checked: bottleneck text correctly cites NdPr (light REE) where CNRE dominates; China Rare Earth Group (separate entity) controls 60-70% of heavy REE, so the description is accurate. (8) Dual-sourcing by customers in 1-2 quarters — rejected: post-April 2025 controls, US magnet imports fell ~90% YoY with no rapid substitution available.

## Full ratings by subsector

### Industrial Robots (27 tickers)

| Ticker | Name | Proposed | Confidence | Bottleneck |
|---|---|---|---|---|
| NDSN | Nordson Corp | **MEDIUM** | MEDIUM | Precision dispensing leader (adhesive, sealant, encapsulant) with strong position in semiconductor underfill/encapsulation tooling. |
| 2395 TT | Advantech Co | **MEDIUM** | MEDIUM | Industrial PC and embedded-board leader (~34-40% share) with high qualification stickiness in long-life industrial deployments. |
| IPGP | IPG Photonics | **MEDIUM** | MEDIUM | Global leader in high-power fiber lasers with vertical integration in pump diodes; structural top-5 oligopoly with TRUMPF, Coherent, nLIGHT, Lumentum. |
| 6134 JP | Fuji Corporation | **MEDIUM** | MEDIUM | Top-3 SMT placement-equipment vendor (with ASMPT and Yamaha) -- structural oligopoly in chip-mounter machines. |
| DUE GR | Duerr AG | **MEDIUM** | MEDIUM | Top-2 global automotive paint-shop / paint-application equipment vendor (~23% share) -- structural oligopoly with high qualification stickiness. |
| 6902 JP | Denso Corp | **LOW** | HIGH | Tier-1 auto components supplier with internal robotics/automation; broad competitive segments rather than a sole-source bottleneck. |
| 002008 C2 | Han's Laser Technology | **LOW** | HIGH | Largest Chinese industrial laser equipment maker (cutting, marking, PCB drilling) competing with Raycus, MaxPhotonics, IPG and TRUMPF. |
| LECO | Lincoln Electric Holdings | **LOW** | HIGH | Largest North American welding equipment/consumables supplier; competes head-to-head with ITW/Miller, ESAB, Kemppi. |
| 300757 C2 | Robotechnik Intelligent | **LOW** | MEDIUM | Chinese automation systems integrator for PV cell, semiconductor and electronics assembly lines. |
| 6506 JP | Yaskawa Electric | **LOW** | HIGH | Big-4 industrial robot manufacturer with strong servo motor/motion control franchise; peer-competitive with Fanuc, ABB, KUKA. |
| G1A GR | GEA Group | **LOW** | HIGH | Diversified food/dairy/beverage/pharma process equipment with strong but contested positions across segments. |
| KCR FH | Konecranes Oyj | **LOW** | HIGH | Industrial overhead crane and port-equipment maker; #3-4 European share, competes with Liebherr, Terex, Cargotec, ZPMC. |
| JBTM | JBT Marel Corp | **LOW** | HIGH | Combined leader in poultry/fish processing equipment post-Marel merger; competes with GEA, BAADER, Buhler, Middleby. |
| 6645 JP | Omron Corp | **LOW** | HIGH | Broad factory automation portfolio (PLC, sensors, switches, vision); peer-competitive vs Siemens, Rockwell, Mitsubishi, Keyence. |
| 6113 JP | Amada Co | **LOW** | HIGH | Top-3 global machine tool/sheet-metal fabrication vendor; competes with TRUMPF, Bystronic, Mazak, Mitsubishi, Chinese entrants. |
| 6845 JP | Azbil Corp | **LOW** | HIGH | Process automation/instrumentation and building automation; mid-tier global player competing with ABB, Emerson, Honeywell, Yokogawa. |
| KRN GR | Krones AG | **LOW** | HIGH | Global market leader in beverage filling/packaging lines; peer-competitive with KHS, Sidel, Sacmi, Tetra Pak. |
| 002747 C2 | Estun Automation | **LOW** | HIGH | Largest domestic Chinese industrial-robot brand (~10% China share) plus vertically integrated servo/controller stack. |
| 300024 C2 | Siasun Robot & Automation | **LOW** | MEDIUM | Chinese Academy of Sciences-spin-off integrator (~6% China share) across industrial, mobile, and cobot lines. |
| ATS CN | ATS Corp | **LOW** | HIGH | Custom automation systems integrator (life sciences, food, EV battery, transportation); peer-competitive with JR Automation, Hahn, Krones, Scott Automation. |
| 6141 JP | DMG Mori Co | **LOW** | HIGH | Top-2 global CNC machining-center vendor (with Yamazaki Mazak); competes with Okuma, Makino, Haas, JTEKT, DN Solutions. |
| 6622 JP | Daihen Corp | **LOW** | MEDIUM | OTC Daihen is a leading arc-welding robot brand with strong Japanese auto OEM footprint; competes with Yaskawa, Panasonic, Fanuc, Nachi, Kuka in welding cells. |
| 688165 C1 | EFORT Intelligent Robot | **LOW** | MEDIUM | Top-5 Chinese industrial robot brand; concentration in PV/3C/auto integration with cross-shop substitutes. |
| 6104 JP | Shibaura Machine Co | **LOW** | MEDIUM | Mid-tier injection-molding and machine-tool maker (ex-Toshiba Machine); competes with Sumitomo Heavy, JSW, ENGEL, KraussMaffei, Sodick. |
| 6258 JP | Hirata Corp | **LOW** | MEDIUM | Custom factory-automation integrator for autos, semiconductors and appliances; 'factory that builds factories' model. |
| 090360 KS | Robostar Co | **LOW** | MEDIUM | LG Electronics' captive robotics supplier (cartesian, SCARA, parallel, glass-transfer); display/electronics handling focus. |
| 388720 KS | Yuil Robotics | **LOW** | LOW | Small Korean robotics vendor offering articulated, collaborative, takeout, humanoid and food/logistics automation. |

### Motion Control & Actuators (15 tickers)

| Ticker | Name | Proposed | Confidence | Bottleneck |
|---|---|---|---|---|
| 6324 | Harmonic Drive Systems | **HIGH** | HIGH | Inventor and dominant supplier of strain-wave (harmonic) gears used in robot wrist/elbow joints and humanoid-robot dexterous joints; standard-class incumbent across global cobot/industrial robot de… |
| 600111 | China Northern Rare Earth (Group) High-Tech | **HIGH** | HIGH | World's largest producer of NdPr oxide from the Bayan Obo deposit, supplying the rare earth feedstock for sintered NdFeB permanent magnets used in every servo motor and robot joint. |
| 002050 | Zhejiang Sanhua Intelligent Controls | **MEDIUM** | HIGH | Qualified Tesla supplier for EV thermal management valves, expansion valves, and electronic pumps; designated for Tesla Optimus actuator joints. |
| 601100 | Jiangsu Hengli Hydraulic | **MEDIUM** | HIGH | World's largest excavator hydraulic cylinder supplier (~30% global share) with growing presence in hydraulic pumps, motors, and valves for construction machinery. |
| MOG/A | Moog Inc Class A | **MEDIUM** | HIGH | Leading flight-control actuation supplier for civil and military aircraft; high-performance servovalves and electromechanical actuators with deep platform incumbency. |
| 688017 | Leader Harmonious Drive Systems | **MEDIUM** | MEDIUM | China's largest harmonic reducer manufacturer with ~26-40% domestic share; primary domestic alternative to Harmonic Drive Systems Japan for robot wrist joints. |
| 2049 | Hiwin Technologies | **MEDIUM** | HIGH | World #3 in ball screws and major supplier of linear guideways; growing position in industrial robots and semiconductor-grade precision motion components. |
| 6594 | Nidec Corp | **LOW** | HIGH | Global #1 brushless DC motor supplier across hard-disk drives, fans, appliances; significant EV traction motor (E-Axle) presence. |
| RRX | Regal Rexnord | **LOW** | HIGH | Roll-up of mid-market power transmission, electric motors, mechanical conveyance, and gearing; serves industrial, HVAC, data-center cooling markets. |
| 002472 | Zhejiang Shuanghuan Driveline | **LOW** | MEDIUM | Leading China automotive gear specialist (passenger vehicle, commercial vehicle, construction machinery) with growing RV reducer presence for industrial robots. |
| 003021 | Shenzhen Zhaowei Machinery | **LOW** | MEDIUM | Largest China integrated micro-transmission/drive system supplier (4th globally); micro motors, planetary gearboxes for consumer electronics, smart-home, and robotics. |
| 603009 | Shanghai Beite Technology | **LOW** | MEDIUM | Automotive chassis components Tier-1 with announced $260M planetary roller screw investment targeting humanoid-robot linear actuators. |
| 300100 | Shuanglin Co | **LOW** | MEDIUM | Auto parts maker (reducers, screws, decorative components) pivoting to planetary roller screws for humanoid robots via Wuxi Kezhixin acquisition. |
| 002979 | China Leadshine Technology | **LOW** | HIGH | Mid-market stepper and servo drive supplier serving Chinese automation, 3D printing, and CNC OEMs; entry-level motion control alternative to Inovance and global servo players. |
| SHA | Schaeffler AG | **LOW** | HIGH | Global bearing and motion technology supplier (FAG, INA brands) serving automotive, industrial, and aerospace; ongoing restructuring after Vitesco merger. |

### Machine Vision & Sensors (11 tickers)

| Ticker | Name | Proposed | Confidence | Bottleneck |
|---|---|---|---|---|
| NOVT | Novanta Inc. | **MEDIUM** | MEDIUM | Precision photonics, optical encoders, motors and servo drives designed-in to medical, surgical-robot and advanced-industrial OEM platforms with long regulatory/qualification cycles. |
| HSAI | Hesai Group | **MEDIUM** | HIGH | Automotive ADAS lidar leader with ~33% overall, 43% long-range ADAS and 61% robotaxi share, but RoboSense, Huawei and Seyond contest the market and Chinese lidar supply is geopolitically gated for … |
| JEN GR | Jenoptik AG | **MEDIUM** | MEDIUM | Specialty optics, microoptics and beam-shaping subsystems co-designed with ASML for DUV/EUV lithography platforms, with a new ~EUR100M Dresden fab doubling micro-optics capacity. |
| 2498 HK | RoboSense Technology | **MEDIUM** | HIGH | World #1 passenger-car lidar by 2024 volume and growing robotics lidar leader (1,458% YoY Q1 2026 robotics growth) in a Chinese-dominated duopoly with Hesai. |
| 098460 KS | Koh Young Technology | **MEDIUM** | MEDIUM | Sole producer of 3D AOI inspection equipment with 52% global SPI share and 30% AOI share, 24,000+ installed base, dominant in 3D Moire SMT inspection. |
| HEXAB SS | Hexagon AB | **LOW** | HIGH | Industrial metrology hardware (CMM, laser trackers, scanners) and software with 12-23% market share, but peer competitive against Zeiss, Mitutoyo, Nikon and Keyence. |
| CGNX | Cognex Corporation | **LOW** | HIGH | Machine vision systems (~11-21% share) sharing the global machine vision market with Keyence, Basler, Teledyne, Omron and SICK in a 5-player 20-30% fragmented oligopoly. |
| 603662 | Keli Sensing Technology | **LOW** | MEDIUM | Strain-gauge load cells and weighing force sensors with #1 China market share for 15 consecutive years, but commodity-tier sensor category with many global alternatives. |
| OUST | Ouster, Inc. | **LOW** | HIGH | Digital flash/spinning lidar for industrial, automotive and robotics, post Velodyne merger; ~$110-150M annualized revenue, sub-scale vs Chinese leaders Hesai and RoboSense. |
| 6914 JP | Optex Group | **LOW** | MEDIUM | Photoelectric, laser displacement and FA sensors plus security PIR sensors, competing with Keyence, Omron, SICK, Panasonic, Banner, Pepperl+Fuchs and Micro-Epsilon. |
| BSL GR | Basler AG | **LOW** | HIGH | World's largest unit-volume producer of digital industrial cameras (area-scan, line-scan, 3D, embedded vision), but heavily dependent on Sony CMOS sensors and competing with Teledyne, IDS, JAI, All… |

### Warehouse & Logistics Automation (7 tickers)

| Ticker | Name | Proposed | Confidence | Bottleneck |
|---|---|---|---|---|
| 6383 JP | Daifuku Co | **MEDIUM** | HIGH | Effective duopolist (with Murata Machinery) in semiconductor AMHS / overhead hoist transport (OHT) and FOUP-stocker systems inside 300mm/sub-3nm fabs, where vendor qualification and cleanroom integ… |
| ZBRA | Zebra Technologies | **LOW** | HIGH | Leading vendor of enterprise barcode scanners, rugged mobile computers and thermal label printers, but in product categories where Honeywell, Datalogic, SATO and Cognex offer functionally equivalen… |
| KGX GR | Kion Group | **LOW** | HIGH | #2 global forklift OEM (after Toyota Industries) and operator of Dematic, one of several top-tier warehouse automation integrators competing with Honeywell Intelligrated, Daifuku, Murata, SSI Schae… |
| AUTO NO | AutoStore Holdings | **LOW** | MEDIUM | Category-creator and leader in cube/grid ASRS with ~1,900 installations and a global integrator channel, but the same retrieval workload can be served by competing ASRS architectures (shuttles, min… |
| HIAB FH | Hiab Oyj | **LOW** | HIGH | Leading on-road load-handling OEM (loader cranes, truck-mounted forklifts, hooklifts, tail lifts), in a fragmented market where Palfinger, Fassi, Tadano, Manitou and Chinese OEMs (XCMG, SANY) compe… |
| KARN SW | Kardex Holding | **LOW** | HIGH | One of the largest vertical lift module (VLM) / vertical carousel vendors with global reach via Kardex Remstar, competing with Modula, SSI Schaefer Logimat, Hänel and System Logistics in a product … |
| INRN SW | Interroll Holding | **LOW** | HIGH | Global market leader in conveyor rollers and drum motors with a broad platform (>60,000 SKUs) sold to system integrators, but in a component category where Van der Graaf, Rulmeca, Damon, Titan and … |

### Software & Simulation (7 tickers)

| Ticker | Name | Proposed | Confidence | Bottleneck |
|---|---|---|---|---|
| 9660 HK | Horizon Robotics | **MEDIUM** | HIGH | Leading Chinese ADAS SoC + software stack supplier with ~21% market share among Chinese OEMs and embedded Tier-1 design wins across BYD, Li Auto, SAIC, VW Carizon JV; switching cost rises with each… |
| RSW LN | Renishaw PLC | **MEDIUM** | MEDIUM | World leader in machine-tool touch probes, CMM probes, optical/wireless transmission probes, and laser/encoder calibration; effective duopoly with Hexagon plus specialized peers (Heidenhain, Zeiss,… |
| KDK | Kodiak AI | **LOW** | HIGH | AI self-driving software stack (Kodiak Driver) for Class-8 trucks and military AGV applications; competitive autonomy-software market with multiple credible peers. |
| 2431 HK | MiniEye Technology | **LOW** | MEDIUM | Mid-tier Chinese L2/L2+ ADAS domain-controller and DMS supplier; competitive design-win basis, partially backed by Horizon Robotics shareholding. |
| 2121 HK | AInnovation Technology | **LOW** | HIGH | Enterprise AI software vendor (machine vision ManuVision, edge video MatrixVision, ML platform Orion) for Chinese manufacturing, finance, retail; commodity AI-solutions market. |
| IMI LN | IMI PLC | **LOW** | HIGH | Diversified fluid- and motion-control engineering group (valves, actuators, controls, pneumatic/electric motion systems) across process automation, industrial automation, life science, climate, tra… |
| RPI LN | Raspberry Pi Holdings | **LOW** | HIGH | Low-cost single-board computer and RP2 microcontroller silicon for education, hobbyist, and OEM/IoT/industrial customers; structurally competitive SBC market. |

### Humanoid & Service Robots (7 tickers)

| Ticker | Name | Proposed | Confidence | Bottleneck |
|---|---|---|---|---|
| 9880 HK | UBTECH Robotics | **LOW** | HIGH | One of several Chinese humanoid OEMs (Walker S series) competing with Unitree, Xpeng, Fourier, Agibot domestically and Tesla/Figure/Apptronik globally; no sole-source role in any downstream OEM sup… |
| 688169 C1 | Beijing Roborock Technology | **LOW** | HIGH | Global #1 in robot vacuum unit share (~19-23%) but operating in a structurally contested consumer-appliance category with at least five well-funded peers; not a critical-input bottleneck for any do… |
| 6600 HK | OneRobotics Shenzhen | **LOW** | HIGH | Smart-home / consumer SwitchBot brand with a nascent humanoid (Onero H1) launched Q1 2026; competes with Roborock, Ecovacs, Dreame in consumer robotics — no critical-input role. |
| RR | Richtech Robotics | **LOW** | HIGH | Small US service-robot integrator (ADAM coffee robot, Scorpion bartender, Titan delivery) with NVIDIA-based control stack; deployments are individually substitutable, no sole-source role. |
| 455900 KS | Angel Robotics | **LOW** | HIGH | KAIST-spinout medical exoskeleton maker (WalkON Suit, Angel Suit, Angel Legs) targeting paraplegia rehab; competes with Ekso Bionics, ReWalk, Cyberdyne, Wandercraft, Suit-X. |
| 277810 KS | Rainbow Robotics | **LOW** | HIGH | KAIST HUBO spinout, now 35%-owned by Samsung, with RB Series cobots and HUBO humanoid platform; competes with UR, Doosan, Techman, Fanuc CRX, ABB GoFa in cobots and with global humanoid pure-plays. |
| 108490 KS | Robotis Co | **LOW** | HIGH | Maker of Dynamixel all-in-one smart servo actuators widely used in research and education robots; competes with Maxon, Faulhaber, U2D2/Cubemars/Dephy in smart-servo categories. |

### Autonomous Systems & Drones (6 tickers)

| Ticker | Name | Proposed | Confidence | Bottleneck |
|---|---|---|---|---|
| AVAV | AeroVironment | **MEDIUM** | HIGH | Dominant US-domestic supplier of Switchblade loitering munitions and tactical small UAS to US Army/DoD, with battle-tested program-of-record status that creates real qualification switching friction. |
| MBLY | Mobileye Global | **MEDIUM** | HIGH | Dominant ADAS vision SoC supplier with EyeQ family deployed in ~230M vehicles across ~1,200 vehicle models and >95% win rate at top OEM customers, creating multi-year automotive qualification switc… |
| 688297 C1 | AVIC Chengdu UAS | **MEDIUM** | MEDIUM | Sole publicly listed Chinese state-backed MALE military UAV prime contractor, producing the Wing Loong family (the primary Chinese export competitor to MQ-9 Reaper) with structural domestic monopol… |
| EXA FP | Exail Technologies | **MEDIUM** | HIGH | Top-tier global supplier of fiber-optic gyroscope inertial navigation systems, with vertically integrated FOG manufacturing and trusted-by-70-navies status creating multi-year qualification switchi… |
| EH | EHang Holdings | **MEDIUM** | MEDIUM | First and only eVTOL manufacturer worldwide to hold all four Chinese CAAC certificates (Type, Airworthiness, Production, Operational) for autonomous passenger air taxi, conferring a 12-24 month reg… |
| SERV | Serve Robotics | **LOW** | HIGH | Largest US sidewalk delivery robot fleet (~2,000 units) with anchor Uber Eats partnership, operating in a contested last-mile autonomous delivery market with multiple peer alternatives. |

### Unknown (5 tickers)

| Ticker | Name | Proposed | Confidence | Bottleneck |
|---|---|---|---|---|
| 6268_JP | Nabtesco Corp | **HIGH** | HIGH | Dominant global supplier of RV (cycloidal) reducers used in the base, shoulder, and elbow joints of articulated industrial robots; ~35-60% global share in robot RV reducers. |
| 300124_C2 | Shenzhen Inovance Technology | **MEDIUM** | HIGH | Dominant China servo drive + low-voltage VFD supplier with ~40% domestic servo share; deep penetration into robot joint motors and industrial automation. |
| 6273_JP | SMC Corp | **MEDIUM** | HIGH | Global #1 pneumatic automation supplier (~30% global share) of solenoid valves, cylinders, and air treatment equipment for factory automation. |
| 6481_JP | THK Co | **MEDIUM** | HIGH | World #1 linear motion (LM) guide and ball screw supplier; precision class deeply qualified into semiconductor lithography, machine tool, and high-precision robotics. |
| 1590_TT | Airtac International | **LOW** | HIGH | #2 pneumatic component supplier in China (~30% share) producing cylinders, valves, and FRLs; positioned as cost-disruptive alternative to SMC/Festo. |

### Surgical & Medical (4 tickers)

| Ticker | Name | Proposed | Confidence | Bottleneck |
|---|---|---|---|---|
| GMED | Globus Medical | **LOW** | HIGH | #2 spine surgical robotics platform (ExcelsiusGPS) in a clearly contested 4-5 player market against Medtronic Mazor, J&J VELYS, Stryker Mako Spine, and Zimmer Rosa Spine. |
| 2252 HK | Shanghai MicroPort MedBot | **LOW** | HIGH | Chinese domestic challenger to Intuitive Surgical's da Vinci with its Toumai laparoscopic robot; only ~100 cumulative global orders as of late 2025 against a market overwhelmingly served by Intuitive. |
| TECN SW | Tecan Group | **LOW** | HIGH | Lab automation/liquid handling vendor competing directly with Hamilton, Beckman Coulter, Thermo Fisher, Agilent, Eppendorf, and Revvity across the lab automation stack. |
| PRCT | PROCEPT BioRobotics | **LOW** | HIGH | AquaBeam/HYDROS Aquablation is the only robotic heat-free waterjet BPH therapy, but the broader BPH treatment market has many established alternatives (TURP, HoLEP, Rezum, UroLift, TULSA-PRO). |

### Collaborative Robots (2 tickers)

| Ticker | Name | Proposed | Confidence | Bottleneck |
|---|---|---|---|---|
| 454910 KS | Doosan Robotics | **LOW** | HIGH | Heavy-payload (20kg+) collaborative robot arms - a niche where Doosan leads but where Universal Robots (UR20), FANUC (CRX-25iA) and ABB now offer direct substitutes. |
| 2432 HK | Shenzhen Dobot Corp | **LOW** | HIGH | General-purpose collaborative robots (3-20kg payload) and best-selling MG400 desktop robot - a contested space with multiple Chinese (AUBO, JAKA) and global (UR, FANUC, ABB) substitutes. |

### Test & Measurement (1 tickers)

| Ticker | Name | Proposed | Confidence | Bottleneck |
|---|---|---|---|---|
| 6841 JP | Yokogawa Electric | **LOW** | HIGH | Process automation, DCS, field instruments, and test/measurement equipment supplier competing in well-populated oligopolistic markets with multiple credible global alternatives. |

### Warehouse & Logistics (1 tickers)

| Ticker | Name | Proposed | Confidence | Bottleneck |
|---|---|---|---|---|
| KALMAR FH | Kalmar Oyj | **LOW** | HIGH | Container/cargo handling equipment maker (terminal tractors, reach stackers, straddle carriers, empty container handlers) in a moderately concentrated but peer-competitive port equipment market. |

## Flagged entries (going-concern / parent-basis)

- **688297 C1** — AVIC Chengdu UAS: going_concern=None, parent_basis_note=Listed entity is the AVIC Group's Chengdu UAV subsidiary; rating reflects this subsidiary's specific MALE UAV franchise, not the broader AVIC conglomerate.

## MarketStack symbology probes — findings

### marketstack_german_equity_symbology

**Recommendation:** Use the .XFRA suffix (Frankfurt Stock Exchange MIC) on the V1 /eod endpoint for all German equities. All 5 test symbols (SIE, BAS, IFX, JEN, KGX) returned valid OHLC data with .XFRA, dated 2026-05-22. This is the only suffix that works consistently for German equities on MarketStack V1. Replace any .XETR mappings with .XFRA in the ticker map (data/mappings/ or wherever the MarketStack adapter resolves German tickers). Do NOT use .DE — although V1 redirects to V2, the V2 endpoint returns close=null even when it accepts the symbol, making it unusable for price tracking. Do NOT use bare symbols, .XETR, or .ETR — all rejected as invalid. Note the data freshness gap: .XFRA returned 2026-05-22 (Friday) while .DE on V2 returned 2026-05-28 (Thursday) — V1/XFRA may lag a few business days vs V2, but trades off currency for usable close prices.

**Open questions:** 1) Why does V2 return close=null for .DE symbols on the most recent date? Could be a free-tier restriction (V2 may gate intraday/recent EOD behind a higher plan) or a data-feed lag where the most recent day hasn't settled. Worth testing with `date_from`/`date_to` to fetch older dates on V2 .DE to see if historical closes populate. 2) The .XFRA data is several business days stale (2026-05-22 returned on 2026-05-29). Is this typical lag, weekend bunching, or a plan-tier limitation? Worth a follow-up probe on a US symbol (e.g. AAPL) to baseline freshness expectations. 3) XFRA is Frankfurt Stock Exchange (the broader Börse Frankfurt floor), while XETR is the Xetra electronic system — XFRA prices may have lower liquidity than XETR. If liquidity/accuracy matters more than freshness, this is a tradeoff to flag, but for index calculation the XFRA close is acceptable. 4) Did not test other German equities outside the 5 requested (e.g. SAP, ALV, DTE) — recommend a sweep across the full DE universe before cutover to confirm .XFRA coverage is universal.

### marketstack-tokyo-symbology

**Recommendation:** The failure is per-format, not per-ticker. Two independent issues stacked on each other:

1) ENDPOINT: V1 returns 'data not available, try V2' for ALL Tokyo tickers regardless of suffix. Use V2 (/v2/eod) for Tokyo coverage.
2) SUFFIX: On V2, the .XTKS (MIC) suffix is rejected for Tokyo tickers, but .T (Yahoo/EODHD-style) works and returns clean data with exchange='XJPX' echoed back. Bare numeric symbols are rejected on both endpoints.

Recommended symbology for Japanese equities: `<4-digit-code>.T` (e.g., 6594.T, 6857.T, 8035.T) queried against `https://api.marketstack.com/v2/eod`.

Concrete code changes in /Users/robertosborne-ov/Projects/Robotnik/scripts/marketstack_client.py:
  - Line 46: flip `API_VERSION = 'v1'` to `'v2'` (the comment already anticipated this migration as 'one constant change').
  - Line 74 / the COUNTRY_TO_MIC map: for Japan, switch the suffix-builder from 'XTKS' to 'T'. This is a Yahoo/EODHD-style ticker suffix, NOT a MIC, so it deserves a comment noting the inconsistency (MarketStack accepts MICs for other exchanges like XKRX/XAMS but uses Yahoo-style .T specifically for Tokyo).
  - Re-run scripts/marketstack_coverage_test.py after the change to confirm Tokyo tickers now resolve and that no previously-working exchanges regress on V2.

The V1 deprecation note from MarketStack is also a forcing function — even non-Tokyo coverage will eventually need V2, so this migration should not be Japan-only.

**Open questions:** - Does the .T-vs-.XTKS quirk apply to other exchanges, or just Tokyo? Korean (XKRX), Taiwan (XTAI), Hong Kong (XHKG) tickers were not retested on V2 in this probe — they may also need Yahoo-style suffixes (.KS, .TW, .HK) instead of MIC suffixes. Worth a systematic V2 sweep of the COUNTRY_TO_MIC map in marketstack_client.py.
- Are there any V1 endpoints (splits, dividends, tickers metadata) the current client depends on that don't have a V2 equivalent? The pure /eod migration is clean, but other endpoints weren't probed.
- The 'exchange' field in V2 responses returns 'XJPX' (JPX holding-company MIC) rather than 'XTKS' (Tokyo Stock Exchange MIC). If downstream code filters/joins on exchange code, the JPX→TSE mapping may need handling.
- V2 response sets `exchange_code`, `asset_type`, `price_currency` to null — if the existing pipeline reads any of those fields, they may need a fallback or to be derived from the symbol suffix."

### marketstack-index-symbology-2026-05-29

**Recommendation:** Use MarketStack's `.INDX` suffix convention for index symbols. Confirmed working symbols:

- NASDAQ Composite: `IXIC.INDX` (current, 2026-05-22 close 26,343.97)
- S&P 500: `GSPC.INDX` (current, 2026-05-22 close 7,473.47)
- MSCI World: NO live index symbol available. Recommended fallback: `URTH` (iShares MSCI World ETF, NYSE Arca, current to 2026-05-28). The nominally-correct index symbol `990100.INDX` exists in MarketStack's INDX exchange directory ('MSCI International World Index Price', USD) but its most recent EOD bar is 2022-11-18 — the underlying series is not being maintained. If broader 'all-country' exposure (incl. EM) is acceptable, `ACWI` is also live (2026-05-28).

Key rejected patterns to avoid: bare tickers (IXIC, GSPC), Yahoo carets (^IXIC, ^GSPC), Reuters dot-prefix (.GSPC), CBOE SPX, Bloomberg MXWO, and Google INX. MarketStack rejects all of these with `no_valid_symbols_provided`.

Note on lag: spot index series (e.g. GSPC.INDX) appears to trail by ~3 trading days relative to ETF symbols (e.g. SPY, URTH ran through 2026-05-28 while GSPC.INDX stopped at 2026-05-22). If recency matters more than purity, prefer the ETF proxies. If index purity matters more, accept the lag.

Discovery tip for future symbology questions: the endpoint `https://api.marketstack.com/v1/exchanges/INDX/tickers?search=<query>` returns the full INDX index catalog and is the fastest way to find MarketStack's exact symbol for any index by name.

**Open questions:** 1) Can MarketStack's MSCI World series (990100.INDX) be refreshed by upgrading the subscription tier? It is listed with has_eod=true but data stops in Nov 2022 — unclear whether this is a tier-restriction artifact or a permanent data-vendor gap on MarketStack. Worth a support-ticket follow-up if MSCI World index purity (not ETF proxy) is required.

2) Is the ~3 trading-day lag on US index series (GSPC.INDX, IXIC.INDX, DJI.INDX all stop at 2026-05-22 while ETFs run to 2026-05-28) a persistent SLA characteristic of MarketStack's index feed or a transient delay? If persistent, this affects daily index calculation freshness vs an ETF-based approach.

3) MarketStack lists `MSCIALL.INDX` (MSCI All-Country World Equity Index, has_eod=true) in its INDX directory — not probed for live data. If MSCI ACWI is the desired benchmark instead of MSCI World, this symbol should be probed before defaulting to the ACWI ETF.

4) MarketStack also exposes `SP500NTR.INDX` (S&P 500 net total return) and `US500.INDX` (S&P 500 Futures) — both has_eod=true. Worth probing if total-return or futures-based S&P 500 exposure is preferred over the price-return GSPC.INDX.

## Open questions for reviewer

1. **6324 (Harmonic Drive) verifier-flagged downgrade HIGH → MEDIUM.** The verifier found dual-sourcing has materially occurred at Tesla Optimus (Suzhou Green Harmonic 688017 now primary supplier at 30–40% discount, Leaderdrive humanoid revenue went from negligible to 30% of Q1 2025 revenue, Jefferies downgraded to Underperform). Accept downgrade or override?
2. **MarketStack production adapter direction.** Three independent findings:
   - German: flip `.XETR` → `.XFRA` (V1 endpoint)
   - Japan: flip API_VERSION v1→v2 AND `.XTKS` → `.T` suffix
   - Indices: use `.INDX` suffix (IXIC.INDX, GSPC.INDX both confirmed)
   The Japan finding is the major architectural change — V2 endpoint for Tokyo. Does the adapter migrate to V2 entirely (all endpoints) or selectively (V2 only when V1 fails)?
3. **CNRE 600111 HIGH for rare-earth feedstock.** Defensible? Confirmed by verifier on Bayan Obo dominance + Apr/Oct 2025 export controls. The ticker maps the upstream Materials sector into the Robotics rating set — should this rating live in `enrichment_data.json` under the Robotics batch, or under Materials when we get there?
4. **Schema fields.** Same as Semi: `bottleneck_description`, `confidence` on all 93. Going-concern / parent-basis only when applicable.
