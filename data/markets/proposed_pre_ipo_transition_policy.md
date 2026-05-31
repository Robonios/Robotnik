# Entity Lifecycle Policy — private → pre-IPO → public → delisted (FINALIZED for review)

**Status:** FINALIZED DRAFT. Nothing applied. **STOP for review (C2)** before applying the
field migration; **STOP again (C4)** before committing the near-term case dispositions.

Goal: a unified `entity_id` lifecycle so a frontier entity moving private → public is
**neither lost nor double-counted**, carries its identity/history/rating across the boundary,
and is handled **by design** rather than patched per-case. This is the structural answer to the
class of membership-rigor gaps the B-sweep just closed.

---

## C1 — Current state (surfaced)

| Structure | Today | Gap |
|---|---|---|
| Registry | 562 entries; **key == `id`** for all. 214 private (keyed by **slug**, e.g. `cerebras-systems`), 305 public (keyed by **ticker**, e.g. `ALGM`), 43 token. Private entries carry `total_raised_m`/`last_round`. | **No `lifecycle_status`, no `entity_id` field, no `public_ticker`** — the lifecycle machinery does not exist yet. |
| `rounds.json` | 1244 rounds, each with an `entity_id` field. | **Only 344/1244 link to a registry entity** (900 orphan entity_ids — companies funded but not in the registry). |
| RPCI (`calculate_private_index.py`) | Excludes `IPO` + `IPO (filed)` round types; M&A conditional on private in-universe acquirer. | **No `lifecycle_status` filter** — a company that has gone public is not yet structurally removed from "active private". |
| Index (`calculate_index.py`) | Keys by ticker; registry membership lookups by ticker (works because public key==ticker); forward + reverse parity guards live. | Slug-keyed private entities are **not ticker-findable** — the unresolved entity_id↔ticker bridge. |
| Cases | `cerebras-systems`, `unitree-robotics` exist as `private`. | **SpaceX, York/`YSS`, `CBRS` are absent** from the registry. |

**The architectural crux:** the registry key is the ticker for public entities but a slug for
private ones. The index finds public names by ticker; a private slug going public must become
ticker-findable *without* breaking its rounds-link or creating a silent duplicate. §3 resolves this.

---

## 1. States — the `lifecycle_status` enum (7)

| Value | Meaning | Lives in | In equity indices? |
|---|---|---|---|
| `private` | Private company, no IPO process | rounds.json (history) + registry | No |
| `pre_ipo_filed` | S-1/F-1/confidential filing confirmed, not priced | registry (+ rounds); **filing valuation = metadata, NOT a market cap** | No |
| `pre_ipo_priced` | Priced/allocated, not yet first trade | registry | No |
| `public` | First trading day has occurred | EQUITIES + equities.json + registry | **Yes** |
| `delisted` | Was public, ceased trading (bankruptcy/going-private) | registry (history) | No — exits via CA/reorg |
| `acquired` | Was public, absorbed via M&A (ticker retired) | registry (history) | No — exits via CA on close |
| `withdrawn` | Filed then pulled the IPO → **reverts to `private`** | registry | No |

*Additions vs the draft:* `acquired` (M&A exit — distinct from `delisted`; the acquirer/terms are
recorded) and `withdrawn` (filed-then-pulled → back to `private`). *Not adding* a `halted` state —
a temporary trading halt stays `public`; only permanent cessation moves to `delisted`/`acquired`.
**Default:** the 214 existing private entities → `private`; 305 public → `public`; status advances
**only** when a filing/pricing/first-trade is sourced (no fabrication).

---

## 2. Transitions & triggers

```
  filing confirmed (S-1/F-1)          → pre_ipo_filed   (filing valuation = METADATA, never mcap)
  priced / allocated                  → pre_ipo_priced
  FIRST TRADING DAY                    → public          (enters EQUITIES; chain-link entry:
                                                          first price, return 1.0, no jump —
                                                          identical rule in the reconstruction)
  ceases trading (bankruptcy/private)  → delisted        (exit via CA/reorg: WOLF-class wipeout
                                                          realizes the loss; reverse-split = flat)
  acquired / merged away               → acquired        (exit via CA on deal close)
  IPO withdrawn / pulled               → withdrawn → private
```

**Index entry trigger = actual first trading day** — not the S-1 filing, not the pricing. An S-1
can be withdrawn; a target valuation is not a market price. Only after a tradeable close does a
market cap exist and feed the index, via the established chain-link entry (enter-at-first-price,
day-one return forced to 1.0, no artificial jump; the independent reconstruction applies the same
rule, so Δ=0 holds).

---

## 3. Entity-linking — the `entity_id` backbone (resolves the crux)

**Add `entity_id` as a stable, immutable field on every registry entry** (backfill = current key
for all 562). It never changes across the lifecycle. The registry is the master entity list;
`rounds.json` and the index both reference `entity_id`.

**Approved mechanic — IMMUTABLE `entity_id` key (no re-key):**
The registry **key IS the immutable `entity_id`** and **never changes** across the lifecycle. The
trading symbol is a **`public_ticker` FIELD**, not the key. All index/price/RPM lookups reference
`public_ticker` (= the ticker for native-public names → a no-op for them; = the assigned ticker for
transitioned ones). A `private → public` transition is a **pure field update** — set
`lifecycle_status: public` + `public_ticker: <TICKER>` on the existing row. No destructive mutation,
one row, **no-double-count by construction**.
- e.g. `cerebras-systems` stays keyed `cerebras-systems` (immutable); on IPO it gains
  `public_ticker: CBRS`, `lifecycle_status: public`. Its 15 rounds keep `entity_id: cerebras-systems`
  and resolve to the same unchanged row.
