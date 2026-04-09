// ===== MARKET DATA (real prices, close Mar 4 2026) =====
// ===== DYNAMIC PRICE DATA =====
let allCompanies = [];
let uniqueCompanies = [];
let marketShowLimit = 50;

// Sector mapping from JSON to internal keys
function mapSector(s) {
  if (!s) return 'semi';
  const sl = s.toLowerCase();
  if (sl.includes('semiconductor')) return 'semi';
  if (sl.includes('robotics')) return 'robo';
  if (sl.includes('space')) return 'space';
  if (sl.includes('cross')) return 'semi';  // Cross-Stack eliminated — legacy data maps to semi
  if (sl.includes('material')) return 'materials';
  if (sl.includes('token')) return 'token';
  return 'semi';
}

// Format market cap for display
function fmtMcap(n) {
  if (!n || n <= 0) return '—';
  if (n >= 1e12) return '$' + (n / 1e12).toFixed(2) + 'T';
  if (n >= 1e9) return '$' + (n / 1e9).toFixed(0) + 'B';
  if (n >= 1e6) return '$' + (n / 1e6).toFixed(0) + 'M';
  return '$' + n.toLocaleString();
}

// Format price with appropriate currency symbol
function fmtPrice(price, currency) {
  if (!price) return '—';
  const c = (currency || 'USD').toUpperCase();
  const sym = c === 'GBP' ? '£' : c === 'EUR' ? '€' : c === 'JPY' ? '¥' : c === 'KRW' ? '₩' : c === 'HKD' ? 'HK$' : c === 'CHF' ? 'CHF ' : c === 'SEK' ? 'SEK ' : c === 'NOK' ? 'NOK ' : c === 'CAD' ? 'C$' : c === 'TWD' ? 'NT$' : c === 'CNY' ? '¥' : '$';
  return sym + price.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
}

// Generate a deterministic color from ticker string
function tickerColor(ticker) {
  let h = 0;
  for (let i = 0; i < ticker.length; i++) h = ticker.charCodeAt(i) + ((h << 5) - h);
  h = Math.abs(h) % 360;
  return 'hsl(' + h + ', 55%, 50%)';
}

// Load price data from JSON, merge with market caps if available
async function loadPriceData() {
  try {
    const cb = '?v=' + Date.now();
    const [priceResp, mcapResp, summaryResp, registryResp] = await Promise.allSettled([
      fetch('data/prices/all_prices.json' + cb),
      fetch('data/index/market_caps.json' + cb),
      fetch('data/index/summary.json' + cb),
      fetch('data/registries/entity_registry.json' + cb),
    ]);

    let priceData = null;
    if (priceResp.status === 'fulfilled' && priceResp.value.ok) {
      priceData = await priceResp.value.json();
    }

    let mcapData = null;
    if (mcapResp.status === 'fulfilled' && mcapResp.value.ok) {
      mcapData = await mcapResp.value.json();
    }

    // Load Robotnik Index summary
    if (summaryResp.status === 'fulfilled' && summaryResp.value.ok) {
      window.robotnikSummary = await summaryResp.value.json();
    }

    // Build excluded-ticker set from entity registry
    const excludedTickers = new Set();
    let registryData = null;
    if (registryResp.status === 'fulfilled' && registryResp.value.ok) {
      registryData = await registryResp.value.json();
      for (const [ticker, entity] of Object.entries(registryData)) {
        if (entity && entity.status === 'excluded') excludedTickers.add(ticker);
      }
    }

    // Build mcap lookup
    const mcapMap = {};
    if (mcapData && mcapData.market_caps) {
      for (const m of mcapData.market_caps) {
        mcapMap[m.ticker] = m.market_cap_usd;
      }
    }

    if (priceData && priceData.prices) {
      // Filter out excluded entities
      const activePrices = priceData.prices.filter(e => !excludedTickers.has(e.ticker));
      allCompanies = activePrices.map(e => ({
        name: e.name || e.ticker,
        sub: e.sector || '',
        ticker: e.ticker,
        price: e.price || 0,
        change: e.change_pct || 0,
        mcap: mcapMap[e.ticker] || 0,
        mcapFmt: fmtMcap(mcapMap[e.ticker]),
        sector: mapSector(e.sector),
        currency: e.currency || 'USD',
        color: tickerColor(e.ticker),
        date: e.date || '',
      }));

      // Dedupe
      const seen = new Set();
      uniqueCompanies = allCompanies.filter(c => { if (seen.has(c.ticker)) return false; seen.add(c.ticker); return true; });

      // Sort by market cap desc (entities without mcap go to bottom)
      uniqueCompanies.sort((a, b) => (b.mcap || 0) - (a.mcap || 0));

      // Update timestamp note
      const note = document.getElementById('market-note');
      if (note) {
        const ts = priceData.fetched_at ? new Date(priceData.fetched_at).toLocaleDateString('en-US', {month:'short', day:'numeric', year:'numeric'}) : 'unknown';
        note.textContent = uniqueCompanies.length + ' entities · Prices as of ' + ts + ' · Source: EODHD, CoinGecko · Data provided by CoinGecko · Updates daily';
      }
    }
  } catch (err) {
    console.warn('Failed to load price data:', err);
  }

  // Fallback if fetch failed — use empty array
  if (uniqueCompanies.length === 0) {
    const noteEl = document.getElementById('market-note');
    if (noteEl) noteEl.textContent = 'Price data unavailable — check data/prices/all_prices.json';
  }

  renderAssetList();
  renderComparePills();
  renderChart();
  renderTicker();
  updateMarketOverview();
  renderMarketTable();
}

// Populate Market Overview panel from live price data
function updateMarketOverview() {
  if (!uniqueCompanies.length) return;

  // Total market cap (USD-denominated equities only for meaningful total)
  var totalMcap = 0;
  for (var i = 0; i < uniqueCompanies.length; i++) totalMcap += (uniqueCompanies[i].mcap || 0);
  var mcapEl = document.getElementById('ov-mcap');
  if (mcapEl) mcapEl.textContent = totalMcap >= 1e12 ? '$' + (totalMcap / 1e12).toFixed(2) + 'T' : totalMcap >= 1e9 ? '$' + (totalMcap / 1e9).toFixed(0) + 'B' : '--';

  // Tracked count
  var countEl = document.getElementById('ov-count');
  if (countEl) countEl.textContent = String(uniqueCompanies.length);

  // Find top gainer, top loser, largest
  var largest = uniqueCompanies[0]; // already sorted by mcap
  var gainer = uniqueCompanies[0], loser = uniqueCompanies[0];
  var avgChg = 0, chgCount = 0;
  for (var j = 0; j < uniqueCompanies.length; j++) {
    var c = uniqueCompanies[j];
    if (c.change !== undefined && c.change !== null) {
      avgChg += c.change;
      chgCount++;
      if (c.change > gainer.change) gainer = c;
      if (c.change < loser.change) loser = c;
    }
  }
  avgChg = chgCount ? avgChg / chgCount : 0;

  var chgEl = document.getElementById('ov-24h');
  if (chgEl) {
    chgEl.textContent = (avgChg >= 0 ? '+' : '') + avgChg.toFixed(2) + '%';
    chgEl.className = 'overview-val ' + (avgChg >= 0 ? 'v-green' : 'v-red');
  }

  var largestEl = document.getElementById('ov-largest');
  if (largestEl && largest) {
    var lCls = largest.change >= 0 ? 'v-green' : 'v-red';
    var lSign = largest.change >= 0 ? '+' : '';
    largestEl.innerHTML = largest.ticker + ' <span class="' + lCls + '">' + lSign + largest.change.toFixed(2) + '%</span>';
  }

  var gainerEl = document.getElementById('ov-gainer');
  if (gainerEl && gainer) {
    gainerEl.innerHTML = gainer.ticker + ' <span class="v-green">+' + gainer.change.toFixed(2) + '%</span>';
  }

  var loserEl = document.getElementById('ov-loser');
  if (loserEl && loser) {
    loserEl.innerHTML = loser.ticker + ' <span class="v-red">' + loser.change.toFixed(2) + '%</span>';
  }

  // Last updated timestamp
  var updatedEl = document.getElementById('ov-updated');
  if (updatedEl) {
    // Try to get the updated field from price data
    try {
      var ts = new Date().toISOString().slice(0, 16).replace('T', ' ') + ' UTC';
      updatedEl.textContent = ts;
    } catch(e) {}
  }
}

