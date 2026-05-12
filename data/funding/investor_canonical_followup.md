# Investor Canonical Follow-Up Review (v1.1.1 deferred USER-VERIFY rows)

**Date:** 2026-05-12
**Source:** `data/funding/investor_name_map.csv`
**Scope:** 154 USER-VERIFY rows minus 3 already merged in v1.1.1 (`Eclipse → Eclipse Ventures`, `Mayfield Capital → Mayfield Fund`, `Mayfield Fund → Mayfield Fund`) = **151 rows** for review.

Occurrence counts: `variant_occ` is from the CSV; `canonical_occ` is the live count in `data/funding/rounds.json` (lead + co_investors) as of 2026-05-12. Confirmed user policy: **corporate vs venture arm stays distinct globally** (AMD ≠ AMD Ventures, etc.).

## Quick stats

| Bucket | Count | Action |
|---|---|---|
| HIGH | 71 | Fast-approve — clear shorthand/suffix/case variants of same firm |
| MEDIUM | 23 | Sanity-check — likely same firm but plausible reasons to keep distinct |
| LOW | 13 | Ambiguous — investigate before merge |
| REJECT | 44 | Keep distinct per corporate-vs-venture-arm policy or user-flagged distinct |
| **Total** | **151** | |

---

## HIGH confidence — fast approve (71)

Same firm; differs only by spelling/case/suffix/parenthetical, or a known rebrand.

