# Robotnik Private Capital Index (RPCI) — Methodology

**Code:** RPCI · **Base:** 1,000.00 on 2025-03-31 · **Periodicity:** monthly

The RPCI measures activity and conviction in private-market fundraising
across the frontier technology stack (semiconductors, robotics, space,
critical materials). It sits alongside the public Robotnik Composite Index
as a structurally different signal: **capital deployment flow and
conviction signal, not mark-to-market valuation.**

## At a glance

| Property | Value |
|---|---|
| Base value | 1,000.00 |
| Base date | 2025-03-31 |
| Series start | 2024-01 (Jan 2023 – Dec 2023 is the calibration window, not published) |
| Periodicity | monthly recalculation |
| Reading window | 3-month trailing (May 2026 reading aggregates Mar / Apr / May 2026) |
| Component count | 5 |
| Underlying data | `data/funding/rounds.json` (v1.1.3+; 1,244+ private rounds since Jan 2023) |

The RPCI is recalculated each month after the monthly ingestion cycle.
Both the monthly point and a 3-month trailing smoothed line are published.

## Components and weights

| # | Component | Weight | What it measures |
|---|---|---:|---|
| 1 | Capital deployed (USD) | **30%** | Sum of disclosed round sizes in the 3-month window, with per-round cap at the 95th-percentile of prior-12-month rounds at the same stage |
| 2 | Deal count | **20%** | Count of all rounds in the window (includes undisclosed-amount rounds) |
| 3 | Stage-weighted activity | **25%** | Sum of (count at stage × stage weight) across the window |
| 4 | Round size vs trailing 12M median | **15%** | Average of (round size / prior-12M median at the same stage) across rounds in the window |
| 5 | Investor breadth | **10%** | Count of unique investors in the window; new-in-prior-24M investors get a 1.25× multiplier |

### Component 3 — stage weights

| Stage | Weight |
|---|---:|
| Pre-seed / Seed | 0.7 |
| Series A | 1.0 |
| Series B | 1.3 |
| Series C+ | 1.6 |
| Growth / pre-IPO | 2.0 |

### Stage mapping (from raw round labels)

The dataset's round enum (37 canonical values) maps to the five RPCI stages:

- **Pre-seed / Seed:** `Pre-Seed`, `Pre-Seed (extension)`, `Seed`, `Seed (extension)`, `Seed+`, `Seed II`, `Pre-Series A`
- **Series A:** `Series A`, `Series A (extension)`, `Pre-Series B`
- **Series B:** `Series B`, `Series B2`, `Series B (extension)`, `Series B Extension`, `Pre-Series C`
- **Series C+:** `Series C` through `Series H` and their extensions
- **Growth / pre-IPO:** `Pre-IPO`, `IPO (filed)` *(company still private at filing)*

### Round labels excluded from the RPCI

Not private equity venture rounds; these are tracked in `rounds.json` but
do not contribute to RPCI components:

`IPO`, `IPO (filed)`, `Strategic` (stage-ambiguous), `Government investment`,
`Government`, `Grant`, `Debt Financing`, `Bridge` (stage-ambiguous),
`Undisclosed`, `Other`.

The `M&A` value is handled **conditionally** rather than as a blanket
exclusion — see the next section.

These exclusions are logged at each run in
`data/index/private_capital_index_guardrails.log`.

### IPO exclusion (both filed and listed)

Both `IPO` and `IPO (filed)` are out of scope for RPCI. An IPO — whether
the actual listing or just the S-1 filing — is a transition event from
private to public, not a private capital deployment. Including either
would mix two structurally different signals.

`Pre-IPO` rounds stay in scope (private growth-stage capital still
deployed before the IPO process begins).

Per-month IPO exclusion counts are logged in the guardrails file so the
filter can be verified to be biting correctly.

### M&A conditional inclusion rule

`M&A` rows are evaluated case-by-case rather than blanket-excluded.
An M&A row is included in RPCI **iff the acquirer is a private company
in the Robotnik universe**:

- **Public acquirer** (in or out of universe) → excluded. Public-market
  capital deployment, not private. The target is also exiting the
  private market.
- **Private acquirer, in the Robotnik universe** → **included**. This
  represents private capital flowing to acquire frontier-stack assets,
  with the combined entity remaining private.
