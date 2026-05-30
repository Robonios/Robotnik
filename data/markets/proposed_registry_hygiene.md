# Workstream A — Registry Hygiene (APPLIED 2026-05-30)

**Status:** APPLIED. A1/A2/A3 approved; A4/A5 revised by founder and applied.

**Resolution (revised A4/A5):**
- **A5 — ADD `token` type** to the registry enum (not just observe). All 43
  tokens reclassified `type="public"` → `type="token"`. This is the isolation
  mechanism; both index calculators now filter on type (+ sector fallback).
  See `token_isolation_policy.md`.
- **A4 — KEEP all tokens** (no deletions, incl. ATNM/BREW). Added
  `activity_status` (ATNM=dead, BREW=low, SLC=live, 40 unassessed). Tokens are
  a legacy content/research watchlist, never product-functional, never
  displayed customer-facing.
- **A1/A2/A3 — applied as proposed below** (14 countries, STMPA→France,
  LMT/NOC→US, 3 duplicate consolidations with data migration).
- **Mandatory aggregation check — PASSED.** No token leaks into the composite,
  bottleneck-weighted composite, or equity-rating coverage (0/43 pass the
  hardened filter). Both calculators hardened to filter `type=="token"`.

Original proposal retained below for the audit trail.

---

**Status (original):** Proposal. NOTHING applied yet. STOP for review.

Scope: close known registry-quality issues across `scripts/fetch_prices.py`
(the `EQUITIES` price-pipeline list), `data/registries/entity_registry.json`
(the 566-entry identity registry), and `data/markets/enrichment_data.json`
(ratings). Three issue classes + a token-disposition decision + one systemic
observation.

Anti-fabrication note: every country assignment below is deterministic from
the ticker's exchange code (Shanghai 6xxxxx → China, Shenzhen 00xxxx/30xxxx →
China, 4-digit TSE → Japan, HKEX → Hong Kong) and confirmed against each
entity's `eodhd_ticker` exchange suffix. No guessed countries. The two
proposed *removals* (ATNM, BREW) are backed by a sourced token audit.

---

## A1 — TBD-country sweep (14 entities)

All 14 carry `country="TBD"` in `EQUITIES` (which blocks MarketStack symbology
resolution). Exchange is unambiguous from ticker format + `eodhd_ticker`
suffix. Proposed country in **bold**.

| Ticker | Name | Exchange (eodhd) | Proposed country |
|---|---|---|---|
| 002979 | China Leadshine Technology | Shenzhen (.SHE) | **China** |
| 003021 | Shenzhen Zhaowei Machinery | Shenzhen (.SHE) | **China** |
| 300100 | Shuanglin Co | Shenzhen ChiNext (.SHE) | **China** |
| 002050 | Zhejiang Sanhua Intelligent | Shenzhen (.SHE) | **China** |
| 002472 | Zhejiang Shuanghuan Driveline | Shenzhen (.SHE) | **China** |
| 600111 | China Northern Rare Earth | Shanghai (.SHG) | **China** |
| 601100 | Jiangsu Hengli Hydraulic | Shanghai (.SHG) | **China** |
| 603662 | Keli Sensing Technology | Shanghai (.SHG) | **China** |
| 688017 | Leader Harmonious Drive Systems | Shanghai STAR (.SHG) | **China** |
| 601689 | Ningbo Tuopu Group | Shanghai (.SHG) | **China** |
| 603009 | Shanghai Beite Technology | Shanghai (.SHG) | **China** |
| 6594 | Nidec Corp | Tokyo (TSE) | **Japan** |
| 6723 | Renesas Electronics | Tokyo (TSE) | **Japan** |
| 9868 | XPeng Inc Class A | Hong Kong (.HK) | **Hong Kong** |

Result: 11 China + 2 Japan + 1 Hong Kong. All route under the existing
`marketstack_client` China-prefix logic (6xxxxx→XSHG, 00/30→XSHE) and the
Japan/HK MIC maps. **9868 (XPeng HK line)** routes to the Yahoo override (HK
feed frozen per §9). Apply the same country to the matching
`entity_registry.json` entries.

