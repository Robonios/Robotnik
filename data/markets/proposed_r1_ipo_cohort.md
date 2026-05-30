# R1 — Post-2021 IPO Cohort: Include/Exclude Proposal

**Context.** The historical index is a fixed 2021-cohort: it requires a price on
the raw base date (2021-06-01), so 59 eligible names that IPO'd later never enter
the sub-indices. This proposes which to admit (genuine frontier-tech equities)
and which to drop on hygiene grounds (non-frontier / mis-categorized), per the
AGPXX precedent. **Lean: include the genuine ones.** Founder decides per name.

**Current counts:** 282 eligible · **223 actually contributing** to history · 59
excluded (this list). After the lean proposal below (~6 excluded, ~53 admitted):
**~276 eligible · ~276 contributing.**

**Implementation note (matters).** Admitting late IPOs is *not* just relaxing the
base date — done naively, a name entering at "1.0" dilutes a high index level and
creates a fake drop on its entry day. It must be **chain-linked**: each
constituent enters at its first available price (return = 1.0, no jump), and only
its *subsequent* returns count. The reconstruction (`verify_index_reconstruction.py`)
will be updated to the same chain-linked rule and must re-confirm Δ=0.

---

## PROPOSED EXCLUDE — non-frontier industrial / mis-categorized (6)

| Ticker | Name | Sector tag | Why exclude |
|--------|------|-----------|-------------|
| **DVLT** | DataVault AI | Semiconductor | Not a semiconductor — data-monetization/AI software (ex-WISA). Mis-sectored, $0.4B. |
| **SRTA** | Strata Critical Medical | Robotics | Not robotics — critical-care medical supply/infrastructure. Mis-sectored, $0.6B, IPO 2025-08. |
| **RRX** | Regal Rexnord | Robotics | Diversified industrial motors / power transmission. Motion-adjacent, not frontier physical-AI. $13.5B. |
| **JBTM** | JBT Marel | Robotics | Food & beverage processing equipment. Industrial, not frontier robotics. $7.0B. |
| **HIAB FH** | Hiab Oyj | Robotics | Load-handling (truck cranes, forklifts). Traditional industrial. $3.9B. |
| **KALMAR FH** | Kalmar Oyj | Robotics | Cargo/container-handling equipment. Port industrial. $3.1B. |

## BORDERLINE — flag for your call (lean INCLUDE, note the caveat) (5)

| Ticker | Name | Caveat |
|--------|------|--------|
| **OKLO** | Oklo | Frontier, but it's advanced **nuclear (SMR)** mis-tagged as Robotics. Include → **re-sector** (Space/Energy?). $11.8B. |
| **ATS CN** | ATS Corp | Factory-automation **systems integrator** — automation core to thesis, but more SI than product. $3.0B. |
| **2121 HK** | AInnovation | AI **software** solutions, not robotics hardware. $0.3B. |
| **RPI LN** | Raspberry Pi | Edge-compute platform (frontier-adjacent). **mcap reads $0.0B — GBp data bug to fix** before inclusion. |
| **NN** | NextNav | Terrestrial PNT (positioning), not pure space. Frontier positioning infra. $3.0B. |

## PROPOSED INCLUDE — genuine frontier-tech equities (48)

**Semiconductor (7):** ARM ($357B), ALAB Astera Labs ($60B), CRDO Credo ($41B),
RGTI Rigetti/quantum ($9B), NVTS Navitas/GaN ($6.8B), PENG Penguin Solutions
($2.8B), INDI indie Semiconductor ($1.1B)

**Space (18):** RKLB Rocket Lab ($86B), PL Planet Labs ($18B), KRMN Karman
($8.7B), LUNR Intuitive Machines ($7.3B), RDW Redwire ($5.2B), VOYG Voyager
($3.1B), TSAT Telesat ($3.0B), 186A JP Astroscale ($2.4B), BKSY BlackSky
($1.9B), 290A JP Synspective ($1.7B), 464A JP QPS ($1.5B), SATL Satellogic
($1.5B), SPIR Spire ($0.9B), OVZON SS Ovzon ($0.8B), 9348 JP ispace ($0.6B),
SIDU Sidus ($0.4B), MNTS Momentus ($0.2B) — *(NN moved to borderline above)*

