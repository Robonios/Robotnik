/* ============================================================
   ROBOTNIK — HOME PAGE controller
   Reads data/home.json (the single source) and renders every
   section: top-strip ticker, hero proof, the Frontier Stack graph,
   index family, sector cards, signals, product, reference library,
   and the research rail (incl. research → graph cell-highlight).
   Nothing here is hardcoded data — swap home.json to go live.
   No browser storage is used.
   ============================================================ */
(function () {
  'use strict';

  var CRIT_COLOR = { low: '#4DA98B', medium: '#E0A33C', high: '#E0703D', critical: '#DC4A4A' };
  var SPARK_COLOR = { composite: '#F5D921', bottleneck: '#E0A33C', public: '#5B8DEF', private: '#A98BEA' };

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function num(v, dec) {
    if (v == null) return '—';
    return Number(v).toLocaleString(undefined, { minimumFractionDigits: dec, maximumFractionDigits: dec });
  }
  function $(id) { return document.getElementById(id); }
  function spark(series, color) {
    return (window.FrontierStack && FrontierStack.sparkline) ? FrontierStack.sparkline(series, color, 120, 34) : '';
  }
  function openAccess(e) { if (e) e.preventDefault(); if (typeof window.openEarlyAccess === 'function') window.openEarlyAccess(); }

  // ---------------------------------------------------------- TOP STRIP
  function renderTopStrip(d) {
    var bar = document.querySelector('.top-bar');
    if (!bar || document.querySelector('.top-strip-extra')) return;
    var c = d.indexes && d.indexes.composite;
    var wrap = document.createElement('div');
    wrap.className = 'top-strip-extra';
    var ticker = '';
    if (c) {
      var up = (c.change1y || 0) >= 0;
      ticker =
        '<a class="top-rci" href="' + esc(c.chartUrl || '#') + '" style="text-decoration:none">' +
          '<span class="top-rci-label">RCI</span>' +
          '<span class="top-rci-val">' + num(c.value, 2) + '</span>' +
          (c.change1y != null ? '<span class="top-rci-chg ' + (up ? 'up' : 'down') + '">' + (up ? '+' : '') + c.change1y.toFixed(2) + '%</span>' : '') +
        '</a>';
    }
    wrap.innerHTML = ticker + '<button class="btn-access" type="button">Request access</button>';
    bar.appendChild(wrap);
    wrap.querySelector('.btn-access').addEventListener('click', openAccess);
  }

  // ---------------------------------------------------------- HERO PROOF
  function renderHeroProof(d) {
    var host = $('hero-proof');
    if (!host) return;
    var c = d.indexes && d.indexes.composite;
    var m = d.meta || {};
    if (!c) { host.innerHTML = '<div class="proof-empty">Composite awaiting calibration.</div>'; return; }
    var up = (c.change1y || 0) >= 0;
    host.innerHTML =
      '<div class="proof-main">' +
        '<span class="proof-name">' + esc(c.name) + '</span>' +
        '<span class="proof-value">' + num(c.value, 2) + '</span>' +
        (c.change1y != null ? '<span class="proof-change ' + (up ? 'up' : 'down') + '">' + (up ? '+' : '') + c.change1y.toFixed(2) + '% · 1Y</span>' : '') +
      '</div>' +
      '<div class="proof-divider"></div>' +
      '<div class="proof-meta">' +
        '<span class="proof-meta-row">Base <b>' + num(m.base, 2) + '</b> on <b>' + esc(m.baseDate) + '</b></span>' +
        '<span class="proof-meta-row">Universe <b>' + esc(m.universe) + '</b> entities · market-cap weighted</span>' +
        '<a href="' + esc(c.methodologyUrl || '#') + '">Methodology &rarr;</a>' +
      '</div>';
  }

  // ---------------------------------------------------------- INDEX FAMILY
  function indexTile(key, ix) {
    if (!ix) return '';
    if (ix.status === 'soon') {
      return '<div class="index-tile is-soon">' +
        '<div class="index-tile-top"><span class="index-tile-name">' + esc(ix.name) + '</span>' +
          '<span class="index-tag soon">Soon</span></div>' +
        '<div class="index-tile-val">—</div>' +
        '<div class="index-tile-blurb">' + esc(ix.blurb || '') + '</div>' +
        '<div class="index-tile-links"><a href="' + esc(ix.methodologyUrl || '#') + '">Methodology &rarr;</a></div>' +
        '</div>';
    }
    // Calibrating: a real index whose value is not yet published (placeholder
    // collision guard — don't print a number that duplicates the flagship).
    if (ix.calibrating) {
      return '<div class="index-tile is-calibrating">' +
        '<div class="index-tile-top"><span class="index-tile-name">' + esc(ix.name) + '</span>' +
          '<span class="index-tag calibrating">Calibrating</span></div>' +
        '<div class="index-tile-val pending">&mdash; calibrating</div>' +
        '<div class="index-tile-chg muted">Value pending · 1Y —</div>' +
        '<div class="index-tile-blurb">' + esc(ix.blurb || '') + '</div>' +
        '<div class="index-tile-links">' +
          '<a href="' + esc(ix.chartUrl || '#') + '">Detailed chart &rarr;</a>' +
          '<a href="' + esc(ix.methodologyUrl || '#') + '">Methodology &rarr;</a>' +
        '</div></div>';
    }
    var tag = ix.flagship ? '<span class="index-tag flagship">Flagship</span>'
            : ix.cadence ? '<span class="index-tag cadence">' + esc(ix.cadence) + '</span>' : '';
    var chg;
    if (ix.change1y != null) {
      var up = ix.change1y >= 0;
      chg = '<div class="index-tile-chg ' + (up ? 'up' : 'down') + '">' + (up ? '+' : '') + ix.change1y.toFixed(2) + '% · 1Y</div>';
    } else {
      chg = '<div class="index-tile-chg muted">' + (ix.cadence ? esc(ix.cadence) + ' mark' : '1Y —') + '</div>';
    }
    return '<div class="index-tile' + (ix.flagship ? ' is-flagship' : '') + '">' +
      '<div class="index-tile-top"><span class="index-tile-name">' + esc(ix.name) + '</span>' + tag + '</div>' +
      '<div class="index-tile-val">' + num(ix.value, 2) + '</div>' + chg +
      '<div class="index-tile-blurb">' + esc(ix.blurb || '') + '</div>' +
      '<div class="index-spark">' + spark(ix.series, SPARK_COLOR[key] || '#F5D921') + '</div>' +
      '<div class="index-tile-links">' +
        '<a href="' + esc(ix.chartUrl || '#') + '">Detailed chart &rarr;</a>' +
        '<a href="' + esc(ix.methodologyUrl || '#') + '">Methodology &rarr;</a>' +
      '</div></div>';
  }

  function renderIndexFamily(d) {
    var host = $('index-family');
    if (!host) return;
    var ix = d.indexes || {};
    var order = ['composite', 'bottleneck', 'public', 'commodities', 'private'];
    var html = order.map(function (k) { return indexTile(k, ix[k]); }).join('');
    // product tile
    var p = d.product;
    if (p) {
      html += '<div class="product-tile">' +
        '<div class="index-tile-top"><span class="index-tile-name">' + esc(p.name) + '</span>' +
          '<span class="index-tag cadence">Product</span></div>' +
        '<div class="product-mini"><img class="product-mini-bot" src="robotlogo.png" alt=""></div>' +
        '<a class="product-tile-link" href="' + esc(p.url || '#') + '">Product showcase &rarr;</a>' +
        '</div>';
    }
    host.innerHTML = html;
  }

  // ---------------------------------------------------------- SECTOR CARDS
  function renderSectors(d) {
    var host = $('sector-cards');
    if (!host) return;
    host.innerHTML = (d.sectors || []).map(function (s) {
      var ix = s.index || {};
      var d24 = ix.change24h, ytd = ix.changeYTD;
      var count = (s.public || 0) + (s.private || 0) + (s.commodities || 0);
      var rank = s.tierLabel ? s.tierLabel : '';
      var commodities = s.commodities ? (' · ' + s.commodities + ' commodities') : '';
      return '<div class="sector-card" style="--hue:' + s.hue + '">' +
        '<div class="sector-card-top"><span class="sector-swatch"></span>' +
          '<span class="sector-name">' + esc(s.name) + '</span>' +
          (rank ? '<span class="sector-rank">' + esc(rank) + '</span>' : '') + '</div>' +
        '<div class="sector-val">' + num(ix.value, 2) + '</div>' +
        '<div class="sector-changes">' +
          '<div class="sector-chg-block"><span class="sector-chg-label">24h</span>' +
            '<span class="sector-chg-val ' + (d24 >= 0 ? 'up' : 'down') + '">' + (d24 >= 0 ? '+' : '') + (d24 != null ? d24.toFixed(2) : '—') + '%</span></div>' +
          '<div class="sector-chg-block"><span class="sector-chg-label">YTD</span>' +
            '<span class="sector-chg-val ' + (ytd >= 0 ? 'up' : 'down') + '">' + (ytd >= 0 ? '+' : '') + (ytd != null ? ytd.toFixed(1) : '—') + '%</span></div>' +
        '</div>' +
        '<div class="sector-count"><b>' + s.public + '</b> public · <b>' + s.private + '</b> private' + commodities + '</div>' +
        '</div>';
    }).join('');
  }

  // ---------------------------------------------------------- SIGNALS
  function renderSignals(d) {
    var host = $('signals-block');
    if (!host) return;
    var s = d.signals || {};
    host.className = 'signals-block';
    host.innerHTML =
      '<div class="signals-copy">' +
        '<span class="signals-badge">● Coming soon</span>' +
        '<h3 class="signals-headline">' + esc(s.name || 'Frontier Signals') + ' — a single read on the backdrop</h3>' +
        '<p class="signals-blurb">' + esc(s.blurb || '') + '</p>' +
        '<p class="signals-note">' + esc(s.note || '') + '</p>' +
      '</div>' +
      '<div class="signals-gauge" aria-hidden="true">' +
        '<div class="gauge-scale"><span>−100</span><span>0</span><span>+100</span></div>' +
        '<div class="gauge-track"><span class="gauge-needle"></span></div>' +
        '<div class="gauge-readout">Calibrating…</div>' +
      '</div>';
  }

  // ---------------------------------------------------------- PRODUCT
  function renderProduct(d) {
    var host = $('product-block');
    if (!host) return;
    var p = d.product || {};
    var demo = p.demo || {};
    var critColor = CRIT_COLOR[demo.criticality] || '#888';
    host.innerHTML =
      '<div class="product-copy">' +
        '<p class="product-copy-tagline">' + esc(p.tagline || 'The ledger, wherever you read.') + '</p>' +
        '<p class="product-copy-blurb">' + esc(p.blurb || '') + '</p>' +
        '<div class="product-meta-row">' +
          '<span class="product-pill">' + esc((p.kind || '').replace('-', ' ')) + '</span>' +
          '<span class="product-pill muted">' + esc((p.status || '').toUpperCase()) + '</span>' +
          '<span class="product-pill muted">Retail roadmap</span>' +
        '</div>' +
        '<a class="product-link" href="' + esc(p.url || '#') + '">Product showcase &rarr;</a>' +
      '</div>' +
      '<div class="product-demo"><div class="popover">' +
        '<div class="popover-bar"><span class="popover-dot r"></span><span class="popover-dot y"></span><span class="popover-dot g"></span>' +
          '<span class="popover-url">research.note/frontier-read</span>' +
          '<img class="popover-bot" src="robotlogo.png" alt=""></div>' +
        '<div class="popover-body">' +
          '<div class="popover-detected">● Asset detected</div>' +
          '<div class="popover-asset"><span class="popover-asset-name">' + esc(demo.asset || '') + '</span>' +
            '<span class="popover-asset-ticker">' + esc(demo.ticker || '') + '</span></div>' +
          '<div class="popover-row"><span class="k">Sector</span><span class="v">' + esc(demo.sector || '') + '</span></div>' +
          '<div class="popover-row"><span class="k">Tier</span><span class="v">' + esc(demo.tier || '') + '</span></div>' +
          '<div class="popover-row"><span class="k">Bottleneck</span><span class="v popover-crit">' +
            '<span class="popover-crit-dot" style="background:' + critColor + '"></span>' + esc(demo.criticality || '') + '</span></div>' +
          '<div class="popover-line">' + esc(demo.line || '') + '</div>' +
          '<a class="popover-cta" href="' + esc(p.url || '#') + '">→ full ledger</a>' +
        '</div>' +
      '</div></div>';
  }

  // ---------------------------------------------------------- REFERENCE LIBRARY
  function renderReferences(d) {
    var host = $('reference-library');
    if (!host) return;
    host.innerHTML = (d.references || []).map(function (r) {
      return '<a class="ref-card" href="' + esc(r.url || '#') + '">' +
        '<span class="ref-kind">' + esc(r.kind) + '</span>' +
        '<span class="ref-name">' + esc(r.name) + '</span>' +
        '<span class="ref-blurb">' + esc(r.blurb || '') + '</span>' +
        '<span class="ref-arrow">Open &rarr;</span>' +
        '</a>';
    }).join('');
  }

  // ---------------------------------------------------------- RESEARCH RAIL
  function renderRail(d, graph) {
    var host = $('rail-list');
    if (!host) return;
    var arts = d.articles || [];
    host.innerHTML = arts.map(function (a, i) {
      var cells = (a.cells || []).map(function (c) {
        return '<span class="rail-cell-chip">' + esc(c[0]) + ' · T' + esc(c[1]) + '</span>';
      }).join('');
      return '<div class="rail-tile" data-idx="' + i + '">' +
        '<button class="rail-tile-btn" type="button" aria-expanded="false">' +
          '<span>' + esc(a.title) + '</span><span class="rail-tile-chev">&rsaquo;</span></button>' +
        '<div class="rail-tile-body"><div class="rail-tile-body-inner">' +
          '<p class="rail-tile-summary">' + esc(a.summary) + '</p>' +
          '<div class="rail-tile-cells">' + cells + '</div>' +
          '<a class="rail-tile-link" href="' + esc(a.url || '#') + '">Read full article &rarr;</a>' +
        '</div></div>' +
        '</div>';
    }).join('');

    var tiles = host.querySelectorAll('.rail-tile');
    tiles.forEach(function (tile) {
      var btn = tile.querySelector('.rail-tile-btn');
      btn.addEventListener('click', function () {
        var isOpen = tile.classList.contains('is-open');
        // accordion — one open at a time
        tiles.forEach(function (t) {
          t.classList.remove('is-open');
          t.querySelector('.rail-tile-btn').setAttribute('aria-expanded', 'false');
        });
        if (isOpen) {
          if (graph) graph.clearHighlight();
        } else {
          tile.classList.add('is-open');
          btn.setAttribute('aria-expanded', 'true');
          var art = arts[+tile.dataset.idx];
          if (graph && art) graph.highlight(art.cells);
        }
      });
    });
  }

  // ---------------------------------------------------------- BOOT
  function boot(d) {
    renderTopStrip(d);
    renderHeroProof(d);
    renderIndexFamily(d);
    renderSectors(d);
    renderReferences(d);

    var graph = null;
    var mount = $('frontier-stack');
    if (mount && window.FrontierStack) {
      graph = new FrontierStack(mount, d, { mode: 'stack', toggleEl: $('fs-mode-toggle') });
      // Integration handle: lets other scripts/console drive the graph
      // (e.g. graph.highlight(cells), graph.setPropagationGranularity('asset')).
      window.frontierStack = graph;
    }
    renderRail(d, graph);

    var fa = $('footnote-access');
    if (fa) fa.addEventListener('click', openAccess);
  }

  function fail(msg) {
    var hp = $('hero-proof');
    if (hp) hp.innerHTML = '<div class="proof-empty">' + esc(msg) + '</div>';
    var rl = $('rail-list');
    if (rl) rl.innerHTML = '<div class="rail-skeleton">Research unavailable.</div>';
  }

  function start() {
    fetch('data/home.json?v=' + Date.now())
      .then(function (r) { if (!r.ok) throw new Error('home.json ' + r.status); return r.json(); })
      .then(boot)
      .catch(function (e) { fail('Data feed offline — calibrating, tovarishch.'); if (window.console) console.warn('[home]', e); });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
