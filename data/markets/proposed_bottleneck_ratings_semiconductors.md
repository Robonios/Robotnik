# Proposed Bottleneck Ratings — Semiconductors Batch (B4 Sector 1)

**Status:** Proposal for review. NOT YET WRITTEN to `enrichment_data.json`.

Existing rated set (25 tickers): 1 CRITICAL · 5 HIGH · 10 MEDIUM · 9 LOW.
This batch (42 tickers): **1 CRITICAL · 0 HIGH · 22 MEDIUM · 19 LOW**.

Calibration check against the existing set:
- CRITICAL is reserved for genuine monopolies. ASML (EUV monopoly) is the only existing entry. The single new CRITICAL proposed below (Lasertec for EUV mask inspection) sits in the same supply-chain bottleneck cluster.
- HIGH was reserved for category dominants where switching is multi-year/multi-billion (NVDA accelerators, TSM N3/N2, ARM ISA, CDNS+SNPS EDA duopoly). None of the 42 unrated names clear that bar without overreaching.
- MEDIUM is concentrated in fab equipment + niche-leader fabless where substitutes exist but require qualification/redesign cycles.
- LOW is the commodity/competitive cohort — broad analog, mainstream RFFE, mature foundry, auto-MCU.

---

## CRITICAL (1)

### 6920 JP — Lasertec Corp ($21.5B, Equipment)

| Field | Value |
|---|---|
| `bottleneck_risk` | **CRITICAL** |
| `bottleneck_description` | Sole commercial supplier of EUV mask blank inspection (MBI) and actinic patterned mask inspection (APMI) tools. EUV reticle manufacturing at advanced nodes cannot be quality-controlled without Lasertec equipment. |
| `key_customers` | TSMC, Samsung Foundry, Intel Foundry, mask shops (Toppan, DNP, Hoya, Photronics) |
| `key_suppliers` | Carl Zeiss SMT (EUV optics for the inspection light path), in-house Japanese subsystem supply chain |
| `rationale` | KLA and Applied Materials do not offer a competing EUV-actinic mask inspection product. ASML and the foundry/IDM ecosystem have publicly acknowledged Lasertec's monopoly position in EUV mask inspection in industry briefings and at ASML's Investor Day. The substitute — DUV-based mask inspection — cannot detect the printable defect modes that emerge under EUV exposure at sub-7nm geometries, so the bottleneck deepens as nodes shrink. Mirrors ASML's EUV-scanner monopoly one tier upstream in the mask-production chain. |
| `confidence` | HIGH |

---

## MEDIUM (22)

### Fabless Design subsector (10)

