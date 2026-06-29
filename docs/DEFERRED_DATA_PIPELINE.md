# Deferred to the gate-build — CI-coupled data + the funding workstream

The 2026-06-29 exposure pass removed only **inert** data. This file is the
**flag to the data-pipeline thread**: everything below stays publicly tracked
**for now** because something **served depends on it** — via the CI pipeline or
local regeneration — and removing it would break the live product. The right test
is *"does anything served depend on it (CI included)"*, not *"does a page fetch
it."*

De-exposing this set requires giving the pipeline a **private place to read/write
its state** (a private data repo checked out in CI with a PAT, or cloud storage),
then repointing the scripts. That is the gate-build — out of scope for the
additive removal pass.

## A. CI-load-bearing substrate (≈ 65 MB) — stays tracked

The daily GitHub Actions job ([fetch-data.yml](../.github/workflows/fetch-data.yml))
checks out fresh and **reads** these to regenerate the **served** indices:

- **`data/prices/`** — the **60 MB price-history corpus** is the incremental base:
  `fetch_price_history_marketstack.py --refresh` merges the last 45 days against
  the **on-disk 5-year series**; `calculate_index.py` reads `data/prices/history/`
  to build `robotnik_index.json`. Remove it → the served multi-year chart
  collapses to 45 days on the next run. (Also `all_prices`, `benchmarks`,
  `equities`, `tokens`, corporate-action class.)
- **`data/registries/`** persistent inputs — `entity_registry.json`
  ("Registry is the only source" for sector in `calculate_index.py`),
  `marketstack_symbols.json`, `data_source_overrides.json`,
  `corporate_action_route.json` (self-maintained by the weekly sweep),
  `index_membership_exceptions.json`, `taxonomy.json`.
- **`data/mappings/`** — ticker→id maps read by the fetchers.
- **`data/index/`** — the index machinery + served outputs (kept-served subset:
  `index_summary`, `robotnik_index`, `composite_index`, `commodities_index`,
  `bottleneck_weighted_composite`, `sub_indices`, `private_capital_index`,
  `weights`, `market_caps`).
- **`data/markets/`** CI/served — `robotnik_public_markets.json`,
  `enrichment_data.json`, `enriched_equities.json`, coverage/gap artifacts.
- **`data/quarantine/`** (weekly health-check writes), **`data/news.json` /
  `filings.json` / `reports.json`** (intel job outputs).

> Note for the security thread: `entity_registry.json` — flagged earlier as the
> real stakes inside the price-history bundle — is the **most** load-bearing file
> here. Its de-exposure specifically requires the private-registry + CI-repoint.

## B. Funding workstream — `rounds.json` + the de-risk rewire

`data/funding/rounds.json` (1,287 deals incl. `robotnik_take`, valuations,
investor syndicates) is the **highest-sensitivity asset**, but it is the input to
the **locally-regenerated served outputs** (`private_capital_index.json` / the
RPCI, and the planned funding aggregate). Removing it + repointing the build
scripts at the private archive would bake a **machine-specific path into the
public repo** and create a **hidden cross-repo dependency** — the public repo
could no longer regenerate its own served funding aggregates. So `rounds.json`
**stays tracked** until the gate-build establishes the private-input architecture
properly.

### Ready-to-execute design (do this in the gate-build, once private inputs exist)

1. **`scripts/build_funding_aggregates.py`** — reads `rounds.json` (from the
   private store), writes `data/funding/funding_aggregates.json` carrying **no
   deal rows**: per-period blocks (`3M/6M/1Y/ALL` + each prior) with
   capital/round/avg/median, sector & stage breakdowns, mega-round counts, the
   investor **leaderboard (name + deal-count only)**, and a `monthly_by_sector`
   capital series for the trends chart.
2. **Singleton suppression (build-side):** the 12 `(month, sector)` cells with a
   single disclosed round (7% of 161) must be emitted as **absent/null — never
   `$0`** — so the exact figure never enters the JSON. Add a brief "sparse cells
   omitted" legend note if a gap looks odd. *(Confirmed treatment.)*
3. **Largest Round:** keep the company name — the period's single largest is
   always a publicly-reported mega-round (a public fact), and it renders from the
   resolved aggregate record, **not** a retained slice of `rounds.json`.
   *(Confirmed.)*
4. **Rewire [funding.js](../js/funding.js):** fetch `funding_aggregates.json`
   only; **delete the sortable "Top Rounds" deal table** (the one row-level
   surface) and its markup in [funding.html](../funding.html). Keep the donut /
   trends / stage / leaderboard / notable cards and the RPCI panel.
5. **Rewire [nav.js](../js/nav.js):** the top-bar search "Funding" branch fetches
   `rounds.json` on **every page** (lines ~371, 430-448) — drop that branch + the
   fetch; keep Research + Assets search.
6. Then `rounds.json` (+ the dead-fetch `summary.json`, `investor_name_map.csv`)
   moves to the private store and out of the public repo, via the same
   private-input architecture as §A.

## C. Gate-build checklist (the actual infra)

- [ ] Private data repo (or cloud store) for the §A substrate + §B funding inputs.
- [ ] CI: checkout/sync the private store with a PAT secret before the compute steps.
- [ ] Repoint `calculate_index.py`, the fetchers, and `build_funding_aggregates.py`
      to the private path **via env/config** (never a hardcoded `~/...`).
- [ ] Land the funding rewire (§B 1-5), commit the rows-free aggregate.
- [ ] Move §A + §B inputs out of the public tree (copy-verify-then-remove).
- [ ] Second history purge for the newly-removed substrate.