*Informational, not an action:* 9868 (XPeng HK) and the existing **XPEV**
(US ADR) are two listings of the same company — kept as distinct securities,
not a duplicate key. Flagged so the future "total composite" build de-dupes by
entity, not ticker.

---

## A2 — Missing / junk registry country (beyond the 14)

The `country=None` / `country="/"` scan surfaced entries the original task
didn't list:

### Equities with `country=None` in the registry (3 new)

| Ticker | Name | EQUITIES says | Proposed registry country | Note |
|---|---|---|---|---|
| LMT | Lockheed Martin | United States | **United States** | Registry None; EQUITIES already correct — reconcile registry. |
| NOC | Northrop Grumman | United States | **United States** | Same. |
| STMPA | STMicroelectronics NV | United States ⚠ | **France** | **EQUITIES is wrong** — STMPA is the Euronext Paris line (`STMPA.PA`, V2), not US. The US ADR is the separate `STM` (Switzerland). Fix both EQUITIES and registry to France. |

### Tokens with `country="/"` (junk) (3)

| Ticker | Name | Proposed |
|---|---|---|
| FORMA | Forma Robotics | normalize `/` → `null` (chain-native token; no country) |
| GEOD | Geodnet | normalize `/` → `null` (legit GNSS/RTK DePIN — keep) |
| BREW | Homebrew Robotics Club | see A4 — proposed **DROP** |

