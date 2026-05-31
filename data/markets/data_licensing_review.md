# Data-Licensing Review — pre-commercial-launch (counsel-ready)

**Status:** founder-flagged for a legal read. This document states *facts*, not legal
conclusions — terms interpretation is counsel's call. Two market-data vendors with
restrictive redistribution terms have data touching the **DISPLAYED** product surface.
A third vendor (MarketStack) is the confirmed-terms migration target.

**Why now:** before commercial launch. An ETF-issuer's / institutional buyer's diligence
would question vendor-scraped data embedded in a displayed, monetised index. Cheaper to
fix the sourcing now than to re-paper it under diligence pressure.

---

## 1. EODHD — deprecating; stored + displayed exposure

EODHD's non-pro/standard licence forbade **redistribution or public display** of its data.
The API key is being decommissioned (~2-week deadline; Workstream A). Two exposure classes,
independent of the API deadline:

### 1a. Stored raw EODHD data committed to the public GitHub Pages repo — **CLOSED (this commit)**
| Path | Disposition |
|---|---|
| `data/prices/_compare/eodhd_2026-05-29.json` (+ MS/parity siblings) | removed from tree |
| `data/markets/prices/history/` (315 files, ~34M; 276+ EODHD-marked) | removed from tree |
| `data/prices/history/MOG_A.json` (lone EODHD file in served history; Moog = excluded) | removed from tree |
| `data/prices/_history_eodhd_backup/` (349 files, ~51M) | removed from tree; **retained locally, gitignored** as a rollback aid until the 30-day window closes, then delete |

**Residual (lower-priority, flagged):** the same data remains in **git history** (prior commits).
A history rewrite (`git filter-repo`) is riskier than the served-tree removal and does not block
launch — served-tree removal eliminates the *active* GitHub-Pages exposure. Counsel to advise
whether history scrubbing is warranted.

### 1b. Displayed EODHD **fundamentals** — **STILL LIVE → Workstream B (priority)**
`data/markets/fundamentals.json` (EODHD, stale 2026-04-09) → consumed by
`scripts/calculate_metrics.py` → emitted into **`data/markets/robotnik_public_markets.json`**,
which **is displayed** (assets.html per-name + search). So EODHD-derived fundamentals
(revenue / margins / multiples) are **on the live site today.** This is a *licensing* exposure,
not merely a staleness/consistency one. **Close it as part of the EODHD cleanup, not deferred:**
rebuild `robotnik_public_markets.json` **without** the EODHD fundamentals fields (on the
182-membership), **then** delete `fundamentals.json`. Tracked as a B item (see §4).

---

## 2. Yahoo Finance — NEW finding (parallel to EODHD), displayed exposure

Yahoo Finance data carries **restrictive commercial / redistribution terms** — the *same
exposure class as EODHD*. Yahoo currently feeds the displayed index in **two load-bearing roles**
(methodology §14 documents the roles; this is the licensing lens on them):

| Role | Mechanism | Displayed? | Exposure |
|---|---|---|---|
| **~21 override prices** | `fetch_yahoo_overrides.py` merges Yahoo closes for MS-unsupported names into `equities.json` → `all_prices.json` → index + market table | **YES** — in the headline index + displayed prices | direct |
| **Daily FX** | `currency_convert.py` / `fetch_yahoo_daily` pulls daily rates converting *every* native price to USD | **YES** — touches **every** displayed USD price | pervasive |
| Parity guard (validation) | `parity_guard.py` cross-checks MS vs Yahoo | no (internal CI) | low-risk |

**Bounded and addressable** (none are blockers; all have clean-source paths):
- **Internal validation use** (parity guard) — low-risk; internal, not displayed.
- **Daily FX** — re-sourceable from **clean public reference rates** (ECB euro reference rates,
  US Federal Reserve H.10) or a licensed FX feed. Mechanical swap; no methodology change.
- **~21 override names** — need a **clean-terms** price source (MarketStack where it can be
  coaxed to route them, a licensed feed, or exchange-direct). Smallest, most specific gap.

**Can't rule on Yahoo's terms (not a lawyer) → add to the same licence read.** Flagging now,
pre-launch, because this is the one that an external data-diligence pass would catch.

---

## 3. MarketStack — the confirmed-terms target; CoinGecko — out of scope

- **MarketStack:** licence basis confirmed at cutover (Step 0). Primary equities + history +
  benchmarks + (proposed) the surviving commodity ETF. This is the clean-terms home.
- **CoinGecko (tokens):** `tokens.json` is a legacy internal watchlist (`type=="token"`),
  **excluded from every equity index by construction** — not in the displayed index math.
  Separate review if/when tokens are surfaced commercially; not in this index's exposure.

---

## 4. Hand-off to Workstream B (displayed-surface reconciliation)
1. **`robotnik_public_markets.json`** — rebuild WITHOUT EODHD fundamentals fields, on 182-membership; then delete `fundamentals.json` (closes §1b). *Licensing priority, not deferred.*
2. **"Data from EODHD. Fundamentals weekly."** displayed subtitle (assets.html) — now false; fix text.
3. **253 → 182** universe-count reconciliation across displayed views (assets meta, weights/registry).
4. **funding.html / RPCI** (`private_capital_index.json`) + **assets.html "Frontier Assets"** — B1 targets.
5. **Yahoo FX + overrides** clean-source migration (§2) — schedule before commercial launch.

---

## 5. Bottom line
- **Active EODHD stored-data exposure on GitHub Pages: closed** (served tree; git-history residual flagged, non-blocking).
- **Displayed EODHD fundamentals: still live** → B priority (regen-then-delete).
- **Yahoo (overrides + FX): newly flagged, displayed, bounded** → same licence read; clean-source paths identified.
- **Net legal read needed on:** EODHD stored-data history residual + EODHD displayed fundamentals + Yahoo displayed prices/FX. MarketStack is the clean-terms target.
