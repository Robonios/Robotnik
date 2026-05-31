# A1 — EODHD Dependency Audit (Step 0, Workstream A)

**Objective:** get every EODHD dependency off EODHD before the key expires (~2 weeks).
Items feeding **DISPLAYED** website data carry a licensing imperative *on top of* the
deadline. Verified against the working tree (YAML line numbers, archive paths, frontend
fetches, file dates). Where a discovery agent was wrong it is corrected inline + flagged
in §4.

---

## 1. The real set of EODHD data types (enumerated, not assumed)

| # | Data type | Producer | Status |
|---|-----------|----------|--------|
| 1 | Equity EOD prices | `fetch_prices.py` | **DORMANT** — replaced by MarketStack; `main()` behind `__main__`, never invoked |
| 2 | Daily OHLCV history | `archive/scripts/eodhd/fetch_price_history.py` | **ARCHIVED** — live history now MarketStack |
| 3 | Live prices (15-min delayed) | `archive/scripts/eodhd/fetch_live_prices.py` → `live.json` | **ARCHIVED but DISPLAYED** → P1 |
| 4 | Intraday OHLCV (1h + 5-min index) | same archived producer → `intraday.json`, `intraday_index.json` | **ARCHIVED**; `intraday_index.json` fetched by main.js → P1 |
| 5 | **Commodities** (metals via FOREX + ETF proxies) | `scripts/fetch_commodities.py` | **LIVE EODHD CALL** → P2 |
| 6 | **Fundamentals** (mcap/revenue/margins/multiples/earnings) | `scripts/fetch_fundamentals.py` | **LIVE EODHD CALL** → P2 |
| 7 | **Earnings calendar** (90-day forward) | `scripts/fetch_earnings_calendar.py` | **LIVE EODHD CALL** → P2 |
| 8 | Benchmark prices (SPY/IXIC/URTH/QQQ/SOXX/ROBO) | `fetch_benchmarks.py` `fetch_eodhd_daily()` | **DORMANT** — `main()` routes to `fetch_ms_daily()` |

**Not found (not in scope unless confirmed):** dedicated splits/dividends fetchers (splits
handled MarketStack-side via `adj_close`), standalone forex product (FOREX appears only inside
commodities), live/intraday for the displayed core beyond #3–4.

## 2. `fetch_prices.py` runtime check → CLEAN

**Dormant / import-only.** `main()` calls `fetch_eodhd_price()` but is `__main__`-guarded and
never invoked downstream or by the YAML. Imported solely for the **EQUITIES universe constant**,
`ticker_to_eodhd()`, `guess_currency()` — none trigger an API call at import. **Critical-path
EODHD imports: zero** (all 10 critical-path scripts use only MarketStack/Yahoo at runtime).

---

## 3. Migration priority buckets

### P1 — DISPLAYED + EODHD-tainted (deadline + LICENSING — do first)
- **`data/prices/live.json`** — producer archived (`archive/scripts/eodhd/fetch_live_prices.py`),
  **DISPLAYED** on `index.html` + `assets.html` (overlays `all_prices.json` when <2h old;
  `main.js:64` / gate `main.js:115`).
