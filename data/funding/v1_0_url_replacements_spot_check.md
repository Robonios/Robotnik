# v1.0.1 URL Spot-Checks — Pending Approval

**Date:** 2026-05-06
**Scope:** 6 rows currently `source_status: pending` (all in-scope per freshness rule). 84 high-confidence URL mutations already applied; 11 phantom rows already dropped; 10 fixes already applied. These 6 are the residual cases that need a human call.

The actual count is **6** (was reported as "7 = 6 medium + 1 low" in the v1.0.1 tag annotation; one of the medium rows ended up applied during cleanup). Approve `[A]`, reject `[R]`, drop `[D]`, mark verified `[V]`, or flag `[F]` per row.

## Decisions to make

| Row | Action choice |
|-----|---------------|
| 1. Etched.ai $500M | `[A]` apply Bloomberg URL · `[R]` keep TechCrunch placeholder · `[D]` drop row |
| 2. ICEYE $163M | `[A]` apply Breaking Defense URL · `[R]` keep SpaceNews placeholder · `[D]` drop row · `[F]` flag for ICEYE direct PR search |
| 3. PsiBot $280M | `[V]` mark verified (Gasgoo URL already canonical — agent erred) · `[D]` drop row |
| 4. Fourier Intelligence $42M | `[D]` drop row · `[R]` accept current placeholder · `[F]` flag for re-search after amount fix |
| 5. ENCOS $27.5M | `[A]` apply Pandaily URL · `[R]` keep Gasgoo aggregate · `[D]` drop row |
| 6. Anvil Robotics $5M (Sep 2025) | `[D]` drop as phantom (per agent: only event is Apr 2026 $5.5M) · `[A]` apply Crunchbase News URL |

## Detailed rows

### 1. Etched.ai $500M (2026-01-14, 1Q26, Semis / Fabless Design)

**Current URL:** `https://techcrunch.com/2026/01/14/etched-raises-500m/` (returns 404 — agent-fabricated)

**Proposed replacement:** `https://www.bloomberg.com/news/articles/2026-01-13/ai-chip-startup-etched-raises-500-million-to-take-on-nvidia`

**Confidence:** medium (Bloomberg paywall but cite-worthy)

**Notes:** Bloomberg has the scoop dated 2026-01-13. Etched did not issue an official press release at the time (per Bloomberg "the company has not yet announced the funding officially"). Alternative non-paywall: `datacenterdynamics.com/en/news/etchedai-raises-500m-for-a-5bn-valuation-report/`.

**Recommendation:** Apply Bloomberg URL `[A]`. It's the most authoritative source and the paywall is acceptable — same convention we used for FT/WSJ-cited deals.

---

### 2. ICEYE $163M (2025-12-05, 4Q25, Space / Earth Observation)

**Current URL:** `https://spacenews.com` (placeholder — bare domain, no article)

**Proposed replacement:** `https://breakingdefense.com/2025/12/germany-awards-iceye-rheinmetall-almost-2b-for-new-sar-satellite-network/`

**Confidence:** medium

**Notes:** The proposed URL is about a Germany–Rheinmetall contract, not a clean ICEYE Series E announcement. Agent couldn't find a direct ICEYE-corporate press release for the Dec 2025 round. The $163M may be a journalist-aggregated figure across multiple Dec 2025 events.

**Concern:** Replacement URL doesn't cite a "$163M Series E" event directly — it's a different (larger) contract.

**Recommendation:** Hold on applying. Either (a) `[F]` flag for direct ICEYE corporate press search, or (b) `[D]` drop the row since the source is genuinely unclear, or (c) `[R]` keep placeholder until next monthly cleanup pass.

---

### 3. PsiBot $280M (2026-03-10, 1Q26, Robotics / Humanoid & Service Robots)

**Current URL:** `https://autonews.gasgoo.com/articles/news/2-billion-yuan-why-did-state-backed-capital-collectively-bet-on-this-robotics-startup-2031717172080922625`

**Proposed replacement:** None (agent reported "no canonical source found in Western trade press")

**Confidence:** low

