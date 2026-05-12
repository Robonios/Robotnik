# Investor Field Placeholder Audit — v1.1.1

**Date:** 2026-05-12
**Scope:** `data/funding/rounds.json` (1,132 rows). Audit of `lead_investors` and `co_investors` for vague placeholder values (e.g., "Multiple", "Various", "Existing investors", "Other existing and new investors", "Multiple state-backed investors") that break downstream groupby aggregation.

**Fix rule:**
- `lead_investors` unknown / placeholder → `Undisclosed`
- `co_investors` unknown / placeholder → empty string (`""`)
- Named investors buried inside an "Existing investors (...)" string are extracted to `co_investors` when they can be cleanly separated.
- No fabrication. When the source URL does not resolve a real lead, fall back to `Undisclosed`.

**Totals:** 12 `lead_investors` fixes · 14 `co_investors` fixes · 2 rows flagged for `robotnik_take` descriptive-content migration (no take modifications performed in this audit).

---

## Table 1 — `lead_investors` Fixes

| entity_id | company | date | current | proposed | source / rationale |
|---|---|---|---|---|---|
| `electralith` | ElectraLith | 2025-01-16 | `Multiple` | `Undisclosed` | TechCrunch source URL 404. WSJ headline ("ElectraLith Raises $17M to Produce Low-Cost Lithium Without China") behind paywall. Company site lists Marathon, Rio Tinto among backers but does not designate Jan-2025 lead. Fall back to Undisclosed. |
| `fairmat` | Fairmat | 2025-04-02 | `Multiple` | `Undisclosed` | TechCrunch source URL 404. Cross-source attempts (tech.eu, eu-startups) returned 403 / 404 / no record. Cannot identify a single lead with confidence. Fall back. |
| `roboforce` | RoboForce | 2025-05-20 | `Multiple` | `Undisclosed` | The Robot Report source says only "an additional $5 million in funding from new and existing investors" — no named lead. Fall back. |
| `albedo` | Albedo | 2025-04-23 | `Multiple` | `Undisclosed` | SpaceNews URL paywalled / 429. Payloadspace 404. No alternative source successfully fetched naming a single lead. Fall back. |
| `aethero` | Aethero | 2025-06-11 | `Multiple` | `Kindred Ventures` | Satellite Today source confirms **Kindred Ventures led**; Neo, Giant Step, O'Shaughnessy Ventures, Alumni Ventures co-invested. (Co-investors string is currently empty — recommend populating with these names in a follow-up content pass; out of scope for this placeholder-only audit.) |
| `turion-space` | Turion Space | 2024-12-02 | `Multiple` | `Undisclosed` | PR Newswire source announces Veteran Ventures Capital's investment but does **not** designate VVC as lead and does not name others. Fall back to Undisclosed. (NB: a separate `turion-space` row dated 2024-12-02 already carries `lead=Undisclosed` / `co=Veteran Ventures Capital` — confirm no duplicate before applying.) |
| `infravision` | Infravision | 2025-11-03 | `Multiple` | `GIC` | Company press release explicitly states "$91 Million Series B led by GIC". User-confirmed fix. |
| `mujin` | Mujin | 2025-12-02 | `Multiple` | `NTT Group, Qatar Investment Authority` | Mujin Series D press release names **NTT Group as lead** and **Qatar Investment Authority as co-lead**; Mitsubishi HC Capital Realty and Salesforce Ventures also participated in equity (candidates for co_investors in a follow-up content pass). |
| `commcrete` | Commcrete | 2025-09-30 | `Multiple` | `Undisclosed` | Armada International source URL returned 403; no alternative source surfaced a named lead. Fall back. |
| `constellr` | constellr | 2026-02-10 | `Multiple` | `Alpine Space Ventures, Lakestar` | Company press release: **Alpine Space Ventures led**, **Lakestar co-led**. Other participants (Semapa Next, Bayern Kapital, Cardumen Capital, Cooperative Ventures, Kineo Finance, plus existing shareholders Vsquared / CosmiCapital / FTTF / EIC Fund) are co_investor candidates for a follow-up content pass. |
| `hailo` | Hailo | 2024-04-02 | `Existing investors (Zisapel family, Gil Agmon, Delek Motors, Alfred Akirov, DCLBA, Vasuki, OurCrowd, Talcar, Comasco, Automotive Equipment, Poalim Equity)` | `Undisclosed` | Hailo press release describes the round as "led by current and new investors" without designating a single lead. Per fix rule, lead → `Undisclosed`; the eleven named participants migrate to `co_investors` (see Table 2 below). |
| `skydio` | Skydio | 2026-04-23 | `Undisclosed (existing investors)` | `Undisclosed` | User-specified fix. Skydio blog confirms round was "led by existing investors" with no names disclosed. Strip parenthetical, normalize to `Undisclosed`. |

