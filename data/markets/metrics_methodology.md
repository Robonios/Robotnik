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
| 3 | **Robotnik Commodities Concentration Index** | Strategic commodities + critical minerals, weighted by supply-chain concentration | COHORT SETTLED — cohort + ratings + sourcing documented in §11; pending index-computation workstream + feed procurement |
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

- **Commodities**: documented in **§11** (commodity universe definition,
  five-level bottleneck enum, data-sourcing taxonomy, and equity-proxy
  baskets). The concentration-weighting formula itself is deferred to the
  index-computation workstream (see §11.8).
- **Private Shadow**: a future section (or an extension of the existing
  private_capital_index_methodology.md by reference) will cover the
  RPCI-with-bottleneck variant.
- **Total Frontier**: a future section will document inter-feeder weights,
  rebalance rules, and the combined divergence flagging.

(Section numbers in the original plan have shifted: §9 and §10 were assigned
to vendor-coverage and the bottleneck-weighted audit trail respectively;
commodities landed at §11.)

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

---

## 11. Commodities universe — methodology

This section documents the commodities cohort that feeds the **Robotnik
Commodities Concentration Index** (Index 3 of the five-index family, §8.1).
It is the source-of-truth on how the commodity universe was defined, rated,
and priced. It is the commodities analogue of §1–§4 for public equities and
supersedes the placeholder forward-reference in §8.5 (which anticipated a
"§9" before sections 9 and 10 were assigned to vendor-coverage and the
bottleneck-weighted audit trail respectively).

The commodities workstream followed the same discipline as the equity rating
batches: define carefully, surface for review, apply only after approval,
document the limitations honestly. Anti-fabrication rules (§7) carry in full —
`no_public_price` and `UNRATED` are acceptable outcomes and were used where
the public record could not support a defensible call.

### 11.1 Universe definition and scope

The commodities cohort is **56 entries**: 47 core commodities plus 9
borderline v1 inclusions carried at documented confidence levels (Mg, V, Y,
Bi, GOES, Te at MEDIUM/HIGH; Scandium at LOW; Palladium at LOW
frontier-relevance; plus the energy/propulsion narrative tiles). Praseodymium
was consolidated into the single **NdPr oxide** headline; the
Li/Co/Ni/Mn/W headlines carry chemical sub-fields (carbonate/hydroxide,
metal/sulfate, APT/WF6) rather than splitting into separate rows.

**Value-chain placement** (8-tier taxonomy, §11 of the commodities scoping
prompt — Step 2):

| Tier | Name | Count |
|---|---|---:|
| 1 | Upstream Materials | 49 |
| 4 | Fabrication & Manufacturing | 7 |
| **Total** | | **56** |

The 7 Tier-4 placements are engineered substrates and formulated fab
consumables where the engineering — not the raw chemistry — is the product:
SiC substrates, GaN substrates, photoresist (EUV + ArF), CMP slurry,
sputtering targets, synthetic fused silica / EUV mask blanks, and
grain-oriented electrical steel (GOES). The calibration line approved at
Step 2 is **"a discrete chemical or feedstock stays Tier 1 even at fab-grade
purity; engineered structure (substrate, formulated recipe, oriented-grain
steel) becomes Tier 4."** Fab gases (WF6, NF3, NH3, HF, silane), hyperpure
polysilicon, litho-grade neon, and aerospace propellants therefore remain
Tier 1 — consistent with the battery-precursor precedent that keeps
chemically-converted intermediates (battery-grade salts, APT) upstream.
Tungsten's WF6 sub-field is carried under the Tier-1 W parent, not split into
a separate Tier-4 entry (same model as Li carbonate/hydroxide).

### 11.2 Five-level bottleneck enum

Public equities use the **4-level enum** in §3 (CRITICAL / HIGH / MEDIUM /
LOW). Commodities and other private/upstream cohorts use a **5-level enum**
that adds **Pre-commercial** for entities with no functional spot market at
production scale:

| Level | Definition (commodities) | Anchor |
|---|---|---|
| **CRITICAL** | Single-country ≥70% share AND no commercial substitute today AND multi-year qualification path for alternatives. Removal halts/severely degrades stack production within 1–2 quarters. | Dysprosium (China ~99% refining + binding Apr-2025 export controls + no NdFeB substitute). |
| **HIGH** | Significant single-country concentration (~50–70%) OR sole-source on a key sub-field where substitution requires capex outside a hostile jurisdiction. | Gallium (China ~98% primary, but recyclate + ex-China qualification underway). |
| **MEDIUM** | Concentration exists but viable substitution/diversification is within 2–3 year reach. | SiC substrates (concentrated but multi-supplier, capex scaling). |
| **LOW** | Multi-country, fungible, ample substitution; no stack-relevant concentration risk. | Copper (LME-traded, multi-country). |
| **Pre-commercial** | No commercial production at scale; future bottleneck, no current market. | Helium-3 (DOE-allocation byproduct; no spot market). |
| **UNRATED** | Public record too thin OR cohort fit ambiguous; marked rather than guessed. | Scandium (opaque ~25 t/yr market; frontier-stack volume speculative). |

The CRITICAL bar requires **all three** of (≥70% single-country share) + (no
substitute today) + (multi-year qualification). Two-of-three lands at HIGH.
This is the same hostile-jurisdiction + binding-policy discipline used in the
equity batches, applied to supply concentration rather than firm-level
sole-sourcing.

### 11.3 Rating results and verifier discipline

Adversarial verification ran on every CRITICAL and HIGH proposal (24 elevated
reviews). Verifier verdicts: **9 HOLD / 14 DOWNGRADE / 0 UPGRADE / 1
USER-OVERRIDE**. The heavy downgrade ratio reflects strict application of the
three-bar CRITICAL test and the Gallium HIGH anchor — first-pass proposals
over-weighted "concentration alone," and the verifier collapsed several down
a tier.

**Final distribution (post-verifier + founder override):**

| Rating | Count | Share |
|---|---:|---:|
| CRITICAL | 6 | 10.7% |
| HIGH | 7 | 12.5% |
| MEDIUM | 33 | 58.9% |
| LOW | 8 | 14.3% |
| Pre-commercial | 1 | 1.8% |
| UNRATED | 1 | 1.8% |
| **Total** | **56** | **100%** |

- **CRITICAL (6):** Dysprosium, Samarium, Tungsten (APT + WF6), Yttrium,
  Terbium, Antimony.
- **HIGH (7):** Neodymium (NdPr), Manganese (HPMSM), Graphite (anode),
  Magnesium, Gallium, Photoresist (EUV + ArF), Synthetic fused silica / EUV
  mask blanks.

**Founder override — Antimony held at CRITICAL.** The verifier proposed a
downgrade to HIGH (Nov-2025 suspension of the Dec-2024 prohibition; ~18% price
correction; thin Robotics-stack relevance). The founder rejected the
downgrade: the Aug-2024 MOFCOM controls are actively binding, Perpetua (US)
does not reach commercial scale until 2028, and Mandalay (AU) is sub-scale.
The same logic that justifies Dy/Sm at CRITICAL despite paper alternatives —
**current sole-source reality governs the rating, not future alternatives** —
applies to Sb. The Nov-2025 suspension reverts to licensing, not denial, which
remains binding policy weaponization consistent with the CRITICAL anchor. The
override is logged in `proposed_commodities_bottleneck_ratings.json`
(`verifier_verdict: "OVERRIDDEN"`, with rationale) for the audit trail.

