# Pre-Seed / Seed Sweep — Summary

**Date:** 2026-05-13
**Window:** January 2025 – April 2026 (16 months)
**Scope:** Pre-Seed + Seed (incl. extensions, Seed+, Seed II) across Robotics, Semiconductors, Space, Materials, Token
**Goal:** Fill the early-stage gap before v1.1.2 ships to VCs.

## Headline result

**112 new rows added** to `rounds.json` (1,131 → 1,243).

Pre-seed/seed rows in the 2025-2026 window now stand at **168** (37 pre-seed + 131 seed), up from a much sparser baseline pre-sweep.

## Per-sector breakdown

| Sector | Candidates surfaced | NEW added | DEDUP-CHECK approved | Excluded |
|---|---:|---:|---:|---|
| Robotics | 30 | 27 | 2 (Scout AI, Antioch) | 1 held (Mind Robotics pending spot-check) |
| Semiconductors | 27 | 25 | 1 (Ricursive Intelligence) | 1 (Vinci — inferred amount, anti-fabrication) |
| Space | 40 | 40 | 0 | 0 |
| Materials | 16 | 11 | 0 | 5 (file-level SKIPs by source agent) + 1 (Alta Resource Jan 7 close = same round as existing May 5) |
| Token | 7 | 6 | 0 | 1 (out-of-window) |
| **Total** | **120** | **109** | **3** | **8** |

**Net new rows: 112 (109 + 3).** Plus 1 in-place correction (Alta Resource lead investor).

## Threshold override (this sweep only)

The monthly ingestion template's standard thresholds were dropped:
- **Pre-Seed:** $500K minimum (template default: $5M for robotics, $3M for space)
- **Seed:** $1M minimum

Documented here so the monthly template stays unchanged for going-forward ingestion. The override is one-time, sweep-specific.

## Sources surveyed

**Standard press (verified):**
- TechCrunch, The Information, Bloomberg (paywalled but citable), Reuters, FT, WSJ
- Sector pubs: SpaceNews, Robotics Business Review, The Robot Report, Robohub, IEEE Spectrum
- Regional: Sifted (Europe), Pandaily / TechNode / Caixin (China), Tech in Asia, The Korea Herald, Calcalist, BusinessKorea

**Early-stage-friendly (broader surface for sweep):**
- Incubators / accelerators: Y Combinator, HAX, IndieBio, Plug and Play, Creative Destruction Lab, Entrepreneur First, Founders Factory, MassChallenge, ESA BIC
- University tech-transfer: CMU, MIT, Stanford, Imperial, TUM, ETH Zurich, KAIST, Tsinghua, EPFL, Cambridge, Oxford, UC Berkeley
- VC firm portfolio pages: Lux Capital, Eclipse Ventures, At One Ventures, Lowercarbon, Playground Global, 1517 Fund, Khosla Ventures, Toyota Ventures, Founders Fund, BoxGroup
- Press release wires: BusinessWire, PRNewswire (deal-specific announcements only)

**Verification approach (per Rule 1):** every URL HEAD-requested via WebFetch before citing. 100/120 candidates resolved verified; 20 marked `source_status: pending` (mostly eu-startups.com 403 errors and a few uktechnews.info 403s — content cross-verified via secondary sources but primary URL remained un-WebFetchable).

## Anti-fabrication holdbacks

Candidates considered but **excluded** per anti-fabrication rules:

**Robotics holdbacks (per source agent):**
- Sunday ($35M Nov 2025) — not labeled "seed" verbatim per Rule 7
- Reflex Robotics ($7M) — date was actually March 2024, outside window
- Louiza Labs ($5M) — round type not specified in source
- Foundation Q1 2025 follow-on — no canonical URL
- WaiV Robotics ($7.5M May 5) — outside Apr 30 window cutoff
- Mirai Robotics ($4.2M) — source 403, no clean secondary

**Semis holdbacks:** Vinci Semi Seed inferred at $10M from cumulative — violates Rule 1 (no fabrication of amounts).

**Space holdbacks:** ~6 candidates couldn't be source-verified to a canonical URL within timing; held for next cycle.

**Materials holdbacks:** Several candidates flagged SKIP in the source file itself (tozero, Endolith, Element Zero, Theion, Lithios, RarEarth) — agent's per-row dedup logic caught existing-row collisions.

