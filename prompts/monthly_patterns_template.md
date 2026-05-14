# Monthly Patterns One-Pager — Workflow Template

**Locked at:** v1.1.3 (2026-05-13), worked example: April 2026 edition.

The monthly Patterns one-pager is the second editorial deliverable in the Robotnik VC outreach wave (alongside the monthly CSV). Initial distribution: Notion-bridge page per recipient with a CSV download link. Site-hosted version (`/patterns/[month-year].html`) is deferred until format is validated with first-cohort VC readers.

This template encodes the workflow so each subsequent month can run on the same rails.

---

## Cadence

- Drafted alongside the monthly CSV regeneration (first Sunday of the following month).
- May 2026 edition drafts on the first Sunday of June 2026. Same workflow.
- One edition per month. No skipping a month even if the data is light — light months *are* a signal.

---

## Inputs

Each month, you need:

1. **The locked monthly CSV.** Source: `data/exports/Robotnik Frontier Private Rounds <Month-YYYY>.csv` plus the underlying `data/funding/rounds.json` for slice-and-dice queries.
2. **Schema version locked.** Confirm the CSV schema_version matches what VCs will receive. If a v1.x.y release shipped the same week, use that.
3. **Source signal candidates.** Patterns visible in the data that a busy analyst would miss. The pre-seed/seed sweep audits, transposition logs, and prior remediation docs are useful priors but not required reading.

---

## Process

### Step 1 — Compute the month's aggregates

For the target month, compute and record:
- Row count (deals)
- Total capital raised (USD millions)
- Sector mix (deals and capital per sector)
- Round-type distribution
- Top 15 deals by amount
- Pre-seed / seed breakdown (these are early-signal goldmines)
- IPO / M&A / Pre-IPO event list (always worth examining for migration-vs-exit pattern)
- Geographic concentration (look for clusters)
- Investor concentration (any fund leading 2+ in one sector?)

Save the aggregate computation script output to `data/patterns/<month_year>_aggregates.txt` for traceability.

### Step 2 — Surface pattern candidates

Read the aggregates. Look for:

- **Numeric anomalies.** Sector amounts way above/below trailing months. Round-type clustering. Geographic concentration unusual for the segment.
- **Round-size geometry.** Pre-seed/seed at amounts that don't match the round letter (e.g., $455M Pre-Series A). These are pricing-signal events.
- **Investor concentration patterns.** Same fund leading multiple rounds in one sub-segment. Strategic-acquirer M&A streaks.
- **Inter-round comparisons.** What's the same company doing vs three months ago? Six months?
- **The dog that didn't bark.** Sectors that should have raised and didn't (e.g., US humanoid in April 2026). This is often the strongest signal.

Pattern-selection rule:

A good pattern is **specific** (named companies, regions, sub-sectors, investors), **numeric where possible** (counts, multiples, dollar figures), **inferential** (saying something the raw rounds don't), and **hard to see from any single round** (the pattern's value is in the aggregation).

Lean toward patterns visible in the month, but broader-window early-stage signals are fair game if more analytically striking. The one-pager is "the month's read", not "month-only".

### Step 3 — Draft

Target: **600-800 words, 2-3 patterns.**

Structure:
- **Title:** "Robotnik Patterns — [Month YYYY]"
- **Subhead** (~one-line framing of the month overall)
- **Opening paragraph** (~80 words) — sets the month-level frame, names the headline aggregate, points to the sector/round mix that tells more than the headline.
- **2-3 patterns** as H2 sections, ~200-300 words each. Each pattern: one-line claim in the H2, then supporting evidence from the month's data, then the read-through.
- **Closing** (~one line gesturing at what to watch next month, falsifiable if possible).
- **Signature line:** `*Robotnik / [Month YYYY]*`

Voice rules:
- First person plural ("we see", "we lean") or no-person declarative. **Never** first person singular.
- Confident but not breathless. Names companies and investors. Doesn't anonymise.
- Comfortable disagreeing with consensus, but the disagreement has to earn its place via evidence.
- Plain prose. Minimal bolding in body text. No bullet lists in body unless absolutely necessary (a short comp-set list is fine if it earns its place).

Falsification rule: at least one pattern should have a clear near-term test that would falsify the read. (April 2026 example: "if Q3 2026 IPO pricing on SpaceX or Cerebras comes in soft, the migration thesis breaks immediately.")

Save at `data/patterns/<month_year>_draft.md`.

### Step 4 — Surface for review

**STOP here.** Surface to user for review. Do not Notion-format or publish until explicit approval.