**Elevated-density skew is structurally correct.** CRITICAL+HIGH stands at
**13 of 56 (23.2%)** — far above Semi (12%), Robotics (3%), and Space (8%),
and second only to Materials (36%). This is expected, not a calibration
error: supply-chain concentration is the *defining characteristic* of the
upstream commodity cohort, just as it is for Materials. Both sectors sit at
the upstream end of the stack where geopolitical concentration is the norm
rather than the exception. An allocator asking "why are a fifth of your
commodities elevated?" gets the structural answer, not a hand-wave.

### 11.4 Data sourcing — `pricing_status` taxonomy

Every commodity record carries a `pricing_status` field. The four-value enum
records how (and whether) the commodity can be priced:

| Status | Meaning | Count | Share |
|---|---|---:|---:|
| `live_market_price` | Trades on a recognized exchange or transparent global benchmark with daily settled prices. | 11 | 19.6% |
| `exchange_proxy` | No direct trade, but a closely-correlated benchmark/assessment tracks it (often paywalled specialist: Fastmarkets, SMM, Asian Metal, Benchmark). | 22 | 39.3% |
| `equity_proxy_only` | No price feed; exposure is tradable only via the public producer(s). Price discovery happens through an equity basket (§11.7). | 16 | 28.6% |
| `no_public_price` | No public price feed in any form; sold via bilateral contract, allocation, or state-controlled distribution. | 7 | 12.5% |
| **Total** | | **56** | **100%** |

**The structurally important cross-tab — `pricing_status` × rating:**

```
                    CRIT  HIGH   MED   LOW  PRE  UNR  TOTAL
live_market_price      0     0     7     4    0    0     11
exchange_proxy         6     5     9     2    0    0     22
equity_proxy_only      0     2    12     2    0    0     16
no_public_price        0     0     5     0    1    1      7
TOTAL                  6     7    33     8    1    1     56
```

**Zero of the 13 CRITICAL/HIGH commodities sit on a live market price.** All 13
route through paywalled subscription assessments (11 → `exchange_proxy`) or
equity baskets (2 → `equity_proxy_only`: photoresist and EUV mask blanks).
This is the defining data constraint of the commodities universe and an
honest disclosure for the index: the most strategically important commodities
are precisely the ones with the least transparent price discovery, because
concentration and opacity travel together. The index must disclose that its
elevated constituents are priced off paywalled/equity proxies, not exchange
settlement.

### 11.5 Vendor procurement plan

**v1 vendor stack: Fastmarkets MB + Shanghai Metals Market (SMM)** — combined
~$20–40k/yr. This pairing covers 9 of the 13 elevated (CRITICAL/HIGH)
commodities: Fastmarkets carries APT (W), Sb, HPMSM (Mn), Mg, and the
base-metal sulfate spreads; SMM carries Dy, Tb, NdPr, Ga daily FOB-China.
Benchmark Mineral Intelligence (graphite, battery materials, monthly) and
Argus (energy, minor metals) are **deferred to phase 2** — subscribe when
usage signals justify, not before.

**Operating-cost flag for the financial model:** commodity feeds add a new
recurring line item of **~$1.5–3.5k/month (~$20–40k/yr)** that the API and
ETF-licensing unit economics must absorb. This is the first hard
cost-of-goods on the data side beyond the equity vendor (MarketStack) and
should be modeled as such. Phase-2 additions (Benchmark ~$15–25k/yr, Argus
~$20–40k/yr) roughly double it if both are taken.

Until a feed is procured, an `exchange_proxy` commodity is reported with its
documented vendor + feed identifier and a **"tracked, paywalled — not yet
ingested"** status, consistent with the §8.4 "preliminary" gating: the
universe is published with honest source attribution before the live feed is
wired in.

### 11.6 `no_public_price` handling — anti-fabrication

The 7 `no_public_price` commodities are **Neon (litho-grade), Xenon, Krypton,
Hydrazine + MMH/UDMH, N2O4 / MON, Helium-3, and Scandium.** Per the founder
decision, these are **not dropped from the universe.** Each is carried as a
fully-tracked entity with a **null price field** and complete structural
metadata:

- producers / operators
- capacity and production scale (where public)
- policy exposure (export controls, treaty regimes, allocation programs)
- key consumers
- substitution paths
- documented rationale for the null price

This preserves the entity's analytical value (an allocator can see the
bottleneck, the players, and the policy risk) without fabricating a price the
market does not transparently produce. **Forcing a proxy where the proxy is
misleading is itself a fabrication** — the noble gases (Ne/Xe/Kr) were
explicitly held at `no_public_price` rather than relabeled `exchange_proxy`
via Argus, because public retail buyers cannot transact at the
LTA-driven bilateral prices that industrial-gas commentary reports. Calling
that "exchange_proxy" would stretch the category past honesty.

**Scandium** is the fullest expression of the discipline: **UNRATED +
`no_public_price` + metadata-tracked.** No bottleneck rating was forced
(record too thin), no price was invented (no transparent market), and the
entity was preserved in the universe for re-rating when frontier-stack
adoption matures. **Helium-3** is **Pre-commercial + `no_public_price`** —
tracked as a future bottleneck with no current market.

### 11.7 Equity-proxy baskets (revenue-share weighting)

The 16 `equity_proxy_only` commodities (§11.4) have no transparent
commodity price in any form — no exchange contract, no paywalled assessor
print. The only public read on them is the equity of the firms that produce
or consume them. For each, this subsection defines a single **equity-proxy
basket**: a small set of listed constituents whose blended return stands in
as the commodity's "price" everywhere Robotnik computes it.

**What an equity-proxy basket is.** A basket is a fixed list of tickers, each
with (a) a **weight**, (b) an **exposure-purity** flag, and (c) a sourced
share note. The weight follows a single rule — **revenue-share weighting**:
each constituent is sized by its share of the commodity's revenue pie,
normalized to **1.0 across the public constituents**. The rule is chosen as
the first-pass methodology because it is defensible against public 10-K /
annual-report data and reproducible: one documented basket per commodity
means the API, the companion, and Index 3 all compute the same number for
"the price of photoresist."

Two honesty mechanisms travel with every basket and are reported
**separately** from the weight:

- **Exposure purity** (`high` / `medium` / `low` / `negligible`) answers a
  different question than weight does. Weight asks *"how much of the
  commodity does this firm supply?"*; purity asks *"how much of this firm's
  equity actually tracks the commodity?"* A constituent can carry a large
  weight (it dominates supply) yet `negligible` purity (the commodity is a
  rounding-error revenue line, so the stock barely moves with it). The two
  are independent and both are disclosed.
- **The private gap.** Revenue-share weights are normalized over *public*
  constituents only. Where a material share of the commodity sits with
  unlisted or state-owned producers, that share is removed from the
  denominator and documented in the per-basket exclusions. A large private
  gap means the public basket covers only part of the market and the level
  is a **partial proxy**, not a full-market proxy — this directly lowers
  `basket_confidence`.

**`basket_confidence`.** Each commodity carries a per-commodity
`basket_confidence` (HIGH / MEDIUM / LOW) reflecting how clean the underlying
revenue-share data is — a function of (1) public coverage of supply, (2)
exposure purity across constituents, and (3) whether per-company shares are
audited, estimated, or merely qualitative. Per the anti-fabrication rules
(§7), a basket built on estimated or qualitative shares, or one where every
constituent is low/negligible purity, is labelled LOW *even when the
underlying commodity is a clean oligopoly* — confidence describes the proxy,
not the commodity. The distribution across the 16 baskets is **HIGH 1 /
MEDIUM 6 / LOW 9**, skewed low for exactly these reasons: the cleanest
oligopolies tend to have either a private leader or diversified-conglomerate
constituents.

