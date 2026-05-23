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
