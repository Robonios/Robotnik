// ═══════════════════════════════════════════════════════════
// FRONTIER ASSET PROFILE — per-entity nine-layer renderer
// Derives the slug from the page path, fetches the shard at
// /data/assets/{slug}.json, and renders the nine layers in order.
// Layers 1-2 (identity, classification) are open; layers 3-9 are
// badged "Research preview". Honest states render as labelled
// placeholders (Unrated, Unmapped, Forthcoming); nothing is invented.
// No raw vendor field is present in a shard, so none can be shown.
// ═══════════════════════════════════════════════════════════
(function () {
  'use strict';

  // ── one-time injected styles (reuses existing design tokens) ──
  var STYLE_ID = 'asset-profile-styles';
  function injectStyles() {
    if (document.getElementById(STYLE_ID)) return;
    var css = [
      '.ap-wrap{max-width:760px;margin:0 auto;padding:0 1rem;}',
      '.ap-preview{font-family:var(--font,monospace);font-size:9px;letter-spacing:0.1em;text-transform:uppercase;color:var(--text-muted,#5A6178);border:1px solid var(--border,#2A2F3A);border-radius:2px;padding:3px 8px;display:inline-block;margin-bottom:1rem;}',
      '.ap-header{border-bottom:1px solid var(--border,#2A2F3A);padding-bottom:1rem;margin-bottom:1.5rem;}',
      '.ap-name{font-family:var(--font,monospace);font-size:1.5rem;font-weight:700;color:var(--text,#e6e9ef);line-height:1.15;}',
      '.ap-sub{color:var(--text-dim,#9AA3B2);font-size:11px;margin-top:0.4rem;letter-spacing:0.03em;}',
      '.ap-section{background:var(--bg-card,#12151C);border:1px solid var(--border,#2A2F3A);border-radius:6px;padding:0.9rem 1.15rem;margin-bottom:0.85rem;}',
      '.ap-shead{display:flex;align-items:center;justify-content:space-between;gap:0.75rem;margin-bottom:0.6rem;}',
      '.ap-stitle{font-family:var(--font,monospace);font-size:11px;font-weight:700;letter-spacing:0.09em;text-transform:uppercase;color:var(--yellow,#F5D921);}',
      '.ap-badge{font-size:8px;letter-spacing:0.08em;text-transform:uppercase;color:#5A6178;border:1px solid var(--border,#2A2F3A);border-radius:2px;padding:2px 6px;white-space:nowrap;}',
      '.ap-row{display:flex;gap:1rem;padding:0.32rem 0;border-bottom:1px solid rgba(255,255,255,0.04);font-size:11px;line-height:1.55;}',
      '.ap-row:last-child{border-bottom:none;}',
      '.ap-label{flex:0 0 36%;color:var(--text-dim,#9AA3B2);}',
      '.ap-value{flex:1;color:var(--text,#e6e9ef);}',
      '.ap-muted{color:var(--text-muted,#5A6178);}',
      '.ap-state{display:inline-block;font-size:9px;letter-spacing:0.06em;text-transform:uppercase;color:var(--text-muted,#5A6178);background:rgba(255,255,255,0.03);border:1px solid var(--border,#2A2F3A);border-radius:2px;padding:1px 6px;}',
      '.ap-rating{font-weight:700;letter-spacing:0.04em;}',
      '.ap-rating.critical,.ap-rating.high{color:var(--red,#F87171);}',
      '.ap-rating.medium{color:var(--yellow,#F5D921);}',
      '.ap-rating.low{color:var(--green,#4ADE80);}',
      '.ap-notes{font-size:11px;line-height:1.7;color:var(--text-dim,#9AA3B2);}',
      '.ap-note{font-size:10px;line-height:1.5;color:var(--text-muted,#5A6178);margin-top:0.4rem;}',
      '.ap-fail{max-width:760px;margin:3rem auto;text-align:center;color:var(--text-dim,#9AA3B2);font-size:12px;}'
    ].join('');
    var el = document.createElement('style');
    el.id = STYLE_ID; el.textContent = css;
    document.head.appendChild(el);
  }

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function row(label, value) {
    var v = (value == null || value === '') ? '<span class="ap-muted">Not available</span>' : value;
    return '<div class="ap-row"><div class="ap-label">' + esc(label) + '</div><div class="ap-value">' + v + '</div></div>';
  }
  function muted(t) { return '<span class="ap-muted">' + esc(t) + '</span>'; }
  function state(t) { return '<span class="ap-state">' + esc(t) + '</span>'; }
  function bandLabel(b) {
    if (!b) return null;
    if (b === '5-capped') return 'At the 5% single-name cap';
    return esc(b) + '% of sector index';
  }

  // ── nine layer renderers (identity + classification open; rest badged) ──
  function rIdentity(d) {
    var id = d.identity || {}, ids = id.identifiers || {};
    var bits = [];
    if (ids.ticker) bits.push('Ticker ' + esc(ids.ticker));
    if (ids.coingecko_id) bits.push('CoinGecko ' + esc(ids.coingecko_id));
    if (ids.cik) bits.push('SEC CIK ' + esc(ids.cik));
    return row('Name', esc(id.name))
      + row('Aliases', (id.aliases && id.aliases.length) ? esc(id.aliases.join(', ')) : null)
      + row('Type', esc((id.type || '').charAt(0).toUpperCase() + (id.type || '').slice(1)))
      + row('Lifecycle', esc(id.lifecycle_status))
      + row('Identifiers', bits.length ? bits.join(' &middot; ') : muted('None on record'))
      + row('Description', id.description ? esc(id.description) : state('Forthcoming'));
  }
  function rClassification(d) {
    var c = d.classification || {};
    var US = { index_constituent: 'Index constituent', active_private: 'Private (tracked)', active_token: 'Token (isolated)' };
    return row('Sector', esc(c.sector))
      + row('Subsector', c.subsector ? esc(c.subsector) : muted('Unclassified'))
      + row('Value-chain tier', c.value_chain ? esc(c.value_chain) : muted('Unclassified'))
      + row('Universe status', esc(US[c.universe_status] || c.universe_status));
  }
  function rBottleneck(d) {
    var b = d.bottleneck || {};
    if (b.state !== 'rated') return row('Control-point rating', state('Unrated'));
    var r = String(b.rating || '').toLowerCase();
    var pill = '<span class="ap-rating ' + r + '">' + esc(b.rating) + '</span>';
    return row('Control-point rating', pill)
      + row('Assessment', b.description ? esc(b.description) : muted('Not available'))
      + row('Confidence', b.confidence ? esc(b.confidence) : muted('Not available'));
  }
  function rDependency(d) {
    var dep = d.dependency || {};
    if (dep.state !== 'mapped') return row('Supply-chain map', state('Unmapped'));
    return row('Key customers', dep.key_customers ? esc(dep.key_customers) : muted('Not available'))
      + row('Key suppliers', dep.key_suppliers ? esc(dep.key_suppliers) : muted('Not available'));
  }
  function rMarket(d) {
    var m = d.market_context || {};
    if (m.state === 'live') {
      return row('Membership', 'Index constituent')
        + row('Sector index', esc(m.sector_index))
        + row('Weight band', m.weight_band ? bandLabel(m.weight_band) : muted('Not available'))
        + row('Sector rank', (m.sector_rank != null) ? 'No. ' + esc(m.sector_rank) + ' by weight' : muted('Not available'));
    }
    if (m.state === 'token_isolated') {
      return row('Membership', state('Token isolated'))
        + '<div class="ap-note">Tokens are held as a research watchlist and never enter an equity index.</div>';
    }
    if (m.state === 'private_capital_index') {
      return row('Membership', 'Private')
        + row('Coverage', 'Robotnik Private Capital Index');
    }
    return row('Membership', muted('Not available'));
  }
  function rCapital(d) {
    var cap = d.capital || {};
    if (cap.state === 'live') {
      return row('Last round', cap.last_round ? esc(cap.last_round) : muted('Not available'))
        + row('Total raised', (cap.total_raised_m != null) ? '$' + esc(cap.total_raised_m) + 'm' : muted('Not available'));
    }
    if (cap.state === 'sparse') {
      return row('Last round', cap.last_round ? esc(cap.last_round) : muted('Not available'))
        + row('Total raised', state('Amount undisclosed'));
    }
    return row('Capital structure', state('Forthcoming'));
  }
  function rPolicy() { return row('Policy exposure', state('Forthcoming')); }
  function rGeographic(d) {
    var g = d.geographic || {};
    return row('Headquarters country', g.hq_country ? esc(g.hq_country) : muted('Not available'))
      + row('Headquarters city', g.hq_city ? esc(g.hq_city) : muted('Not available'))
      + row('Supply-chain exposure', state('Forthcoming'));
  }
  function rEditorial(d) {
    var ed = d.editorial || {};
    if (ed.notes) return '<div class="ap-notes">' + esc(ed.notes) + '</div>';
    return row('Analyst notes', state('Forthcoming'));
  }

  var SECTIONS = [
    { title: 'Identity', preview: false, fn: rIdentity },
    { title: 'Classification', preview: false, fn: rClassification },
    { title: 'Bottleneck exposure', preview: true, fn: rBottleneck },
    { title: 'Dependencies', preview: true, fn: rDependency },
    { title: 'Market context', preview: true, fn: rMarket },
    { title: 'Capital structure', preview: true, fn: rCapital },
    { title: 'Policy', preview: true, fn: rPolicy },
    { title: 'Geography', preview: true, fn: rGeographic },
    { title: 'Editorial', preview: true, fn: rEditorial }
  ];

  function render(mount, d) {
    var id = d.identity || {}, c = d.classification || {};
    var typeLabel = { public: 'Public', private: 'Private', token: 'Token' }[id.type] || id.type;
    var sub = [];
    if (id.identifiers && id.identifiers.ticker) sub.push(esc(id.identifiers.ticker));
    if (c.sector) sub.push(esc(c.sector));
    if (typeLabel) sub.push(esc(typeLabel));

    var html = '<div class="ap-wrap">'
      + '<div class="ap-preview">Research preview</div>'
      + '<div class="ap-header"><div class="ap-name">' + esc(id.name || d.meta.id) + '</div>'
      + '<div class="ap-sub">' + sub.join(' &middot; ') + '</div></div>';

    for (var i = 0; i < SECTIONS.length; i++) {
      var s = SECTIONS[i];
      var badge = s.preview ? '<span class="ap-badge">Research preview</span>' : '';
      html += '<div class="ap-section"><div class="ap-shead"><div class="ap-stitle">' + esc(s.title) + '</div>' + badge + '</div>'
        + s.fn(d) + '</div>';
    }
    html += '</div>';
    mount.innerHTML = html;
  }

  function slugFromPath() {
    var seg = (location.pathname || '').split('/').filter(Boolean).pop() || '';
    return seg.replace(/\.html?$/i, '');
  }

  function boot() {
    var mount = document.getElementById('asset-profile');
    if (!mount) return;
    injectStyles();
    var slug = slugFromPath();
    if (!slug) { mount.innerHTML = '<div class="ap-fail">No asset specified.</div>'; return; }
    fetch('/data/assets/' + encodeURIComponent(slug) + '.json?v=' + Date.now())
      .then(function (r) { if (!r.ok) throw new Error('shard ' + r.status); return r.json(); })
      .then(function (d) { render(mount, d); })
      .catch(function (e) {
        mount.innerHTML = '<div class="ap-fail">Profile not available yet for <strong>' + esc(slug) + '</strong>.</div>';
        if (window.console) console.warn('[asset-profile]', e);
      });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