- **`data/prices/intraday_index.json`** — same archived producer; **fetched** by `main.js:1573`
  (render path may be disabled — see Gap #3).

  **Critical nuance:** the producer is **archived and NOT scheduled** (live-prices job removed at
  cutover). So **no new EODHD calls are made for these today** — the exposure is **stale
  committed EODHD-sourced data still shipping in the repo and reachable by the frontend**, not
  ongoing fetches. **Decision needed:** *retire* the live overlay + purge the committed EODHD
  file, **or** *repoint* to a licence-clean intraday source (MarketStack/Yahoo). Per the cutover
  plan (intraday "not the product"), retire is the likely call — but it's displayed, so it's your
  decision.

### P2 — INTERNAL + LIVE EODHD calls (deadline only; these BREAK on expiry)
The **only three scripts still making live EODHD calls** via the active YAML, none displayed:
- **`fetch_fundamentals.py`** → `data/markets/fundamentals.json` (YAML L104, Mondays). *Stale: last_updated 2026-04-09.*
- **`fetch_commodities.py`** → `data/prices/commodities.json` (YAML L111, continue-on-error). *FOREX metals + ETF proxies.*
- **`fetch_earnings_calendar.py`** → `data/markets/earnings_calendar.json` (YAML L118, Mondays, continue-on-error). *Stale: 2026-04-09.*

→ Migrate to a new vendor, or disable, before key expiry.

### P3 — Already clean / no runtime EODHD (no deadline action)
- **Dormant-but-key-loaded:** `fetch_prices.py`, `fetch_benchmarks.py`, `config.py` (loads key, unused).
- **Clean:** all MarketStack/Yahoo scripts, guards, assemblers, test harnesses (EODHD only in docstrings).
- **Frozen historical:** `_history_eodhd_backup/`, `data/markets/prices/history/` (276+ EODHD files),
  `_compare/*`, `_equities_eodhd_backup.json` (actually MarketStack content).

**Hygiene (post-deadline):** strip unused `EODHD_API_KEY` env from YAML L103/110/117; remove unused
key loads in `config.py:25`, `fetch_prices.py`, `fetch_benchmarks.py`.

---

## 4. Gaps / uncertainties (flagged, not guessed)

1. **`live.json` reconciliation (resolved, confirm):** displayed-capable but **not refreshed** (producer
   archived/unscheduled; file dated 2026-05-30). Confirm no *other* mechanism (external cron/manual)
   regenerates it before deciding retire-vs-repoint.
2. **`intraday_index.json` displayed?** `main.js:1573` fetches it but the render path may be disabled —
   one-line UI check needed; treated as P1 conservatively.
3. **Commodities/fundamentals/earnings displayed?** No frontend `fetch()` found → classed **INTERNAL (P2)**.
   Caveat: `commodities.html` + `funding.html` exist; if a future/unmerged page renders them, reclassify to P1.
4. **`data/markets/prices/history/` (276+ EODHD files) vs `data/prices/history/`** — different dirs; the
   *served* history is `data/prices/history/` (MarketStack). Confirm the `markets/` tree isn't read anywhere.
5. **LICENSING on stored data (independent of the API deadline):** `_history_eodhd_backup/`, `_compare/*`,
   `data/markets/prices/history/` contain EODHD data committed to a **public GitHub Pages repo**. If EODHD's
   licence forbids redistribution of *stored* data, their presence is a licensing question separate from the
   fetch deadline. **Flagged for a licence read.**
6. **`fetch_commodities.py` shape:** precious metals via **FOREX pairs** + others via **ETF proxies** — a
   migration must reproduce *both* mechanics (a like-for-like swap may not cover FOREX metal pairs).
   Reconcile against the commodities sourcing plan + `pricing_status` enum (A2/overlap item).

---

## 5. Bottom line
- **Live EODHD calls that break at expiry = exactly 3 scripts** (fundamentals, commodities, earnings — all **internal**, P2).
- **Only displayed EODHD exposure** = the **archived, unscheduled** `live.json` / `intraday_index.json` path (P1 — a stale-data/licensing *decision*, not an active-fetch fix).
- **Displayed core price/index surface** (`all_prices`, `history/{ticker}`, `robotnik_index`, `summary`, `market_caps`, `weights`, `entity_registry`) is **already MarketStack/Yahoo** (P3).
- `fetch_prices.py` confirmed runtime-dormant; critical path has zero EODHD.

*(Bonus for Workstream B: the display agent's full DISPLAYED-artifact list is captured in the workflow output for B1 — incl. a `funding.html`/RPCI surface and an `assets.html` "Frontier Assets" view, and a weights/universe "253" count to reconcile against the new 182-membership.)*

---

## 6. Step-0 A2 execution record

### 6a. Descheduled + archived (commit `0856ca9c`)
- `fetch_fundamentals.py`, `fetch_earnings_calendar.py` → `archive/scripts/eodhd/`; YAML steps removed.
- Retired served stale-EODHD `live.json` / `intraday.json` / `intraday_index.json` (frontend handles absence gracefully — verified).
- EODHD_API_KEY now on a **single** YAML step (the commodities fetcher, pending §6c).

### 6b. Stored-data removal (this commit) — raw EODHD purged from the served public tree
| Target | Action | Note |
|---|---|---|
| `data/prices/_compare/` | removed (tree+disk) | incl. raw `eodhd_2026-05-29.json`; readers = dormant cutover one-offs, not in YAML |
| `data/markets/prices/history/` (315) | removed (tree+disk) | confirmed **zero readers** (served history is `data/prices/history/`) |
| `data/prices/history/MOG_A.json` | removed | lone EODHD file in served history; Moog = `excluded`, not in index |
| `data/markets/earnings_calendar.json` | removed | orphaned (producer archived) |
| `data/prices/_history_eodhd_backup/` (349) | removed from tree, **retained local + gitignored** | rollback aid until 30-day window closes |
| **`data/markets/fundamentals.json`** | **LEFT** | displayed via `robotnik_public_markets.json` → **Workstream B** (regen-then-delete) |

**Flagged, not removed (scope / not approved):** the 4 stale Apr-2 sibling snapshots still under
`data/markets/prices/` (`all_prices.json`, `equities.json`, `history_index.json`, `tokens.json` —
zero readers, same EODHD-era staleness); `data/prices/_equities_eodhd_backup.json` (mislabeled —
actually MarketStack content); dormant cutover scripts `parity_report.py` / `parallel_day.py`.
One-word approval folds any of these into the next removal. Licensing detail → `data_licensing_review.md`.

### 6c. Commodities reconciliation (NOT a straight port — reconciled against the cohort + energy decisions)
The legacy `fetch_commodities.py` (10 EODHD symbols) predates the commodities-cohort and energy
scope calls. Reconciled keep/drop (sources: `proposed_commodities_cohort.md`, `…_data_sourcing.md`):

| Legacy item | Symbol | Cohort verdict | Disposition |
|---|---|---|---|
| Gold | XAUUSD.FOREX | **excluded** (monetary/macro) | DROP |
| Platinum | XPTUSD.FOREX | **excluded** (no distinct frontier use) | DROP |
| Crude WTI | USO.US | **excluded** (macro/OPEC) | DROP |
| Lithium | LIT.US | ETF **replaced** by direct Li carbonate/hydroxide (specialist) | DROP → specialist |
| Rare Earths | REMX.US | ETF **replaced** by underlying Nd/Pr/Dy/Sm (specialist) | DROP → specialist |
| Uranium | URA.US | in-cohort (energy) but **deferred** per scope call | DROP (deferred) |
| Natural Gas | UNG.US | energy bucket (methalox proxy) | DROP |
| Palladium | XPDUSD.FOREX | in-cohort but **minority frontier** (auto-cat dominates); intended source NYMEX PA (live), not ETF | DROP → proper buildout |
| **Silver** | XAGUSD.FOREX | in-cohort + frontier (PV/MLCC/die-attach) but has a **true exchange price** (LBMA/COMEX) → ETF/FOREX = proxy-where-true-price-exists, fails "intended source" test | **DROP** → proper buildout |
| **Copper** | CPER.US | in-cohort + frontier (datacenter/EV/BEOL) but has a **true exchange price** (COMEX/LME) → CPER = proxy-where-true-price-exists, fails "intended source" test | **DROP** → proper buildout |

**FINAL DECISION: DROP ALL 10, no interim fetcher.** Copper fails the "ETF-proxy is the
intended source" test exactly like Silver — both have true exchange prices, so CPER/SLV would be
proxies-where-a-true-price-exists. An interim proxy fetcher for an **internal, not-displayed**
feed (`commodities.json`, no frontend `fetch()`) is a half-measure that would be ripped out when
the proper 56-commodity surface (true prices + specialist sourcing per `…_data_sourcing.md`) is
built. So: the EODHD commodities YAML step is **removed**, `fetch_commodities.py` archived,
`commodities.json` dropped, and commodities sourcing is **deferred to the Concentration Index
build**. This takes **EODHD fully off the live workflow** — the last remaining EODHD touch is the
displayed stale `fundamentals.json` (→ Workstream B: regen-without-EODHD-fields, then delete).
