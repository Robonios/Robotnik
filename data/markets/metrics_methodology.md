# Public Equities Metrics Methodology

Methodology for the per-constituent enrichment pipeline that produces the
API-ready dataset for portfolio analysis. Pipeline:

```
fetch_prices.py / fetch_market_caps.py / fetch_price_history.py
  ↓
calculate_metrics.py        (returns, ATH, sparkline, fundamentals join)
  ↓
enrich_equities.py          (vol, drawdown, momentum, beta, rankings, bottleneck)
calculate_index_metrics.py  (Step 5 — mirror at sub-index + composite level)
calculate_bottleneck_composite.py  (Step 7 — bottleneck-weighted composite)
```

Outputs:
- `data/markets/enriched_equities.json` — consolidated per-constituent record
- `data/markets/coverage_report.json` — per-metric coverage across the universe
- `data/index/index_metrics.json` — composite + sub-index metric blocks
- `data/index/bottleneck_weighted_composite.json` — bottleneck-tilted index
- `data/index/bottleneck_composite_divergence.log` — monthly divergence flags

---

## 1. Universe and data sources

The enrichment script consolidates five canonical sources of truth into one
clean record per equity:

| Source                                       | Provides                                                                       |
|----------------------------------------------|--------------------------------------------------------------------------------|
| `data/prices/equities.json`                  | Live quote, sector tag, EODHD symbol, currency                                 |
| `data/prices/history/*.json`                 | 5Y daily OHLCV per constituent (332 files)                                     |
| `data/prices/benchmarks.json`                | 5Y daily series for SPY, IXIC, URTH, QQQ, SOXX, ROBO                           |
| `data/index/market_caps.json`                | USD-converted market caps                                                      |
| `data/markets/robotnik_public_markets.json`  | PE, EV/EBITDA, FCF, margins, sparkline, ATH, change_24h/7d/30d (from upstream) |
| `data/markets/enrichment_data.json`          | `bottleneck_risk`, key customers/suppliers, qualitative notes (rated subset)   |
| `data/registries/entity_registry.json`       | Canonical `sector`, `subsector`, `value_chain`; `status` (excluded/quarantined) |

**Universe size after gating:** 254 enriched of 304 in `equities.json`. The
50 skipped are `registry.status == "excluded"` — typically delisted,
mismatched, or low-quality entries. See
[classification_change_log.md](classification_change_log.md) for the list.

**Index-eligible universe:** 233 of 254 enriched, after applying
`mcap ≥ $10M` and `sector ≠ Token` (matches the gating in
`calculate_index.py` so divergence figures are like-for-like).

---

## 2. Per-constituent metrics

### Returns (% price change)

For each lookback target the script finds the closest prior trading-day
close within a 5-day window (handles weekends/holidays). When the lookback
exceeds the price history depth, the metric returns null — never extrapolates.

| Field             | Window  | Notes                          |
|-------------------|---------|--------------------------------|
| `return_1m_pct`   | 30 days |                                |
| `return_3m_pct`   | 90 days |                                |
| `return_6m_pct`   | 180 days|                                |
| `return_ytd_pct`  | from Dec 31 prior year |                 |
| `return_1y_pct`   | 365 days|                                |
| `return_3y_pct`   | 3 × 365 days| null if <3Y history        |
| `return_5y_pct`   | 5 × 365 days| null if <5Y history        |

### Volatility (annualised, decimal form)

```
log_return_t   = ln(price_t / price_{t-1})
volatility_ann = stdev(log_returns) × √252
```

Computed over rolling 30D / 90D / 1Y windows of daily log returns. The
output is the decimal form: `volatility_1y_ann = 0.354` means **35.4%**
annualised. Requires at least 10 daily observations in the window; otherwise
null.

### Drawdown

```
peak_t      = max(close_1, …, close_t)
drawdown_t  = (close_t − peak_t) / peak_t × 100   # always ≤ 0
```

| Field                     | Window           |
|---------------------------|------------------|
| `drawdown_current_pct`    | All-time         |
| `drawdown_max_1y_pct`     | Rolling 1Y       |
| `drawdown_max_3y_pct`     | Rolling 3Y       |

### Momentum (risk-adjusted)

```
momentum_3m_risk_adj = return_3m_pct / (volatility_90d_ann × 100)
momentum_6m_risk_adj = return_6m_pct / (volatility_1y_ann  × 100)
```

