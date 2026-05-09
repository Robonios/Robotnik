# v1.0 URL Replacements — Medium + Low Confidence Spot-Check
**Date:** 2026-05-06
**Scope:** 20 medium/low-confidence URL replacement candidates (84 high-confidence already applied per approval)

## Status snapshot

| State | Count | Notes |
|---|---:|---|
| Still pending — needs spot-check | 9 | URLs not yet applied; review below before mutating |
| Already dropped (per DQ approval) | 11 | Row removed from dataset; no URL action |
| **Total** | **20** | |

## STILL PENDING — spot-check these URLs before mutation (9)

Approve `[Y]` or reject `[N]` per row. Approved URLs will be applied to the row's `source` field with `source_status: verified`.

| Approve | idx | Company | Date | $M | Conf | Current | Proposed | Source |
|:-------:|----:|---------|------|---:|:----:|---------|----------|--------|
| [ ] | 218 | **Etched.ai** | 2026-01-14 | $500 | medium | `https://techcrunch.com/2026/01/14/etched-raises...` | `https://www.bloomberg.com/news/articles/2026-01-13/ai-chi...` | Bloomberg (paywall) |
| [ ] | 222 | **PsiBot** | 2026-03-10 | $280 | low | `https://autonews.gasgoo.com/articles/news/2-bil...` | `(NONE FOUND)` | no canonical source found in Western trade pres... |
| [ ] | 129 | **D-Robotics** | 2025-09-10 | $270 | medium | `https://techcrunch.com` | `https://www.yicaiglobal.com/news/chinas-d-robotics-raises...` | Yicai Global |
| [ ] | 197 | **ICEYE** | 2025-12-05 | $163 | medium | `https://spacenews.com` | `https://breakingdefense.com/2025/12/germany-awards-iceye-...` | Breaking Defense |
| [ ] | 115 | **Fourier Intelligence** | 2025-08-20 | $120 | low | `https://techcrunch.com` | `(NONE FOUND)` | no canonical Western press article found for Au... |
| [ ] | 60 | **ClearSpace** | 2025-06-01 | $95 | medium | `https://esa.int` | `https://www.esa.int/Space_Safety/ESA_purchases_world-firs...` | ESA |
| [ ] | 203 | **ENCOS** | 2025-12-15 | $28 | medium | `https://autonews.gasgoo.com/articles/news/china...` | `https://pandaily.com/encos-raises-nearly-28-m-to-lead-the...` | Pandaily |
| [ ] | 75 | **Turion Space** | 2025-06-18 | $20 | medium | `https://spacenews.com` | `https://www.veteranventures.us/news1/announcing-a-strateg...` | Veteran Ventures Capital |
| [ ] | 137 | **Anvil Robotics** | 2025-09-20 | $5 | low | `https://techcrunch.com` | `https://news.crunchbase.com/robotics/physical-ai-custom-r...` | Crunchbase News |

## DROPPED — for context only (11)

These rows have already been removed from the dataset per approved DQ drops. Listed here so you can see the full medium+low scope of the URL replacement audit.

| idx | Company | Date | $M | Conf | Reason for drop |
|----:|---------|------|---:|:----:|-----------------|
| 132 | Kargo | 2025-09-15 | $100 | low | no canonical source found for $100M Kargo Series A in September 2025. Most recent confirmed funding is $42M Series B in  |
| 133 | General Fusion | 2025-09-15 | $73 | low | no canonical source found for $73M bridge funding in September 2025. Search shows General Fusion raised $30M CAD in Aug  |
| 52 | RobCo | 2025-05-10 | $52 | low | Best matches are RobCo's $42.5M Series B (2024). No $52M round in May 2025 found. Recommend manual triage — amount or da |
| 93 | Bonsai Robotics | 2025-07-10 | $50 | low | DATA QUALITY: Bonsai Series A was $15M in January 2025, not $50M in July 2025. The July 2025 event was the farm-ng acqui |
| 101 | EndoQuest Robotics | 2025-07-20 | $36 | low | No $36M Series A in July 2025 found. EndoQuest closed a $59M round in July 2025 (lifting valuation to $319M). Recommend  |
| 112 | Generative Bionics | 2025-08-15 | $35 | low | DATA QUALITY: Generative Bionics is Italian humanoid robotics (IIT spinoff), not prosthetics. The 70M EUR (~81M USD) see |
| 166 | TRIC Robotics | 2025-11-05 | $30 | low | DATA QUALITY: TRIC Robotics' most recent funding is $5.5M seed in July 2025 — no $30M Series A in November 2025 found. R |
| 59 | Contoro Robotics | 2025-05-20 | $20 | low | DATA QUALITY: Contoro $12M Series A was announced March 2025, not May 2025. No $20M round in May 2025 found. Recommend m |
| 79 | SwarmFarm | 2025-06-25 | $18 | low | No $18M round in June 2025 found. SwarmFarm's Series B was $19.85M in October 2025. Recommend manual triage on date/amou |
| 122 | Surgerii Robotics | 2025-09-05 | $15 | low | DATA QUALITY: Surgerii Robotics' $100M Series D was December 2025; no $15M seed in September 2025 found. September 2025  |
| 200 | Dyna Robotics | 2025-12-10 | $6 | low | DATA QUALITY: No $6M round in December 2025 for Dyna Robotics found. Their Series A was $120M in September 2025, seed wa |

## How to apply approved mutations

After spot-check, list approved row idxs (e.g., "approve idx 226, 350, 412") or just "approve all" / "reject all". I'll apply mutations and re-run the URL audit to confirm dataset health.