Surface message structure:
- Word count + per-section breakdown
- The aggregates table (so the user can see what the month looked like at a glance)
- The 2-3 patterns selected, with a "why this one" rationale per pattern
- Patterns considered but not selected (briefly, with reason)
- The draft inline OR a link to it
- Decisions needed: pattern selection / voice / specific phrasing flags / length

If the user requests changes, apply them, re-save, and re-surface a tight diff. Don't re-open the whole draft for review.

### Step 5 — Notion-ready formatting

After user approval, produce a Notion-ready version at `data/patterns/<month_year>_notion_ready.md`.

Differences vs draft:
- Same content as approved draft (no editorial changes at this step).
- Title and section headers in markdown (Notion ingests cleanly).
- A subhead line under the title in bold ("**Three signals visible only in aggregate**" or similar).
- A closing footer paragraph (after the signature line) inviting feedback during the calibration period. Template:

> *Robotnik — [Month YYYY] edition. The full [Month YYYY] CSV (X,XXX rows × 23 cols, schema vX.Y.Z) is available at the download link in the cover note. Reply with feedback — voice, pattern selection, and signal density are all in calibration mode for the first three monthly editions.*

Update the row count, column count, and schema version to match the locked CSV that ships with the edition.

### Step 6 — Distribution

The Notion-ready markdown gets pasted into a Notion bridge page per recipient. Each page also carries the CSV download link.

The site-hosted version (`/patterns/[month-year].html` plus a `/patterns/` index) is deferred per the v1.1.3 site-overhaul decision. When ready to ship the site-hosted version:
- Convert the Notion-ready markdown to HTML matching the site's typography (Roboto Mono, dark theme).
- Add a `/patterns/` index page listing all editions chronologically.
- Add a `Patterns` nav slot in `js/nav.js`.

---

## Anti-fabrication discipline (same as monthly ingestion)

The Patterns one-pager runs against the SAME data as the CSV. The same anti-fabrication rules apply:

- Don't fabricate valuations. If `valuation_m` is null, don't cite a post-money figure as fact. "Implied $2-3B" is acceptable if the reasoning is clear; "$2.5B post" is not.
- Don't fabricate aggregations. Every count, sum, multiplier, share-percentage must reconcile to the source data.
- Don't fabricate quotes. Don't invent investor commentary.
- Don't fabricate comp sets. Use real public-market tickers; the v1.1.1 ticker-accuracy rules apply (Cerebras = (IPO filed), AspenTech = (now part of Emerson, EMR), etc.).
- Cross-check `robotnik_take` content against `company_description` for transposition (Rule 10). If a take describes a different business than the description, treat the description as ground truth.

---

## File paths

```
data/funding/rounds.json                                       # source
data/exports/Robotnik Frontier Private Rounds <Month-YYYY>.csv # locked CSV
data/patterns/<month_year>_aggregates.txt                       # step 1 output
data/patterns/<month_year>_draft.md                             # step 3 output
data/patterns/<month_year>_notion_ready.md                      # step 5 output (after approval)
prompts/monthly_patterns_template.md                            # this template
```

`<month_year>` format: lowercase month + underscore + four-digit year. Examples: `april_2026`, `may_2026`, `november_2026`.

---

## Worked example: April 2026

- Aggregates: 86 deals, $100.5B total (ex-SpaceX $25.5B). Space $88.4B / Semis $9.2B / Robotics $2.9B / Materials $22M / Token $5M.
- Three patterns selected:
  1. The frontier-tech exit window has reopened (12 IPO/M&A/Pre-IPO events, $91B exit-track, 7/12 strategic acquirers — migration-vs-exit framing).
  2. Chinese humanoid raised 5× what US humanoid raised in April ($1.48B vs $0; TARS $455M Pre-Series A is the load-bearing data point).
  3. Silicon photonics merchant ecosystem is consolidating (DustPhotonics → Credo $1.3B + Polariton M&A; Lightmatter only remaining clean-merchant pure-play at multi-billion private scale).
- Closing watch: SpaceX / Cerebras IPO pricing as the migration-vs-exit binary.
- Word count: 680 (within 600-800 target).
- Files: `data/patterns/april_2026_draft.md`, `data/patterns/april_2026_notion_ready.md`.

---

## Change history

- **2026-05-13 (v1.1.3 release):** Template locked. Workflow encoded after April 2026 edition shipped as worked example. Notion-hosted distribution; site-hosted version deferred per outreach-feedback gate.
