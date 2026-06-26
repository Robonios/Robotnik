/* ============================================================
   INDEX CHART — reusable live time-series line chart
   ------------------------------------------------------------
   A self-contained, interactive index chart for the Robotnik
   index family. Reads a named series from the live index feed
   (index_summary.json by default) and renders a dark-theme line
   chart with area fill, a header readout, and a pointer/touch
   crosshair that reads back the value and date at any point.

   Keyed by series + accent so every index detail page (R4 first,
   R5–R8 next) mounts its own without forking the component.

   Visual language reused from the Frontier Stack flagship:
     - preserveAspectRatio="none" + vector-effect non-scaling-stroke
       for a crisp, resolution-independent line (the sparkline trick);
     - the marker dot lives in an HTML overlay (CSS px), never a
       scaled <circle>, so it stays a true circle under non-uniform
       stretch — and the crosshair survives resize because positions
       are expressed as percentages, recomputed only for hit-testing.

   Public API:
     new IndexChart(mountEl, {
       seriesKey: 'bottleneck',          // key under index_summary.indexes
       accent:    '#E0A33C',             // line / fill / marker colour
       name:      'Robotnik …',          // header label (defaults to feed name)
       code:      'RBWC',                // optional ticker-style code
       source:    '/data/index/index_summary.json'   // optional override
     });
   ============================================================ */
