# Monthly Funding Ingestion — Agent Prompt Template

**Locked at:** v1.0 (2026-05-06)
**Use for:** all monthly ingestion runs (first Sunday of each month) and any backfill / supplemental passes.

This template encodes the schema, classification, and **anti-fabrication** rules that emerged from the v1.0 backfill experience. Copy verbatim into each research agent's prompt; only swap the `## Window` block.

---

## Window

You are researching private-markets funding deals in **{SECTOR}** for **{WINDOW}** (e.g. "May 1 – May 31, 2026"). Aim for comprehensive coverage of {SECTOR_MIN}M+ rounds.

---

## Sectors and subsectors

The Robotnik universe has 5 sectors, 27 subsectors. Pick exactly one subsector per row.

- **Robotics:** Humanoid & Service Robots, Industrial Robots, Warehouse & Logistics, Surgical & Medical, Autonomous Systems & Drones, Software & Simulation, Motion Control & Actuators, Machine Vision & Sensors, Collaborative Robots
- **Semiconductors:** Fabless Design, Foundry, Frontier Compute, EDA & IP, Equipment, Power & Analog, Silicon & Substrates, OSAT / Packaging & Test
- **Space:** Launch, Satellite Communications, Earth Observation, In-Orbit Services, Space Components, Ground Systems & Antennas
- **Materials:** Battery Materials, Rare Earths & Critical Minerals, Structural Materials
- **Token:** Decentralized AI / DePIN, Frontier Compute (only if the token is genuinely a compute infrastructure play)

⚠️ Cross-stack/AI-for-robotics → **Software & Simulation** subsector unless their primary product is a robot platform. Silicon photonics startups → **Frontier Compute** (no separate "Photonics & Optical" subsector exists).

---

## Round enum (canonical values)

```
Bridge, Debt Financing, Government, Government investment, Grant,
IPO, IPO (filed), M&A, Other, Pre-IPO, Pre-Seed, Pre-Series A,
Pre-Series B, Pre-Series C, Seed, Seed (extension),
Series A, Series A (extension),
Series B, Series B2, Series B (extension), Series B Extension,
Series C, Series C (extension),
Series D, Series D (extension),
Series E, Series E (extension), Series E+,
Series F, Series F (extension),
Series G, Series G (extension),
Series H, Series H (extension), Strategic, Undisclosed.
```

**AVOID `Other` as a round value.** Use the closest canonical match (Bridge, Strategic, Debt Financing, Government investment, etc.). If you would otherwise label a round "Other", reconsider whether it's actually a Strategic placement, a Bridge, or a Debt Financing.

Mappings to apply mechanically:
- `Series C-2`, `Series C+`, `Series C (third tranche)` → `Series C (extension)`
- `Series D-1 (extension)`, `Series D-2` → `Series D (extension)`
- `Pre-IPO tranche` → `Pre-IPO`

---

## Schema

Each row must have these fields exactly:

```json
{
  "company": "str",
  "sector": "Robotics | Semiconductors | Space | Materials | Token",
  "subsector": "<one of 27 canonical>",
  "round": "<one of 35 canonical>",
  "amount_m": <float | null>,         // USD millions
  "valuation_m": <float | null>,       // USD millions, post-money preferred
  "lead_investors": "Lead 1, Lead 2",  // null if undisclosed
  "other_investors": "Co 1, Co 2",     // empty string "" if none
  "date": "YYYY-MM-DD",
  "location": "Country (City, ST/Region)",   // use "USA" not "United States"
  "robotnik_notes": "<1-2 sentences, analytical voice>",
  "source": "<canonical URL — verified via HEAD/GET>",
  "source_status": "verified",         // always 'verified' for new rows; if no source found, use 'pending'
  "single_source": <bool>,
  "subsector_uncertain": <bool>,
  "stage_uncertain": <bool>,
  "native_currency": "USD" | "EUR" | "CNY" | "JPY" | "KRW" | etc.,
  "native_amount": <float | null>,
  "fx_source": "<e.g. ECB reference 2026-04-15>",
  "fx_rate_used": <float | null>       // units of native per 1 USD
}
```

For Token sector, also include `_token_classification`: `"true_token_deal"` or `"equity_in_crypto_co"`.

---

## 🚫 ANTI-FABRICATION RULES — MANDATORY

These rules emerged from the v1.0 source URL audit which found ~12% of source URLs were agent-fabricated patterns that never resolved. **Violations will be rejected at review.**

### Rule 1 — URL verification mandatory

