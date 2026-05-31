# Weekly Fundraise Sweep — Search Ruleset Prompt v3.0

## OBJECTIVE
Identify all fundraising announcements (pre-seed through IPO, plus M&A, grants, and government investments) for companies in the following sectors: **Semiconductors, Robotics, Space, Materials, and Cross-Stack** (as defined in the sector taxonomy below). The sweep covers a defined time window (e.g. "March 2026") and outputs a structured spreadsheet.

---

## SECTOR TAXONOMY

### SEMICONDUCTORS
Fabless Design, IDM / Integrated Device Manufacturers, Foundry, OSAT / Packaging & Test, Equipment, EDA & IP, Power & Analog

### ROBOTICS
Industrial Robots, Humanoid & Service Robots, Surgical & Medical Robots, Warehouse & Logistics Automation, Autonomous Systems & Drones, Machine Vision & Sensors, Motion Control & Actuators, Collaborative Robots, Software & Simulation

### SPACE
Launch, Satellite Communications, Earth Observation, In-Orbit Services, Lunar & Planetary, Ground Systems & Antennas, Space Components

### MATERIALS
Silicon & Substrates, Industrial & Specialty Gases, Process Chemicals, Packaging & Substrates, Rare Earths & Critical Minerals, Battery Materials, Structural Materials

### CROSS-STACK
Frontier Compute, Industrial Conglomerates, Test & Measurement

### TOKEN-SPECIFIC (classified under parent sectors)
Agentic Economy, Robotics Infrastructure, Decentralised Compute, Data Infrastructure, DePIN / Physical Infrastructure, Satellite & Connectivity

---

## SEARCH METHODOLOGY

### Step 1 — Tier 1: Wire Services & Aggregators
Run queries against wire services where companies formally announce rounds. These catch ~70% of deals.

**Sources**: Reuters, Bloomberg, PR Newswire, GlobeNewswire, Business Wire, EIN Presswire

**Queries** (adapt date window as needed):
- `[sector] startup funding [month] [year]`
- `[sector] Series A OR Series B OR seed OR IPO [month] [year]`
- `robotics funding round [month] [year]`
- `semiconductor chip startup raise [month] [year]`
- `space startup funding [month] [year]`
- `critical minerals materials startup funding [month] [year]`

### Step 2 — Tier 2: Tech & VC Press
Catch deals with editorial context and some exclusive scoops.

**Sources**: TechCrunch, Fortune, Business Insider, SiliconANGLE, Yahoo Finance, Crunchbase News, PitchBook News, Techstartups.com

**Queries**:
- `site:techcrunch.com [sector] funding [month] [year]`
- `site:news.crunchbase.com biggest funding rounds [month] [year]`
- `"[month] [year]" [sector] raises OR raised OR funding OR round`

### Step 3 — Tier 3: Sector-Specific Sources
Catch niche deals that generalist press misses.

**Semiconductors**: Semiconductor Engineering (quarterly startup funding reports are especially valuable), HPCwire, Data Centre Dynamics, EE Times, Photonics Spectra
**Robotics**: The Robot Report, RoboticsTomorrow, Humanoids Daily, Robotics & Automation News
**Space**: SpaceNews, Spaceflight Now, Satellite Today, Via Satellite
**Materials**: Mining.com, Battery-Tech Network, North American Mining Magazine

**Queries**:
- `site:semiengineering.com startup funding [quarter] [year]`
- `site:spacenews.com funding OR raises [month] [year]`
- `site:therobotreport.com funding OR raises [month] [year]`
- `site:mining.com startup funding critical minerals [month] [year]`

### Step 4 — Tier 4: Regional Sources
Fill geographic blind spots, especially Asia, Europe, LATAM, MENA.

**Europe**: EU-Startups.com, Sifted, Tech Funding News (TFN), DACH startup sources (e.g. startupradio.substack.com)
**Asia**: Tech in Asia, South China Morning Post (tech/business section), 36Kr
**LATAM**: LatamList
**MENA/Africa**: Wamda, Disrupt Africa

**Queries**:
- `European [sector] startup funding [month] [year]`
- `China [sector] startup funding OR IPO [month] [year]`
- `India semiconductor OR robotics funding [month] [year]`
- `Japan OR Korea [sector] funding [month] [year]`

