/* ============================================================
   THE FRONTIER STACK — reusable graph module
   ------------------------------------------------------------
   One object, two morphing modes (Stack ⇄ Flat). Pure CSS-3D.
   Driven entirely by the data contract (Build Brief §7) — nothing
   hardcoded. Honest morph: a dot's x (value-chain tier) is identical
   in both modes; only the sector planes transform.

     x  = value-chain tier (1..8)
     y  = market cap, log-normalised within the dot's layer
     size + colour = bottleneck criticality

   Public API:
     const g = new FrontierStack(mountEl, data, opts);
     g.setMode('stack' | 'flat');
     g.highlight([['semi',3],['semi',4]]);   // research → cells
     g.clearHighlight();
     g.setPropagationGranularity('sector' | 'asset');   // pluggable
   ============================================================ */
(function (global) {
  'use strict';

  // sector layers, bottom → top (Materials base … Space top)
  var SECTOR_ORDER = ['materials', 'semi', 'robotics', 'space'];
  var TIER_COUNT = 8;

  // bottleneck-criticality scale (matches CSS tokens §2)
  var CRIT_COLOR = { low: '#4DA98B', medium: '#E0A33C', high: '#E0703D', critical: '#DC4A4A' };
  var CRIT_SIZE  = { low: 5.5, medium: 7, high: 8.5, critical: 11 };
  var CRIT_GLOW  = { low: 3, medium: 5, high: 7, critical: 10 };
  var CRIT_RANK  = { low: 0, medium: 1, high: 2, critical: 3 };
  // originCriticalityFactor — disruption burns hotter for critical nodes (§5)
  var CRITF      = { critical: 1.0, high: 0.82, medium: 0.62, low: 0.42 };

  // ---- small deterministic PRNG so dot layout never jitters on re-render ----
  function hashSeed(str) {
    var h = 2166136261 >>> 0;
    for (var i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 16777619); }
    return h >>> 0;
  }
  function mulberry32(a) {
    return function () {
      a |= 0; a = (a + 0x6D2B79F5) | 0;
      var t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  // approx standard normal from two uniforms (Box–Muller)
  function gauss(rng) {
    var u = Math.max(1e-9, rng()), v = rng();
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
  }

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function el(tag, cls, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html != null) e.innerHTML = html;
    return e;
  }

  // ---- sparkline (shared with home.js via FrontierStack.sparkline) ----
  function sparkline(series, color, w, h) {
    w = w || 100; h = h || 32;
    if (!series || series.length < 2) return '';
    var min = Math.min.apply(null, series), max = Math.max.apply(null, series);
    var span = (max - min) || 1, n = series.length, pad = 3;
    function X(i) { return (i / (n - 1)) * w; }
    function Y(v) { return h - pad - ((v - min) / span) * (h - pad * 2); }
    var line = series.map(function (v, i) { return X(i).toFixed(1) + ',' + Y(v).toFixed(1); }).join(' ');
    var area = '0,' + h + ' ' + line + ' ' + w + ',' + h;
    return '<svg viewBox="0 0 ' + w + ' ' + h + '" preserveAspectRatio="none" aria-hidden="true">' +
      '<polygon points="' + area + '" fill="' + color + '" fill-opacity="0.13" stroke="none"/>' +
      '<polyline points="' + line + '" fill="none" stroke="' + color + '" stroke-width="1.6" ' +
      'stroke-linejoin="round" stroke-linecap="round" vector-effect="non-scaling-stroke"/>' +
      '<circle cx="' + w.toFixed(1) + '" cy="' + Y(series[n - 1]).toFixed(1) + '" r="1.9" fill="' + color + '"/>' +
      '</svg>';
  }

  // ============================================================
  function FrontierStack(mount, data, opts) {
    this.mount = typeof mount === 'string' ? document.getElementById(mount) : mount;
    this.data = data || {};
    this.opts = opts || {};
    this.mode = this.opts.mode || 'flat';
    this.granularity = 'sector';
    this.layers = {};      // sector key → { el, overlay, dotsEl, dots:[] }
    this.dotEls = [];      // all dot elements
    this.selected = null;
    if (!this.mount) return;
    this._reduced = global.matchMedia && global.matchMedia('(prefers-reduced-motion: reduce)').matches;
    this._build();
    this.setMode(this.mode);
    if (this.opts.toggleEl) this._wireToggle(this.opts.toggleEl);
  }

  FrontierStack.sparkline = sparkline;

  FrontierStack.prototype.sectorMeta = function (key) {
    var arr = this.data.sectors || [];
    for (var i = 0; i < arr.length; i++) if (arr[i].key === key) return arr[i];
    return { key: key, name: key, hue: '#888', index: {} };
  };

  // ---- generate dots from assets[] (live) or expand cells (placeholder) ----
  FrontierStack.prototype._buildDots = function () {
    var bySector = {};
    SECTOR_ORDER.forEach(function (s) { bySector[s] = []; });

    if (Array.isArray(this.data.assets) && this.data.assets.length) {
      // live path — one dot per asset, real market caps
      this.data.assets.forEach(function (a) {
        if (!bySector[a.sector]) bySector[a.sector] = [];
        bySector[a.sector].push({
          sector: a.sector, tier: a.tier, criticality: a.criticality,
          mcap: a.marketCap || 1, name: a.name, ticker: a.ticker,
          stage: a.stage || '', sampleNames: a.name, ledgerUrl: a.ledgerUrl,
          id: a.id
        });
      });
    } else {
      // placeholder path — expand cells into synthetic dots
      (this.data.cells || []).forEach(function (cell, ci) {
        var n = (cell.public || 0) + (cell.private || 0) + (cell.commodities || 0);
        var rng = mulberry32(hashSeed(cell.sector + '-' + cell.tier + '-' + ci));
        for (var k = 0; k < n; k++) {
          // synthetic log-normal market cap, deterministic per dot
          var mcap = Math.exp(gauss(rng) * 1.05 + CRIT_RANK[cell.criticality] * 0.18);
          if (!bySector[cell.sector]) bySector[cell.sector] = [];
          bySector[cell.sector].push({
            sector: cell.sector, tier: cell.tier, criticality: cell.criticality,
            mcap: mcap, stage: cell.stage, sampleNames: cell.sampleNames || '',
            jitter: (rng() - 0.5)
          });
        }
      });
    }
    return bySector;
  };

  FrontierStack.prototype._build = function () {
    var self = this;
    var graph = el('div', 'fs-graph');
    graph.setAttribute('role', 'group');
    graph.setAttribute('aria-label', 'The Frontier Stack — interactive value-chain map');
    this.graph = graph;

    // Value-flow axis (Materials → Space): a single upward arrow spanning the
    // stack. Within-layer vertical position is NOT a quantitative axis here.
    var yax = el('div', 'fs-yaxis', '<span class="fs-yaxis-arrow" aria-hidden="true"></span><span class="fs-yaxis-cap">value</span>');
    graph.appendChild(yax);

    // tier column headers (flat view)
    var heads = el('div', 'fs-tier-headers');
    (this.data.tiers || []).forEach(function (label, idx) {
      var h = el('div', 'fs-tier-header', esc(label));
      h.dataset.tier = String(idx + 1);
      h.addEventListener('mouseenter', function () { self._lensTier(idx + 1); });
      h.addEventListener('mouseleave', function () { self._lensClear(); });
      heads.appendChild(h);
    });
    graph.appendChild(heads);

    // scene + four planes
    var scene = el('div', 'fs-scene');
    var dots = this._buildDots();

    SECTOR_ORDER.forEach(function (skey, i) {
      var meta = self.sectorMeta(skey);
      var layer = el('div', 'fs-layer');
      layer.dataset.sector = skey;
      layer.style.setProperty('--i', i);
      layer.style.setProperty('--hue', meta.hue || '#888');

      layer.appendChild(el('div', 'fs-layer-plane'));
      var overlay = el('div', 'fs-layer-overlay');
      layer.appendChild(overlay);

      // sector label — name + asset count only (no value / %-change / sparkline)
      var count = (meta.public || 0) + (meta.private || 0) + (meta.commodities || 0);
      var panel = el('div', 'fs-layer-panel');
      panel.innerHTML =
        '<span class="fs-panel-name">' + esc(meta.name) + '</span>' +
        '<span class="fs-panel-count">' + count + ' assets</span>';
      layer.appendChild(panel);

      // dots for this layer — y = log market cap normalised within the layer
      var dotsEl = el('div', 'fs-dots');
      var list = dots[skey] || [];
      var logs = list.map(function (d) { return Math.log(d.mcap); });
      var lmin = logs.length ? Math.min.apply(null, logs) : 0;
      var lmax = logs.length ? Math.max.apply(null, logs) : 1;
      var lspan = (lmax - lmin) || 1;
      var padT = 0.13, padB = 0.15;

      list.forEach(function (d, di) {
        var b = document.createElement('button');
        b.type = 'button';
        b.className = 'fs-dot';
        b.dataset.tier = String(d.tier);
        b.dataset.sector = skey;
        var size = CRIT_SIZE[d.criticality] || 6;
        b.style.setProperty('--d', size + 'px');
        b.style.setProperty('--cc', CRIT_COLOR[d.criticality] || '#888');
        b.style.setProperty('--glow', (CRIT_GLOW[d.criticality] || 4) + 'px');

        // x = tier column centre + deterministic jitter within the column
        var jit = (d.jitter != null ? d.jitter : ((di % 7) / 7 - 0.5));
        var xFrac = ((d.tier - 0.5) / TIER_COUNT) + jit * (0.78 / TIER_COUNT);
        // y = log market cap normalised within this layer (higher = nearer top)
        var yNorm = (Math.log(d.mcap) - lmin) / lspan;
        var yFrac = padT + (1 - yNorm) * (1 - padT - padB);
        b.style.left = (xFrac * 100).toFixed(2) + '%';
        b.style.top = (yFrac * 100).toFixed(2) + '%';

        b.setAttribute('aria-label',
          meta.name + ' · ' + (self.data.tiers[d.tier - 1] || ('tier ' + d.tier)) +
          ' · ' + d.criticality + ' criticality');
        b._d = d;
        b.addEventListener('click', function (ev) { ev.stopPropagation(); self._openDoorway(d, b); });
        dotsEl.appendChild(b);
        self.dotEls.push(b);
      });
      layer.appendChild(dotsEl);

      scene.appendChild(layer);
      self.layers[skey] = { el: layer, overlay: overlay, dotsEl: dotsEl, dots: list };
    });

    graph.appendChild(scene);
    this.mount.innerHTML = '';
    this.mount.appendChild(graph);

    this._buildDoorway();
    this._buildLegend();
  };

  // synthesize a short sparkline trend for a sector panel (placeholder)
  FrontierStack.prototype._synthSeries = function (key, chg) {
    var rng = mulberry32(hashSeed('spark-' + key));
    var n = 16, out = [], v = 100;
    var drift = (chg || 0) / 100 / n;
    for (var i = 0; i < n; i++) { v *= (1 + drift + (rng() - 0.5) * 0.03); out.push(v); }
    return out;
  };

  FrontierStack.prototype._buildLegend = function () {
    var host = document.getElementById('fs-legend');
    if (!host) return;
    var sectors = (this.data.sectors || []).map(function (s) {
      return '<span class="fs-legend-item"><span class="fs-legend-swatch" style="border-color:' + s.hue + '"></span>' + esc(s.name) + '</span>';
    }).join('');
    var crit = [['low', 'Low'], ['medium', 'Med'], ['high', 'High'], ['critical', 'Critical']].map(function (c) {
      return '<span class="fs-legend-item"><span class="fs-legend-dot" style="background:' + CRIT_COLOR[c[0]] + '"></span>' + c[1] + '</span>';
    }).join('');
    host.innerHTML =
      '<span class="fs-legend-group"><span class="fs-legend-label">Sector</span>' + sectors + '</span>' +
      '<span class="fs-legend-group"><span class="fs-legend-label">Criticality</span>' + crit + '</span>';
  };

  // ---------- mode ----------
  FrontierStack.prototype.setMode = function (mode) {
    this.mode = (mode === 'flat') ? 'flat' : 'stack';
    this.graph.classList.toggle('is-stack', this.mode === 'stack');
    this.graph.classList.toggle('is-flat', this.mode === 'flat');
    if (this._toggleEl) {
      this._toggleEl.querySelectorAll('.fs-mode-btn').forEach(function (btn) {
        btn.classList.toggle('is-active', btn.dataset.mode === mode);
      });
    }
  };
  FrontierStack.prototype._wireToggle = function (toggleEl) {
    var self = this;
    this._toggleEl = toggleEl;
    toggleEl.querySelectorAll('.fs-mode-btn').forEach(function (btn) {
      btn.addEventListener('click', function () { self.setMode(btn.dataset.mode); });
    });
    this.setMode(this.mode);
  };

  // ---------- tier lens (flat header hover) ----------
  FrontierStack.prototype._lensTier = function (tier) {
    if (this.mode !== 'flat') return;
    this.graph.classList.add('is-lensing');
    this.dotEls.forEach(function (d) { d.classList.toggle('fs-lit', d.dataset.tier === String(tier)); });
  };
  FrontierStack.prototype._lensClear = function () {
    this.graph.classList.remove('is-lensing');
    this.dotEls.forEach(function (d) { d.classList.remove('fs-lit'); });
  };

  // ---------- research highlight (article → cells) ----------
  FrontierStack.prototype.highlight = function (cells) {
    if (!cells || !cells.length) { this.clearHighlight(); return; }
    var keys = {};
    cells.forEach(function (c) { keys[c[0] + '|' + c[1]] = true; });
    var hitSectors = {};
    this.graph.classList.add('is-highlighting');
    this.dotEls.forEach(function (d) {
      var hit = keys[d.dataset.sector + '|' + d.dataset.tier];
      d.classList.toggle('fs-hit', !!hit);
      if (hit) hitSectors[d.dataset.sector] = true;
    });
    for (var s in this.layers) {
      this.layers[s].el.classList.toggle('fs-hit-layer', !!hitSectors[s]);
    }
  };
  FrontierStack.prototype.clearHighlight = function () {
    this.graph.classList.remove('is-highlighting');
    this.dotEls.forEach(function (d) { d.classList.remove('fs-hit'); });
    for (var s in this.layers) this.layers[s].el.classList.remove('fs-hit-layer');
  };

  // ---------- disruption cascade ----------
  // Pluggable on edge granularity. severity(dependent) =
  //   max-over-paths( Π edge_strength ) × originCriticalityFactor.
  FrontierStack.prototype.setPropagationGranularity = function (g) {
    this.granularity = (g === 'asset') ? 'asset' : 'sector';
  };
  FrontierStack.prototype._propagate = function (originSector, originCrit) {
    // Asset-level granularity is a forward hook: it activates only when assets
    // carry dependsOn/dependedOnBy edges. If 'asset' is requested before that
    // data exists, fall back to sector-level — so setPropagationGranularity('asset')
    // is always a safe no-op, never an error.
    var hasAssetEdges = this.granularity === 'asset' &&
      Array.isArray(this.data.assets) &&
      this.data.assets.some(function (a) { return a && (a.dependsOn || a.dependedOnBy); });
    // (asset-level traversal will branch here on hasAssetEdges once populated)
    void hasAssetEdges;
    var edges = this.data.dependencyEdges || {};
    var factor = CRITF[originCrit] != null ? CRITF[originCrit] : 0.6;
    var best = {}, depth = {};
    best[originSector] = 1; depth[originSector] = 0;
    // Bellman–Ford style relaxation (max-product); 4 sectors → converges fast
    for (var pass = 0; pass < SECTOR_ORDER.length; pass++) {
      for (var u in best) {
        var outs = edges[u] || {};
        for (var v in outs) {
          var prod = best[u] * outs[v];
          if (best[v] == null || prod > best[v]) {
            best[v] = prod; depth[v] = depth[u] + 1;
          }
        }
      }
    }
    var sev = {};
    for (var k in best) sev[k] = { severity: best[k] * factor, depth: depth[k] };
    return sev;
  };

  FrontierStack.prototype.runDisruption = function (originSector, originCrit, originDotEl) {
    var self = this;
    var sev = this._propagate(originSector, originCrit);
    this.clearDisruption(true);
    // force a reflow so each overlay's opacity transition starts from 0
    // (set synchronously rather than via rAF, which throttles in hidden tabs)
    void this.graph.offsetHeight;
    this.graph.classList.add('is-disrupting');
    var step = this._reduced ? 0 : 130;

    SECTOR_ORDER.forEach(function (skey) {
      var L = self.layers[skey];
      if (!L) return;
      var s = sev[skey];
      var v = s ? Math.max(0, Math.min(1, s.severity)) : 0;
      L.overlay.style.transitionDelay = (s ? s.depth * step : 0) + 'ms';
      L.el.style.setProperty('--sev', v.toFixed(3));
    });

    // origin burst
    if (originDotEl && !this._reduced) {
      var burst = el('div', 'fs-burst');
      burst.style.left = originDotEl.style.left;
      burst.style.top = originDotEl.style.top;
      self.layers[originSector].dotsEl.appendChild(burst);
      setTimeout(function () { if (burst.parentNode) burst.parentNode.removeChild(burst); }, 950);
    }
    this._renderCascade(sev, originSector);
  };

  FrontierStack.prototype.clearDisruption = function (keepClass) {
    if (!keepClass) this.graph.classList.remove('is-disrupting');
    for (var s in this.layers) {
      this.layers[s].el.style.setProperty('--sev', '0');
      this.layers[s].overlay.style.transitionDelay = '0ms';
    }
    var cas = this._doorway && this._doorway.querySelector('.fs-dw-cascade');
    if (cas && !keepClass) cas.classList.remove('is-shown');
  };

  FrontierStack.prototype._renderCascade = function (sev, originSector) {
    var cas = this._doorway.querySelector('.fs-dw-cascade');
    if (!cas) return;
    var self = this;
    var rows = SECTOR_ORDER.slice().reverse().map(function (skey) {
      var meta = self.sectorMeta(skey);
      var s = sev[skey];
      var v = s ? s.severity : 0;
      var pct = Math.round(v * 100);
      var color = v > 0.8 ? '#DC4A4A' : v > 0.55 ? '#E0703D' : v > 0.3 ? '#E0A33C' : v > 0 ? '#4DA98B' : '#2A2D34';
      var tag = (skey === originSector) ? ' <span style="color:#DC4A4A;font-size:8px;letter-spacing:.1em;">ORIGIN</span>' : '';
      return '<div class="fs-cascade-row">' +
        '<span class="fs-cascade-name">' + esc(meta.name.split(' ')[0]) + tag + '</span>' +
        '<span class="fs-cascade-bar"><span class="fs-cascade-fill" style="width:' + pct + '%;background:' + color + '"></span></span>' +
        '<span class="fs-cascade-pct">' + (v > 0 ? pct + '%' : '—') + '</span>' +
        '</div>';
    }).join('');
    cas.innerHTML = '<div class="fs-dw-section-label">Cascade severity by layer</div>' + rows;
    cas.classList.add('is-shown');
  };

  // ---------- doorway ----------
  FrontierStack.prototype._buildDoorway = function () {
    if (document.getElementById('fs-doorway')) {
      this._doorway = document.getElementById('fs-doorway');
      this._backdrop = document.getElementById('fs-doorway-backdrop');
      return;
    }
    var self = this;
    var back = el('div', 'fs-doorway-backdrop');
    back.id = 'fs-doorway-backdrop';
    var dw = el('div', 'fs-doorway');
    dw.id = 'fs-doorway';
    dw.setAttribute('role', 'dialog');
    dw.setAttribute('aria-label', 'Asset doorway');
    dw.setAttribute('aria-hidden', 'true');
    dw.innerHTML =
      '<button class="fs-dw-close" aria-label="Close">&times;</button>' +
      '<div class="fs-doorway-scroll"></div>';
    document.body.appendChild(back);
    document.body.appendChild(dw);
    this._doorway = dw; this._backdrop = back;

    dw.querySelector('.fs-dw-close').addEventListener('click', function () { self.closeDoorway(); });
    back.addEventListener('click', function () { self.closeDoorway(); });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && dw.classList.contains('is-open')) self.closeDoorway();
    });
  };

  FrontierStack.prototype._openDoorway = function (d, dotEl) {
    var self = this;
    var meta = this.sectorMeta(d.sector);
    var tierLabel = (this.data.tiers && this.data.tiers[d.tier - 1]) || ('Tier ' + d.tier);
    var critColor = CRIT_COLOR[d.criticality] || '#888';

    if (this.selected) this.selected.classList.remove('fs-selected');
    this.selected = dotEl || null;
    if (dotEl) dotEl.classList.add('fs-selected');
    this.clearDisruption();

    var ledger = (this.data.ledgerLayers || []).map(function (L) {
      var free = L.access === 'free';
      return '<div class="fs-ledger-row ' + (free ? 'free' : 'paid') + '">' +
        '<span><span class="fs-ledger-name">' + esc(L.name) + '</span><br>' +
        '<span class="fs-ledger-blurb">' + esc(L.blurb || '') + '</span></span>' +
        '<span class="fs-ledger-lock ' + (free ? 'free' : 'paid') + '">' + (free ? 'Free' : 'Locked') + '</span>' +
        '</div>';
    }).join('');

    var samples = d.sampleNames || d.name || '';
    var ledgerUrl = d.ledgerUrl || (d.id ? ('/asset/' + d.id) : 'assets.html');

    var html =
      '<span class="fs-dw-eyebrow" style="color:' + (meta.hue || '#888') + '">' + esc(meta.name) + '</span>' +
      '<h3 class="fs-dw-title">' + esc(d.stage || tierLabel) + '</h3>' +
      '<div class="fs-dw-meta">' +
        '<span class="fs-dw-chip">' + esc(tierLabel) + '</span>' +
        '<span class="fs-dw-chip" style="border-color:' + (meta.hue || '#888') + ';color:' + (meta.hue || '#888') + '">' + esc(meta.name) + '</span>' +
        '<span class="fs-dw-chip crit" style="background:' + critColor + '">' + esc(d.criticality) + '</span>' +
      '</div>' +
      (samples ? ('<div class="fs-dw-section-label">Sample assets</div><div class="fs-dw-samples">' + esc(samples) + '</div>') : '') +
      '<div class="fs-dw-section-label">The nine-layer ledger</div>' +
      '<div class="fs-dw-ledger">' + ledger + '</div>' +
      '<div class="fs-dw-actions">' +
        '<a class="fs-dw-btn primary" href="' + esc(ledgerUrl) + '">Open 9-layer ledger &rarr;</a>' +
        '<button class="fs-dw-btn ghost" type="button" id="fs-dw-disrupt">Simulate disruption &rarr;</button>' +
      '</div>' +
      '<div class="fs-dw-cascade"></div>';

    this._doorway.querySelector('.fs-doorway-scroll').innerHTML = html;
    this._doorway.querySelector('#fs-dw-disrupt').addEventListener('click', function () {
      self.runDisruption(d.sector, d.criticality, dotEl);
    });

    this._doorway.classList.add('is-open');
    this._doorway.setAttribute('aria-hidden', 'false');
    this._backdrop.classList.add('is-open');
    var closeBtn = this._doorway.querySelector('.fs-dw-close');
    if (closeBtn) closeBtn.focus();
  };

  FrontierStack.prototype.closeDoorway = function () {
    this._doorway.classList.remove('is-open');
    this._doorway.setAttribute('aria-hidden', 'true');
    this._backdrop.classList.remove('is-open');
    this.clearDisruption();
    if (this.selected) { this.selected.classList.remove('fs-selected'); this.selected.focus(); this.selected = null; }
  };

  global.FrontierStack = FrontierStack;
})(window);