// ===== FUNDRAISING DATA (sample — you'll replace with real data) =====
const raises = [
  { company:"Figure AI", hq:"USA", stage:"Series B", amount:675, date:"2025-02", valuation:"$2.6B", investors:"Microsoft, NVIDIA, Bezos Expeditions, Intel Capital", sector:"robo", subsector:"Humanoid", source:"TechCrunch" },
  { company:"Physical Intelligence", hq:"USA", stage:"Series A", amount:400, date:"2025-01", valuation:"$2.4B", investors:"Bezos Expeditions, Thiel Capital, Lux Capital", sector:"robo", subsector:"Foundation models", source:"Bloomberg" },
  { company:"Skild AI", hq:"USA", stage:"Series A", amount:300, date:"2024-07", valuation:"$1.5B", investors:"Lightspeed, SoftBank, Coatue, Bezos Expeditions", sector:"robo", subsector:"Foundation models", source:"Forbes" },
  { company:"Agility Robotics", hq:"USA", stage:"Series B", amount:150, date:"2024-09", valuation:"", investors:"DCVC, Playground Global, Amazon Industrial Innovation Fund", sector:"robo", subsector:"Humanoid", source:"Reuters" },
  { company:"Tenstorrent", hq:"Canada", stage:"Series D", amount:693, date:"2025-01", valuation:"$2.6B", investors:"Samsung, LG, Hyundai, AFT Partners", sector:"semi", subsector:"AI silicon", source:"Tenstorrent blog" },
  { company:"Groq", hq:"USA", stage:"Series D", amount:640, date:"2024-08", valuation:"$2.8B", investors:"BlackRock, Samsung Catalyst, Neuberger Berman", sector:"semi", subsector:"AI inference", source:"Reuters" },
  { company:"Cerebras Systems", hq:"USA", stage:"Series F", amount:250, date:"2024-06", valuation:"$4.3B", investors:"G42, Altimeter Capital, Benchmark", sector:"semi", subsector:"AI training", source:"Bloomberg" },
  { company:"1X Technologies", hq:"Norway", stage:"Series B", amount:100, date:"2024-01", valuation:"", investors:"EQT Ventures, Samsung NEXT, OpenAI Startup Fund", sector:"robo", subsector:"Humanoid", source:"TechCrunch" },
  { company:"Sanctuary AI", hq:"Canada", stage:"Series C", amount:175, date:"2024-05", valuation:"", investors:"Accenture Ventures, SE Health, InBC", sector:"robo", subsector:"Humanoid", source:"Company blog" },
  { company:"Apptronik", hq:"USA", stage:"Series A", amount:350, date:"2024-03", valuation:"", investors:"Google Ventures, Capital Factory, Grit Ventures", sector:"robo", subsector:"Humanoid", source:"Crunchbase" },
  { company:"Covariant", hq:"USA", stage:"Series C", amount:222, date:"2024-05", valuation:"", investors:"Radical Ventures, Canada Pension Plan, Index Ventures", sector:"robo", subsector:"Warehouse AI", source:"Reuters" },
  { company:"Machina Labs", hq:"USA", stage:"Series B", amount:72, date:"2024-08", valuation:"", investors:"Innovation Endeavors, Breakthrough Energy", sector:"robo", subsector:"Manufacturing", source:"TechCrunch" },
  { company:"Sila Nanotechnologies", hq:"USA", stage:"Series F", amount:375, date:"2024-01", valuation:"$3.3B", investors:"Coatue, 8VC, T. Rowe Price", sector:"infra", subsector:"Battery / materials", source:"Bloomberg" },
  { company:"d-Matrix", hq:"USA", stage:"Series B", amount:110, date:"2024-04", valuation:"", investors:"Microsoft M12, Playground Global, SK hynix", sector:"semi", subsector:"AI inference", source:"VentureBeat" },
  { company:"Rain AI", hq:"USA", stage:"Series B", amount:25, date:"2024-02", valuation:"", investors:"Sam Altman (personal), Buckley Ventures", sector:"semi", subsector:"Neuromorphic", source:"TechCrunch" },
  { company:"Legged Robots (Unitree)", hq:"China", stage:"Series B", amount:90, date:"2024-06", valuation:"", investors:"Hillhouse Capital, Source Code Capital", sector:"robo", subsector:"Quadruped / Humanoid", source:"36Kr" },
  { company:"Symbotic", hq:"USA", stage:"Secondary", amount:320, date:"2024-03", valuation:"$16B", investors:"SoftBank (via Warehouse JV)", sector:"robo", subsector:"Warehouse", source:"SEC filings" },
  { company:"Ayar Labs", hq:"USA", stage:"Series C", amount:155, date:"2024-09", valuation:"", investors:"NVIDIA, Intel Capital, Hewlett Packard Pathfinder", sector:"semi", subsector:"Optical I/O", source:"Company blog" },
];

raises.sort((a,b) => b.amount - a.amount);

// ===== RENDER TICKER =====
function renderTicker() {
  const el = document.getElementById('ticker');
  if (!el || !uniqueCompanies.length) return;
  // Show top 30 by market cap in the scrolling ticker
  const top = uniqueCompanies.slice(0, 30);
  const items = top.map(c => {
    const cls = c.change >= 0 ? 't-up' : 't-dn';
    const sign = c.change >= 0 ? '+' : '';
    return `<div class="ticker-item"><span class="t-name">${c.ticker}</span><span class="t-price">${fmtPrice(c.price, c.currency)}</span><span class="t-chg ${cls}">${sign}${c.change.toFixed(2)}%</span></div>`;
  }).join('');
  el.innerHTML = items + items;
}

// ===== SPARKLINES =====
function spark(change) {
  const pts = [];
  let y = 12;
  for (let i = 0; i <= 12; i++) {
    const d = change > 0 ? -0.35 : 0.35;
    y += (Math.random() - 0.5 + d) * 2.5;
    y = Math.max(2, Math.min(22, y));
    pts.push(`${(i/12)*60},${y}`);
  }
  const c = change >= 0 ? '#22c55e' : '#ef4444';
  return `<svg class="sparkline" viewBox="0 0 60 22"><polyline fill="none" stroke="${c}" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" points="${pts.join(' ')}" /></svg>`;
}

// ===== MARKET RENDERING (Messari-style) =====
let mFilter = 'all';
let chartMode = 'pct';  // 'pct' or 'price'
let chartRange = 30;
let compareAsset = null; // single compare ticker (free tier)
let activeChart = null;
let activeIdxSeries = null;   // persistent LightweightCharts series ref
let activeCompSeries = null;  // persistent LightweightCharts series ref
let chartHistoryCache = {};
let indexSeries = null;  // Robotnik Index series

function setFilter(btn) {
  document.querySelectorAll('#asset-filters button').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  mFilter = btn.dataset.filter;
  renderAssetList();
}