> **First-pass, revisable.** Every basket below is explicitly a first-pass
> construction (§11.7.4). Where no per-company revenue share is published,
> weights are sourced estimates or qualitative rankings, flagged as such, and
> scheduled for v2 revision once cleaner share studies (TECHCET, TrendForce,
> Yole, QYResearch full reports) are obtained.

#### 11.7.1 Per-basket constituents

Baskets are grouped by `basket_confidence`. Within each basket, weights
normalize to 1.0 over the listed public constituents; the private/excluded
players that the normalization removes are summarized in §11.7.3. Exposure
purity is `EP` in the tables (h=high, m=medium, l=low, n=negligible).

---

##### HIGH confidence (1 basket)

**Synthetic fused silica / EUV mask blanks** — Tier 4, rating HIGH. The
cleanest basket in the set: EUV mask blanks are an effective **duopoly of two
public Japanese firms** (Hoya + AGC ≈ 90%+), both directly investable, so the
public basket covers the large majority of supply.

| Ticker | Constituent | Weight | EP | Share note |
|---|---|---:|:--:|---|
| 7741.T | Hoya Corporation | 0.60 | m | Dominant EUV mask-blank leader on industry/Yole consensus (~70%+ of blanks); mask blanks/electronics a major segment, but group also carries a large eyeglass-lens/medical/optics business. |
| 5201.T | AGC Inc. (Asahi Glass) | 0.27 | l | Clear No.2 in EUV blanks (~25–30%); a giant diversified glass/chemicals conglomerate where blanks are a tiny revenue slice — tracks weakly. |
| 4063.T | Shin-Etsu Chemical | 0.08 | n | Added for the broader synthetic-quartz / 193nm-photomask-substrate layer; fused silica is a rounding error in a PVC/wafer/silicone/magnet business. |
| 4042.T | Tosoh Corporation | 0.05 | n | Recognized fused-quartz-glass maker (with Corning/Heraeus/SCHOTT); quartz glass is a small line in a commodity-chemicals/bioscience portfolio. |

_Caveat: a genuine **source conflict** exists on the Hoya/AGC split —
industry/Yole consensus puts Hoya ~70%+ vs AGC ~25–30%, while several
low-quality market-mill reports invert it to AGC ~59% / Hoya ~34%. The
Hoya-leads consensus is adopted; the 60/27 split is rounded/estimated. If the
basket is scoped to EUV blanks only, drop Shin-Etsu/Tosoh and renormalize
Hoya/AGC to ~69/31. Confidence is HIGH-but-not-perfect: both leaders public,
clean ~90%+ coverage, but the exact split is unresolved and only Hoya is even
medium-purity._

---

##### MEDIUM confidence (6 baskets)

**Photoresist (EUV + ArF immersion)** — Tier 4, rating HIGH. Clean,
well-documented oligopoly (top-5 ≈ 80%; EUV top-3 ≈ 90%), but the
~25%-share **leader JSR was delisted June 2024** (JIC tender offer, now
government-fund-owned), so the public basket misses the dominant operator and
is re-normalized over the survivors.

| Ticker | Constituent | Weight | EP | Share note |
|---|---|---:|:--:|---|
| 4186.T | Tokyo Ohka Kogyo (TOK) | 0.50 | h | Total-photoresist ~20–25%; top-2/3 maker, leading EUV resist supplier. Photoresists are TOK's core — the only high-purity public tracker, hence over-weighted. |
| 4063.T | Shin-Etsu Chemical | 0.25 | l | ~10–15%; named in EUV top-3, but resist is a small slice of a PVC/wafer/silicone/magnet giant. |
| 4901.T | Fujifilm Holdings | 0.15 | n | ~8–12%; consistently top-5, but resist is a tiny fraction of a healthcare/imaging/document business. |
| 4005.T | Sumitomo Chemical | 0.10 | n | ~5–8%; smaller EUV/specialty position, negligible within a diversified petrochemicals/agro/pharma portfolio. |

_Underlying shares are estimated (no source gives all four EUV-specific
splits). Because JSR (~25%) is excluded, this public basket
**under-represents the commodity by roughly a quarter** — treat the level as
a partial proxy. Capped at MEDIUM by the private-leader gap plus low-purity
diversified survivors, despite a clean commodity._

**CMP slurry** — Tier 4, rating MEDIUM. Reasonable public coverage (top-5 ≈
64%; several public), with two genuinely high-purity trackers (Entegris,
Fujimi).

| Ticker | Constituent | Weight | EP | Share note |
|---|---|---:|:--:|---|
| ENTG | Entegris (incl. CMC Materials, acq. 2022) | 0.42 | h | Largest public position via CMC (historic slurry leader); est. ~25–30% total slurry. Pure-play semiconductor-materials firm. |
| 5384.T | Fujimi Incorporated | 0.31 | h | Est. ~18–20% slurry; polishing/CMP materials are its core business — high-purity. |
| 4004.T | Resonac Holdings (ex-Showa Denko / Hitachi Chemical) | 0.18 | l | Est. ~10–15% (legacy Hitachi Chemical slurry); small slice of a large diversified chemical/semiconductor-materials group. |
| 281820.KS | KCTech | 0.05 | m | >50% Korea-domestic in CMP equipment **and** slurry, but small global slurry share; revenue split between equipment and electronic materials. |
| 357780.KQ | Soulbrain | 0.04 | l | Named CMP-slurry player but revenue dominated by etchants/electrolytes; slurry is a minor line. (Trades KOSDAQ `.KQ`, correcting the `.KS` suffix in the sourcing table.) |

_The No.1/No.2 slurry player **Versum is private inside Merck KGaA** (MRK.DE),
where slurry purity is negligible; DuPont (~8–10%) is public but
low-purity. Held to MEDIUM by the private gap plus estimated shares._

**Sputtering targets (Ta, Ti, Cu, Co, Ru)** — Tier 4, rating MEDIUM.
Coverage is **much better than the sourcing table assumed** because **JX
Advanced Metals IPO'd on the TSE in March 2025** (ENEOS retains ~42%), making
the dominant leader investable.

| Ticker | Constituent | Weight | EP | Share note |
|---|---|---:|:--:|---|
| 5020.T | JX Advanced Metals | 0.82 | h | Global leader ~60% of semiconductor sputtering targets (Nikkei/Reuters/Wikipedia 2025; the table's "~30%" is outdated); claims world No.1 in Cu/Ta/Ti/W/Co. Now a high-purity chip-materials stock. |
| MTRN | Materion Corporation | 0.15 | m | Leading merchant supplier of specialty targets; single-digit-to-low-teens global share; targets are one line in a broader advanced-materials (incl. beryllium) portfolio. |
| HON | Honeywell Electronic Materials | 0.03 | n | Historic merchant target supplier, but immaterial within Honeywell International; HON is spinning off Advanced Materials (Solstice), which may be the correct v2 vehicle. |

_**Plansee** (a major refractory-metal Ta/W target maker) is **private** —
the main coverage gap. Materion/Honeywell shares are estimated. The dominant
player being public argues borderline-HIGH; held to MEDIUM by the private
Plansee gap and HON's negligible purity._

**SiC substrates** — Tier 4, rating MEDIUM. The strongest *mechanical* logic
in the set (pure-play wafer revenue ≈ ASP × volume, disclosed quarterly);
the four TrendForce-named top-4 are all listed (~82% public coverage).

| Ticker | Constituent | Weight | EP | Share note |
|---|---|---:|:--:|---|
| WOLF | Wolfspeed, Inc. | 0.411 | h | 33.7% of 2024 global SiC-substrate revenue (TrendForce), the single largest; pure-play. **Chapter 11 in 2025** cancelled all legacy equity (~0.0083 reissue ratio) — the post-reorg price series is **discontinuous** and now a distressed-restructuring story. |
| 688275.SS | TanKeBlue Semiconductor | 0.211 | h | 17.3% (TrendForce 2024); largest domestic Chinese supplier, effective pure-play. Newer STAR-Market listing, A-share accessibility frictions. |
| 688234.SS | SICC Co., Ltd. | 0.209 | h | 17.1% (TrendForce); ~80% of SICC's own revenue is SiC substrates. (SICC's own materials claim ~22.8% / world No.2; the lower third-party figure is used for consistency.) |
| COHR | Coherent Corp. | 0.170 | l | 13.9% (TrendForce); SiC is only ~5–6% of revenue (lasers/datacom dominate) and Coherent is spinning out its SiC unit. |