| Ticker | Name | Bottleneck description | Rationale | Confidence |
|---|---|---|---|---|
| **ALAB** | Astera Labs | Leading position in PCIe Gen5/6 retimers + CXL interconnect for AI server fabric. | Hyperscalers are dual-sourcing across Astera/Marvell/Credo. TSMC dependence on the fab side adds an upstream constraint. Switching cost is real (board-level qualification) but substitutes exist. | MEDIUM |
| **CRDO** | Credo Technology | Active Electrical Cables (AECs) + serdes for AI cluster interconnect. | Direct competition with Marvell, Astera Labs, MACOM. Niche leader but customers have substitution paths. | MEDIUM |
| **MTSI** | MACOM Technology | RF + photonic ICs for telco/datacenter optical + defence. Acquired Wolfspeed RF business 2024. | Defence-relevant content increases switching friction (qualified-part lists). Qorvo, Skyworks, Sumitomo Electric, Broadcom all compete in commercial RF. | MEDIUM |
| **LSCC** | Lattice Semiconductor | Low-power FPGA leader (sub-65nm process nodes). | Owns low-density low-power FPGA niche. AMD (Xilinx) competes upmarket; Microchip in adjacencies. Toolchain lock-in slows but doesn't block substitution. | MEDIUM |
| **SITM** | SiTime | MEMS-based silicon clocks/oscillators displacing legacy quartz. | Dominant in MEMS oscillators (~90% share). Quartz-based suppliers (Epson, NDK, Kyocera) remain technically substitutable in most designs, but the timing-precision advantage of MEMS creates lock-in once specified. | MEDIUM |
| **RMBS** | Rambus | Memory interface IP (DDR5 RDIMM, CXL.mem) + security IP. | Owns several memory-interface patents that are difficult to design around for DDR5/CXL. Synopsys and Cadence offer competing IP for adjacent functions; Rambus's RCD/MRDIMM positioning gives near-term dominance with CXL substitution paths emerging. | MEDIUM |
| **SMTC** | Semtech | LoRa wireless platform near-monopoly + analog mixed-signal. | LoRa owns LPWAN niche, but cellular IoT (NB-IoT, LTE-M) is a credible substitute architecture chosen by carriers globally. Switching cost is moderate (firmware redesign). | MEDIUM |
| **NVTS** | Navitas Semiconductor | GaN power ICs for fast chargers and (emerging) EV/datacenter. | Leader in fast-charger GaN but GaN itself is an emerging power-device category with multiple suppliers (Infineon-acquired GaN Systems, Power Integrations, EPC private, Transphorm, STMicro). SiC remains a substitute at higher voltages. | MEDIUM |
| **LASR** | nLIGHT | High-power fibre lasers + photonic ICs for industrial + defence (directed-energy programs). | Defence procurement (DoD HELSI, OPIR programs) creates qualified-part-list switching friction. Coherent (COHR), IPG Photonics, Trumpf compete in commercial high-power laser. | MEDIUM |
| **PI** | Impinj | RAIN RFID readers + IC tags — structural duopoly with NXP. | The RAIN UHF passive RFID IC market is a long-running duopoly with NXP. Reader infrastructure (encoding, antennas) is tied to ICs, so single-supplier defection at scale (Walmart-tier rollouts) is multi-year. | MEDIUM |

### Equipment subsector (9)

| Ticker | Name | Bottleneck description | Rationale | Confidence |
|---|---|---|---|---|
| **MKSI** | MKS Instruments | Vacuum gauges, gas delivery, motion control, photonics subsystems for fab tools. | Largest pure-play fab subsystem supplier post-Atotech. Many products are mission-critical (vacuum interfaces specifically), but per-segment competitors exist (Brooks, Edwards, Watlow). | MEDIUM |
| **AMKR** | Amkor Technology | Largest US-based OSAT (outsourced assembly + test). | Global OSAT is a 3-4 player market (ASE ~30%, Amkor ~15%, JCET, Powertech). CHIPS Act packaging-incentive build-out adds US-specific bargaining position. | MEDIUM |
| **NVMI** | Nova Ltd | Optical metrology — film-thickness + critical-dimension. | KLA is structurally larger; Onto Innovation is the closest peer. Nova owns OCD metrology niche for several process-control loops; substitutes exist but require recalibration. | MEDIUM |
| **ONTO** | Onto Innovation | Macro defect inspection + lithography metrology + advanced-packaging inspection. | KLA dominates patterned-wafer inspection; Onto leads in macro inspection and advanced-packaging metrology. Substitutes per-application but not blanket. | MEDIUM |
| **AEIS** | Advanced Energy Industries | RF + DC plasma power generators (etch, deposition). | Plasma power is a 3-player market (AEIS, MKS-ENI, Comet). Customers (Lam, AMAT, Tokyo Electron) qualify multiple suppliers but switching mid-program is rare. | MEDIUM |
| **FORM** | FormFactor | Wafer probe cards for advanced DRAM/HBM and leading-edge logic test. | Probe cards are a 3-supplier market (FormFactor, MJC, Technoprobe). FormFactor's HBM probe-card position is leveraged by the AI-memory ramp. | MEDIUM |
| **PLAB** | Photronics | Merchant photomask supplier. | Structurally concentrated market (Photronics + DNP + Toppan + Hoya). Captive mask shops at Samsung/Intel/SMIC reduce merchant TAM but provide no substitution for non-IDM customers. | MEDIUM |
| **CAMT** | Camtek Ltd | Israeli advanced-packaging inspection — bumps, RDL, copper pillars. | Direct competition with Onto Innovation; KLA upstream. Position strengthens with the advanced-packaging build-out (CoWoS, hybrid bonding). | MEDIUM |
| **KLIC** | Kulicke & Soffa | Wire bonders + ball bonders for IC packaging. | Effectively a duopoly with ASMPT for advanced wire-bonding. Wire-bond is a commodity in mature packaging but mission-critical at high pin counts. | MEDIUM |

