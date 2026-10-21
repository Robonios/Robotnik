/* ============================================================
   ROBOTNIK: RESEARCH HUB controller
   Renders the reference and methodology library. Live reference
   pages render as links; planned ones render as plain cards.
   ============================================================ */
(function () {
  'use strict';

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function $(id) { return document.getElementById(id); }

  // Reference and methodology, three groups
  var REFERENCE = [
    { group: 'Front-door narrative', items: [
      { id: 'R1', title: 'Robotnik thesis', sub: 'Frontier tech as a coherent investable asset class, read through its control points', url: '/research/frontier-stack-thesis', live: true }
    ] },
    { group: 'Foundations', items: [
      { id: 'R2', title: 'Universe membership methodology', sub: 'What qualifies as a Robotnik entity, and when it enters / leaves', url: '/research/universe-membership', live: true },
      { id: 'R3', title: 'Control points', sub: 'How control points are found and the dependency map built', url: '/research/control-points', live: true },
      { id: 'R9', title: 'Value-chain taxonomy', sub: 'The 8-tier positional axis locating every company in the stack', url: '/research/value-chain-taxonomy', live: true },
      { id: 'R10', title: 'Structured context', sub: 'The nine-layer schema for reading a single frontier entity', url: '/research/structured-context', live: true },
      { id: 'R12', title: 'Sources and provenance', sub: 'How every claim about the world is sourced or marked curated interpretation', url: '/research/sources-and-provenance', live: true }
    ] },
    { group: 'Index family', items: [
      { id: 'R4', title: 'Bottleneck-weighted index', sub: 'How the universe is weighted by supply risk, and how each company is rated', url: '/research/bottleneck-weighted-index', live: true },
      { id: 'R5', title: 'Public equities index', sub: 'The base index: the listed frontier stack at market value, built as a sector blend', url: '/research/public-equities-index', live: true },
      { id: 'R6', title: 'Private capital index', sub: 'Frontier funding activity and conviction, not private-company valuation', url: '/research/private-capital-index', live: true },
      { id: 'R7', title: 'Commodities index', sub: 'How raw materials are weighted by frontier-demand intensity, not by tonnage or supply risk', url: '/research/commodities-index', live: true },
      { id: 'R8', title: 'Composite index', sub: 'The headline blend: three-quarters public equities, one-quarter commodities', url: '/research/composite-index', live: true },
      { id: 'R11', title: 'Frontier Conditions', sub: 'The −100 / +100 diffusion index, planned' }
    ] }
  ];

  function renderReference() {
    $('reference-groups').innerHTML = REFERENCE.map(function (g) {
      var cards = g.items.map(function (it) {
        var inner =
          '<div class="rh-ref-top">' + (it.id ? '<span class="rh-ref-id">' + esc(it.id) + '</span>' : '') +
            '<span class="rh-ref-badges"><span class="rh-tier reference">Reference</span></span></div>' +
          '<h3 class="rh-ref-title">' + esc(it.title) + '</h3>' +
          (it.sub ? '<p class="rh-ref-sub">' + esc(it.sub) + '</p>' : '');
        // Live reference pages render as links; planned ones as plain cards.
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
    if ($('reference-groups')) renderReference();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
