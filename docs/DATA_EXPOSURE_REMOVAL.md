# Public-repo data-exposure removal — 2026-06-29

This repo is **public** (github.com/Robonios/Robotnik) and deployed on GitHub
Pages. Every tracked file is fetchable at `https://robotnik.world/<path>` and at
`raw.githubusercontent.com/Robonios/Robotnik/main/<path>`. This pass removed the
**inert** internal data that nothing served — and nothing in the CI pipeline —
depends on.

## ⚠️ HEAD removal ≠ history removal

This change removes the files from the **current tree (HEAD)** only. They remain
in the **public git history** and are still retrievable by anyone who clones the
repo or reads an old commit. **De-exposure is not complete until the history
purge runs** — see [HISTORY_PURGE_PLAN.md](HISTORY_PURGE_PLAN.md). And because
the repo has been public, a purge cannot retract what was already cloned, forked,
or cached: **treat anything genuinely secret as disclosed and rotate it.**
(Secret-scan of these files at removal time was clean — no keys/tokens — so there
is nothing to rotate from this set; the `.env` was always gitignored.)

## What moved, and where

- **145 files / 27.4 MB** were **copied → checksum-verified → manifested**, and
  only then `git rm`-ed. Preservation is **copy-verify-then-remove**, never
  move-and-hope.
- Destination: **`~/Robotnik-private-archive/`** — *outside* the repo working
  tree (deliberately not a gitignored subfolder, which a single `git add -f`
  could defeat on a public repo). It mirrors the repo's relative paths, so
  re-publishing it as a private repo later is trivial.
- Manifest (path · bytes · sha256 · verified): `~/Robotnik-private-archive/MANIFEST_inert_removal.tsv`.

### 🔴 Action for Robert — back the archive up off-machine
Until you push it to a private repo, `~/Robotnik-private-archive/` is the **only
copy of these files outside git history**. Take an off-machine copy (external
drive / cloud) **before** running the history purge. "Preserved" must not mean
"one copy on one laptop." This archive is also kept **separate** from the
mirror-clone backup the purge plan requires — two independent safety nets.

## What was removed (categories)

- **Investor / funding backend (high sensitivity):** `data/entities/{investors,registry}.json`,
  `data/funding/*.md` audits, `data/funding/investor_name_map.csv`,
  `data/registries/investor_registry.csv`, and the private-rounds CSVs under
  `data/exports/`.
- **Internal moat:** `data/rag/` (prompts), `data/sweeps/` (rulesets),
  `data/predictions/`, `data/patterns/`, `data/research/` legacy dumps, `data/_reports/`.
- **Supply-chain + commodities staging:** `data/markets/material_nodes.json`,
  `data/registries/dependency_edges.json`, `phase1_*`, all `proposed_*`, and
  related working docs/audits.
- **Report exports** incl. the retired 1Q26 PDFs and chart/social images
  (`data/exports/`). *Marketing note:* the 1Q26 report was a deliberate public
  artifact. It is preserved, not destroyed — re-expose it on purpose later via a
  live, linked page if it earns one. That is a marketing decision, not a security
  one. (At removal time nothing linked the PDFs — sitemap-excluded, only an
  orphaned archive page pointed at the report HTML — so removal breaks no live
  surface.)
- **Misc inert:** `data/manifest.json`, `data/task2a_reports.json`, legacy
  `data/prices.json`.

## Archive frontend retired

`archive/news/news-page.html` and `archive/research/intelligence-page.html` were
orphaned (no inbound links, absent from the sitemap) and were the only loaders of
the legacy `js/main.js`. They are now **meta-refresh redirect stubs** (the
301-spirit equivalent on GitHub Pages — `noindex` + canonical to the live page),
and `js/main.js` is removed.

## What was deliberately NOT removed (deferred)

The headline targets — the **60 MB price-history corpus, `entity_registry.json`,
the index machinery, `rounds.json`, mappings/tokens** — are **CI-load-bearing**:
the daily GitHub Actions job *reads* them to regenerate the **served** indices
(`fetch_price_history_marketstack.py --refresh` merges against the on-disk 5-year
series; `calculate_index.py` reads the registry as "the only source"). Removing
them from the public repo without first giving CI a private place to read them
would collapse the live index chart. The right test was **"does anything served
depend on it (CI included)"**, not "does a page fetch it." That set is deferred to
the gate-build — see [DEFERRED_DATA_PIPELINE.md](DEFERRED_DATA_PIPELINE.md).

## `.gitignore`

Patterns for the removed inert paths were added so the CI `git add data/` cannot
re-introduce them. The deferred CI substrate is **not** ignored — it stays
tracked.
