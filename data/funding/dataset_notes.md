# Funding Dataset — Documentation Notes

**v1.0.1 (2026-05-06)**

This document captures known dataset limitations, methodology notes, and acceptance criteria for downstream consumers (VCs, analysts).

## Schema

Canonical 21 fields + 4 optional FX fields + 1 status field. See [`prompts/monthly_ingestion_template.md`](../../prompts/monthly_ingestion_template.md) for the full spec.

## Coverage window

- **Earliest dated row:** 2023-01-02
- **Latest dated row:** 2026-04-30
- **Total rows:** 1,133 (post-v1.0.1 remediation including spot-check resolutions)

## Known limitation: sub-$25M long-tail rounds in 3Q25–4Q25

**24 rows** in 3Q25 (n=4) and 4Q25 (n=20) where `amount_m < 25` were flagged as `unverifiable` by the bulk data audit. These are mostly small early-stage rounds across mixed geographies (USA n=8, France n=3, Belgium n=2, Switzerland n=2, plus singles from Norway, Germany, Israel, Italy, South Korea, India, UAE, UK).

The pattern is **aggregator-only sourcing** — primary press (TechCrunch, Reuters, etc.) typically don't cover sub-$25M rounds outside flagship cases. Sources like Pulse 2, EU-Startups, FinSMEs, RoboticsTomorrow are the surface, but the bulk audit couldn't independently verify against company-direct primary sources within timing.

**Acceptance:** Per user decision (2026-05-06), these rows are accepted as-is in v1.0.1. Pattern is a known artifact of:
- Sub-$25M rounds rarely receiving English trade-press coverage
- Aggregator coverage being the primary surface for the long tail
- Anti-fabrication rules favor "verified-but-aggregator" over "fabricated-but-canonical"

If a downstream consumer needs higher confidence on a specific row, recommend manual triage against the company's own newsroom or LinkedIn announcement.

The list is preserved at `/tmp/sub_25M_unverifiable_rows.json` (24 rows, mostly US/EU/Asia early-stage).

## Source URL audit summary (post-v1.0.1)

| Status | Count | % |
|--------|------:|---:|
| `verified` — URL confirmed live or paywall-citable | 1,058 | 93.4% |
| `archived` — out-of-scope per freshness rule (date >365d AND amount <$500M) | 75 | 6.6% |
| `pending` — awaiting spot-check approval | 0 | 0.0% |
| **Total** | **1,133** | **100%** |

**In-scope verified rate: 100%** (1,058 / 1,058) — exceeds the ≥95% target.

## URL freshness rule (in scope vs out of scope)

A row's `source` URL must be valid (returns 200/301/302) if either:
- `date` falls within the last 365 days from current date, OR
- `amount_m >= 500` (i.e., ≥ $500M, regardless of age)

Out-of-scope rows can have dead URLs and are marked `source_status: archived`. They remain in the dataset because the deal is verified; only the citation is stale.

## Anti-fabrication rules (locked at v1.0.1)

Every URL in the dataset must:
1. Be HEAD-requested and confirmed to return 200/301/302 before being recorded
2. Prefer canonical company press release pages > trade publications > aggregators
3. Be **verbatim** from search results — never constructed from URL patterns
4. Use `source_status: pending` instead of fabricating a URL

See [`prompts/monthly_ingestion_template.md`](../../prompts/monthly_ingestion_template.md) Rules 1–7.

## Quarter migrations from v1.0 → v1.0.1

23 rows changed quarter during the remediation pass (Pacific Fusion, Hadrian, Mujin, CMR Surgical, Zap Energy, Starfish Space, Lyte, Infravision, constellr, SatVu, Cambridge GaN Devices, Distalmotion, Tokamak Energy, Turion Space, plus the Zipline phantom drop and extension add). Full log at [`v1_0_remediation_log.md`](v1_0_remediation_log.md) and [`v1_0_data_quality_issues.md`](v1_0_data_quality_issues.md).

## v1.0 vs v1.0.1

- **v1.0** (git tag, locked 2026-05-06 morning): Pre-remediation snapshot. 1,154 rows. ~12% of source URLs were agent-fabricated. Used for the initial CSV export.
- **v1.0.1** (git tag, locked 2026-05-06 afternoon): Post-remediation. 1,135 rows. 99.3% in-scope verified. Anti-fabrication rules added. The version that ships to Tier 1 VCs.

## Deal-type classifier convention

```python
def classify(r):
    if r['sector'] == 'Token':
        return 'token'
    if r['round'] == 'Strategic':
        return 'strategic_corporate'
    if r['round'] in ('Government investment', 'Government', 'Grant'):
        return 'government'
    if r['round'] == 'Debt Financing':
        return 'debt'
    return 'venture'
```

`venture` includes IPO and IPO (filed) and M&A by classifier convention. For "true venture" comparisons, exclude `round in ('IPO', 'IPO (filed)', 'M&A', 'Pre-IPO')` from the venture bucket.

## Excluded categories (rules locked at v1.0)

- **Public secondaries / PIPEs at already-listed companies** (Aurora rule)
- **Pure-software crypto plays** (zkVM, MEV, custody, social platforms, cross-chain L1) — don't fit hardware-anchored thesis
- **Conditional government commitments** (CHIPS Act PMTs, DOE LPO conditional, DPA LOIs) — only binding awards count
- **Parent-corporate capex commitments** without a discrete equity/debt raise
- **M&A divestitures** of business units from non-universe parents (e.g., Honeywell W&WS carve-out)
- **Routine procurement contracts** (SBIR awards, OTAs, etc. — only meaningful capital events)