Unitless. A positive value means positive return per unit of volatility over
the window. Returns null if either numerator or denominator is null/zero.
Not the same as Sharpe ratio (no risk-free rate adjustment) — kept
deliberately simple as a directional signal.

### Beta

OLS slope of constituent log returns regressed on benchmark log returns,
over the last 252 aligned trading days (~1Y). Per the Step 2 benchmark probe
the broad-market betas use:

| Field        | Benchmark                                  | Role                |
|--------------|--------------------------------------------|---------------------|
| `beta_spy`   | S&P 500 (SPY ETF)                          | US large-cap        |
| `beta_ixic`  | NASDAQ Composite Index (IXIC.INDX proper)  | US tech-tilted      |
| `beta_urth`  | iShares MSCI World ETF (URTH.US)           | Global beta         |

QQQ, SOXX, and ROBO are reported as sector references on the benchmark side
but are **not** used as broad-market beta benchmarks. Computing beta against
a sector ETF for an equity *within* that sector amounts to industry-on-itself
correlation and produces a structurally biased ≈1.0 figure that adds no
information. The historical mislabel of QQQ as "NASDAQ Composite proxy" is
corrected — QQQ tracks the NASDAQ-100 (top 100 non-financials), not the
~3,000-constituent Composite, and the two have meaningfully different
constituent mixes especially below the mega-cap layer.

Beta returns null if fewer than 30 aligned observations exist.

### Volume

```
volume_avg_30d = mean(volumes over last 30 calendar days)
volume_avg_90d = mean(volumes over last 90 calendar days)
```

Sourced from the same OHLCV history files. Native volume units preserved
(no FX conversion — comparable within ticker, not across tickers without
mcap normalisation).

---

## 3. Bottleneck rating and multiplier

### 4-level public enum

The equity-side bottleneck rating uses 4 levels (Critical / High / Medium /
Low). The 5-level private enum (Critical / High / Medium / Low /
Pre-commercial) collapses to the 4-level form when joined to public assets:
public companies are revenue-generating and cannot qualify for
Pre-commercial.

### Bottleneck enum mapping

| Public (equity) enum | Private (round) enum | Mapping action  |
|----------------------|----------------------|-----------------|
| `CRITICAL`           | `Critical`           | direct          |
| `HIGH`               | `High`               | direct          |
| `MEDIUM`             | `Medium`             | direct          |
| `LOW`                | `Low`                | direct          |
| (n/a)                | `Pre-commercial`     | private-only — never appears in public dataset |

When joining a public sub-index to a private sector heat-map, the
`Pre-commercial` bucket is left out of the join: it represents company-level
risk for a pre-revenue startup and has no analogue in the public market.

### Multiplier values (v1.0)

| Rating    | Multiplier |
|-----------|-----------:|
| CRITICAL  |       4.0  |
| HIGH      |       2.5  |
| MEDIUM    |       1.5  |
| LOW       |       1.0  |
| UNRATED   |       1.0  |

**These multipliers are a deliberate analytical choice, not empirically
derived constants.** They encode a thesis about bottleneck severity:

