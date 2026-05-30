# Token Isolation Policy

**Status:** ACTIVE (applied 2026-05-30, Workstream A registry hygiene).

## Decision

Tokens are a **legacy category**, retained only as an **isolated background
watchlist for content / research**. They are:

- **never product-functional** — not part of any index, composite, or
  equity-rating aggregation;
- **never displayed customer-facing** — excluded from all website / product
  surfaces (record for the future website-restructure workstream);
- **kept, not pruned** — including dead/low-activity tokens, which retain
  content value and whose `token` type resolves the ticker-collision confusion
  (e.g. ATNM/SLC/BREW are crypto tokens, not the Actinium/Superloop/Craft-Brew
  equities their tickers suggest).

## Isolation mechanism — the `token` type

The registry `type` enum is extended to **`public` / `private` / `token`**. All
43 `sector="Token"` entities are reclassified `type="token"`. This is the
**primary isolation key**: it travels with the entity regardless of sector, so
a token mis-tagged into a non-Token sector (as ATNM/SLC/BREW once were, in
Space/Materials) still cannot leak into an equity aggregation.

### Every aggregation filters tokens out

| Aggregation | Script | Filter |
|---|---|---|
| Robotnik Composite Index | `calculate_index.py` | excludes `type=="token"` (registry-sourced) **and** `sector=="Token"` |
| Bottleneck-Weighted Composite | `calculate_bottleneck_composite.py` | excludes `type=="token"` **and** `sector=="Token"` |
| Equity-rating coverage | computed over the `eligible` (token-excluded) set in the bottleneck composite | inherited |

Belt-and-suspenders: **type-based** (primary, robust to mis-sectoring) +
**sector-based** (fallback). Verified 2026-05-30: 0 of 43 tokens pass either
hardened filter. `market_caps.json` remains a deliberate superset (it carries
tokens) but every consumer filters them out.

## `activity_status` field

Each token carries an `activity_status` (`live` / `low` / `dead` /
`unassessed`) so dead-vs-live is visible without pruning. Seeded from the
Workstream-A token audit:

- **live:** SLC (Silencio — real DePIN noise-sensor network, 400K+ users)
- **low:** BREW (Homebrew Robotics Club — robotics-themed, thin liquidity)
- **dead:** ATNM (Autonoma Network — ~$8/day volume, no product)
- **unassessed (40):** not yet liveness-audited — honest default, not a
  fabricated status.

**Follow-up:** a full liveness assessment of the remaining 40 tokens is a
small future research pass (not blocking).

## Customer-facing display (website-restructure workstream)

**Tokens are excluded from all customer-facing display.** The website
restructure must treat `type=="token"` as a hard display-exclusion filter —
tokens exist for internal content/research only and never render on any
product surface.