function renderAssetList() {
  const scroll = document.getElementById('asset-list-scroll');
  if (!scroll) return; // Element not present in current page layout
  const searchEl = document.getElementById('market-search');
  const s = (searchEl ? searchEl.value : '').toLowerCase();
  let data = mFilter === 'all' ? uniqueCompanies : uniqueCompanies.filter(c => c.sector === mFilter);
  if (s) data = data.filter(c => c.name.toLowerCase().includes(s) || c.ticker.toLowerCase().includes(s) || c.sub.toLowerCase().includes(s));

  const totalFiltered = data.length;
  const isSearching = s.length > 0;
  const visibleData = isSearching ? data : data.slice(0, marketShowLimit);

  // Build HTML: Robotnik Index pinned at top (always, unless searching)
  let html = '';
  if (!s) {
    const idxData = window.robotnikSummary;
    const idxVal = idxData ? idxData.composite.value.toFixed(2) : '1,000.00';
    const idxChg = idxData ? idxData.composite.daily_change_pct : 0;
    const idxChgCls = idxChg >= 0 ? 'up' : 'dn';
    const idxSign = idxChg >= 0 ? '+' : '';
    html += `<div class="asset-row pinned" onclick="selectAsset('RBTK_INDEX')">
      <div class="ar-rank" style="color:var(--yellow);">&#9733;</div>
      <div class="ar-info">
        <div class="ar-icon" style="background:var(--yellow);color:var(--bg);font-size:0.55rem;font-weight:700;">R</div>
        <span class="ar-name" style="color:var(--yellow);">Robotnik Index</span>
      </div>
      <div class="ar-price" style="color:var(--yellow);">${idxVal}</div>
      <div class="ar-chg ${idxChgCls}">${idxSign}${idxChg.toFixed(2)}%</div>
    </div>`;
  }

  html += visibleData.map((c, i) => {
    const col = c.color || tickerColor(c.ticker);
    const chgCls = c.change >= 0 ? 'up' : 'dn';
    const sign = c.change >= 0 ? '+' : '';
    const isActive = compareAsset === c.ticker;
    return `<div class="asset-row${isActive ? ' active' : ''}" onclick="selectAsset('${c.ticker.replace(/'/g, "\\'")}')">
      <div class="ar-rank">${i + 1}</div>
      <div class="ar-info">
        <div class="ar-icon" style="background:${col}15;color:${col};border:1px solid ${col}28">${(c.name || '?')[0]}</div>
        <span class="ar-name">${c.name}</span>
        <span class="ar-ticker">${c.ticker}</span>
      </div>
      <div class="ar-price">${fmtPrice(c.price, c.currency)}</div>
      <div class="ar-chg ${chgCls}">${sign}${c.change.toFixed(2)}%</div>
    </div>`;
  }).join('');

  // Load more
  if (!isSearching && visibleData.length < totalFiltered) {
    html += `<div class="asset-load-more">
      <button onclick="showMore()">Show more (${visibleData.length} of ${totalFiltered})</button>
    </div>`;
  }

  scroll.innerHTML = html;
}

function showMore() {
  marketShowLimit += 50;
  renderAssetList();
}

// Select an asset to compare against the Robotnik Index
let _preCompareMode = null; // remember mode before compare
function selectAsset(ticker) {
  if (ticker === 'RBTK_INDEX') {
    compareAsset = null;
  } else if (compareAsset === ticker) {
    compareAsset = null;
  } else {
    compareAsset = ticker;
  }

  // Auto-switch to % mode when comparing (standard for multi-asset charts)
  if (compareAsset && chartMode !== 'pct') {
    _preCompareMode = chartMode;
    chartMode = 'pct';
    document.querySelectorAll('.chart-mode-btns button').forEach(b => {
      b.classList.toggle('active', b.textContent.trim() === '%');
    });
  } else if (!compareAsset && _preCompareMode) {
    chartMode = _preCompareMode;
    _preCompareMode = null;
    document.querySelectorAll('.chart-mode-btns button').forEach(b => {
      b.classList.toggle('active', b.textContent.trim() === (chartMode === 'pct' ? '%' : 'Price'));
    });
  }

  renderAssetList();
  renderComparePills();
  renderChart();
}

// Compare pills bar
function renderComparePills() {
  const bar = document.getElementById('chart-compare-bar');
  if (!bar) return;
  let html = '';

  // Robotnik Index always shown
  html += `<span class="compare-pill" style="border-color:var(--yellow);color:var(--yellow);">
    <span class="cp-dot" style="background:var(--yellow);"></span>
    RBTK Index
  </span>`;

  if (compareAsset) {
    const c = uniqueCompanies.find(x => x.ticker === compareAsset);
    const col = c ? (c.color || tickerColor(c.ticker)) : '#3b82f6';
    const name = c ? c.ticker : compareAsset;
    html += `<span class="compare-pill" style="border-color:${col};color:${col};">
      <span class="cp-dot" style="background:${col};"></span>
      ${name}
      <span class="cp-close" onclick="event.stopPropagation();selectAsset('${compareAsset.replace(/'/g, "\\'")}')">&times;</span>
    </span>`;
  }

  html += `<button class="compare-add" onclick="document.getElementById('market-search').focus()">+ Add</button>`;
  bar.innerHTML = html;
}

// Chart mode toggle (% vs Price)
function setChartMode(btn, mode) {
  document.querySelectorAll('.chart-mode-btns button').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  chartMode = mode;
  renderChart();
}

// Chart range
function setChartRange(btn) {
  if (btn.classList.contains('disabled')) return;
  document.querySelectorAll('#chart-range-btns button').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  chartRange = btn.dataset.range === 'ytd' ? 'ytd' : parseFloat(btn.dataset.range);
  renderChart();
}

// Load history data for a ticker
async function loadHistory(ticker) {
  if (chartHistoryCache[ticker]) return chartHistoryCache[ticker];
  const safeTicker = ticker.replace(/\//g, '_').replace(/ /g, '_');
  try {
    const resp = await fetch(`data/prices/history/${safeTicker}.json`);
    if (resp.ok) {
      const data = await resp.json();
      chartHistoryCache[ticker] = data.series || [];
      return chartHistoryCache[ticker];
    }
  } catch (e) { /* continue */ }
  return [];
}

// Load Robotnik Index series (full basket + equities-only for longer ranges)
let _indexData = null; // cached raw index JSON
async function loadIndexSeries() {
  if (indexSeries && _indexData) return indexSeries;
  try {
    const resp = await fetch('data/index/robotnik_index.json?v=' + Date.now());
    if (resp.ok) {
      _indexData = await resp.json();
      indexSeries = _indexData.series || [];
      if (_indexData.current_value) {
        window.robotnikIndexValue = _indexData.current_value;
        window.robotnikBaseDate = _indexData.base_date;
      }
      return indexSeries;
    }
  } catch (e) { /* continue */ }
  indexSeries = [];
  return indexSeries;
}

// Pick the right index series based on range:
// - Ranges > 365 days use equities-only series (5Y of data)
// - Ranges <= 365 days use full basket (equities + tokens)
function getIndexSeriesForRange(rangeDays) {
  if (!_indexData) return indexSeries || [];
  const useEquitiesOnly = (rangeDays !== 'ytd' && rangeDays > 365);
  if (useEquitiesOnly && _indexData.equities_only && _indexData.equities_only.series) {
    return _indexData.equities_only.series;
  }
  return _indexData.series || [];
}

// Convert price series to % change series
function toPctChange(series) {
  if (!series || series.length === 0) return [];
  const base = series[0].value;
  if (!base) return series;
  return series.map(s => ({
    time: s.time,
    value: ((s.value - base) / base) * 100,
  }));
}

// Filter series by date range
function filterByRange(series) {
  if (!series || series.length === 0) return [];
  if (chartRange === 'ytd') {
    const year = new Date().getFullYear();
    const cutoff = year + '-01-01';
    return series.filter(s => s.time >= cutoff);
  }
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - chartRange);
  const cutoffStr = cutoff.toISOString().slice(0, 10);
  return series.filter(s => s.time >= cutoffStr);
}

// Chart created once during page init, never destroyed.
// Index: LightweightCharts AreaSeries (setData works for first series).
// Compare: drawn on a canvas overlay using chart coordinate mapping
//   (LightweightCharts won't repaint additional series added after init).
let _chartReady = false;
let _compareOverlay = null; // canvas element
let _compareData = null;    // { series, color }

function _drawCompareOverlay() {
  if (!_compareOverlay || !activeChart || !activeIdxSeries) return;
  const canvas = _compareOverlay;
  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const container = document.getElementById('chart-container');
  const w = container.clientWidth;
  const h = 480;
  canvas.width = w * dpr;
  canvas.height = h * dpr;
  canvas.style.width = w + 'px';
  canvas.style.height = h + 'px';
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, w, h);

  if (!_compareData || !_compareData.series || _compareData.series.length < 2) return;

  const ts = activeChart.timeScale();
  const series = _compareData.series;
  const color = _compareData.color;

  // Map data to pixel coordinates using chart's coordinate system
  // (autoscaleInfoProvider ensures the price scale covers both datasets)
  const points = [];
  for (let i = 0; i < series.length; i++) {
    const x = ts.timeToCoordinate(series[i].time);
    const y = activeIdxSeries.priceToCoordinate(series[i].value);
    if (x !== null && y !== null && isFinite(x) && isFinite(y)) {
      points.push({ x, y });
    }
  }

  if (points.length < 2) return;

  // Draw the line
  ctx.beginPath();
  ctx.strokeStyle = color;
  ctx.lineWidth = 2;
  ctx.lineJoin = 'round';
  ctx.moveTo(points[0].x, points[0].y);
  for (let i = 1; i < points.length; i++) {
    ctx.lineTo(points[i].x, points[i].y);
  }
  ctx.stroke();

  // Draw last value label
  const last = points[points.length - 1];
  const lastVal = series[series.length - 1].value;
  const label = chartMode === 'pct' ? lastVal.toFixed(2) + '%' : lastVal.toFixed(2);
  ctx.font = '11px "Roboto Mono", monospace';
  ctx.fillStyle = color;
  ctx.textAlign = 'left';
  ctx.fillText(label, last.x + 5, last.y - 5);
}