Recommendation: for tokens, country is not a meaningful field; normalize all
junk (`/`, `TBD`) country values on tokens to `null` rather than inventing a
jurisdiction. (Tokens are excluded from equity symbology resolution, so this
has no pipeline effect — it's cleanliness.)

---

## A3 — Duplicate-key consolidation (3)

In two of the three, the **duplicate holds the better data** — so consolidation
keeps the canonical key but migrates the good country/rating onto it before
deleting the dup.

### MOG.A  (canonical)  ←  MOG/A  (remove)
- `EQUITIES`: both present → **remove `MOG/A`**, keep `MOG.A` (US).
- `registry`: both present (`MOG/A` country=None) → **remove `MOG/A`**.
- `enrichment`: **both** carry `bottleneck_risk=MEDIUM` (duplicate rating) →
  **remove `MOG/A`**, keep `MOG.A=MEDIUM`.
- Canonical `MOG.A` is the standard vendor format; `MOG/A` is the slash variant
  already flagged `provider: skip` in the data-source overrides.

### 600111  (canonical)  ←  600111 C1  (remove)
- `EQUITIES`: both present. Canonical `600111` has country=TBD; the dup
  `600111 C1` has country=China → **set `600111`→China (A1), then remove
  `600111 C1`**.
- `registry`: both present → **remove `600111 C1`**, set `600111` country=China,
  repair `eodhd_ticker` (currently `None` → `600111.600111.SHG`).
- `enrichment`: only `600111` (CRITICAL ✓) — already consolidated, no change.

### 6723  (canonical)  ←  6723 JP  (remove)
- `EQUITIES`: both present. Canonical `6723` has country=TBD; the dup `6723 JP`
  has country=Japan → **set `6723`→Japan (A1), then remove `6723 JP`**.
- `registry`: both present (`6723 JP` country=None) → **remove `6723 JP`**, set
  `6723` country=Japan.
- `enrichment`: the **MEDIUM rating lives under `6723 JP`**, none under `6723`
  → **migrate the rating to `6723`, then remove `6723 JP`**.

Canonical choice throughout = the bare price-pipeline key the `EQUITIES` list
already iterates (`MOG.A`, `600111`, `6723`), matching the convention used by
every other A-share/TSE ticker (e.g. `6594`).

---

## A4 — Token disposition: ATNM / SLC / BREW

These three are **not the equities their tickers suggest** (Actinium /
Superloop / Craft Brew). In the Robotnik registry they are crypto tokens,
already correctly `sector=Token` (the earlier space/materials mis-tag was
caught during the Space/Materials rating batches — that's why they appear in
those proposal markdowns). The open question is disposition. Backed by a
sourced token audit:

| Ticker | Token | Verdict | Basis |
|---|---|---|---|
| **ATNM** | Autonoma Network (Solana, pump.fun) | **DROP** | Dead microcap — ~$4.3K mcap, **~$8.70/24h volume**, single DEX, no product/team/whitepaper. Robotics terminology only. Zero analytical value. |
| **SLC** | Silencio (peaq + Base) | **KEEP** | Genuine DePIN noise-sensor network — 400K+ users / 180+ countries, live app, ~$1.05M mcap, ~$123K/24h multi-venue volume. Squarely sensor-network / physical-AI. |
| **BREW** | Homebrew Robotics Club (Solana, pump.fun) | **DROP** | Robotics-*themed* memecoin — ~$850K mcap, ~$8K/24h volume, no shipped product/team, recent contract migration. Not affiliated with the real HomeBrew Robotics Club. Thematic-only. |

**DROP actions** (ATNM, BREW): remove from `entity_registry.json`, the token
source list (CoinGecko-ID mapping), `data/prices/tokens.json`,
`data/prices/history/{ATNM,BREW}.json`, and `market_caps.json`. This drops the
live token count 43 → 41.

**KEEP** SLC as-is (frontier-relevant, live feed). Minor: its registry
`country="United States"` is arguably wrong (Silencio is a peaq/EU project) —
optional normalize to `null` like other tokens.

*If* you'd rather track very-early "robotics-narrative" tokens deliberately,
BREW becomes FLAG-FOR-REVIEW instead of DROP — but on a "live frontier-tech
project" quality bar it does not clear. My recommendation stands at DROP.

---

## A5 — Systemic observation (not a bug to fix here)

**All 43 `sector=Token` entries carry `type="public"`.** The registry's `type`
enum is only `public`/`private` (352/214) — there is no `token` type. So this
is schema design (tokens are publicly tradeable), *not* a per-entity mislabel.
I am **not** proposing a mass `type` rewrite under Workstream A. Flagging it as
an optional future schema enhancement (add a `token` type for clean
asset-class partitioning) for a separate decision — it does not affect the
pipeline today.

---

## Apply plan (on approval)

1. `EQUITIES` (fetch_prices.py): 14 TBD→country; STMPA US→France; remove rows
   `MOG/A`, `600111 C1`, `6723 JP`; remove `ATNM`/`BREW` if present in token
   list.
2. `entity_registry.json`: same country fixes; repair `600111` eodhd_ticker;
   remove dup keys `MOG/A`, `600111 C1`, `6723 JP`; remove `ATNM`, `BREW`;
   normalize junk token countries → null.
3. `enrichment_data.json`: remove `MOG/A` (keep `MOG.A=MEDIUM`); migrate
   `6723 JP`→`6723` (MEDIUM); `600111` already CRITICAL.
4. Token artifacts: drop ATNM/BREW from tokens.json, history, market_caps,
   CoinGecko-ID mapping.

**Net:** 14 countries resolved, 3 missing registry countries fixed, 1 mis-tag
(STMPA) corrected, 3 duplicate keys consolidated, 2 dead tokens dropped
(43→41), 1 legit token confirmed kept. Every change deterministic or sourced;
no guesses.

## STOP — for your review

1. Approve the 14 country assignments (A1)?
2. Approve the 3 registry-country fixes incl. **STMPA→France** correction (A2)?
3. Approve the 3 duplicate consolidations with data-migration (A3)?
4. Approve **DROP ATNM + BREW, KEEP SLC** (A4)? Or hold BREW as FLAG-FOR-REVIEW?
5. The systemic `type=public`-on-tokens (A5) — leave as-is, or want a separate
   schema-enhancement task to add a `token` type?