- The CRITICAL → HIGH step (4.0 → 2.5, a 38% drop) is intentionally large.
  The two are categorically different — CRITICAL means *no viable
  substitute exists* (ASML's EUV monopoly), while HIGH means *a costly
  substitute is available but requires multi-quarter switching*. Encoding
  this as a linear 4 → 3 step would understate the severity gap.
- HIGH → MEDIUM (2.5 → 1.5) and MEDIUM → LOW (1.5 → 1.0) are smaller because
  those steps are more gradient than categorical (degrees of substitutability).
- UNRATED defaults to **1.0** (no amplification, conservative). With 75% of
  the eligible universe unrated at v1.0, this matters: any non-1.0 default
  would silently bias the index.

The values are **revisable**. The methodology should be re-examined as:
- Rating coverage closes (towards the 80% headline threshold).
- Empirical correlation between rating and stress-period drawdown can be
  measured (currently insufficient sample, especially in CRITICAL).
- Stakeholders provide pushback on specific encodings.

---

## 4. Bottleneck-weighted composite (v1.0 — preliminary)

Pattern A multiplicative tilt applied to the same 233-entity eligible
universe as the mcap composite. Universe parity is essential — the
divergence flag would otherwise reflect differing universes, not the tilt.

```
raw_weight_i      = market_cap_i × multiplier(bottleneck_i)
preliminary_w_i   = raw_weight_i / Σ raw_weight
weight_i          = 5% cap with proportional excess redistribution
```

The 5% cap is **retained** for parity with the mcap composite. Without it,
the largest amplified mega-cap (NVDA × 2.5 = ~13T effective) would dominate
the entire series — measuring "NVDA's path" rather than "bottleneck-amplified
breadth". The cap dampens the tilt but preserves the divergence signal as a
breadth measure rather than a single-name measure.

**Important consequence:** the cap partially mutes the tilt precisely where
it would be largest. ASML (CRITICAL ×4.0), NVDA (HIGH ×2.5), TSM (HIGH ×2.5),
and ARM (HIGH ×2.5) all hit the 5% ceiling under current weights — their
raw amplified weights exceed 5%, so the cap-redistribution step recovers
those excess weights and spreads them across uncapped constituents (mostly
unrated). The v1.0 index is therefore best read as **"tilt within the cap
constraint"**, not pure multiplicative tilt. A name's bottleneck rating
amplifies its position only up to the 5% ceiling; beyond that, the
amplification flows through to the rest of the universe as redistributed
weight. v1.1 may experiment with relaxing or removing the cap to quantify
how much signal the parity constraint costs.

### Honest framing — rated-subset bias

> ⚠ **This is a preliminary, directional-signal metric, not a headline figure.**
> Only **24.9%** of the eligible universe carries a bottleneck rating at v1.0
> (58 of 233 eligible constituents — see distribution in
> [classification_change_log.md](classification_change_log.md)). The remaining
> 175 unrated constituents are treated as `multiplier = 1.0`, which means
> the index is reading the **rated subset's** concentration, not the
> **universe's** concentration. The headline threshold is rating coverage
> ≥ 80%. Until then, the bottleneck-weighted composite is reported alongside
> the mcap composite as a directional signal only; it is not a publishable
> alternative headline.

This caveat is non-optional and must accompany any external citation of the
v1.0 figure. It is the difference between a defensible preliminary metric
and a misleading one.

### Divergence flagging

Monthly average of `(bw_value − mcap_value) / mcap_value × 100` is flagged
when `|avg| ≥ 5.0%`. The threshold mirrors the existing Composite-vs-
subindices guardrail in `calculate_index.py`.

Read the v1.0 divergence series with care:
- **Pre-2025-03 (negative divergence):** the bottleneck-weighted version
  sits *below* the mcap composite. This isn't underperformance per se —
  both series are normalised to 1000 on 2025-03-31, so a pre-base divergence
  reflects different historical paths into the base date, not different
  forward returns.
- **Post-2025-03 (positive, growing to ≈5–6% by late 2025):** the tilt is
  currently *adding* to returns, consistent with bottleneck-amplified
  positions (NVDA, ASML, TSM, ARM) outperforming the broad mcap-weighted
  basket during this window.

### Methodology version history

| Version | Date       | Change                                                    |
|---------|------------|-----------------------------------------------------------|
| 1.0     | 2026-05-23 | Initial build. Pattern A multiplicative tilt, multipliers 4.0/2.5/1.5/1.0, 5% cap, 233-entity eligible universe, 24.9% rating coverage. Preliminary status. |

### Future revisions (logged for tracking)

- **v1.1 — bottleneck-weighted sub-indices.** Deferred until each sub-index
  achieves ≥80% rating coverage (Robotics and Semiconductor are closest;
  Space and Materials need substantial rating work).
- **Multiplier calibration.** Once a stress-period drawdown dataset exists,
  test whether the 4.0/2.5/1.5/1.0 encoding survives empirical correlation
  with downside-deviation behaviour.
- **Cap relaxation experiment.** Test a no-cap or 10% cap variant in a
  side-by-side comparison to quantify exactly how much the 5% cap is
  dampening the tilt signal.

---

## 5. Cross-sectional rankings

For each metric below, every constituent receives within-sector and
within-subsector rank and percentile. Sector and subsector rankings are
computed independently. Buckets with fewer than 3 rated members are
skipped (rankings in tiny universes are noise).

| Metric                  | Direction         |
|-------------------------|-------------------|
| `return_1y_pct`         | higher is better  |
| `return_3y_pct`         | higher is better  |
| `volatility_1y_ann`     | lower is better   |
| `drawdown_max_1y_pct`   | higher (less neg) |
| `beta_spy`              | lower is better   |
| `momentum_3m_risk_adj`  | higher is better  |

Percentile is `(N − rank) / (N − 1) × 100`, so the top performer is 100.0
and the worst is 0.0. Rankings are stored under each constituent's
`rankings` block.

---

## 6. Data completeness flags

Per-constituent flag based on history span:

| Flag       | History span | Implication                                |
|------------|--------------|--------------------------------------------|
| `full`     | ≥ ~5Y        | All metrics computable                     |
| `partial`  | ≥ ~3Y        | 5Y returns nulled                          |
| `minimal`  | ≥ ~1Y        | 3Y + 5Y returns/drawdowns nulled           |
| `thin`     | < 1Y         | Only 30D and YTD-scale metrics meaningful  |
| `missing`  | no history   | All derived metrics nulled                 |

Universe-level coverage report at `data/markets/coverage_report.json`.
**v1.0 snapshot:** 209 full, 15 partial, 16 minimal, 14 thin, 0 missing.

The coverage report carries:
- `data_completeness_members` — named list of every constituent in each
  bucket, sorted by `first_history_date` descending (newest IPOs / shortest
  histories surface first). This is the honest disclosure tool: API docs
  citing null-metric coverage should lift the head of `minimal` and
  `partial` to show "these are the recent IPOs / late-listed names driving
  it" (Voyager Technologies, Karman Holdings, Astera Labs, ARM, Serve
  Robotics, etc.). The `thin` bucket additionally captures international
  tickers where the price-history fetcher has not yet populated a file
  (upstream pipeline gap, not a constituent issue).