async function renderChart() {
  // ---- Load all data (async) ----
  await loadIndexSeries(); // ensure _indexData is populated
  // Pick the right index series based on selected range
  // (equities-only for 3Y/5Y, full basket for <= 1Y)
  const rawIndex = getIndexSeriesForRange(chartRange);
  let idxSeries = rawIndex.map(s => ({ time: s.date, value: s.value }));

  let compareSeries = [];
  let compareColor = '#3b82f6';
  let hasCompare = false;
  let rawCompare = [];
  if (compareAsset) {
    const c = uniqueCompanies.find(x => x.ticker === compareAsset);
    compareColor = c ? (c.color || tickerColor(c.ticker)) : '#3b82f6';
    rawCompare = await loadHistory(compareAsset);
    compareSeries = rawCompare.map(s => ({ time: s.date, value: s.close ?? s.price ?? 0 }));
  }

  // ---- Update range button availability based on data ----
  // Check ALL available index data (full basket + equities-only) for max range
  const idxDays = idxSeries.length > 1
    ? Math.round((new Date(idxSeries[idxSeries.length-1].time) - new Date(idxSeries[0].time)) / 86400000)
    : 0;
  // Also check equities-only series (available for longer ranges)
  const eqSeries = _indexData?.equities_only?.series || [];
  const eqDays = eqSeries.length > 1
    ? Math.round((new Date(eqSeries[eqSeries.length-1].date) - new Date(eqSeries[0].date)) / 86400000)
    : 0;
  const compDays = compareSeries.length > 1
    ? Math.round((new Date(compareSeries[compareSeries.length-1].time) - new Date(compareSeries[0].time)) / 86400000)
    : 0;
  const availDays = Math.max(idxDays, eqDays, compDays);
  // Enable/disable range buttons based on available data
  document.querySelectorAll('#chart-range-btns button[data-range]').forEach(btn => {
    const r = btn.dataset.range;
    if (r === '0.5' || r === '1') return; // intraday stays disabled
    const rangeDays = r === 'ytd' ? 90 : parseFloat(r); // ytd always available
    if (rangeDays > availDays + 30) { // +30 day buffer
      btn.classList.add('disabled');
      btn.title = `Only ${Math.round(availDays/365*10)/10}Y of data available`;
    } else {
      btn.classList.remove('disabled');
      btn.title = '';
    }
  });

  // Auto-downgrade range if current selection exceeds available data
  if (chartRange !== 'ytd' && chartRange > availDays + 30) {
    // Find the largest available range that fits the data
    const ranges = [7, 30, 90, 365, 1095, 1825];
    chartRange = ranges.filter(r => r <= availDays + 30).pop() || 30;
    // Update active button
    document.querySelectorAll('#chart-range-btns button').forEach(b => {
      b.classList.toggle('active', parseFloat(b.dataset.range) === chartRange);
    });
  }

  // Apply range filter
  idxSeries = filterByRange(idxSeries);
  if (compareSeries.length > 0) {
    compareSeries = filterByRange(compareSeries);
    hasCompare = compareSeries.length > 0;
  }

  if (chartMode === 'pct') {
    idxSeries = toPctChange(idxSeries);
    if (hasCompare) compareSeries = toPctChange(compareSeries);
  }

  // ---- Create chart once (first call, during page init) ----
  const container = document.getElementById('chart-container');
  if (!container) return; // Element not present in current page layout
  if (!_chartReady) {
    _chartReady = true;
    container.innerHTML = '';
    container.style.position = 'relative';
    const chart = LightweightCharts.createChart(container, {
      width: container.clientWidth || 800,
      height: 480,
      layout: {
        background: { type: 'solid', color: '#1a1e27' },
        textColor: '#8b92a5',
        fontFamily: "'Roboto Mono', monospace",
        fontSize: 11,
      },
      grid: {
        vertLines: { color: '#252a3622' },
        horzLines: { color: '#252a3644' },
      },
      rightPriceScale: {
        borderColor: '#252a36',
        scaleMargins: { top: 0.1, bottom: 0.1 },
      },
      timeScale: {
        borderColor: '#252a36',
        timeVisible: false,
      },
    });

    activeIdxSeries = chart.addAreaSeries({
      lineColor: '#F5D921', lineWidth: 2,
      topColor: 'rgba(245,217,33,0.25)',
      bottomColor: 'rgba(245,217,33,0.02)',
      lastValueVisible: true, priceLineVisible: false,
    });
    activeIdxSeries.setData(idxSeries);
    chart.timeScale().fitContent();
    activeChart = chart;

    // Create overlay canvas for compare line
    _compareOverlay = document.createElement('canvas');
    _compareOverlay.style.position = 'absolute';
    _compareOverlay.style.top = '0';
    _compareOverlay.style.left = '0';
    _compareOverlay.style.pointerEvents = 'none';
    _compareOverlay.style.zIndex = '3';
    container.appendChild(_compareOverlay);

    // Redraw overlay when chart scrolls/zooms
    chart.timeScale().subscribeVisibleLogicalRangeChange(_drawCompareOverlay);

    // Set initial composition note
    const compNote0 = document.getElementById('chart-composition-note');
    if (compNote0 && _indexData) {
      compNote0.textContent = `Index: ${_indexData.entity_count} entities (equities + tokens)`;
    }
    return;
  }

  // ---- Subsequent renders ----
  activeIdxSeries.setData(idxSeries.length > 0 ? idxSeries : [{ time: '2000-01-01', value: 0 }]);
  activeChart.timeScale().fitContent();

  // Set autoscaleInfoProvider to include compare data range in Y-axis
  if (hasCompare) {
    const compMin = Math.min(...compareSeries.map(d => d.value));
    const compMax = Math.max(...compareSeries.map(d => d.value));
    const idxMin = Math.min(...idxSeries.map(d => d.value));
    const idxMax = Math.max(...idxSeries.map(d => d.value));
    const overallMin = Math.min(compMin, idxMin);
    const overallMax = Math.max(compMax, idxMax);
    activeIdxSeries.applyOptions({
      autoscaleInfoProvider: () => ({
        priceRange: { minValue: overallMin, maxValue: overallMax },
      }),
    });
  } else {
    activeIdxSeries.applyOptions({
      autoscaleInfoProvider: undefined,
    });
  }

  // Store compare data and draw overlay
  if (hasCompare) {
    _compareData = { series: compareSeries, color: compareColor };
  } else {
    _compareData = null;
  }
  // Delay overlay draw to let chart finish its layout update
  setTimeout(_drawCompareOverlay, 50);

  // Update composition note
  const compNote = document.getElementById('chart-composition-note');
  if (compNote) {
    const useEqOnly = (chartRange !== 'ytd' && chartRange > 365);
    const eqData = _indexData?.equities_only;
    if (useEqOnly && eqData) {
      compNote.textContent = `Index: ${eqData.entity_count} equities only (tokens excluded for ${chartRange > 1095 ? '5' : '3'}Y view \u2014 insufficient token history)`;
    } else if (_indexData) {
      compNote.textContent = `Index: ${_indexData.entity_count} entities (equities + tokens)`;
    } else {
      compNote.textContent = '';
    }
  }
}

// ===== FUNDRAISING RENDERING =====
let fFilter = 'all';
function setFundFilter(btn) {
  document.querySelectorAll('[data-ffilter]').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  fFilter = btn.dataset.ffilter;
  renderFundraising();
}

