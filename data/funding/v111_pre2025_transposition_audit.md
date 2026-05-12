# Pre-2025 Take/Description Transposition Audit (v1.1.1)

**Date:** 2026-05-12
**Scope:** All rows in `data/funding/rounds.json` where `date < 2025-01-01`
**Rows audited:** 776 (772 with both `robotnik_take` and `company_description`; 4 with empty description and no transposition signal)
**Comparison:** `robotnik_take` vs `company_description` for subject-matter alignment

## Verdict: Rare (3 flags total)

The pre-2025 corpus is markedly cleaner on take/description alignment than 2025-vintage. Three confirmed mismatches, all isolated, no clustering by sector / quarter / source.

- TRANSPOSITION (take wrong, description right): **2**
- INVERSE (description wrong, take right): **1**

---

## TRANSPOSITION cases (take wrong, description right)

| entity_id | date | company | what take says | what description says | verification | recommendation |
|---|---|---|---|---|---|---|
| `impulse-space` | 2024-10-01 | Impulse Space | "Final private round before the long-telegraphed **RISC-V IPO**; NVIDIA strategic + Atreides lead reads as IPO syndicate forming. Comp framing is brutal: ARM (ARM) at >100B market cap is the public reference, and **SiFive is being priced as the RISC-V challenger**…" — describes a semiconductor / RISC-V IP business. | "Builds in-space transportation vehicles — the Mira orbital tug for last-mile satellite delivery and Helios kick stage for direct-to-GEO transfers. Founded by former SpaceX propulsion lead Tom Mueller…" | Source URL is SpaceNews announcement of $150M Series B for Impulse Space; the company's other pre-2025 row (`idx=572`, 2023-07-24) carries a correct take ("Tom Mueller's (ex-SpaceX) in-space mobility startup… funds Helios kick stage and Mira tug"); description is consistent with both rows and with public record. | **Description is right.** Take appears to be content meant for a SiFive / RISC-V IPO row that was pasted onto the wrong entity. Recommend regenerating `robotnik_take` for this row from the SpaceNews source. |
| `hanyang-technology` | 2023-05-12 | Hanyang Technology | "Intelligent service-robot R&D; Shenzhen-based competitor in China's crowded service-robot stack **vs. Pudu, Keenon**." — describes a hospitality / commercial service-robot business. | "Chinese manufacturer of the **Yarbo modular yard robot**, with interchangeable snow-blower and lawnmower attachments. Targets cold-climate North American consumers as a competitor to Husqvarna and Worx." | Description matches `idx=613` (Yarbo entity, same Kickstarter / cold-climate / yard-care positioning). Same entity's earlier 2023-03-15 row (`idx=611`) carries a correct take referencing "Yarbo modular yard-robot maker (snow blower + lawnmower attachments)… competitor to Husqvarna/Worx." Web confirms Hanyang Technology = Yarbo (Shenzhen-based, founded 2015, Pandayoo / Pandaily / 36kr / People's Daily / Yarbo company coverage). | **Description is right.** Take was apparently confused with one of the many Chinese commercial-service-robot rounds in the same May 2023 batch. Recommend regenerating `robotnik_take` referencing Yarbo / yard-care / Husqvarna comp. |

## INVERSE cases (description wrong, take right)

| entity_id | date | company | what take says | what description says | verification | recommendation |
|---|---|---|---|---|---|---|
| `ncodin` | 2024-05-28 | NcodiN | "**Optical interposer using nanolasers for chiplet-to-chiplet interconnect**. Targets the same packaging-bottleneck thesis as Ayar Labs / Lightmatter." | "French designer of **neuromorphic AI processors for edge computing** applications. Competes with Intel Loihi, BrainChip, and SynSense in neuromorphic chips." | Source URL (`https://tech.eu/2024/05/28/ncodin-secures-eur35-million-for-optical-interposer-technology/`) headline and body confirm optical interposer / integrated nanolaser business. Web fetch of source confirms: "optical interposer that enables high-bandwidth, low-latency optical data communications between chiplets within a processor package" using "integrated semiconductor nanolasers." Take is correct; description appears to be wholesale wrong (no public record of NcodiN doing neuromorphic chips). | **Take is right.** Recommend regenerating `company_description` as: "French developer of optical interposer technology using integrated semiconductor nanolasers for chiplet-to-chiplet optical interconnect within processor packages. Comparable thesis to Ayar Labs and Lightmatter in co-packaged optics, targeting AI / HPC packaging bottleneck." |

---

## Borderline cases considered and rejected