**Robotics (20):** SYM Symbotic ($29.5B), 9660 HK Horizon Robotics ($10.6B),
MBLY Mobileye ($8.8B), 688017 Leader Harmonious Drive ($8.5B), 9880 HK UBTECH
($7.1B), AUTO NO AutoStore ($4.8B), 454910 KS Doosan Robotics ($4.4B), 688297 C1
AVIC Chengdu UAS ($4.3B), 2252 HK MicroPort MedBot ($3.3B), HSAI Hesai/lidar
($3.1B), EXA FP Exail ($2.9B), 6600 HK OneRobotics ($2.9B, **thin <6mo history**),
2498 HK RoboSense ($1.8B), 2432 HK Dobot ($1.8B), PRCT PROCEPT BioRobotics
($1.5B), 688165 C1 EFORT ($1.5B), KDK Kodiak AI ($1.3B), SERV Serve Robotics
($0.8B), RR Richtech ($0.7B), 2431 HK MiniEye ($0.5B), 1274 HK iMotion ($0.1B)

**Materials (3):** 6680 HK China Rare Earth Resources ($6.6B, **ticker-slot
reissue — verify Yahoo serves the right entity**), WAF GR Siltronic/wafers
($3.4B), WOLF Wolfspeed/SiC ($3.1B)

---

## Data caveats for admitted names

- **Vendor routing:** most HK/JP names here are `MARKETSTACK_UNSUPPORTED` →
  served by Yahoo. Admitting them requires Yahoo history back to IPO (feasible;
  the override fetcher already handles it).
- **Thin history (<1y):** 6600 HK, KRMN, VOYG, KDK, JBTM (if kept), HIAB/KALMAR
  (if kept), SRTA — recent 2024-25 IPOs contribute little history but enter
  cleanly via chain-linking from their first bar.
- **Entity-resolution to confirm before admit:** 6680 HK (slot reissue),
  RPI LN (mcap data bug).

---

## DECISIONS (founder, this round)

**Inclusion bar (standing rule):** core business = the physical frontier stack
(semis / robotics / space / materials) + direct supply chain. Exclude pure
software (unless frontier-specific like EDA), energy/nuclear (unless deliberate
scope expansion), diversified-industrial-incidental, non-frontier.

**EXCLUDED (9):** DVLT (AI software), SRTA (medical, mis-cat), RRX (diversified
industrial — also a 2021 rename, not an IPO), JBTM (food processing), HIAB FH
(load handling), KALMAR FH (cargo handling), 2121 HK AInnovation (pure AI
software), NN NextNav (terrestrial PNT, not space hardware), OKLO (frontier
energy/nuclear — scope decision, not a cleanup default; admit only via a
deliberate energy-layer expansion with its own sector).

**INCLUDED from contested:** ATS CN (automation integrator), RPI LN (Raspberry
Pi — GBp mcap bug FIXED, now $2.07B, enters with correct weight).

**48-audit exceptions (3) — surfaced for founder call, not blanket-included:**
- **PENG Penguin Solutions** — memory + AI-compute infrastructure/integrator.
  Lean INCLUDE (compute-hardware stack; parallels the ATS integrator call).
- **TSAT Telesat** — satellite-comms OPERATOR (legacy GEO + LEO build). Owns
  space hardware (unlike NN) but is a service/operator. Lean borderline.
- **688297 AVIC Chengdu UAS** — primarily a military fighter-aircraft prime
  (J-10/J-20); UAS/drones are a minority line. Diversified defense-aerospace,
  not frontier-core. Lean EXCLUDE (no clean sector home, à la OKLO).

**Workstream-B flags (pre-2021, out of R1 scope):** IMI plc (diversified
industrial, likely fails bar), Renishaw RSW (broken price feed + borderline).

**Hardening backlog:** R4 per-name plausibility band (mcap/price vs live) to
replace blunt global ceilings (10k load guard, GBp). Non-blocking.