- `metric_null_members` — per-metric named list of every constituent with
  a null value for that metric, grouped by sector. Lets a consumer query
  "which constituents are missing `return_5y_pct`?" and get a sector-sorted
  answer immediately.

---

## 7. Null handling — anti-fabrication discipline

The pipeline never extrapolates, interpolates, or fabricates values to
inflate coverage figures:

- Beta requires ≥30 aligned daily observations; otherwise null.
- Volatility requires ≥10 daily observations; otherwise null.
- Drawdown requires ≥5 daily observations in the window; otherwise null.
- Each return lookback walks back ≤5 days for nearest prior trading day; if
  none exists, the return is null.

A null is more informative than a fabricated value. The coverage report
discloses non-null counts by metric so downstream consumers can decide
which metrics meet their threshold.

---

## 8. Robotnik Index Family — five-index scope (placeholder section)

This section formalises the planned index family. Three of the five indexes
exist today (sections 4 and 5 above plus the production Composite); two are
placeholders for build-out as their underlying rating cohorts complete.

### 8.1 The five indexes

| # | Index | Built from | Status |
|---|---|---|---|
| 1 | **Robotnik Composite Index** | Public equities, mcap-weighted, 5% cap | LIVE (calculate_index.py) |
| 2 | **Robotnik Bottleneck-Weighted Composite** | Public equities, mcap × bottleneck-multiplier, 5% cap | LIVE PRELIMINARY (calculate_bottleneck_composite.py, gated on ≥80% rating coverage for headline status) |
| 3 | **Robotnik Commodities Concentration Index** | Strategic commodities + critical minerals, weighted by supply-chain concentration | PLACEHOLDER — depends on Commodities scoping workstream + commodities bottleneck ratings |
| 4 | **Robotnik Private Shadow Index** | Private rounds dataset, sector-weighted capital deployment | PLACEHOLDER — depends on RPCI methodology extension + private-company bottleneck ratings |
| 5 | **Robotnik Total Frontier Composite** | Weighted combination of indexes 1–4 above | PLACEHOLDER — depends on all four feeders existing |

### 8.2 Why five, not one

Each index measures a different layer of the frontier stack and produces a
different signal for the consumer:

- **Composite** → broad public-market exposure to the frontier stack.
  Answers "where is the public-market money on robotics + semiconductors +
  space + materials right now?".
- **Bottleneck-Weighted** → bottleneck-tilted public exposure. Diverges from
  Composite when amplification-rated names (Critical/High) move
  independently of broad mcap-weighted breadth. The divergence flag IS the
  signal.
- **Commodities Concentration** → upstream feedstock risk. Measures how
  exposed the frontier stack is to commodity-supply concentration (e.g.
  rare-earth processing, lithium refining, gallium, neon). Different
  duration / risk profile than equities.
