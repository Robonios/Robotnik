# Robotnik Composite Index — Transform Convergence Inventory

**Purpose.** An explicit, exhaustive list of *every* transformation between raw
vendor data and the published Composite, each with its independent validation.
This is the checklist that tells us we have found the **last** bug, not merely
the latest. Compiled during the MarketStack cutover correctness gate.

**Provisional value under review:** Composite **2,573.22** (+157.3% from base
1000 @ 2025-03-31), current_date **2026-05-29**, 1,255 points, 0 non-trading-day
points, guardrails pass (exit 0).

**Status of this value:** PROVISIONAL pending the human flip decision. It has
*held unchanged* under every validation below — notably it did **not** move when
examined harder (contrast the prior +81.7% which collapsed under the same
scrutiny because Semi was frozen).

---

## Validation instruments (independent of the production code path)

| ID | Instrument | What it proves | Result |
|----|-----------|----------------|--------|
| **A** | **Independent reconstruction** — `scripts/verify_index_reconstruction.py`, a from-scratch second implementation using different internals (dense forward-filled arrays vs. production's incremental dicts) | Production code faithfully implements the methodology (catches *implementation* bugs) | **MATCH** — Δ=0.0000 on all 1,255 points × (composite + 4 sub-indices); identical date sets |
| **B** | **Hand computation** from raw prices, sharing no code with either implementation | The methodology itself yields the value (catches *shared methodology* bugs A can't) | Semi ratio = 2.94084 → 2940.84 (Δ=0.00); Σ(share×sub) = 2573.22 (Δ=0.00) |
| **C** | **Constituent cross-vendor** — MS history vs. independent Yahoo on the largest movers | Underlying split-adjusted prices are real, not artifacts (ASML/RTX-class) | INTC +405%, LRCX +338%, AMAT +210%, KLAC +183%, NVDA +95%, TSM +152%, ASML +143% — **all penny-exact** vs. Yahoo; all MS-sourced (non-circular) |
| **D** | **Base-anchor interrogation** | The 1000-point isn't computed on stale/holiday prices (multiplicative mis-scale) | Norm anchor 2025-03-31 = 98% real coverage; raw base 2021-06-01 = 0 bug-class exclusions |
| **E** | **Stability / determinism** | The value doesn't drift across runs | 3× recompute → bit-identical series (SHA256 stable), 2573.2200 each |
| **F** | **Per-constituent manifest** — `data/markets/cutover_constituent_manifest.json` | Every name traceable: source/currency/FX/freshness | 305 names, 0 stale, 0 missing |

The instrument that previously "passed" the wrong number — **index-level
benchmark comparison** — is explicitly **demoted**: it confirmed both +81.7% and
+157.3%, so it is non-discriminating and is NOT relied on. (Benchmarks remain a
reported context line, not a validation gate.)

---

## Transform inventory (raw vendor data → published index)

### Fetch layer (produces `data/prices/history/*.json`, `all_prices.json`, `benchmarks.json`)

| # | Transform | What it does | Validation | Status |
|---|-----------|--------------|-----------|--------|
| 1 | **Instrument resolution / vendor routing** | MS MIC routing, US-ADR overrides, `MARKETSTACK_UNSUPPORTED`→Yahoo | Manifest (F) + cross-vendor (C); ASML (double-convert), RTX (corrupt), Ibiden (V1-406/raw-JPY) caught & routed | ✅ |
| 2 | **Pagination / range-coverage** | Page-full pagination + loud coverage guard (MS caps `pagination.total` at 1000) | Every history file reaches 2026-05-29; `_assert_range_coverage` guard | ✅ |
| 3 | **Currency conversion** (native→USD, daily FX) | MIC→ccy, Yahoo `<CCY>USD=X` daily, GBp÷100, never-1.0, prior-date fallback | Full-universe raw-currency scan: only Ibiden diverged (now fixed); cross-vendor (C) confirms USD levels | ✅ |
| 4 | **Split adjustment** (price-return, self-computed from `split_factor`, snap-to-boundary) | Walk newest→oldest, accumulate factors, snap to true price-move bar | Boundary tests (AVGO/NVDA/4063 JP date-lag/MNTS reverse/synthetic cumulative) + **cross-vendor penny-match (C)** = agreement with Yahoo's independent split-adjuster | ✅ |
| 5 | **Dividend handling** | Price-return basis ⇒ **no** dividend reinvestment | Uses raw `close` (not `adj_close`); MS-vs-Yahoo `close` penny-match (C) confirms no div-adjustment leak; benchmarks share PR basis | ✅ |
| 6 | **`MAX_LOAD_USD` load guard** | Skip close > 10,000 (raw-currency leak catch) | Necessary but **insufficient alone** — Ibiden 9,915 passed under it; caught instead by reconstruction reality-check | ⚠️ R4 |

### Index layer (`scripts/calculate_index.py`)

| # | Transform | What it does | Validation | Status |
|---|-----------|--------------|-----------|--------|
| 7 | **Eligible filter** | mcap≥$10M, has price, not excluded/quarantined, **not token** (type + sector) | Reconstruction (A) replicates → 282 eligible; token isolation belt-and-suspenders | ✅ |
| 8 | **Trading-day filter** (NEW) | Retain dates with ≥50% eligible real-bar coverage | Coverage histogram: holidays ≤35% vs real ≥79% (wide gap); drops weekends+holidays; reconstruction (A) replicates | ✅ |
| 9 | **Today-injection gating** (NEW/FIX) | Inject a fresh point only when snapshot is genuinely ahead of history; never on wall-clock non-trading days | 2026-05-30 (Sat) NOT added; headline = last trading day 2026-05-29 | ✅ |
| 10 | **Index-side quarantine** (Layer 2) | Reject null/≤0, >5000 USD, >50% single-day swing at injection | Only gates injection; 0 false quarantines this run | ✅ |
| 11 | **Raw backfill base anchor** (2021-06-01) | First trading day ≥(today−1825d) with ≥30% coverage | Base-anchor interrogation (D): **0 existed-but-missing**; was the frozen-Semi bug (2021-05-31 = Memorial Day), now fixed | ✅ |
| 12 | **Capped weights** (5% iterative) | Pin >5%, redistribute proportionally | Reconstruction (A) Δ=0; top names all at 5.00% cap | ✅ |
| 13 | **Sub-index backfill** | Fixed-base weighted return, active-weight normalized, carry-forward | Reconstruction (A) + hand-comp (B) both Δ=0 | ✅ |
| 14 | **20×-median sanity cap** | Clamp sub-series points >20× median | Replicated in (A); not triggered (median ~2k, cap ~40k) | ✅ |
| 15 | **Freshness / carry-forward** | Missing price → last-known; stale carry-forward & flag (§13.6) | Reconstruction (A) replicates ffill exactly | ✅ |
| 16 | **Normalization** (→1000 @ 2025-03-31) | Rescale each sub-index so 2025-03-31 = 1000 | Anchor 98% real (D); exact-match present. `normalise_series` missing-target fallback fragile | ⚠️ R3 |
| 17 | **Composite construction** (Option A) | Per-date mcap-share-weighted average of the 4 equity sub-indices | Reconstruction (A) + hand-comp (B) Δ=0; shares on D2: Semi 50.3 / Robo 42.8 / Space 3.8 / Mat 3.1 | ✅ |
| 18 | **Runtime assertion** | Abort if composite ∉ [min(sub), max(sub)] any date | Holds on all 1,255 points | ✅ |
| 19 | **Publish guardrails** | Block on >25% dod, composite-vs-subindex divergence >5% | Pass (exit 0); **caught the Ibiden +476% materials spike** before this fix | ✅ |

---

## Residual characteristics (design choices / caveats — not blocking bugs)

- **R1 — Fixed-base cohort.** 59 eligible names that IPO'd after 2021-06-01 never
  enter the historical sub-indices (no base price). The index is a 2021-cohort of
  ~223 names. Defensible, but the "282 entities" headline overstates active
  historical constituents. *Recommend:* document, or move to per-constituent
  entry-base so post-2021 listings contribute from their first bar.
- **R2 — Share/level basis mismatch.** The composite weights sectors by the full
  eligible current mcap (incl. post-2021 IPOs) but the sub-index *levels* track
  only the 223-name cohort. Small distortion for sectors with large recent
  entrants. *Recommend:* reconcile cohort between weighting and leveling.
- **R3 — `normalise_series` fragility.** If 2025-03-31 were ever absent, the
  fallback walks to the *last* value (mis-scales the whole series). Currently
  harmless (anchor present at 98%). *Recommend:* fix the fallback to nearest-date.
- **R4 — `MAX_LOAD_USD` insufficiency.** A flat 10k ceiling let Ibiden's 9,915
  raw-JPY through. *Recommend:* per-name plausibility band (e.g., vs. live USD
  price) instead of a single global ceiling.

---

## Verdict

Every transform is enumerated and independently validated; the four residuals
are characterized, not latent. The provisional value **2,573.22** is corroborated
by an independent reconstruction (Δ=0), two hand computations (Δ=0), cross-vendor
constituent data (penny-exact), a clean base anchor, and bit-level determinism —
and it held under all of them. **Recommend making instrument A
(`verify_index_reconstruction.py`) a permanent CI gate** so the two
implementations must always agree on every pipeline run.