---

## Table 2 — `co_investors` Fixes

| entity_id | company | date | current | proposed | source / rationale |
|---|---|---|---|---|---|
| `atlant-3d` | ATLANT 3D | 2025-03-11 | `Existing investors` | `""` (empty) | No specific names disclosed in source PR. Per fix rule. |
| `anduril-industries` | Anduril Industries | 2025-06-02 | `Other existing and new investors` | `""` (empty) | User-specified fix. Crunchbase News source does not enumerate co-investors. |
| `spinlaunch` | SpinLaunch | 2025-08-18 | `Existing investors` | `""` (empty) | SpaceNews source does not name specific co-investors beyond the leads (Kongsberg Defence & Aerospace, ATW Partners). |
| `paragraf` | Paragraf | 2025-08-25 | `Existing investors` | `""` (empty) | tech.eu source confirms Mubadala as lead but does not name specific co-investors. |
| `quantum-systems` | Quantum Systems | 2024-09-24 | `Existing investors` | `""` (empty) | Company press release does not enumerate co-investors. |
| `medical-microinstruments` | Medical Microinstruments | 2024-02-21 | `Existing investors not disclosed` | `""` (empty) | The phrase itself states non-disclosure; remove. |
| `aqua-robotics` | Aqua Robotics | 2024-01-30 | `Existing investors` | `""` (empty) | Undercurrent News source does not name specific existing co-investors. |
| `talon-metals` | Talon Metals | 2023-10-12 | `Various institutional investors via non-brokered private placement of 80.35M shares at C$0.27/share` | `""` (empty) | Descriptive placement-mechanics text, no investor names. Note: structural detail (80.35M shares @ C$0.27) may belong in `robotnik_take` — see special-handling section. |
| `runpeng-semiconductor` | Runpeng Semiconductor | 2023-08-14 | `Multiple state-backed investors; parent China Resources Microelectronics` | `China Resources Microelectronics` | Parent strategic (China Resources Microelectronics) is a named entity and should be retained as co-investor. Strip the placeholder "Multiple state-backed investors" preamble. Descriptive context flagged for take migration. |
| `axiom-space` | Axiom Space | 2023-08-21 | `Various venture capital funds and strategic brand partners` | `""` (empty) | No named entities; pure placeholder. |
| `space-pioneer-beijing-tianbing-technology` | Space Pioneer (Beijing Tianbing Technology) | 2023-07-01 | `Disclosed multiple Chinese state-linked and private investors (consortium); cumulative raised ~US$414M` | `""` (empty) | Placeholder descriptor + cumulative-raise stat. Note: cumulative-raise context flagged for take migration (see special-handling section). Lead is also empty for this row. |
| `orienspace-dongfang-space-yantai-dongfang-space-technology` | Orienspace | 2023-08-05 | `Multiple Chinese state-linked and private investors (consortium)` | `""` (empty) | Placeholder descriptor only. Note: descriptive content may belong in `robotnik_take` — flagged. Lead is also empty for this row. |
| `hailo` | Hailo | 2024-04-02 | `""` (empty) | `Zisapel family, Gil Agmon, Delek Motors, Alfred Akirov, DCLBA, Vasuki, OurCrowd, Talcar, Comasco, Automotive Equipment, Poalim Equity` | User-specified fix — migrate the eleven named participants out of the placeholder `lead_investors` string into `co_investors`. |
| `stardust-power` | Stardust Power | 2024-07-08 | `PIPE syndicate (undisclosed)` | `""` (empty) | Pure placeholder ("syndicate (undisclosed)"). No named entities. Entity_id is recorded as `SDST` (ticker form). |