- **Private Shadow** → forward-looking VC funding signal. Captures sector
  capital deployment ahead of public-market repricing (RPCI v1.x is the
  working iteration). Different lead-lag relationship than the composite.
- **Total Frontier Composite** → cross-asset summary. The integrated
  number for a single allocator dashboard, combining the four feeders with
  documented weights. Resists collapse into any single sub-signal.

### 8.3 Sequencing

Build order (gating dependencies):

1. **Composite + Bottleneck-Weighted** — live; coverage closes as rating
   batches complete (Semi done, Robotics done, Space next, Materials after).
2. **Commodities Concentration** — depends on the Commodities scoping
   workstream (separate prompt) producing a defined commodity universe + a
   bottleneck-rating extension for commodities.
3. **Private Shadow** — RPCI v1.x already covers the funding signal;
   extension to incorporate per-round bottleneck ratings is gated on
   private-company bottleneck rating coverage.
4. **Total Frontier Composite** — built only after 1–3 are stable. Weights
   between feeders TBD; provisional plan is equal-weight 25%/25%/25%/25%
   with annual rebalance, subject to revision based on observed inter-
   index correlation.

### 8.4 Universe gating across the family

The rule that headline-publishable status requires ≥80% rating coverage
within the relevant cohort applies to all five indexes:

- Index 1 (Composite) — no rating requirement (uses raw mcap weights).
- Index 2 (Bottleneck-Weighted) — gated on equity-bottleneck coverage (currently 34%).
- Index 3 (Commodities) — gated on commodity-bottleneck coverage (currently 0%).
- Index 4 (Private Shadow) — gated on private-round bottleneck coverage (currently 0%).
- Index 5 (Total) — gated on all four feeders being headline-publishable.

Until each gate clears, the index is reported with the same "preliminary —
directional signal only" framing as the current Bottleneck-Weighted Composite.

### 8.5 What changes in this doc as the family fills out

This section is a placeholder. As each placeholder index becomes real:

- **Commodities**: a §9 will document the commodity universe definition,
  concentration weighting formula, and source data.
- **Private Shadow**: §10 (or extend the existing private_capital_index_methodology.md
  by reference) covers the RPCI-with-bottleneck variant.
- **Total Frontier**: §11 documents inter-feeder weights, rebalance rules, and
  the combined divergence flagging.

The placeholder framing here exists so the methodology doc can be cited as
the source-of-truth on the index family structure even before all five
indexes are operational.

---

## 9. Vendor coverage ceiling (post-Round-3 measurement)

The Robotnik universe's realistic resolution ceiling with **MarketStack as
primary vendor** sits at **~95–97% served** (MarketStack direct + Yahoo
override via `data/registries/data_source_overrides.json`). The remaining
3–5% gap is structural:

- Hong Kong feed frozen at 2023-10-09 (10 entries) — routed to Yahoo as
  permanent override
- Korean KOSDAQ + small-cap names absent from MarketStack catalogue (5
  entries) — Yahoo override
- Taiwan TPEx (1 entry — XTAI MIC covers TWSE main board only) — Yahoo
- Post-2024 letter-suffix Japan IPOs (464A Tokyo Metro, 290A Kioxia) — Yahoo
- Andritz / Wiener Börse (1 entry — MarketStack does not carry XWBO) — Yahoo
- TBD-country registry entries (13 entries) — registry hygiene issue, not
  vendor coverage
- KRW field-cap on Hanwha (1 entry, same bug present in both EODHD and
  MarketStack) — Yahoo

**Override count is monitored as a vendor-health signal** per the
`_meta.vendor_health_signal` block of the overrides registry. Triggers:

| Override count | Action |
|---|---|
| ≤ 15 entries (≈5%) | Normal — no action |
| 15–25 entries (≈5–8%) | Flag and review; cause must be documented per-entry. Current state. |
| 25–35 entries (≈8–11%) | Investigate primary-vendor alternatives in parallel; do not block new feature work |
| > 35 entries (>11%) | Block new feature work until primary-vendor re-evaluation |

Re-measure at each cutover-relevant change and at every quarterly registry
audit. The methodology document is updated when the override count crosses
a threshold or when a new vendor-coverage-pattern surfaces (e.g. a new
country joins MARKETSTACK_UNSUPPORTED).

---