- **Why immutable, not re-key:** the fragility we keep killing is the *mutable key*. The fix is an
  immutable identity key — not a guarded re-key of a mutable one. The ticker-keyed price/index
  pipeline resolves `public_ticker → entity_id` (identity for native-public names).
- **Backfill:** `entity_id` = current key (dict does not move) + explicit field for downstream code;
  add `public_ticker` (= ticker for public, null for private/pre-IPO) + `lifecycle_status`.
  `rounds ↔ registry` linking stays **key-match** (key == entity_id, immutable) — **no linking change**.

*Alternatives rejected: (a) two rows (private anchor + public record) — reintroduces the
filter-dependent double-count class we've been eliminating; (b) re-key on transition — a guarded
mutation of a mutable key, strictly worse than an immutable one.*

**Orphans/duplicates (surfaced for cleanup):** 900/1244 rounds carry `entity_id`s with no registry
entity — mostly out-of-scope small rounds, but any *frontier* orphan that has since IPO'd is a
reverse-parity candidate. Duplicate detection reuses the STM/STMPA discipline: no two `entity_id`s
for the same company; no company keyed under both a slug and a ticker simultaneously.

---

## 4. No-double-count invariant

A company contributes to the **private** aggregations (funding / RPCI) during its private phase and
to the **public** index during its public phase — **never both simultaneously**, with a clean handoff
at the IPO trading date. With the single-canonical model this is **structural**: one entity has one
`lifecycle_status`, so it is counted in exactly one layer. Its historical private rounds **remain in
`rounds.json`** as a permanent record (they happened), but once `lifecycle_status: public` it is no
longer an *active-private* entity for RPCI. A future "total frontier composite" de-dupes by
`entity_id` so the entity is counted once.

---

## 5. Pre-IPO valuation handling (anti-fabrication — critical)

A target/filing valuation (SpaceX ~$1.75T; Cerebras's pricing valuation; Figure AI's $39B round) is
**not** a market cap. Stored only as **labelled metadata**: `filing_valuation_m` (or
`private_valuation_m`) **with `valuation_source` + `valuation_as_of`**, explicitly fenced from
`market_cap_usd`. A pre-IPO entity has **no index weight by definition** (it does not trade). Never
synthesize or interpolate a pre-IPO market cap.

---

## 6. Rating carryover + re-validation

A private/pre-IPO bottleneck rating travels with the `entity_id` as a **starting point**, and is
**re-validated on transition** (the S-1/424B4 prospectus is far richer than private data) via the
rigorous rating process (research + **adversarial verifier for CRITICAL/HIGH**), with the change
logged. It is re-validated, **not re-derived from scratch**.

---

## 7. Display-eligibility (data-capability only; display itself is step-1)

Pre-IPO entities are defined as **display-eligible but index-walled-off**: the data is structured so
a future pre-IPO watchlist *could* render them (`lifecycle_status`, bottleneck rating, labelled
`filing_valuation_m`) while the lifecycle-parity guard (§C3) keeps them out of **every** index
aggregation. **No display is built here** — data-capability only.

---

## C3 — Lifecycle-parity guard (to build, publish-blocking)

Mirrors the membership-parity guards with a lifecycle dimension:
1. **No-double-count:** no `entity_id` appears in both the active-private set (RPCI universe) and the
   public-index set. (Structural under single-canonical; the guard asserts it anyway.)
2. **Index eligibility:** only `lifecycle_status == public` (and non-excluded, non-token, frontier)
   entities are index-eligible; `private` / `pre_ipo_*` / `delisted` / `acquired` / `withdrawn` are
   index-excluded **by status** — the same gate as `excluded` / `token`.
3. **Negative-tested:** confirm it fires if a `pre_ipo` entity is given an index weight, or if one
   `entity_id` lands in both aggregations.

---

## C4 — Near-term cases (dispositions surfaced at the C4 STOP, not here)

Cerebras (`CBRS`, public 2026-05-14 — add + rate + chain-link entry; reverse-parity guard should
*require* it once it's a non-excluded public frontier entry), SpaceX (`pre_ipo_filed`, rate CRITICAL
via verifier, ~$1.75T as metadata, not indexed), Unitree (`pre_ipo_filed`, rate), York/`YSS`
(confirm disposition — was routed to B), plus a sweep for any other transition in the project window.
Full re-validation after Cerebras enters (196 → ~197).

---

## C5 — Scan integration (policy-aware, not run here)

The June private-market scan becomes lifecycle-aware: it adds new rounds **and** detects + applies
transitions — `private → pre_ipo_filed` on a sourced filing, `pre_ipo_* → public` on first trading
day, `public → delisted/acquired` on cessation — routing each through entity-linking + no-double-count
+ rating-carryover. Detection signals surfaced before the scan runs.

---

## STOP (C2) — decisions for review
1. **Enum (7 states)** incl. the added `acquired` + `withdrawn`, and the first-trading-day trigger (§1–§2)?
2. **`entity_id` backbone + single-canonical re-key-on-transition** mechanic (§3), incl. moving
   rounds↔registry linking to `entity_id`-field match?
3. **No-double-count via single `lifecycle_status`** + RPCI filtering on it (§4)?
4. **Pre-IPO valuation = labelled metadata, never mcap** (§5) + **rating re-validate-not-re-derive** (§6)?
5. **Display-eligible-but-index-walled-off** data shape for pre-IPO (§7)?
6. Proceed to build the **lifecycle-parity guard (C3)** + backfill the fields, then bring the
   **near-term cases (C4)** for a second STOP?