---

## Special-Handling Notes — Descriptive Content Flagged for `robotnik_take` Migration

These rows contain analytically useful descriptive content embedded in `co_investors`. The audit removes the placeholder from `co_investors` per the fix rule, but **the underlying information is worth preserving in `robotnik_take`** in a follow-up content pass. **No takes are modified in this audit.**

1. **`runpeng-semiconductor` (2023-08-14)** — "Multiple state-backed investors" descriptor signals state-driven syndicate around China Resources Microelectronics parent stake. Useful colour for take: round is a clear example of Chinese state-coordinated semiconductor financing layered atop a SOE parent.
2. **`space-pioneer-beijing-tianbing-technology` (2023-07-01)** — "Multiple Chinese state-linked and private investors (consortium); cumulative raised ~US$414M" — the **$414M cumulative-raise** datum and the state-linked consortium structure are both worth surfacing in the take, not the co-investors field.
3. **`orienspace-dongfang-space-yantai-dongfang-space-technology` (2023-08-05)** — "Multiple Chinese state-linked and private investors (consortium)" — consortium-structure observation belongs in take rather than as a `co_investors` value.
4. **`talon-metals` (2023-10-12)** — Mechanism detail ("non-brokered private placement of 80.35M shares at C$0.27/share") is structurally informative and belongs in `robotnik_take` if not already noted.

Audit also notes the following sources where partial co-investor enrichment is **available but out of this audit's scope** (placeholder-only) — flag for the v1.1.x content pass:

- `aethero` (2025-06-11): Neo, Giant Step, O'Shaughnessy Ventures, Alumni Ventures (per Satellite Today).
- `mujin` (2025-12-02): Mitsubishi HC Capital Realty, Salesforce Ventures (per Mujin press release).
- `constellr` (2026-02-10): Semapa Next, Bayern Kapital, Cardumen Capital, Cooperative Ventures, Kineo Finance, Vsquared, CosmiCapital, FTTF, EIC Fund (per constellr press release).

---

## Summary Statistics

| Metric | Count |
|---|---|
| Total rows scanned | 1,132 |
| `lead_investors` placeholder rows | 12 |
| `lead_investors` rows resolved to a real lead via source | 4 (Aethero, Infravision, Mujin, constellr) |
| `lead_investors` rows falling back to `Undisclosed` | 8 |
| `co_investors` placeholder rows | 13 (incl. 11 reductions to `""` + 1 partial retain for Runpeng + 1 stripping of Hailo-style noise) |
| New `co_investors` populated via name migration | 1 (Hailo — 11 named participants moved from `lead_investors`) |
| Rows flagged for descriptive-content migration to `robotnik_take` (NOT modified by this audit) | 4 (Runpeng, Space Pioneer, Orienspace, Talon Metals) |
| Source URLs that failed to fetch during investigation (403/404/429) | 6 (ElectraLith TC, Fairmat TC, Albedo SpaceNews, Commcrete Armada, RoboForce alt, multiple search-engine consent walls) |

**Net total placeholder fixes:** **26 rows** (12 lead + 14 co-investor row mutations) across the 1,132-row corpus.

**Next steps for v1.1.1 release:**
1. Apply the Table 1 + Table 2 mutations to `data/funding/rounds.json` (separate write-pass; this document is the spec).
2. Re-run any downstream groupby aggregations to confirm no remaining "Multiple" / "Various" / "Existing investors" tokens leak into investor-keyed views.
3. Defer the take-migration work (4 rows in special-handling) to a content-editing pass, not a placeholder fix.
4. Optional follow-up: enrich `co_investors` for Aethero, Mujin, and constellr using source-confirmed names from this audit.
