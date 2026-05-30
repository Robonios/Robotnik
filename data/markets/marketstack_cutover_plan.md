# MarketStack Cutover Plan

**Status:** EXECUTED 2026-05-30. Price/index pipeline cut over to MarketStack+Yahoo (chain-linked, daily-FX, split-adjusted); EODHD off the price path; price-history/live/intraday fetchers archived to `archive/scripts/eodhd/`; EODHD key retained 30 days for rollback. fetch_prices.py kept (defines EQUITIES universe; EODHD main() dormant). Fundamentals/earnings/commodities remain on EODHD (deferred, within key-retention window).

**Prerequisites for cutover start:**
1. ✓ Licence-basis confirmation (MarketStack permits redistribution + display)
2. ✓ Adapter built (`scripts/marketstack_client.py`) with per-country routing
3. ✓ Round 1 + 2 symbology fixes applied — Germany, Japan, UK, Chinese A-share, ADR routing, Frankfurt cross-listings
4. ✓ Override registry populated for unsupported tickers (17 entries → 5.5% of universe)
5. ◯ Stable coverage report (re-run currently in progress; target ≥78% with no further symbology-fixable gaps)
6. ◯ Parallel-run period complete with comparison logs (this document defines the procedure)

## 1. What "cutover" means concretely

After cutover:
- `scripts/fetch_prices.py` no longer runs.
- `scripts/fetch_price_history.py` no longer runs.
- `scripts/fetch_benchmarks.py` continues but uses the MarketStack adapter (no further EODHD calls).
- `scripts/fetch_live_prices.py`, `scripts/fetch_intraday_index.py` deleted (intraday isn't displayed and not part of the product per earlier decision).
- New `scripts/fetch_prices_marketstack.py` becomes the primary EOD price fetcher; produces the same `data/prices/equities.json` shape.
- New `scripts/fetch_price_history_marketstack.py` produces the same `data/prices/history/*.json` per-ticker shape.
- Yahoo (`scripts/fetch_yahoo.py`) remains as the fallback vendor for tickers in `data/registries/data_source_overrides.json`.
- `data/registries/data_source_overrides.json` is the single source of truth for vendor routing.
- GitHub Actions workflow `.github/workflows/fetch-data.yml` swaps the EOD steps from EODHD fetchers to MarketStack fetchers + a Yahoo backfill pass for overridden tickers.

## 2. Parallel-run period (5 trading days)

### Why parallel
Catch silent regressions before they ship: cases where MarketStack returns the wrong instrument, has stale data, or rounds differently than EODHD in a way that propagates into the composite or bottleneck-weighted indexes.

### Mechanic
For each of 5 consecutive trading days:

```
[06:00 UTC]  EODHD baseline pull          → data/prices/_compare/eodhd_YYYY-MM-DD.json
[06:30 UTC]  MarketStack candidate pull   → data/prices/_compare/marketstack_YYYY-MM-DD.json
[07:00 UTC]  Comparison report run        → data/prices/_compare/compare_YYYY-MM-DD.json
```

### Comparison report fields per ticker

| Field | Meaning |
|---|---|
| `ticker` | Internal ticker |
| `eodhd_close` | Today's EODHD close |
| `marketstack_close` | Today's MarketStack close (USD-normalised) |
| `delta_pct` | `(ms - eodhd) / eodhd × 100` |
| `flag` | `OK` (\|delta\| ≤ 2%), `DRIFT` (\|delta\| ≤ 10%), `MAJOR` (>10%) |
| `eodhd_date` / `marketstack_date` | Source dates — different dates means stale snapshot, not real divergence |
| `marketstack_supported` | If false, the value is from Yahoo via override, not from MarketStack |

### Decommission gate criteria

After 5 trading days, the migration is **GO** if:
- ≥99% of EODHD-resolved tickers are also MarketStack-resolved (or have a valid Yahoo override)
- ≥95% of resolved tickers carry `OK` flag (\|delta\| ≤ 2%) across all 5 days
- No `MAJOR` flag persists for 2+ consecutive days (transient delta-vs-EODHD-staleness is fine; persistent is a bug)
- The index recalculation (`calculate_index.py`) produces a composite value within 0.5% of the EODHD-sourced equivalent on each of the 5 days

The migration is **NO-GO** if:
- Override registry grows past 20 entries (6.5% of universe) during the parallel run
- Any MAJOR-flag wrong-instrument issue surfaces that the override registry can't fix
- A new geography is discovered with systematically broken coverage

## 3. Rollback procedure

If a regression surfaces post-cutover:

```bash
# Restore EODHD fetchers
git revert <cutover-commit>

# Re-run the EOD pipeline
python3 scripts/fetch_prices.py
python3 scripts/fetch_price_history.py --refresh
python3 scripts/calculate_index.py
python3 scripts/enrich_equities.py
```

The downstream pipeline (`calculate_index.py`, `enrich_equities.py`, `calculate_bottleneck_composite.py`) is vendor-agnostic — it reads the same `data/prices/*.json` files. So rolling back the fetcher is sufficient; no downstream change is required.

The EODHD API key should remain active for at least 30 days post-cutover as a rollback safety net.

## 4. Decommission steps (after GO decision)

### 4.1 New fetcher scripts (build before cutover)

- `scripts/fetch_prices_marketstack.py` — pulls latest EOD for the universe via `route_for_ticker()`. Skips overridden tickers (delegated to `fetch_yahoo.py`).
- `scripts/fetch_price_history_marketstack.py` — pulls 45-day historical refresh for non-overridden universe; merges with on-disk history.
- `scripts/fetch_yahoo.py` extension — bulk pass for all `data_source_overrides.json` entries with `applies_to_vendors: ["marketstack"]`.

### 4.2 Workflow YAML changes

Swap these EODHD steps:

```yaml
- name: Fetch prices (EODHD + CoinGecko)
  run: python scripts/fetch_prices.py

- name: Refresh price history (EODHD)
  run: python scripts/fetch_price_history.py --refresh
```

…for:

```yaml
- name: Fetch prices (MarketStack + Yahoo overrides + CoinGecko)
  run: python scripts/fetch_prices_marketstack.py && python scripts/fetch_yahoo.py --overrides && python scripts/fetch_prices_tokens.py

- name: Refresh price history (MarketStack + Yahoo overrides)
  run: python scripts/fetch_price_history_marketstack.py --refresh && python scripts/fetch_yahoo.py --history-overrides
```

Same pattern for `fetch_benchmarks.py` (now MarketStack-routed). `fetch_market_caps.py` already uses Yahoo, no change.

### 4.3 Files moved to `archive/scripts/`

- `scripts/fetch_prices.py` → `archive/scripts/eodhd/fetch_prices.py`
- `scripts/fetch_price_history.py` → `archive/scripts/eodhd/fetch_price_history.py`
- `scripts/fetch_live_prices.py` → `archive/scripts/eodhd/fetch_live_prices.py`
- `scripts/fetch_intraday_index.py` → `archive/scripts/eodhd/fetch_intraday_index.py`
- `scripts/fetch_fundamentals.py` → kept (could move to MarketStack later, or to Yahoo)
- `scripts/fetch_earnings_calendar.py` → kept

The archive copy preserves the EODHD code as a rollback reference. Removing entirely deferred to a later cleanup pass once parallel-run logs have ≥30 days of clean operation.

### 4.4 Efficiency wins folded into the cutover

Per earlier audit:
- Drop duplicate `fetch_live_prices` call from the EOD job — saves ~8,700 calls/month.
- Drop intraday SOXX (`fetch_intraday_index.py`) — not displayed, not the product.
- Result: production call volume drops from ~127k/mo (EODHD) to a projected ~25k/mo (MarketStack EOD-only). Well inside Professional 100k limit with 75k headroom for the universe to grow.

## 5. Vendor health monitoring (ongoing)

The `data/registries/data_source_overrides.json` `_meta.vendor_health_signal` is the canary. Audit triggers:

| Trigger | Action |
|---|---|
| Override count > 15 entries (≈5% of universe) | Flag and review. **Currently triggered: 17 entries** — driven by HK + Korean KOSDAQ gaps. |
| Override count > 30 entries (≈10% of universe) | Block new feature work until primary-vendor re-evaluation. |
| Any single new MarketStack `MAJOR` flag persists 5 trading days | Add to overrides; investigate root cause. |
| MarketStack monthly request count exceeds 80k | Investigate inefficient call patterns. |

A monthly `scripts/audit_vendor_health.py` script (build during cutover or shortly after) generates a summary fed into the cutover-status section of the methodology doc.

## 6. Known unresolved gaps to disclose at cutover

Even after Round 2 fixes, these remain MarketStack-unserved and rely on Yahoo:

| Geography | Count | Cause | Remediation status |
|---|---:|---|---|
| Hong Kong | 10 | MarketStack HK feed frozen at 2023-10-09; post-cutoff IPOs absent | Permanent Yahoo override |
| Korean KOSDAQ | 5 | Not licensed on MarketStack | Permanent Yahoo override |
| Taiwan TPEx | 1 | XTAI MIC covers TWSE only | Permanent Yahoo override |
| KRW field cap | 1 (Hanwha) | Vendor-side field-width truncation (same bug as EODHD) | Permanent Yahoo override |
| TBD-country universe entries | 14 | Registry data quality — country tag missing | Registry fix needed (separate workstream) |

The 14 TBD-country entries are a registry hygiene issue, not a vendor coverage issue. Cutover does not require their resolution but should flag them for the next registry audit.

## 7. Decision matrix at end of parallel run

| Outcome | Action |
|---|---|
| ✅ All gate criteria met | Execute decommission steps in 4.x order. PR-review the workflow YAML changes. Cutover commit. Keep EODHD scripts in `archive/scripts/eodhd/` as rollback reference. |
| ⚠ Coverage gate met but ≥3 MAJOR flags persist | Hold cutover. Run round-3 symbology investigation for the new gaps. Decide vendor or re-tag fix. |
| ❌ Override registry exceeded 20 entries | Reconsider primary-vendor choice. Options: continue with MarketStack + larger Yahoo fallback, or evaluate Polygon / Twelve Data for a side-by-side. |

## 8. Timeline (assuming GO at parallel-run end)

| Day | Activity |
|---|---|
| D0 | Coverage stabilisation confirmed (Round 2 re-run output approved) |
| D1 | Build `fetch_prices_marketstack.py`, `fetch_price_history_marketstack.py` |
| D2-D6 | Parallel run (5 trading days); daily comparison logs |
| D7 | GO/NO-GO review |
| D7 (if GO) | Workflow YAML PR, merged after review |
| D8 | First production day on MarketStack; monitor closely |
| D14 | First weekly vendor health audit |
| D30 | EODHD key deactivation review (only after 4 consecutive clean weeks) |

---

This plan stays a draft until coverage stabilisation lands. Update timestamps + the `Status` block once approved.