function renderFundraising() {
  const tbody = document.getElementById('fund-body');
  const s = (document.getElementById('fund-search').value || '').toLowerCase();
  let data = fFilter === 'all' ? raises : raises.filter(r => r.sector === fFilter);
  if (s) data = data.filter(r => r.company.toLowerCase().includes(s) || r.subsector.toLowerCase().includes(s) || r.investors.toLowerCase().includes(s));

  const stageClass = st => {
    const l = st.toLowerCase();
    if (l.includes('pre')) return 'stage-pre';
    if (l.includes('seed')) return 'stage-seed';
    if (l.includes('series a')) return 'stage-a';
    if (l.includes('series b')) return 'stage-b';
    if (l.includes('series c')) return 'stage-c';
    return 'stage-late';
  };

  const sectorClass = sc => sc === 'semi' ? 'stag-semi' : sc === 'robo' ? 'stag-robo' : 'stag-infra';
  const sectorLabel = sc => sc === 'semi' ? 'Semis' : sc === 'robo' ? 'Robotics' : 'Infra';

  tbody.innerHTML = data.map((r, i) => {
    return `<tr>
      <td><span class="rank">${i+1}</span></td>
      <td><div><span class="co-name">${r.company}</span><span class="co-sub">${r.hq} · ${r.subsector}</span></div></td>
      <td><span class="stage-tag ${stageClass(r.stage)}">${r.stage}</span></td>
      <td><span class="prc">$${r.amount}M</span></td>
      <td><span class="tkr">${r.date}</span></td>
      <td><span class="mcap">${r.valuation || '—'}</span></td>
      <td><span class="investor-list">${r.investors}</span></td>
      <td><span class="stag ${sectorClass(r.sector)}">${sectorLabel(r.sector)}</span></td>
      <td><span class="tkr" style="font-size:var(--fs-label)">${r.source}</span></td>
    </tr>`;
  }).join('');
}

// ===== TAB SWITCHING =====
function switchTab(tab) {
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('tab-' + tab).classList.add('active');
  document.querySelectorAll('.tab-btn').forEach(b => {
    if (b.dataset.tab === tab) b.classList.add('active');
  });
}

function switchSubtab(sub) {
  document.querySelectorAll('.subtab-content').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.subtab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('subtab-' + sub).classList.add('active');
  document.querySelector(`.subtab-btn[data-subtab="${sub}"]`).classList.add('active');
}

// ===== CSV EXPORT =====
function exportCSV() {
  const headers = ['Company','HQ','Stage','Amount ($M)','Date','Valuation','Lead Investors','Sector','Subsector','Source'];
  const rows = raises.map(r => [r.company, r.hq, r.stage, r.amount, r.date, r.valuation, `"${r.investors}"`, r.sector, r.subsector, r.source]);
  const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'robotnik_fundraising.csv';
  a.click();
}

// ===== INTELLIGENCE DATA =====
let newsData = [], researchData = [], filingsData = [], reportsData = [];
let iTypeFilter = 'all', iCatFilter = 'all', intelligenceDisplayCount = 25;

async function loadIntelligenceData() {
  const cb = '?v=' + Date.now();
  const load = (url) => fetch(url + cb).then(r => r.ok ? r.json() : null).catch(() => null);
  const [news, research, filings, reports] = await Promise.all([
    load('data/news.json'), load('data/research.json'), load('data/filings.json'), load('data/reports.json'),
  ]);
  if (news) newsData = news.items || [];
  if (research) researchData = research.papers || [];
  if (filings) filingsData = filings.filings || [];
  if (reports) reportsData = reports.reports || [];

  var el1 = document.getElementById('stat-news-count');
  if (el1) el1.textContent = newsData.length || '\u2014';
  var el2 = document.getElementById('stat-paper-count');
  if (el2) el2.textContent = researchData.length || '\u2014';
  var el3 = document.getElementById('stat-filing-count');
  if (el3) el3.textContent = filingsData.length || '\u2014';
  const updated = (news && news.updated) || (research && research.updated) || '\u2014';
  var el4 = document.getElementById('stat-updated');
  if (el4) el4.textContent = updated;
  renderIntelligence();
}

function setInsightType(btn) {
  document.querySelectorAll('[data-itype]').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  iTypeFilter = btn.dataset.itype;
  intelligenceDisplayCount = 25;
  renderIntelligence();
}

function setInsightCat(btn) {
  document.querySelectorAll('[data-icat]').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  iCatFilter = btn.dataset.icat;
  intelligenceDisplayCount = 25;
  renderIntelligence();
}

function catTag(cat) {
  const cls = cat === 'semi' ? 'stag-semi' : cat === 'robo' ? 'stag-robo' : cat === 'ai' ? 'stag-ai' : cat === 'supply' ? 'stag-supply' : 'stag-infra';
  const lbl = cat === 'semi' ? 'Semis' : cat === 'robo' ? 'Robotics' : cat === 'ai' ? 'AI/ML' : cat === 'supply' ? 'Supply Chain' : cat;
  return `<span class="stag ${cls}">${lbl}</span>`;
}

function renderNewsCard(n) {
  return `<div class="news-card">
    <div style="display:flex;justify-content:space-between;align-items:center;">
      <span class="news-card-source">${n.source}</span>${catTag(n.category)}
    </div>
    <div class="news-card-title"><a href="${n.url}" target="_blank" rel="noopener">${n.title}</a></div>
    <div class="news-card-date">${n.date || ''}</div>
    ${n.summary ? `<div class="news-card-summary">${n.summary}</div>` : ''}
  </div>`;
}

function renderPaperCard(p) {
  const authors = (p.authors || []).slice(0, 3).join(', ') + (p.authors && p.authors.length > 3 ? ' et al.' : '');
  return `<div class="paper-card">
    <div style="display:flex;justify-content:space-between;align-items:center;">
      <span class="paper-meta">${p.journal || 'Research paper'}</span>
      <div style="display:flex;gap:0.3rem;">${p.open_access ? '<span class="oa-badge">Open Access</span>' : ''}${catTag(p.category)}</div>
    </div>
    <div class="paper-title"><a href="${p.doi_url || '#'}" target="_blank" rel="noopener">${p.title}</a></div>
    <div class="paper-meta">${authors}${p.date ? ' · ' + p.date : ''}${p.citation_count ? ' · ' + p.citation_count + ' citations' : ''}</div>
    ${p.abstract_snippet ? `<div class="paper-abstract">${p.abstract_snippet}</div>` : ''}
    ${p.topics && p.topics.length ? `<div class="paper-tags">${p.topics.slice(0,4).map(t=>`<span class="paper-tag">${t}</span>`).join('')}</div>` : ''}
  </div>`;
}

function renderFilingCard(f) {
  return `<div class="paper-card">
    <div style="display:flex;justify-content:space-between;align-items:center;">
      <div class="filing-company">${f.company}<span class="filing-ticker">${f.ticker}</span></div>
      <div style="display:flex;gap:0.3rem;"><span class="filing-type-small">${f.form_type}</span><span class="stag stag-filing">SEC</span></div>
    </div>
    <div class="paper-title"><a href="${f.url}" target="_blank" rel="noopener">${f.description || f.form_type}</a></div>
    <div class="paper-meta">${f.date} · SEC EDGAR</div>
  </div>`;
}

function renderReportCard(r) {
  return `<div class="paper-card">
    <div style="display:flex;justify-content:space-between;align-items:center;">
      <span class="paper-meta">${r.source}</span>${catTag(r.category)}
    </div>
    <div class="paper-title"><a href="${r.url}" target="_blank" rel="noopener">${r.title}</a></div>
    <div class="paper-meta">${r.date || 'Industry report'}</div>
    ${r.summary ? `<div class="paper-abstract">${r.summary}</div>` : ''}
  </div>`;
}

