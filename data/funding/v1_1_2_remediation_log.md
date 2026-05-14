# v1.1.2 Remediation Log

**Date:** 2026-05-13
**Predecessor:** v1.1.1 (1,131 rows)
**Result:** v1.1.2 (1,243 rows, 92.8% verified — 15 pending from early-stage sweep)

This log captures every mutation applied between v1.1.1 and v1.1.2. Total: **112 new rows + 1 in-place correction**.

## Summary

| Mutation class | Count |
|---|---:|
| New pre-seed/seed rows added (sweep) | 112 |
| In-place lead-investor correction (Alta Resource) | 1 |

**Net row delta:** 1,131 → 1,243 (+112). No drops.

## v1.1.2 is a data-only release

No schema changes (CSV stays 23 cols, internal JSON unchanged). All mutations are data additions plus one in-place correction.

## Pre-seed / seed sweep

Full detail in [`preseed_seed_sweep_summary.md`](preseed_seed_sweep_summary.md). Headline:

| Sector | New rows | Notes |
|---|---:|---|
| Robotics | 29 | 27 NEW + 2 approved DEDUP-CHECK (Scout AI, Antioch); Mind Robotics held pending; Vinci skipped (anti-fabrication) |
| Semiconductors | 26 | 25 NEW + 1 approved DEDUP-CHECK (Ricursive Intelligence) |
| Space | 40 | All NEW |
| Materials | 11 | 11 NEW (file-level SKIPs by source agent caught existing-row collisions) |
| Token | 6 | 6 NEW (1 out-of-window, ~30 pure-software-crypto exclusions deferred to future audit) |
| **Total** | **112** | |

### Source mix (broadened for this sweep)

Beyond the monthly template's standard press sources, this sweep pulled from:
- Incubators / accelerators: Y Combinator, HAX, IndieBio, Plug and Play, CDL, Entrepreneur First, Founders Factory, MassChallenge, ESA BIC
- University tech-transfer: CMU, MIT, Stanford, ETH Zurich, TUM, Imperial, KAIST, Tsinghua, EPFL, Cambridge, Oxford, UC Berkeley
- VC firm portfolio pages: Lux Capital, Eclipse Ventures, At One Ventures, Lowercarbon, Playground Global, 1517 Fund, Khosla Ventures, Toyota Ventures, Founders Fund, BoxGroup
- Regional: Sifted, Pandaily, TechNode, Caixin, Tech in Asia, The Korea Herald, Calcalist, BusinessKorea

### Threshold override (sweep-specific, NOT applied to monthly template)

- Pre-Seed min: $500K (vs $5M robotics / $3M space standard)
- Seed min: $1M

Documented in [`preseed_seed_sweep_summary.md`](preseed_seed_sweep_summary.md). Future monthly ingestions revert to standard thresholds.

## Alta Resource Technologies correction (in-place)

**Entity:** `alta-resource-technologies` 2025-05-05 Seed
**Issue:** `lead_investors` was incorrectly recorded as `In-Q-Tel`. Per primary source (company press release), the actual lead is DCVC with Voyager Ventures as co-lead.
**Action:** `lead_investors` `In-Q-Tel` → **`DCVC, Voyager Ventures`**. No other field touched.

**Note on Jan 7 close:** The Alta Resource Jan 7, 2025 announcement ($5.1M close) is the same Seed round as the May 5, 2025 announcement. NOT added as a duplicate row. Treated per the same single-event-per-round convention applied to multi-tranche closes.

## Anti-fabrication holdbacks (rows considered but excluded)

Per the v1.1.1 anti-fabrication rules in [`prompts/monthly_ingestion_template.md`](../../prompts/monthly_ingestion_template.md), these candidates were considered and excluded:

