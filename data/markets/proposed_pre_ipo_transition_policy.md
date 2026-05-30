# Workstream C — Pre-IPO / IPO Transition Policy (Surface for Review)

**Status:** DRAFT. Nothing applied. STOP for review before applying.

Goal: a clean, repeatable handoff so a frontier-tech entity moving private →
public is **neither lost nor double-counted**, and so the entity carries its
identity, history, and rating across the boundary.

---

## 0. The timeline has moved past the prompt's April data

The brief was written on April-2026 data ("SpaceX S-1 filed at ~$1.75T;
Cerebras refiled"). As of **late May 2026** the facts have advanced, and the
policy must apply to *current* reality:

- **Cerebras has already IPO'd** — priced **May 13 2026 @ $185**, trading
  **May 14 2026 on Nasdaq `CBRS`** (~$56.4B pricing valuation; CFIUS cleared,
  G42 off the cap table). It is no longer pre-IPO — it is a **live
  private→public transition that has already occurred** and is currently
  *uncaptured* in the equities universe.
- **SpaceX filed its public S-1 on May 20 2026** (~$1.75T **target**, raise up
  to ~$75B; first trade expected mid-to-late June 2026). Genuinely
  `pre_ipo_filed` — but **SpaceX is not in the entity registry at all**, so the
  brief's "ensure the existing CRITICAL rating is attached" cannot be done as
  written: there is no existing SpaceX entity or rating to attach.

These two cases are the policy's first real applications and are time-sensitive
(both land before/around the June scan).

---

## 1. The `lifecycle_status` field

Add `lifecycle_status` to the **entity registry** (the source of truth for
entity identity). Enum:

| Value | Meaning | In which dataset | Counted in equity indices? |
|---|---|---|---|
| `private` | Private company, no IPO process | rounds.json (historical), registry | No |
| `pre_ipo_filed` | S-1 / F-1 / confidential filing confirmed, not priced | rounds.json + registry; **filing valuation recorded as metadata, NOT a market cap** | No |
| `pre_ipo_priced` | Priced/allocated, not yet first trading day | registry | No |
| `public` | First trading day has occurred | equities.json + EQUITIES + registry | **Yes** |
| `delisted` | Was public, no longer trades | registry (historical) | No |

Default for the 214 existing private entities: `private`. No fabrication —
status is only advanced when a filing/pricing/first-trade is sourced.

---

## 2. Transition trigger = **actual first trading day** (not S-1 filing)

An S-1 can be withdrawn or delayed; a target valuation is not a market price.
Until there is a tradeable close, there is no public-equity data to ingest.

```
  S-1 / confidential filing confirmed   → pre_ipo_filed
        (filing valuation = METADATA, never treated as market cap)
  Priced / allocated                    → pre_ipo_priced
  FIRST TRADING DAY                      → public
        (entity enters equities.json + EQUITIES, picked up by the price
         pipeline, evaluated for index inclusion)
  Ceases trading                         → delisted
```

**The market-cap rule (anti-fabrication):** a *target / filing* valuation
(SpaceX ~$1.75T; Figure AI's $39B private round; Cerebras's $56.4B at pricing)
is **not** an actual market cap. Only after the first trade does a market cap
exist and feed the index. Pre-trade valuations live in a `filing_valuation_m`
metadata field, explicitly fenced off from `market_cap_usd`.

---

## 3. Linking + no double-counting (shared `entity_id`)

The mechanism already partly exists: **every round in `rounds.json` carries an
`entity_id`** (e.g. `cerebras-systems`), and registry keys *are* those ids.
Currently 344 / 1244 rounds link to a registry entity.

Policy:
- The **registry entity is the canonical identity**, keyed by `entity_id`.
- `rounds.json` (historical private rounds) and the public-equity record both
  reference the **same `entity_id`**. On transition the entity gains a
  `public_ticker` (e.g. `CBRS`) and `lifecycle_status: public`; its historical
  rounds stay in `rounds.json` as a permanent record (they happened).
- **No double-counting:** the composite/bottleneck indices read the
  *public-equity* set (now filtered to `lifecycle_status == public` — same
  place the token `type` filter lives). Private rounds are a separate dataset
  and never enter the equity composite. A future "total frontier composite"
  (§8 of the methodology) de-dupes by `entity_id`, so an entity that is both a
  historical private round and a current public equity is counted **once**.

---

## 4. Rating carryover

A bottleneck rating assigned while private **transfers to the public record on
transition** — it is **re-validated, not re-derived from scratch**:

- The latest private rating travels with the `entity_id`.
- At first-trade, it is re-validated against the public disclosures the IPO
  produces (the S-1/prospectus is far richer than private data) and confirmed
  or adjusted, with the change logged.
- Example: Cerebras's private rounds carry `bottleneck_risk: High`
  (System Integration tier). On its public transition that **HIGH carries
  over**, re-validated against the 424B4 prospectus.

---

## 5. Transition-candidate list (current status, late May 2026)

Confirmed, sourced (target valuation ≠ market cap flagged):

| Entity | In registry? | In rounds? | Actual current status | Proposed `lifecycle_status` | Action on approval |
|---|---|---|---|---|---|
| **Cerebras Systems** | ✅ `cerebras-systems` (private) | ✅ (risk=High; has `IPO (filed)` rounds) | **PUBLIC — `CBRS` Nasdaq, trading May 14 2026** | **`public`** | **Immediate:** add `CBRS` to EQUITIES/equities.json linked via `entity_id`; carry HIGH rating, re-validate vs 424B4; set registry `public_ticker=CBRS`. First live application. |
| **SpaceX** | ❌ **not in registry** | ✅ `SpaceX` rounds exist | S-1 filed May 20 2026; ~$1.75T target; first trade ~mid-late June | **`pre_ipo_filed`** | **Add** registry entity (`entity_id: spacex`); `filing_valuation_m≈1,750,000` as metadata (NOT mcap); **assign a rating** (CRITICAL candidate — no prior rating exists); on first trade → `public`. |
| **Unitree Robotics** | ✅ `unitree-robotics` (private) | ✅ | Shanghai STAR draft S-1 accepted Mar 20 2026; ~$610M; review ~Jun 1 | **`pre_ipo_filed`** | Flag `pre_ipo_filed`; `filing_valuation_m` metadata; rate at Workstream D. |
| **York Space Systems** | ❌ not in registry | ✅ (`York Space Systems / ALL.SPACE`) | **PUBLIC — `YSS` NYSE, trading Jan 29 2026** | **`public`** | Decide universe inclusion; if in-scope, add `YSS` + `entity_id: york-space`, rate. |

**Speculative — NOT flagged (no confirmed filing; do not tag as filed):**
Figure AI ($39B *private* round, listing eyed 2027-28), Impulse Space, Stoke
Space, Boston Dynamics ("$100B IPO" is SEO rumor). These stay `private`.

**Context — already public >6 months (not new transitions):** Firefly
Aerospace (`FLY`, Aug 2025), Voyager (`VOYG`, Jun 2025), Karman (`KRMN`, Feb
2025), CoreWeave (`CRWV`, Mar 2025). Flag for the Workstream B
excluded-equities audit if any belong in-universe and aren't yet tracked.

---

## 6. Coordination with the June private-market scan

This policy should be **applied before the first-week-of-June scan** so the May
ingestion stamps `lifecycle_status` correctly on anything new. The scan will
pick up new rounds and may surface new `pre_ipo_filed` candidates; with the
field + trigger in place, it can tag them under the monthly template rather than
needing a retrofit. SpaceX's expected mid-late-June first trade falls right in
this window — the `pre_ipo_filed → public` path must be ready.

---

## STOP — decisions for review

1. **Approve the `lifecycle_status` enum + first-trading-day trigger** (§1-§2)?
2. **Approve the linking / no-double-count design** (§3 — registry entity as
   canonical `entity_id`, indices filter `lifecycle_status==public`, rounds stay
   historical)?
3. **Cerebras (already public):** approve the immediate private→public
   transition — add `CBRS`, carry HIGH (re-validated)? This is the most
   time-sensitive item (it's already trading and currently uncaptured).
4. **SpaceX:** approve **adding** it to the registry as `pre_ipo_filed` (it
   isn't there today) and assigning a fresh **CRITICAL** rating (there is no
   pre-existing rating to "carry")? Filing valuation stays metadata-only.
5. **York Space / Unitree:** in-universe? York is already public (`YSS`);
   Unitree is `pre_ipo_filed` (Shanghai STAR). Add both, or defer York to the
   Workstream B audit?
6. **Rating carryover mechanics** (§4) — re-validate-not-re-derive, with the
   change logged — acceptable?

On approval I apply the field + the four dispositions, then the June scan and
Workstream D operate on a lifecycle-aware registry.