### IDM subsector (1)

| Ticker | Name | Bottleneck description | Rationale | Confidence |
|---|---|---|---|---|
| **WOLF** | Wolfspeed | Largest US-based 200mm SiC substrate + SiC MOSFET capacity (Mohawk Valley fab). | US national-security-relevant SiC substrate position (CHIPS Act funded), but global SiC market has credible substitutes (Coherent's 200mm rollout, ROHM, Sumitomo, Infineon vertical). **Going-concern risk is real** (Ch.11 watch as of late 2025) — separate from the structural bottleneck question. | MEDIUM |

### Foundry subsector (2)

| Ticker | Name | Bottleneck description | Rationale | Confidence |
|---|---|---|---|---|
| **TSEM** | Tower Semiconductor | Specialty foundry — RF SOI, high-voltage analog, BCD, SiGe. | RF SOI capacity is structurally tight (Tower + GlobalFoundries are the merchant suppliers for smartphone PA chips). Failed Intel acquisition (2022-23) demonstrated the strategic value of this capacity. | MEDIUM |
| **SKYT** | SkyWater Technology | US trusted-foundry (DoD STA-2 approved) for defence + emerging-customer R&D. | Narrow customer base (DoD, R&D startups). GlobalFoundries also holds trusted-foundry credentials; Intel Foundry Services emerging. SkyWater's niche is small but defensible for strategic-supply programs. | MEDIUM |

---

## LOW (19)

### Fabless Design subsector (10)

| Ticker | Name | Rationale (compact) | Confidence |
|---|---|---|---|
| **SWKS** | Skyworks Solutions | RFFE for handset/IoT. Apple ~50% of revenue, but Apple dual-sources with Qorvo + Broadcom + Murata. | HIGH |
| **QRVO** | Qorvo | RFFE peer of Skyworks — same customer concentration, same substitution paths. | HIGH |
| **MXL** | MaxLinear | Mixed-signal broadband + comms. Broadcom, Marvell, MediaTek compete by segment. | HIGH |
| **CRUS** | Cirrus Logic | Audio codecs (Apple-heavy). Realtek, NXP, Knowles substitute. | HIGH |
| **SYNA** | Synaptics | Touch + display + IoT comms. Goodix, FocalTech, MediaTek substitute. | HIGH |
| **SLAB** | Silicon Laboratories | IoT MCU + multi-protocol wireless. Highly competitive (NXP, Nordic, ST, TI, Espressif). | HIGH |
| **AMBA** | Ambarella | Video processing SoCs for ADAS + security cameras. NVIDIA, Mobileye, Qualcomm, Sony substitute. | HIGH |
| **MELE** | Melexis | Hall-effect/magnetic sensors for auto. Allegro (also in batch), Infineon, NXP, TI substitute. | HIGH |
| **INDI** | Indie Semiconductor | Auto sensor interface + mmWave radar. Subscale vs NXP, ST, TI, Renesas, Bosch. | HIGH |
| **NVEC** | NVE Corp | Spintronic (MR) sensors. Niche; TDK, Allegro, Honeywell substitute. Public bottleneck data is thin — confidence flagged. | MEDIUM |

### IDM subsector (3)

| Ticker | Name | Rationale (compact) | Confidence |
|---|---|---|---|
| **6723 JP** | Renesas Electronics | Auto + industrial MCU. Competes head-to-head with NXP, Infineon, ST at the high end. | HIGH |
| **ON** | ON Semiconductor | Power semis + image sensors. SiC + CMOS image sensors are both competitive markets. | HIGH |
| **STM** | STMicroelectronics (ADR has tiny float; parent ~$25B) | Power + MCU + sensors. Competes with NXP, Infineon, Renesas, TI. | HIGH |

### Power & Analog subsector (4)

| Ticker | Name | Rationale (compact) | Confidence |
|---|---|---|---|
| **ALGM** | Allegro MicroSystems | Magnetic sensors + power for auto. Melexis, Infineon, NXP, TI substitute. | HIGH |
| **POWI** | Power Integrations | Offline switcher ICs. Navitas (GaN), TI, Infineon, STMicro substitute. | HIGH |
| **AOSL** | Alpha + Omega Semiconductor | Power MOSFETs + IGBTs. Infineon, ON Semi, ST, TI, Nexperia substitute. | HIGH |
| **DIOD** | Diodes Inc | Discrete + analog. Nexperia, Infineon, ST, TI substitute. | HIGH |

### Foundry subsector (1)

| Ticker | Name | Rationale (compact) | Confidence |
|---|---|---|---|
| **UMC** | United Microelectronics | Mature-node pure-play foundry (28nm+). GlobalFoundries, SMIC, Vanguard, Tower substitute. | HIGH |

### EDA & IP subsector (1)

| Ticker | Name | Rationale (compact) | Confidence |
|---|---|---|---|
| **CEVA** | CEVA Inc | Licensed DSP IP for audio + BT + CV. Arm, Synopsys ARC, Cadence Tensilica substitute. In-house cores at hyperscalers. | HIGH |

---

## Summary table

| Rating | Count | Tickers |
|---|---:|---|
| CRITICAL | 1 | 6920 JP |
| HIGH | 0 | — |
| MEDIUM | 22 | ALAB, CRDO, MTSI, LSCC, SITM, RMBS, SMTC, NVTS, LASR, PI, MKSI, AMKR, NVMI, ONTO, AEIS, FORM, PLAB, CAMT, KLIC, WOLF, TSEM, SKYT |
| LOW | 19 | SWKS, QRVO, MXL, CRUS, SYNA, SLAB, AMBA, MELE, INDI, NVEC, 6723 JP, ON, STM, ALGM, POWI, AOSL, DIOD, UMC, CEVA |
| **Total** | **42** | |

## Resulting Semi-sector rating distribution (rated + this batch = 67)

| Rating | Existing | This batch | Combined | % of 67 |
|---|---:|---:|---:|---:|
| CRITICAL | 1 | 1 | 2 | 3.0% |
| HIGH | 5 | 0 | 5 | 7.5% |
| MEDIUM | 10 | 22 | 32 | 47.8% |
| LOW | 9 | 19 | 28 | 41.8% |

Coverage of total Semiconductors universe (67 of 67 in this batch's scope) would reach **~100%** assuming the registry's Semiconductor sector contains all the named tickers. The few sector-tagged as "Cross-stack" (likely NVIDIA-class names) are already rated and would slot into Semi for sub-index purposes after the existing cross-stack legacy mapping.

## Open questions / reviewer prompts

1. **Lasertec CRITICAL** — defensible? The case rests on EUV-actinic mask inspection monopoly. If you'd prefer the next-most-conservative call, HIGH would be the alternative (treating "actinic inspection has DUV substitutes that work at higher-defect tolerance" as a costly but available fallback).
2. **PI (Impinj) MEDIUM vs LOW** — the RFID duopoly with NXP is structural but the substitute (NXP) is also a credible large supplier. Is "structural 2-player market" enough to justify MEDIUM, or does the existence of a single named substitute push it to LOW?
3. **WOLF MEDIUM with going-concern flag** — should the financial-distress signal be encoded somewhere (separate field, or weight into the rating)? Current proposal keeps it MEDIUM on structural grounds and flags Ch.11 risk in the rationale text only.
4. **STM ADR vs parent** — the ADR has trivially low float. The rating is based on the parent STMicroelectronics. Should the universe carry the ADR with a flag noting the parent-level basis?

---

Once you approve / revise per row, I'll write the approved ratings into `data/markets/enrichment_data.json` following the existing schema (`bottleneck_risk`, `key_customers`, `key_suppliers`, `rationale` — the existing entries don't currently carry `bottleneck_description` or `confidence` fields, so adding these would be a schema extension — please confirm.)
