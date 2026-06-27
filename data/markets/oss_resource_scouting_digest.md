# Open-Source Repos + Open Datasets — Resource Scouting Digest

**Produced:** 2026-06-27 · **Status:** research/sourcing only — NO adoption, NO installs, NO repo changes. Hold for Robert.
**Filter applied to every item:** SCOUT what deepens **interpretation / structure / distribution**; DECLINE anything pulling toward price prediction / alpha / backtesting / portfolio / trading. *(Result: the sweep was scoped on-thesis, so nothing tripped the price-prediction decline-trigger — the DECLINE calls below are driven by **license** or **maintenance/fit**, not the filter. I checked each anyway.)*
**Verification:** every license/maintenance claim was checked against live GitHub/PyPI/official pages by the research sweep (cited per item). EdgarTools and moov-io/watchman were additionally **spot-checked firsthand this session**.

---

## TL;DR — adopt-now / defer / decline

**SCOUT (clean license, maintained, on-thesis — candidates for Robert to adopt):**
| Resource | License | Serves | Why |
|---|---|---|---|
| **EdgarTools** | MIT ✅ | enrichment + resolution + distribution | SEC filings→typed data, ships an **MCP server**, in Anthropic's OSS program, release **dated yesterday**. Top pick. |
| **moov-io/watchman** | Apache-2.0 ✅ | node `policy_context` + policy ledger | Pulls OFAC SDN + trade.gov **CSL (incl. BIS Entity List/DPL)** + EU/UK/UN from **public-domain** gov sources; daily-maintained. The export-control spine. |
| **GLEIF data + `pygleif`** | **CC0** data ✅ / MIT client | entity normalization + ownership | Open legal-entity IDs + **Level-2 parent/ownership**; free bulk; free OpenCorporates-ID↔LEI bridge. |
| **pyJedAI** | Apache-2.0 ✅ | edge / entity-resolution | Sentence-transformer + FAISS semantic match — resolves "Foxconn"→"Hon Hai", "Lam"→"Lam Research" into the registry. Best fit for the resolution gap. |
| **`comtradeapicall`** + **`py-ecomplexity`** + **`world_trade_data`** | all MIT ✅ | structure / dependency graph | Bilateral trade flows + ECI/PCI/proximity math + WITS tariffs — the primitives to **build** the criticality graph. |
| **USGS FS2025-3038 / MCS data** + **IEA Critical Minerals Dataset** | public-domain ✅ / **CC BY 4.0** ✅ | node verification (56+3) | Authoritative concentration/supply data — **energy-transition minerals, NOT semiconductor chokepoints** (scope caveat). |
| **`extruct`** + **`llms_txt2ctx`** + hand-authored `llms.txt`/JSON-LD | BSD / Apache ✅ | distribution / AEO | Validate, don't generate — the category is author-first (see Cat 4). |

**DEFER (relevant but a license/terms/architecture decision):** WTO-ADB TiCM (no stated data license; possibly viz-only) · Neo4j KG datastore (GPLv3 core / paid Aura — adopt the *pattern*, defer the store) · `pymrio` (GPL-3 — offline data-prep only) · OpenSanctions **dataset** (MIT code, but **CC-BY-NC data** → needs a paid commercial license) · `dedupe`/`Splink` (excellent, but fit/scale nuances) · `comtradr` (GPL-3, R-only).

**DECLINE (license or fit blocker):** **Zingg (AGPL-3.0 🚩)** · Senzing (commercial SDK, not OSS) · OpenCorporates API (paid/restricted data) · OEC API clients (dead API) · `pyComtrade`-family (power-grid COMTRADE, wrong domain) · OSS-"criticality" scorers (score software, wrong domain) · archived patent repos (`patent_client`, google `patents-public-data`) · schema.org generators (PHP or stale).

**The build-not-buy finding:** there is **no maintained open-source critical-minerals "criticality scoring" or "supply-chain graph" library.** That layer — the interpreted dependency/centrality scoring — is exactly what Robotnik sells, and the ecosystem doesn't supply it. **Assemble it in-house** from the SCOUT'd primitives (Comtrade/WITS → py-ecomplexity → pymrio → USGS/IEA CSVs → your own scoring + graph).

---

## ⚠️ Chokepoint open-data probe (the negative result — called out explicitly)

**Question:** can the three `verification:pending` nodes (CoWoS, ABF substrate, high-purity quartz) be auto-sourced from open/public structured data?
**Answer: NO. All three must stay curated. The negative result is real and validates the "curated interpretation = moat" thesis.**

