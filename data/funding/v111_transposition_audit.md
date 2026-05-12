# v1.1.1 Pre-Rewrite Take Transposition Audit

**Date:** 2026-05-12
**Scope:** 172 rows in the 2025 funding backlog (pre-v1.1.1 rewrite). Source: `/tmp/v111_backlog/batch_{1..4}.json`.
**Method:** For every row, compared the pre-v1.1 `current_take` field against the v1.1 `company_description` field. Flagged only rows where the two fields describe substantively DIFFERENT businesses, products, or industries (the Neros pattern). Did not flag rows that were merely thin, fragmentary, mis-categorized in `sector`/`subsector`, or that mentioned a different product line within the same company.

## Verdict

**ONE-OFF.** Exactly 1 confirmed transposition. The Neros case appears to be an isolated v1.0 ingestion error, not a systemic pattern across the 2025 backlog.

## Flagged Rows (Confirmed Transpositions)

| entity_id | date | company | current_take says | company_description says | Why this is transposition |
|-----------|------|---------|-------------------|--------------------------|----------------------------|
| neros | 2025-11-07 | Neros (Series B, $75M) | "AI compute infrastructure company building custom silicon for inference workloads. … Competes with Groq, Cerebras, and NVIDIA (NVDA) in inference. Watch for first customer deployments and benchmark results." | "Builds NDAA-compliant FPV combat drones for the US Army and allied militaries. Operates a Los Angeles factory producing kamikaze and reconnaissance drones at scale; sells primarily into the defense channel." | Take describes a fabless AI inference silicon startup (Groq/Cerebras competitor). Description correctly identifies Neros as an FPV combat drone manufacturer for DoD. The take's comp set (Groq, Cerebras, NVIDIA) is fully incompatible with an attritable-drone OEM. Subsector `Autonomous Systems & Drones` also matches the description, not the take. Classic transposition. |

## Borderline / Considered but Rejected

The following rows were inspected closely and DID NOT meet the transposition bar. They are recorded here for transparency.

- **xLight (idx 95, 2025-07-22 Series B; and idx 171, 2025-12-02 Grant).** Take describes "free electron laser EUV light source for semiconductor manufacturing … able to serve 20 ASML tools from one source." Company_description says "advanced photonic integrated circuit manufacturing capacity in the US … competes with GlobalFoundries and AIM Photonics." These describe genuinely different businesses (a lithography light-source company vs. a PIC fab). **However:** xLight (the real entity) is publicly documented as developing FEL-based EUV light sources, so the TAKE is accurate to the company. This looks like a `company_description` error introduced during v1.1, not a `current_take` transposition. Out of scope for this audit (which targets pre-v1.1 take transpositions, the Neros pattern). Recommend separate review of v1.1 company_description for `xlight`.

- **Lila Sciences (idx 32, 2025-03-15 Seed).** `sector="Robotics"`, `subsector="Silicon & Substrates"` — clearly mis-categorized metadata. But `current_take` ("AI Science Factories combining foundation models + lab robots for materials science") and `company_description` (AI-driven scientific discovery platform with lab automation) describe the same business. Not a transposition.

- **Robot Era (idx 79, 2025-07-08 Series A).** Take cites STAR1/L7 bipedal humanoids and ERA-42 AI brain; description cites the Xing Xing humanoid platform. Both clearly identify the same company (Chinese Tsinghua humanoid spinout). Different product naming but same business. Not transposition.

- **RoboForce (idx 39, 2025-05-20 Seed extension).** Take says "Force-controlled industrial robots for contact-rich assembly tasks." Description says "AI-powered industrial robots for heavy manufacturing applications … competes with FANUC, ABB, and Veo Robotics." Both describe industrial robots; "force-controlled / contact-rich assembly" is a specific framing of the same business. Not transposition.

- **Reflect Orbital (idx 52, 2025-05-14 Series A).** Take and description both describe orbital mirror constellation for redirecting sunlight. Match.

- **Multiple thin / fragment-style takes** (e.g., Aethero, ElectraLith, ArkEdge Space, Alta Resource, several others). Pre-v1.1 takes are routinely brief or under-developed. None describe a different industry from the company_description. Not transpositions.

## Patterns Observed

- The single confirmed case (Neros) is in `Robotics / Autonomous Systems & Drones` with a 2025-11-07 date and Sequoia as lead. No clustering signal — only one data point.
- No date clustering, no source clustering, no sector clustering detectable across 172 rows. The Neros case appears genuinely isolated.
- One adjacent data-hygiene issue surfaced (xLight company_description likely incorrect at v1.1), but it is the inverse pattern (description wrong, take right) and is outside this audit's scope.

## Total time spent

Approximately 18 minutes (read 4 batch files, 172-row sweep, cross-check on borderline candidates, draft).