_Weights are TrendForce raw shares (33.7/17.3/17.1/13.9) normalized over the
four public names; sums to ~1.001 by rounding. **Do not splice pre- and
post-Sept-2025 WOLF closes** — the Chapter 11 reset terminates the old
series. The ~18% held by private SK Siltron CSS, captive STMicro/Norstel, and
smaller Chinese names is out of basket._

**Helium (high-purity)** — Tier 1, rating MEDIUM. The four named public
wholesalers genuinely control the large majority of *refined-helium
distribution* (~75–80% top-5, four of five public).

| Ticker | Constituent | Weight | EP | Share note |
|---|---|---:|:--:|---|
| AI.PA | Air Liquide S.A. | 0.28 | l | Co-leading wholesaler (one analysis: ~11.5% specialty-grade); helium unreported within a >EUR27bn gas business. |
| APD | Air Products and Chemicals | 0.28 | l | Co-leader with NA/Asia/Europe purification & liquefaction; small fraction of total revenue. |
| LIN | Linde plc | 0.27 | l | Global sourcing/purification/distribution/recovery; small slice of ~$33bn revenue. |
| 4091.T | Nippon Sanso Holdings (incl. Matheson) | 0.17 | l | Clear fourth, strongest in Japan/Asia and (via Matheson) the US; minor line within a diversified gas business. |

_The four weights are a **soft co-leader ranking, not hard shares** — no
company reports helium as a segment. A very large **crude-production layer is
private/state** (ExxonMobil LaBarge ~20% of world supply, QatarEnergy ~33% by
country, Gazprom ~9–13%, Sonatrach) and is **not** in the wholesale basket.
Iwatani (8133.T) is a public top-5 wholesaler outside the chosen four — a v2
add. Every constituent is low purity; that plus the crude-layer gap caps it
at MEDIUM._

**Liquid Hydrogen** — Tier 1, rating MEDIUM. Strong supply-chain coverage —
Linde (global liquefaction leader ~170 TPD) plus Air Products (largest
merchant-H2, historical US LH2, NASA) — plus one high-purity pure-play.