| Chokepoint | Open structured data? | What exists | Verdict |
|---|---|---|---|
| **CoWoS capacity** (TSMC 2.5D + OSAT) | **No** | Every quantified capacity/share figure traces to **paywalled analysts** (TrendForce, Yole, SemiAnalysis, Morgan Stanley) re-quoted in free prose. `siliconanalysts.com` blurs values behind "Pro"; SEMI World Fab Forecast is paid **and not CoWoS-granular**; TSMC discloses only *qualitatively* (no monthly wpm, no OSAT split). | curated only |
| **ABF substrate** (Ajinomoto film; Ibiden/Unimicron/Shinko/AT&S shares) | **No** | Shares (top-3 ≈61–74%, Ajinomoto film >95%) are **paid market-research only** (Prismark, TechInsights, QY/Mordor) or **uncited blog prose**. USGS doesn't cover it (manufactured polymer, not a mined mineral); no Comtrade line isolates it. | curated only |
| **High-purity quartz** (Spruce Pine; Sibelco/Unimin + The Quartz Corp) | **Partial — gov data exists but omits the metric** | **USGS MCS "Quartz (High-Purity…)" IS open, public-domain, on data.gov** (DOI 10.5066/P13XCP3R) and even names the crucible end-use — **but it states verbatim "World Mine Production and Reserves: This information was not available," rounds US output "to avoid disclosing company proprietary data," and warns HPQ trade can't be isolated in HTS 2505.10.** The Sibelco/TQC ~75–85% duopoly figure is **paid-report only**. | curated only (cite USGS for *narrative*, not share) |

**Bottom line:** the % concentration numbers these nodes depend on live only behind analyst paywalls or in unsourced prose. They confirm the 3 pending nodes cannot be auto-sourced — curated interpretation is what produces them.

---

## Category 1 — Supply-chain / criticality DATA + data-as-code