(function (global) {
  'use strict';

  var DEFAULT_SOURCE = '/data/index/index_summary.json';
  var STYLE_ID = 'index-chart-styles';

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
  function fmtDate(s) {
    if (!s) return '';
    var d = new Date(s + 'T00:00:00Z');
    if (isNaN(d.getTime())) return s;
    return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' });
  }

  // ---- one-time injected stylesheet (accent is per-instance via --ic-accent) ----
  function ensureStyles() {
    if (document.getElementById(STYLE_ID)) return;
    var css =
      '.ic-card{border:1px solid var(--border,#23262d);border-radius:14px;background:rgba(255,255,255,0.015);padding:1.05rem 1.2rem 0.85rem;}' +
      '.ic-head{display:flex;align-items:flex-start;justify-content:space-between;gap:1rem;}' +
      '.ic-id{display:flex;flex-direction:column;gap:3px;min-width:0;}' +
      ".ic-name{font-family:'Space Grotesk',sans-serif;font-size:12.5px;font-weight:600;color:var(--text,#e6e9ef);}" +
      ".ic-code{font-family:'Space Grotesk',sans-serif;font-size:10px;font-weight:500;letter-spacing:0.18em;text-transform:uppercase;color:var(--text-dim,#8a909c);}" +
      '.ic-readout{text-align:right;white-space:nowrap;}' +
      ".ic-value{display:block;font-family:'Space Grotesk',sans-serif;font-size:1.55rem;font-weight:700;font-variant-numeric:tabular-nums;color:var(--text,#e6e9ef);line-height:1.05;}" +
      ".ic-change{font-family:'Space Grotesk',sans-serif;font-size:12px;font-weight:600;font-variant-numeric:tabular-nums;color:var(--text-dim,#8a909c);}" +
      '.ic-change.up{color:#46d39a;}.ic-change.down{color:#ef6a6a;}' +
      '.ic-plot{position:relative;height:240px;margin:0.55rem 0 0.3rem;touch-action:pan-y;}' +
      '.ic-svg{position:absolute;inset:0;width:100%;height:100%;display:block;}' +
      '.ic-crosshair{position:absolute;top:0;bottom:0;width:1px;background:linear-gradient(var(--ic-accent,#E0A33C),rgba(224,163,60,0));opacity:0;transform:translateX(-0.5px);transition:opacity .12s ease;pointer-events:none;}' +
      '.ic-dot{position:absolute;width:9px;height:9px;border-radius:50%;background:var(--ic-accent,#E0A33C);box-shadow:0 0 0 3px color-mix(in srgb, var(--ic-accent,#E0A33C) 20%, transparent);transform:translate(-50%,-50%);pointer-events:none;}' +
      '.ic-tip{position:absolute;transform:translate(-50%,calc(-100% - 12px));background:#15171c;border:1px solid var(--border,#2a2d34);border-radius:8px;padding:5px 9px;line-height:1.25;white-space:nowrap;box-shadow:0 6px 20px rgba(0,0,0,0.45);opacity:0;transition:opacity .12s ease;pointer-events:none;}' +
      '.ic-tip.ic-tip--below{transform:translate(-50%,12px);}' +
      ".ic-tip-val{display:block;font-family:'Space Grotesk',sans-serif;font-size:12.5px;font-weight:700;font-variant-numeric:tabular-nums;color:var(--text,#e6e9ef);}" +
      ".ic-tip-date{display:block;font-family:'Space Grotesk',sans-serif;font-size:10.5px;color:var(--text-dim,#8a909c);font-variant-numeric:tabular-nums;}" +
      '.ic-card.is-active .ic-crosshair,.ic-card.is-active .ic-tip{opacity:1;}' +
      '.ic-hit{position:absolute;inset:0;cursor:crosshair;}' +
      '.ic-msg{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;color:var(--text-dim,#8a909c);font-family:\'Mulish\',sans-serif;font-size:0.9rem;}' +
      '.ic-axis{display:flex;justify-content:space-between;align-items:center;gap:0.5rem;font-family:\'Space Grotesk\',sans-serif;font-size:11px;color:var(--text-dim,#8a909c);font-variant-numeric:tabular-nums;}' +
      '.ic-axis-base{opacity:0.85;}' +
      '.ic-card[data-state="loading"] .ic-axis,.ic-card[data-state="error"] .ic-axis{visibility:hidden;}' +
      '.ic-card[data-state="ready"] .ic-msg{display:none;}' +
      '@media (max-width:640px){.ic-plot{height:200px;}.ic-value{font-size:1.32rem;}}' +
      '@media print{.ic-card{break-inside:avoid;}.ic-crosshair,.ic-tip,.ic-hit{display:none;}}';
    var s = document.createElement('style');
    s.id = STYLE_ID;
    s.textContent = css;
    document.head.appendChild(s);
  }

  // ============================================================
  function IndexChart(mount, opts) {
    this.mount = typeof mount === 'string' ? document.getElementById(mount) : mount;
    this.opts = opts || {};
    this.seriesKey = this.opts.seriesKey;
    this.accent = this.opts.accent || '#E0A33C';
    this.source = this.opts.source || DEFAULT_SOURCE;
    this.W = 720; this.H = 260; this.padT = 14; this.padB = 12;
    if (!this.mount || !this.seriesKey) return;
    ensureStyles();
    this._build();
    this._load();
  }

  IndexChart.prototype._yv = function (v) {
    return this.padT + (1 - (v - this.min) / this.span) * (this.H - this.padT - this.padB);
  };

  // ---- scaffold: header + plot + overlay + axis, in a loading state ----
  IndexChart.prototype._build = function () {
    var card = el('div', 'ic-card');
    card.setAttribute('data-state', 'loading');
    card.style.setProperty('--ic-accent', this.accent);

    var name = this.opts.name || this.seriesKey;
    var code = this.opts.code || '';
    card.appendChild(el('div', 'ic-head',
      '<div class="ic-id"><span class="ic-name">' + esc(name) + '</span>' +
      (code ? '<span class="ic-code">' + esc(code) + '</span>' : '') + '</div>' +
      '<div class="ic-readout"><span class="ic-value">&mdash;</span>' +
      '<span class="ic-change"></span></div>'));

    var plot = el('div', 'ic-plot');
    plot.innerHTML =
      '<div class="ic-svg-mount"></div>' +
      '<div class="ic-crosshair"></div>' +
      '<div class="ic-dot" style="display:none"></div>' +
      '<div class="ic-tip"><span class="ic-tip-val"></span><span class="ic-tip-date"></span></div>' +
      '<div class="ic-hit"></div>' +
      '<div class="ic-msg">Loading live series&hellip;</div>';
    card.appendChild(plot);
    card.appendChild(el('div', 'ic-axis', '<span class="ic-axis-l"></span><span class="ic-axis-base"></span><span class="ic-axis-r"></span>'));

    this.mount.innerHTML = '';
    this.mount.appendChild(card);

    this._card = card;
    this._plot = plot;
    this._svgMount = plot.querySelector('.ic-svg-mount');
    this._crosshair = plot.querySelector('.ic-crosshair');
    this._dot = plot.querySelector('.ic-dot');
    this._tip = plot.querySelector('.ic-tip');
    this._tipVal = plot.querySelector('.ic-tip-val');
    this._tipDate = plot.querySelector('.ic-tip-date');
    this._hit = plot.querySelector('.ic-hit');
    this._msg = plot.querySelector('.ic-msg');
  };

  IndexChart.prototype._load = function () {
    var self = this;
    var url = this.source + (this.source.indexOf('?') >= 0 ? '&' : '?') + 'v=' + Date.now();
    fetch(url)
      .then(function (r) { if (!r.ok) throw new Error('http ' + r.status); return r.json(); })
      .then(function (j) {
        var s = j && j.indexes && j.indexes[self.seriesKey];
        if (!s || !s.series || s.series.length < 2) throw new Error('no series');
        self.data = s;
        self.series = s.series;
        self._render();
      })
      .catch(function () { self._fail(); });
  };

  IndexChart.prototype._fail = function () {
    this._card.setAttribute('data-state', 'error');
    if (this._msg) this._msg.textContent = 'Live series unavailable just now.';
  };

  IndexChart.prototype._render = function () {
    var d = this.data, series = this.series, n = series.length;
    var vals = series.map(function (p) { return p.value; });
    this.min = Math.min.apply(null, vals);
    this.max = Math.max.apply(null, vals);
    this.span = (this.max - this.min) || 1;

    // header readout — current level + 1Y return (header stays static; the
    // tooltip is the live per-point readout)
    this._card.querySelector('.ic-value').textContent = fmtNum(d.value);
    var oneY = d.returns && d.returns['1Y'];
    var chg = this._card.querySelector('.ic-change');
    if (oneY != null && !isNaN(oneY)) {
      var up = oneY >= 0;
      chg.textContent = (up ? '+' : '') + Number(oneY).toFixed(2) + '% · 1Y';
      chg.className = 'ic-change ' + (up ? 'up' : 'down');
    }

    // SVG line + area in viewBox units (fills the plot via preserveAspectRatio=none)
    var W = this.W, H = this.H, self = this;
    function X(i) { return (i / (n - 1)) * W; }
    var pts = series.map(function (p, i) { return X(i).toFixed(1) + ',' + self._yv(p.value).toFixed(1); }).join(' ');
    var area = '0,' + H + ' ' + pts + ' ' + W + ',' + H;
    var gid = 'ic-grad-' + this.seriesKey;
    this._svgMount.innerHTML =
      '<svg class="ic-svg" viewBox="0 0 ' + W + ' ' + H + '" preserveAspectRatio="none" role="img" ' +
        'aria-label="' + esc((this.opts.name || d.name || 'Index') + ' over the past year, ending at ' + fmtNum(d.value) + ' on ' + fmtDate(d.as_of) + '.') + '">' +
        '<defs><linearGradient id="' + gid + '" x1="0" y1="0" x2="0" y2="1">' +
          '<stop offset="0%" stop-color="' + this.accent + '" stop-opacity="0.22"/>' +
          '<stop offset="100%" stop-color="' + this.accent + '" stop-opacity="0"/>' +
        '</linearGradient></defs>' +
        '<polygon points="' + area + '" fill="url(#' + gid + ')" stroke="none"/>' +
        '<polyline points="' + pts + '" fill="none" stroke="' + this.accent + '" stroke-width="2" ' +
          'stroke-linejoin="round" stroke-linecap="round" vector-effect="non-scaling-stroke"/>' +
      '</svg>';

    // axis: first date · base annotation · last date
    var base = d.base || {};
    this._card.querySelector('.ic-axis-l').textContent = fmtDate(series[0].date);
    this._card.querySelector('.ic-axis-base').textContent =
      'Base ' + fmtNum(base.value, 0) + ' · ' + fmtDate(base.date);
    this._card.querySelector('.ic-axis-r').textContent = fmtDate(series[n - 1].date);

    this._wire();
    this._dot.style.display = '';
    this._pos(n - 1);                 // park the marker on the latest point at rest
    this._card.setAttribute('data-state', 'ready');
  };

  // position crosshair + marker + tooltip at a data index (percentages =
  // resize-proof; only hit-testing needs live pixel geometry)
  IndexChart.prototype._pos = function (idx) {
    var n = this.series.length, pt = this.series[idx];
    var xFrac = (n > 1 ? idx / (n - 1) : 0.5) * 100;
    var yFrac = (this._yv(pt.value) / this.H) * 100;
    this._crosshair.style.left = xFrac + '%';
    this._dot.style.left = xFrac + '%';
    this._dot.style.top = yFrac + '%';
    this._tipVal.textContent = fmtNum(pt.value);
    this._tipDate.textContent = fmtDate(pt.date);
    // flip the tooltip below the point when near the top edge
    this._tip.classList.toggle('ic-tip--below', yFrac < 22);
    this._tip.style.top = yFrac + '%';
    // clamp the tooltip within the plot width
    var pw = this._plot.clientWidth || 1;
    var halfFrac = ((this._tip.offsetWidth / 2 + 4) / pw) * 100;
    var L = Math.max(halfFrac, Math.min(100 - halfFrac, xFrac));
    this._tip.style.left = L + '%';
  };

  IndexChart.prototype._track = function (clientX) {
    var rect = this._plot.getBoundingClientRect();
    if (!rect.width) return;
    var n = this.series.length;
    var frac = (clientX - rect.left) / rect.width;
    frac = frac < 0 ? 0 : frac > 1 ? 1 : frac;
    this._pos(Math.round(frac * (n - 1)));
    this._card.classList.add('is-active');
  };

  IndexChart.prototype._leave = function () {
    this._card.classList.remove('is-active');
    this._pos(this.series.length - 1);   // return the marker to the latest point
  };

  IndexChart.prototype._wire = function () {
    var self = this, hit = this._hit;
    hit.addEventListener('pointermove', function (e) { self._track(e.clientX); });
    hit.addEventListener('pointerdown', function (e) { self._track(e.clientX); });
    hit.addEventListener('pointerleave', function () { self._leave(); });
    hit.addEventListener('pointercancel', function () { self._leave(); });
    // touch: lifting the finger ends the scrub (mouse keeps the crosshair on hover)
    hit.addEventListener('pointerup', function (e) { if (e.pointerType === 'touch') self._leave(); });
    // resize: positions are percentage-based, so just re-park and hide the cursor
    self._onResize = function () { self._leave(); };
    global.addEventListener('resize', self._onResize);
  };

  IndexChart.mount = function (mountEl, opts) { return new IndexChart(mountEl, opts); };

  global.IndexChart = IndexChart;
})(window);
