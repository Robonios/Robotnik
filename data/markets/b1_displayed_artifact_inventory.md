# B1 — Displayed/Consumed Artifact Inventory & Status

Workstream B, Step 1. Every artifact the frontend `fetch()`es (or a script consumes to
produce a displayed file), statused against the three "new" baselines:
**(M)** 182-membership · **(P)** MarketStack/Yahoo prices · **(T)** chain-linked methodology.
Frontend pages: index, assets, funding, intelligence(news/research), portfolio, signals,
commodities, thesis, report-1Q26, recreation/tetris. Fetches mapped from `js/{main,assets,funding,nav}.js`.

Legend: ✅ consistent · ⚠ minor/verify · ❌ inconsistent (action) · 🔒 EODHD/Yahoo licensing-adjacent

---

## A. Index / price layer — CONSISTENT (182 + chain-link + MS/Yahoo)
| Artifact | Fetched by | Status | Verdict |
|---|---|---|---|
| `index/summary.json` | main.js | 182 entities, 3221.39, base 1000@2025-03-31, chain-linked; sub: semi 61 / robotics 75 / space / materials | ✅ M·P·T |
| `index/robotnik_index.json` | main.js | 1255-pt chain-linked series, base 2025-03-31 | ✅ T |
| `index/sub_indices.json` | main.js | **4 sectors** (semi/robotics/space/materials) | ✅ but ⚠ **4 vs "6 sub-indices" in CLAUDE.md/docs** — reconcile doc |
| `index/weights.json` | main.js, assets.js | **len=182** | ✅ M (on-membership) |
| `prices/all_prices.json` | main.js | MS+Yahoo+CoinGecko (assembled), 343 rows, 2026-05-30 | ✅ P |
| `prices/benchmarks.json` | main.js | MarketStack PR split-adj, base 2025-03-31 | ✅ P·T |
| `prices/history/{ticker}.json` | main.js | MS+Yahoo merged | ✅ P |
| `index/market_caps.json` | main.js | Yahoo; 2026-05-28 (2d older than prices) | ⚠ minor staleness (weekly mcap cadence) |
| `registries/entity_registry.json` | main.js | drives membership; 108 status=excluded; carries `eodhd_ticker` mapping strings | ✅ functional; ⚠ stale `eodhd_ticker` fields (internal, NOT displayed) |

## B. Retired at A2 — confirm graceful (verified)
| `prices/live.json` | main.js:64 | removed | ✅ graceful (Promise.allSettled + `.ok`) |
| `prices/intraday_index.json` | main.js:1573 | removed | ✅ graceful (try/catch + `!resp.ok`) |

## C. Markets layer — STALE + INCONSISTENT (core B data work)
| Artifact | Fetched by | Status | Verdict |
|---|---|---|---|
| `markets/robotnik_public_markets.json` | index, assets, **nav (site-wide)** | **264 entities (≠182); 61 EXCLUDED names leak; carries EODHD fundamentals (revenue_ttm, revenue_growth_yoy, operating_margin, eps, pe_ratio, forward_pe, ev_ebitda, ps_ratio, pb_ratio); includes tokens; dated 2026-05-28 (pre-purge)** | ❌🔒 **PRIMARY regen** — rebuild on 182 WITHOUT EODHD fundamentals fields, then delete `fundamentals.json` |
| `markets/enrichment_data.json` | assets.js:244 | 239 entities; **57 excluded leak**; qual bottleneck data (risk/customers/suppliers/notes) | ❌ membership-stale → refilter to 182 (producers: `calculate_bottleneck_composite.py`, `enrich_equities.py`) |

## D. Funding / private-capital layer — STATUS TBD (B2 pass)
| `funding/summary.json` | index.html, funding.js | present, no markers | ⚠ status TBD |
| `funding/rounds.json` | funding.js, nav.js | 1244 rounds | ⚠ status TBD (private rounds — not index-membership, but check) |
| `index/private_capital_index.json` (RPCI) | funding.js:462 | base 2025-03-31 (matches index), 40 pts, 2026-05-22 | ⚠ check chain-link/methodology parity in B2 |

## E. Intel layer — separate from index/membership
| `news.json` | main.js | RSS, 150 items, 2026-05-28 | ✅ |
| `filings.json` | main.js:880 | SEC EDGAR | ✅ |
| `reports.json` | main.js:880 | IFR/SEMI/SIA | ✅ |
| `research.json` | main.js:880 (research.html) | **MISSING from tree** (not gitignored; never produced/committed) | ❌ data gap — produce/backfill (`fetch_research.py`); `load()` likely graceful (404→null) |

## F. Displayed TEXT — provenance/counts now FALSE (RENDERING = step-1, flagged here)
| Location | String | Verdict |
|---|---|---|
| `js/main.js:183` | `… · Source: EODHD · Updates daily` (+ "Live (15-min delayed)" tag) | ❌🔒 **LIVE false provenance** — prices are MS/Yahoo |
| `js/assets.js:220` / `assets.html:124` | "Data from EODHD. Fundamentals weekly." (JS-written subtitle) | ❌🔒 **LIVE false provenance** |
| `index.html:242,270` (`ov-universe`,`explainer-count`) | "253" — JS-overwritten by main.js:220-222 | ⚠ static fallback stale; confirm JS sources the canonical 182 |
| `portfolio.html:206` | "253" | ⚠ reconcile |
| `js/main.js:1617` | "EODHD" | ignore — code comment (retired intraday), not displayed |

---

## Open decisions for the regen (need founder call)
1. **Assets "Public Market Universe" count semantics.** The index is **182**. The assets page historically showed **253** (tracked public equities, incl. sub-$10M / excluded). Post-purge, should the assets table display: **(a) the 182 index constituents only**, **(b) 182 + tokens**, or **(c) a broader "tracked public" set** (non-excluded public, ≠ index)? Drives what `robotnik_public_markets` regen includes + the displayed count.
2. **EODHD fundamentals fields on regen.** Drop them entirely (null/remove), or freeze+relabel "as of 2026-04-09 (legacy)" until re-sourced? (Licensing favors removal.)
3. **`sub_indices` = 4 vs docs "6".** Confirm 4 sectors is the intended displayed taxonomy (cross-stack folded, tokens excluded) and update CLAUDE.md/methodology, or restore 6.

## B2–B5 queue
- **B2** per-artifact consistency status — finish the funding/RPCI layer; confirm JS count sources.
- **B3** membership-everywhere + standing guard (excluded-leak guard on RPM/enrichment, like the index parity guard).
- **B4** regenerate stale — RPM (182, no EODHD fundamentals) → delete `fundamentals.json`; enrichment refilter; research backfill; market_caps refresh.
- **B5** cross-artifact reconciliation (counts agree everywhere) → STOP.