## 10. Bottleneck-Weighted Composite — coverage milestones and audit trail

This section captures the numerical evolution of the bottleneck-weighted
composite as rating coverage expands. The audit trail matters at index
licensing — allocators will ask "how did this index evolve as your rating
coverage grew, and at what coverage level did it stabilise?".

### 10.1 Headline coverage thresholds

Two coverage figures matter:

- **Universe-wide coverage** (n_rated / n_total_registry, currently 240 / 566 = 42%):
  Includes private companies, tokens, materials companies not in the public
  universe, and other non-equity rows. This is the figure cited in §4 of
  the methodology and in the doc-wide "preliminary / not headline-publishable
  until ≥80%" framing.

- **Equities-only coverage** (n_rated_in_eligible / n_eligible_for_composite,
  currently 210 / 233 = **90.1%**): Only the public-equity subset that the
  bottleneck-weighted composite actually reads from. This is the headline
  figure for the licensable index. **At 90.1%, the equities composite is
  past the 80% threshold and graduates from preliminary to publishable
  status** for the equities-only product, while the broader cross-asset
  methodology framing in §4 continues to disclose the universe-wide gap.

The distinction has been added to the headline framing in §4 going forward.

### 10.2 Numerical evolution — pre- vs post-batch regen

The bottleneck-weighted composite was first computed against 58 rated
entities (24.9% eligible coverage). After all four sector batches
(Semi/Robotics/Space/Materials) plus the 600111 CNRE consolidation,
coverage reaches 210/233 = 90.1% eligible. The composite shifts as follows
on the common-date baseline 2026-05-23:

| Snapshot | Coverage | BW level | Mcap level | Divergence (BW − mcap)/mcap |
|---|---:|---:|---:|---:|
| Pre-regen (prelim) | 24.9% | 2,766.13 | 2,690.01 | +2.83% |
| Post-regen (publishable equities) | 90.1% | 2,751.75 | 2,690.01 | +2.30% |
| Δ | +65.2 pts | −14.38 (−0.52%) | (no change) | −0.53 pp |

**Direction:** as coverage expanded, the bottleneck-weighted composite
*tightened* its divergence vs the mcap-weighted composite (from +2.83%
to +2.30%). This is the honest result — at 90% coverage, the rating
distribution starts to resemble broader market structure, so the
amplification of a few CRITICAL/HIGH constituents is partially offset by
the dilution of newly-added MEDIUM (×1.5) and LOW (×1.0) constituents.

The expansion did NOT fabricate divergence; if anything, it removed
some of the artificial concentration the preliminary 58-name set carried.
This is the kind of result that survives allocator scrutiny.

### 10.3 Constituent composition at 90.1% coverage

| Multiplier tier | Pre-regen count (58 rated) | Post-regen count (210 rated) | Δ |
|---|---:|---:|---:|
| CRITICAL ×4.0 | 2 | 3 | +1 (Soitec added; CNRE 600111 consolidated under CRITICAL) |
| HIGH ×2.5 | 7 | 20 | +13 (Materials added 11 + Robotics 2 + Space 2) |
| MEDIUM ×1.5 | 16 | 69 | +53 (Semi 22 + Robotics 27 + Space 7 + Materials 9, net of overlaps) |
| LOW ×1.0 | 33 | 118 | +85 (LOW dominates the breadth pickup) |
| UNRATED ×1.0 | 175 | 23 | −152 |

The CRITICAL+HIGH tier now stands at 23 of 233 eligible constituents
(9.9% of the index by count, before the 5% cap), versus 9 (3.9%) in the
preliminary run.

### 10.4 What this changes for downstream

- The bottleneck-weighted composite output is now **publishable as the
  Robotnik equities-only product** rather than directional-signal only.
  The methodology framing in §4 should disclose the dual coverage state:
  equities (publishable) vs universe-wide (still preliminary pending
  commodities + private cohort ratings).
- The composite vs mcap divergence flagging continues at the same 5%
  monthly-average threshold. 35 months flagged across the full 40-month
  series vs 36 in the preliminary run — calibration window (2023) drives
  most of the flagging, full-confidence post-2025 stays at +2-5%.
- The divergence series is a meaningful signal even at the post-regen
  number: the bottleneck-amplified subset is currently outperforming the
  mcap-weighted basket by a documentable +2.3% (recent days). That's the
  thesis paying off in real numbers.