| variant | proposed canonical | variant_occ | canonical_occ | rationale |
|---|---|---|---|---|
| Abstract | Abstract Ventures | 1 | 2 | Brand shorthand |
| ACME | ACME Capital | 1 | 5 | Brand shorthand |
| AE Industrial | AE Industrial Partners | 1 | 2 | Missing suffix |
| Aliya Capital | Aliya Capital Partners | 1 | 2 | Missing suffix |
| Arm | Arm Holdings | 5 | 1 | Brand vs legal entity — canonicalize to brand actually; see MEDIUM if user prefers Arm |
| Ascend | Ascend Capital Partners | 1 | 1 | Shorthand (canonical_occ=1 — see all-rows occ) |
| Balerion Space | Balerion Space Ventures | 3 | 5 | Shorthand |
| Basis Set | Basis Set Ventures | 1 | 1 | Shorthand |
| BDC | BDC Capital | 1 | 2 | Shorthand |
| Bricks Capital | Bricks Capital Management | 1 | 2 | Missing suffix |
| BRV | BRV Capital Management | 1 | 1 | Shorthand |
| Cantos Ventures | Cantos | 1 | 4 | Reverse: shorter form is canonical brand |
| CMB International | CMB International Capital | 1 | 1 | Missing suffix |
| Clal-Tech | Claltech (Blavatnik) | 1 | 1 | Spelling variant |
| ClearVision | Clearvision Ventures | 1 | 1 | Case |
| DST Global Partners | DST Global | 1 | 2 | Strip 'Partners' |
| DYNE | DYNE Ventures | 1 | 1 | Shorthand |
| E14 | E14 Fund | 1 | 2 | Missing suffix |
| Elaia Partners | Elaia | 1 | 5 | Brand shorthand preferred |
| EPIQ Capital Group | Epiq Capital | 1 | 1 | Case + suffix |
| Expansion | Expansion Ventures | 4 | 2 | Shorthand (4 occ); should consolidate |
| Extantia | Extantia Capital | 1 | 1 | Shorthand |
| Faber | Faber Ventures | 1 | 1 | Shorthand |
| Flex | Flex Capital | 1 | 1 | Shorthand |
| French Tech Seed (managed by Bpifrance) | French Tech Seed Fund | 1 | 2 | Strip parenthetical |
| Fuse Venture Capital | FUSE | 2 | 2 | Brand normalization |
| FUSE Ventures | FUSE | 1 | 2 | Brand normalization |
| Gates Frontier Holdings | Gates Frontier | 1 | 4 | Strip 'Holdings' |
| Geodesic | Geodesic Capital | 1 | 1 | Shorthand |
| Glade Brook Capital Partners | Glade Brook Capital | 1 | 2 | Strip 'Partners' |
| Greenoaks | Greenoaks Capital Management | 1 | 1 | Shorthand |
| GV (Google Ventures) | GV | 6 | 1 | Strip disambiguation parenthetical; flip direction — canonical is GV |
| HarbourVest | HarbourVest Partners | 1 | 1 | Missing suffix |
| Heartcore | Heartcore Capital | 2 | 1 | Shorthand |
| Hefei State-owned Investment | Hefei State-Owned Capital | 1 | 1 | Case + suffix |
| Hillhouse | Hillhouse Capital | 1 | 1 | Shorthand |
| Hummingbird | Hummingbird Ventures | 1 | 1 | Shorthand |
| IAG Capital | IAG Capital Partners | 4 | 7 | Missing suffix |
| Ignite Innovation | Ignite Innovation Fund | 2 | 2 | Missing suffix |
| IQT (In-Q-Tel) | In-Q-Tel | 1 | 12 | Strip parenthetical; collapse 'IQT' too |
| IQT | In-Q-Tel | 2 | 12 | Brand shorthand to full name |
| IronGate | Irongate Capital | 1 | 1 | Case + suffix |
| Latitude | Latitude Ventures | 2 | 2 | Shorthand |
| Lingotto | Lingotto Investment Management | 1 | 2 | Shorthand |
| LuminArx Capital | LuminArx Capital Management | 1 | 1 | Missing suffix |
| MaC Ventures | MaC Venture Capital | 1 | 3 | Full firm name |
| Main Sequence Ventures | Main Sequence | 1 | 5 | Brand shorthand preferred |
| MetaVC | MetaVC Partners | 1 | 1 | Missing suffix |
| Mitsui Sumitomo Insurance Capital | Mitsui Sumitomo Insurance Venture Capital | 1 | 1 | Missing 'Venture' word |
| New Legacy | New Legacy Ventures | 1 | 1 | Shorthand |
| Newfund | Newfund Capital | 1 | 1 | Shorthand |
| Notion | Notion Capital | 1 | 1 | Shorthand |
| Nysno Climate Investment | Nysno Climate Investments | 1 | 1 | Plural |
| Omnes | Omnes Capital | 1 | 5 | Shorthand |
| Ondas | Ondas Holdings | 1 | 1 | Suffix |
| Overmatch | Overmatch Ventures | 1 | 2 | Shorthand |
| OVNI | OVNI Capital | 1 | 1 | Shorthand |
| Presidio (Sumitomo) | Presidio Ventures (Sumitomo) | 1 | 3 | Missing 'Ventures' |
| Primo Space Fund | Primo Space | 1 | 1 | Strip 'Fund' |
| Project A | Project A Ventures | 2 | 2 | Shorthand |
| Protagonist | Protagonist Management | 1 | 1 | Shorthand |
| Prysm | Prysm Capital | 1 | 1 | Shorthand |
| Qbic Fund | QBIC | 1 | 1 | Case + strip suffix |
| Raptor | Raptor Group | 1 | 1 | Shorthand |
| Republic | Republic Capital | 1 | 2 | Shorthand |
| SevenX | SevenX Ventures | 1 | 1 | Shorthand |
| SIP Global | SIP Global Partners | 1 | 1 | Missing suffix |
| Snowpoint | Snowpoint Ventures | 1 | 1 | Shorthand |
| Spacecadet | Spacecadet Ventures | 1 | 1 | Shorthand |
| SquareOne | SquareOne Venture Capital | 1 | 1 | Shorthand |
| Taiwania | Taiwania Capital | 1 | 3 | Shorthand |
| Tangent | Tangent Ventures | 1 | 1 | Shorthand |
| Tencent Holdings | Tencent | 1 | 3 | Strip 'Holdings' |
| Tether Holdings | Tether | 1 | 1 | Strip 'Holdings' |
| The Engine | The Engine Ventures | 1 | 2 | Known rebrand |
| The Engine Fund | The Engine Ventures | 1 | 2 | Known rebrand |
| Topology | Topology Ventures | 1 | 1 | Shorthand |
| Translink | Translink Capital | 1 | 2 | Shorthand |
| Tru Arrow | Tru Arrow Partners | 1 | 1 | Shorthand |
| Upfront | Upfront Ventures | 1 | 1 | Shorthand |
| Yamato | Yamato Holdings | 1 | 1 | Shorthand |
| Hyundai Motor Company | Hyundai Motor | 1 | 2 | Strip 'Company'; **keep Hyundai Motor Group distinct** |

## MEDIUM confidence — sanity-check (23)

Likely same firm but the user could plausibly want them distinct. Most are regional fund arms, parent-vs-subsidiary, or near-duplicates that the user previously flagged "different firms possible."