| Ticker | Constituent | Weight | EP | Share note |
|---|---|---:|:--:|---|
| APD | Air Products and Chemicals | 0.32 | l | World's largest merchant-H2 producer, historical US LH2 leader (four NA plants + 30 TPD Louisiana, Jan 2024), primary NASA LH2 supplier; LH2 sits within a much larger H2/gas business. |
| LIN | Linde plc | 0.30 | l | Global LH2 liquefaction leader (~170 TPD; built most of the world's liquefaction plants); a slice of a diversified gas/engineering business. |
| AI.PA | Air Liquide S.A. | 0.18 | l | Major NA/global LH2 player; smaller footprint than APD/LIN. |
| PLUG | Plug Power Inc. | 0.12 | h | Largest US LH2 *capacity* (40 TPD) and largest LH2 *buyer* — the only near-pure-play H2 name, but green/PEM-electrolytic-focused and pre-profit/going-concern-stressed (~$536m FY2025 operating burn, ~$296m cash, DOE loan guarantee). Weight deliberately held modest so a distressed, differently-driven stock cannot dominate. |
| 4091.T | Nippon Sanso Holdings (incl. Matheson) | 0.08 | l | Smaller participant via Japan/Asia and US (Matheson); minor relative to the leaders. |

_Weights mix **TPD-capacity** (PLUG, APD-Louisiana) and **merchant-share**
(APD, LIN) bases — soft, not clean revenue shares. Unlike helium there is **no
dominant private/state crude layer**; the gap is other public names (Iwatani
8133.T, Air Water 4088.T), which supports MEDIUM rather than LOW._

---

##### LOW confidence (9 baskets)

The nine LOW baskets fall into three failure modes, often overlapping: (a)
**all constituents low/negligible purity** (the industrial/cryogenic gases —
Argon, LOX — and the diversified-conglomerate substrate baskets), (b) **a
private or state leader removed from the denominator** (WF6, NF3, polysilicon,
tantalum, niobium), and (c) **no published per-company share, so weights are
qualitative** (most of this group). Per §7 these are honestly labelled LOW
even where the underlying commodity is concentrated.

**Argon (electronic grade)** — Tier 1, rating LOW. Public UHP-gas coverage is
actually good (~72–75% top-5, four of five public), but argon is a cheap,
abundant air-separation co-product and even 6N/9N grade is a small premium
inside large businesses, so the stocks barely move with it.

| Ticker | Constituent | Weight | EP | Share note |
|---|---|---:|:--:|---|
| AI.PA | Air Liquide S.A. | 0.30 | n | Co-leader of UHP semiconductor gases (Air Liquide + Linde ~35–38%, implying ~18% each); electronic-grade argon specifically is negligible in total revenue. |
| LIN | Linde plc | 0.30 | n | Co-leader via on-site air-separation (e.g. Samsung Pyeongtaek N2/Ar expansion, Apr 2025); negligible argon-specific share of revenue. |
| APD | Air Products and Chemicals | 0.22 | n | Top-5 UHP electronic-gas supplier, third among public names; negligible. |
| 4091.T | Nippon Sanso Holdings (incl. Taiyo Nippon Sanso / Matheson) | 0.18 | l | Top-5; relatively higher electronics weighting via Asian "total gas center" on-site fab supply, still minor. |

_Weights are estimates inferred from UHP-gas studies (no electronic-argon
disclosure exists). Private top-5 **Messer** is excluded. All-negligible
purity + estimated shares ⇒ LOW._

**Liquid Oxygen (LOX)** — Tier 1, rating LOW. Public merchant-oxygen coverage
is good (~75% top-5), but merchant LOX is a commodity air-separation product
and the rocket-propellant slice is tiny relative to medical/steel/industrial
oxygen.

| Ticker | Constituent | Weight | EP | Share note |
|---|---|---:|:--:|---|
| LIN | Linde plc | 0.30 | n | Leading ASU operator (>15% share); named LOX/LN2 supplier to SpaceX Starbase (Mims FL; $100m Brownsville plant); "powered 100+ rocket launches in 2024." Still a commodity line. |
| AI.PA | Air Liquide S.A. | 0.27 | n | Top-3 merchant-oxygen major; broad industrial/aerospace LOX supply. |
| APD | Air Products and Chemicals | 0.26 | n | Top-3 major and long-running NASA LOX/LN2 supplier (Kennedy); rocket-LOX a tiny niche on a commodity O2 business. |
| 4091.T | Nippon Sanso Holdings (incl. Matheson) | 0.17 | n | Smaller top-5 major, strongest in Japan/Asia; minimal US rocket-LOX. |

_Weights inferred from oxygen/ASU studies (no LOX disclosure). Private
**Messer** excluded. Structural risk: **SpaceX began building its own Starbase
ASU in 2025** to self-supply LOX/LN2 — vertical integration that *removes* the
merchant demand this proxy is meant to track. All-negligible purity ⇒ LOW._

**Tungsten Hexafluoride (WF6)** — Tier 1, rating MEDIUM. Concentrated
oligopoly (top-6 ≈ 90%), but **public investability is poor**.

| Ticker | Constituent | Weight | EP | Share note |
|---|---|---:|:--:|---|
| 4047.T | Kanto Denka Kogyo | 0.55 | m | Recognized major WF6 supplier in the Japanese ~25%-of-global bloc; fluorine specialty gases (NF3/WF6/etchants/ClF3) are its core — the purest cleanly-listed WF6 tracker. No published WF6 %. |
| 4004.T | Resonac Holdings (ex-Showa Denko) | 0.45 | l | Recognized high-purity electronic-gas supplier, but WF6 is a small line in a very large diversified group. No published WF6 %. |

_Weights are **qualitative** (no defensible per-company WF6 % was found). The
likely overall leader **SK Specialty is private** inside SK Inc. (old KOSDAQ
036490 delisted Dec 2021; the sourcing table's `036490.KQ` is no longer a
pure-play). Central Glass (4044.T) is a public v2 add. Private leader +
diversified public names + no clean shares ⇒ LOW confidence on a MEDIUM
commodity._

**Nitrogen trifluoride (NF3)** — Tier 1, rating MEDIUM. ~80% Korean-controlled
with decent public Korean coverage (Hyosung, Foosung), but the global No.1 is
private.

| Ticker | Constituent | Weight | EP | Share note |
|---|---|---:|:--:|---|
| 298000.KS | Hyosung Chemical | 0.40 | m | Largest cleanly-listed Korean NF3 specialty-gas play after private SK Specialty; NF3/specialty gas meaningful but not sole (also TPA/PP/films). No clean NF3 %. |
| 093370.KS | Foosung Co., Ltd. | 0.30 | m | Korean fluorine-chemicals maker in the NF3 bloc; fluorine chemistry (NF3, LiPF6 electrolytes) is core but diversified across battery materials. No clean NF3 %. |
| 4047.T | Kanto Denka Kogyo | 0.20 | m | Principal Japanese NF3 producer; fluorine specialty gases are its core. No published NF3 %. |
| 4004.T | Resonac Holdings (ex-Showa Denko) | 0.10 | l | NF3 among its specialty-gas line, but a small line in a very large group. |

_Weights largely **qualitative**. **SK Specialty is private** and the global
No.1 at **>40% share** (old KOSDAQ 036490 delisted Dec 2021) — its removal
means this basket covers **well under half the commodity**. Top-3 ≈ 45%
(QYResearch) but not name-split. Honest LOW._

**Silane (SiH4) / Disilane (Si2H6)** — Tier 1, rating MEDIUM. Only weak
public purity; much silane is captive to private polysilicon makers, and the
"purest" name is distressed.

| Ticker | Constituent | Weight | EP | Share note |
|---|---|---:|:--:|---|
| RECSI.OL | REC Silicon ASA | 0.40 | l | Largest single named silane producer (~12.89%, QYResearch) and most silane-focused public name, but purity **downgraded**: shut Moses Lake polysilicon (Dec 2024/Jan 2025) and pivoted remaining Butte MT output toward **battery-anode** silane over semiconductor grade; distressed micro-cap. |
| LIN | Linde plc | 0.28 | n | Named in the silane top-5 and delivers silane to fabs, but it is negligible in Linde's vast gas revenue; a highly liquid public proxy. |
| AI.PA | Air Liquide S.A. | 0.22 | n | Named in top-5, core electronic-gas major; silane negligible in revenue. |
| 4183.T | Mitsui Chemicals | 0.10 | n | Listed among participants; silane negligible within a large petrochemical/performance-materials portfolio. No clean %. |

_Anchor: QYResearch top-5 ≈ 47%. A large **private/captive Chinese layer**
(Inner Mongolia Xingyang, CNS; China >74% of consumption) sits outside the
basket, and Wacker's silane is captive to its polysilicon. If v2 wants
*semiconductor* silane specifically, REC's weight should be cut further.
Private/captive gap + all-low purity + distressed lead ⇒ LOW._

**GaN substrates** — Tier 4, rating MEDIUM. Public *parents* cover ~79% of the
freestanding-GaN market (top-3 = 78.84%, all three listed), but every
constituent is a giant diversified conglomerate.

| Ticker | Constituent | Weight | EP | Share note |
|---|---|---:|:--:|---|
| 5802.T | Sumitomo Electric Industries | 0.45 | n | Widely regarded #1 freestanding-GaN producer (proprietary low-dislocation HVPE), but **no published single-company %** — weight is a qualitative estimate within the 78.84% cluster. Bulk GaN is a rounding-error line in a ~JPY 4tn conglomerate. |
| 4005.T | Sumitomo Chemical (SCIOCS Company) | 0.30 | n | Top-3 freestanding-GaN/epi supplier via subsidiary SCIOCS; share bundled in the top-3 with no clean split. GaN immaterial to a multi-segment chemicals parent. |
| 4188.T | Mitsubishi Chemical Group | 0.25 | n | Ammonothermal bulk-GaN effort, recognized top-3, but a small/semi-carved-out unit; share not separately published. GaN immaterial to one of the world's largest diversified chemical groups. |

_Intra-basket weights are **qualitative estimates** (Sumitomo Electric >
SCIOCS > Mitsubishi), not defensible percentages. The market is tiny (~$400m,
2024). All-negligible purity + qualitative weights + tiny market ⇒ LOW; the
proxy says *who supplies* GaN, not what it costs._

**Hyperpure polysilicon (semi grade)** — Tier 1, rating MEDIUM. Wacker is a
genuinely strong leader, but a top-2 producer is private and solar-grade
revenue contaminates purity.

| Ticker | Constituent | Weight | EP | Share note |
|---|---|---:|:--:|---|
| WCH.DE | Wacker Chemie AG | 0.60 | m | Recognized global #1 in electronic/semiconductor-grade (11N) polysilicon; largest public pure exposure. Medium purity: Polysilicon is one of several divisions and even within it the **solar-grade** business has historically dominated volume — so the equity carries large non-semi exposure. |
| 4043.T | Tokuyama Corporation | 0.28 | m | World's ~#3 semi-grade producer; JPY 30bn Shunan expansion for sub-3nm purity (2024) + OCI Malaysia JV (~2029). Electronic-materials slice more central than at the GaN conglomerates. |
| 3800.HK | GCL Technology Holdings | 0.12 | l | Emerging Chinese 11N producer (>50% China-domestic share), still small globally; **overwhelmingly a solar-grade/granular-silicon company**, so the equity tracks the oversupplied, China-priced solar-poly cycle — explicitly misleading for semi-grade. |

_Weights are **estimates of relative public-producer rank** (no semi-grade-
specific shares are published). **Hemlock** (Corning/DuPont JV) — the co-#1/#2
producer — is **entirely private**: the single largest coverage gap.
Semi-grade prices are set in confidential LTAs at 10–20× the visible
solar-grade price, so **none of these equities is a tight price proxy**. Treat
as an indicative supply-side composite. Private top-2 gap + estimated shares +
solar-cycle contamination ⇒ LOW._

**Tantalum** — Tier 1, rating MEDIUM. No clean public pure-play; the largest
producers are private or state-owned.

| Ticker | Constituent | Weight | EP | Share note |
|---|---|---:|:--:|---|
| AMG.AS | AMG Critical Materials N.V. | 0.55 | l | Principal listed Ta-exposed name (Mibra Ta2O5 concentrate), a named top-tier supplier, but **repositioned around lithium/vanadium** — Mibra now centers a 130 ktpy spodumene plant using Ta tailings as feedstock, so Ta is a minor, shrinking line. No clean Ta %. |
| PLS.AX | Pilbara Minerals Ltd. | 0.25 | n | Tantalite strictly a **by-product** of Pilgangoora lithium mining; a pure lithium equity with an immaterial Ta credit. Added only for non-Central-African mine-supply representation. |
| 5706.T | Mitsui Mining & Smelting (Mitsui Kinzoku) | 0.20 | n | Named top-4 Ta processor (refining/powder stage), but Ta is a minor line in a large diversified non-ferrous group. |

_Weights are **qualitative** (no public company-level Ta share table exists).
The true leaders are **private/state**: Global Advanced Metals (GAM, ~19% of
pentoxide powder), Taniobis, and Ningxia Orient, plus ~50% of *mine* supply
from informal DRC/Rwanda coltan. The basket captures a minority slice via
stocks that overwhelmingly reflect **lithium**. Low-fidelity proxy only ⇒
LOW._

**Niobium** — Tier 1, rating MEDIUM. Structurally the hardest to proxy: ~77–80%
of global supply is **CBMM, which is private**.

| Ticker | Constituent | Weight | EP | Share note |
|---|---|---:|:--:|---|
| 3993.HK | CMOC Group (China Molybdenum) | 0.68 | n | World's #2 niobium producer (~11% share) and the only public firm that actually mines niobium at scale; but it is a copper-cobalt giant — niobium is a tiny earnings line, so the stock tracks copper/cobalt. |
| 5401.T | Nippon Steel Corp. | 0.11 | n | Holds a passive minority share of CBMM (the ~80% leader) via the 2011 ~15% Japanese-Korean consortium; immaterial to a steelmaker's equity. |
| 005490.KS | POSCO Holdings | 0.11 | n | Passive minority CBMM stake (same 2011 consortium); immaterial to a steel/battery-materials group. |
| 8001.T | ITOCHU Corp. | 0.05 | n | Trading-house exposure linked to the CBMM consortium/offtake; immaterial. Linkage less precisely documented than the steelmakers' 2011 deal. |
| 0267.HK | CITIC Ltd. | 0.05 | n | Passive minority CBMM stake via the 2011 Chinese ~15% consortium; immaterial to a sprawling conglomerate. |

_Weights are **qualitative tokens**, not market shares: CMOC as the only real
public producer, plus four small tokens for passive CBMM equity stakes. Raw
tokens (0.65/0.10/0.10/0.05/0.05) summed to 0.95; **normalized to 1.0 here**
per the normalize-to-1.0 rule. With CBMM (~80%) and private Niobec outside any
tracking equity and every constituent negligible-purity, this is an
**ownership map of niobium, not a price proxy**. CMOC's price is driven by
copper and cobalt. Honest LOW._

#### 11.7.2 The purity problem

`basket_confidence` and rating measure different things, and the gap between
them is concentrated in **exposure purity**. Several baskets sit on
commodities that are genuinely concentrated oligopolies (rating MEDIUM/HIGH)
yet are built almost entirely from **low- or negligible-purity** constituents
— firms for which the commodity is a rounding-error revenue line. These
baskets identify *who supplies* the commodity correctly but **track its price
weakly**, because the equity moves with the firm's dominant unrelated
businesses.

The starkest cases:

- **The industrial/cryogenic gases (Argon, LOX, Helium, Silane).** Argon and
  LOX are built **entirely from `negligible`-purity** constituents — Air
  Liquide, Linde, Air Products and Nippon Sanso, for whom argon and merchant
  oxygen are cheap air-separation co-products buried inside tens of billions
  of dollars of unrelated O2/N2/engineering/electronics revenue. These two
  baskets will essentially **not move with the commodity**; they track the
  broad industrial-gas equity complex. Helium and Silane are marginally better
  (a `low`-purity helium-wholesale read; a single distressed `low`-purity
  silane name) but the same dynamic dominates. This is the clearest "weak
  tracker" cluster and the honest reason all four cryogenic/specialty-gas
  baskets that are gas-major-built sit at LOW.
- **The diversified-conglomerate substrate baskets (GaN substrates).** All
  three GaN constituents are `negligible` purity — Sumitomo Electric,
  Sumitomo Chemical, Mitsubishi Chemical are giant chemical/industrial groups
  where bulk GaN (a ~$400m market) is immaterial. The basket tracks the
  Japanese chemical complex far more than GaN wafer ASPs.
- **Niobium and Tantalum.** Every niobium constituent is `negligible` purity;
  the lead, CMOC, is a copper-cobalt major. Tantalum's lead, AMG, is now a
  lithium story. These baskets reflect **other commodities** (copper/cobalt;
  lithium) more than the named one.

The discipline applied throughout: **a low-purity basket is reported as a
low-purity basket.** Where weight and purity diverge, both are shown so a
consumer can see that a 65%-weight constituent (CMOC in niobium) is
simultaneously a `negligible` tracker — the weight answers supply share, the
purity flag warns that the price signal is contaminated.

#### 11.7.3 Private-player coverage gaps

Revenue-share weights normalize over public constituents, so the size of the
**private/state-held share removed from the denominator** is the second major
driver of low confidence. Where that excluded share is large, the public
basket is a **partial proxy** and the level under-represents the commodity.
The material gaps, by commodity:

| Commodity | Key unlisted / removed share | Effect on basket |
|---|---|---|
| **Tantalum** | **Global Advanced Metals (GAM)** — private, ~19% of pentoxide powder, the leading producer; plus Taniobis (private), Ningxia Orient (state), and ~50% of mine supply from informal DRC/Rwanda coltan | Public basket captures only a minority slice; weights qualitative |
| **Niobium** | **CBMM** — private, ~77–80% of global supply; plus Niobec (private). Only a ~30% CBMM equity stake is held (passively) by listed consortium members | ~88% of the commodity outside any tracking equity — ownership map, not price |
| **Polysilicon (semi)** | **Hemlock** (Corning/DuPont JV) — private, co-#1/#2 semiconductor-grade producer | A top-2 supplier entirely absent from any public basket |
| **WF6** | **SK Specialty** — private subsidiary of SK Inc. (KOSDAQ 036490 delisted Dec 2021), the likely Korean leader | Probable overall leader missing; only investable via diversified holdco |
| **NF3** | **SK Specialty** — private, global No.1 at **>40% share** | Public basket covers well under half the commodity |
| **Photoresist** | **JSR** — delisted June 2024 (JIC tender offer), ~25%-share leader | Public basket under-represents by ~a quarter |
| **CMP slurry** | **Versum** — inside Merck KGaA (MRK.DE), ~10–15% est., negligible purity in the parent | No.1/No.2 slurry player not a usable pure proxy |
| **Sputtering targets** | **Plansee** — private, major refractory-metal (Ta/W) target maker | Refractory-target segment under-covered |
| **GaN substrates** | Mitsubishi's bulk-GaN unit is quasi-internal; the three top-3 firms' *individual* shares are themselves undisclosed inside the parents | Intra-basket weights unverifiable |
| **Helium / LOX / Argon** | **Messer** (private top-5 gas major) across all three; plus helium's crude layer (Exxon/Qatar/Gazprom/Sonatrach) and LOX's SpaceX self-supply ASU | Crude/private layer (helium) or self-integration (LOX) sits outside the merchant basket |
| **Silane** | Private/captive **Chinese** producers (Inner Mongolia Xingyang, CNS; China >74% of consumption); Wacker's captive silane | Majority of consumption effectively non-investable |

The four explicitly called out by the founder brief — **Tantalum/GAM,
Niobium/CBMM, Sputtering/Plansee, and GaN/Mitsubishi-private** — are the
canonical examples: in each, a leading or near-leading producer is unlisted,
so the basket's *normalized* weights describe only the visible public slice.
This is recorded per-basket in the `excluded_private` field of the basket
data so the gap travels with the proxy.

#### 11.7.4 v2 revision notes

Every weight in §11.7.1 is **first-pass and explicitly revisable**. The
revision priority, from thinnest to firmest first-pass basis:

1. **Niobium — structurally the weakest.** Weights are normalized qualitative
   tokens (raw tokens summed to 0.95, normalized to 1.0 here). The deeper
   problem is unfixable publicly: the basket is an ownership map, not a price
   proxy, while CBMM (~80%) is private. The honest v2 may keep niobium
   metadata-only or carry CMOC alone with a documented partial-coverage flag.
2. **Tantalum** — qualitative weights on lithium-dominated stocks; revisit
   once a company-level Ta share table exists (none found). Weakest in the
   set alongside niobium.
3. **The qualitative-share gas baskets (WF6, NF3, Silane).** No defensible
   per-company % was found for any of them; weights are equal-ish/qualitative.
   Revisit once a name-split study (TECHCET / QYResearch full report) is
   obtained. For Silane specifically, decide whether the basket targets
   *semiconductor* or *battery-anode* silane and cut REC's weight if the
   former. Candidate adds: Central Glass (4044.T) for WF6; Mitsui Chemicals
   (4183.T) for NF3.
4. **GaN substrates** — intra-top-3 split (Sumitomo Electric / SCIOCS /
   Mitsubishi) is a qualitative estimate inside the 78.84% cluster; needs a
   published per-company freestanding-GaN share to become defensible.
5. **Polysilicon** — weights are relative-rank estimates; the structural
   Hemlock gap cannot be closed publicly. Flag that all three carry
   solar-grade contamination; consider an explicit "semi-grade indicative,
   not a price feed" label.
6. **Photoresist / CMP slurry / Sputtering / SiC** — cleaner first-pass
   bases (third-party share data exists) but with specific watch items: TOK is
   over-weighted in photoresist as the only high-purity survivor and should be
   rechecked against a post-JSR-delisting share study; consider adding MRK.DE
   (Versum) and DuPont at low weight/low purity to CMP slurry; re-base
   sputtering once HON's Solstice spin-off completes (the spun entity may be
   the correct vehicle); and for SiC, monitor whether the post-Chapter-11
   Wolfspeed series stabilizes enough to remain the 41%-weight anchor, and
   keep the pre-/post-reorg series strictly unspliced.