### Step 5 — Tier 5: Crypto / Token-Specific
For DePIN, decentralised compute, and other token-related fundraises.

**Sources**: Cointelegraph, CoinDesk, The Block

**Queries**:
- `DePIN funding [month] [year]`
- `decentralised compute token funding [month] [year]`
- `robotics crypto token raise [month] [year]`

### Step 6 — Tier 6: Databases, Investor Blogs & Ecosystem
Catch early-stage deals and those without press coverage.

**Sources**: Tracxn, Dealroom, Crunchbase (company profiles), Y Combinator companies page, university tech transfer announcements, startup blog posts

**Queries**:
- `site:ycombinator.com/companies [sector] [year]`
- `[university name] spinout funding [sector] [month] [year]`
- `[known investor name] investment [sector] [month] [year]`

### Step 7 — Tier 7: Investor Blog Sweep
VCs announce investments on their own blogs, often with more detail than press releases.

**Key frontier tech investors to check**:

Robotics-focused: Lux Capital, Eclipse Ventures, Playground Global, Coatue, DCVC, Khosla Ventures, Sequoia, Tiger Global
Semiconductor-focused: Intel Capital, Samsung Ventures, Qualcomm Ventures, Applied Ventures, TSMC-affiliated funds
Space-focused: Space Capital, Seraphim Capital, In-Q-Tel, Lockheed Martin Ventures, Boeing HorizonX
Materials-focused: The Engine (MIT), Breakthrough Energy Ventures, DCVC
Generalist with frontier exposure: a16z, Founders Fund, General Catalyst, Accel, Bessemer

**Queries**:
- `site:[investor-domain] investment OR portfolio [sector] [month] [year]`
- `[investor name] blog new investment [month] [year]`
- Check investor portfolio pages for newly added companies

---

## DOUBLE-VERIFICATION PROTOCOL

After the initial sweep produces a draft list, run a SECOND PASS on every entry that is missing ANY of these critical fields:
- Lead Investor(s)
- Amount ($M)
- Location

### Second Pass Procedure:

1. **Search with enriched queries**:
   - `"[Company name]" "[Round stage]" [year] "led by" OR investors OR valuation`
   - `"[Company name]" funding [amount if known] [month] [year]`
   - `"[Company name]" raises OR secures OR closes [year]`

2. **Check these specific sources in order** (higher = more likely to have full detail):
   a. Company's own website / newsroom / blog
   b. Lead investor's blog or portfolio page
   c. LinkedIn posts from the company's CEO/founders
   d. Sector-specific trade press (SpaceNews, The Robot Report, SemiEngineering, Mining.com)
   e. Crunchbase company profile
   f. TechCrunch, Fortune, Bloomberg articles

3. **For each missing field, record**:
   - The enriched value found
   - The source URL where it was found (this may differ from the primary source)
   - If still not found after second pass, mark as "n/d" (not disclosed)

4. **Source URL quality rule**:
   - If the primary source URL is dead (404), a company blog that has been reorganised, or behind a paywall with no useful preview, REPLACE it with the best alternative source found during the second pass
   - Priority order for source URLs:
     1. Original company announcement or press release
     2. Lead investor's blog post about the investment
     3. Sector-specific trade press article
     4. Generalist tech press (TechCrunch, etc.)
     5. Wire service (Reuters, Bloomberg)
   - The source URL must be LIVE and accessible at time of sweep

5. **Validation checkpoint**: After second pass, count entries still missing Lead Investor(s). If >20% of entries are missing this field, the sweep is incomplete — run additional targeted searches.

---

## ROBOTNIK'S NOTES (Column K)

Original intelligence commentary — NOT a restatement of the press release.

### Each note should answer:

