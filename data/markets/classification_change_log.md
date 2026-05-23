# Public Equities Classification Change Log

Tracks reclassifications, subsector moves, and bottleneck-rating revisions
applied across enrichment runs. Sister document to
[metrics_methodology.md](metrics_methodology.md).

Format: `YYYY-MM-DD | ticker | field | from → to | reason`

---

## v1.0 — initial enrichment build (2026-05-23)

This was a build run, not a reclassification pass. No constituent had its
sector, subsector, value_chain, or bottleneck rating altered as part of the
enrichment work. The fields were read straight from their canonical sources:

| Field             | Source of truth                              |
|-------------------|----------------------------------------------|
| `sector`          | `data/registries/entity_registry.json`       |
| `subsector`       | `data/registries/entity_registry.json`       |
| `value_chain`     | `data/registries/entity_registry.json`       |
| `bottleneck_risk` | `data/markets/enrichment_data.json`          |

### Universe gating decisions (not reclassifications)

These are documented here so the audit trail captures *which* equities were
consumed by the enrichment pipeline and which were not:

- **50 equities skipped** because `registry.status == "excluded"`. Sample
  tickers: DVLT, FSLR, AGPXX, KOPN, PENG, RGTI, OLED, ANDR AV, 2317 TT,
  1274 HK. Effective active universe enriched = **254** of 304 in
  `data/prices/equities.json`.
- **0 equities quarantined** in this run (registry `status == "data_quarantine"`
  is empty as of generation).
- The 5-level *private* bottleneck enum (`Critical`, `High`, `Medium`, `Low`,
  `Pre-commercial`) does not include `Pre-commercial` at the public-equity
  level. Public companies are by definition revenue-generating and cannot
  qualify for `Pre-commercial`. The equity-side enum is therefore 4 levels:
  `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`. The cross-asset mapping is defined in
  [metrics_methodology.md § Bottleneck enum mapping](metrics_methodology.md#bottleneck-enum-mapping).

### Bottleneck distribution snapshot (eligible-universe basis)

Of 233 eligible constituents (after MIN_MARKET_CAP + sector ≠ Token gating):

| Rating   | Multiplier | Count | Share |
|----------|-----------:|------:|------:|
| CRITICAL |      ×4.0  |     2 |  0.9% |
| HIGH     |      ×2.5  |     7 |  3.0% |
| MEDIUM   |      ×1.5  |    16 |  6.9% |
| LOW      |      ×1.0  |    33 | 14.2% |
| UNRATED  |      ×1.0  |   175 | 75.1% |

Rating coverage at v1.0 = **24.9%** of the eligible universe. The
bottleneck-weighted composite is preliminary and labeled directional-only
until coverage exceeds 80% (see methodology doc).

---

## Future entries

Append below this line as reclassifications occur. Use idempotent action
descriptions so re-running the enrichment never silently overwrites prior
audit history.
