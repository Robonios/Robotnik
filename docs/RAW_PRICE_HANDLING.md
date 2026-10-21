# Raw price handling

GitHub Pages serves every tracked file and Actions logs of a public repository are public, so raw vendor values (prices, market caps, % changes, P/E, sparklines) are never committed or printed. This note records how the pipeline keeps to that rule (CLAUDE.md, served-data rule) from 21 October 2026.

## What the published files no longer carry

- `data/index/base_date.json` has no `base_prices`. The field held each constituent's latest USD close from `all_prices.json`, rewritten every run (not base-date closes), and no script read it.
- `data/index/commodities_index.json` has no `usd_price` or `base_price_usd` on its constituents. `relative_to_base` is published at full float precision.
- `data/index/parity_guard_report.json` is no longer tracked. `scripts/parity_guard.py` runs only locally (it skips in CI) and writes its report to the gitignored `data/private/`.
- Pipeline scripts print tickers, counts, statuses and published derived figures only.

CLAUDE.md's directory map still lists `parity_guard_report.json` under `data/index/`; correct it when CLAUDE.md is next edited.

## Commodity base prices: the `COMMODITIES_BASE_PRICES` secret

- A repository secret, passed only to the calculator step of `weekly-commodities-composite.yml`.
- Value: one JSON object mapping each of the 20 priced commodities to its fixed 17 June 2026 launch price in USD, exactly as last published in `base_price_usd`, in the form `{"Gallium": <number>, "Silicon": <number>, ...}`.
- Read order: the secret; else the `base_price_usd` still in the published record (the first run after the change only); else the run stops before fetching.
- Checks before any fetch: every published constituent is present, no other names, every value a positive number, and, while the record still carries `base_price_usd`, an exact match with it. A failure names commodities, never values.
- To rebuild the value, take `base_price_usd` from the last committed `commodities_index.json` that still carried it: `git log -S base_price_usd -- data/index/commodities_index.json`.
- A re-baseline (weights review, `COMMODITIES_GENESIS=1`) needs `COMMODITIES_GENESIS_BASES_OUT` set to a private path such as `data/private/genesis_bases.json`. The run writes the new base prices there, never prints or publishes them, and the secret must be replaced before the next weekly run. Without the variable a genesis run stops, so CI can no longer re-baseline the index on its own if the record goes missing.

## Commodities with no fresh price

A constituent with no fresh price this week carries its prior published `relative_to_base` instead of a raw price. At full precision this reproduces the former calculation exactly. Only the first carry after the change reads a six-decimal value; that moves the index by at most 0.00006 points per carried name and 0.0005 points if every name were carried, against a published precision of 0.01.

## The guard: `scripts/check_published_vendor_fields.py`

It reads every tracked JSON file (untracked and gitignored files are not served and are not read) for raw vendor keys and key-less dated price series.

- Gated commits: the daily data commit (`fetch-data.yml`, fetch-prices job) and the weekly commodities and composite commit (`weekly-commodities-composite.yml`). Both run `--staged` after `git add`; a failure stops the job before it commits.
- Checked, not gated: every push and pull request, through `conflict-marker-check.yml`. A push to `main` is live before the check reports. A pull request is blocked only if branch protection requires the check. The intel commit (`fetch-intel` job), the search-index commit (`refresh-search-index.yml`) and commits made by hand get only this check.
- Allowances: `base_prices` in `base_date.json` and `usd_price` / `base_price_usd` in `commodities_index.json` until their writers next run, and `last_close` in `data/registries/marketstack_symbols.json` (removed on another branch). All warn until 31 October 2026 and fail after it.

## Dry runs

`ROBOTNIK_INDEX_OUT`, `COMMODITIES_INDEX_OUT` and `COMPOSITE_INDEX_OUT` accept any path. Inside the repository, use `data/private/` or a path whose name contains `dryrun` or `staging`; `.gitignore` keeps those out of commits.

## Rollback

If this change is reverted after the first record without `base_price_usd` is published, the reverted calculator fetches as before and then stops with `KeyError: 'base_price_usd'`. Nothing is written or published, but the commodities and composite indices stop advancing until the change is restored. Restoring the old fields instead would publish raw prices again.