**Token holdbacks (significant):** ~30 candidates considered but excluded per the pure-software-crypto rule. **Future-review note:** flagged for a follow-up audit — some of these may be DePIN / decentralized-AI legitimately in scope. Not for v1.1.2. (See `dataset_notes.md` Out-of-universe exclusions for current criteria.)

## Patterns surfaced

**Robotics:**
- RLWRLD (Korea) raised $14.8M Seed I (Apr 2025) + $26M Seed II (Feb 2026) — $41M combined seed capital with no Series A label. Unusual structure but kept verbatim per Rule 7.
- Indian inspection-robotics cluster: Octobotics ($1.1M) + Armatrix ($2.1M) raised within 18 days in Feb 2026.
- Plural (London hard-tech fund) led two robotics seeds (Sunrise Robotics + Upside Robotics) — concentrated thesis bet.
- Three data-infrastructure plays competing in seed/pre-seed (Rerun $17M, Alloy $4.5M, Neuracore $3M) — category collision worth tracking.

**Semiconductors:**
- EDA-AI cohort emerged (6 net-new in 13 months) — Coronado, Maieutic, others.
- Coherent-quantum hardware supply chain emerging at seed: cryo wiring, niobium thin-film, NV-imaging, nonlinear photonics.
- Three $100M+ "Seed" rounds (Substrate, Upscale AI, Unconventional AI) — de facto Series A by stage but labeled "Seed" verbatim per Rule 7.
- Foundry + OSAT subsectors have zero seed candidates — structural (capital intensity prevents seed-stage entry).

**Space:**
- 14 of 40 (35%) tagged DoD / sovereign defense customer — dual-use thesis is now structural at pre-seed.
- Reentry-services subcluster dense (Catalyx, Reditus, Lux Aeterna, Orbital Paradigm in 16 months).
- Lux Aeterna has 2 distinct rounds (pre-seed Jun-25 + seed Mar-26, different leads) — both kept per Rule 7.

**Materials:**
- Pre-seed/seed concentration on biological/chemical extraction (Alta Resource, ChemFinity, Nascent, Sequestra) — DAC + critical-mineral biomining theses.

**Token:**
- 5 of 6 retained are Bittensor / GPU-DePIN-adjacent — narrow surface consistent with our hardware-anchored thesis. The wider DePIN exclusion question deferred.

## In-place correction (separate from sweep)

**Alta Resource Technologies** (`alta-resource-technologies`, 2025-05-05 Seed):
- `lead_investors`: `In-Q-Tel` → **`DCVC, Voyager Ventures`**
- The Jan 7, 2025 announcement ($5.1M close) is the same round as the May 5 announcement ($X final close); not added as a duplicate row.

## Held pending decision

**Mind Robotics** Seed $115M Nov 2025 — surfaced for spot-check (Stark-pattern transposition history with this entity). Content verified internally consistent (Rivian spinout, RJ Scaringe, Eclipse Ventures lead). Held; can land in a v1.1.3 follow-up.

## Final state after v1.1.2

| Metric | Pre-sweep (v1.1.1) | Post-sweep (v1.1.2) | Δ |
|---|---:|---:|---:|
| Total rows | 1,131 | 1,243 | +112 |
| `source_status: verified` | 1,056 | 1,153 | +97 |
| `source_status: pending` | 0 | 15 | +15 |
| `source_status: archived` | 75 | 75 | 0 |
| Pre-seed in 2025-2026 | (low baseline) | 37 | +X |
| Seed in 2025-2026 | (low baseline) | 131 | +X |

## Files

- `rounds.json` — 1,243 rows, `schema_version: v1.1.2`
- `data/exports/Robotnik Frontier Private Rounds April-2026.csv` — 23 cols, 1,243 rows
- `data/funding/preseed_seed_sweep_robotics_candidates.md` — 30 candidates
- `data/funding/preseed_seed_sweep_semiconductors_candidates.md` — 27 candidates
- `data/funding/preseed_seed_sweep_space_candidates.md` — 40 candidates
- `data/funding/preseed_seed_sweep_materials_token_candidates.md` — 23 candidates
- `data/funding/v1_1_2_remediation_log.md` — v1.1.1 → v1.1.2 mutation log
