/* ============================================================
   INDEX CHART — reusable live time-series index chart
   ------------------------------------------------------------
   A self-contained, interactive index chart for the Robotnik
   index family. Keyed by series + accent so every index detail
   page (R4 first, R5–R8 next) mounts its own without forking it.

   Features:
     - Time-range toggle: 1M / 3M / 6M / 1Y / 3Y / 5Y (default 1Y),
       each window rescaled to its own data.
     - Value / % toggle. % mode rebases to 0 at the LEFT EDGE of the
       visible window — the convention from the earlier dashboard
       chart (js/main.js: (v - v0) / v0 * 100).
     - Labelled y-axis with gridlines (index values in value mode,
       percentages in % mode) and a labelled 1,000 base line in value
       mode whenever the base is within the visible price range.
     - Pointer/touch crosshair + marker reading back value and date.

   Data:
     - Binds to the live feed (index_summary.json) for the per-series
       header / base / current level, keyed by seriesKey.
     - Pulls the FULL multi-year series from the canonical per-index
       file that the feed self-describes in _meta.sources[seriesKey]
       (e.g. bottleneck_weighted_composite.json — ~5Y of history).
       Falls back to the feed's trailing-1Y slice if that read fails.

   Visual language reused from the Frontier Stack flagship: SVG line +
   area with non-scaling strokes; the marker lives in an HTML overlay
   (CSS px) so it stays a true circle and all positions are percentage
   based, which makes the chart resize-proof.

   Public API:
     new IndexChart(mountEl, {
       seriesKey: 'bottleneck',          // key under index_summary.indexes
       accent:    '#E0A33C',             // line / fill / marker colour
       name:      'Robotnik …',          // header label (defaults to feed name)
       code:      'RBWC',                // optional ticker-style code
       source:    '/data/index/index_summary.json',  // live feed (optional)
       fullSource:'/data/index/…json'    // deep-history file (optional override)
     });
   ============================================================ */