7. **Synthetic fused silica (the one HIGH)** — resolve the Hoya/AGC source
   conflict if a clean Yole figure becomes available; otherwise retain the
   industry-consensus Hoya-leads split. Decide whether the canonical basket is
   EUV-blanks-only (Hoya/AGC ~69/31) or includes the fused-silica leg
   (Shin-Etsu/Tosoh); add Corning (GLW) at low weight/low purity if the
   fused-silica leg is kept.

Two cross-cutting v2 items apply broadly: (a) **the cryogenic/industrial-gas
trio** (Helium, Argon, LOX, and the gas legs of LH2/Silane) all share the same
four-name gas-major roster and should be reconciled together, including the
Iwatani (8133.T) / Air Water (4088.T) public adds and the Messer private gap;
and (b) several **ticker-suffix and share-figure corrections** already
captured in the basket notes should be propagated to the §11.4 sourcing table
on commit — notably Soulbrain `357780.KQ` (not `.KS`), JX Advanced Metals at
~60% (not ~30%) share, the JSR `4185.T` delisting, and the SK Specialty
`036490` delisting that voids `036490.KQ` as a pure-play.

> **Net.** One HIGH-confidence basket (synthetic fused silica), six MEDIUM,
> and nine LOW. The LOW majority is the honest verdict of the methodology, not
> a defect of execution: the commodities that route to equity proxies do so
> precisely because they have no transparent price, and the same opacity that
> denies them a price feed — private leaders, state producers, fab-LTA
> pricing, commodity co-product economics — also denies their public proxies
> clean revenue-share data. The single documented basket per commodity is the
> canonical definition the API, the companion, and Index 3 compute from; the
> per-basket `basket_confidence`, exposure-purity flags, and private-gap notes
> are shipped alongside it so every consumer sees exactly how hard the proxy
> is working.

