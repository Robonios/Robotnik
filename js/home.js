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
  // Detailed-chart + Methodology links all point at one placeholder for now.
  var PLACEHOLDER_URL = '#';

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
    return (window.FrontierStack && FrontierStack.sparkline) ? FrontierStack.sparkline(series, color, 120, 44) : '';
  }
  // ---- index_summary.json read helpers. Every number the page shows is gated
  // on real presence here — nothing synthetic, nothing hardcoded. ----
  function isNum(x) { return typeof x === 'number' && isFinite(x); }
  function ret1y(s) { return s && s.returns ? s.returns['1Y'] : null; }
  function hasHorizon(s) {                 // any numeric return horizon present?
    if (!s || !s.returns) return false;
    for (var k in s.returns) { if (isNum(s.returns[k])) return true; }
    return false;
  }
  // The build (build_index_summary.py) now owns the cadence-aware freshness judgement
  // and emits status='live' | 'stale' | 'calibrating' | 'soon'. Trust it: a 'live'
  // entry is current at its cadence. (The old fresh_through === as_of check was
  // tautological — the writer set them equal — and would false-negative now that as_of
  // is the run date and fresh_through the data date.)
  function isFresh(s) { return !!s && s.status === 'live'; }
  function seriesVals(s) { return (s && s.series ? s.series : []).map(function (p) { return p.value; }); }
  var MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  function fmtDate(s) {                     // "2026-06-17"->"17 Jun 2026"; "2026-05"->"May 2026"
    if (!s) return '';
    var p = String(s).split('-');
    if (p.length >= 3) return parseInt(p[2], 10) + ' ' + MON[+p[1] - 1] + ' ' + p[0];
    if (p.length === 2) return MON[+p[1] - 1] + ' ' + p[0];
    return String(s);
  }
  // Flagship is derived, not stored: Composite reclaims it the day it carries a
  // real 1Y; until then Public Equities (the one with the track record) headlines.
  function flagshipKey(sum) {
    var c = sum && sum.indexes && sum.indexes.composite;
    return (c && isNum(ret1y(c))) ? 'composite' : 'public';
  }
  function openAccess(e) { if (e) e.preventDefault(); if (typeof window.openEarlyAccess === 'function') window.openEarlyAccess(); }

  // ---------------------------------------------------------- TOP STRIP
  function renderTopStrip(sum) {
    var bar = document.querySelector('.top-bar');
    if (!bar || document.querySelector('.top-strip-extra')) return;
    var c = sum && sum.indexes && sum.indexes.composite;
    var wrap = document.createElement('div');
    wrap.className = 'top-strip-extra';
    var ticker = '';
    if (c && isFresh(c)) {
      var oneY = ret1y(c), hasY = isNum(oneY), up = hasY && oneY >= 0;
      ticker =
        '<a class="top-rci" href="' + PLACEHOLDER_URL + '" style="text-decoration:none">' +
          '<span class="top-rci-label">' + esc(c.code || 'RCI') + '</span>' +
          '<span class="top-rci-val">' + num(c.value, 2) + '</span>' +
          (hasY ? '<span class="top-rci-chg ' + (up ? 'up' : 'down') + '">' + (up ? '+' : '') + oneY.toFixed(2) + '%</span>' : '') +
        '</a>';
    }
    wrap.innerHTML = ticker + '<button class="btn-access" type="button">Contact</button>';
    bar.appendChild(wrap);
    wrap.querySelector('.btn-access').addEventListener('click', openAccess);
  }

  // ---------------------------------------------------------- HERO PROOF
  // NOTE: dead code today — index.html has no #hero-proof element and boot()
  // does not call this. Rebound to the summary (derived flagship) for hygiene so
  // no placeholder read remains; inert until a #hero-proof element is wired.
  function renderHeroProof(d, sum) {
    var host = $('hero-proof');
    if (!host) return;
    var s = sum && sum.indexes && sum.indexes[flagshipKey(sum)];
    var ed = (d.indexes || {})[flagshipKey(sum)] || {};
    var m = d.meta || {};
    if (!s || !isFresh(s)) { host.innerHTML = '<div class="proof-empty">Index awaiting calibration.</div>'; return; }
    var oneY = ret1y(s), hasY = isNum(oneY), up = hasY && oneY >= 0;
    var chg = hasY
      ? '<span class="proof-change ' + (up ? 'up' : 'down') + '">' + (up ? '+' : '') + oneY.toFixed(2) + '% · 1Y</span>'
      : (!hasHorizon(s) ? '<span class="proof-change muted">since inception · ' + esc(fmtDate(s.base && s.base.date)) + '</span>' : '');
    host.innerHTML =
      '<div class="proof-main">' +
        '<span class="proof-name">' + esc(ed.name || s.name) + '</span>' +
        '<span class="proof-value">' + num(s.value, 2) + '</span>' + chg +
      '</div>' +
      '<div class="proof-divider"></div>' +
      '<div class="proof-meta">' +
        '<span class="proof-meta-row">Base <b>' + num(s.base && s.base.value, 2) + '</b> on <b>' + esc(fmtDate(s.base && s.base.date)) + '</b></span>' +
        '<span class="proof-meta-row">Universe <b>' + esc(m.universe) + '</b> entities · market-cap weighted</span>' +
        '<a href="' + esc(ed.methodologyUrl || '#') + '">Methodology &rarr;</a>' +
      '</div>';
  }

  // ---------------------------------------------------------- INDEX FAMILY
  // s = index_summary.json entry (numbers/status/series); ed = home.json editorial
  // (display name, blurb, links). isLead = positional lead tile (visual only).
  function indexTile(key, s, ed, isLead) {
    ed = ed || {};
    if (!s) return '';
    var name = esc(ed.name || s.name);
    // One "Examine in detail" affordance per tile. No per-index detail /
    // methodology page is published yet, so this renders as a quiet "coming
    // soon" state rather than a dead link; when a page ships, set ed.detailUrl.
    var detail = (ed.detailUrl)
      ? '<div class="index-tile-links"><a href="' + esc(ed.detailUrl) + '">Examine in detail &rarr;</a></div>'
      : '<div class="index-tile-links"><span class="index-tile-soon" aria-disabled="true">Examine in detail</span></div>';
    // Not-yet-live: only a genuine soon status reads "Soon" (none today).
    if (s.status === 'soon') {
      return '<div class="index-tile is-soon">' +
        '<div class="index-tile-top"><span class="index-tile-name">' + name + '</span>' +
          '<span class="index-tag soon">Soon</span></div>' +
        '<div class="index-tile-val">—</div>' +
        '<div class="index-tile-blurb">' + esc(ed.blurb || '') + '</div>' + detail + '</div>';
    }
    // Live-but-behind cadence: a launched index whose data has fallen behind its cadence.
    // Show the REAL last value with its age and a "Delayed" badge — never "Calibrating",
    // which would claim not-yet-live when the truth is live-but-behind.
    if (s.status === 'stale') {
      var svals = seriesVals(s);
      var sspark = svals.length >= 2 ? spark(svals, SPARK_COLOR[key] || '#F5D921') : '';
      return '<div class="index-tile is-stale">' +
        '<div class="index-tile-top"><span class="index-tile-name">' + name + '</span>' +
          '<span class="index-tag delayed">Delayed</span></div>' +
        '<div class="index-tile-val">' + num(s.value, 2) + '</div>' +
        '<div class="index-tile-chg muted">as of ' + esc(fmtDate(s.fresh_through)) + '</div>' +
        '<div class="index-tile-blurb">' + esc(ed.blurb || '') + '</div>' +
        '<div class="index-spark">' + sspark + '</div>' + detail + '</div>';
    }
    // Calibrating (not yet live), or any other non-live status: no current value.
    if (s.status === 'calibrating' || !isFresh(s)) {
      return '<div class="index-tile is-calibrating">' +
        '<div class="index-tile-top"><span class="index-tile-name">' + name + '</span>' +
          '<span class="index-tag calibrating">Calibrating</span></div>' +
        '<div class="index-tile-val pending">&mdash; calibrating</div>' +
        '<div class="index-tile-blurb">' + esc(ed.blurb || '') + '</div>' + detail + '</div>';
    }
    // Live. Cadence badge only — no flagship label (lead is positional/visual).
    var tag = s.cadence ? '<span class="index-tag cadence">' + esc(s.cadence) + '</span>' : '';
    var oneY = ret1y(s), chg = '';
    if (isNum(oneY)) {
      var up = oneY >= 0;
      chg = '<div class="index-tile-chg ' + (up ? 'up' : 'down') + '">' + (up ? '+' : '') + oneY.toFixed(2) + '% · 1Y</div>';
    } else if (!hasHorizon(s)) {            // forward-only: since inception, no horizon button
      chg = '<div class="index-tile-chg muted">since inception · ' + esc(fmtDate(s.base && s.base.date)) + '</div>';
    }                                        // else: real index missing 1Y but with other horizons -> no 1Y line
    var vals = seriesVals(s);
    var sparkHtml = vals.length >= 2 ? spark(vals, SPARK_COLOR[key] || '#F5D921') : '';
    return '<div class="index-tile' + (isLead ? ' is-lead' : '') + '">' +
      '<div class="index-tile-top"><span class="index-tile-name">' + name + '</span>' + tag + '</div>' +
      '<div class="index-tile-val">' + num(s.value, 2) + '</div>' + chg +
      '<div class="index-tile-blurb">' + esc(ed.blurb || '') + '</div>' +
      '<div class="index-spark">' + sparkHtml + '</div>' + detail + '</div>';
  }

  function renderIndexFamily(d, sum) {
    var host = $('index-family');
    if (!host) return;
    var ix = (sum && sum.indexes) || {};
    var ed = d.indexes || {};
    // Order: the two mature daily indices, then the monthly private index, then
    // the two forward-only weekly indices last (RCI ready to lead once it
    // carries history). Public Equities leads — positional emphasis, no label.
    var order = ['public', 'bottleneck', 'private', 'composite', 'commodities'];
    host.innerHTML = order.map(function (k, i) {
      return indexTile(k, ix[k], ed[k], i === 0);
    }).join('');
  }

  // ---------------------------------------------------------- SECTOR CARDS
  var SECTOR_KEY_MAP = { semi: 'semiconductors' };   // _meta: home keys 'semi', summary keys 'semiconductors'
  function renderSectors(d, sum) {
    var host = $('sector-cards');
    if (!host) return;
    var ss = (sum && sum.sectors) || {};
    host.innerHTML = (d.sectors || []).map(function (s) {
      var sm = ss[SECTOR_KEY_MAP[s.key] || s.key] || {};
      var r = sm.returns || {};
      var commodities = s.commodities ? (' · ' + s.commodities + ' commodities') : '';
      // presence-gated: a return block renders only if the summary carries a number
      function chgBlock(label, v) {
        if (!isNum(v)) return '';
        return '<div class="sector-chg-block"><span class="sector-chg-label">' + label + '</span>' +
          '<span class="sector-chg-val ' + (v >= 0 ? 'up' : 'down') + '">' + (v >= 0 ? '+' : '') + v.toFixed(2) + '%</span></div>';
      }
      return '<div class="sector-card" style="--hue:' + s.hue + '">' +
        '<div class="sector-card-top"><span class="sector-swatch"></span>' +
          '<span class="sector-name">' + esc(s.name) + '</span></div>' +
        '<div class="sector-val">' + num(sm.value, 2) + '</div>' +
        '<div class="sector-changes">' + chgBlock('1W', r['1W']) + chgBlock('1M', r['1M']) + '</div>' +
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
      var inner =
        '<span class="ref-kind">' + esc(r.kind) + '</span>' +
        '<span class="ref-name">' + esc(r.name) + '</span>' +
        '<span class="ref-blurb">' + esc(r.blurb || '') + '</span>';
      // Published reference pages render as a real link; the rest stay quiet
      // "coming soon" stubs (matches research.html's reference treatment).
      if (r.live && r.url) {
        return '<a class="ref-card" href="' + esc(r.url) + '">' + inner +
          '<span class="ref-arrow">Open &rarr;</span></a>';
      }
      return '<div class="ref-card is-soon">' + inner +
        '<span class="ref-arrow">Coming soon</span></div>';
    }).join('');
    // The home library is a curated subset — point to the full set on the
    // research page (Reference & methodology section).
    var more = '<a class="reference-more" href="research.html#rh-ref-title">Full reference library &rarr;</a>';
    if (host.parentNode && !host.parentNode.querySelector('.reference-more')) {
      host.insertAdjacentHTML('afterend', more);
    }
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
          (a.url ? '<a class="rail-tile-link" href="' + esc(a.url) + '">Read full article &rarr;</a>' : '') +
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
  function boot(d, sum) {
    renderTopStrip(sum);
    renderIndexFamily(d, sum);
    renderSectors(d, sum);
    renderReferences(d);

    var graph = null;
    var mount = $('frontier-stack');
    if (mount && window.FrontierStack) {
      // Flat is the single Frontier Stack view (no Stack mode / toggle).
      graph = new FrontierStack(mount, d, { mode: 'flat' });
      // Integration handle: lets other scripts/console drive the graph
      // (e.g. graph.highlight(cells), graph.setPropagationGranularity('asset')).
      window.frontierStack = graph;
    }
    renderRail(d, graph);
  }

  function fail(msg) {
    var hp = $('hero-proof');
    if (hp) hp.innerHTML = '<div class="proof-empty">' + esc(msg) + '</div>';
    var rl = $('rail-list');
    if (rl) rl.innerHTML = '<div class="rail-skeleton">Research unavailable.</div>';
  }

  function start() {
    function okJson(label) {
      return function (r) { if (!r.ok) throw new Error(label + ' ' + r.status); return r.json(); };
    }
    Promise.all([
      fetch('data/home.json?v=' + Date.now()).then(okJson('home.json')),
      fetch('data/index/index_summary.json?v=' + Date.now()).then(okJson('index_summary.json'))
    ]).then(function (res) { boot(res[0], res[1]); })
      .catch(function (e) { fail('Data feed offline — calibrating, tovarishch.'); if (window.console) console.warn('[home]', e); });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