function renderIntelligence() {
  const container = document.getElementById('intelligence-content');
  if (!container) return; // Element not present in current page layout
  const searchEl = document.getElementById('intelligence-search');
  const search = (searchEl ? searchEl.value : '').toLowerCase();

  let items = [];
  if (iTypeFilter === 'all' || iTypeFilter === 'news')
    items = items.concat(newsData.map(n => ({...n, _type:'news'})));
  if (iTypeFilter === 'all' || iTypeFilter === 'research')
    items = items.concat(researchData.map(p => ({...p, _type:'research'})));
  if (iTypeFilter === 'all' || iTypeFilter === 'filings')
    items = items.concat(filingsData.map(f => ({...f, _type:'filing', category: 'semi'})));
  if (iTypeFilter === 'all' || iTypeFilter === 'reports')
    items = items.concat(reportsData.map(r => ({...r, _type:'report'})));

  if (iCatFilter !== 'all') items = items.filter(i => i.category === iCatFilter);

  if (search) {
    items = items.filter(i => {
      const text = (i.title + ' ' + (i.summary || i.abstract_snippet || i.description || '') + ' ' + (i.source || i.company || '')).toLowerCase();
      return text.includes(search);
    });
  }

  items.sort((a,b) => (b.date || '').localeCompare(a.date || ''));
  const visible = items.slice(0, intelligenceDisplayCount);
  document.getElementById('intelligence-load-more').style.display = items.length > intelligenceDisplayCount ? 'inline-block' : 'none';

  if (!visible.length) {
    container.innerHTML = '<div style="text-align:center;padding:3rem;color:var(--text-muted);font-size:var(--fs-table);">No signals detected in this sector, tovarishch. Robotnik will continue scanning.</div>';
    return;
  }

  const useGrid = iTypeFilter === 'news';
  const cards = visible.map(i =>
    i._type === 'news' ? renderNewsCard(i) :
    i._type === 'research' ? renderPaperCard(i) :
    i._type === 'filing' ? renderFilingCard(i) :
    renderReportCard(i)
  ).join('');

  container.innerHTML = useGrid
    ? `<div class="news-grid">${cards}</div>`
    : `<div class="paper-list">${cards}</div>`;
}

function loadMoreIntelligence() {
  intelligenceDisplayCount += 25;
  renderIntelligence();
}

// ===== SIGNUP =====
function handleSignup() {
  const email = document.getElementById('email-input').value;
  const msg = document.getElementById('signup-msg');
  if (email && email.includes('@')) {
    msg.style.display = 'block';
    msg.style.color = '#22c55e';
    msg.textContent = "Welcome aboard, tovarishch. Robotnik will transmit shortly.";
    document.getElementById('email-input').value = '';
  } else {
    msg.style.display = 'block';
    msg.style.color = '#ef4444';
    msg.textContent = 'Communication line not recognized. Please verify coordinates.';
  }
}

// Smooth scroll (only for pure in-page anchors)
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    const href = a.getAttribute('href');
    if (href.length > 1 && !href.includes('.html')) {
      e.preventDefault();
      const target = document.querySelector(href);
      if (target) target.scrollIntoView({ behavior: 'smooth' });
    }
  });
});

// ===== INDEX CHART =====
let indexChart = null;
let indexAreaSeries = null;
let indexChartData = {};
let indexSubMeta = {};       // {key: {current_value, entity_count, ...}}
let currentIndexSeries = 'composite';
let currentIndexRange = 365;  // days, or 'ytd' — default 1Y
let compareLines = [];       // [{ticker, series, color, isBenchmark}]
const COMPARE_COLORS = ['#3B82F6', '#10B981', '#F59E0B'];
const BENCHMARK_META = {
  'SPY':  { name: 'S&P 500',  color: '#7B8794' },
  'QQQ':  { name: 'NASDAQ',   color: '#5B9BD5' },
  'SOXX': { name: 'SOX',      color: '#E97451' },
  'ROBO': { name: 'ROBO ETF', color: '#70AD47' },
};
let _benchmarkData = null;   // loaded from data/prices/benchmarks.json

function initIndexChart() {
  const container = document.getElementById('index-chart-container');
  const placeholder = document.getElementById('chart-placeholder');
  if (!container || typeof LightweightCharts === 'undefined') return;

  fetch('data/index/robotnik_index.json')
    .then(r => { if (!r.ok) throw new Error('No data'); return r.json(); })
    .then(data => {
      var series = Array.isArray(data) ? data : (data.series || []);
      if (!series.length) throw new Error('Empty');
      indexChartData.composite = series;
      indexSubMeta.composite = { current_value: data.current_value, entity_count: data.entity_count };
      // Also store equities-only for longer ranges
      if (data.equities_only && data.equities_only.series) {
        indexChartData.composite_eq = data.equities_only.series;
      }
      placeholder.style.display = 'none';
      createIndexChart(container, series);

      // Update index widget (applyIndexData will set value+% for 1Y default)
      // Set base date labels
      if (data.base_date) {
        var chartBase = document.getElementById('chart-base-label');
        if (chartBase) chartBase.textContent = 'Base: 1,000.00 on ' + data.base_date;
        var explainerBase = document.getElementById('explainer-base');
        if (explainerBase) explainerBase.textContent = 'Base: 1,000.00 on ' + data.base_date;
      }

      // Load sub-indices
      fetch('data/index/sub_indices.json')
        .then(r => r.ok ? r.json() : {})
        .then(sub => {
          var keyMap = {
            semi: ['semi', 'semiconductor'],
            robotics: ['robotics'],
            space: ['space'],
            token: ['token'],
            materials: ['materials']
          };
          for (var chartKey in keyMap) {
            for (var i = 0; i < keyMap[chartKey].length; i++) {
              var jsonKey = keyMap[chartKey][i];
              if (sub[jsonKey]) {
                var s = Array.isArray(sub[jsonKey]) ? sub[jsonKey] : (sub[jsonKey].series || []);
                indexChartData[chartKey] = s;
                indexSubMeta[chartKey] = { current_value: sub[jsonKey].current_value, entity_count: sub[jsonKey].entity_count };
                // Update dashboard card with 24h change
                var card = document.querySelector('[data-sub="' + jsonKey + '"]');
                if (card && sub[jsonKey].current_value) {
                  var cv = sub[jsonKey].current_value;
                  var vel = card.querySelector('.sub-index-val');
                  if (vel) vel.textContent = cv.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2});
                  var seriesArr = sub[jsonKey].series || [];
                  if (seriesArr.length > 1) {
                    // Use last 2 data points for 24h change
                    var prevV = seriesArr[seriesArr.length - 2].value;
                    var lastV = seriesArr[seriesArr.length - 1].value;
                    var pc24 = prevV ? ((lastV - prevV) / prevV * 100) : 0;
                    var ce = card.querySelector('.sub-index-chg');
                    if (ce) { ce.textContent = (pc24 >= 0 ? '+' : '') + pc24.toFixed(2) + '% (24h)'; ce.className = 'sub-index-chg ' + (pc24 >= 0 ? 'v-green' : 'v-red'); }
                  }
                }
                break;
              }
            }
          }
        }).catch(() => {});
    })
    .catch(() => { placeholder.style.display = 'flex'; });
}

function createIndexChart(container, data) {
  indexChart = LightweightCharts.createChart(container, {
    width: container.clientWidth, height: 270,
    layout: { background: { type: 'solid', color: 'transparent' }, textColor: '#8B92A5', fontFamily: "'Roboto Mono', monospace", fontSize: 10 },
    grid: { vertLines: { color: '#1E2330' }, horzLines: { color: '#1E2330' } },
    crosshair: { vertLine: { color: '#F5D921', width: 1, style: 2 }, horzLine: { color: '#F5D921', width: 1, style: 2 } },
    timeScale: { borderColor: '#1E2330', timeVisible: false },
    rightPriceScale: { borderColor: '#1E2330' },
  });
  indexAreaSeries = indexChart.addAreaSeries({
    lineColor: '#F5D921', topColor: 'rgba(245,217,33,0.10)', bottomColor: 'rgba(245,217,33,0.02)', lineWidth: 2,
  });
  applyIndexData(data);
  const ro = new ResizeObserver(() => { indexChart.applyOptions({ width: container.clientWidth }); });
  ro.observe(container);
  // Add base label inside chart area (bottom-left)
  var baseLabel = document.createElement('div');
  baseLabel.id = 'chart-base-label';
  baseLabel.style.cssText = 'position:absolute;bottom:24px;left:8px;font-size:9px;color:#5A6178;font-family:var(--font);z-index:2;pointer-events:none;';
  container.appendChild(baseLabel);
}

function getFilteredData(data) {
  if (!data || !data.length) return [];
  let filtered = data;
  if (currentIndexRange === 'ytd') {
    var year = new Date().getFullYear();
    var cutoffStr = year + '-01-01';
    filtered = data.filter(d => (d.time || d.date) >= cutoffStr);
  } else if (currentIndexRange > 0) {
    var cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - currentIndexRange);
    var cutoffStr2 = cutoff.toISOString().slice(0, 10);
    filtered = data.filter(d => (d.time || d.date) >= cutoffStr2);
  }
  return filtered.length > 0 ? filtered : data;
}