| variant | proposed canonical | variant_occ | canonical_occ | rationale |
|---|---|---|---|---|
| Alibaba | Alibaba Group | 2 | 1 | Brand vs legal entity — Alibaba often = corporate parent |
| Arm | Arm Holdings | 5 | 1 | Brand (Arm) is far more common; canonical direction needs user call |
| Alliance | Alliance Ventures | 2 | 1 | "Alliance" could be Renault-Nissan-Mitsubishi corporate vs the joint VC arm |
| Capricorn | Capricorn Investment Group | 1 | 3 | Capricorn alone ambiguous (also Capricorn Partners exists — different firm) |
| Cathay Capital | Cathay Capital | 2 | 2 | "Cathay Ventures" (1 occ) — possibly separate firm |
| DST Global Partners | DST Global | 1 | 2 | Likely same; some rounds list "Partners" suffix variant |
| Foresight Group | Foresight Ventures | 1 | 3 | UK Foresight Group could be the same firm or its corporate parent |
| Future Capital | Future Capital | 1 | 1 | KEEP DISTINCT from "Future Ventures" (2 occ) — both real firms |
| Hefei State-owned Investment | Hefei State-Owned Capital | 1 | 1 | Possible same Chinese SOE; could also be sibling vehicles |
| Hyundai Motor Company | Hyundai Motor | 1 | 2 | Hyundai Motor Group (3 occ) must stay distinct |
| Kia | Kia Corporation | 1 | 2 | Brand vs legal — same entity, but Kia/Hyundai pair worth a glance |
| Kindred Ventures | Kindred Capital | 1 | 2 | Two firms (US vs UK) — likely KEEP DISTINCT |
| Kolon Group (strategic, South Korea) | Kolon Group | 1 | 0 | Same firm modulo annotation; Kolon Investment (1 occ) is the venture arm — keep distinct from group |
| Macquarie | Macquarie Capital | 2 | 2 | Parent investment bank vs investment arm — likely same but worth checking |
| Mirae Asset | Mirae Asset | 3 | 3 | Group spans Mirae Asset Capital (5) and Mirae Asset Venture Investment (2) — user wants to canonicalize the group |
| Mitsubishi | Mitsubishi Corporation | 1 | 4 | Bare "Mitsubishi" likely Mitsubishi Corp, but could be MUFG/MHI |
| Mizuho Capital | Mizuho | 1 | 2 | Mizuho Capital is a distinct VC arm — likely KEEP DISTINCT |
| NTT | NTT Group | 1 | 2 | Same parent group, low-risk merge |
| NVentures | NVentures (NVIDIA) | 2 | 24 | Same firm; canonical already includes disambiguation |
| POSCO Investment | POSCO Holdings | 1 | 2 | POSCO investment arm vs holding parent — could KEEP DISTINCT |
| Primo Capital | Primo Ventures | 1 | 2 | Possible rebrand or sibling Italian funds |
| Ravelin Capital | Ravelin | 1 | 2 | Same firm probably; verify direction |
| Samsung Venture Investment Corporation | Samsung Ventures | 2 | 7 | Legal name vs brand — same firm |
| SoftBank | SoftBank Group | 5 | 8 | Same parent; bare "SoftBank" sometimes Vision Fund — needs row-level check |

## LOW confidence — investigate (13)

Ambiguous — could be same firm or different entities sharing partial name.

| variant | proposed canonical | variant_occ | canonical_occ | rationale |
|---|---|---|---|---|
| BDC | BDC Capital | 1 | 2 | "BDC" could be BDC Capital (Canadian) or another BDC — verify the round |
| Cathay Capital | Cathay Capital | 2 | 2 | "Cathay Ventures" (1 occ) may be separate firm — check Cathay Capital Group |
| Day One Capital | Day One Capital | 1 | 1 | "Day One Ventures" (1 occ) is separate firm — KEEP DISTINCT |
| FUSE / Fuse Venture Capital / FUSE Ventures cluster | FUSE | 2 / 2 / 1 | 2 | Could be Seattle FUSE vs Polish FUSE Venture Capital — verify per round |
| GAC | GAC Capital | 1 | 3 | "GAC Group" (1 occ) = parent corporate; bare "GAC" ambiguous |
| Linear Venture | Linear Capital | 1 | 2 | Two distinct Chinese VC firms with similar names — likely KEEP DISTINCT |
| Polygon | Polygon Ventures | 1 | 1 | "Polygon" alone could mean Polygon Labs/blockchain — verify |
| Porsche Investments Management | Porsche Ventures | 1 | 3 | May be legacy entity name for same arm; or distinct subsidiary |
| Ridgeline | Ridgeline Partners | 1 | 2 | "Ridgeline" alone could be unrelated firm |
| SAIC | SAIC Ventures | 1 | 1 | SAIC = Shanghai Auto OR US defense contractor — verify per round |
| SCG | SCG Group | 2 | 1 | Siam Cement Group vs other SCG entities |
| Seraphim Capital | Seraphim | 1 | 2 | "Seraphim Space" exists too — verify direction |
| Sparta / Spartan | (separate) | 1 / 1 | 2 / 1 | "Sparta Group" and "Spartan Group" are likely **different firms** — do NOT merge |