| Row | Sector | Reason |
|---|---|---|
| Vinci Semi Seed | Semis | Amount inferred from cumulative ($46M total − $36M Series A); violates Rule 1 (no fabrication) |
| Mind Robotics Seed $115M | Robotics | Held pending spot-check (Stark-pattern transposition history); can land in v1.1.3 |
| Sunday $35M | Robotics | Not labeled "seed" verbatim per Rule 7 |
| Reflex Robotics $7M | Robotics | Date actually March 2024, outside window |
| Louiza Labs $5M | Robotics | Round type not specified in source |
| Foundation Q1 2025 | Robotics | No canonical URL |
| WaiV Robotics $7.5M May 5 | Robotics | Outside Apr 30 window cutoff |
| Mirai Robotics $4.2M | Robotics | Source 403, no clean secondary |
| Alta Resource Jan 7 close | Materials | Same round as existing May 5 row (handled as correction) |
| ~6 Space candidates | Space | Source verification timing |
| 5 Materials candidates (tozero, Endolith, Element Zero, Theion, Lithios, RarEarth) | Materials | Source agent flagged as existing-row collisions / out-of-scope |
| Token deal #6 | Token | Out-of-window (2024 close) |
| ~30 Token candidates | Token | Pure-software-crypto exclusion; flagged for future audit (some may be DePIN legitimately in scope) |

## DEDUP-CHECK resolutions

User-triaged outcomes for the 6 DEDUP-CHECK candidates surfaced by sector agents:

| Row | Existing entity | Decision |
|---|---|---|
| Scout AI Seed $15M Apr 2025 | Series A 378d later | **ADD** — distinct earlier round |
| Mind Robotics Seed $115M Nov 2025 | Series A 127d later | **HOLD** — spot-check pending |
| Antioch Pre-Seed $4.24M Dec 2025 | Seed 129d later | **ADD** — distinct earlier round |
| Ricursive Intelligence Seed | Series A | **ADD** — distinct earlier round |
| Vinci Semi Seed | Series A 2025-12-02 | **SKIP** — inferred amount, anti-fabrication |
| Alta Resource Seed Jan 7 2025 | Seed 2025-05-05 (existing) | **MERGE** — same round; treat existing as canonical |

## Future-review queue (logged here, not actioned in v1.1.2)

1. **Mind Robotics Seed $115M** — pending user spot-check decision.
2. **Token pure-software-crypto exclusion** — ~30 candidates excluded per current rule. Some may be DePIN / decentralized-AI legitimately in scope. Worth a dedicated audit on whether the exclusion is now too tight. Likely v1.2 scope.
3. **151 USER-VERIFY canonical-name candidates** ([`investor_canonical_followup.md`](investor_canonical_followup.md)) — still deferred from v1.1.1.
4. **Pre-2025 takes** — not yet refreshed to v1.1 spec. Future release.
5. **15 `source_status: pending` rows from this sweep** — eu-startups.com and uktechnews.info 403s; content cross-verified but primary URL un-fetchable. Re-check next monthly cycle.

## Final dataset state

| Metric | Value |
|---|---:|
| Rows | **1,243** |
| `verified` | 1,153 (92.8%) |
| `archived` | 75 (6.0%) |
| `pending` | 15 (1.2%) |
| Pre-seed in Jan 2025 – Apr 2026 | 37 |
| Seed in Jan 2025 – Apr 2026 | 131 |
| CSV columns | 23 (unchanged from v1.1.1) |
| schema_version | v1.1.2 |
| updated | 2026-05-13 |

## Files

- [`rounds.json`](rounds.json) — final v1.1.2 dataset (1,243 rows)
- [`preseed_seed_sweep_summary.md`](preseed_seed_sweep_summary.md) — sweep summary doc
- [`preseed_seed_sweep_robotics_candidates.md`](preseed_seed_sweep_robotics_candidates.md) — Robotics candidates (30)
- [`preseed_seed_sweep_semiconductors_candidates.md`](preseed_seed_sweep_semiconductors_candidates.md) — Semis candidates (27)
- [`preseed_seed_sweep_space_candidates.md`](preseed_seed_sweep_space_candidates.md) — Space candidates (40)
- [`preseed_seed_sweep_materials_token_candidates.md`](preseed_seed_sweep_materials_token_candidates.md) — Materials + Token (23)
- [`dataset_notes.md`](dataset_notes.md) — updated for v1.1.2
- [`v1_1_1_remediation_log.md`](v1_1_1_remediation_log.md) — predecessor log