function getRangeLabel() {
  if (currentIndexRange === 'ytd') return 'YTD';
  var labels = {1:'1D',7:'1W',30:'1M',90:'3M',365:'1Y',1095:'3Y',1825:'5Y',0:'ALL'};
  return labels[currentIndexRange] || currentIndexRange + 'D';
}

function applyIndexData(data) {
  if (!indexAreaSeries || !data || !data.length) return;
  var filtered = getFilteredData(data);
  indexAreaSeries.setData(filtered.map(d => ({ time: d.time || d.date, value: d.value || d.close })));
  indexChart.timeScale().fitContent();
  // Update the main index hero value + % to match selected period
  var last = filtered[filtered.length - 1];
  var first = filtered[0];
  var heroVal = document.querySelector('.index-value');
  var heroChg = document.querySelector('.index-change');
  if (heroVal && last) heroVal.textContent = (last.value || last.close || 0).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2});
  if (heroChg && last && first) {
    var hv = last.value || last.close || 0, hs = first.value || first.close || 0;
    var hc = hs ? ((hv - hs) / hs * 100) : 0;
    heroChg.textContent = (hc >= 0 ? '+' : '') + hc.toFixed(2) + '% (' + getRangeLabel() + ')';
    heroChg.className = 'index-change ' + (hc >= 0 ? 'v-green' : 'v-red');
  }
  // Update range button availability
  updateRangeAvailability(data);
  // Update compare lines
  refreshCompareLines();
}

function updateRangeAvailability(data) {
  if (!data || !data.length) return;
  var firstDate = data[0].time || data[0].date;
  var lastDate = data[data.length - 1].time || data[data.length - 1].date;
  var availDays = Math.round((new Date(lastDate) - new Date(firstDate)) / 86400000);
  // For composite, also consider equities-only data
  if (currentIndexSeries === 'composite' && indexChartData.composite_eq && indexChartData.composite_eq.length) {
    var eqFirst = indexChartData.composite_eq[0].time || indexChartData.composite_eq[0].date;
    var eqLast = indexChartData.composite_eq[indexChartData.composite_eq.length - 1].time || indexChartData.composite_eq[indexChartData.composite_eq.length - 1].date;
    availDays = Math.max(availDays, Math.round((new Date(eqLast) - new Date(eqFirst)) / 86400000));
    firstDate = eqFirst < firstDate ? eqFirst : firstDate;
  }
  document.querySelectorAll('.chart-range-btn[data-range]').forEach(function(btn) {
    var r = btn.dataset.range;
    if (r === '0.5' || r === '1') return; // 12H and 1D stay disabled (no intraday data)
    if (r === 'ytd' || r === '0') { btn.classList.remove('disabled'); btn.removeAttribute('title'); return; }
    var days = parseInt(r);
    if (days > availDays + 30) {
      btn.classList.add('disabled');
      btn.title = 'Data available from ' + firstDate;
      btn.onclick = null;
    } else {
      btn.classList.remove('disabled');
      btn.removeAttribute('title');
      btn.onclick = function() { setIndexRange(this); };
    }
  });
}