(function (global) {
  'use strict';

  var DEFAULT_SOURCE = '/data/index/index_summary.json';
  var STYLE_ID = 'index-chart-styles';
  var RANGES = [
    { d: 30,   l: '1M' }, { d: 90,   l: '3M' }, { d: 180,  l: '6M' },
    { d: 365,  l: '1Y' }, { d: 1095, l: '3Y' }, { d: 1825, l: '5Y' }
  ];
  var DEFAULT_RANGE = 365;       // 1Y
  var VB_W = 1000, VB_H = 300;   // SVG viewBox (line drawn here, stretched to fill)

  function el(tag, cls, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html != null) e.innerHTML = html;
    return e;
  }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function fmtNum(n, dp) {
    if (n == null || isNaN(n)) return '—';
    return Number(n).toLocaleString('en-GB', {
      minimumFractionDigits: dp == null ? 2 : dp,
      maximumFractionDigits: dp == null ? 2 : dp
    });
  }
  function fmtPct(n) {
    if (n == null || isNaN(n)) return '—';
    return (n >= 0 ? '+' : '') + Number(n).toFixed(2) + '%';
  }
  function ord(dateStr) {            // y-m-d -> day number (UTC, no clock)
    var p = String(dateStr).split('-');
    return Date.UTC(+p[0], +p[1] - 1, +p[2]) / 86400000;
  }
  function fmtDate(s) {
    if (!s) return '';
    var d = new Date(s + 'T00:00:00Z');
    if (isNaN(d.getTime())) return s;
    return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' });
  }
  function fmtDateShort(s, rangeDays) {
    if (!s) return '';
    var d = new Date(s + 'T00:00:00Z');
    if (isNaN(d.getTime())) return s;
    if (rangeDays > 365) return d.toLocaleDateString('en-GB', { month: 'short', year: '2-digit', timeZone: 'UTC' }).replace(' ', " '");
    return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', timeZone: 'UTC' });
  }
  // "nice" axis ticks: round step + rounded bounds, ~count divisions
  function niceTicks(min, max, count) {
    if (min === max) { min -= 1; max += 1; }
    function nice(range, round) {
      var exp = Math.floor(Math.log(range) / Math.LN10), f = range / Math.pow(10, exp), nf;
      if (round) nf = f < 1.5 ? 1 : f < 3 ? 2 : f < 7 ? 5 : 10;
      else nf = f <= 1 ? 1 : f <= 2 ? 2 : f <= 5 ? 5 : 10;
      return nf * Math.pow(10, exp);
    }
    var step = nice(nice(max - min, false) / (count - 1), true);
    var lo = Math.floor(min / step) * step, hi = Math.ceil(max / step) * step;
    var ticks = [];
    for (var v = lo; v <= hi + step * 0.5; v += step) ticks.push(+v.toFixed(6));
    return { ticks: ticks, min: lo, max: hi };
  }

  // ---- one-time injected stylesheet (accent is per-instance via --ic-accent) ----
  function ensureStyles() {
    if (document.getElementById(STYLE_ID)) return;
    var css = [
      ".ic-card{border:1px solid var(--border,#23262d);border-radius:14px;background:rgba(255,255,255,0.015);padding:1.05rem 1.2rem 0.9rem;}",
      ".ic-head{display:flex;align-items:flex-start;justify-content:space-between;gap:1rem;}",
      ".ic-id{display:flex;flex-direction:column;gap:3px;min-width:0;}",
      ".ic-name{font-family:'Space Grotesk',sans-serif;font-size:12.5px;font-weight:600;color:var(--text,#e6e9ef);}",
      ".ic-code{font-family:'Space Grotesk',sans-serif;font-size:10px;font-weight:500;letter-spacing:0.18em;text-transform:uppercase;color:var(--text-dim,#8a909c);}",
      ".ic-readout{text-align:right;white-space:nowrap;}",
      ".ic-value{display:block;font-family:'Space Grotesk',sans-serif;font-size:1.55rem;font-weight:700;font-variant-numeric:tabular-nums;color:var(--text,#e6e9ef);line-height:1.05;}",
      ".ic-change{font-family:'Space Grotesk',sans-serif;font-size:12px;font-weight:600;font-variant-numeric:tabular-nums;color:var(--text-dim,#8a909c);}",
      ".ic-change.up{color:#46d39a;}.ic-change.down{color:#ef6a6a;}",
      ".ic-controls{display:flex;align-items:center;justify-content:space-between;gap:0.6rem;flex-wrap:wrap;margin:0.75rem 0 0.35rem;}",
      ".ic-ranges,.ic-modes{display:inline-flex;gap:2px;background:rgba(255,255,255,0.04);border:1px solid var(--border,#23262d);border-radius:8px;padding:2px;}",
      ".ic-range-btn,.ic-mode-btn{font-family:'Space Grotesk',sans-serif;font-size:11px;font-weight:600;letter-spacing:0.02em;color:var(--text-dim,#8a909c);background:transparent;border:0;padding:4px 9px;border-radius:6px;cursor:pointer;}",
      ".ic-range-btn:hover,.ic-mode-btn:hover{color:var(--text,#e6e9ef);}",
      ".ic-range-btn.is-active,.ic-mode-btn.is-active{background:color-mix(in srgb, var(--ic-accent,#E0A33C) 18%, transparent);color:var(--text,#e6e9ef);}",
      ".ic-plotwrap{position:relative;height:300px;}",
      ".ic-yaxis{position:absolute;left:0;top:8px;bottom:24px;width:46px;pointer-events:none;}",
      ".ic-ylabel{position:absolute;right:6px;transform:translateY(-50%);font-family:'Space Grotesk',sans-serif;font-size:10px;font-weight:500;color:var(--text-dim,#8a909c);font-variant-numeric:tabular-nums;white-space:nowrap;}",
      ".ic-canvas{position:absolute;left:46px;right:4px;top:8px;bottom:24px;}",
      ".ic-svg{position:absolute;inset:0;width:100%;height:100%;display:block;}",
      ".ic-grid{position:absolute;left:0;right:0;height:0;border-top:1px solid rgba(255,255,255,0.055);pointer-events:none;}",
      ".ic-baseline{position:absolute;left:0;right:0;height:0;border-top:1px dashed color-mix(in srgb, var(--ic-accent,#E0A33C) 55%, transparent);pointer-events:none;}",
      ".ic-baseline-tag{position:absolute;right:2px;top:-7px;font-family:'Space Grotesk',sans-serif;font-size:9.5px;font-weight:600;color:color-mix(in srgb, var(--ic-accent,#E0A33C) 75%, var(--text,#e6e9ef));background:rgba(10,11,14,0.72);padding:0 4px;border-radius:3px;}",
      ".ic-xaxis{position:absolute;left:46px;right:4px;bottom:0;height:20px;pointer-events:none;}",
      ".ic-xlabel{position:absolute;transform:translateX(-50%);font-family:'Space Grotesk',sans-serif;font-size:10px;font-weight:500;color:var(--text-dim,#8a909c);font-variant-numeric:tabular-nums;white-space:nowrap;}",
      ".ic-crosshair{position:absolute;top:0;bottom:0;width:1px;background:linear-gradient(var(--ic-accent,#E0A33C),rgba(224,163,60,0));opacity:0;transform:translateX(-0.5px);transition:opacity .12s ease;pointer-events:none;}",
      ".ic-dot{position:absolute;width:9px;height:9px;border-radius:50%;background:var(--ic-accent,#E0A33C);box-shadow:0 0 0 3px color-mix(in srgb, var(--ic-accent,#E0A33C) 20%, transparent);transform:translate(-50%,-50%);pointer-events:none;}",
      ".ic-tip{position:absolute;transform:translate(-50%,calc(-100% - 12px));background:#15171c;border:1px solid var(--border,#2a2d34);border-radius:8px;padding:5px 9px;line-height:1.25;white-space:nowrap;box-shadow:0 6px 20px rgba(0,0,0,0.45);opacity:0;transition:opacity .12s ease;pointer-events:none;z-index:2;}",
      ".ic-tip.ic-tip--below{transform:translate(-50%,12px);}",
      ".ic-tip-val{display:block;font-family:'Space Grotesk',sans-serif;font-size:12.5px;font-weight:700;font-variant-numeric:tabular-nums;color:var(--text,#e6e9ef);}",
      ".ic-tip-date{display:block;font-family:'Space Grotesk',sans-serif;font-size:10.5px;color:var(--text-dim,#8a909c);font-variant-numeric:tabular-nums;}",
      ".ic-card.is-active .ic-crosshair,.ic-card.is-active .ic-tip{opacity:1;}",
      ".ic-hit{position:absolute;inset:0;cursor:crosshair;touch-action:pan-y;}",
      ".ic-msg{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;color:var(--text-dim,#8a909c);font-family:'Mulish',sans-serif;font-size:0.9rem;}",
      ".ic-card[data-state='ready'] .ic-msg{display:none;}",
      ".ic-card[data-state='loading'] .ic-controls,.ic-card[data-state='error'] .ic-controls{visibility:hidden;}",
      "@media (max-width:640px){.ic-plotwrap{height:248px;}.ic-value{font-size:1.32rem;}.ic-range-btn,.ic-mode-btn{padding:4px 7px;}}",
      "@media print{.ic-card{break-inside:avoid;}.ic-crosshair,.ic-tip,.ic-hit,.ic-controls{display:none;}}"
    ].join('');
    var s = document.createElement('style');
    s.id = STYLE_ID; s.textContent = css;
    document.head.appendChild(s);
  }

  // ============================================================
  function IndexChart(mount, opts) {
    this.mount = typeof mount === 'string' ? document.getElementById(mount) : mount;
    this.opts = opts || {};
    this.seriesKey = this.opts.seriesKey;
    this.accent = this.opts.accent || '#E0A33C';
    this.source = this.opts.source || DEFAULT_SOURCE;
    this.range = DEFAULT_RANGE;
    this.mode = 'value';            // 'value' | 'pct'
    if (!this.mount || !this.seriesKey) return;
    ensureStyles();
    this._build();
    this._load();
  }

  // ---- scaffold: header + controls + plot frame, loading state ----
  IndexChart.prototype._build = function () {
    var card = el('div', 'ic-card');
    card.setAttribute('data-state', 'loading');
    card.style.setProperty('--ic-accent', this.accent);

    var name = this.opts.name || this.seriesKey, code = this.opts.code || '';
    card.appendChild(el('div', 'ic-head',
      '<div class="ic-id"><span class="ic-name">' + esc(name) + '</span>' +
      (code ? '<span class="ic-code">' + esc(code) + '</span>' : '') + '</div>' +
      '<div class="ic-readout"><span class="ic-value">&mdash;</span><span class="ic-change"></span></div>'));

    var ranges = RANGES.map(function (r) {
      return '<button type="button" class="ic-range-btn" data-d="' + r.d + '">' + r.l + '</button>';
    }).join('');
    card.appendChild(el('div', 'ic-controls',
      '<div class="ic-ranges" role="group" aria-label="Time range">' + ranges + '</div>' +
      '<div class="ic-modes" role="group" aria-label="Value or percentage">' +
        '<button type="button" class="ic-mode-btn" data-mode="value">Value</button>' +
        '<button type="button" class="ic-mode-btn" data-mode="pct">%</button>' +
      '</div>'));

    var wrap = el('div', 'ic-plotwrap');
    wrap.innerHTML =
      '<div class="ic-yaxis"></div>' +
      '<div class="ic-canvas">' +
        '<div class="ic-svg-mount"></div>' +
        '<div class="ic-crosshair"></div>' +
        '<div class="ic-dot" style="display:none"></div>' +
        '<div class="ic-tip"><span class="ic-tip-val"></span><span class="ic-tip-date"></span></div>' +
        '<div class="ic-hit"></div>' +
      '</div>' +
      '<div class="ic-xaxis"></div>' +
      '<div class="ic-msg">Loading live series&hellip;</div>';
    card.appendChild(wrap);

    this.mount.innerHTML = '';
    this.mount.appendChild(card);

    this._card = card;
    this._yaxis = wrap.querySelector('.ic-yaxis');
    this._canvas = wrap.querySelector('.ic-canvas');
    this._svgMount = wrap.querySelector('.ic-svg-mount');
    this._xaxis = wrap.querySelector('.ic-xaxis');
    this._crosshair = wrap.querySelector('.ic-crosshair');
    this._dot = wrap.querySelector('.ic-dot');
    this._tip = wrap.querySelector('.ic-tip');
    this._tipVal = wrap.querySelector('.ic-tip-val');
    this._tipDate = wrap.querySelector('.ic-tip-date');
    this._hit = wrap.querySelector('.ic-hit');
    this._msg = wrap.querySelector('.ic-msg');
    this._valueEl = card.querySelector('.ic-value');
    this._changeEl = card.querySelector('.ic-change');
  };

  IndexChart.prototype._fail = function () {
    this._card.setAttribute('data-state', 'error');
    if (this._msg) this._msg.textContent = 'Live series unavailable just now.';
  };

  // ---- load: live feed (keyed) + deep-history source it references ----
  IndexChart.prototype._load = function () {
    var self = this;
    var bust = (this.source.indexOf('?') >= 0 ? '&' : '?') + 'v=' + Date.now();
    fetch(this.source + bust)
      .then(function (r) { if (!r.ok) throw new Error('http ' + r.status); return r.json(); })
      .then(function (j) {
        var live = j && j.indexes && j.indexes[self.seriesKey];
        if (!live || !live.series || !live.series.length) throw new Error('no series');
        self.live = live;
        self.base = live.base || null;
        var srcPath = self.opts.fullSource ||
          (j._meta && j._meta.sources && j._meta.sources[self.seriesKey]);
        if (!srcPath) { self._ready(live.series); return; }
        var url = '/' + String(srcPath).replace(/^\//, '');
        return fetch(url + '?v=' + Date.now())
          .then(function (r) { return r.ok ? r.json() : null; })
          .then(function (sj) {
            var full = sj && sj.series && sj.series.length ? sj.series : live.series;
            self._ready(full);
          })
          .catch(function () { self._ready(live.series); });
      })
      .catch(function () { self._fail(); });
  };

  IndexChart.prototype._ready = function (full) {
    // normalise to {date, value, o:ordinal}; sort defensively
    this.full = full.map(function (p) { return { date: p.date, value: +p.value, o: ord(p.date) }; })
                    .filter(function (p) { return !isNaN(p.value); })
                    .sort(function (a, b) { return a.o - b.o; });
    if (this.full.length < 2) { this._fail(); return; }
    this._wire();
    this._dot.style.display = '';
    this._card.setAttribute('data-state', 'ready');
    this._draw();
  };

  // ---- windowing ----
  IndexChart.prototype._window = function () {
    var full = this.full, last = full[full.length - 1].o, cut = last - this.range;
    var i = 0; while (i < full.length && full[i].o < cut) i++;
    if (i > 0) i--;                       // include the nearest-prior anchor
    var w = full.slice(i);
    return w.length >= 2 ? w : full.slice(-2);
  };

  // ---- draw everything for the current range + mode ----
  IndexChart.prototype._draw = function () {
    var vis = this._window();
    var n = vis.length, self = this, pct = this.mode === 'pct';
    var v0 = vis[0].value || 1;

    // plotted points: y is value or rebased %
    this.pts = vis.map(function (p) {
      return { date: p.date, value: p.value, pct: (p.value - v0) / v0 * 100 };
    });
    var ys = this.pts.map(function (p) { return pct ? p.pct : p.value; });
    var dMin = Math.min.apply(null, ys), dMax = Math.max.apply(null, ys);
    if (pct) { dMin = Math.min(dMin, 0); dMax = Math.max(dMax, 0); }     // % always includes 0

    var nt = niceTicks(dMin, dMax, 5);
    this.yMin = nt.min; this.yMax = nt.max;
    var span = (this.yMax - this.yMin) || 1;
    function yFrac(y) { return (1 - (y - self.yMin) / span) * 100; }     // 0..100 within canvas
    this._yFrac = yFrac;

    // ---- SVG line + area (viewBox units, stretched to fill canvas) ----
    function X(i) { return (i / (n - 1)) * VB_W; }
    function Yv(y) { return (1 - (y - self.yMin) / span) * VB_H; }
    var line = this.pts.map(function (p, i) { return X(i).toFixed(1) + ',' + Yv(pct ? p.pct : p.value).toFixed(1); }).join(' ');
    var area = '0,' + VB_H + ' ' + line + ' ' + VB_W + ',' + VB_H;
    var gid = 'ic-grad-' + this.seriesKey;
    this._svgMount.innerHTML =
      '<svg class="ic-svg" viewBox="0 0 ' + VB_W + ' ' + VB_H + '" preserveAspectRatio="none" role="img" ' +
        'aria-label="' + esc((this.opts.name || this.seriesKey) + ', ' +
          (RANGES.filter(function (r) { return r.d === self.range; })[0] || { l: '' }).l +
          ', ' + (pct ? 'percentage change' : 'index value') + '.') + '">' +
        '<defs><linearGradient id="' + gid + '" x1="0" y1="0" x2="0" y2="1">' +
          '<stop offset="0%" stop-color="' + this.accent + '" stop-opacity="0.22"/>' +
          '<stop offset="100%" stop-color="' + this.accent + '" stop-opacity="0"/></linearGradient></defs>' +
        '<polygon points="' + area + '" fill="url(#' + gid + ')" stroke="none"/>' +
        '<polyline points="' + line + '" fill="none" stroke="' + this.accent + '" stroke-width="2" ' +
          'stroke-linejoin="round" stroke-linecap="round" vector-effect="non-scaling-stroke"/>' +
      '</svg>';

    // ---- gridlines + y-axis labels ----
    var grid = '', ylab = '';
    nt.ticks.forEach(function (t) {
      var f = yFrac(t);
      if (f < -0.5 || f > 100.5) return;
      grid += '<div class="ic-grid" style="top:' + f.toFixed(2) + '%"></div>';
      ylab += '<div class="ic-ylabel" style="top:' + f.toFixed(2) + '%">' +
        (pct ? (t > 0 ? '+' : '') + Math.round(t) + '%' : fmtNum(t, 0)) + '</div>';
    });
    // base-1,000 line (value mode only, when in range)
    var baseHtml = '';
    if (!pct && this.base && this.base.value != null) {
      var bf = yFrac(this.base.value);
      if (bf >= 0 && bf <= 100) {
        baseHtml = '<div class="ic-baseline" style="top:' + bf.toFixed(2) + '%">' +
          '<span class="ic-baseline-tag">' + fmtNum(this.base.value, 0) + ' base</span></div>';
      }
    }
    // gridlines + baseline live in the canvas, behind the svg-driven overlays
    var old = this._canvas.querySelectorAll('.ic-grid,.ic-baseline');
    for (var k = 0; k < old.length; k++) old[k].remove();
    this._canvas.insertAdjacentHTML('afterbegin', grid + baseHtml);
    this._yaxis.innerHTML = ylab;

    // ---- x-axis date labels (~4 across) ----
    var xn = Math.min(4, n), xlab = '';
    for (var xi = 0; xi < xn; xi++) {
      var idx = Math.round(xi / (xn - 1) * (n - 1));
      var f2 = (idx / (n - 1)) * 100;
      xlab += '<div class="ic-xlabel" style="left:' + f2.toFixed(2) + '%;transform:translateX(' +
        (xi === 0 ? '0' : xi === xn - 1 ? '-100%' : '-50%') + ')">' +
        fmtDateShort(this.pts[idx].date, this.range) + '</div>';
    }
    this._xaxis.innerHTML = xlab;

    // ---- header: current level (absolute) + period return for this window ----
    var lastP = this.pts[n - 1], first = this.pts[0];
    this._valueEl.textContent = fmtNum(this.live ? this.live.value : lastP.value);
    var ret = (lastP.value - first.value) / first.value * 100;
    var rl = (RANGES.filter(function (r) { return r.d === self.range; })[0] || { l: '' }).l;
    var up = ret >= 0;
    this._changeEl.textContent = (up ? '+' : '') + ret.toFixed(2) + '% · ' + rl;
    this._changeEl.className = 'ic-change ' + (up ? 'up' : 'down');

    this._pos(n - 1);   // park marker on the latest visible point
  };

  // position crosshair + marker + tooltip at a visible index (percentages)
  IndexChart.prototype._pos = function (idx) {
    var n = this.pts.length, p = this.pts[idx], pct = this.mode === 'pct';
    var xFrac = (n > 1 ? idx / (n - 1) : 0.5) * 100;
    var yFrac = this._yFrac(pct ? p.pct : p.value);
    this._crosshair.style.left = xFrac + '%';
    this._dot.style.left = xFrac + '%';
    this._dot.style.top = yFrac + '%';
    this._tipVal.textContent = pct ? fmtPct(p.pct) : fmtNum(p.value);
    this._tipDate.textContent = pct ? (fmtDate(p.date) + ' · ' + fmtNum(p.value)) : fmtDate(p.date);
    this._tip.classList.toggle('ic-tip--below', yFrac < 24);
    this._tip.style.top = yFrac + '%';
    var pw = this._canvas.clientWidth || 1;
    var halfFrac = ((this._tip.offsetWidth / 2 + 4) / pw) * 100;
    this._tip.style.left = Math.max(halfFrac, Math.min(100 - halfFrac, xFrac)) + '%';
  };

  IndexChart.prototype._track = function (clientX) {
    var rect = this._canvas.getBoundingClientRect();
    if (!rect.width) return;
    var n = this.pts.length, frac = (clientX - rect.left) / rect.width;
    frac = frac < 0 ? 0 : frac > 1 ? 1 : frac;
    this._pos(Math.round(frac * (n - 1)));
    this._card.classList.add('is-active');
  };
  IndexChart.prototype._leave = function () {
    this._card.classList.remove('is-active');
    if (this.pts) this._pos(this.pts.length - 1);
  };

  IndexChart.prototype._wire = function () {
    var self = this;
    // range tabs
    this._card.querySelectorAll('.ic-range-btn').forEach(function (b) {
      b.classList.toggle('is-active', +b.dataset.d === self.range);
      b.addEventListener('click', function () {
        self.range = +b.dataset.d;
        self._card.querySelectorAll('.ic-range-btn').forEach(function (x) {
          x.classList.toggle('is-active', x === b);
        });
        self._draw();
      });
    });
    // value / % toggle
    this._card.querySelectorAll('.ic-mode-btn').forEach(function (b) {
      b.classList.toggle('is-active', b.dataset.mode === self.mode);
      b.addEventListener('click', function () {
        self.mode = b.dataset.mode;
        self._card.querySelectorAll('.ic-mode-btn').forEach(function (x) {
          x.classList.toggle('is-active', x === b);
        });
        self._draw();
      });
    });
    // pointer + touch crosshair
    var hit = this._hit;
    hit.addEventListener('pointermove', function (e) { self._track(e.clientX); });
    hit.addEventListener('pointerdown', function (e) { self._track(e.clientX); });
    hit.addEventListener('pointerleave', function () { self._leave(); });
    hit.addEventListener('pointercancel', function () { self._leave(); });
    hit.addEventListener('pointerup', function (e) { if (e.pointerType === 'touch') self._leave(); });
    // resize: percentage geometry is self-correcting; just re-park + hide cursor
    self._onResize = function () { self._leave(); };
    global.addEventListener('resize', self._onResize);
  };

  IndexChart.mount = function (mountEl, opts) { return new IndexChart(mountEl, opts); };
  global.IndexChart = IndexChart;
})(window);
