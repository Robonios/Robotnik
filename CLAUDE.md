# Robotniks

Structured intelligence platform for robotics and semiconductors — like Messari, but for the physical AI stack. Tracks public markets, startup funding, supply chains, and technical milestones.

## Architecture

- **Multi-page static site**: Separate HTML pages, shared CSS and JS
- **No build tools**: No package.json, no bundler, no framework. Pure static site
- **Data pipeline**: Python fetcher scripts → JSON files → frontend reads via `fetch()`
- **Hosting**: GitHub Pages
- **Config**: `.env` file for API keys, loaded by `scripts/config.py` (no external deps)
- **Archiving**: `scripts/archive_utils.py` provides shared archive-and-filter logic for all fetchers

## Project Structure

```
Robotnik/
├── index.html              # Home page — "The Frontier Stack" graph + index family (reads data/home.json)
├── assets.html             # Frontier Assets (market table / registry)
├── funding.html            # Funding Ops
├── research.html           # Research index (coming-soon placeholder)
├── intelligence.html       # News/research feed with filters
├── signals.html            # Placeholder (greyed out)
├── commodities.html        # Placeholder (greyed out)
├── portfolio.html          # Placeholder (greyed out)
├── thesis.html             # Mission directive + roadmap
├── recreation.html         # Tetris game
├── tetris.html             # Legacy landing/teaser page
├── cosmonaut-bg.png        # Background image
├── css/
│   ├── style.css           # Shared styles (chrome, dashboard, tables)
│   ├── typography.css      # Space Grotesk / Mulish type system
│   ├── frontier-stack.css  # Home-page Frontier Stack graph styles
│   └── home.css            # Home-page sections + Build-Brief token palette
├── js/
│   ├── main.js             # Legacy dashboard JS (NOT loaded on the new home page)
│   ├── nav.js              # Left sidebar navigation (injected on all pages)
│   ├── assets.js           # Frontier Assets page
│   ├── funding.js          # Funding Ops page
│   ├── frontier-stack.js   # Reusable FrontierStack graph module
│   └── home.js             # Home-page controller (reads data/home.json)
├── requirements.txt        # Python dependencies
├── .env                    # API keys (gitignored)
├── .gitignore
├── CLAUDE.md
├── .github/workflows/
│   └── fetch-data.yml      # GitHub Actions: daily prices + weekly intel
├── scripts/
│   ├── config.py           # Shared config (paths, API keys)
│   ├── archive_utils.py    # Shared archive-and-filter logic
│   ├── fetch_prices.py     # EODHD + CoinGecko (equities + tokens)
│   ├── fetch_market_caps.py # Market cap data
│   ├── fetch_price_history.py # Historical price data
│   ├── calculate_index.py  # Robotnik Composite Index + 4 sub-indices
│   ├── fetch_prices_alphavantage.py  # Legacy Alpha Vantage fetcher
│   ├── fetch_news.py       # ~30 RSS feeds
│   ├── fetch_research.py   # OpenAlex API
│   ├── fetch_filings.py    # SEC EDGAR
│   └── fetch_reports.py    # IFR/SEMI/SIA websites
├── data/
│   ├── prices/             # Price data
│   │   ├── equities.json
│   │   ├── tokens.json
│   │   ├── all_prices.json
│   │   └── history/        # Historical price data
│   ├── index/              # Index calculations
│   │   ├── robotnik_index.json
│   │   ├── sub_indices.json
│   │   ├── market_caps.json
│   │   ├── weights.json
│   │   └── summary.json
│   ├── mappings/           # Ticker/ID mappings
│   │   ├── eodhd_tickers.json
│   │   ├── coingecko_ids.json
│   │   └── pending_tickers.json
│   ├── home.json           # Home-page data contract (PLACEHOLDER — research preview; see js/home.js)
│   ├── news.json
│   ├── research.json
│   ├── filings.json
│   ├── reports.json
│   └── prices.json         # Legacy Alpha Vantage output
└── archive/                # Historical data for co-pilot training (gitignored)
    ├── archive_news.json
    ├── archive_research.json
    ├── archive_filings.json
    └── archive_reports.json
```

## Design System

- **Fonts**: **Space Grotesk** (headings, labels, numerals — with `font-variant-numeric: tabular-nums`) and **Mulish** (body / prose). Roboto Mono remains only as a stack fallback. Loaded via Google Fonts; the type system lives in `css/typography.css` (local font files in `assets/fonts/`). The earlier "Roboto Mono only" rule is retired.
- **Background**: `#111318` (dark theme). The home page uses a darker `#0A0B0E` base and the Build-Brief token palette layered in `css/home.css`.
- **Yellow accent**: `#F5D921` (primary brand color)
- **CSS variables are defined in `:root` in `css/style.css`** (home-page-only tokens in `css/home.css`)

## Site Pages