function setIndexRange(btn) {
  document.querySelectorAll('.chart-range-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  var rv = btn.dataset.range;
  currentIndexRange = (rv === 'ytd') ? 'ytd' : (parseInt(rv) || 0);
  var data = indexChartData[currentIndexSeries];
  // For composite with long ranges, use equities-only if available
  if (currentIndexSeries === 'composite' && currentIndexRange !== 'ytd' && currentIndexRange > 365 && indexChartData.composite_eq) {
    data = indexChartData.composite_eq;
  }
  if (data) applyIndexData(data);
}

function setIndexSeries(btn) {
  document.querySelectorAll('.chart-index-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  currentIndexSeries = btn.dataset.idx;
  var data = indexChartData[currentIndexSeries];
  // Update title
  var titleEl = document.getElementById('chart-title');
  var labels = { composite:'Robotnik Index', semi:'Semi Index', robotics:'Robotics Index', space:'Space Index', materials:'Materials Index', token:'Token Index' };
  if (titleEl) titleEl.textContent = labels[currentIndexSeries] || 'Robotnik Index';
  if (data) {
    applyIndexData(data);
  } else {
    if (indexAreaSeries) indexAreaSeries.setData([]);
    var valEl = document.getElementById('chart-index-val');
    var chgEl = document.getElementById('chart-index-chg');
    if (valEl) valEl.textContent = '--';
    if (chgEl) { chgEl.textContent = ''; chgEl.className = 'chart-widget-chg'; }
  }
}

// ===== ASSET COMPARISON =====
// TODO: Restrict to 1 comparison for free users, 3 for premium
// Gate behind auth when premium tier is implemented
function toggleCompareInput() {
  var row = document.getElementById('compare-input-row');
  if (!row) return;
  row.style.display = row.style.display === 'none' ? 'flex' : 'none';
  if (row.style.display !== 'none') document.getElementById('compare-search').focus();
}

function filterCompareResults() {
  var q = (document.getElementById('compare-search').value || '').toUpperCase().trim();
  var box = document.getElementById('compare-results');
  if (!box || q.length < 1) { if (box) box.innerHTML = ''; return; }
  var matches = uniqueCompanies.filter(c => c.ticker.toUpperCase().includes(q) || c.name.toUpperCase().includes(q)).slice(0, 6);
  box.innerHTML = matches.map(c => '<div class="compare-result-item" onclick="addCompare(\'' + c.ticker + '\')">' + c.ticker + ' <span style="color:var(--text-muted)">' + c.name + '</span></div>').join('');
}

function addCompare(ticker) {
  if (compareLines.length >= 3) return;
  if (compareLines.find(c => c.ticker === ticker)) return;
  var color = COMPARE_COLORS[compareLines.length];
  // Load history
  fetch('data/prices/history/' + ticker + '.json')
    .then(r => r.ok ? r.json() : null)
    .then(data => {
      if (!data || !data.series || !data.series.length) {
        // Try with exchange suffix
        return fetch('data/prices/history/' + ticker + '.US.json').then(r => r.ok ? r.json() : null);
      }
      return data;
    })
    .then(data => {
      if (!data || !data.series) return;
      var lineSeries = indexChart.addLineSeries({ color: color, lineWidth: 2, lastValueVisible: true, priceLineVisible: false });
      compareLines.push({ ticker: ticker, series: data.series, color: color, lwcSeries: lineSeries });
      refreshCompareLines();
      renderComparePillsChart();
      // Hide search
      document.getElementById('compare-input-row').style.display = 'none';
      document.getElementById('compare-search').value = '';
      document.getElementById('compare-results').innerHTML = '';
    });
}

function addBenchmark(ticker) {
  if (compareLines.length >= 3) return;
  if (compareLines.find(function(c) { return c.ticker === ticker; })) {
    removeCompare(ticker);
    return;
  }
  var meta = BENCHMARK_META[ticker];
  if (!meta) return;
  var color = meta.color;

  function doAdd(series) {
    if (!series || !series.length) return;
    if (!indexChart) return;
    var lineSeries = indexChart.addLineSeries({ color: color, lineWidth: 2, lastValueVisible: true, priceLineVisible: false });
    compareLines.push({ ticker: ticker, series: series, color: color, lwcSeries: lineSeries, isBenchmark: true, name: meta.name });
    refreshCompareLines();
    renderComparePillsChart();
    // Toggle button active state
    var btns = document.querySelectorAll('.benchmark-btn');
    btns.forEach(function(b) {
      if (b.textContent.includes(meta.name) || b.onclick.toString().includes(ticker)) {
        b.classList.add('active');
      }
    });
  }

  // Load benchmark data
  if (_benchmarkData) {
    var bm = _benchmarkData.benchmarks[ticker];
    if (bm && bm.series) doAdd(bm.series.map(function(d) { return { date: d.date, close: d.close }; }));
  } else {
    fetch('data/prices/benchmarks.json?v=' + Date.now())
      .then(function(r) { return r.ok ? r.json() : null; })
      .then(function(data) {
        if (!data) return;
        _benchmarkData = data;
        var bm = data.benchmarks[ticker];
        if (bm && bm.series) doAdd(bm.series.map(function(d) { return { date: d.date, close: d.close }; }));
      });
  }
}

function removeCompare(ticker) {
  var idx = compareLines.findIndex(function(c) { return c.ticker === ticker; });
  if (idx === -1) return;
  if (indexChart && compareLines[idx].lwcSeries) indexChart.removeSeries(compareLines[idx].lwcSeries);
  compareLines.splice(idx, 1);
  renderComparePillsChart();
  // Deactivate benchmark button if applicable
  if (BENCHMARK_META[ticker]) {
    var btns = document.querySelectorAll('.benchmark-btn');
    btns.forEach(function(b) { if (b.onclick && b.onclick.toString().includes(ticker)) b.classList.remove('active'); });
  }
}

function refreshCompareLines() {
  if (!indexChart) return;
  // Get current index data to normalise % change from same start date
  var idxData = indexChartData[currentIndexSeries] || [];
  var filtered = getFilteredData(idxData);
  var startDate = filtered.length ? (filtered[0].time || filtered[0].date) : null;

  for (var i = 0; i < compareLines.length; i++) {
    var cl = compareLines[i];
    var compFiltered = getFilteredData(cl.series.map(d => ({ time: d.date, value: d.close || d.price || d.value })));
    // Normalise to % change matching index base value
    if (compFiltered.length > 0 && filtered.length > 0) {
      var idxBase = filtered[0].value || filtered[0].close || 1;
      var compBase = compFiltered[0].value || 1;
      var normalised = compFiltered.map(d => ({
        time: d.time,
        value: idxBase * (d.value / compBase)
      }));
      cl.lwcSeries.setData(normalised);
    }
  }
}

function renderComparePillsChart() {
  var box = document.getElementById('compare-pills');
  if (!box) return;
  if (!compareLines.length) { box.innerHTML = ''; return; }
  box.innerHTML = compareLines.map(function(c) {
    var label = c.name || c.ticker;
    return '<span class="compare-pill-chip" style="border-color:' + c.color + ';color:' + c.color + '">' +
    '<span style="background:' + c.color + ';width:6px;height:6px;border-radius:50%;display:inline-block;margin-right:4px;"></span>' +
    label + ' <span onclick="removeCompare(\'' + c.ticker + '\')" style="cursor:pointer;margin-left:4px;opacity:0.6;">&times;</span></span>';
  }).join(' ');
}

// ===== MARKET TABLE (dynamic rendering) =====
var mktSector = 'all';
var mktSort = 'mcap';
var mktSortDir = -1; // -1 = desc, 1 = asc
var SECTOR_LABELS = {semi:'Semi', robo:'Robo', space:'Space', materials:'Materials', token:'Token'};
var SECTOR_CSS = {semi:'sector-semi', robo:'sector-robo', space:'sector-space', materials:'sector-materials', token:'sector-token'};

function filterMarketTable(btn) {
  document.querySelectorAll('.market-tab').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  mktSector = btn.dataset.sector;
  renderMarketTable();
}

function sortMarketTable(col) {
  if (mktSort === col) { mktSortDir *= -1; } else { mktSort = col; mktSortDir = -1; }
  renderMarketTable();
}

function renderMarketTable() {
  var tbody = document.getElementById('mkt-tbody');
  if (!tbody || !uniqueCompanies.length) return;
  var search = (document.getElementById('mkt-search')?.value || '').toLowerCase();
  var data = mktSector === 'all' ? uniqueCompanies : uniqueCompanies.filter(c => c.sector === mktSector);
  if (search) data = data.filter(c => c.ticker.toLowerCase().includes(search) || c.name.toLowerCase().includes(search));

  // Sort
  var sorted = data.slice().sort(function(a, b) {
    var va, vb;
    if (mktSort === 'ticker') { va = a.ticker; vb = b.ticker; return va < vb ? -mktSortDir : va > vb ? mktSortDir : 0; }
    if (mktSort === 'company') { va = a.name; vb = b.name; return va < vb ? -mktSortDir : va > vb ? mktSortDir : 0; }
    if (mktSort === 'sector') { va = a.sector; vb = b.sector; return va < vb ? -mktSortDir : va > vb ? mktSortDir : 0; }
    if (mktSort === 'price') { return (a.price - b.price) * mktSortDir; }
    if (mktSort === 'change') { return (a.change - b.change) * mktSortDir; }
    return ((a.mcap || 0) - (b.mcap || 0)) * mktSortDir; // default: mcap
  });

  var top10 = search ? sorted : sorted.slice(0, 10);
  var rows = top10.map(function(c, i) {
    var chgCls = c.change >= 0 ? 'v-green' : 'v-red';
    var chgSign = c.change >= 0 ? '+' : '';
    var secCss = SECTOR_CSS[c.sector] || 'sector-semi';
    var secLabel = SECTOR_LABELS[c.sector] || c.sector;
    return '<tr><td>' + (i+1) + '</td><td class="ticker">' + c.ticker + '</td><td class="company-name">' + c.name +
      '</td><td><span class="sector-tag ' + secCss + '">' + secLabel + '</span></td><td class="r">' + fmtPrice(c.price, c.currency) +
      '</td><td class="r ' + chgCls + '">' + chgSign + c.change.toFixed(2) + '%</td><td class="r">' + c.mcapFmt + '</td></tr>';
  }).join('');
  tbody.innerHTML = rows;

  // Update sort arrows
  ['#','ticker','company','sector','price','change','mcap'].forEach(function(col) {
    var el = document.getElementById('sort-arrow-' + col);
    if (el) el.textContent = mktSort === col ? (mktSortDir === -1 ? '▼' : '▲') : '';
  });

  // Update tab counts
  var tabs = document.querySelectorAll('.market-tab');
  var counts = {all: uniqueCompanies.length, semi:0, robo:0, space:0, materials:0, token:0};
  uniqueCompanies.forEach(function(c) { if (counts[c.sector] !== undefined) counts[c.sector]++; });
  tabs.forEach(function(t) {
    var s = t.dataset.sector;
    var label = s === 'all' ? 'All' : s === 'semi' ? 'Semi' : s === 'robo' ? 'Robotics' : s === 'space' ? 'Space' : s === 'materials' ? 'Materials' : 'Tokens';
    t.textContent = label + ' (' + (counts[s] || 0) + ')';
  });

  // Update view all link
  var viewAll = document.getElementById('mkt-view-all');
  if (viewAll) viewAll.textContent = 'View all ' + data.length + ' assets →';
}

// ===== EXPORT MODAL =====
function showExportModal() { document.getElementById('export-modal').style.display = 'flex'; }
function closeExportModal() { document.getElementById('export-modal').style.display = 'none'; }
document.addEventListener('keydown', function(e) { if (e.key === 'Escape') closeExportModal(); });

// ===== NEWS FEED (try live data) =====
function loadNewsFeed() {
  // Try loading from data/news.json (RSS pipeline output)
  fetch('data/news.json?v=' + Date.now())
    .then(function(r) { if (!r.ok) throw new Error('no data'); return r.json(); })
    .then(function(data) {
      var items = (data.items || data).slice(0, 5);
      if (!items.length) throw new Error('empty');
      var container = document.getElementById('news-feed-container');
      if (!container) return;
      container.innerHTML = items.map(function(item) {
        var title = item.title || item.headline || '';
        var url = item.url || item.link || '#';
        var source = item.source || item.feed_name || '';
        var timeAgo = '';
        if (item.published || item.date) {
          var diff = Date.now() - new Date(item.published || item.date).getTime();
          var hrs = Math.floor(diff / 3600000);
          timeAgo = hrs < 1 ? 'Just now' : hrs < 24 ? hrs + 'h ago' : Math.floor(hrs/24) + 'd ago';
        }
        return '<div class="news-item"><a href="' + url + '" target="_blank" rel="noopener" class="news-headline">' + title + '</a><div class="news-meta">' + timeAgo + (source ? ' · ' + source : '') + '</div></div>';
      }).join('');
    })
    .catch(function() {
      // Keep placeholder headlines, note already in HTML
    });
}

// Page-gated initialization
const _page = document.body.dataset.page;
if (_page === 'home') {
  loadPriceData();
  initIndexChart();
  loadNewsFeed();
}
if (_page === 'intelligence') {
  loadIntelligenceData();
}
