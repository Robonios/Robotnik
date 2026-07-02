/* ============================================================
   ROBOTNIK — Frontier Conditions Index (RFCI) component
   Data-bound diagram-and-table for research/frontier-conditions-index.
   Reads /data/frontier_conditions.json and renders:
     (a) a row of four component-score boxes for the latest month
     (b) a -100/+100 diffusion thermometer with a marker at the total
     (c) a history table, one row per month (newest first)
   When the data file has no readings it renders a graceful
   "first reading pending" state and never throws. All ids/classes are
   fc- prefixed (collision-safe). Standalone; NOT an IndexChart.
   Styling lives in the page <style> (hardcoded brand hexes); this module
   only fetches the data and builds the DOM.
   ============================================================ */
(function () {
  'use strict';

  var COMPONENTS = [
    { key: 'equity_breadth',   label: 'Equity breadth' },
    { key: 'sector_breadth',   label: 'Sector breadth' },
    { key: 'private_capital',  label: 'Private capital' },
    { key: 'commodity_stress', label: 'Commodity stress' }
  ];
  var MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  // signed integer on the -100..100 scale; en-dash for negatives, em-dash for missing
  function signed(n) {
    if (n == null || isNaN(n)) return '—';
    var r = Math.round(n);
    return r > 0 ? '+' + r : r < 0 ? '−' + Math.abs(r) : '0';
  }
  function fmtMonth(m) {
    if (!m || typeof m !== 'string') return '—';
    var p = m.split('-');
    var i = parseInt(p[1], 10) - 1;
    return (MONTHS[i] || p[1] || '') + ' ' + (p[0] || '');
  }
  // -100..100 -> 0..100 (%) for the marker position
  function markerPct(total) {
    var t = Math.max(-100, Math.min(100, Number(total)));
    return (t + 100) / 2;
  }

  function thermometer(total) {
    var marker = (total != null && !isNaN(total))
      ? '<div class="fc-thermo-marker" style="left:' + markerPct(total).toFixed(1) + '%"></div>'
      : '';
    return '<div class="fc-thermo">' +
      '<div class="fc-thermo-track">' + marker + '</div>' +
      '<div class="fc-thermo-scale"><span>−100 deteriorating</span><span>0 neutral</span><span>+100 improving</span></div>' +
      '</div>';
  }

  function render(root, data) {
    var readings = (data && Array.isArray(data.readings)) ? data.readings.slice() : [];
    // newest first
    readings.sort(function (a, b) { return a.month < b.month ? 1 : a.month > b.month ? -1 : 0; });
    var latest = readings.length ? readings[0] : null;

    var html = '<div class="fc-wrap">';

    if (!latest) {
      // graceful empty state — no fabricated scores
      html += '<div class="fc-empty">' +
        '<div class="fc-empty-badge">First reading pending</div>' +
        '<p class="fc-empty-note">The Frontier Conditions Index publishes its first monthly reading once all four components are available. No reading has been computed yet.</p>' +
        '</div>' +
        thermometer(null) +
        '</div>';
      root.innerHTML = html;
      return;
    }

    // (a) component boxes — latest month
    html += '<div class="fc-boxes">';
    COMPONENTS.forEach(function (c) {
      html += '<div class="fc-box"><div class="fc-box-label">' + esc(c.label) + '</div>' +
        '<div class="fc-box-score">' + signed(latest[c.key]) + '</div></div>';
    });
    html += '</div>';

    // (b) thermometer with a marker at the total
    html += thermometer(latest.total);

    // total readout
    html += '<p class="fc-total-line">Total for ' + esc(fmtMonth(latest.month)) + ': ' +
      '<strong>' + signed(latest.total) + '</strong> ' +
      '<span class="fc-total-sub">(equal-weighted average of the four)</span></p>';

    // (c) history table
    html += '<div class="fc-table-wrap"><table class="fc-table"><thead><tr>' +
      '<th scope="col">Month</th><th scope="col">Total</th>';
    COMPONENTS.forEach(function (c) { html += '<th scope="col">' + esc(c.label) + '</th>'; });
    html += '</tr></thead><tbody>';
    readings.forEach(function (r) {
      html += '<tr><td>' + esc(fmtMonth(r.month)) + '</td>' +
        '<td class="fc-td-total">' + signed(r.total) + '</td>';
      COMPONENTS.forEach(function (c) { html += '<td>' + signed(r[c.key]) + '</td>'; });
      html += '</tr>';
    });
    html += '</tbody></table></div></div>';

    root.innerHTML = html;
  }

  function boot() {
    var root = document.getElementById('fc-root');
    if (!root) return;
    fetch('/data/frontier_conditions.json', { cache: 'no-store' })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) { render(root, data); })
      .catch(function () { render(root, null); }); // network/parse failure -> empty state, never break
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
