// ===== MARKET DATA =====
// ===== DYNAMIC PRICE DATA =====
let allCompanies = [];
let uniqueCompanies = [];
let marketShowLimit = 50;

// Shared date formatter: DD-MMM-YYYY HH:MM UTC
function fmtDateRobotnik(d) {
  if (!d) return '—';
  var dt = (d instanceof Date) ? d : new Date(d);
  if (isNaN(dt.getTime())) return String(d);
  var months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  return dt.getUTCDate() + '-' + months[dt.getUTCMonth()] + '-' + dt.getUTCFullYear() + ' ' +
    String(dt.getUTCHours()).padStart(2,'0') + ':' + String(dt.getUTCMinutes()).padStart(2,'0') + ' UTC';
}

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
    const [priceResp, mcapResp, summaryResp, registryResp, liveResp, metricsResp, weightsResp] = await Promise.allSettled([
      fetch('data/prices/all_prices.json' + cb),
      fetch('data/index/market_caps.json' + cb),
      fetch('data/index/summary.json' + cb),
      fetch('data/registries/entity_registry.json' + cb),
      fetch('data/prices/live.json' + cb),
      fetch('data/markets/robotnik_public_markets.json' + cb),
      fetch('data/index/weights.json' + cb),
    ]);

    // Build sector counts from index weights (authoritative for "index-eligible")
    if (weightsResp.status === 'fulfilled' && weightsResp.value.ok) {
      var weightsData = await weightsResp.value.json();
      if (weightsData && weightsData.weights) {
        window.indexWeightSectors = {semi:0, robo:0, space:0, materials:0};
        weightsData.weights.forEach(function(w) {
          var s = mapSector(w.sector);
          if (window.indexWeightSectors[s] !== undefined) window.indexWeightSectors[s]++;
        });
      }
    }

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

    // Load live data overlay (if available and recent)
    let liveMap = {};
    let isLive = false;
    if (liveResp.status === 'fulfilled' && liveResp.value.ok) {
      const liveData = await liveResp.value.json();
      if (liveData && liveData.prices) {
        // Check if live data is recent (within last 2 hours)
        const liveTs = new Date(liveData.fetched_at);
        const ageMs = Date.now() - liveTs.getTime();
        if (ageMs < 2 * 60 * 60 * 1000) {
          isLive = true;
          for (const [key, val] of Object.entries(liveData.prices)) {
            if (!key.startsWith('BM_') && val.price) {
              liveMap[val.ticker] = val;
            }
          }
        }
      }
    }

    // Load metrics data (for sparklines and multi-timeframe %)
    window.metricsData = {};
    if (metricsResp.status === 'fulfilled' && metricsResp.value.ok) {
      var mData = await metricsResp.value.json();
      if (mData && mData.entities) window.metricsData = mData.entities;
    }

    // Build mcap lookup
    const mcapMap = {};
    if (mcapData && mcapData.market_caps) {
      for (const m of mcapData.market_caps) {
        mcapMap[m.ticker] = m.market_cap_usd;
      }
    }

    if (priceData && priceData.prices) {
      // Filter out excluded entities and tokens
      const activePrices = priceData.prices.filter(e => !excludedTickers.has(e.ticker) && mapSector(e.sector) !== 'token');
      allCompanies = activePrices.map(e => {
        // Overlay live price if available
        const live = liveMap[e.ticker];
        const price = live ? live.price : (e.price || 0);
        const change = live ? (live.change_pct || 0) : (e.change_pct || 0);
        return {
        name: e.name || e.ticker,
        sub: e.sector || '',
        ticker: e.ticker,
        price: price,
        change: change,
        mcap: mcapMap[e.ticker] || 0,
        mcapFmt: fmtMcap(mcapMap[e.ticker]),
        sector: mapSector(e.sector),
        currency: e.currency || 'USD',
        color: tickerColor(e.ticker),
        date: (live && typeof live.timestamp === 'number' && live.timestamp > 0) ? new Date(live.timestamp * 1000).toISOString().slice(0,10) : (e.date || ''),
        isLive: !!live,
      };});

      // Dedupe
      const seen = new Set();
      uniqueCompanies = allCompanies.filter(c => { if (seen.has(c.ticker)) return false; seen.add(c.ticker); return true; });

      // Sort by market cap desc (entities without mcap go to bottom)
      uniqueCompanies.sort((a, b) => (b.mcap || 0) - (a.mcap || 0));

      // Expose the price-feed timestamp for updateMarketOverview's
      // "Last Updated" row. Was previously set to new Date() at render
      // time, which made the sidebar disagree with the chart's
      // Last-updated indicator (the chart reads summary.json's
      // calculated_at, the sidebar was reading wall-clock "now").
      window._priceFetchedAt = priceData.fetched_at || null;

      // Update timestamp note
      const note = document.getElementById('market-note');
      if (note) {
        const ts = priceData.fetched_at ? fmtDateRobotnik(priceData.fetched_at).split(' ')[0] : 'unknown';
        const liveTag = isLive ? ' · Live (15-min delayed)' : '';
        note.textContent = uniqueCompanies.length + ' entities · Prices as of ' + ts + liveTag + ' · Source: EODHD · Updates daily';
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

  // Tracked count — use same number for both Universe and Live Data,
  // plus the "Tracks N frontier technology equities" count in the
  // Robotnik Index description widget. All three must match the
  // Frontier Assets "All (N)" pill, which is also uniqueCompanies.length.
  var countEl = document.getElementById('ov-count');
  if (countEl) countEl.textContent = String(uniqueCompanies.length);
  var univEl = document.getElementById('ov-universe');
  if (univEl) univEl.textContent = String(uniqueCompanies.length);
  var explCountEl = document.getElementById('explainer-count');
  if (explCountEl) explCountEl.textContent = String(uniqueCompanies.length);

  // Find top gainer, top loser, largest
  var largest = uniqueCompanies[0]; // already sorted by mcap
  var gainer = uniqueCompanies[0], loser = uniqueCompanies[0];
  var avgChg = 0, chgCount = 0;
  for (var j = 0; j < uniqueCompanies.length; j++) {
    var c = uniqueCompanies[j];
    if (c.change !== undefined && c.change !== null && !isNaN(c.change)) {
      avgChg += c.change;
      chgCount++;
      if (c.change > (gainer.change || 0)) gainer = c;
      if (c.change < (loser.change || 0)) loser = c;
    }
  }
  avgChg = chgCount ? avgChg / chgCount : 0;

  var chgEl = document.getElementById('ov-24h');
  if (chgEl) {
    if (isNaN(avgChg)) avgChg = 0;
    chgEl.textContent = (avgChg >= 0 ? '+' : '') + avgChg.toFixed(2) + '%';
    chgEl.className = 'overview-val ' + (avgChg >= 0 ? 'v-green' : 'v-red');
  }

  var largestEl = document.getElementById('ov-largest');
  if (largestEl && largest) {
    var lCls = largest.change >= 0 ? 'v-green' : 'v-red';
    var lSign = largest.change >= 0 ? '+' : '';
    largestEl.innerHTML = '<a href="assets.html" style="color:inherit;text-decoration:none;">' + largest.ticker + '</a> <span class="' + lCls + '">' + lSign + largest.change.toFixed(2) + '%</span>';
  }

  // Display company name with ellipsis truncation — prevents tickers like
  // "012450 KS" from appearing visually clipped to "01245" in the narrow sidebar.
  var nameStyle = 'display:inline-block;max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;vertical-align:bottom;';
  var gainerEl = document.getElementById('ov-gainer');
  if (gainerEl && gainer) {
    gainerEl.innerHTML = '<a href="assets.html" style="color:inherit;text-decoration:none;' + nameStyle + '" title="' + gainer.name + ' (' + gainer.ticker + ')">' + gainer.name + '</a> <span class="v-green">+' + gainer.change.toFixed(2) + '%</span>';
  }

  var loserEl = document.getElementById('ov-loser');
  if (loserEl && loser) {
    loserEl.innerHTML = '<a href="assets.html" style="color:inherit;text-decoration:none;' + nameStyle + '" title="' + loser.name + ' (' + loser.ticker + ')">' + loser.name + '</a> <span class="v-red">' + loser.change.toFixed(2) + '%</span>';
  }

  // Last updated timestamp — reflect when the price data was fetched,
  // not when the page was rendered. Falls back to "—" if we couldn't
  // find a fetched_at in all_prices.json.
  var updatedEl = document.getElementById('ov-updated');
  if (updatedEl) {
    try {
      updatedEl.textContent = window._priceFetchedAt
        ? fmtDateRobotnik(window._priceFetchedAt)
        : '—';
    } catch(e) { updatedEl.textContent = '—'; }
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

// Robotnik Composite anchor: the index was rebased to 1,000 on the
// inception date below. Displayed as a horizontal dashed reference line
// across the chart. The in-chart text annotation has been removed —
// at mobile/narrow viewports "BASE 1,000 · 31 MAR 2025" pinned to the
// left edge read as a stray date label near the oldest x-axis tick.
// The base date is still surfaced in the side explainer widget
// ("Base: 1,000.00 on 2025-03-31"), so no information is lost.
const ROBOTNIK_INDEX_BASE = 1000;
const ROBOTNIK_INDEX_INCEPTION = '2025-03-31';

let _indexBasePriceLine = null;   // LightweightCharts IPriceLine
// _indexBaseLabelEl kept nulled for forward-compat with callers that
// still reference it but there is no longer an in-chart label.
let _indexBaseLabelEl   = null;

// Called from applyIndexData() after every setData() and again from
// any chart-event handler that changes layout. Keeps the baseline
// reference line in sync with the active series and chart mode.
function _updateBaselineReference() {
  if (!indexAreaSeries || !indexChart) return;

  const isComposite = currentIndexSeries === 'composite';
  const isPriceMode = currentChartMode !== 'pct';
  const shouldShow = isComposite && isPriceMode;

  // ── Dashed price line at y = 1,000 ──
  if (shouldShow) {
    if (!_indexBasePriceLine) {
      _indexBasePriceLine = indexAreaSeries.createPriceLine({
        price: ROBOTNIK_INDEX_BASE,
        color: 'rgba(90, 97, 120, 0.6)',   // --text-muted @ 60% opacity
        lineWidth: 1,
        lineStyle: LightweightCharts.LineStyle.Dashed,
        axisLabelVisible: false,
        title: '',
      });
    }
  } else if (_indexBasePriceLine) {
    indexAreaSeries.removePriceLine(_indexBasePriceLine);
    _indexBasePriceLine = null;
  }
}
let indexChartData = {};
let indexSubMeta = {};       // {key: {current_value, entity_count, ...}}
let currentIndexSeries = 'composite';
let currentIndexRange = 365;  // days, or 'ytd' — default 1Y
let currentChartMode = 'price';  // 'price' | 'pct'
let _intradayCache = null;   // cached intraday_index.json
let _indexCalculatedAt = null;  // timestamp of last daily index compute
let _intradayFetchedAt = null;  // timestamp of last intraday fetch
// Maps the sequential integer "time" we pass to Lightweight Charts back to
// the original ISO date (or "YYYY-MM-DD HH:MM:SS" for intraday). We re-
// index time because the library renders gaps proportional to calendar
// distance by default — so weekends and holidays in a daily series, or
// the Fri-20:00→Mon-13:30 gap in a 1W intraday series, show up as dead
// empty segments on the axis. Sequential integers collapse those gaps;
// the tick formatter and crosshair formatter read this map to display the
// real date/time without anyone on the reading side knowing.
let _chartTimeMap = [];
let _chartTimeIsIntraday = false;
let _chartTimeSpansMultipleYears = false;
// True when the visible intraday series spans more than one calendar
// date (1W). Drives tickMarkFormatter between "HH:MM throughout"
// (single-day 1D) and "DD Mon per tick" (multi-day).
let _chartTimeSpansMultipleDays = false;
let compareLines = [];       // [{ticker, series, color, isBenchmark}]
const COMPARE_COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EC4899', '#8B5CF6'];
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

  // Fetch summary.json in parallel to get the index-compute timestamp —
  // robotnik_index.json itself only carries `current_date`, which loses
  // the within-day precision we need to detect pipeline staleness.
  fetch('data/index/summary.json').then(function(r) {
    if (!r.ok) return null;
    return r.json();
  }).then(function(s) {
    if (s && s.calculated_at) {
      _indexCalculatedAt = s.calculated_at;
      renderFreshnessIndicator();
    }
  }).catch(function() {});

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

      // Update index widget (applyIndexData will set value+% for 1Y default).
      // The chart-base-label text is now set once at element creation
      // (the baseline-reference label pinned to y=1,000 on the chart); only
      // the sidebar explainer keeps the wordier "Base: 1,000.00 on …" form.
      if (data.base_date) {
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
                // Update dashboard card
                var card = document.querySelector('[data-sub="' + jsonKey + '"]');
                if (card && sub[jsonKey].current_value) {
                  var cv = sub[jsonKey].current_value;
                  var ec = sub[jsonKey].entity_count || 0;
                  var vel = card.querySelector('.sub-index-val');
                  if (vel) vel.textContent = cv.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2});
                  var seriesArr = sub[jsonKey].series || [];
                  // 24h change
                  var pc24 = 0;
                  if (seriesArr.length > 1) {
                    var prevV = seriesArr[seriesArr.length - 2].value;
                    var lastV = seriesArr[seriesArr.length - 1].value;
                    pc24 = prevV ? ((lastV - prevV) / prevV * 100) : 0;
                  }
                  // YTD change (find Jan 1 value)
                  var pcYtd = 0;
                  var ytdKey = new Date().getFullYear() + '-01';
                  for (var si = 0; si < seriesArr.length; si++) {
                    if (seriesArr[si].date && seriesArr[si].date.startsWith(ytdKey)) {
                      pcYtd = seriesArr[si].value ? ((cv - seriesArr[si].value) / seriesArr[si].value * 100) : 0;
                      break;
                    }
                  }
                  // Pick display change: 24h if non-zero, else 1W
                  var displayChg = pc24;
                  var displayLabel = '24h';
                  if (Math.abs(pc24) < 0.01 && seriesArr.length > 5) {
                    var wkV = seriesArr[Math.max(0, seriesArr.length - 6)].value;
                    displayChg = wkV ? ((cv - wkV) / wkV * 100) : 0;
                    displayLabel = '1W';
                  }
                  var ce = card.querySelector('.sub-index-chg');
                  if (ce) {
                    var cls24 = displayChg >= 0 ? 'v-green' : 'v-red';
                    var clsYtd = pcYtd >= 0 ? 'v-green' : 'v-red';
                    ce.innerHTML = '<span class="' + cls24 + '">' + (displayChg >= 0 ? '+' : '') + displayChg.toFixed(2) + '% (' + displayLabel + ')</span>' +
                      ' <span style="color:var(--text-muted);margin:0 2px;">|</span> ' +
                      '<span class="' + clsYtd + '">' + (pcYtd >= 0 ? '+' : '') + pcYtd.toFixed(1) + '% YTD</span>';
                  }
                  var meta = card.querySelector('.sub-index-meta');
                  if (meta) meta.textContent = ec + ' entities';
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
    layout: { background: { type: 'solid', color: 'transparent' }, textColor: '#8B92A5', fontFamily: "'Space Grotesk', sans-serif", fontSize: 10 },
    grid: { vertLines: { color: '#1E2330' }, horzLines: { color: '#1E2330' } },
    crosshair: { vertLine: { color: '#F5D921', width: 1, style: 2 }, horzLine: { color: '#F5D921', width: 1, style: 2 } },
    timeScale: {
      borderColor: '#1E2330',
      timeVisible: false,
      // Sequential-integer time values — see _chartTimeMap above. The
      // formatter turns them back into calendar dates or intraday
      // HH:MM labels at tick time.
      tickMarkFormatter: function(time) {
        // Lightweight Charts occasionally calls with a fractional index
        // at the visible-range edges. Clamp+floor before reverse-lookup
        // and explicitly drop anything outside the data array so we
        // never render a stray edge label (earlier this path could hit
        // Date.now fallbacks in some toolchains).
        if (typeof time !== 'number' || !isFinite(time)) return '';
        var idx = Math.floor(time);
        if (idx < 0 || idx >= _chartTimeMap.length) return '';
        var orig = _chartTimeMap[idx];
        if (orig === undefined || orig === null) return '';
        var months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
        if (_chartTimeIsIntraday) {
          var d = new Date(orig * 1000);
          var pad = function(n) { return n < 10 ? '0' + n : '' + n; };
          // Multi-day intraday (1W): every bar returns its date, so
          // whichever tick position Lightweight Charts picks produces
          // a "DD Mon" label. Adjacent ticks that collapse to the same
          // date are harmless — the library suppresses overlapping
          // labels automatically. Single-day intraday (1D): return
          // HH:MM throughout since the date is redundant and the axis
          // reads as a chronological session.
          if (_chartTimeSpansMultipleDays) {
            return d.getUTCDate() + ' ' + months[d.getUTCMonth()];
          }
          return pad(d.getUTCHours()) + ':' + pad(d.getUTCMinutes());
        }
        // Daily — "YYYY-MM-DD". On views that span multiple calendar
        // years (1Y, 3Y, 5Y), Lightweight Charts often picks idx=0 as
        // its first tick position. For a 1Y view, idx=0 is the bar
        // exactly one year ago, which happens to share today's day
        // and month — the label reads as today even though it's last
        // year. Suppress the idx=0 tick on those views so the
        // leftmost rendered label is a later, unambiguous bar. LC
        // picks enough other tick positions that the axis stays
        // readable. (Single- or short-range views are unaffected
        // because they don't roll the date boundary in a confusing
        // way.)
        if (idx === 0 && _chartTimeSpansMultipleYears) return '';
        var dd = new Date(orig + 'T00:00:00Z');
        if (isNaN(dd.getTime())) return orig;
        return dd.getUTCDate() + ' ' + months[dd.getUTCMonth()];
      },
    },
    localization: {
      timeFormatter: function(time) {
        if (typeof time !== 'number' || !isFinite(time)) return '';
        var idx = Math.floor(time);
        if (idx < 0 || idx >= _chartTimeMap.length) return '';
        var orig = _chartTimeMap[idx];
        if (orig === undefined || orig === null) return '';
        if (_chartTimeIsIntraday) {
          var d = new Date(orig * 1000);
          return d.toLocaleDateString('en-US', {month:'short',day:'numeric',year:'numeric'}) + ' ' +
                 d.toLocaleTimeString('en-US', {hour:'2-digit',minute:'2-digit',timeZoneName:'short'});
        }
        return orig;
      },
    },
    rightPriceScale: { borderColor: '#1E2330' },
    handleScroll: { mouseWheel: false, pressedMouseMove: false, horzTouchDrag: false, vertTouchDrag: false },
    handleScale: { mouseWheel: false, pinch: false, axisPressedMouseMove: false, axisDoubleClickReset: false },
  });
  indexAreaSeries = indexChart.addAreaSeries({
    lineColor: '#F5D921', topColor: 'rgba(245,217,33,0.10)', bottomColor: 'rgba(245,217,33,0.02)', lineWidth: 2,
  });

  container.style.position = container.style.position || 'relative';

  applyIndexData(data);
  const ro = new ResizeObserver(() => {
    indexChart.applyOptions({ width: container.clientWidth });
    _updateBaselineReference();
  });
  ro.observe(container);

  // Re-anchor the label whenever the visible range shifts (pan / zoom).
  indexChart.timeScale().subscribeVisibleLogicalRangeChange(_updateBaselineReference);

  // ── Crosshair tooltip ──
  var tooltip = document.createElement('div');
  tooltip.id = 'chart-tooltip';
  tooltip.style.cssText = 'display:none;position:absolute;z-index:10;background:rgba(22,25,32,0.95);border:1px solid #252A36;border-radius:4px;padding:6px 10px;font-family:var(--font);font-size:10px;color:#E6E8ED;pointer-events:none;white-space:nowrap;box-shadow:0 4px 12px rgba(0,0,0,0.4);';
  container.appendChild(tooltip);

  indexChart.subscribeCrosshairMove(function(param) {
    if (!param || !param.time || param.point === undefined || param.point.x < 0) {
      tooltip.style.display = 'none';
      return;
    }

    // Format time — param.time is a sequential index into
    // _chartTimeMap (see applyIndexData). The map holds either a unix
    // second count (intraday) or a "YYYY-MM-DD" date string (daily).
    var timeStr = '';
    var orig = (typeof param.time === 'number') ? _chartTimeMap[param.time] : param.time;
    if (typeof orig === 'number') {
      var ddn = new Date(orig * 1000);
      timeStr = ddn.toLocaleDateString('en-US', {month:'short',day:'numeric',year:'numeric'}) + ' ' +
                ddn.toLocaleTimeString('en-US', {hour:'2-digit',minute:'2-digit',timeZoneName:'short'});
    } else if (typeof orig === 'string') {
      var dd2 = new Date(orig + 'T00:00:00Z');
      timeStr = isNaN(dd2.getTime())
        ? orig
        : dd2.toLocaleDateString('en-US', {month:'short',day:'numeric',year:'numeric'});
    }

    var html = '<div style="color:var(--text-dim);margin-bottom:3px;">' + timeStr + '</div>';

    // Index (area) series value
    var indexVal = param.seriesData.get(indexAreaSeries);
    if (indexVal && indexVal.value !== undefined) {
      var suffix = currentChartMode === 'pct' ? '%' : '';
      var prefix = currentChartMode === 'pct' ? (indexVal.value >= 0 ? '+' : '') : '';
      html += '<div style="color:#F5D921;">● ' + (document.getElementById('chart-title')?.textContent || 'Composite') +
              '<span style="float:right;margin-left:12px;">' + prefix + indexVal.value.toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2}) + suffix + '</span></div>';
    }

    // Comparison lines
    for (var i = 0; i < compareLines.length; i++) {
      var cl = compareLines[i];
      if (!cl.lwcSeries) continue;
      var clVal = param.seriesData.get(cl.lwcSeries);
      if (clVal && clVal.value !== undefined) {
        var label = cl.name || cl.ticker;
        html += '<div style="color:' + cl.color + ';">● ' + label +
                '<span style="float:right;margin-left:12px;">' + clVal.value.toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2}) + '</span></div>';
      }
    }

    tooltip.innerHTML = html;
    tooltip.style.display = 'block';

    // Position tooltip near cursor but keep within bounds
    var x = param.point.x + 15;
    var y = param.point.y - 10;
    if (x + tooltip.offsetWidth > container.clientWidth) x = param.point.x - tooltip.offsetWidth - 15;
    if (y < 0) y = 10;
    if (y + tooltip.offsetHeight > container.clientHeight) y = container.clientHeight - tooltip.offsetHeight - 10;
    tooltip.style.left = x + 'px';
    tooltip.style.top = y + 'px';
  });
}

