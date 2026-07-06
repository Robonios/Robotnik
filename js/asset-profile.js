// ═══════════════════════════════════════════════════════════
// FRONTIER ASSET PROFILE — per-entity renderer (v2, editorial)
// Fetches /data/assets/{slug}.json and renders the locked nine
// layers. The value-chain spine leads: bottleneck (3) and dependency
// (4) first, then identity (1), classification (2), market context
// (5), then the Pro stack (6-9). Free layers render open; Pro layers
// render a legible teaser with the remainder under the site's
// .blurred-preview treatment and one honest upgrade CTA. Market
// context shows band and rank only, never a number. The dependency
// chart is data-driven from the shard's upstream/downstream edges.
// Schema 2.0 carries authored bodies; 1.0 shards degrade gracefully.
// ═══════════════════════════════════════════════════════════
(function () {
  'use strict';
  var FH = "'Space Grotesk','Roboto Mono',sans-serif";   // headings + numbers
  var FB = "'Mulish','Roboto Mono',sans-serif";           // body prose
  var FM = "var(--font,'Roboto Mono',monospace)";         // labels / chrome

  var STYLE_ID = 'asset-profile-styles-v2';
  function injectStyles() {
    if (document.getElementById(STYLE_ID)) return;
    var css = [
      '.ap-wrap{max-width:820px;margin:0 auto;padding:1.6rem 1rem 4rem;}',
      // header
      '.ap-eyebrow{font-family:' + FM + ';font-size:10px;letter-spacing:0.16em;text-transform:uppercase;color:var(--yellow,#F5D921);}',
      '.ap-name{font-family:' + FH + ';font-size:clamp(1.55rem,3vw,2.1rem);font-weight:700;color:var(--text,#e6e8ed);line-height:1.12;margin:0.35rem 0 0.4rem;}',
      '.ap-idline{font-family:' + FB + ';font-size:12.5px;color:var(--text-dim,#8b92a5);}',
      '.ap-chips{display:flex;flex-wrap:wrap;gap:0.4rem;margin-top:0.8rem;}',
      '.ap-chip{display:inline-flex;align-items:center;font-family:' + FM + ';font-size:9.5px;letter-spacing:0.06em;text-transform:uppercase;border:1px solid var(--border,#252a36);border-radius:3px;padding:3px 8px;color:var(--text-dim,#8b92a5);}',
      '.ap-chip.tier{background:var(--yellow-subtle,rgba(245,217,33,0.05));border-color:var(--yellow,#F5D921);color:var(--yellow,#F5D921);}',
      '.ap-chip.rating.critical,.ap-chip.rating.high{color:var(--red,#ef4444);border-color:rgba(239,68,68,0.5);}',
      '.ap-chip.rating.medium{color:var(--yellow,#F5D921);border-color:rgba(245,217,33,0.5);}',
      '.ap-chip.rating.low{color:var(--green,#22c55e);border-color:rgba(34,197,94,0.5);}',
      // epigraph (free Robotnik note)
      '.ap-epigraph{font-family:' + FB + ';font-size:14px;line-height:1.6;color:var(--text,#e6e8ed);border-left:2px solid var(--yellow,#F5D921);padding:0.3rem 0 0.3rem 0.9rem;margin:1.3rem 0 0.4rem;}',
      // chart
      '.ap-chart{background:var(--bg-raised,#161920);border:1px solid var(--border,#252a36);border-radius:10px;padding:0.6rem;margin:1.1rem 0 0.5rem;overflow-x:auto;}',
      '.ap-chart svg{display:block;width:100%;height:auto;min-width:660px;}',
      '.ap-chart .cx-up{fill:var(--blue,#3b82f6);font:600 10px ' + FM + ';letter-spacing:1px;}',
      '.ap-chart .cx-down{fill:var(--green,#22c55e);font:600 10px ' + FM + ';letter-spacing:1px;}',
      '.ap-chart .node{fill:#12151b;}',
      '.ap-chart .node-t{fill:var(--text,#e6e8ed);font:600 13px ' + FH + ';}',
      '.ap-chart .node-s{fill:var(--text-dim,#8b92a5);font:400 10.5px ' + FB + ';}',
      '.ap-chart .edge-up{stroke:var(--blue,#3b82f6);stroke-width:1.4;opacity:0.6;fill:none;}',
      '.ap-chart .edge-down{stroke:var(--green,#22c55e);stroke-width:1.4;opacity:0.6;fill:none;}',
      '.ap-chart .ent-box{fill:var(--yellow-glow,rgba(245,217,33,0.10));stroke:var(--yellow,#F5D921);stroke-width:2;}',
      '.ap-chart .ent-name{fill:var(--yellow,#F5D921);font:700 21px ' + FH + ';}',
      '.ap-chart .ent-tier{fill:var(--text,#e6e8ed);font:600 11px ' + FB + ';}',
      '.ap-chart .cp-pill{fill:var(--yellow-subtle,rgba(245,217,33,0.06));stroke:var(--yellow,#F5D921);stroke-dasharray:3 3;}',
      '.ap-chart .cp-text{fill:var(--yellow,#F5D921);font:600 10px ' + FM + ';letter-spacing:0.6px;}',
      '.ap-chart .tier{fill:#12151b;stroke:var(--border,#252a36);}',
      '.ap-chart .tier.on{fill:var(--yellow-glow,rgba(245,217,33,0.12));stroke:var(--yellow,#F5D921);}',
      '.ap-chart .tier-t{fill:var(--text-dim,#8b92a5);font:600 9px ' + FB + ';}',
      '.ap-chart .tier-t.on{fill:var(--yellow,#F5D921);font-weight:700;}',
      // sections
      '.ap-section{margin-top:1.6rem;padding-top:1.4rem;border-top:1px solid var(--border,#252a36);}',
      '.ap-section.first{border-top:none;padding-top:0.4rem;}',
      '.ap-shead{display:flex;align-items:baseline;justify-content:space-between;gap:0.75rem;margin-bottom:0.7rem;}',
      '.ap-stitle{font-family:' + FH + ';font-size:15px;font-weight:600;color:var(--text,#e6e8ed);}',
      '.ap-badge{font-family:' + FM + ';font-size:8.5px;letter-spacing:0.08em;text-transform:uppercase;border:1px solid var(--border,#252a36);border-radius:3px;padding:2px 7px;white-space:nowrap;}',
      '.ap-badge.free{color:var(--text-muted,#5a6178);}',
      '.ap-badge.pro{color:var(--yellow,#F5D921);border-color:rgba(245,217,33,0.4);}',
      '.ap-lead{font-family:' + FB + ';font-size:15px;font-weight:600;line-height:1.5;color:var(--text,#e6e8ed);margin:0 0 0.6rem;}',
      '.ap-body{font-family:' + FB + ';font-size:14px;line-height:1.75;color:var(--text-dim,#8b92a5);margin:0 0 0.5rem;}',
      // facts + edges
      '.ap-facts{display:grid;grid-template-columns:repeat(2,1fr);gap:0.4rem 1.2rem;margin:0.4rem 0 0.6rem;}',
      '.ap-fact{display:flex;justify-content:space-between;gap:0.6rem;border-bottom:1px solid rgba(255,255,255,0.04);padding:0.28rem 0;font-size:12px;}',
      '.ap-fact span{color:var(--text-muted,#5a6178);font-family:' + FM + ';font-size:10.5px;text-transform:uppercase;letter-spacing:0.04em;}',
      '.ap-fact b{color:var(--text,#e6e8ed);font-family:' + FB + ';font-weight:600;text-align:right;}',
      '.ap-edges{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-bottom:0.4rem;}',
      '.ap-edge-h{font-family:' + FM + ';font-size:9.5px;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:0.4rem;}',
      '.ap-edge-h.up{color:var(--blue,#3b82f6);}.ap-edge-h.down{color:var(--green,#22c55e);}',
      '.ap-edge{background:rgba(255,255,255,0.02);border:1px solid var(--border,#252a36);border-radius:4px;padding:0.45rem 0.6rem;margin-bottom:6px;}',
      '.ap-edge b{display:block;color:var(--text,#e6e8ed);font-family:' + FB + ';font-size:12.5px;font-weight:600;}',
      '.ap-edge span{color:var(--text-muted,#5a6178);font-family:' + FB + ';font-size:10.5px;}',
      '.ap-subhead{display:flex;align-items:center;gap:0.5rem;margin:1rem 0 0.5rem;font-family:' + FM + ';font-size:10px;letter-spacing:0.06em;text-transform:uppercase;color:var(--text-dim,#8b92a5);}',
      // market chips
      '.ap-market{display:flex;flex-wrap:wrap;gap:0.5rem;margin:0.2rem 0 0.5rem;}',
      '.ap-mchip{background:var(--bg-card,#1a1e27);border:1px solid var(--border,#252a36);border-radius:5px;padding:0.5rem 0.7rem;}',
      '.ap-mchip span{display:block;font-family:' + FM + ';font-size:9px;text-transform:uppercase;letter-spacing:0.05em;color:var(--text-muted,#5a6178);}',
      '.ap-mchip b{font-family:' + FB + ';font-size:12.5px;font-weight:600;color:var(--text,#e6e8ed);}',
      // pro gate
      '.ap-pro-teaser{font-family:' + FB + ';font-size:14px;line-height:1.65;color:var(--text,#e6e8ed);margin:0 0 0.6rem;}',
      '.ap-blur{filter:blur(4px);opacity:0.5;user-select:none;pointer-events:none;max-height:5.5rem;overflow:hidden;}',
      '.ap-cta-row{display:flex;align-items:center;gap:0.8rem;margin-top:0.7rem;flex-wrap:wrap;}',
      '.ap-cta-line{font-family:' + FM + ';font-size:10px;letter-spacing:0.05em;text-transform:uppercase;color:var(--text-muted,#5a6178);}',
      '.ap-cta{display:inline-block;background:var(--yellow,#F5D921);color:var(--bg,#111318);font-family:' + FM + ';font-weight:700;font-size:10px;letter-spacing:0.05em;text-transform:uppercase;padding:6px 12px;border-radius:4px;text-decoration:none;}',
      '.ap-cta:hover{opacity:0.85;}',
      '.ap-state{display:inline-block;font-family:' + FM + ';font-size:9px;letter-spacing:0.06em;text-transform:uppercase;color:var(--text-muted,#5a6178);background:rgba(255,255,255,0.03);border:1px solid var(--border,#252a36);border-radius:2px;padding:1px 6px;}',
      '.ap-note{font-family:' + FB + ';font-size:11px;line-height:1.5;color:var(--text-muted,#5a6178);margin:0.3rem 0 0;}',
      '.ap-muted{color:var(--text-muted,#5a6178);}',
      '.ap-fail{max-width:760px;margin:3rem auto;text-align:center;color:var(--text-dim,#8b92a5);font-family:' + FB + ';font-size:13px;}',
      '@media(max-width:640px){.ap-facts,.ap-edges{grid-template-columns:1fr;}}'
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
  function state(t) { return '<span class="ap-state">' + esc(t) + '</span>'; }
  function muted(t) { return '<span class="ap-muted">' + esc(t) + '</span>'; }
  function ctaRow() {
    return '<div class="ap-cta-row"><span class="ap-cta-line">This is a Pro layer</span>'
      + '<a href="#" class="ap-cta" onclick="if(window.openEarlyAccess){openEarlyAccess();}return false;">Unlock with Pro &rarr;</a></div>';
  }
  // A Pro layer: legible teaser, blurred body, honest CTA. If no authored
  // body exists (sparse shard), render an honest Forthcoming state instead
  // of a fake lock.
  function proBlock(obj) {
    if (obj && obj.body) {
      return (obj.teaser ? '<p class="ap-pro-teaser">' + esc(obj.teaser) + '</p>' : '')
        + '<div class="ap-blur"><p class="ap-body">' + esc(obj.body) + '</p></div>'
        + ctaRow();
    }
    return '<p class="ap-body">' + state('Forthcoming') + '</p>';
  }

  // ── data-driven dependency chart (the free headline asset) ──
  function node(x, y, w, h, stroke, title, note) {
    var s = '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '" rx="8" class="node" stroke="' + stroke + '"/>';
    s += '<text x="' + (x + 14) + '" y="' + (y + 23) + '" class="node-t">' + esc(title) + '</text>';
    if (note) s += '<text x="' + (x + 14) + '" y="' + (y + 41) + '" class="node-s">' + esc(note) + '</text>';
    return s;
  }
  var LADDER = ['Upstream Materials', 'Capital Equipment', 'Fabrication', 'Components', 'IP & Design', 'System Integration', 'Deploy / Operate'];
  function depChart(d) {
    var dep = d.dependency || {}, up = dep.upstream || [], down = dep.downstream || [];
    var name = (d.identity && d.identity.name) || (d.meta && d.meta.id) || '';
    var tier = (d.classification && d.classification.value_chain) || '';
    var cp = dep.control_point || '';
    if (!up.length && !down.length) {
      return '<div class="ap-chart"><p class="ap-note" style="text-align:center;padding:1.4rem 0;">Dependency edges forthcoming for this entity.</p></div>';
    }
    var W = 900, NW = 214, NH = 54, GAP = 14, TOP = 96;
    var rows = Math.max(up.length, down.length, 1);
    var colH = rows * NH + (rows - 1) * GAP;
    var cY = TOP + colH / 2;
    var eW = 196, eH = 116, eX = (W - eW) / 2, eY = cY - eH / 2;
    var ladderY = TOP + colH + 44;
    var H = ladderY + 74;
    var s = '<svg viewBox="0 0 ' + W + ' ' + H + '" role="img" xmlns="http://www.w3.org/2000/svg">';
    s += '<title>' + esc(name) + ' value-chain dependency map</title>';
    s += '<defs>'
      + '<marker id="ma-up" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#3b82f6"/></marker>'
      + '<marker id="ma-down" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#22c55e"/></marker></defs>';
    s += '<text x="22" y="30" class="cx-up">UPSTREAM &#183; DEPENDS ON</text>';
    s += '<text x="' + (W - 22) + '" y="30" text-anchor="end" class="cx-down">DOWNSTREAM &#183; SUPPLIES</text>';
    var eSpots = [eY + 30, eY + 58, eY + 86];
    up.forEach(function (n, i) {
      var y = TOP + i * (NH + GAP), ty = eSpots[Math.min(i, 2)] || (eY + eH / 2);
      s += node(22, y, NW, NH, '#3b82f6', n.name, n.note);
      s += '<line x1="' + (22 + NW) + '" y1="' + (y + NH / 2) + '" x2="' + eX + '" y2="' + ty + '" class="edge-up" marker-end="url(#ma-up)"/>';
    });
    down.forEach(function (n, i) {
      var y = TOP + i * (NH + GAP), ty = eSpots[Math.min(i, 2)] || (eY + eH / 2);
      s += node(W - 22 - NW, y, NW, NH, '#22c55e', n.name, n.note);
      s += '<line x1="' + (eX + eW) + '" y1="' + ty + '" x2="' + (W - 22 - NW) + '" y2="' + (y + NH / 2) + '" class="edge-down" marker-end="url(#ma-down)"/>';
    });
    // entity centre
    var first = String(name).split(' ')[0] || name;
    s += '<rect x="' + eX + '" y="' + eY + '" width="' + eW + '" height="' + eH + '" rx="12" class="ent-box"/>';
    s += '<text x="' + (W / 2) + '" y="' + (eY + 42) + '" text-anchor="middle" class="ent-name">' + esc(first) + '</text>';
    if (tier) s += '<text x="' + (W / 2) + '" y="' + (eY + 64) + '" text-anchor="middle" class="ent-tier">' + esc(tier) + ' tier</text>';
    if (cp) {
      s += '<rect x="' + (eX + 12) + '" y="' + (eY + eH - 34) + '" width="' + (eW - 24) + '" height="26" rx="13" class="cp-pill"/>';
      s += '<text x="' + (W / 2) + '" y="' + (eY + eH - 16) + '" text-anchor="middle" class="cp-text">CONTROL POINT</text>';
    }
    // tier ladder
    var tw = (W - 44) / LADDER.length;
    LADDER.forEach(function (t, i) {
      var x = 22 + i * tw, on = String(t).toLowerCase() === String(tier).toLowerCase();
      s += '<rect x="' + (x + 3) + '" y="' + ladderY + '" width="' + (tw - 6) + '" height="30" rx="5" class="tier' + (on ? ' on' : '') + '"/>';
      s += '<text x="' + (x + tw / 2) + '" y="' + (ladderY + 19) + '" text-anchor="middle" class="tier-t' + (on ? ' on' : '') + '">' + esc(t) + '</text>';
    });
    s += '</svg>';
    var cap = cp ? '<p class="ap-note">Control point: ' + esc(cp) + '. Edges from the entity registry and enrichment store; no price-derived data.</p>' : '';
    return '<div class="ap-chart">' + s + '</div>' + cap;
  }

  // ── layer renderers ──
  function ratingChip(r) {
    if (!r) return '';
    return '<span class="ap-chip rating ' + String(r).toLowerCase() + '">Bottleneck ' + esc(r) + '</span>';
  }
  function rBottleneck(d) {
    var b = d.bottleneck || {};
    if (b.state !== 'rated' && !b.rating) return '<p class="ap-body">Control-point rating: ' + state('Unrated') + '</p>';
    var head = b.headline ? '<p class="ap-lead">' + esc(b.headline) + '</p>' : '';
    var body = b.body ? '<p class="ap-body">' + esc(b.body) + '</p>'
      : (b.description ? '<p class="ap-body">' + esc(b.description) + '</p>' : '');
    return head + body;
  }
  function edgeCol(title, dir, nodes) {
    var chips = nodes.map(function (n) {
      return '<div class="ap-edge"><b>' + esc(n.name) + '</b>' + (n.note ? '<span>' + esc(n.note) + '</span>' : '') + '</div>';
    }).join('');
    return '<div class="ap-edge-col"><div class="ap-edge-h ' + dir + '">' + esc(title) + '</div>' + chips + '</div>';
  }
  function rDependency(d) {
    var dep = d.dependency || {}, up = dep.upstream || [], down = dep.downstream || [];
    var edges;
    if (up.length || down.length) {
      edges = '<div class="ap-edges">' + edgeCol('Upstream, depends on', 'up', up) + edgeCol('Downstream, supplies', 'down', down) + '</div>';
    } else if (dep.key_suppliers || dep.key_customers) {
      edges = '<div class="ap-edges"><div class="ap-edge-col"><div class="ap-edge-h up">Upstream</div><p class="ap-body">' + esc(dep.key_suppliers || 'Not available') + '</p></div>'
        + '<div class="ap-edge-col"><div class="ap-edge-h down">Downstream</div><p class="ap-body">' + esc(dep.key_customers || 'Not available') + '</p></div></div>';
    } else {
      edges = '<p class="ap-body">Supply-chain map: ' + state('Unmapped') + '</p>';
    }
    var analysis = (dep.analysis_body || dep.analysis_teaser)
      ? '<div class="ap-subhead">Concentration &amp; fragility <span class="ap-badge pro">Pro</span></div>'
        + proBlock({ teaser: dep.analysis_teaser, body: dep.analysis_body })
      : '';
    return edges + analysis;
  }
  function fact(k, v) { return v ? '<div class="ap-fact"><span>' + esc(k) + '</span><b>' + esc(v) + '</b></div>' : ''; }
  function rIdentity(d) {
    var id = d.identity || {}, ids = id.identifiers || {};
    var facts = [fact('Ticker', ids.ticker), fact('Listing', id.listing), fact('Domicile', id.domicile), fact('SEC CIK', ids.cik)].join('');
    var body = id.body ? '<p class="ap-body">' + esc(id.body) + '</p>' : (id.description ? '<p class="ap-body">' + esc(id.description) + '</p>' : '');
    return body + (facts ? '<div class="ap-facts">' + facts + '</div>' : '');
  }
  function rClassification(d) {
    var c = d.classification || {};
    var facts = [fact('Sector', c.sector), fact('Subsector', c.subsector), fact('Value-chain tier', c.value_chain), fact('Lifecycle', c.lifecycle || 'Public')].join('');
    var body = c.body ? '<p class="ap-body">' + esc(c.body) + '</p>' : '';
    return (facts ? '<div class="ap-facts">' + facts + '</div>' : '') + body;
  }
  function mchip(k, v) { return v ? '<div class="ap-mchip"><span>' + esc(k) + '</span><b>' + esc(v) + '</b></div>' : ''; }
  function rMarket(d) {
    var m = d.market_context || {};
    if (m.state === 'live' || m.member) {
      var band = m.weight_band_label || (m.weight_band === '5-capped' ? 'At the 5% single-name cap' : (m.weight_band ? m.weight_band + '% of sector index' : null));
      var rank = m.rank_label || (m.sector_rank != null ? ('No. ' + m.sector_rank + ' by weight') : null);
      return '<div class="ap-market">' + mchip('Index', m.sector_index) + mchip('Weight band', band) + mchip('Sector rank', rank) + '</div>'
        + '<p class="ap-note">Membership, band and rank only. No price, market capitalisation, or exact weight is shown.</p>';
    }
    if (m.state === 'token_isolated') return '<p class="ap-body">' + state('Token isolated') + ' Tokens are held as a research watchlist and never enter an equity index.</p>';
    if (m.state === 'private_capital_index') return '<div class="ap-market">' + mchip('Coverage', 'Robotnik Private Capital Index') + '</div>';
    return '<p class="ap-body">Membership: ' + muted('Not available') + '</p>';
  }
  function rCapital(d) {
    var cap = d.capital || {};
    if (cap.body || cap.teaser) return proBlock(cap);
    if (cap.state === 'live') return '<p class="ap-body">Last round: ' + esc(cap.last_round || 'n/a') + (cap.total_raised_m != null ? ' &#183; Total raised: $' + esc(cap.total_raised_m) + 'm' : '') + '</p>';
    if (cap.state === 'sparse') return '<p class="ap-body">Last round: ' + esc(cap.last_round || 'n/a') + ' &#183; ' + state('Amount undisclosed') + '</p>';
    return '<p class="ap-body">' + state('Forthcoming') + '</p>';
  }
  function rPolicy(d) { return proBlock(d.policy || {}); }
  function rGeographic(d) {
    var g = d.geographic || {};
    if (g.body || g.teaser) return proBlock(g);
    return '<div class="ap-facts">' + fact('HQ country', g.hq_country) + fact('HQ city', g.hq_city) + '</div><p class="ap-body">Supply-chain exposure: ' + state('Forthcoming') + '</p>';
  }
  function rEditorial(d) {
    var ed = d.editorial || {};
    if (ed.body || ed.teaser) return proBlock(ed);
    // notes already surface as the free epigraph; the Pro synthesis is forthcoming.
    return '<p class="ap-body">' + state('Forthcoming') + '</p>';
  }

  // locked render order (value-chain spine first) + tier tags
  var LAYERS = [
    { title: 'Bottleneck exposure', tier: 'free', fn: rBottleneck },
    { title: 'Dependency graph', tier: 'free', fn: rDependency },
    { title: 'Identity', tier: 'free', fn: rIdentity },
    { title: 'Classification', tier: 'free', fn: rClassification },
    { title: 'Market context', tier: 'free', fn: rMarket },
    { title: 'Capital structure', tier: 'pro', fn: rCapital },
    { title: 'Policy exposure', tier: 'pro', fn: rPolicy },
    { title: 'Geography', tier: 'pro', fn: rGeographic },
    { title: 'Editorial', tier: 'pro', fn: rEditorial }
  ];

  function render(mount, d) {
    var id = d.identity || {}, c = d.classification || {}, b = d.bottleneck || {};
    var typeLabel = { public: 'Public', private: 'Private', token: 'Token' }[id.type] || id.type;
    var idbits = [];
    if (id.identifiers && id.identifiers.ticker) idbits.push(esc(id.identifiers.ticker));
    if (c.sector) idbits.push(esc(c.sector));
    if (id.listing) idbits.push(esc(id.listing)); else if (typeLabel) idbits.push(esc(typeLabel));

    var chips = '';
    if (c.value_chain) chips += '<span class="ap-chip tier">' + esc(c.value_chain) + '</span>';
    if (b.rating) chips += ratingChip(b.rating);
    if (c.universe_status === 'index_constituent') chips += '<span class="ap-chip">Index constituent</span>';

    var html = '<div class="ap-wrap">'
      + '<div class="ap-eyebrow">Robotnik equity profile</div>'
      + '<h1 class="ap-name">' + esc(id.name || (d.meta && d.meta.id)) + '</h1>'
      + '<div class="ap-idline">' + idbits.join(' &#183; ') + '</div>'
      + (chips ? '<div class="ap-chips">' + chips + '</div>' : '');

    // free epigraph (the enrichment one-liner), if present
    var note = (d.editorial && d.editorial.notes) || '';
    if (note) html += '<blockquote class="ap-epigraph">' + esc(note) + '</blockquote>';

    // the free headline chart
    html += depChart(d);

    for (var i = 0; i < LAYERS.length; i++) {
      var L = LAYERS[i];
      var badge = L.tier === 'pro' ? '<span class="ap-badge pro">Pro</span>' : '<span class="ap-badge free">Free</span>';
      html += '<section class="ap-section' + (i === 0 ? ' first' : '') + '">'
        + '<div class="ap-shead"><h2 class="ap-stitle">' + esc(L.title) + '</h2>' + badge + '</div>'
        + L.fn(d) + '</section>';
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