**Curated datasets (Step 1):**
- **USGS FS2025-3038** *"Global maps of critical mineral production 2023"* — production + processing **concentration by country** (~29 mined / ~18 processed commodities; China processing-share jumps e.g. cobalt 1%→80%). **License: U.S. public domain** ✅. ⚠️ It's a **narrative+maps** Fact Sheet — no CSV release; pair with **USGS MCS 2025 ScienceBase CSV ZIPs** (~90 commodities, public domain) for raw numbers. **Serves node verification. → SCOUT.** [src](https://pubs.usgs.gov/publication/fs20253038/full)
- **WTO–ADB Trade in Critical Minerals (TiCM)** at critmin.org — bilateral critical-minerals trade at HS sub-heading level + tariffs + **network-graph viz** (the shape of our edge graph). **License: none stated on the announcement** ⚠️; possibly **viz-only, no bulk/API.** **Serves edge-resolution. → DEFER** (check critmin.org's own terms + extractability first). [src](https://www.wto.org/english/news_e/news24_e/envir_18dec24_e.htm)
- **IEA Critical Minerals Dataset** (`CM_Data_Explorer.xlsx`) — demand by clean-energy tech (STEPS/APS/NZE to 2050) + mining/refining supply by country to 2040; 37 minerals; updated May 2025. **License: CC BY 4.0 — VERIFIED** (a genuine exception to IEA's usual restrictive terms; the user's claim is correct) ✅. ⚠️ **Energy-transition minerals, NOT semiconductor chokepoints** (no Ga/Ge/quartz/ABF/CoWoS). **Serves content-enrichment of *materials-layer* nodes. → SCOUT** (free account login to download). [src](https://www.iea.org/data-and-statistics/data-product/critical-minerals-dataset)

**Data-as-code repos (my finds — the biggest tooling gap, per the brief):**
| Repo | What it is | License | Maintenance | Verdict |
|---|---|---|---|---|
| [uncomtrade/comtradeapicall](https://github.com/uncomtrade/comtradeapicall) | Official UN Comtrade Python client (bilateral trade, trade matrix, bulk) | **MIT** ✅ | active (Jun 2026; 145★) | **SCOUT** — canonical path to HS-coded trade flows |
| [cid-harvard/py-ecomplexity](https://github.com/cid-harvard/py-ecomplexity) | Harvard Growth Lab — ECI/PCI, RCA, proximity, product space | **MIT** ✅ | mature/stable (82★) | **SCOUT** — the dependency-structure/centrality math |
| [Datawheel/py-economic-complexity](https://github.com/Datawheel/py-economic-complexity) | Complexity indicators, pandas+polars | **MIT** ✅ | active-ish (13★) | SCOUT (secondary) |
| [mwouts/world_trade_data](https://github.com/mwouts/world_trade_data) | World Bank **WITS** wrapper (trade + tariffs, no key) | **MIT** ✅ | minimal (last rel 2022; 42★) | **SCOUT** — pin version |
| [IndEcol/pymrio](https://github.com/IndEcol/pymrio) | Multi-regional input-output (EXIOBASE/WIOD/EORA); inter-sector linkages | **GPL-3** ⚠️ copyleft | active (Dec 2025; 218★) | **SCOUT w/ caveat** — standalone/offline data-prep only; do not link into distributed proprietary code |
| USGS MCS — no Python wrapper exists | use ScienceBase **CSV ZIPs** directly + thin parser | public domain ✅ | USGS-maintained | **SCOUT the data**, build the loader |
| OEC API clients (`yahiaali/oec`, `pachadotdev/oec`) | OEC wrappers | MIT | **dead** (OEC killed its free API 2021) | **DECLINE** |
| `pyComtrade` / `miguelmoreto/pycomtrade` | **IEEE COMTRADE oscillography (power grids)** | — | — | **DECLINE** — name collision, off-domain |
| `ossf/criticality_score`, NETL `URC-Assessment-Method` | score *software* criticality / predict ore *geology* | varied | n/a | **DECLINE** — wrong domain (not supply-chain structure) |

→ **No maintained critical-minerals criticality/graph library exists → in-house wedge.**

---

## Category 2 — Document/filing pipelines + filing-adjacent enrichment

**Primary repo candidate (curated):**
- **EdgarTools** ([github](https://github.com/dgunning/edgartools)) — SEC EDGAR filings → typed objects (XBRL financials, 20+ forms, insider trades, CIK/ticker lookup, full-text search). **License: MIT ✅** (spot-checked). **Ships a real MCP server ✅** ("Run EdgarTools as an MCP server for any AI client — Claude Desktop, Cline…"). **In Anthropic's Claude for Open Source Program ✅** (announced Mar 18 2026). **Maintenance: v5.40.0 dated Jun 26 2026 — released *yesterday*; ~2.4k★, heavily active.** **Serves content-enrichment + entity-resolution (CIK↔ticker↔entity) + distribution (MCP).** **→ SCOUT (top pick, highest-confidence adopt).**

**Patents (my finds) — ⚠️ the ecosystem hit a maintenance cliff (PatentsView legacy API 410-Gone since 2025-05; `patent_client` + google `patents-public-data` archived):**
| Repo | License | Maintenance | Verdict |
|---|---|---|---|
| [parkerhancock/patent-client-agents](https://github.com/parkerhancock/patent-client-agents) (successor to archived `patent_client`) | Apache-2.0 | live (v0.22.0) | **SCOUT** — broad USPTO+EPO+Google retrieval |
| [ip-tools/python-epo-ops-client](https://github.com/ip-tools/python-epo-ops-client) | Apache-2.0 (code); **EPO OPS data = fair-use, commercial ≈ €2,800/yr 🚩**) | live (v4.2.2 May 2026) | **SCOUT** — EPO client (mind the OPS commercial tier) |
| PatentsView **bulk data** (now data.uspto.gov) | **CC BY 4.0** ✅ | USPTO-maintained | **SCOUT** for assignee→company identity *(note: PatentsView dropped its PermID linkage — assignee→company-ID bridge is a residual gap)* |
| `patent_client`, google `patents-public-data`, `PatentsView-APIWrapper`, `pypatent` | mixed | **archived/dead** | **DECLINE/DEFER** (use successors) |

**Export-control / sanctions (my finds — highest relevance: this IS the node `policy_context` + policy ledger):**
- **moov-io/watchman** ([github](https://github.com/moov-io/watchman)) — **Apache-2.0 ✅**; ingests **OFAC SDN/non-SDN + trade.gov CSL (which bundles the BIS Entity List + DPL) + EU + UK OFSI + UN**, all from **public-domain gov sources**; **v0.63.3 Jun 5 2026, near-daily, 475★** (spot-checked). **Serves the policy ledger from commercial-safe sources. → SCOUT (build the policy layer on this).** *(Note: BIS Entity List arrives via the CSL bundle, not a standalone feed; verify UK source points at the new FCDO list, and trade.gov's API needs a free key.)*
- **OpenSanctions ecosystem** — `followthemoney` (FtM schema, **MIT** ✅, **SCOUT**), `nomenklatura` (dedup, **MIT** ✅, **SCOUT**), `yente`/`opensanctions` (**MIT code** but the consolidated **DATASET is CC-BY-NC 4.0 — commercial use requires a paid license 🚩**, verified verbatim from licensing page + README). **→ DEFER the dataset** (SCOUT the MIT tooling, point it at public-domain lists). Also: OpenSanctions is sanctions/PEP-centric, **not** comprehensive export-control.

**Corporate registries / identifiers (my finds):**
- **GLEIF + [pygleif](https://github.com/ggravlingen/pygleif)** — LEI data is **CC0 ✅** (Level-1 entity + **Level-2 parent/ownership**, free bulk); MIT client (maintained, Feb 2026). **Plus GLEIF publishes a free open OpenCorporates-ID↔LEI mapping** (bridge without paying for OC). **Serves entity normalization + ownership. → SCOUT (adopt first for the ownership layer).**
- [openownership/data-standard (BODS)](https://github.com/openownership/data-standard) — Apache-2.0 ownership schema (a standard to normalize into; **not data**). **→ SCOUT** (as schema).
- OpenCorporates API clients (`opyncorporates` etc.) — **OC data is paid/restricted + client stale 2019.** **→ DECLINE** (use the GLEIF↔OC mapping instead).
- Wikidata: `qwikidata` (Apache-2.0, stale 2022) / `dahlia/wikidata` (GPL-3 ⚠️) — CC0 data (P127 owned-by, P749 parent, P1278 LEI). **→ SCOUT/DEFER** (or hit SPARQL directly).

---

## Category 3 — Entity resolution / graph (edge + resolution automation)

**Method reference (curated):**
- **Neo4j unstructured-text→KG toolchain** ([page](https://neo4j.com/developer/genai-ecosystem/importing-graph-from-unstructured-data/)) — real tooling (GraphRAG Python, LLM-Graph-Builder, LangChain `LLMGraphTransformer`, LlamaIndex `PropertyGraphIndex`, MCP servers). Client libs are Apache-family (permissive), **but the Neo4j core datastore is GPLv3 / Enterprise commercial / Aura paid 🚩.** **Serves edge-resolution (text→supplier→consumer graph) — architecturally the closest match to what Robotnik *is*.** **→ DEFER** — adopt the **pattern** (LLM→KG extraction) + permissive client libs; treat the datastore as a separate licensing call.

**Entity resolution / record linkage (my finds — for the Samsung/Foxconn registry gap; problem = alias→canonical at ~600-entity scale, which favors lightweight embedding/fuzzy over heavy ML/Spark):**
| Repo | Approach | License | Maintenance | Verdict |
|---|---|---|---|---|
| [AI-team-UoA/pyJedAI](https://github.com/AI-team-UoA/pyJedAI) | sentence-transformers + FAISS **semantic** blocking/match | **Apache-2.0** ✅ | active (rel Nov 2025; ~96★) | **SCOUT (#1)** — beats string-distance on "Foxconn"↔"Hon Hai"; trivial at 600-entity scale; small community is the only caveat |
| [dedupeio/dedupe](https://github.com/dedupeio/dedupe) | **active-learning** fuzzy match/dedup | **MIT** ✅ | mature, slowing (commit Jul 2025; 4.5k★) | **SCOUT (#2)** — active-learning fits the curation posture; enrich mentions w/ sector/country/ticker for signal |
| [moj-analytical-services/splink](https://github.com/moj-analytical-services/splink) | probabilistic (Fellegi-Sunter), DuckDB/Spark | **MIT** ✅ | very active (v4.0.16 Mar 2026; 2.2k★) | **SCOUT (#3)** — scale-mismatched to 600 mentions; use for **registry-internal dedup**, not live alias matching |
| [J535D165/recordlinkage](https://github.com/J535D165/recordlinkage) | build-your-own blocking→compare→classify | BSD-3 ✅ | **stale** (v0.16 Jul 2023) | **DEFER** — clean license, but maintenance risk |
| [zinggAI/zingg](https://github.com/zinggAI/zingg) | ML ER on Spark | **AGPL-3.0 🚩** | active | **DECLINE** — AGPL network-copyleft = adoption-blocking for a commercial SaaS; + Spark overkill |
| `megagonlabs/ditto`, `facebookresearch/BLINK`, `vintasoftware/entity-embed` | transformer pair-matching / bi-encoder KB-linking / neural embed | Apache/MIT ✅ | **stale/archived** | **DEFER as *patterns*** (BLINK's bi-encoder→cross-encoder design is the right mental model), not dependencies |
| Senzing | principle-based ER | **commercial SDK** (only wrappers are OSS) | — | **DECLINE** for the OSS mandate |

→ **Design that falls out:** embed all ~600 canonical names once → FAISS nearest-neighbor per mention → threshold to auto-resolve, route low-confidence to a review queue. **pyJedAI** delivers this in one Apache-2.0 package; **dedupe** adds the active-learning curation loop.

---

## Category 4 — AEO / distribution

**Curated references (Step 1):** the [llms.txt guide](https://dev.to/lab451/complete-llmstxt-guide-for-2026-57d) (practice ref) and [schema-markup-for-LLM-visibility](https://www.walkersands.com/about/blog/how-can-schema-markup-support-llm-visibility/) (practice ref) — **adopt the practices, not as dependencies. → SCOUT (as references).**

**Tooling (my finds) — the category is thin and *author-first*, exactly as expected:**
| Repo | What it is | License | Maintenance | Verdict |
|---|---|---|---|---|
| [AnswerDotAI/llms-txt](https://github.com/AnswerDotAI/llms-txt) (`llms_txt2ctx`) | canonical spec; CLI **parses/expands** a hand-authored llms.txt (does NOT crawl-generate) | Apache-2.0 ✅ | active (Jan 2026; 2.5k★) | **SCOUT (narrow)** — adopt the spec; use CLI to lint a file you hand-write |
| [scrapinghub/extruct](https://github.com/scrapinghub/extruct) | **extracts/validates** JSON-LD/microdata from HTML | BSD-3 ✅ | active (v0.18 Nov 2024; 967★) | **SCOUT** — CI guard that your hand-written JSON-LD stays valid |
| firecrawl `llmstxt-generator` / `create-llmstxt-py` | crawl→summarize llms.txt | none/MIT | **deprecated / paid API keys** | **DECLINE/DEFER** — overkill + paid for ~10 hand-curated lines |
| `pydantic_schemaorg` (Python JSON-LD gen) / `spatie/schema-org` (PHP) / `openschemas` | JSON-LD generators | MIT / MIT / MPL-2.0 | **stale (v1 Pydantic, 2022)** / wrong-language (PHP) / stale | **DEFER/DECLINE** |

→ **Honest finding:** for a no-build static site, the win is **hand-author `/llms.txt` + inline JSON-LD** (you already hand-author sophisticated JSON-LD). The highest-leverage AEO move — **`schema.org/Dataset` markup on the index pages** with `distribution → DataDownload` pointing at `data/index/*.json` (machine-citable!) — has **no good generator**; emit it from a small helper in the existing Python pipeline (the `generate_sitemap.py` pattern). **→ DECLINE tooling, ship hand-authored markup; SCOUT `extruct` as a validator.**

---

## Filter note + escalations

- **Filter integrity:** every item was checked against the decline-trigger (price-prediction / alpha / backtesting / portfolio / trading). **None tripped it** — the sweep stayed on the interpretation/structure/distribution side by construction. The DECLINEs above are **license** (Zingg AGPL, Senzing/OC commercial, OpenSanctions NC-data) or **maintenance/domain** (dead APIs, archived repos, wrong-domain "criticality" scorers), not thesis violations.
- **Adopt/architecture calls are Robert's, not mine.** Nothing here is adopted. The clearest adopt-now candidates (EdgarTools, watchman, GLEIF/pygleif, pyJedAI, the trade/complexity primitives) each still carry a per-repo integration decision; the GPL/AGPL/NC-data flags above are the load-bearing constraints to weigh before any install.
- **The strongest strategic signal in this sweep:** the one layer with **no open-source supply** — critical-minerals criticality scoring + the supply-chain dependency graph — is precisely Robotnik's product. The open ecosystem gives you the *inputs* (trade flows, complexity math, gov concentration data) but not the *interpretation*. Build the interpretation; source the inputs.

*Digest location note: filed under `data/markets/` alongside the existing `data_licensing_review.md` and `proposed_commodities_data_sourcing.md` (same genre). Move to a dedicated research dir if preferred.*