Every URL written to the dataset MUST be HEAD-requested (or WebFetch'd) and confirmed to return 200 / 301 / 302 before being recorded. Process:

1. Find a candidate URL via web search.
2. Verify it loads (WebFetch returns content; not 404 / DNS failure / timeout).
3. Only then write it to the row.

If verification fails, the URL must NOT be used. Try the next candidate or fall through to Rule 4.

### Rule 2 — Prefer canonical company press release pages

When a deal is announced, the company's own press release page is the preferred primary citation:

- ✓ `https://shield.ai/shield-ai-to-acquire-software-simulation-company-aechelon-and-raise-2b-at-12-7b-valuation/`
- ✓ `https://www.nscale.com/press-releases/nscale-series-c`
- ✓ `https://www.helionenergy.com/articles/helion-announces-425m-series-f-investment-to-scale-commercialized-fusion-power/`

These are **stable** and rarely 404. Use publication URLs (TechCrunch, Bloomberg, Reuters, Sifted, etc.) as **fallback**, not first-line.

Aggregators (PRNewswire, BusinessWire, GlobeNewswire) — use only when no company-own URL exists. These often 404 within a year.

### Rule 3 — Verbatim URLs only — NO SYNTHESIS FROM PATTERNS

Cite URLs that come **verbatim** from search results or directly retrieved pages.

🚫 **BANNED:** Constructing URLs by inferring patterns. Examples of fabrication that audit caught:

- `techcrunch.com/2025/11/14/zipline-raises-800m` — agent guessed slug from amount
- `nscale.com/news/series-c` — agent guessed canonical path; actual is `/press-releases/...`
- `prnewswire.com/news-releases/galbot-secures-over-300-million-302647204.html` — agent truncated the slug; actual ends `...sector-302647204.html`
- `therobotreport.com/neura-robotics-1-2b-funding/` — agent guessed slug

If the agent has not actually visited the page (verified via WebFetch), it cannot cite the URL. **No exceptions.**

### Rule 4 — `source_status: pending` instead of fabrication

If no verifiable URL is found for a deal:

- Set `source_status: "pending"`
- Leave `source` as `null` or as the best unverified candidate (with a clear `notes` field)
- Surface in the run summary for manual review

**Better to flag a missing source than fabricate one.** A pending row gets manually triaged before going to VCs; a fabricated URL embarrasses the platform.

### Rule 5 — Date verification

The `date` field MUST match the canonical announcement date stated by the cited primary source. Specifically:

- If the source says "today" or "this week" with a publication date, the publication date IS the announcement date.
- Don't infer dates from secondary references ("as reported earlier in March...", "previously announced...") — those are stale.
- Don't synthesize dates from URL slugs or search-result snippets without verifying against article body.
- For multi-tranche / multi-close rounds, use the date of the SPECIFIC close being recorded, not the cumulative-disclosure date.

🚫 **BANNED:** Recording an event at the date the agent first encountered the deal in search results, instead of the actual announcement date in the source. The 1Q25-4Q25 audit found multiple rows where the agent picked an arbitrary mid-quarter date when the real announcement was in a prior quarter.

### Rule 6 — Currency capture mandatory for non-USD raises

Every non-USD raise MUST record:

- `native_currency` — the currency code as stated in the source (EUR, GBP, CNY, JPY, KRW, AUD, CAD, INR, etc.)
- `native_amount` — the amount in native currency, in millions
- `fx_rate_used` — units of native per 1 USD, at announcement date (preferred sources: ECB reference rate, Federal Reserve H.10, oanda.com)
- `fx_source` — string naming the rate source and date (e.g., "ECB reference 2026-04-15")

`amount_m` is the USD-converted amount using `fx_rate_used`.

🚫 **BANNED:** Storing a USD figure that's clearly a sloppy conversion (e.g., "CNY 300M = $120M" when the actual rate gives $42M). The 1Q25-4Q25 audit found currency-conversion drift on multiple Chinese and European deals.

If no separate FX fields exist, capture all four pieces of information in `robotnik_notes` instead. Better to embed in notes than to skip.

### Rule 7 — Round naming verbatim

The `round` field uses the **exact round name as stated by the company** in the primary source. Do not normalize for cleanliness if it changes meaning:

- ✓ "Series A+" stays "Series A+" (don't collapse to "Series A")
- ✓ "Series B-1", "Series B-2" stay as labeled (don't collapse to "Series B")
- ✓ "Series C extension" stays "Series C (extension)" — closest canonical form
- ✓ "Pre-Series A" / "Pre-Series B" / "Pre-Series C" stay as Pre-Series labels
- ✓ "Pre-IPO" stays "Pre-IPO"

🚫 **BANNED:** Mapping "Series A+" to "Series A" because it looks cleaner. The structural distinction matters for cap-table reconstruction. The 1Q25-4Q25 audit found round-name conflation in several rows.

If the round name doesn't match a canonical enum value, use the closest extension/variant (e.g., "Series C-2" → "Series C (extension)"). Never use bare "Other" — pick the closest canonical match.

### Rule 8 — Investor fields contain names only (added v1.1.1)

`lead_investors` and `co_investors` carry **named entities only**. Never use vague placeholders like "Multiple", "Various", "Existing investors", "Other existing and new investors", "Multiple state-backed investors", "PIPE syndicate (undisclosed)", etc. These break downstream groupby aggregation when VCs query the export.

- **Unknown `lead_investors`** → write `Undisclosed`
- **Unknown `co_investors`** → leave empty (empty string)
- If the source describes a structural detail (e.g., "via non-brokered private placement of 80M shares at C$0.27") rather than naming investors, that content belongs in `robotnik_take`, not in the investor field

🚫 **BANNED:** "Multiple", "Various ...", "Existing investors (...)" as values. Move named participants buried inside such strings into `co_investors`, then either resolve a real lead from source or fall back to `Undisclosed`. Same anti-fabrication discipline as URL rule 1.

### Rule 9 — Investor name canonicalization (added v1.1.1)

Before writing any investor name, canonicalize it against the investor names already present in [`data/funding/rounds.json`](../data/funding/rounds.json) — that dataset is the living canonical corpus. (The curated `investor_name_map.csv` was retired in the data-exposure cleanup and no longer exists; match each new name to how the firm already appears in the dataset.) Same firm should not appear under multiple spellings (case, spacing, abbreviation, division, suffix variants).

- Common canonicalizations: `Fidelity Investments` / `Fidelity Management & Research Co.` → `Fidelity Management & Research`. `Sequoia` → `Sequoia Capital`. `J.P. Morgan` / `JP Morgan` → `JPMorgan`. `Tiger Global` → `Tiger Global Management`. `10X Founders` → `10x Founders`. `BV.VC` → `BVVC`. Many more — grep the existing `lead_investors` / `co_investors` values in `rounds.json` for the established spelling.
- **Corporate vs venture arm: KEEP DISTINCT** globally. AMD ≠ AMD Ventures, Bosch Group ≠ Bosch Ventures, Qualcomm ≠ Qualcomm Ventures, Cisco ≠ Cisco Investments, Salesforce ≠ Salesforce Ventures, Stellantis ≠ Stellantis Ventures, Yamaha Motor ≠ Yamaha Motor Ventures, Honeywell ≠ Honeywell Ventures, Equinor ≠ Equinor Ventures, Ericsson ≠ Ericsson Ventures, Hanwha ≠ Hanwha Ventures. Different decision-makers, different mandates.
- For regional fund arms with distinct legal entities (e.g., Sequoia Capital China, Sequoia Capital India), keep distinct from the US parent unless the user merges them.
- If a new investor not yet in the dataset appears, write it in its canonical form and reuse that spelling consistently thereafter. When unsure, flag as `USER-VERIFY` in a `notes` field for the next canonicalization review.

### Rule 10 — `robotnik_take` ↔ `company_description` cross-check (added v1.1.1)

Before submitting a row, re-read its `robotnik_take` against its `company_description`. They MUST describe the same business / segment / product. If they don't, one of them is transposed from a different company — a paste-style error pattern caught 7 times in the v1.1.1 audit (Neros, MACH, Impulse Space 2024, Hanyang Tech 2023, xLight ×2, NcodiN ×2).

- ✓ The take's comp set and strategic frame must align with what `company_description` says the company does
- 🚫 If `current_take` describes "AI compute infrastructure" but `company_description` says "FPV combat drones", treat `company_description` as ground truth (it's freshly drafted from primary sources during the same pass) and rewrite the take from scratch
- Bonus: cross-check `related_tickers` and `source` URL against both. If the source URL is about a different company than the row claims, the row itself is likely transposed.

---

## Quality bar

- Each deal must have a verifiable primary source URL OR `source_status: pending`.
- Avoid Tracxn / PitchBook profile URLs as primary sources (they're aggregator pages, not contemporaneous announcements).
- Single-source: flag with `single_source: true` if only one publication confirmed the deal.
- For non-USD: capture native amount + announcement-date FX rate (ECB reference rate or oanda.com).
- For CHIPS Act / DOE LPO / METI: confirm BINDING award, not conditional / preliminary memorandum / Letter of Intent. Conditional commitments are explicitly excluded from the dataset (binding-only government rule).

---

## What to skip

- Series-letter rounds < $5M unless flagship (notable founder, breakthrough tech, marquee lead investor).
- Pre-seed < $2M unless flagship.
- Public secondaries / PIPEs at already-listed companies (Aurora rule). Post-IPO public market events out of scope.
- ICO / token sales (those go to the Tokens agent only).
- Pure-software crypto plays (zkVM, MEV, custody, social platforms, cross-chain L1 messaging) — they don't fit the hardware-anchored thesis.
- Suspicious single-source rows from PitchBook/Crunchbase that contradict the company's own press release.
- Parent-corporate capex commitments — facility investment plans without a discrete equity / debt raise.
- DOE LPO / ATVM **conditional commitments** — only include the closed/binding award at its actual close date.
- M&A divestitures of business units from non-universe parents (e.g., Honeywell W&WS carve-out).

---

## Robotnik notes voice

Brief (1–2 sentences), analytical, no marketing fluff. Examples:

- *"Series C extension at flat valuation amid broader robotics down-rounds. Lead is a sovereign-backed corporate VC, signaling industrial offtake intent over financial bet."*
- *"Insider-led; primary use of proceeds is scaling humanoid pilot deployments at warehouse customers (Amazon-adjacent). Comp: Figure (private $2.6B post)."*
- *"Strategic equity from CRH/Holcim alongside binding offtake. Validates electrolytic cement at industrial scale."*

Compare to public comps where useful: NVDA, TSM, ASML, AMAT, INTC, ARM, AVGO (semis); IRBT, SYM, LUNR, RKLB, ASTS, IRDM (robotics/space); ALB, LAC, MP, USAR (materials).

---

## Output

Save the JSON array to `/tmp/{window_slug}_research/{sector}.json` (e.g. `/tmp/may26_research/robotics.json`).

**Save incrementally — write the file after every ~10 deals you complete.** This protects against usage-limit interruptions.

Print a brief summary at the end: deal count, total $ disclosed, top 5 by size, count of `source_status: pending` rows.

---

## Run summary expectations

After all sectors complete, the orchestrator will produce a monthly summary with:

| Metric | Reporting |
|--------|-----------|
| Total rows added | n |
| Total disclosed | $XX.XB |
| `source_status: verified` | n / total (target ≥95%) |
| `source_status: pending` | n / total (target ≤5%; flagged for manual review) |
| Anti-fabrication compliance | 100% URLs WebFetch-verified |

---

## Change history

- **2026-05-06 (v1.0):** Template locked. Added `source_status` field, anti-fabrication rules (Rule 1-4), `Pre-IPO` round enum, binding-only government rule, public secondaries exclusion, pure-software crypto exclusion, parent capex exclusion. Codified after URL audit found ~12% of v1.0 source URLs were agent-fabricated.
- **2026-05-06 (v1.0.1):** Added Rules 5, 6, 7 covering systematic error classes surfaced in the 1Q25-4Q25 bulk data audit: date verification (use canonical announcement date, not synthesized), currency capture mandatory for non-USD raises (native + FX), and round naming verbatim (no normalization that changes meaning). Audit found 14 confirmed errors in 200 rows (~7% rate) plus 69 unverifiable; pattern errors concentrated in date-misattribution and currency-conversion-drift. Added `Series B2` to round enum (first use: Commonwealth Fusion Systems $863M, 2025-08-28) per Rule 7 verbatim-naming.
- **2026-05-12 (v1.1.1):** Added Rules 8, 9, 10 covering data-quality patterns surfaced in v1.1.1 CSV review: (8) investor placeholder ban — no "Multiple"/"Various"/"Existing investors" filler in lead/co fields; unknown → `Undisclosed` / empty. (9) canonical-name check against `investor_name_map.csv` before writing investor names; corporate-vs-venture-arm distinct globally. (10) `robotnik_take` ↔ `company_description` cross-check before submitting (transposition pattern caught 7× across the dataset). Note: `total_raised_m` and `total_number_of_raises` are retained internally but no longer in CSV export — they computed only from 2023+ coverage and under-counted companies with pre-2023 history.
- **2026-07-06 (v1.1.2):** Rule 9 repointed. The curated `investor_name_map.csv` was retired in the data-exposure cleanup (commit `afe10397`) and no longer exists in the repo; the old Rule 9 link pointed at a deleted file, so sweep agents silently fell back to a derived list (surfaced during the June 2026 sweep). Rule 9 now canonicalizes investor names against the spellings already present in `data/funding/rounds.json` (the living canonical corpus). No change to the canonicalization principles themselves (corporate-vs-venture-arm distinct, no duplicate spellings).