// Keep weekdays only. Tokens (CoinGecko) trade 24/7 and the index
// carries equity closes forward across Sat/Sun, producing flat dead
// segments on the chart. Stripping Sat/Sun lets the axis collapse to
// trading days only. Market holidays where all equities are closed
// are rare and sometimes still have a token-driven tick, so we don't
// try to detect them — the residual one-day flats they'd produce are
// within visual noise. Today is never pruned even if the value is
// provisional.
function pruneNonTradingDays(arr) {
  if (!arr || !arr.length) return arr || [];
  var todayKey = new Date().toISOString().slice(0, 10);
  return arr.filter(function(d) {
    var key = (d.time || d.date || '');
    if (!key || key === todayKey) return true;
    var dt = new Date(key);
    if (isNaN(dt.getTime())) return true;
    var dow = dt.getUTCDay();
    return dow !== 0 && dow !== 6;
  });
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
    // For the 1D sub-day range show a few trading days of daily data as
    // fallback (the real 1D view uses the intraday SOXX proxy).
    var days = currentIndexRange < 2 ? 3 : Math.ceil(currentIndexRange);
    cutoff.setDate(cutoff.getDate() - days);
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
  var chartData;

  // Build the re-indexed time map so the axis and crosshair can display
  // real calendar dates/times even though Lightweight Charts is given
  // sequential integer timestamps. This re-indexing is what collapses
  // weekends/holidays (daily) and the Fri-20:00→Mon-13:30 gap (intraday).
  //
  // Intraday data arrives from _filterIntraday() with `time` as a unix
  // second count (number). Daily data arrives with `time` / `date` as a
  // "YYYY-MM-DD" string. We key the map by the original value so the
  // tick/crosshair formatters can reverse-lookup the real date or
  // timestamp when rendering labels.
  var timeKey = function(d) { return d.time !== undefined ? d.time : d.date; };
  var first = filtered.length ? timeKey(filtered[0]) : '';
  _chartTimeIsIntraday = typeof first === 'number';
  if (!_chartTimeIsIntraday) {
    filtered = pruneNonTradingDays(filtered);
  }
  _chartTimeMap = filtered.map(function(d) { return timeKey(d); });

  // Detect whether the visible range spans multiple calendar years. On
  // a 1Y view the oldest bar is exactly 365 days old, so its day-of-
  // month matches today's — a label of just "22 Apr" at the leftmost
  // position reads as today even though it's last year. On year-
  // spanning views we suppress the leftmost tick (idx=0) so the
  // leftmost rendered label is a later, unambiguous bar.
  _chartTimeSpansMultipleYears = false;
  if (_chartTimeMap.length >= 2) {
    var firstVal = _chartTimeMap[0], lastVal = _chartTimeMap[_chartTimeMap.length - 1];
    var firstYear, lastYear;
    if (_chartTimeIsIntraday) {
      firstYear = new Date(firstVal * 1000).getUTCFullYear();
      lastYear = new Date(lastVal * 1000).getUTCFullYear();
    } else {
      firstYear = parseInt(firstVal.slice(0, 4), 10);
      lastYear = parseInt(lastVal.slice(0, 4), 10);
    }
    _chartTimeSpansMultipleYears = firstYear !== lastYear;
  }
  if (_chartTimeIsIntraday && _chartTimeMap.length > 1) {
    var firstDate = new Date(_chartTimeMap[0] * 1000);
    var lastDate = new Date(_chartTimeMap[_chartTimeMap.length - 1] * 1000);
    _chartTimeSpansMultipleDays =
      firstDate.getUTCDate() !== lastDate.getUTCDate() ||
      firstDate.getUTCMonth() !== lastDate.getUTCMonth() ||
      firstDate.getUTCFullYear() !== lastDate.getUTCFullYear();
  } else {
    _chartTimeSpansMultipleDays = false;
  }

  if (currentChartMode === 'pct') {
    // Rebase to 0% from start of visible range
    var baseVal = filtered[0].value || filtered[0].close || 1;
    chartData = filtered.map(function(d, i) {
      var v = d.value || d.close || 0;
      return { time: i, value: parseFloat(((v - baseVal) / baseVal * 100).toFixed(2)) };
    });
    // Update Y-axis format for percentage
    indexAreaSeries.applyOptions({ priceFormat: { type: 'custom', formatter: function(v) { return (v >= 0 ? '+' : '') + v.toFixed(1) + '%'; } } });
  } else {
    chartData = filtered.map(function(d, i) { return { time: i, value: d.value || d.close }; });
    indexAreaSeries.applyOptions({ priceFormat: { type: 'price', precision: 2, minMove: 0.01 } });
  }

  indexAreaSeries.setData(chartData);
  _updateBaselineReference();
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

function setChartMode(btn) {
  if (btn.classList.contains('disabled')) return;
  document.querySelectorAll('.chart-mode-tab').forEach(function(b) { b.classList.remove('active'); });
  btn.classList.add('active');
  currentChartMode = btn.dataset.mode;
  var data = indexChartData[currentIndexSeries];
  if (currentIndexSeries === 'composite' && currentIndexRange !== 'ytd' && currentIndexRange > 365 && indexChartData.composite_eq) {
    data = indexChartData.composite_eq;
  }
  if (data) applyIndexData(data);
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
    // 12H and 1D use intraday data (loaded on demand)
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

async function loadIntradayIndex() {
  if (_intradayCache) return _filterIntraday(_intradayCache);
  try {
    var resp = await fetch('data/prices/intraday_index.json?v=' + Date.now());
    if (!resp.ok) return null;
    _intradayCache = await resp.json();
    _intradayFetchedAt = _intradayCache.fetched_at || null;
    return _filterIntraday(_intradayCache);
  } catch(e) { return null; }
}

// Pick the right "last updated" timestamp for the currently selected
// range. 1D and 1W are driven by the intraday proxy; longer ranges are
// driven by the daily index compute. Exposed as a separate helper so
// setIndexRange and applyIndexData can both call it without duplication.
function renderFreshnessIndicator() {
  var el = document.getElementById('chart-last-updated');
  if (!el) return;
  var isIntraday = (currentIndexRange !== 'ytd' && currentIndexRange > 0 && currentIndexRange <= 7 && currentIndexSeries === 'composite');
  var iso = isIntraday ? _intradayFetchedAt : _indexCalculatedAt;
  if (!iso) { el.textContent = ''; return; }
  // Tolerate a legacy format where calculate_index.py concatenated an
  // extra 'Z' onto an already-offset-aware isoformat() string (yielding
  // "…+00:00Z"). new Date() refuses to parse that, so strip a trailing
  // Z when one is already preceded by a numeric offset.
  var normalised = iso.replace(/([+-]\d\d:?\d\d)Z$/, '$1');
  var d = new Date(normalised);
  if (isNaN(d.getTime())) { el.textContent = ''; return; }
  var ageHours = (Date.now() - d.getTime()) / 3600000;
  // 36h is generous: EOD data pulled weekday 22:00 UTC should never be
  // older than the most recent weekday + weekend carry. Anything older
  // signals a pipeline problem worth surfacing in the UI.
  var stale = ageHours > 36;
  var months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  var pad = function(n) { return n < 10 ? '0' + n : '' + n; };
  var label = 'Last updated: ' + d.getUTCDate() + ' ' + months[d.getUTCMonth()] + ' ' + d.getUTCFullYear()
            + ', ' + pad(d.getUTCHours()) + ':' + pad(d.getUTCMinutes()) + ' GMT';
  el.textContent = label;
  el.classList.toggle('stale', stale);
}

function _filterIntraday(data) {
  // Pick series based on range: 1D = 5min, 1W = 1h.
  var series = currentIndexRange <= 1 ? data.series_5m : data.series_1h;
  if (!series || !series.length) return null;

  // Anchor the window to the LATEST bar, not wall-clock `now`. If the
  // intraday feed stalls (EODHD publish delay, missed cron), anchoring
  // to `now` makes the filter return zero and silently fall back to an
  // arbitrary tail, producing a stale window that looks like today. By
  // anchoring to the latest bar we always show the correct recency
  // semantics relative to the data we actually have — and the separate
  // "Last updated" indicator surfaces the staleness to the reader.
  var lastBar = new Date(series[series.length - 1].datetime.replace(' ', 'T') + 'Z');
  var lastBarMs = lastBar.getTime();
  var cutoff;
  if (currentIndexRange <= 1) {
    // 1D => bars on the SAME calendar date as the latest bar. A fixed
    // hours-back window (e.g. 30h) crossed the date boundary, which
    // pushed the time-axis formatter into multi-day "DD Mon" mode
    // instead of intra-day "HH:MM". Filtering by calendar date keeps
    // the view to a single session and the formatter shows time of day.
    cutoff = Date.UTC(lastBar.getUTCFullYear(), lastBar.getUTCMonth(), lastBar.getUTCDate());
  } else {
    // 1W => 5 trading days (7 calendar days / 168h covers weekend gaps).
    cutoff = lastBarMs - 168 * 3600000;
  }

  var filtered = series.filter(function(pt) {
    return new Date(pt.datetime.replace(' ', 'T') + 'Z').getTime() >= cutoff;
  });

  // Defensive fallback: if the series is too sparse (e.g. a holiday-
  // shortened week), use a last-N-bars cap instead of returning nothing.
  if (filtered.length < 3) {
    var n = currentIndexRange <= 1 ? 78 : series.length;
    filtered = series.slice(-n);
  }

  // Convert to Lightweight Charts format (unix timestamp in seconds)
  return filtered.map(function(pt) {
    var d = new Date(pt.datetime.replace(' ', 'T') + 'Z');
    return {
      time: Math.floor(d.getTime() / 1000),
      value: pt.value,
    };
  });
}

function setIndexRange(btn) {
  document.querySelectorAll('.chart-range-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  var rv = btn.dataset.range;
  currentIndexRange = (rv === 'ytd') ? 'ytd' : (parseFloat(rv) || 0);
  renderFreshnessIndicator();

  // For 1D and 1W: load intraday data (SOXX proxy)
  if (currentIndexRange <= 7 && currentIndexRange > 0 && currentIndexSeries === 'composite') {
    loadIntradayIndex().then(function(intradayData) {
      if (intradayData) {
        applyIndexData(intradayData);
      } else {
        // Fall back to daily data
        var data = indexChartData[currentIndexSeries];
        if (data) applyIndexData(data);
      }
      renderFreshnessIndicator();
    });
    // Also re-render market table for range-synced %
    renderMarketTable();
    return;
  }

  var data = indexChartData[currentIndexSeries];
  // For composite with long ranges, use equities-only if available
  if (currentIndexSeries === 'composite' && currentIndexRange !== 'ytd' && currentIndexRange > 365 && indexChartData.composite_eq) {
    data = indexChartData.composite_eq;
  }
  if (data) applyIndexData(data);
  // Re-render market table for range-synced %
  renderMarketTable();
}

function setIndexSeries(btn) {
  document.querySelectorAll('.chart-index-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  currentIndexSeries = btn.dataset.idx;
  var data = indexChartData[currentIndexSeries];
  renderFreshnessIndicator();
  // Update title
  var titleEl = document.getElementById('chart-title');
  var labels = { composite:'Robotnik Index', semi:'Semi Index', robotics:'Robotics Index', space:'Space Index', materials:'Materials Index' };
  if (titleEl) titleEl.textContent = labels[currentIndexSeries] || 'Robotnik Index';

  // Sub-indices only have ~1Y of data; disable 3Y/5Y for non-composite
  var isSubIndex = currentIndexSeries !== 'composite';
  document.querySelectorAll('.chart-range-btn').forEach(function(rb) {
    var rv = parseFloat(rb.dataset.range);
    if (isSubIndex && rv > 365) {
      rb.classList.add('disabled');
      rb.title = 'Sub-index data available for 1Y only';
      rb.onclick = null;
    } else if (rv > 0) {
      rb.classList.remove('disabled');
      rb.removeAttribute('title');
      rb.onclick = function() { setIndexRange(this); };
    }
  });
  // If current range is >1Y and we switched to sub-index, snap to 1Y
  if (isSubIndex && typeof currentIndexRange === 'number' && currentIndexRange > 365) {
    currentIndexRange = 365;
    document.querySelectorAll('.chart-range-btn').forEach(function(rb) {
      rb.classList.remove('active');
      if (rb.dataset.range === '365') rb.classList.add('active');
    });
  }

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
  if (compareLines.length >= 5) return;
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

var BENCHMARK_BASE_DATE = '2025-03-31';
var BENCHMARK_BASE_VALUE = 1000;

function _rebaseBenchmark(rawSeries) {
  // Find the base price on 2025-03-31 (or nearest prior date)
  var basePrice = null;
  var baseCandidates = ['2025-03-31', '2025-03-28', '2025-03-27', '2025-03-26'];
  for (var i = 0; i < baseCandidates.length; i++) {
    for (var j = 0; j < rawSeries.length; j++) {
      if (rawSeries[j].date === baseCandidates[i]) {
        basePrice = rawSeries[j].close;
        break;
      }
    }
    if (basePrice) break;
  }
  if (!basePrice) {
    // Fallback: find closest date <= 2025-03-31
    for (var k = rawSeries.length - 1; k >= 0; k--) {
      if (rawSeries[k].date <= '2025-03-31') {
        basePrice = rawSeries[k].close;
        break;
      }
    }
  }
  if (!basePrice || basePrice <= 0) return rawSeries; // can't rebase

  // Rebase: value = (price / basePrice) * 1000
  return rawSeries.map(function(d) {
    return { date: d.date, close: (d.close / basePrice) * BENCHMARK_BASE_VALUE };
  });
}

function addBenchmark(ticker) {
  if (compareLines.length >= 5) return;
  if (compareLines.find(function(c) { return c.ticker === ticker; })) {
    removeCompare(ticker);
    return;
  }
  var meta = BENCHMARK_META[ticker];
  if (!meta) return;
  var color = meta.color;

  function doAdd(rawSeries) {
    if (!rawSeries || !rawSeries.length) return;
    if (!indexChart) return;
    // Rebase to 1,000 on 2025-03-31 to match Robotnik Composite base
    var rebasedSeries = _rebaseBenchmark(rawSeries);
    var lineSeries = indexChart.addLineSeries({ color: color, lineWidth: 2, lastValueVisible: true, priceLineVisible: false });
    compareLines.push({ ticker: ticker, series: rebasedSeries, color: color, lwcSeries: lineSeries, isBenchmark: true, name: meta.name });
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
  // Get current index data to determine visible date range
  var idxData = indexChartData[currentIndexSeries] || [];
  var filtered = getFilteredData(idxData);

  // Build a lookup from original date -> integer index used by the main
  // chart. Compare lines must share this index so they overlay correctly
  // on the re-indexed (non-trading-day-compressed) time axis.
  var timeIndex = {};
  for (var j = 0; j < _chartTimeMap.length; j++) timeIndex[_chartTimeMap[j]] = j;

  for (var i = 0; i < compareLines.length; i++) {
    var cl = compareLines[i];
    var compAll = cl.series.map(function(d) { return { time: d.date, value: d.close || d.price || d.value }; });
    var compFiltered = getFilteredData(compAll);
    var finalData;

    if (currentChartMode === 'pct') {
      // In % mode, every line (index + benchmarks + asset compares) is rebased
      // to 0% at the left edge of the visible timeframe so the Y-axis is a
      // common percentage scale. Pre-rebasing of benchmarks to 1,000 on
      // 2025-03-31 is irrelevant here — percentage change is scale-invariant.
      if (compFiltered.length > 0) {
        var pctBase = compFiltered[0].value || 1;
        finalData = compFiltered.map(function(d) {
          return { time: timeIndex[d.time], value: parseFloat(((d.value - pctBase) / pctBase * 100).toFixed(2)) };
        }).filter(function(d) { return d.time !== undefined; });
      } else {
        finalData = [];
      }
    } else if (cl.isBenchmark) {
      // Price mode: benchmarks are already rebased to 1,000 on 2025-03-31
      // (same scale as Robotnik Composite), plot raw values directly.
      finalData = compFiltered
        .map(function(d) { return { time: timeIndex[d.time], value: d.value }; })
        .filter(function(d) { return d.time !== undefined; });
    } else {
      // Price mode, regular asset comparison: scale to index start value
      // so both lines begin at the same visible point.
      if (compFiltered.length > 0 && filtered.length > 0) {
        var idxBase = filtered[0].value || filtered[0].close || 1;
        var compBase = compFiltered[0].value || 1;
        finalData = compFiltered.map(function(d) {
          return { time: timeIndex[d.time], value: idxBase * (d.value / compBase) };
        }).filter(function(d) { return d.time !== undefined; });
      } else {
        finalData = [];
      }
    }
    cl.lwcSeries.setData(finalData);
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

// Get the matching change field for the current chart range
function _rangeChangeField() {
  var m = { 0.5:'change_24h_pct', 1:'change_24h_pct', 7:'change_7d_pct', 30:'change_30d_pct',
            90:'change_3m_pct', 365:'change_1y_pct', 1095:'change_3y_pct', 1825:'change_5y_pct' };
  if (currentIndexRange === 'ytd') return 'change_ytd_pct';
  return m[currentIndexRange] || 'change_24h_pct';
}

function _rangeChangeLabel() {
  var m = { 0.5:'24h', 1:'24h', 7:'7D', 30:'1M', 90:'3M', 365:'1Y', 1095:'3Y', 1825:'5Y' };
  if (currentIndexRange === 'ytd') return 'YTD';
  return m[currentIndexRange] || '24h';
}

// Sparkline SVG from data array
function _sparkSvg(arr) {
  if (!arr || arr.length < 2) return '';
  var mn = Math.min.apply(null, arr), mx = Math.max.apply(null, arr);
  if (mx === mn) mx += 1;
  var pts = arr.map(function(v, i) { return (i / (arr.length - 1) * 50).toFixed(1) + ',' + (18 - (v - mn) / (mx - mn) * 16).toFixed(1); }).join(' ');
  var col = arr[arr.length - 1] >= arr[0] ? '%2322c55e' : '%23ef4444';
  return '<svg width="50" height="18" viewBox="0 0 50 18"><polyline fill="none" stroke="' + col + '" stroke-width="1.2" points="' + pts + '"/></svg>';
}

// Highlight compare line on hover
function _highlightComp(ticker) {
  var cl = compareLines.find(function(c) { return c.ticker === ticker; });
  if (cl && cl.lwcSeries) cl.lwcSeries.applyOptions({ lineWidth: 4 });
}
function _unhighlightComp(ticker) {
  var cl = compareLines.find(function(c) { return c.ticker === ticker; });
  if (cl && cl.lwcSeries) cl.lwcSeries.applyOptions({ lineWidth: 2 });
}

function renderMarketTable() {
  var tbody = document.getElementById('mkt-tbody');
  if (!tbody || !uniqueCompanies.length) return;
  var search = (document.getElementById('mkt-search')?.value || '').toLowerCase();
  var data = mktSector === 'all' ? uniqueCompanies : uniqueCompanies.filter(function(c) { return c.sector === mktSector; });
  if (search) data = data.filter(function(c) { return c.ticker.toLowerCase().includes(search) || c.name.toLowerCase().includes(search); });

  // Sort
  var chgField = _rangeChangeField();
  var sorted = data.slice().sort(function(a, b) {
    var va, vb;
    if (mktSort === 'ticker') { va = a.ticker; vb = b.ticker; return va < vb ? -mktSortDir : va > vb ? mktSortDir : 0; }
    if (mktSort === 'company') { va = a.name; vb = b.name; return va < vb ? -mktSortDir : va > vb ? mktSortDir : 0; }
    if (mktSort === 'sector') { va = a.sector; vb = b.sector; return va < vb ? -mktSortDir : va > vb ? mktSortDir : 0; }
    if (mktSort === 'price') { return (a.price - b.price) * mktSortDir; }
    if (mktSort === 'change') {
      var ma = window.metricsData[a.ticker], mb = window.metricsData[b.ticker];
      va = ma ? (ma[chgField] || 0) : (a.change || 0);
      vb = mb ? (mb[chgField] || 0) : (b.change || 0);
      return (va - vb) * mktSortDir;
    }
    return ((a.mcap || 0) - (b.mcap || 0)) * mktSortDir;
  });

  var top10 = search ? sorted : sorted.slice(0, 10);
  var rows = top10.map(function(c, i) {
    var md = window.metricsData[c.ticker] || {};
    var chgVal = md[chgField] !== undefined && md[chgField] !== null ? md[chgField] : c.change;
    var chgCls = chgVal >= 0 ? 'v-green' : 'v-red';
    var chgSign = chgVal >= 0 ? '+' : '';
    var chgStr = chgVal !== null && chgVal !== undefined ? chgSign + chgVal.toFixed(2) + '%' : '—';
    var secCss = SECTOR_CSS[c.sector] || 'sector-semi';
    var secLabel = SECTOR_LABELS[c.sector] || c.sector;
    var spark = _sparkSvg(md.sparkline_30d);
    var isCompared = compareLines.some(function(cl) { return cl.ticker === c.ticker; });
    var rowStyle = isCompared ? 'border-left:3px solid var(--yellow);' : '';
    var esc = c.ticker.replace(/'/g, "\\'");
    return '<tr style="cursor:pointer;' + rowStyle + '" onclick="addCompare(\'' + esc + '\')" ' +
      'onmouseenter="_highlightComp(\'' + esc + '\')" onmouseleave="_unhighlightComp(\'' + esc + '\')">' +
      '<td>' + (i+1) + '</td><td class="ticker">' + c.ticker + '</td><td class="company-name">' + c.name +
      '</td><td><span class="sector-tag ' + secCss + '">' + secLabel + '</span></td><td class="r">' + fmtPrice(c.price, c.currency) +
      '</td><td style="text-align:center">' + spark + '</td>' +
      '<td class="r ' + chgCls + '">' + chgStr + '</td><td class="r">' + c.mcapFmt + '</td></tr>';
  }).join('');
  tbody.innerHTML = rows;

  // Update change column header
  var chgHeader = document.getElementById('sort-arrow-change');
  if (chgHeader && chgHeader.parentElement) {
    chgHeader.parentElement.childNodes[0].textContent = _rangeChangeLabel() + ' ';
  }

  // Update sort arrows
  ['#','ticker','company','sector','price','change','mcap'].forEach(function(col) {
    var el = document.getElementById('sort-arrow-' + col);
    if (el) el.textContent = mktSort === col ? (mktSortDir === -1 ? '▼' : '▲') : '';
  });

  // Update tab counts — per-sector counts must match the Robotnik Index's
  // eligibility criteria (same authoritative source used by the sector cards).
  // "All" stays at the raw tracked-entity count because sub-$10M equities
  // are still displayed in the table, just not in the index.
  var tabs = document.querySelectorAll('.market-tab');
  var counts = {all: uniqueCompanies.length, semi:0, robo:0, space:0, materials:0};
  if (window.indexWeightSectors) {
    counts.semi = window.indexWeightSectors.semi || 0;
    counts.robo = window.indexWeightSectors.robo || 0;
    counts.space = window.indexWeightSectors.space || 0;
    counts.materials = window.indexWeightSectors.materials || 0;
  } else {
    uniqueCompanies.forEach(function(c) { if (counts[c.sector] !== undefined) counts[c.sector]++; });
  }
  tabs.forEach(function(t) {
    var s = t.dataset.sector;
    var label = s === 'all' ? 'All' : s === 'semi' ? 'Semi' : s === 'robo' ? 'Robotics' : s === 'space' ? 'Space' : s === 'materials' ? 'Materials' : s;
    t.textContent = label + ' (' + (counts[s] || 0) + ')';
  });

  // Update view all link
  var viewAll = document.getElementById('mkt-view-all');
  if (viewAll) viewAll.textContent = 'View all ' + data.length + ' assets →';
}

// ===== EXPORT MODAL =====
// Intermediate export-gate modal was removed in v1.1.3 polish; the Export
// button on the home page now routes directly to openEarlyAccess(). These
// stubs are retained for any legacy onclick handlers and become no-ops if
// the modal div is absent.
function showExportModal() {
  if(typeof openEarlyAccess==='function')openEarlyAccess();
}
function closeExportModal() {
  var m=document.getElementById('export-modal');
  if(m)m.style.display='none';
}

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
