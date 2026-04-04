# Robotnik API Usage Ruleset

**Date:** 2026-04-02
**Purpose:** Govern how Robotnik's data pipeline uses external APIs

## API Tier System

### Tier 1 — Primary
| API | Purpose | Cost | Priority |
|-----|---------|------|----------|
| EODHD | Equity prices, market caps, fundamentals | $19.99/mo | Primary price source (equities) |
| CoinGecko | Token prices, market caps | Free (rate-limited) | Primary price source (tokens) |
| Claude API | News summaries, Robotnik's notes, RAG, predictions | Per-token | Primary intelligence layer |
| OpenAlex | Academic paper discovery | Free | Primary academic research |

### Tier 2 — Secondary
| API | Purpose | Cost | Priority |
|-----|---------|------|----------|
| SEC EDGAR | US company filings | Free (10 req/sec) | Primary for US filings |
| Brave Search | Web search for research, verification | Free ($5 credit, 1K/mo) | Supplement |
| Spectrawl | Web crawling for news RSS misses | Free | Supplement RSS |

### Tier 3 — Future/Evaluation
| API | Potential purpose | Status |
|-----|-------------------|--------|
| Finance WebSocket | Real-time prices | Park |
| Aletheia | Earnings transcripts | Evaluate |
| Alpha Vantage | Backup price source | Backup only |

## Usage Rules

1. **Tier 1 first, always** — never call secondary for data a primary covers
2. **Respect rate limits** — build in delays, stay below limits
3. **Cache aggressively** — never fetch same data twice per day
4. **Fail gracefully** — log, retry once, skip if still failing, alert in summary
5. **Track spend** — monthly cost log for all paid APIs
6. **No unnecessary calls** — every call serves a specific pipeline step

## Pipeline → API Mapping

| Step | Primary API | Secondary | Frequency |
|------|-------------|-----------|-----------|
| Price fetch | EODHD + CoinGecko | Alpha Vantage (backup) | Daily |
| Index calculation | Internal | — | Daily |
| News fetch | RSS feeds | Spectrawl | Daily |
| News tagging | Entity matcher | — | Daily |
| News summary + notes | Claude API | — | Daily |
| Daily briefing | Claude API | — | Weekdays + Sunday |
| Academic research | OpenAlex | Brave Search | Weekly |
| Industry reports | Brave Search | — | Weekly |
| Company filings | SEC EDGAR | — | Weekly |
| Predictions | Claude API + internal | — | As needed |
| Investor rebuild | Internal | — | After funding updates |
| Market caps | EODHD | — | Weekly |