| entity_id | date | issue considered | reason rejected |
|---|---|---|---|
| `foundation-humanoid` (idx=149) | 2024-08-22 | TAKE talks about founder's prior fintech (Synapse bankruptcy), DESC about humanoid robotics. | Not a transposition: TAKE explicitly contextualizes the founder's bankrupt fintech as a credentialing-risk note; DESC also references the same fintech as part of founder bio. Same subject. |
| `vsora` (idx=440) | 2023-11-02 | TAKE: "French generative AI inference accelerator… EU sovereign alternative to NVDA/AMD in datacenter compute." DESC: "Tyr family of automotive ADAS and autonomous driving compute IP for L2+ to L5 vehicles." | Borderline but VSORA's own EIC announcement (verified via web fetch) shows the company markets both Tyr (automotive) and Jotunn (genAI inference / datacenter chiplet). Take emphasizes the genAI side (the EIC grant rationale); description emphasizes automotive. Multi-product company — not a transposition under conservative rules. Same entity's earlier 2023-01-11 row (`idx=750`) describes the Tyr/auto side, which fits DESC. |
| `cerebras-systems` (idx=118, 119) | 2024-09-30 | Lowest Jaccard overlap (0.00) — both rows talk about Cerebras IPO mechanics while DESC describes wafer-scale architecture. | Same business: IPO filing and Series F-1 of the wafer-scale AI chip company. TAKE focuses on capital-markets event, DESC on architecture. No subject mismatch. |
| `impulse-space` (idx=572) | 2023-07-24 | Already-validated correct row from same entity. | Cross-references support the idx=4 flag above; no issue here. |
| `taalas` (idx=303) | 2024-03-06 | TAKE talks about Tenstorrent/AMD alums + "direct competitor to Etched"; DESC about HC1 model-specific AI chips on TSMC. | Both consistent: Etched also does model-specific transformer ASICs (same product category). Take and DESC describe same business at different angles. |
| Short-take rows in 2023 (e.g., `tokamak-energy`, `zap-energy`, `turion-space`, etc.) | various 2023-2024 | Fragment-style takes are common in early-quarter 2023 backfills. | Per scope rules, fragment takes were only flagged if subject matter mismatched. All checked: subject matter agreed. |
| `iceye` (idx=176) | 2024-04-17 | TAKE jaccard=0.00 against DESC because TAKE is short ("Sovereign Solidium leads SAR-leader's growth round…") and DESC uses different vocabulary. | Both describe ICEYE's SAR business. No mismatch. |
| `shield-ai`, `pony-ai`, `nimble-robotics`, `spacex`, `mangata-networks` (low-overlap idxs 369, 374, 725, 754, 758) | 2023-01–2023-12 | Low Jaccard scores. | All examined; each TAKE describes the same company / business as its DESC, just emphasizing the round mechanics rather than the company's core product. |

---

## Pattern observations

- **No clustering.** The three flags span three different sectors (Space, Robotics, Semiconductors), three different quarters (Q2-2023, Q2-2024, Q4-2024), and three different sources (SpaceNews press release, Robot Report aggregate, tech.eu primary). No common reviewer or batch artifact is apparent.
- **Same failure mode as 2025 audit.** Two of three look like content paste errors during batch generation: text intended for a different deal (likely SiFive for `impulse-space` Q4-2024, a different Chinese service-robot round for `hanyang-technology` Q2-2023, or a different French semi for `ncodin`) ended up on the wrong row. This is consistent with the v1.1 Q2-2025 Neros/MACH/xLight pattern.
- **Entity-cross-check helped.** Both Impulse Space and Hanyang Technology have *correct* sibling rows for the same `entity_id` at different dates. Future regen passes should diff `robotnik_take` against existing-correct sibling rows for the same `entity_id` as a cheap cross-validation.
- **Description quality is mostly excellent.** Only one inverse case (NcodiN) found across 772 descriptions — implies the description-generation process has been very reliable for pre-2025 vintage. The single failure cluster is in `robotnik_take` content paste errors.
- **Empty descriptions, not transpositions.** Four pre-2025 rows have empty `company_description` (`ruizhu-technology`, `true-health`, `clodot`, `blue-ocean-robot` — all 2023 Chinese rows). These are scope-out (no description means no transposition possible) but worth flagging for a separate description-backfill task.

---

## Total

- Pre-2025 rows audited: 776 (772 with both fields populated)
- TRANSPOSITION (take wrong): **2** (`impulse-space` 2024-10-01, `hanyang-technology` 2023-05-12)
- INVERSE (description wrong): **1** (`ncodin` 2024-05-28)
- Empty-description rows (out of scope for transposition, scope for separate backfill): 4
- Borderline considered-and-rejected: ~8
- Net pre-2025 take/description-pair flagged rate: 3 / 772 = 0.39%

Combined with the 2025 audit (3 flags across 172 rows = 1.74%), the v1.1 dataset's full-corpus pair-mismatch rate is 6 / 944 = 0.64%.