- **Private acquirer, out of the Robotnik universe** → excluded.
  Out-of-scope (e.g., a retail conglomerate acquiring a niche
  frontier-tech asset).
- **Undisclosed acquirer** → excluded.

Public-universe detection works from two sources:
1. Ticker patterns in the acquirer string (e.g., `(NASDAQ: CRDO)`).
2. Name-match against `data/index/market_caps.json` (the active public
   universe), supplemented by an in-script list of common public
   acquirers (Amazon, Microsoft, Intel, etc.) not always present in
   market_caps.

Included M&A rows map to the **Growth / pre-IPO** stage for component 3
(stage-weighted activity) — these are late-stage capital events by
construction.

**Private-in-universe definition.** Operationally a company is "private
in the Robotnik universe" if either:

1. It appears as a target of a non-M&A round in `rounds.json` during
   the dataset coverage window. *(default: derived automatically)*
2. It is in the explicit `PRIVATE_ACQUIRER_ALLOWLIST` in
   `scripts/calculate_private_index.py`. *(manual allowlist)*

The allowlist exists to capture real frontier-tech private companies
that happen to be acquisitive without raising private capital
themselves during our coverage window. As of v1.1 the allowlist
contains:

| Entry | Why |
|---|---|
| York Space Systems | Active space/defense private; acquired ALL.SPACE 2026-04 for $355M; no fundraising rounds in our coverage window |

The allowlist is reviewed periodically against new "EXCLUDE: acquirer
not in Robotnik universe" entries in the M&A audit log — a small
research artefact tracking which private frontier-tech companies are
acquisitive but not actively fundraising.

Every M&A decision (include or exclude, with reason) is logged in
`data/index/private_capital_index_ma_audit.log`.

## Composite calculation

For a reading at month *t*:

1. Compute the raw value of each component for the 3-month window ending at *t*.
2. Normalise each component against its value at the base date (2025-03-31)
   such that each component reads **1,000.00** at base.
3. Apply weights and sum:

   `RPCI(t) = Σ wᵢ × normalised_componentᵢ(t)`

By construction, RPCI = 1,000.00 exactly at the base date.

A 3-month trailing smoothed value is also published per row.

## Trailing-window conventions

Two distinct trailing windows are used:

- **3-month reading window** (the data the reading covers): the 3 calendar
  months *including* month *t*. The reading at May 2026 covers
  March – May 2026.

- **Trailing 12M reference** (used by components 1 and 4): the 12 calendar
  months **ending immediately before the 3-month window starts**. The
  trailing 12M for May 2026 is therefore March 2025 – February 2026.

  Using a prior-12M reference rather than an inclusive-of-current-window
  reference is necessary for the per-round cap to actually bite — a
  mega-round included in its own reference distribution moves the
  percentile up with itself and loses its constraining effect. The spec's
  stated intent ("prevent single-round skew") is only achieved by an
  exogenous trailing reference.

- **Investor freshness lookback** (component 5): the 24 months ending
  immediately before the 3-month window. An investor present in the
  current window but absent in the prior 24 months receives the 1.25×
  multiplier.

## Calibration window

January 2023 – December 2023 serves as the calibration window. It
establishes the trailing-12M reference distributions needed for the
earliest published readings (Jan 2024 onward). Calibration-window
readings are not themselves published, only used as backstop history.

Early back-test months use whatever portion of the 24-month investor
lookback is available within the dataset history. The first complete
24-month investor history is available at the January 2025 reading.

## Handling missing data

Per component:

| Field state | Components 1, 4 | Components 2, 3, 5 |
|---|---|---|
| `amount_m` is null (undisclosed amount) | **Exclude** the round | **Include** the round |
| `lead_investors` / `co_investors` empty | (no effect) | Counts toward dealcount/stage; no investors added to breadth |
| Round value in `EXCLUDED_ROUNDS` set | Excluded everywhere | Excluded everywhere |
| Round value not in `STAGE_MAP` and not in `EXCLUDED_ROUNDS` | **Guardrail 3 failure → exit non-zero** | (same) |

Undisclosed amounts (~5–10% of rounds historically) still convey signal in
deal count, stage mix, and investor presence — only their dollar
contribution is unavailable. Components 1 and 4 work on the disclosed
subset; components 2, 3, and 5 use the full set.

