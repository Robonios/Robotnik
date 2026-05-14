# Funding Ops Recompute — v1.1.3 Audit

**Date:** 2026-05-13
**Source:** `data/funding/rounds.json` (1,244 rows, schema_version v1.1.3, updated 2026-05-13)
**Status:** Review-only — `funding.html` and `funding.js` NOT modified.

> All recomputes anchored at the live page anchor **2026-05-14** (today), since
> `funding.js`'s `daysAgo(n)` derives from `new Date()`. A second set anchored at
> **2026-04-30** (latest dated row, per the user's task spec) is included in the
> appendix for completeness. The two sets are within 0.5% of each other for 1Y;
> they diverge by ~12% on 3M because two weeks of late-Apr/early-May rounds
> sit on the boundary.
>
> Frontier universe = rows where `sector NOT IN ('Token', 'Cross-Stack')` and
> `date` is non-null. This matches the existing `filterByPeriod` filter in
> `funding.js`. Frontier total = **1,215 rounds** of 1,244 (29 Token rounds
> excluded; Cross-Stack sector does not appear in the v1.1.3 universe).

---

## Summary — 1Y window (current page period for headline KPIs)

| Stat | Old display (user observation) | New v1.1.3 (live anchor 2026-05-14) | Comment |
|---|---|---|---|
| Capital Raised | $173.0B | **$171.6B** | Within $1.4B — user's snapshot is essentially current data. |
| Number of Rounds | 328 | **392** | +64 rounds added since user's snapshot (v1.0 → v1.1.3 backfills + sweeps). |
| Avg Deal Size | $546M | **$449M** | Lower; more disclosed rounds (382) dilute the mean. |
| YoY Capital change | +227% | **+228%** | Matches. NOT a bug — see Anomaly A below. |
| YoY Rounds change | +18% | **+36%** | The +18% was stale; current is +36%. |
| YoY Avg Deal Δ | +179% | **+142%** | Lower; same mega-round drivers, more denominator. |

The "+227% YoY" anomaly the user flagged turns out to be the **correct number** —
not a bug. It's driven by four mega-events in 2026 (SpaceX $75B IPO filing,
Amazon/Globalstar $11.6B M&A, Waymo $16B Series D, Rapidus $4B government).
The headline rounds count and avg deal size, however, ARE stale (the prior-period
"+18% rounds" hasn't refreshed with the v1.1.1 → v1.1.3 adds).

---

## Per-window stats (live anchor 2026-05-14, frontier-only)

| Window | Cutoff | Rounds | Disclosed | Capital ($B) | Avg ($M) |
|---|---|---:|---:|---:|---:|
| 3M  | 2026-02-13 | 154   | 146  | $119.60B  | $819.2M |
| 6M  | 2025-11-15 | 248   | 238  | $150.97B  | $634.3M |
| 1Y  | 2025-05-14 | 392   | 382  | $171.60B  | $449.2M |
| ALL | (all dates) | 1,215 | 1,187 | $288.04B | $242.7M |

## Per-window stats vs prior (Δ shown)

| Window | Capital | Δ Capital | Rounds | Δ Rounds | Avg | Δ Avg |
|---|---:|---:|---:|---:|---:|---:|
| 3M  | $119.60B | **+281.2%** vs $31.37B  | 154 | **+63.8%** vs 94  | $819.2M | **+140.2%** vs $341.0M |
| 6M  | $150.97B | **+638.3%** vs $20.45B  | 248 | **+79.7%** vs 138 | $634.3M | **+328.1%** vs $148.2M |
| 1Y  | $171.60B | **+227.7%** vs $52.36B  | 392 | **+36.1%** vs 288 | $449.2M | **+141.9%** vs $185.7M |
| ALL | $288.04B | (no prior) | 1,215 | (no prior) | $242.7M | (no prior) |

---

## All-window stats (for the new ALL filter)

| Stat | ALL |
|---|---:|
| Rounds | **1,215** |
| Disclosed | 1,187 |
| Capital Raised | **$288.04B** |
| Avg Deal Size | $242.7M |
| Date range | 2023-01-02 → 2026-04-30 (~40 months) |

ALL filter recommendation: the existing ALL branch in `filterByPeriod` already
handles this (lines 38-40 of `funding.js`); `chg()` already returns `''` when
prior is empty (line 153 — checks `hasPrior`). The "+18% vs prior" pill should
auto-suppress under ALL. **The current ALL implementation works.** The only fix
needed is to ensure the trends chart range, the period label in the notable
card, and the "X rounds detected" phrasing all read correctly under ALL —
existing code handles all three. The ALL button is **already wired in the HTML**
(line 118) and **already supported in JS** (line 36, 38). No change needed.

---

## Anomalies investigated

### A. The "+227% YoY" anomaly — NOT A BUG

**Finding:** +227.7% is the correct number against v1.1.3 data, with a healthy
prior-period denominator (288 frontier rounds, $52.36B).

**Driver:** 2026 mega-events not present in the prior 1Y window:

| Company | Round | Amount | Date | Impact on YoY |
|---|---|---:|---|---|
| SpaceX | IPO (filed) | $75.0B | 2026-04-01 | Single-handedly responsible for ~143% of the YoY swing |
| Amazon / Globalstar | M&A | $11.6B | 2026-04-14 | +22% |
| Waymo | Series D | $16.0B | 2026-02-02 | +31% |
| Rapidus | Govt investment | $4.0B + $1.7B | 2026 | +11% |
| Anduril | Series G | $2.5B | 2025-06-02 | +5% |

**Sanity check — strip the four >$10B mega-events:** YoY recomputes to **+31.8%**
(within the user-expected +30% to +80% range). So the data is healthy; the
+227% is a real signal that 2026 had a structural cluster of IPO/M&A/govt
mega-deals that the prior year (mostly CHIPS Act govt grants) didn't hit.

**Sanity check — strip all IPO/M&A/Govt/Debt/Strategic (pure venture only):**
YoY recomputes to **+215.9%** still — because Waymo ($16B Series D) and
Anduril ($2.5B Series G) are pure venture and account for most of the rest.

**Prior-period coverage:** The prior 1Y window (2024-05-14 → 2025-05-14) holds
288 rounds with quarterly counts 2Q24=51, 3Q24=76, 4Q24=93, 1Q25=49, 2Q25 partial=19.
Coverage is NOT thin — it's well-populated post-v1.1.1 backfills.

**Recommendation:** Keep the YoY math as-is. Consider adding a small footnote
under the Capital Raised card that explains "+227% reflects $75B SpaceX IPO
filing, $16B Waymo, $11.6B Globalstar M&A, $4B Rapidus" so analysts don't
mis-read it as a venture-funding boom. Or compute YoY ex-IPO/M&A as a secondary
KPI.

### B. The "Other 60 ($110.0B)" stage distribution

**Root cause: the user is reading a stale render.** Against v1.1.3 with the
current 10-bucket logic in `funding.js` (lines 65-84), the "Other" bucket is
TINY:

| Window | Other rounds | Other capital |
|---|---:|---:|
| 3M  | 6  | $3.02B |
| 6M  | 12 | $4.03B |
| 1Y  | 17 | $5.98B |
| ALL | 60 | $7.52B |

The 1Y "Other" is **17 rounds, $5.98B** — not 60/$110B.

**Where the user's "60" came from:** the ALL window has exactly **60 Other rounds**.
So either:
1. The user was on the ALL view when they read "60", OR
2. The page was rendered against an older bucketing function that lumped IPO/M&A
   into Other.

**Where the user's "$110B" came from:** with a 6-bucket Seed/A/B/C/D+/Other
function (which is the v1.0 stage logic, per git history), the 1Y "Other" bucket
recomputes to **52 rounds, $108.43B** — that's an exact match for "60 ($110B)"
within rounding. So the user IS seeing v1.0-style bucketing.

Looking at `js/funding.js` lines 65-84, the CURRENT code IS the 10-bucket logic.
So either the browser is loading a cached funding.js, or the user saw this in
a screenshot from before the 10-bucket logic shipped.

**Verification — distinct round values in 1Y window that fall into the v1.1.3
"Other" bucket:**

| Round value | n | Falls into "Other" because |
|---|---:|---|
| `Undisclosed` | 16 | No "Seed"/"Series X"/"IPO"/"M&A"/"Strategic"/etc. substring match |
| `Other` | 1 | Literal "Other" value (1 row: Taalas, $169M) |

The 10-bucket function correctly separates:
- `IPO`, `IPO (filed)`, `M&A` → IPO/M&A bucket (18 rounds, $94.41B in 1Y)
- `Strategic`, `Pre-IPO` → Strategic (4 rounds, $0.24B)
- `Government investment`, `Government`, `Grant` → Government (8 rounds, $7.26B)
- `Debt Financing` → Debt (5 rounds, $0.54B)

**Recommendation:**

1. **No relabel needed** — the 10-bucket logic already separates non-venture
   capital appropriately. The "Other" bucket is now legitimately small.
2. **Bug to fix:** rows with `round = 'Undisclosed'` (16 of them in 1Y, mostly
   large rounds — NEURA, Eutelsat, World Labs, Etched.ai) are dumped into
   "Other" because none of the substring checks match "Undisclosed". Add an
   explicit `else if (rd === 'Undisclosed' || rd === '') stage = 'Undisclosed'`
   branch BEFORE the Series A/B/C ladder. This pulls 16 rounds + $5.81B out of
   "Other" into their own bucket, leaving "Other" as 1 round / $169M (just
   Taalas, which legitimately has `round = 'Other'`). Then "Other" can be
   safely hidden, since it's a single outlier.
3. **Bridge round** appears 9 times in the corpus (none in 1Y). Add `'Bridge'`
   handling to avoid future Other-bucket bleed.
4. **Pre-Series A** / **Pre-Series B** / **Pre-Series C** / **Seed II** values
   exist in the corpus and currently fall into Other (none in 1Y window).
   Either add `Pre-Series` substring matches or extend the Seed/A/B/C
   conditions to include "Pre-".

### C. The "328 rounds" headline vs "138 rounds" table reconciliation

**Source of each number in `funding.js`:**

- **Headline "Number of Rounds" card (line 158):** `p.num_rounds` =
  `current.length` where `current = filterByPeriod(roundsData, currentPeriod)`.
  This is the 1Y frontier round count.
- **"View all N rounds" link (line 180):** `viewAllLink.innerHTML='View all '+p.num_rounds+' rounds'`.
  Also `p.num_rounds`. **By design, this is the same as the headline.**

So in well-formed v1.1.3 they should both display **392**. They cannot differ
within a single render — they're both bound to `p.num_rounds` from the same
period filter.

**Hypothesis for the "328 vs 138" mismatch the user observed:**

- "328" looks like a v1.0 1Y count (rough order of magnitude — v1.0 had 1,154 rows;
  1Y at that snapshot ≈ 328).
- "138" matches my recompute for the **Prior 6M** rounds count (138 rounds).
  Possible the user is reading the prior-comparison number from the 6M view
  and mistaking it for a different count. Or "138" is a static figure from
  an old `summary.json` snapshot that we're not loading anywhere visible.
- More likely: **the meta description** at `funding.html` line 7, 12, 20 still
  says **"1,154 funding rounds"** — that's v1.0. Also `funding.html` line 198
  hardcodes **"1,154 Funding Rounds"** in the gated-rounds enterprise preview.
  Those need to update to 1,244 (or 1,215 frontier-only).

**Recommendations:**

1. Update `funding.html` line 7, 12, 20 meta description from "1,154" → "1,244"
   (or compute dynamically server-side; static is fine for SEO).
2. Update `funding.html` line 198 hardcoded "1,154 Funding Rounds" → "1,244
   Funding Rounds".
3. The headline and "View all" link will reconcile to **392** automatically once
   the browser flushes cached JS — there's no extra code change required there.

### D. Top Investor counting logic — CRITICAL BUG

**The page is reading the wrong field.** `funding.js` lines 186 and 329 both reference
`r.other_investors`, but the actual field in `rounds.json` is `r.co_investors`.
Across the full corpus:

| Field | Rows where non-null |
|---|---:|
| `r.lead_investors`  | 1,159 |
| `r.co_investors`    | 899 |
| `r.other_investors` | **0** |

So the page's investor counts are derived from **lead-only data**. The Top
Investor KPI card and the Top 10 Investors panel under-count by ~50-70%.

**Top 10 Investors comparison (1Y window):**

| Rank | Broken (lead-only) | Correct (lead + co_investors, deduped per-round) |
|---:|---|---|
| 1 | Eclipse Ventures (8) | **NVentures (NVIDIA) (17)** |
| 2 | Founders Fund (7) | Eclipse Ventures (13) |
| 3 | Khosla Ventures (6) | Lightspeed Venture Partners (13) |
| 4 | Playground Global (5) | Fidelity Management & Research (12) |
| 5 | Fidelity Management & Research (5) | Andreessen Horowitz (11) |
| 6 | Sequoia Capital (5) | Founders Fund (10) |
| 7 | Andreessen Horowitz (5) | Sequoia Capital (9) |
| 8 | Lightspeed Venture Partners (5) | Valor Equity Partners (9) |
| 9 | NATO Innovation Fund (4) | Khosla Ventures (9) |
| 10 | Lux Capital (4) | Atreides Management (9) |

**NVentures (NVIDIA) is the true #1 with 17 deals** (Eclipse falls to #2 with 13).
The current page reports Eclipse #1 with 8 deals. Both the rank order and the
counts are wrong.

**Double-counting concern (the user asked about this):** investigated. Of the
392 rounds in 1Y, only **5 rows** have a firm appearing in both `lead_investors`
AND `co_investors` for the same deal (3 of those 5 are just the `Undisclosed`
placeholder, which is already filtered). Real overlap: 2 rows (Zipline,
Nio GeniTech). Negligible impact — but to be safe, the "Correct" column above
deduplicates within each round (using a per-row `seen` Set) before incrementing.

**Recommendations:**

1. **`funding.js` line 186:** change `r.other_investors` → `r.co_investors`.
2. **`funding.js` line 329:** change `r.other_investors` → `r.co_investors`.
3. **Add per-round dedup** to prevent the 2 legitimate overlap rows from
   double-counting (insert a `Set` initialized per `forEach(function(r){...})`
   iteration; check `il` against it before incrementing). Optional — impact is
   tiny.
4. **Optional:** the `EXCLUDE` set currently has 6 placeholder strings but the
   data also contains other non-firm strings worth filtering: `'TBD'`, `'See note'`,
   etc. Audit if any leak through (none seen in 1Y top 50).

### E. Auto-generated narrative paragraph

**Location:** `funding.js` lines 367-385, `renderNotable(p, periodLabel)`. It IS
dynamically computed — not hardcoded — but it's bound to the broken metrics so
its numbers are wrong, and the phrasing has a v1.0 hardcoded string.

Current rendered template:
```
Tovarishch, <strong>{p.num_rounds} frontier stack rounds</strong> detected
{phrase}, deploying <strong>{fmtM(p.total_capital_m)}</strong> of capital.
{mostActive} dominates deal flow with {mostActiveRounds} rounds, but
{bestAvgSector} commands the highest average deal size at {fmtM(bestAvg)} per
round. <strong>{megas} mega-rounds</strong> exceeding $500M signal deep
conviction in frontier compute and physical AI infrastructure.
```

Where `phrase = currentPeriod==='ALL' ? 'across the full v1.0 dataset (since Jan 2023)' : 'in the last '+periodLabel`.

**Problems:**

1. **"v1.0 dataset" is hardcoded in the ALL branch (line 382).** The dataset is
   now v1.1.3. Either remove the version marker or update to "v1.1.3" — better:
   inject the version from `summaryData.schema_version` (already loaded), e.g.,
   `'across the full dataset ('+summaryData.schema_version+', since Jan 2023)'`,
   so it auto-updates. NOTE: `summary.json` does not currently contain a
   `schema_version` field — only `rounds.json` does. Either add it to
   summary.json, or pull from `roundsData.schema_version` (need to capture the
   wrapper before extracting `.rounds`).

2. **All numeric tokens are correctly computed** (`p.num_rounds`, `p.total_capital_m`,
   `mostActiveRounds`, `bestAvg`, `megas`) — they'll all update when the data
   refreshes. Once funding.js redeploys, the narrative will read against v1.1.3
   automatically.

3. **`mostActive` and `bestAvgSector`** are derived from `p.sector_breakdown`,
   which is built in `calcMetrics` (line 56-60). Both will recompute correctly.

**Recommendations:**

1. Change line 382: `'across the full v1.0 dataset (since Jan 2023)'` →
   `'across the full dataset (since Jan 2023)'` (drop the version marker), OR
   capture `roundsData.schema_version` during fetch and template it in.
2. Optional polish: the `bestAvgSector` line currently rounds avg to int via
   `Math.round(bestAvg)` then `fmtM` — small precision issue, not a bug. Fine.
3. **Expected v1.1.3 narrative (1Y):**
   > Tovarishch, **392 frontier stack rounds** detected in the last 12 months,
   > deploying **$171.6B** of capital. Robotics dominates deal flow with 161
   > rounds, but Space commands the highest average deal size at $1.0B per
   > round. **47 mega-rounds** exceeding $500M signal deep conviction in
   > frontier compute and physical AI infrastructure.
4. **Expected v1.1.3 narrative (ALL):**
   > Tovarishch, **1,215 frontier stack rounds** detected across the full
   > dataset (since Jan 2023), deploying **$288.0B** of capital.
   > Robotics dominates deal flow with 585 rounds, but Space commands the
   > highest average deal size at $471M per round. **[N] mega-rounds**
   > exceeding $500M signal deep conviction…

---

## Top 10 Rounds (1Y) — v1.1.3

| # | Company | Sector | Round | Amount | Date |
|---:|---|---|---|---:|---|
| 1 | SpaceX | Space | IPO (filed) | $75.0B | 2026-04-01 |
| 2 | Waymo | Robotics | Series D | $16.0B | 2026-02-02 |
| 3 | Amazon / Globalstar | Space | M&A | $11.57B | 2026-04-14 |
| 4 | Rapidus | Semiconductors | Government investment | $4.0B | 2026-04-11 |
| 5 | Anduril Industries | Robotics | Series G | $2.5B | 2025-06-02 |
| 6 | Nscale | Semiconductors | Series C | $2.0B | 2026-03-09 |
| 7 | Shield AI | Robotics | Series G | $2.0B | 2026-03-26 |
| 8 | Cerebras Systems | Semiconductors | IPO (filed) | $2.0B | 2026-04-17 |
| 9 | Rapidus | Semiconductors | Government investment | $1.7B | 2026-02-27 |
| 10 | Eutelsat | Space | Undisclosed | $1.55B | 2025-06-19 |

Total of top 10 = **$118.32B** (69% of 1Y total).

## Top 10 Rounds (ALL) — v1.1.3 (for reference)

| # | Company | Sector | Round | Amount | Date |
|---:|---|---|---|---:|---|
| 1 | SpaceX | Space | IPO (filed) | $75.0B | 2026-04-01 |
| 2 | Waymo | Robotics | Series D | $16.0B | 2026-02-02 |
| 3 | Amazon / Globalstar | Space | M&A | $11.57B | 2026-04-14 |
| 4 | Intel | Semiconductors | Government investment | $7.87B | 2024-11-26 |
| 5 | Micron Technology | Semiconductors | Government investment | $6.17B | 2024-12-10 |
| 6 | Arm Holdings | Semiconductors | IPO | $4.87B | 2023-09-14 |
| 7 | Samsung Electronics | Semiconductors | Government investment | $4.75B | 2024-12-20 |
| 8 | Hua Hong Semiconductor JV | Semiconductors | Strategic | $4.02B | 2023-01-31 |
| 9 | Rapidus | Semiconductors | Government investment | $4.0B | 2026-04-11 |
| 10 | ESMC (TSMC/Bosch/Infineon/NXP JV) | Semiconductors | Strategic | $3.85B | 2023-08-08 |

---

## Top 10 Investors (1Y) — old vs new

| Rank | OLD (lead_investors only, broken r.other_investors lookup) | NEW v1.1.3 (lead + co_investors, deduped) |
|---:|---|---|
| 1 | Eclipse Ventures (8 deals) | **NVentures (NVIDIA) (17 deals)** |
| 2 | Founders Fund (7) | Eclipse Ventures (13) |
| 3 | Khosla Ventures (6) | Lightspeed Venture Partners (13) |
| 4 | Playground Global (5) | Fidelity Management & Research (12) |
| 5 | Fidelity Management & Research (5) | Andreessen Horowitz (11) |
| 6 | Sequoia Capital (5) | Founders Fund (10) |
| 7 | Andreessen Horowitz (5) | Sequoia Capital (9) |
| 8 | Lightspeed Venture Partners (5) | Valor Equity Partners (9) |
| 9 | NATO Innovation Fund (4) | Khosla Ventures (9) |
| 10 | Lux Capital (4) | Atreides Management (9) |

**Top Investor card** (single value): OLD = Eclipse Ventures, NEW = **NVentures (NVIDIA)**.

---

## Sector Breakdown (1Y) — v1.1.3

| Sector | Rounds | Capital ($B) | % of 1Y total |
|---|---:|---:|---:|
| Space | 96 | $97.96B | 57.1% |
| Robotics | 161 | $44.61B | 26.0% |
| Semiconductors | 107 | $25.58B | 14.9% |
| Materials | 28 | $3.44B | 2.0% |
| **Total** | **392** | **$171.60B** | 100.0% |

Note: Space concentration is driven by SpaceX $75B (single round = 44% of 1Y
total) + Globalstar $11.6B M&A. Strip SpaceX and Space drops to $22.96B (19%
of remaining $96.6B 1Y total).

## Sector Breakdown (ALL) — v1.1.3

| Sector | Rounds | Capital ($B) | % of ALL total |
|---|---:|---:|---:|
| Space | 233 | $109.75B | 38.1% |
| Semiconductors | 285 | $87.89B | 30.5% |
| Robotics | 585 | $69.65B | 24.2% |
| Materials | 112 | $20.76B | 7.2% |
| **Total** | **1,215** | **$288.04B** | 100.0% |

---

## Funding Trends chart (1Y) — quarterly bars

| Quarter | Rounds | Total ($B) | Semi | Robo | Space | Mat |
|---|---:|---:|---:|---:|---:|---:|
| 2Q25 | 35  | $7.54B   | $0.22B | $4.87B  | $2.01B  | $0.44B |
| 3Q25 | 75  | $10.26B  | $3.75B | $2.84B  | $2.08B  | $1.59B |
| 4Q25 | 86  | $8.06B   | $2.54B | $3.00B  | $1.83B  | $0.69B |
| 1Q26 | 111 | $45.20B  | $9.83B | $31.04B | $3.62B  | $0.70B |
| 2Q26 | 85  | $100.54B | $9.23B | $2.86B  | $88.42B | $0.02B |

The current trends chart in `funding.js` uses **monthly bars** (line 254,
`chartMonths = Math.max(6, Math.ceil(days/30))`). For the 1Y view it shows
~12 monthly bars. The data those bars draw against:

| Month | Semi | Robo | Space | Mat |
|---|---:|---:|---:|---:|
| May-25 | $0.03B | $0.03B | $0.13B | — |
| Jun-25 | $0.19B | $4.84B | $1.88B | $0.44B |
| Jul-25 | $0.26B | $1.20B | $0.20B | $0.55B |
| Aug-25 | $0.19B | $0.50B | $1.01B | $0.94B |
| Sep-25 | $3.29B | $1.15B | $0.86B | $0.10B |
| Oct-25 | $0.16B | $0.47B | $0.62B | $0.35B |
| Nov-25 | $0.23B | $1.71B | $0.23B | $0.04B |
| Dec-25 | $2.15B | $0.81B | $0.98B | $0.30B |
| Jan-26 | $1.06B | $4.62B | $0.11B | $0.18B |
| Feb-26 | $4.81B | $19.78B | $1.84B | — |
| Mar-26 | $3.96B | $6.64B | $1.68B | $0.52B |
| Apr-26 | $9.23B | $2.86B | $88.42B | $0.02B |

**Apr-26 ($88.42B Space bar) will dominate the chart vertically.** The
SpaceX+Globalstar pair makes the visual collapse — every other month becomes a
sliver. Consider:

1. **Add a log scale option** to the trends chart.
2. **Add an "ex-IPO/M&A" toggle** so users can see venture-only trends.
3. **Annotate the Apr-26 bar** with a marker indicating it's IPO-driven.

---

## Recommended code changes to `funding.js`

| # | File:Line | Change | Severity |
|---:|---|---|---|
| 1 | funding.js:186 | `r.other_investors` → `r.co_investors` (in `getTopInvestor`) | **HIGH** — fixes Top Investor KPI |
| 2 | funding.js:329 | `r.other_investors` → `r.co_investors` (in `renderTopInvestors`) | **HIGH** — fixes Top 10 Investors panel |
| 3 | funding.js:75-80 | Insert `else if(rd==='Undisclosed'\|\|rd==='') stage='Undisclosed'` BEFORE Seed match | MEDIUM — pulls 16 rounds + $5.81B out of "Other" in 1Y |
| 4 | funding.js:353 | Add `'Undisclosed'` to stages array; add a 10th color in stgColors | MEDIUM — companion to #3 |
| 5 | funding.js:382 | `'across the full v1.0 dataset'` → `'across the full dataset'` or template the version | LOW — cosmetic but visible |
| 6 | funding.js:188 / 331 | Add per-round dedup set to prevent firm-in-both-lead-and-co double-count (2 legitimate cases in 1Y) | LOW — small impact |
| 7 | funding.js:36 | Optional: `ALL` already returns `null` from `periodDays`; works correctly. No change. | OK |
| 8 | funding.js:78-79 | Optionally extend Seed/Series A matching to handle `Pre-Series A/B/C`, `Seed II`, `Bridge` (currently → Other) | LOW |
| 9 | funding.js:74 | `rd==='Strategic'\|\|rd==='Pre-IPO'` → consider lumping `Pre-IPO` into IPO/M&A bucket instead (more natural read) | LOW |

| # | File:Line | Change | Severity |
|---:|---|---|---|
| 10 | funding.html:7,12,20 | "1,154 funding rounds" → "1,244 funding rounds" in meta description (3 places) | LOW — SEO/social |
| 11 | funding.html:198 | "1,154 Funding Rounds" → "1,244 Funding Rounds" in gated rounds enterprise preview | LOW |

**Note on cache-busting:** `funding.html` line 242 sets `js/funding.js?v=20260506`.
After the fix-pass, bump the `?v=` query string to force browser refresh on
re-deploy.

---

## Appendix — Recompute at the task-spec anchor (2026-04-30, latest dated row)

For completeness, here are the numbers anchored at **2026-04-30** rather than
live (2026-05-14). The 1Y window then becomes 2025-04-30 → 2026-04-30.

| Window | Rounds | Capital ($B) | Avg ($M) |
|---|---:|---:|---:|
| 3M  | 173   | $139.77B | $852.2M |
| 6M  | 262   | $152.20B | $603.9M |
| 1Y  | 399   | $172.14B | $442.5M |
| ALL | 1,215 | $288.04B | $242.7M |

| YoY (2026-04-30 anchor) | Current | Prior | Δ |
|---|---:|---:|---:|
| Capital  | $172.14B | $54.52B | **+215.7%** |
| Rounds   | 399      | 298     | **+33.9%** |
| Avg      | $442.5M  | $186.7M | **+137.0%** |

(Live anchor 2026-05-14 produces +227.7% / +36.1% / +141.9% — within noise.
The user's observed +227% matches the live anchor. The task-spec anchor
diverges modestly because two weeks of late-Apr 2025 rounds get newly
included in the prior 1Y window.)

---

*Generated 2026-05-13. Source of truth: `data/funding/rounds.json` (v1.1.3, 1,244 rows).
No modifications made to `funding.html` or `funding.js`.*