### 11.8 Feed into the Commodities Concentration Index (Index 3)

This cohort is the input to **Index 3 — Robotnik Commodities Concentration
Index** (§8.1), currently a PLACEHOLDER pending the index-computation
workstream. This methodology section settles the cohort, ratings, and
pricing; it does **not** build the index (per the scoping constraint "do not
begin commodity-index computation until the cohort is approved"). What §11
establishes for that future build:

- **Concentration weighting input.** The 5-level bottleneck rating is the
  first-pass supply-chain-concentration measure. Whether Index 3 reuses the
  §3 multiplier ladder (4.0 / 2.5 / 1.5 / 1.0) or an explicit concentration
  metric (e.g. supply HHI) is deferred to the index build; the rating
  provides the defensible starting weight either way.
- **Price-series eligibility.** Only commodities with a price path
  (`live_market_price` + `exchange_proxy` + `equity_proxy_only` = **49 of
  56**) can contribute a return series to a priced index. The 7
  `no_public_price` entries are tracked as metadata-only constituents and
  excluded from the priced computation while remaining in the concentration
  map.
- **Coverage gating (§8.4).** Rating coverage within the cohort is **55 / 56
  = 98.2%** (only Scandium UNRATED); priced coverage is **49 / 56 = 87.5%**.
  Both clear the 80% headline-publishable threshold — so Index 3 is *not*
  gated by cohort completeness once built; it is gated only by the
  index-computation workstream itself and by feed procurement (§11.5).
- **Equity-basket consistency.** The single documented basket per
  `equity_proxy_only` commodity (§11.7) is the canonical definition the API,
  the companion, and the index all compute from, so the three surfaces never
  diverge on what "the price of photoresist" means.

### 11.9 Applied on commit (provenance)

Landed in the same commit as this section:

1. **§8.5** — the stale "Commodities: a §9 will document…" forward-reference
   was replaced with a pointer to this §11, and the §8.5 bullet trio reconciled
   to the actual §9/§10 assignments (vendor-coverage / bottleneck-weighted
   audit trail).
2. **§8.1, row 3** — the Commodities Concentration Index status moved from bare
   PLACEHOLDER to "COHORT SETTLED — cohort + ratings + sourcing documented in
   §11; pending index-computation workstream + feed procurement."

3. **`proposed_commodities_data_sourcing.json` ticker/share corrections**
   surfaced by the basket research (§11.7.4), applied to the sourcing JSON in
   this commit (`_corrections_applied` block records them):
   - Soulbrain trades KOSDAQ **`357780.KQ`**, not `357780.KS`.
   - **JX Advanced Metals** holds ~60% of semiconductor sputtering targets,
     not the ~30% the sourcing table assumed (it IPO'd on the TSE Mar-2025,
     ticker `5020.T`).
   - **JSR (`4185.T`) delisted Jun-2024** to JIC — no longer a public
     photoresist proxy; basket re-normalized over survivors.
   - **SK Specialty (`036490`) delisted Dec-2021** — `036490.KQ` is no longer
     a pure-play; WF6/NF3 baskets route around it.
   - **Wolfspeed (`WOLF`)** Chapter 11 reorg (2025) terminates the pre-reorg
     price series — the SiC basket must not splice pre- and post-reorg closes.

---

## 12. Currency normalization — daily-FX conversion (MarketStack migration)

**Introduced:** 2026-05-30, at the EODHD → MarketStack cutover.

### 12.1 What changed and why it is more correct

Index constituents trade in many native currencies; the index is
USD-denominated. Until the MarketStack migration, the pipeline did **not**
convert prices to USD via daily FX:

- The legacy fixed-FX table (`FX_TO_USD`) only converted KRW (at a constant
  rate). Every other non-USD currency (JPY, CNY, EUR, GBP, HKD, TWD, CHF, …)
  was carried at ×1.0 — i.e. **native units treated as USD**.
- This "worked" only because EODHD routed most international names to **US
  ADRs** (already USD). The ADR market bakes in the daily FX move via
  arbitrage, so EODHD's ADR series *implicitly* carried a currency-return
  component — but only for the names it ADR-routed. Non-ADR international
  names (London pence, China A-shares, ASX, SIX, …) were carried as raw local
  units under EODHD too, with **no** currency-return component and an
  incorrect level.

**The fix (`scripts/currency_convert.py`):** all three production price
sources — MarketStack live, MarketStack history, and Yahoo overrides — now
convert native prices to USD using **daily FX** (Yahoo `<CCY>USD=X`,
per-bar at each date's rate; London pence handled per quote convention;
FX cache with most-recent-prior fallback and a hard refusal to ever default a
non-USD currency to 1.0). `calculate_index.py` is unchanged — the conversion
lives entirely in the fetch layer.

**Net correctness statement:** because daily-FX conversion adds the
currency-return component (USD return = local return + FX return) for **every**
international constituent — not just ADR-routed ones — the **post-fix index is
more correct than either prior version**: more correct than EODHD (which
omitted FX for non-ADR international names) and more correct than an unconverted
MarketStack-only feed (which would have omitted FX for *all* international
names and tripped the per-share guardrails).

### 12.2 Validation — index before/after

The legacy/contaminated history (mixed EODHD-ADR-USD and pre-fix
MarketStack-raw-local bars) produced FX-convention discontinuities that
**guardrail-blocked** the index:

| Series | Pre-fix worst day-over-day | Post-fix |
|---|---|---|
| Composite | **+662%** (2026-04-13→14) | swing eliminated |
| Robotics | **+842%** | eliminated |
| Materials | **+916%** | eliminated |

After re-fetching all history through the daily-FX pipeline, the historical
series (2021-05-31 → 2026-05-29) is smooth — maximum day-over-day move
**−13.9%** (the 2021 base-period point), with no FX-boundary swings. Per-name
spot checks against EODHD's genuine USD ADRs match within FX noise (Keyence
$502.98 vs $503; Advantest 0.995) or a clean ADR ratio.

