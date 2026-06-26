/* ============================================================
   ROBOTNIK — RESEARCH HUB controller
   Renders the catalogue / enterprise / reference card grids and
   wires the client-side category filter. Shell + placeholders only:
   every card is a "coming soon" stub — no article content, no
   gating logic (tier badges are visual only).
   ============================================================ */
(function () {
  'use strict';

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function $(id) { return document.getElementById(id); }

  // filter categories (first is the reset)
  var CATEGORIES = ['All', 'Sectors', 'Indexes', 'Dependency Chain', 'Private Market', 'Commodities', 'Conditions', 'Market commentary'];

  // C · research catalogue (gated reviews)
  var CATALOGUE = [
    { title: 'Index family review', sub: 'Composite · Bottleneck · Public market', cat: 'Indexes', tier: 'pro' },
    { title: 'Private market review (RPCI)', sub: 'Robotnik Private Capital Index', cat: 'Private Market', tier: 'pro' },
    { title: 'Commodities review', sub: 'Rare earths · wafers · gases', cat: 'Commodities', tier: 'pro' },
    { title: 'Materials & Inputs sector review', cat: 'Sectors', tier: 'pro' },
    { title: 'Semiconductors sector review', cat: 'Sectors', tier: 'pro' },
    { title: 'Robotics sector review', cat: 'Sectors', tier: 'pro' },
    { title: 'Space sector review', cat: 'Sectors', tier: 'pro' },
    { title: 'Dependency-chain read', sub: 'Cross-sector read', cat: 'Dependency Chain', tier: 'pro', sig: true },
    { title: 'Benchmark / proxy (ETF) reviews', cat: 'Market commentary', tier: 'pro' },
    { title: 'Frontier Conditions read', sub: '−100 / +100 conditions index', cat: 'Conditions', tier: 'pro' },
    { title: 'Event / thematic piece', sub: 'Free preview · truncated', cat: 'Market commentary', tier: 'free' }
  ];

  // D · enterprise shelf (additive subject matter)
  var ENTERPRISE = [
    'Geography review', 'Supply-chain review', 'Policy review',
    'Patents / licensing review', 'Dependency-chain full analysis', 'Per-asset deep-dives'
  ];

  // E · reference & methodology (open / free), three groups
  var REFERENCE = [
    { group: 'Front-door narrative', items: [
      { id: 'R1', title: 'Robotnik thesis', sub: 'Frontier tech as a coherent investable asset class, read through its control points', url: '/research/frontier-stack-thesis', live: true },
      { title: 'Product overview / showcase', sub: 'What the platform is and does' }
    ] },
    { group: 'Foundations', items: [
      { id: 'R2', title: 'Universe membership methodology', sub: 'What qualifies as a Robotnik entity, and when it enters / leaves', url: '/research/universe-membership', live: true },
      { id: 'R3', title: 'Control points', sub: 'How control points are found and the dependency map built', url: '/research/control-points', live: true },
      { id: 'R9', title: 'The 8-tier value chain', sub: 'The positional taxonomy locating every entity' },
      { id: 'R10', title: 'The 9 layers of structured context', sub: 'The schema describing each entity' },
      { id: 'R12', title: 'Data & sources methodology', sub: 'Sources, FX, corrections, the anti-fabrication / UNRATED standard' }
    ] },
    { group: 'Index family', items: [
      { id: 'R4', title: 'Bottleneck criticality methodology' },
      { id: 'R5', title: 'Public equities methodology' },
      { id: 'R6', title: 'Private market shadow index (RPCI) methodology' },
      { id: 'R7', title: 'Commodities index methodology' },
      { id: 'R8', title: 'Composite index methodology' },
      { id: 'R11', title: 'Frontier Conditions', sub: 'The −100 / +100 diffusion index, planned' }
    ] }
  ];

  function tierBadge(t) {
    var label = t === 'pro' ? 'Pro' : t === 'enterprise' ? 'Enterprise' : 'Free';
    return '<span class="rh-tier ' + t + '">' + label + '</span>';
  }
  var SOON = '<span class="rh-soon">Coming soon</span>';

  // ---- C · catalogue ----
  function renderCatalogue() {
    $('research-catalogue').innerHTML = CATALOGUE.map(function (item) {
      return '<article class="rh-card" data-cat="' + esc(item.cat) + '">' +
        '<div class="rh-card-top"><span class="rh-card-cat">' + esc(item.cat) + '</span>' + tierBadge(item.tier) + '</div>' +
        '<h3 class="rh-card-title">' + esc(item.title) + '</h3>' +
        (item.sub ? '<p class="rh-card-sub">' + esc(item.sub) + '</p>' : '') +
        '<div class="rh-card-foot">' + SOON + (item.sig ? '<span class="rh-sig">Signature</span>' : '') + '</div>' +
        '</article>';
    }).join('');
  }

  function renderFilters() {
    var host = $('research-filters');
    var counts = {};
    CATALOGUE.forEach(function (c) { counts[c.cat] = (counts[c.cat] || 0) + 1; });
    host.innerHTML = CATEGORIES.map(function (cat, i) {
      var n = cat === 'All' ? CATALOGUE.length : (counts[cat] || 0);
      return '<button type="button" class="rh-chip' + (i === 0 ? ' is-active' : '') + '" data-filter="' + esc(cat) + '" aria-pressed="' + (i === 0) + '">' +
        esc(cat) + '<span class="rh-chip-count">' + n + '</span></button>';
    }).join('');
    host.addEventListener('click', function (e) {
      var chip = e.target.closest('.rh-chip'); if (!chip) return;
      var f = chip.dataset.filter;
      host.querySelectorAll('.rh-chip').forEach(function (c) {
        var on = c === chip; c.classList.toggle('is-active', on); c.setAttribute('aria-pressed', on ? 'true' : 'false');
      });
      document.querySelectorAll('#research-catalogue .rh-card').forEach(function (card) {
        card.classList.toggle('is-hidden', !(f === 'All' || card.dataset.cat === f));
      });
    });
  }

  // ---- D · enterprise ----
  function renderEnterprise() {
    $('enterprise-shelf').innerHTML = ENTERPRISE.map(function (title) {
      return '<article class="rh-card">' +
        '<div class="rh-card-top"><span class="rh-card-cat">Enterprise</span>' + tierBadge('enterprise') + '</div>' +
        '<h3 class="rh-card-title">' + esc(title) + '</h3>' +
        '<div class="rh-card-foot">' + SOON + '</div>' +
        '</article>';
    }).join('');
  }

  // ---- E · reference ----
  function renderReference() {
    $('reference-groups').innerHTML = REFERENCE.map(function (g) {
      var cards = g.items.map(function (it) {
        var inner =
          '<div class="rh-ref-top">' + (it.id ? '<span class="rh-ref-id">' + esc(it.id) + '</span>' : '') +
            '<span class="rh-ref-badges"><span class="rh-tier free">Free</span><span class="rh-tier reference">Reference</span></span></div>' +
          '<h3 class="rh-ref-title">' + esc(it.title) + '</h3>' +
          (it.sub ? '<p class="rh-ref-sub">' + esc(it.sub) + '</p>' : '');
        // Published reference pages render as a real link; the rest stay as
        // non-clickable "coming soon" stubs until their article goes live.
        if (it.live && it.url) {
          return '<a class="rh-ref-card rh-ref-card--live" href="' + esc(it.url) + '">' +
            inner + '<span class="rh-ref-readout">Read &rarr;</span></a>';
        }
        return '<article class="rh-ref-card">' + inner + '</article>';
      }).join('');
      return '<div class="rh-ref-group"><div class="rh-ref-group-title">' + esc(g.group) + '</div><div class="rh-ref-grid">' + cards + '</div></div>';
    }).join('');
  }

  function boot() {
    if ($('research-catalogue')) { renderCatalogue(); renderFilters(); }
    if ($('enterprise-shelf')) renderEnterprise();
    if ($('reference-groups')) renderReference();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