## Guardrails

Three defensive checks at each run. Matches the pattern established for
the public Robotnik Index after the Korean-ticker / EODHD sentinel
incident.

### Guardrail 1 — Single-round sanity

Any single round whose disclosed amount exceeds **5× the 99th-percentile
of prior-12M rounds at the same stage** is logged for review. The round
remains in the calculation but is capped at the 95th-percentile per the
component-1 methodology (so it cannot single-handedly distort the
reading). Informational; does not exit.

Examples flagged during back-test:
- The Bot Company $150M Pre-seed (May 2024) — 5.8× prior-99th
- Commonwealth Fusion Systems $863M Series B2 (Aug 2025) — 5.1–5.5×
- Waymo $16B Series C+ (Feb 2026) — 9.3–9.4×
- SpaceX $75B Growth / pre-IPO (Apr 2026) — flagged + capped

### Guardrail 2 — Currency check

Asserts that `amount_m` is either `null` (undisclosed) or a positive
number. The Robotnik ingestion template (Rule 6) normalises all amounts
to USD on ingest, with native-currency and FX-rate captured separately
where applicable. Any negative or non-numeric amount triggers a SKIP at
load time, logged in the guardrails file. Currently zero rows trip this
in the v1.1.3 dataset.

### Guardrail 3 — Stage label coverage

Every round must map to either:
1. One of the five RPCI canonical stages (via `STAGE_MAP`), or
2. The `EXCLUDED_ROUNDS` set (out-of-scope rounds explicitly tracked but
   not included in the index)

Any round with a `round` value not in either set is a guardrail 3 failure
and exits the script non-zero. This forces a human triage before the
next ingestion can change the stage enum without an explicit code update.

## Output

JSON: `data/index/private_capital_index.json`

```jsonc
{
  "index_name": "Robotnik Private Capital Index",
  "index_code": "RPCI",
  "base_date": "2025-03-31",
  "base_value": 1000.0,
  "fetched_at": "<ISO timestamp>",
  "method": "5-component composite, 3M trailing window, monthly recalc",
  "components": { ... },                       // component definitions + weights
  "current_month": "2026-04",
  "current_value": 7421.25,
  "current_value_3m_trailing": 3930.31,
  "series": [
    {
      "month": "2024-01",
      "value": 1232.30,                        // composite reading
      "value_3m_trailing": 1232.30,            // 3M smoothed
      "components": {                          // each component normalised to 1000@base
        "capital_deployed": 649.46,
        "deal_count": 1693.88,
        "stage_weighted_activity": 1764.49,
        "round_size_vs_trailing": 553.81,
        "investor_breadth": 1723.79
      },
      "deal_count_raw": 83,                    // raw counts
      "capital_deployed_raw_usd": 3392000000   // raw $ after cap
    },
    ...
  ]
}
```

## Run

```bash
python3 scripts/calculate_private_index.py
```

Produces:
- `data/index/private_capital_index.json` — the index series + components
- `data/index/private_capital_index_guardrails.log` — guardrails (cap flags + stage classification + IPO filter summary)
- `data/index/private_capital_index_ma_audit.log` — M&A include/exclude decision table

## Versioning

The RPCI methodology is locked to this document. Any methodology change
(component weights, stage map, base date, trailing window definition)
requires a new methodology version and a `RPCI vN.N` re-publication of
the series. The output JSON's `method` field tracks the current version
string.

**Current version: RPCI v1.1** (2026-05-21)

### Version history

- **v1.0 (2026-05-14):** initial methodology. IPO (filed) mapped to
  Growth/pre-IPO. M&A blanket-excluded.
- **v1.1 (2026-05-21):** IPO and IPO (filed) both excluded (transition
  events, not private capital). M&A conditional inclusion rule
  introduced — included only when the acquirer is private and in the
  Robotnik universe. `PRIVATE_ACQUIRER_ALLOWLIST` mechanism added for
  in-universe acquirers without fundraising activity (York Space added).
  6M trailing smoothed series added to the output JSON for research
  use; chart continues to publish the monthly point + 3M trailing line
  only. Audit logs split into guardrails + M&A audit for cleaner
  downstream review.