**Notes:** This is the canonical-source row I personally fixed during the 1Q26 integrity pass on 2026-05-03 — the Gasgoo article IS the primary English-language source, which is why the second-pass agent's "no Western trade press" comment is stale. The row was given the Gasgoo URL already at that time. Agent simply didn't recognize Gasgoo as a valid Western trade pub.

**Recommendation:** Mark `[V]` (`source_status: verified`), no URL change. The current Gasgoo URL is already the canonical source. Agent's "low confidence" verdict is incorrect — this is a v1.0 false negative.

---

### 4. Fourier Intelligence $42M (2025-08-20, 3Q25, Robotics / Humanoid & Service Robots)

**Current URL:** `https://techcrunch.com` (placeholder)

**Proposed replacement:** None (agent reported "no canonical Western press article found")

**Confidence:** low

**Notes:** Amount was already fixed during major-fix pass ($120M → $42M / CNY 300M). FX captured. But no English-language source URL found. Agent's recommendation: manual triage. The deal IS real (Caixin and 36Kr have it in Chinese), just no English primary press.

**Recommendation:** This is the kind of row the `dataset_notes.md` sub-$25M caveat is intended to cover, but at $42M it's above that threshold. Either (a) `[D]` drop (no Western source) or (b) `[F]` flag for a second-pass with Mandarin-source acceptance (Caixin Pro / 36Kr). My lean: keep but mark `source_status: archived` (treat as out-of-scope per the dataset_notes acceptance) — but only if you accept Caixin/36Kr as legitimate primaries. Otherwise drop.

---

### 5. ENCOS $27.5M (2025-12-15, 4Q25, Robotics / Motion Control & Actuators)

**Current URL:** `https://autonews.gasgoo.com/articles/news/china-robotics-industry-financing-recap-for-december-2025` (Gasgoo monthly recap, not deal-specific)

**Proposed replacement:** `https://pandaily.com/encos-raises-nearly-28-m-to-lead-the-embodied-intelligence-core-components-race`

**Confidence:** medium

**Notes:** Pandaily article is deal-specific; Gasgoo recap is generic. Pandaily is a respected English-language China-tech outlet. ENCOS is a Chinese embodied-AI components company.

**Recommendation:** Apply Pandaily URL `[A]`. Better than the recap aggregate currently cited.

---

### 6. Anvil Robotics $5M (2025-09-20, 3Q25, Robotics / Industrial Robots)

**Current URL:** `https://techcrunch.com` (placeholder)

**Proposed replacement (low confidence):** `https://news.crunchbase.com/robotics/physical-ai-custom-robot-builder-seed-funding-anvil/`

**Confidence:** low — flagged for DROP

**Notes:** Per second-pass agent: "Anvil Robotics' $5.5M seed was announced April 2026, not September 2025." We already have a SEPARATE Anvil Robotics row at 2026-04-03 ($5.5M Seed extension). The Sept 2025 row appears to be the same fabrication pattern — there's no real Anvil Sept 2025 event.

**Recommendation:** **Drop** `[D]`. This row is a phantom; the only real Anvil event is captured in the April 2026 row.

---

## Summary recommendation

If you want speed:
- **Apply [A]** rows 1 (Etched.ai) and 5 (ENCOS) — solid replacements
- **Drop [D]** row 6 (Anvil Sep 2025) — confirmed phantom
- **Mark verified [V]** row 3 (PsiBot) — agent's "low" verdict was wrong; current Gasgoo URL is canonical
- **Hold / triage [F]** rows 2 (ICEYE) and 4 (Fourier Intelligence) — need additional research

Net effect: +2 URLs applied, +1 verified-correction, −1 phantom drop, 2 still pending → dataset 1,134 → 1,133, with 5 newly verified and 2 stay pending.

Or batch-approve everything and I'll execute.

## Files

- `data/funding/rounds.json` — current dataset (mutations frozen pending your call)
- `data/funding/v1_0_url_replacements_pending.md` — earlier comprehensive view (now stale, kept for history)
- `data/funding/v1_0_1_remediation_log.md` — full log of v1.0 → v1.0.1 mutations