### 12.3 Known follow-up (not a currency defect)

A residual last-day discontinuity arises when the MarketStack **history tail
freshness is uneven** (some tickers' EOD history lags the live snapshot by a
few sessions) and the live today-injection adds constituents not present on the
prior history date. This is a coverage/injection-alignment issue, independent
of currency, and is tracked separately; it must be resolved before the
daily-FX index publishes.

---

## 13. Return basis — price-return, self-computed split adjustment

**Decided:** 2026-05-30, during the MarketStack cutover split-adjustment work.

### 13.1 The basis arc (how we got here)

1. **TR attempted via `adj_close`.** Splits forced an adjusted basis (NVDA/AVGO
   10:1 in 2024 created −90% bars on raw `close`). We first adopted MarketStack
   `adj_close` (split + dividend = total-return) and flipped benchmarks to
   `adjusted_close` to match.
2. **`adj_close` found systemically broken.** A full re-backfill exposed that
   MarketStack's `adj_close` back-adjusts **only one session before the split**,
   leaving earlier bars unadjusted — **~70 names** with residual split cliffs
   (AVGO, LRCX, ISRG, ~20 Japanese splits). It is inconsistent name-to-name and
   cannot be trusted.
3. **Reverted to PRICE-RETURN, self-computed.** The reliable signal is the raw
   `split_factor`. We now self-compute a **split-only** back-adjustment from it
   (`marketstack_client.apply_split_adjustment`) and use raw `close` everywhere
   else. This **shrinks the vendor-trust surface to raw close + split_factor +
   daily FX** — all reliable or self-computed — and eliminates the entire
   dividend-adjustment category along with the broken `adj_close`.

### 13.2 The self-computed split adjustment

`apply_split_adjustment` walks each series newest→oldest, dividing every bar's
OHLC by the cumulative factor of splits that took effect after it. It does NOT
trust the `split_factor` **date** (MarketStack's stamp can lag the actual price
move by a session — e.g. 4063.T: factor 5.0 stamped 2023-03-30 while the price
split on 03-29); instead it **snaps each split to the true boundary** — the bar
carrying the biggest price move in the split's direction. Verified at the
day-before/of/after boundary for AVGO/NVDA (10:1), 4063.T (5:1, date-lag),
a 1:50 reverse split, and a synthetic cumulative (2:1→3:1) — all smooth. Where
no clear price move matches a stamped split it warns loudly and falls back to
the stamp date (never a silent mis-adjustment).

### 13.3 Benchmarks share the PR basis

Benchmarks (`SPY / QQQ / SOXX / ROBO / URTH / IXIC`) are sourced from MarketStack
and run through the **identical** `apply_split_adjustment` (price-return), so the
composite and its benchmarks share one basis — no dividend-differential bias.
SOXX's 2024 3:1 split is the one benchmark split, now correctly smoothed;
indices (IXIC) never split. **Rule of record:** the Robotnik index family is
**price-return**, benchmarked against **price-return** series.

### 13.4 Base-period characteristic (not a defect)

The first session of the series (2021-05-31→06-01) shows a composite vs
weighted-sub-index divergence (~9%) flagged by the guardrail. This is a
**low-coverage base-period edge** — few constituents have data on the very
first day, so the composite and the sector aggregation are computed over
slightly different universes — not a bad data point (all individual movers that
day are <7%). Documented as a base-period characteristic; the series should be
anchored where coverage is adequate rather than suppressing the flag.

### 13.5 Known caveat — freeze published history at go-live

Self-computed split adjustment is still **back-adjusted** (older values re-scale
when a new split occurs), though PR removes the larger dividend drift. **Once the
index is published, historical values must be frozen point-in-time** so a value
an allocator saw on date T stays that value. Not a v1 blocker; go-live hardening.

### 13.6 Stale-constituent policy — carry-forward-and-flag (documented, not silent)

MarketStack's EOD history genuinely lags by up to ~1 week for some exchanges
(China A-shares, Taiwan, Korea). The policy is **carry-forward-and-flag**:

- **Carry-forward:** when a constituent has no price on a date, the index uses
  its most recent prior close (`calculate_index.py`). A stale constituent thus
  contributes ~0 return until it catches up — a small, bounded distortion for a
  ~1-week lag on the (small-weight) names affected.
- **Flag, never silent:** the per-fetch coverage guard warns when a series ends
  >7 days short, and the **per-constituent reconciliation manifest**
  (`data/markets/cutover_constituent_manifest.json`) records every name's
  source, currency, FX rate, freshness-in-days, adjustment basis, and status —
  so the carry-forward is visible and auditable per name.
- **Escalation:** constituents stale beyond tolerance (the 3 names >2yr stale on
  MarketStack — 9868, AUTO NO, KCR FH) are routed to Yahoo (current). Material
  weight + bad data is fixed at source (e.g. RTX → Yahoo), not carried.

Independent (non-circular) validation: top-weighted constituents are checked
MarketStack vs Yahoo vs exchange — not against EODHD alone (which has its own
bugs). This is what caught the ASML routing and RTX corruption faults.