1. **Home** (`index.html`) — "The Frontier Stack" graph centerpiece (Stack⇄Flat morph, dot doorway, disruption cascade), index family, sector cards, research rail. Reads `data/home.json` (placeholder values — research preview).
2. **Frontier Assets** (`assets.html`) — market table / asset registry
3. **Funding Ops** (`funding.html`) — private-market funding rounds
4. **Research** (`research.html`) — research index (coming-soon placeholder)
5. **Intelligence** (`intelligence.html`) — News/research feed with type and category filters
6. **Signals** (`signals.html`) — Placeholder, greyed out in nav
7. **Commodities** (`commodities.html`) — Placeholder, greyed out in nav
8. **Thesis** (`thesis.html`) — Mission directive and roadmap
9. **Recreation** (`recreation.html`) — Tetris game (Recreation Bay)

## Data

- **Universe**: 347 entities (Robotnik_Universe_v5.xlsx) — Semi (45), Cross-stack (22), Robotics (152), Space (41), Materials (44), Tokens (43)
- **Live data**: 331/347 entities with price feeds
- **Robotnik Composite Index**: Market-cap weighted + 4 sub-indices (semiconductors, robotics, space, materials). Cross-stack entities are redistributed into these 4 by primary sector; tokens are isolated out of the index (token isolation policy). The "6 sectors" below describe the full 347-entity *universe*, not the index sub-indices.
- API keys stored in `.env` (not committed), loaded by `scripts/config.py`

## Data Fetcher Scripts

All scripts live in `scripts/` and output to `data/`.

| Script | Source | Output | Dependencies |
|--------|--------|--------|-------------|
| `scripts/fetch_prices.py` | EODHD + CoinGecko | `data/prices/*.json` | stdlib only |
| `scripts/fetch_market_caps.py` | EODHD + CoinGecko | `data/index/market_caps.json` | stdlib only |
| `scripts/fetch_price_history.py` | EODHD + CoinGecko | `data/prices/history/` | stdlib only |
| `scripts/calculate_index.py` | Local data | `data/index/*.json` | stdlib only |
| `scripts/fetch_news.py` | ~30 RSS feeds | `data/news.json` | `feedparser` |
| `scripts/fetch_research.py` | OpenAlex API | `data/research.json` | stdlib only |
| `scripts/fetch_filings.py` | SEC EDGAR | `data/filings.json` | stdlib only |
| `scripts/fetch_reports.py` | IFR/SEMI/SIA websites | `data/reports.json` | `beautifulsoup4`, `lxml` |
| `scripts/fetch_prices_alphavantage.py` | Alpha Vantage API | `data/prices.json` | `requests` |
| `scripts/archive_utils.py` | (shared utility) | — | stdlib only |
| `scripts/config.py` | (shared config) | — | stdlib only |

### Content Retention Rules

- **Research**: Papers from Jan 2023 onward in live output; all papers archived
- **News**: Rolling 12-month window in live output; older items archived
- **Filings**: Most recent filing per company in live output; all filings archived
- **Reports**: All reports in live output (dates unreliable); all archived
- **Archive files** (`archive/`): Full historical data for co-pilot training. Gitignored.

### Key RSS Sources (~30 feeds in `scripts/fetch_news.py`)

Industry: The Robot Report, IEEE Spectrum Robotics, Robohub, Robotics Tomorrow, Automate.org, Automation World, SemiEngineering, EE Times, Semiconductor Today, The Elec, eeNews Europe, Electronics Weekly

Substacks: SemiAnalysis, Fabricated Knowledge, Asianometry

Business/Tech: Ars Technica, TechCrunch AI, TechCrunch Robotics, VentureBeat AI, The Verge Robotics, Supply Chain Dive

Company: NVIDIA Blog/Newsroom/Developer, Boston Dynamics, ARM Community, TSMC Newsroom

Policy: Commerce Dept

Research: arXiv Robotics (cs.RO), arXiv AI (cs.AI)

### Setup

```bash
pip install -r requirements.txt
```

### `.env` file (required, not committed)

```
OPENALEX_API_KEY=<your-key>
EODHD_API_KEY=<your-key>
COINGECKO_API_KEY=<your-key>
```

### Running fetchers

```bash
python3 scripts/fetch_prices.py          # EODHD + CoinGecko → data/prices/
python3 scripts/fetch_market_caps.py     # Market caps → data/index/market_caps.json
python3 scripts/fetch_price_history.py   # Historical prices → data/prices/history/
python3 scripts/calculate_index.py       # Index calculation → data/index/
python3 scripts/fetch_news.py            # ~30 RSS feeds → data/news.json
python3 scripts/fetch_research.py        # OpenAlex → data/research.json
python3 scripts/fetch_filings.py         # SEC EDGAR → data/filings.json
python3 scripts/fetch_reports.py         # IFR/SEMI/SIA → data/reports.json
```

## Dev Server

```
python3 -m http.server 8000
```

Config saved in `.claude/launch.json` as `robotniks-site`.