## REJECT — keep distinct per policy (44)

Corporate parent vs venture arm — per user policy these stay distinct globally. Listed as variant↔canonical pairs from the CSV.

- Accenture ↔ Accenture Ventures — corporate-vs-venture-arm; keep distinct per policy
- AMD ↔ AMD Ventures — corporate-vs-venture-arm; keep distinct per policy
- Baidu ↔ Baidu Ventures — corporate-vs-venture-arm; keep distinct per policy
- Bain Capital ↔ Bain Capital Ventures — parent firm vs strategy; keep distinct per policy
- Bosch (10%) ↔ Bosch Ventures — corporate-vs-venture-arm; keep distinct per policy
- Bosch Group ↔ Bosch Ventures — corporate-vs-venture-arm; keep distinct per policy
- Capricorn Partners (self-row) — distinct from Capricorn Investment Group; keep distinct per policy
- Cisco ↔ Cisco Investments — corporate-vs-venture-arm; keep distinct per policy
- Equinor ↔ Equinor Ventures — corporate-vs-venture-arm; keep distinct per policy
- Ericsson ↔ Ericsson Ventures — corporate-vs-venture-arm; keep distinct per policy
- GAC Group (self-row) — parent corporate distinct from GAC Capital; keep distinct per policy
- Goldman Sachs (self-row) — user-flagged: keep Goldman Sachs / Asset Management / Growth Equity distinct
- Goldman Sachs Asset Management (self-row) — keep distinct per user instruction
- Goldman Sachs Growth Equity (self-row) — keep distinct per user instruction
- Google ↔ Google Ventures — corporate-vs-venture-arm; keep distinct per policy
- Hanwha Ventures (self-row) — keep distinct from Hanwha corporate per policy
- Honeywell Ventures (self-row) — keep distinct from Honeywell corporate per policy
- Liberty Global Ventures (self-row) — keep distinct from Liberty Global corporate per policy
- Lockheed Martin (self-row) — keep distinct from Lockheed Martin Ventures per policy
- Lockheed Martin Ventures (self-row) — keep distinct from Lockheed Martin corporate per policy
- Matrix Capital Management (self-row) — different firm from Matrix Partners; keep distinct
- Maverick Capital (self-row) — keep distinct from generic "Maverick" per existing flag
- Micron ↔ Micron Ventures — corporate-vs-venture-arm; keep distinct per policy
- Mitsubishi Corporation (self-row) — keep distinct from bare "Mitsubishi"
- Morgan Stanley (self-row) — user-flagged: keep distinct from Morgan Stanley Counterpoint
- Morgan Stanley Counterpoint (self-row) — keep distinct per user instruction
- Mubadala ↔ Mubadala Capital — sovereign vs asset mgmt arm; keep distinct per policy
- Natural Ventures ↔ Natural Capital — likely different firms; keep distinct
- OKX ↔ OKX Ventures — corporate-vs-venture-arm; keep distinct per policy
- Point72 ↔ Point72 Ventures — corporate-vs-venture-arm; keep distinct per policy
- Porsche ↔ Porsche Ventures — corporate-vs-venture-arm; keep distinct per policy
- Prosus ↔ Prosus Ventures — corporate-vs-venture-arm; keep distinct per policy
- Qualcomm ↔ Qualcomm Ventures — corporate-vs-venture-arm; keep distinct per policy
- Salesforce ↔ Salesforce Ventures — corporate-vs-venture-arm; keep distinct per policy
- Stellantis (self-row) — keep distinct from Stellantis Ventures per policy
- Stellantis Ventures (self-row) — keep distinct from Stellantis corporate per policy
- Swisscom ↔ Swisscom Ventures — corporate-vs-venture-arm; keep distinct per policy
- UMC ↔ UMC Capital — parent corporate vs investment arm; keep distinct per policy
- Yamaha Motor ↔ Yamaha Motor Ventures — corporate-vs-venture-arm; keep distinct per policy
- Future Capital (self-row) — keep distinct from Future Ventures (different firms)
- Day One Capital (self-row) — keep distinct from Day One Ventures (different firms)
- Kindred Ventures ↔ Kindred Capital — likely different firms; keep distinct
- Linear Venture ↔ Linear Capital — likely different Chinese VC firms; keep distinct
- Mizuho Capital ↔ Mizuho — corporate-vs-subsidiary venture arm; keep distinct per policy

---

**Next step:** Review HIGH bucket in one pass; expect ~71 merges. MEDIUM and LOW require per-row decisions. REJECT bucket can be batch-marked as resolved in the canonical map (no merge action needed).