1. **What does this company do?** (one sentence, specific)
2. **Who else in the frontier stack is relevant?** Cross-reference against the Robotnik public market universe (347 entities) and other companies in the funding database. Note relationships: competitors, customers, suppliers, ecosystem partners.
3. **What does the round size signal?** Compare to sector and stage norms, prior rounds by the same company, and geographic context.
4. **What should the reader watch for next?** (follow-on round, product launch, partnership, IPO path, regulatory milestone)
5. **Any notable investor context?** (lead investor's track record, strategic investors signalling thesis, co-investment patterns)

### Example of good Robotnik's Notes:

"European heavy kickstage for orbital transfer, enabling last-mile satellite deployment. Operates in the same in-orbit transport segment as Momentus (MNTS) and D-Orbit. €40M seed is 3x the median European space seed in trailing 12M, signalling strong conviction. Backed by [Investor] who also led [related company]'s Series A. Watch for ESA in-orbit servicing contracts and potential Rocket Lab (RKLB) or Firefly (FLY) launch partnerships."

### Example of BAD notes:

"Raised €40M seed round for kickstage development. Plans to scale operations."

---

## CROSS-REFERENCE PROTOCOL

When writing Robotnik's Notes, actively cross-reference each entry against:

1. **Robotnik Public Market Universe**: If related public companies exist in the 347-entity universe, name them with their ticker.

2. **Other Funding Rounds in Database**: Reference prior rounds or related companies that have also raised.

3. **Sector Patterns**: Note if multiple companies in the same subsector raised in the same period.

4. **Investor Patterns**: Note if the lead investor has backed other companies in the database.

---

## OUTPUT FORMAT

### Spreadsheet Columns (in order)
| Col | Field | Notes |
|-----|-------|-------|
| A | Company | Company name only (no parentheticals) |
| B | Sector | One of: Robotics, Semiconductors, Space, Materials, Cross-Stack |
| C | Subsector | From taxonomy above |
| D | Round | Pre-Seed, Seed, Series A, Series B, etc. Use "Series X (extension)" for extensions. IPO, M&A, Grant, Government investment, Debt Financing, Undisclosed. |
| E | Amount ($M) | In USD millions. Convert from local currency. "n/d" if not disclosed. |
| F | Valuation ($M) | Post-money in USD millions. "n/d" if not disclosed (this is normal and expected, especially at early stages). |
| G | Lead Investor(s) | Only investors who led/co-led. "n/d" if not disclosed. |
| H | Other Investor(s) | All other participants. "n/d" if none named. |
| I | Date | DD-MMM-YY format (e.g. "13-Mar-26"). |
| J | Location | "Country (City)". If city unknown, just country. |
| K | Robotnik's Notes | Original intelligence commentary per protocol above. |
| L | Source | Primary source URL. Must be LIVE. |
| M | Month-Year | MMM-YY format (e.g. "Mar-26") |
| N | Quarter | 1Q26, 2Q26, 3Q25, etc. |
| O | Year | YYYY |
| P | Total Raised ($M) | Cumulative total raised by this company to date (including this round). "n/d" if not available. Sourced from Crunchbase, press releases, or company disclosures. |
| Q | Public Market Link | Ticker ONLY if: (a) the company is already publicly listed in the Robotnik universe, or (b) the company is a subsidiary/spinout of a public company in the universe (e.g., a Siemens spinout → "SIE GR"). Blank for most entries (most funded companies are private). |
| R | Related Tickers | Tickers of public companies in the Robotnik universe that are RELEVANT to this fundraise. Relationships include: competitors, customers, suppliers, ecosystem partners, or potential acquirers. Comma-separated. Not limited to competitors. |

### REMOVED COLUMNS (from v2):
- **Verification Status**: Removed. Missing valuation is normal market behaviour, not a data quality failure. If the company, sector, round, amount (or "n/d"), lead investor (or "n/d"), and date are present, the entry is considered complete.

### Formatting Rules
- No section divider rows
- Freeze header row
- Auto-filter enabled on all columns
- Arial font, size 10
- Header row: white text on dark blue (#2F5496)
- Data rows: thin light grey borders, wrap text, top-aligned
- Amount, Valuation, and Total Raised columns: right-aligned, #,##0 number format
- Source column: blue underlined hyperlinks

---

## LIFECYCLE TRANSITION DETECTION (Workstream C)

Beyond logging new rounds, **each monthly sweep must detect and apply lifecycle transitions** for
entities already tracked, per `data/markets/proposed_pre_ipo_transition_policy.md`. The registry key is
the **immutable `entity_id`**; the trading symbol is a `public_ticker` field; `lifecycle_status` ∈
{private, pre_ipo_filed, pre_ipo_priced, public, delisted, acquired, withdrawn}.

### Detection signals + handling
1. **private → pre_ipo_filed** — a *sourced* S-1 / F-1 / confidential-filing confirmation for a tracked
   private entity (or a new frontier private). Set `lifecycle_status=pre_ipo_filed`; store any filing/
   target valuation as **`filing_valuation_m` METADATA with `valuation_source` + `valuation_as_of`** —
   **never** a market cap, never in any index. Assign a provisional bottleneck rating (finalize in D).
2. **pre_ipo_* → public** — the entity's **first trading day** (a ticker begins trading) is the *only*
   index-entry trigger (not the filing, not the pricing). Apply the validated entry process:
   field-update (`lifecycle_status=public`, `public_ticker=<TICKER>`, `type=public`, sector); add the
   ticker to `EQUITIES`; fetch + **validate** price/mcap/history (px × *total* shares scale check — watch
   multi-class float-vs-total, as with CBRS); enter the index via **chain-link (enter-at-first-price,
   day-one return 1.0)**; **re-validate the rating** vs the prospectus (adversarial verifier for
   CRITICAL/HIGH — do not anchor on carryover); run the full re-validation (reconstruction Δ=0,
   reverse-parity ≡, bottleneck self-check, benchmark) and surface the new value/count.
3. **public → delisted / acquired** — a tracked public name ceases trading (going-private/bankruptcy →
   `delisted`; M&A close → `acquired`). Exit the index via the established CA/reorg handling (bankruptcy
   wipeout realizes the loss; reverse-split = flat — the WOLF-class distinction).
4. **withdrawn** — a `pre_ipo_*` entity that pulls/abandons its IPO → `lifecycle_status=withdrawn` →
   revert to `private`.

### Invariants the scan must preserve
- **Entity-linking / dedup:** new entities get a stable slug `entity_id` (the registry key); rounds link
  by `entity_id`. No two `entity_id`s for one company — check new names against the registry before
  adding (the STM/STMPA + York/ALL.SPACE lesson).
- **No-double-count:** a company contributes to the **private** aggregations (RPCI) while private/pre-IPO
  and to the **public** index while public — never both; its historical rounds stay in `rounds.json`. The
  lifecycle-parity guard in `calculate_index.py` blocks publish on violation.
- **Reverse-parity backstop:** once a newly-public frontier name is a non-excluded `public` registry
  entry, the reverse-parity guard **requires** it in the index (flags it missing until entered) — a
  transition cannot be silently dropped (the private-side analogue of the B-sweep's 13-name gap).
- **Anti-fabrication:** valuations are labelled metadata; **never synthesize or interpolate a pre-IPO
  market cap**; genuinely missing data → `null` / documented, never guessed.

### Monthly transition checklist
- [ ] Each tracked `private` entity: new sourced IPO filing? → `pre_ipo_filed` (+ metadata valuation, provisional rating).
- [ ] Each `pre_ipo_*` entity: first trading day yet? → full `public` entry + re-validation; or IPO pulled? → `withdrawn`→`private`.
- [ ] Each `public` name: still trading? → else `delisted`/`acquired` + index exit.
- [ ] A new frontier private in this sweep that has *already* IPO'd? → enter directly as `public` (reverse-parity will flag it).
- [ ] No `entity_id` duplicates introduced; no entity in both the private set and the index.

---

## QUALITY CHECKS
Before finalising:
- [ ] Every entry has a valid, LIVE Source URL
- [ ] Every entry has a Date in DD-MMM-YY format
- [ ] No duplicate companies for the same round
- [ ] Amounts converted to USD where originally in other currencies
- [ ] Lead vs Other investors correctly separated
- [ ] Round types use standardised terminology
- [ ] Location uses "Country (City)" format
- [ ] Robotnik's Notes contain cross-references, not just headline summaries
- [ ] Double-verification completed for entries missing Lead Investor(s)
- [ ] Related Tickers populated where applicable
- [ ] Source URLs tested — no dead links
- [ ] Total Raised populated where data is available
