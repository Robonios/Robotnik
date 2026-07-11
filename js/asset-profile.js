// ═══════════════════════════════════════════════════════════
// FRONTIER ASSET PROFILE — per-entity renderer (v3, designed)
// Fetches /data/assets/{slug}.json and renders the nine locked
// layers as a data-driven template. Layout: a sticky layer spine
// (the signature element) beside a reading column. The identity
// layer is a thesis hero; bottleneck (03) and dependency (04) are
// the visual centre and carry the two figures; a labelled Pro
// boundary follows market context (05); layers 06-09 render gated
// to a one-line summary + structural skeleton, no blur. Sector hue,
// criticality and every fact are read from the shard, so the same
// template self-colours and populates for ~197 more entities.
// HARD ToS: no price, market cap, exact index weight or any
// price-derived figure on any surface, both figures included; the
// market figure shows index SHAPE only (bands + counts + cap line).
// ?preview=pro reveals authored Pro bodies for review only (there
// is no server-side gating). Schema 2.0 carries authored bodies;
// 1.0 shards degrade gracefully.
// ═══════════════════════════════════════════════════════════
(function () {
  'use strict';
  var FH = "'Space Grotesk',ui-sans-serif,system-ui,sans-serif";   // display: entity name, headings
  var FB = "'Mulish',ui-sans-serif,system-ui,sans-serif";           // body prose
  var FM = "'Space Mono','Roboto Mono',ui-monospace,monospace";     // micro-labels only

  // Render-scoped state, set in boot() before render():
  var _preview = false;    // ?preview=pro -> show authored Pro content in full (review only)
  var _resolver = null;    // search_index-backed edge-label -> slug resolver for chart links

  // sector -> accent hue. The template self-colours from the shard; --sector is
  // set on the profile root so every accent derives from one entity fact.
  var SECTOR_HUE = {
    'semiconductors': '#5B8DD6', 'semiconductor': '#5B8DD6',
    'robotics': '#46B49A',
    'space': '#E8765C',
    'materials': '#9B7BD0', 'materials & inputs': '#9B7BD0'
  };
  var SECTOR_FALLBACK = '#7C89A6';
  function sectorHue(sector) {
    return SECTOR_HUE[String(sector == null ? '' : sector).trim().toLowerCase()] || SECTOR_FALLBACK;
  }
  // criticality rating -> scale colour. Used ONLY in the bottleneck layer scale
  // and the spine dot; nowhere else do these four colours appear.
  var CRIT = { low: '#46B49A', medium: '#E3B341', high: '#E8894A', critical: '#E5484D' };
  var CRIT_STEPS = ['low', 'medium', 'high', 'critical'];

  // Space Mono is not part of the site-wide font load; the profile is the only
  // surface that uses it, so the template loads it (same mechanism: a <head>
  // stylesheet link), scoped to where it is needed.
  function injectFont() {
    if (document.querySelector('link[data-ap-font]')) return;
    var l = document.createElement('link');
    l.rel = 'stylesheet';
    l.href = 'https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&display=swap';
    l.setAttribute('data-ap-font', '1');
    document.head.appendChild(l);
  }

  var STYLE_ID = 'asset-profile-styles-v3';
  function injectStyles() {
    if (document.getElementById(STYLE_ID)) return;
    // Design tokens are scoped to .ap-root so they refine the profile surface
    // without clobbering the site-wide :root. --brand reuses the existing
    // --yellow; the rest of the palette is profile-local.
    var css = `
.ap-root{
  --bg:#161A26; --surface:#1C2130; --well:#10131C; --line:#2A3145;
  --ink:#EDEFF5; --body:#C7CEDA; --mute:#8A93A6;
  --brand:var(--yellow,#F5D921); --sector:${SECTOR_FALLBACK};
  --c-low:#46B49A; --c-med:#E3B341; --c-high:#E8894A; --c-crit:#E5484D;
  --measure:68ch;
  color:var(--body); font-family:${FB};
}
.ap-shell{display:grid; grid-template-columns:200px minmax(0,1fr); gap:3.2rem;
  max-width:1120px; margin:0 auto; padding:1.5rem 1.4rem 6rem;}
.ap-main{min-width:0; max-width:860px;}

/* ── the layer spine (signature) ── */
.ap-spine{position:sticky; top:1.5rem; align-self:start; height:calc(100vh - 3rem);
  display:flex; flex-direction:column;}
.ap-spine-head{font-family:${FH}; font-weight:700; font-size:15px; color:var(--ink);
  letter-spacing:-0.01em; display:flex; align-items:center; gap:0.45rem; margin-bottom:0.15rem;}
.ap-spine-mark{color:var(--brand); font-size:11px; line-height:1;}
.ap-spine-sub{font-family:${FM}; font-size:9.5px; letter-spacing:0.14em; text-transform:uppercase;
  color:var(--mute); margin:0 0 1.4rem 1.05rem;}
.ap-spine-nav{position:relative; display:flex; flex-direction:column; gap:0.05rem;
  padding-left:0.9rem; border-left:1px solid var(--line);}
.ap-spine-prog{position:absolute; left:-1px; top:0; width:1px; height:0; background:var(--sector);
  transition:height .15s linear;}
.ap-spine-item{display:flex; align-items:center; gap:0.55rem; text-decoration:none;
  font-family:${FB}; font-size:13px; color:var(--mute); padding:0.32rem 0; line-height:1.25;
  border-radius:3px; transition:color .18s ease;}
.ap-spine-num{font-family:${FM}; font-size:10px; letter-spacing:0.08em; color:var(--line);
  transition:color .18s ease;}
.ap-spine-item:hover{color:var(--body);}
.ap-spine-item.active{color:var(--ink);}
.ap-spine-item.active .ap-spine-num{color:var(--sector);}
.ap-spine-item.gated{color:var(--line);}
.ap-spine-item.gated.active{color:var(--mute);}
.ap-spine-dot{width:6px; height:6px; border-radius:50%; margin-left:auto; flex:0 0 auto;}
.ap-spine-pro{display:flex; align-items:center; gap:0.5rem; margin:0.55rem 0 0.5rem -0.9rem;
  padding-left:0.9rem; font-family:${FM}; font-size:9px; letter-spacing:0.14em;
  text-transform:uppercase; color:var(--brand);}
.ap-spine-pro::before{content:''; width:0.55rem; height:1px; background:var(--brand);}
.ap-spine-item:focus-visible{outline:2px solid var(--sector); outline-offset:2px;}

/* ── mobile strip (spine collapses to a sticky top bar) ── */
.ap-strip{display:none;}

/* ── shared micro-label + type roles ── */
.ap-eyebrow{font-family:${FM}; font-size:11px; letter-spacing:0.13em; text-transform:uppercase;
  color:var(--sector); display:block; margin:0 0 0.7rem;}
.ap-eyebrow .n{color:var(--sector); opacity:0.7;}
.ap-heading{font-family:${FH}; font-weight:600; font-size:clamp(1.35rem,2.6vw,1.72rem);
  letter-spacing:-0.01em; color:var(--ink); line-height:1.18; margin:0 0 1.1rem; max-width:var(--measure);}
.ap-body{font-family:${FB}; font-size:17.5px; line-height:1.7; color:var(--body);
  margin:0 0 1.25rem; max-width:var(--measure);}
.ap-body:last-child{margin-bottom:0;}
.ap-lead{font-family:${FH}; font-weight:500; font-size:clamp(1.05rem,1.9vw,1.25rem); line-height:1.45;
  color:var(--ink); margin:0 0 1.4rem; max-width:var(--measure);}
.ap-prose a{color:var(--body); text-decoration:none;
  border-bottom:1px solid transparent; transition:border-color .15s ease,color .15s ease;}
.ap-prose a:hover,.ap-prose a:focus-visible{color:var(--ink); border-bottom-color:var(--sector);}
.ap-prose a:focus-visible{outline:2px solid var(--sector); outline-offset:2px; border-radius:1px;}
.ap-note{font-family:${FM}; font-size:10.5px; line-height:1.6; letter-spacing:0.02em;
  color:var(--mute); margin:0.7rem 0 0; max-width:var(--measure);}

/* ── layers + rhythm ── */
.ap-layer{padding:3rem 0; border-top:1px solid var(--line);}
.ap-layer.lead{padding:3.8rem 0;}
.ap-hero{padding:0.5rem 0 3.4rem;}

/* ── identity hero ── */
.ap-kicker{font-family:${FM}; font-size:10.5px; letter-spacing:0.14em; text-transform:uppercase;
  color:var(--mute); margin:0 0 0.9rem;}
.ap-name{font-family:${FH}; font-weight:700; font-size:clamp(2.1rem,5vw,3.35rem); line-height:1.04;
  letter-spacing:-0.02em; color:var(--ink); margin:0 0 1rem;}
.ap-meta{display:flex; flex-wrap:wrap; align-items:center; gap:0.6rem 0.9rem; margin:0 0 1.4rem;}
.ap-sector-chip{font-family:${FM}; font-size:10px; letter-spacing:0.08em; text-transform:uppercase;
  color:var(--sector); border:1px solid color-mix(in srgb,var(--sector) 45%,var(--line));
  background:color-mix(in srgb,var(--sector) 10%,transparent); border-radius:3px; padding:3px 9px;}
.ap-tickline{font-family:${FM}; font-size:12px; letter-spacing:0.06em; color:var(--mute);}
.ap-descriptor{font-family:${FH}; font-weight:400; font-size:clamp(1.1rem,2vw,1.35rem); line-height:1.45;
  color:var(--ink); margin:0 0 1.8rem; max-width:var(--measure);}
.ap-facts{display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:0 2.4rem;
  margin:0 0 2rem; max-width:var(--measure);}
.ap-fact{display:flex; justify-content:space-between; gap:0.8rem; align-items:baseline;
  padding:0.55rem 0; border-bottom:1px solid var(--line);}
.ap-fact-k{font-family:${FM}; font-size:10px; letter-spacing:0.06em; text-transform:uppercase; color:var(--mute);}
.ap-fact-v{font-family:${FB}; font-size:14px; font-weight:600; color:var(--ink); text-align:right;}

/* ── criticality scale (bottleneck only) ── */
.ap-crit{margin:0 0 1.9rem; max-width:var(--measure);}
.ap-crit-track{display:grid; grid-template-columns:repeat(4,1fr); gap:5px;}
.ap-crit-step{font-family:${FM}; font-size:10px; letter-spacing:0.06em; text-transform:uppercase;
  text-align:center; color:var(--mute); padding:0.55rem 0.2rem; border-radius:4px;
  background:var(--well); border:1px solid var(--line); position:relative;}
.ap-crit-step.on{color:#12151b; font-weight:700; background:var(--on,var(--mute));
  border-color:var(--on,var(--mute)); box-shadow:0 0 22px -6px var(--on,transparent);}
.ap-crit-cap{display:flex; justify-content:space-between; font-family:${FM}; font-size:9px;
  letter-spacing:0.1em; text-transform:uppercase; color:var(--mute); margin-top:0.5rem;}

/* ── figures: break out wider than the reading measure, opaque + depth ── */
.ap-fig{margin:0 0 1rem; max-width:none;}
.ap-fig.fade{opacity:0; transform:translateY(10px); transition:opacity .5s ease,transform .5s ease;}
.ap-fig.fade.in{opacity:1; transform:none;}
.ap-chart{background:linear-gradient(180deg,var(--surface),var(--well)); border:1px solid var(--line);
  border-radius:12px; padding:0.8rem; overflow-x:auto; box-shadow:inset 0 1px 0 rgba(255,255,255,0.02),0 18px 40px -30px #000;}
.ap-chart svg{display:block; width:100%; height:auto; min-width:640px;}
/* dependency graph — neutral field, sole accent is the --sector centre */
.ap-chart .cx-up,.ap-chart .cx-down{fill:var(--mute); font:600 10px ${FM}; letter-spacing:0.12em;}
.ap-chart .node{fill:var(--well); stroke:var(--line); stroke-width:1;}
.ap-chart .node-t{fill:var(--ink); font:600 13px ${FH};}
.ap-chart .node-s{fill:var(--mute); font:400 10.5px ${FB};}
.ap-chart .edge-up,.ap-chart .edge-down{stroke:var(--mute); stroke-width:1.2; opacity:0.35; fill:none;}
.ap-chart .ent-box{fill:color-mix(in srgb,var(--sector) 14%,var(--well)); stroke:var(--sector); stroke-width:1.6;
  filter:drop-shadow(0 0 14px color-mix(in srgb,var(--sector) 35%,transparent));}
.ap-chart .ent-name{fill:var(--sector); font:700 21px ${FH};}
.ap-chart .ent-tier{fill:var(--ink); font:600 11px ${FB};}
.ap-chart .cp-pill{fill:color-mix(in srgb,var(--sector) 8%,transparent); stroke:var(--sector); stroke-dasharray:3 3;}
.ap-chart .cp-text{fill:var(--sector); font:600 10px ${FM}; letter-spacing:0.06em;}
.ap-chart .tier{fill:var(--well); stroke:var(--line);}
.ap-chart .tier.on{fill:color-mix(in srgb,var(--sector) 12%,var(--well)); stroke:var(--sector);}
.ap-chart .tier-t{fill:var(--mute); font:600 9px ${FB};}
.ap-chart .tier-t.on{fill:var(--sector); font-weight:700;}
.ap-chart a.node-link,.ap-chart a.tier-link{cursor:pointer;}
.ap-chart a.node-link .node{transition:fill .12s ease,stroke .12s ease;}
.ap-chart a.node-link:hover .node,.ap-chart a.node-link:focus-visible .node{fill:var(--surface); stroke:var(--sector);}
.ap-chart a.node-link:hover .node-t,.ap-chart a.node-link:focus-visible .node-t{text-decoration:underline;}
.ap-chart a.tier-link:hover .tier,.ap-chart a.tier-link:focus-visible .tier{stroke:var(--sector);}
.ap-chart a.node-link:focus,.ap-chart a.tier-link:focus{outline:none;}
.ap-chart a.node-link:focus-visible,.ap-chart a.tier-link:focus-visible{outline:2px solid var(--sector); outline-offset:2px;}
/* market weight-shape figure — restyle only; me-bar in --sector, cap line neutral */
.ap-chart .wc-bar{fill:var(--line);}
.ap-chart .wc-cap{fill:color-mix(in srgb,var(--ink) 16%,var(--surface)); stroke:var(--mute); stroke-width:1;}
.ap-chart .wc-me{fill:var(--sector);}
.ap-chart .wc-capline{stroke:var(--mute); stroke-width:1; stroke-dasharray:4 4; opacity:0.6;}
.ap-chart .wc-capline-lbl{fill:var(--mute); font:600 9px ${FM}; letter-spacing:0.08em;}
.ap-chart .wc-me-lbl{fill:var(--sector); font:700 12px ${FH}; letter-spacing:0.02em;}
.ap-chart .wc-bracket{stroke:var(--mute); stroke-width:1;}
.ap-chart .wc-bracket-lbl{fill:var(--mute); font:600 9px ${FM}; letter-spacing:0.08em;}
.ap-chart .wc-base{stroke:var(--line); stroke-width:1;}
.ap-chart .wc-axis{fill:var(--mute); font:600 9px ${FM}; letter-spacing:0.08em;}
.ap-caption{font-family:${FB}; font-size:14px; line-height:1.6; color:var(--mute);
  margin:0.7rem 0 1.1rem; max-width:var(--measure);}

/* ── dependency edges + market chips ── */
.ap-edges{display:grid; grid-template-columns:1fr 1fr; gap:1.4rem; margin:1.4rem 0 0; max-width:var(--measure);}
.ap-edge-h{font-family:${FM}; font-size:9.5px; letter-spacing:0.1em; text-transform:uppercase; color:var(--mute); margin-bottom:0.6rem;}
.ap-edge{background:var(--surface); border:1px solid var(--line); border-radius:6px; padding:0.5rem 0.65rem; margin-bottom:7px;}
.ap-edge b{display:block; color:var(--ink); font-family:${FB}; font-size:13px; font-weight:600;}
.ap-edge span{color:var(--mute); font-family:${FB}; font-size:11px;}
.ap-market{display:flex; flex-wrap:wrap; gap:0.6rem; margin:0.2rem 0 0;}
.ap-mchip{background:var(--surface); border:1px solid var(--line); border-radius:6px; padding:0.5rem 0.75rem;}
.ap-mchip span{display:block; font-family:${FM}; font-size:9px; text-transform:uppercase; letter-spacing:0.06em; color:var(--mute); margin-bottom:2px;}
.ap-mchip b{font-family:${FB}; font-size:13px; font-weight:600; color:var(--ink);}
.ap-subhead{display:flex; align-items:center; gap:0.6rem; margin:2.2rem 0 1.1rem; font-family:${FM}; font-size:11px; letter-spacing:0.1em; text-transform:uppercase; color:var(--ink); max-width:var(--measure);}
.ap-badge-pro{font-family:${FM}; font-size:8.5px; letter-spacing:0.1em; text-transform:uppercase; color:var(--brand); border:1px solid color-mix(in srgb,var(--brand) 40%,var(--line)); border-radius:3px; padding:2px 7px;}

/* ── the Pro boundary band + gated layers ── */
.ap-pro-band{margin:1rem 0 0; padding:1.5rem 1.6rem; border:1px solid color-mix(in srgb,var(--brand) 40%,var(--line));
  border-radius:12px; background:color-mix(in srgb,var(--brand) 5%,var(--surface)); max-width:var(--measure);}
.ap-pro-band-tag{font-family:${FM}; font-size:10px; letter-spacing:0.14em; text-transform:uppercase; color:var(--brand); margin:0 0 0.5rem;}
.ap-pro-band-title{font-family:${FH}; font-weight:600; font-size:1.15rem; color:var(--ink); margin:0 0 0.55rem;}
.ap-pro-band-list{font-family:${FB}; font-size:13.5px; line-height:1.6; color:var(--mute); margin:0;}
.ap-gate-summary{font-family:${FH}; font-weight:400; font-size:1.08rem; line-height:1.45; color:var(--ink); margin:0 0 1.1rem; max-width:var(--measure);}
.ap-skel{display:flex; flex-wrap:wrap; gap:0.5rem; margin:0 0 1rem;}
.ap-skel-item{font-family:${FM}; font-size:10px; letter-spacing:0.05em; text-transform:uppercase; color:var(--mute);
  border:1px dashed var(--line); border-radius:4px; padding:4px 10px;}
.ap-gate-tag{display:flex; align-items:center; gap:0.7rem; margin-top:0.4rem;}
.ap-gate-tag .lbl{font-family:${FM}; font-size:10px; letter-spacing:0.06em; text-transform:uppercase; color:var(--mute);}
.ap-cta{display:inline-block; background:var(--brand); color:#12151b; font-family:${FM}; font-weight:700;
  font-size:10px; letter-spacing:0.06em; text-transform:uppercase; padding:6px 13px; border-radius:4px; text-decoration:none;}
.ap-cta:hover{filter:brightness(1.06);}
.ap-cta:focus-visible{outline:2px solid var(--brand); outline-offset:2px;}
.ap-preview-banner{margin:1.4rem 0 0; padding:0.55rem 0.8rem; border:1px solid color-mix(in srgb,var(--brand) 40%,var(--line));
  border-radius:6px; background:color-mix(in srgb,var(--brand) 6%,transparent); font-family:${FM}; font-size:10px;
  letter-spacing:0.06em; text-transform:uppercase; color:var(--brand);}
.ap-state{display:inline-block; font-family:${FM}; font-size:9px; letter-spacing:0.06em; text-transform:uppercase;
  color:var(--mute); background:var(--well); border:1px solid var(--line); border-radius:3px; padding:1px 7px;}
.ap-fail{max-width:640px; margin:5rem auto; text-align:center; color:var(--mute); font-family:${FB}; font-size:14px;}

/* ── responsive: spine collapses to a sticky top strip; figures full-bleed ── */
@media(max-width:860px){
  .ap-shell{grid-template-columns:1fr; gap:0; padding:0 1.1rem 5rem;}
  .ap-spine{display:none;}
  .ap-strip{display:flex; align-items:center; justify-content:space-between; gap:0.8rem;
    position:sticky; top:0; z-index:20; margin:0 -1.1rem 1.4rem; padding:0.7rem 1.1rem;
    background:color-mix(in srgb,var(--bg) 88%,transparent); backdrop-filter:blur(8px);
    border-bottom:1px solid var(--line);}
  .ap-strip-now{font-family:${FM}; font-size:11px; letter-spacing:0.06em; text-transform:uppercase; color:var(--ink); min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;}
  .ap-strip-now .n{color:var(--sector);}
  .ap-strip-now .of{color:var(--mute);}
  .ap-strip details{position:relative;}
  .ap-strip summary{list-style:none; cursor:pointer; font-family:${FM}; font-size:10px; letter-spacing:0.08em;
    text-transform:uppercase; color:var(--mute); border:1px solid var(--line); border-radius:4px; padding:5px 10px;}
  .ap-strip summary::-webkit-details-marker{display:none;}
  .ap-strip details[open] summary{color:var(--ink); border-color:var(--sector);}
  .ap-strip-menu{position:absolute; right:0; top:calc(100% + 6px); z-index:30; background:var(--surface);
    border:1px solid var(--line); border-radius:8px; padding:0.4rem; min-width:200px; box-shadow:0 20px 40px -20px #000;}
  .ap-strip-menu a{display:flex; gap:0.6rem; text-decoration:none; font-family:${FB}; font-size:13px;
    color:var(--body); padding:0.4rem 0.6rem; border-radius:4px;}
  .ap-strip-menu a .num{font-family:${FM}; font-size:10px; color:var(--mute);}
  .ap-strip-menu a:hover{background:var(--well); color:var(--ink);}
  .ap-fig{margin-left:-1.1rem; margin-right:-1.1rem;}
  .ap-chart{border-radius:0; border-left:none; border-right:none;}
  .ap-facts,.ap-edges{grid-template-columns:1fr;}
  .ap-body{font-size:16.5px;}
}

@media(prefers-reduced-motion:reduce){
  .ap-fig.fade,.ap-spine-item,.ap-spine-prog,.ap-chart a.node-link .node,.ap-prose a{transition:none !important;}
  .ap-fig.fade{opacity:1; transform:none;}
}`;
    var el = document.createElement('style');
    el.id = STYLE_ID; el.textContent = css;
    document.head.appendChild(el);
  }

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  // Render prose as one or more paragraphs, splitting on blank lines. Plain text
  // only, never pre-built HTML; each paragraph is escaped independently.
  function paras(t, cls) {
    cls = cls || 'ap-body';
    return String(t == null ? '' : t).split(/\n{2,}/)
      .map(function (p) { return p.trim(); }).filter(function (p) { return p; })
      .map(function (p) { return '<p class="' + cls + '">' + esc(p) + '</p>'; }).join('');
  }
  function stateTag(t) { return '<span class="ap-state">' + esc(t) + '</span>'; }

  // ── edge-label -> slug resolver (search_index.json is the name/alias source) ──
  function slugifyId(id) {
    return /^[A-Za-z0-9]+$/.test(id) ? id
      : String(id).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
  }
  var RESOLVE_STOP = { adr: 1, ads: 1, corp: 1, corporation: 1, inc: 1, incorporated: 1,
    ltd: 1, limited: 1, co: 1, company: 1, companies: 1, holdings: 1, holding: 1, group: 1,
    grp: 1, plc: 1, sa: 1, nv: 1, ag: 1, kk: 1, gmbh: 1, representing: 1, american: 1,
    depositary: 1, shares: 1, the: 1, ordinary: 1 };
  function normName(s) {
    s = String(s == null ? '' : s).toLowerCase().replace(/&/g, ' and ').replace(/[^a-z0-9]+/g, ' ');
    return s.split(/\s+/).filter(function (t) { return t && !RESOLVE_STOP[t]; }).join(' ').trim();
  }
  function buildResolver(searchIndex) {
    var map = {}, ents = (searchIndex && searchIndex.entities) || [];
    function add(key, slug) {
      if (!key) return;
      if (key in map) { if (map[key] !== slug) map[key] = false; }
      else map[key] = slug;
    }
    ents.forEach(function (e) {
      var slug = slugifyId(e.id);
      add(normName(e.name), slug);
      (e.aliases || []).forEach(function (a) { add(normName(a), slug); });
    });
    return { resolve: function (label) { var s = map[normName(label)]; return (s && s !== false) ? s : null; } };
  }
  var TIER_PAGE = '/research/value-chain-taxonomy';

  // ── data-driven dependency chart (free headline figure) ──
  // Geometry preserved from v2 exactly; only the palette moved to the token
  // system (neutral field, sole accent is the --sector centre) via CSS classes.
  function node(x, y, w, h, title, note, slug) {
    var inner = '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '" rx="8" class="node"/>'
      + '<text x="' + (x + 14) + '" y="' + (y + 23) + '" class="node-t">' + esc(title) + '</text>'
      + (note ? '<text x="' + (x + 14) + '" y="' + (y + 41) + '" class="node-s">' + esc(note) + '</text>' : '');
    if (slug) {
      return '<a class="node-link" href="/assets/' + encodeURIComponent(slug) + '.html">'
        + '<title>Open ' + esc(title) + ' profile</title>' + inner + '</a>';
    }
    return '<g>' + inner + '</g>';
  }
  var LADDER = ['Upstream Materials', 'Capital Equipment', 'Fabrication', 'Components', 'IP & Design', 'System Integration', 'Deploy / Operate'];
  function depChart(d) {
    var dep = d.dependency || {}, up = dep.upstream || [], down = dep.downstream || [];
    var name = (d.identity && d.identity.name) || (d.meta && d.meta.id) || '';
    var tier = (d.classification && d.classification.value_chain) || '';
    var cp = dep.control_point || '';
    if (!up.length && !down.length) {
      return '<div class="ap-fig"><div class="ap-chart"><p class="ap-note" style="text-align:center;padding:1.4rem 0;">Dependency edges forthcoming for this entity.</p></div></div>';
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
      + '<marker id="ma-up" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#8A93A6"/></marker>'
      + '<marker id="ma-down" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#8A93A6"/></marker></defs>';
    s += '<text x="22" y="30" class="cx-up">UPSTREAM &#183; DEPENDS ON</text>';
    s += '<text x="' + (W - 22) + '" y="30" text-anchor="end" class="cx-down">DOWNSTREAM &#183; SUPPLIES</text>';
    var eSpots = [eY + 30, eY + 58, eY + 86];
    up.forEach(function (n, i) {
      var y = TOP + i * (NH + GAP), ty = eSpots[Math.min(i, 2)] || (eY + eH / 2);
      s += node(22, y, NW, NH, n.name, n.note, _resolver && _resolver.resolve(n.name));
      s += '<line x1="' + (22 + NW) + '" y1="' + (y + NH / 2) + '" x2="' + eX + '" y2="' + ty + '" class="edge-up" marker-end="url(#ma-up)"/>';
    });
    down.forEach(function (n, i) {
      var y = TOP + i * (NH + GAP), ty = eSpots[Math.min(i, 2)] || (eY + eH / 2);
      s += node(W - 22 - NW, y, NW, NH, n.name, n.note, _resolver && _resolver.resolve(n.name));
      s += '<line x1="' + (eX + eW) + '" y1="' + ty + '" x2="' + (W - 22 - NW) + '" y2="' + (y + NH / 2) + '" class="edge-down" marker-end="url(#ma-down)"/>';
    });
    var first = String(name).split(' ')[0] || name;
    s += '<rect x="' + eX + '" y="' + eY + '" width="' + eW + '" height="' + eH + '" rx="12" class="ent-box"/>';
    s += '<text x="' + (W / 2) + '" y="' + (eY + 42) + '" text-anchor="middle" class="ent-name">' + esc(first) + '</text>';
    if (tier) s += '<text x="' + (W / 2) + '" y="' + (eY + 64) + '" text-anchor="middle" class="ent-tier">' + esc(tier) + ' tier</text>';
    if (cp) {
      s += '<rect x="' + (eX + 12) + '" y="' + (eY + eH - 34) + '" width="' + (eW - 24) + '" height="26" rx="13" class="cp-pill"/>';
      s += '<text x="' + (W / 2) + '" y="' + (eY + eH - 16) + '" text-anchor="middle" class="cp-text">CONTROL POINT</text>';
    }
    var tw = (W - 44) / LADDER.length;
    LADDER.forEach(function (t, i) {
      var x = 22 + i * tw, on = String(t).toLowerCase() === String(tier).toLowerCase();
      var rung = '<rect x="' + (x + 3) + '" y="' + ladderY + '" width="' + (tw - 6) + '" height="30" rx="5" class="tier' + (on ? ' on' : '') + '"/>'
        + '<text x="' + (x + tw / 2) + '" y="' + (ladderY + 19) + '" text-anchor="middle" class="tier-t' + (on ? ' on' : '') + '">' + esc(t) + '</text>';
      s += TIER_PAGE ? '<a class="tier-link" href="' + TIER_PAGE + '"><title>Value-chain tier: ' + esc(t) + '</title>' + rung + '</a>' : rung;
    });
    s += '</svg>';
    var cap = cp ? '<p class="ap-note">Control point: ' + esc(cp) + '. Edges from the entity registry and enrichment store; no price-derived data.</p>' : '';
    return '<div class="ap-fig fade">' + '<div class="ap-chart">' + s + '</div></div>' + cap;
  }

  // ── market-context weight-shape chart (figure-free: cap shelf + falloff) ──
  // Geometry preserved from v2 exactly; every bar height is an ordinal weight
  // BAND (7 levels), never a weight. Restyle-only: the me-bar is --sector.
  function wChart(m) {
    var c = m.chart;
    if (!c || !c.falloff || !c.falloff.length) return '';
    var W = 900, H = 250, mL = 24, mR = 24, baseY = 190, capH = 132;
    var HTS = [capH, 104, 82, 62, 44, 28, 16];
    var total = c.total || c.falloff.reduce(function (a, b) { return a + (b.count || 0); }, 0);
    if (!total) return '';
    var slotW = (W - mL - mR) / total, barW = Math.max(3, slotW * 0.66);
    var me = c.me, atCap = c.at_cap || 0;
    var cohort = (c.cohort || []).slice().sort(function (a, b) { return (a === me ? -1 : 0) - (b === me ? -1 : 0); });
    var bars = [], i, j, n;
    for (i = 0; i < atCap; i++) bars.push({ h: HTS[0], kind: cohort[i] === me ? 'me' : 'cap', name: cohort[i] });
    for (i = 1; i < c.falloff.length; i++) { n = c.falloff[i].count || 0; for (j = 0; j < n; j++) bars.push({ h: HTS[i] || HTS[HTS.length - 1], kind: 'bar', bi: i }); }
    var capY = baseY - capH;
    var s = '<svg viewBox="0 0 ' + W + ' ' + H + '" role="img" xmlns="http://www.w3.org/2000/svg">';
    s += '<title>' + esc(m.sector_index || 'Sector index') + ': ' + atCap + ' names at the ' + esc(c.cap_label || '') + ' single-name cap, then the field falls away</title>';
    s += '<line class="wc-capline" x1="' + mL + '" y1="' + capY + '" x2="' + (W - mR) + '" y2="' + capY + '"/>';
    s += '<text class="wc-capline-lbl" x="' + (W - mR) + '" y="' + (capY - 6) + '" text-anchor="end">' + esc(c.cap_label || '') + ' CAP</text>';
    var x = mL;
    bars.forEach(function (bar) {
      var y = baseY - bar.h, cls = bar.kind === 'me' ? 'wc-bar wc-me' : (bar.kind === 'cap' ? 'wc-bar wc-cap' : 'wc-bar');
      var op = bar.kind === 'bar' ? ' opacity="' + Math.max(0.3, 1 - (bar.bi - 1) * 0.12).toFixed(2) + '"' : '';
      var tip = bar.name ? '<title>' + esc(bar.name) + '</title>' : '';
      s += '<rect class="' + cls + '" x="' + x.toFixed(1) + '" y="' + y + '" width="' + barW.toFixed(1) + '" height="' + bar.h + '" rx="1.5"' + op + '>' + tip + '</rect>';
      x += slotW;
    });
    if (me) s += '<text class="wc-me-lbl" x="' + mL + '" y="' + (capY - 20) + '">' + esc(me) + '</text>';
    var shelfW = atCap * slotW - (slotW - barW), brY = baseY + 12;
    s += '<line class="wc-bracket" x1="' + mL + '" y1="' + brY + '" x2="' + (mL + shelfW).toFixed(1) + '" y2="' + brY + '"/>';
    s += '<text class="wc-bracket-lbl" x="' + (mL + shelfW / 2).toFixed(1) + '" y="' + (brY + 15) + '" text-anchor="middle">' + atCap + ' AT THE CAP</text>';
    s += '<line class="wc-base" x1="' + mL + '" y1="' + baseY + '" x2="' + (W - mR) + '" y2="' + baseY + '"/>';
    s += '<text class="wc-axis" x="' + mL + '" y="' + (H - 8) + '">LARGEST</text>';
    s += '<text class="wc-axis" x="' + (W - mR) + '" y="' + (H - 8) + '" text-anchor="end">SMALLEST &#183; BY WEIGHT</text>';
    s += '</svg>';
    return '<div class="ap-fig fade"><div class="ap-chart">' + s + '</div></div>';
  }

  // ── whitelisted, categorical-only identity facts (no price/mcap/weight ever) ──
  function fact(k, v) { return v ? '<div class="ap-fact"><span class="ap-fact-k">' + esc(k) + '</span><span class="ap-fact-v">' + esc(v) + '</span></div>' : ''; }
  var UNIVERSE_LABEL = { index_constituent: 'Index constituent', active_private: 'Private (RPCI)', active_token: 'Token watchlist' };
  function hero(d) {
    var id = d.identity || {}, ids = id.identifiers || {}, c = d.classification || {}, g = d.geographic || {};
    var descriptor = (d.editorial && d.editorial.notes) || '';
    var sectorChip = c.sector ? '<span class="ap-sector-chip">' + esc(c.sector) + '</span>' : '';
    var tick = id.listing ? esc(id.listing) : (ids.ticker ? esc(ids.ticker) : '');
    // exchange + ticker line, categorical only
    var meta = '<div class="ap-meta">' + sectorChip + (tick ? '<span class="ap-tickline">' + tick + '</span>' : '') + '</div>';
    // facts row — whitelist: exchange/listing, ticker, sector, sub-industry,
    // value-chain tier, HQ/country, universe class. Nothing price-derived.
    var hq = g.hq_city && g.hq_country ? (g.hq_city + ', ' + g.hq_country)
      : (g.hq_country || id.domicile || '');
    var facts = [
      fact('Listing', id.listing),
      fact('Ticker', ids.ticker),
      fact('Sector', c.sector),
      fact('Sub-industry', c.subsector),
      fact('Value-chain tier', c.value_chain),
      fact('Headquarters', hq),
      fact('Universe', UNIVERSE_LABEL[c.universe_status] || (c.universe_status ? String(c.universe_status).replace(/_/g, ' ') : '')),
      fact('SEC CIK', ids.cik)
    ].join('');
    var body = id.body ? paras(id.body) : (id.description ? paras(id.description) : '');
    return '<header class="ap-hero" id="layer-1">'
      + '<div class="ap-kicker">Robotnik equity profile</div>'
      + '<h1 class="ap-name">' + esc(id.name || (d.meta && d.meta.id)) + '</h1>'
      + meta
      + (descriptor ? '<p class="ap-descriptor">' + esc(descriptor) + '</p>' : '')
      + (facts ? '<div class="ap-facts">' + facts + '</div>' : '')
      + '<div class="ap-prose">' + body + '</div>'
      + '</header>';
  }
  function rClassification(d) {
    var c = d.classification || {};
    return '<div class="ap-prose">' + (c.body ? paras(c.body) : '<p class="ap-body">' + stateTag('Forthcoming') + '</p>') + '</div>';
  }
  function critScale(rating) {
    var r = String(rating || '').toLowerCase();
    if (!r || CRIT_STEPS.indexOf(r) < 0) return '';
    var steps = CRIT_STEPS.map(function (k) {
      var label = k.charAt(0).toUpperCase() + k.slice(1);
      return k === r
        ? '<span class="ap-crit-step on" style="--on:' + CRIT[k] + '">' + label + '</span>'
        : '<span class="ap-crit-step">' + label + '</span>';
    }).join('');
    return '<div class="ap-crit" role="img" aria-label="Bottleneck criticality rating: ' + esc(r) + ', on a scale of low, medium, high, critical">'
      + '<div class="ap-crit-track">' + steps + '</div>'
      + '<div class="ap-crit-cap"><span>Least critical</span><span>Most critical</span></div></div>';
  }
  function rBottleneck(d) {
    var b = d.bottleneck || {};
    if (b.state !== 'rated' && !b.rating) return '<div class="ap-prose"><p class="ap-body">Control-point rating: ' + stateTag('Unrated') + '</p></div>';
    var scale = critScale(b.rating);
    var head = b.headline ? '<p class="ap-lead">' + esc(b.headline) + '</p>' : '';
    var body = b.body ? paras(b.body) : (b.description ? paras(b.description) : '');
    return scale + head + '<div class="ap-prose">' + body + '</div>';
  }
  function edgeCol(title, nodes) {
    var chips = nodes.map(function (n) {
      return '<div class="ap-edge"><b>' + esc(n.name) + '</b>' + (n.note ? '<span>' + esc(n.note) + '</span>' : '') + '</div>';
    }).join('');
    return '<div><div class="ap-edge-h">' + esc(title) + '</div>' + chips + '</div>';
  }
  function rDependency(d) {
    var dep = d.dependency || {}, up = dep.upstream || [], down = dep.downstream || [];
    var chart = depChart(d);
    var edges;
    if (up.length || down.length) {
      edges = '<div class="ap-edges">' + edgeCol('Upstream, depends on', up) + edgeCol('Downstream, supplies', down) + '</div>';
    } else if (dep.key_suppliers || dep.key_customers) {
      edges = '<div class="ap-edges"><div><div class="ap-edge-h">Upstream</div><p class="ap-body">' + esc(dep.key_suppliers || 'Not available') + '</p></div>'
        + '<div><div class="ap-edge-h">Downstream</div><p class="ap-body">' + esc(dep.key_customers || 'Not available') + '</p></div></div>';
    } else {
      edges = '<p class="ap-body">Supply-chain map: ' + stateTag('Unmapped') + '</p>';
    }
    // Layer 4 splits: graph + edges free; the concentration analysis prose is Pro.
    var analysis = (dep.analysis_body || dep.analysis_teaser)
      ? '<div class="ap-subhead">Concentration &amp; fragility <span class="ap-badge-pro">Pro</span></div>'
        + gate({ teaser: dep.analysis_teaser, body: dep.analysis_body }, [])
      : '';
    return chart + edges + analysis;
  }
  function mchip(k, v) { return v ? '<div class="ap-mchip"><span>' + esc(k) + '</span><b>' + esc(v) + '</b></div>' : ''; }
  function rMarket(d) {
    var m = d.market_context || {};
    if (m.state === 'live' || m.member) {
      var band = m.weight_band_label || (m.weight_band === '5-capped' ? 'At the 5% single-name cap' : (m.weight_band ? m.weight_band + ' of sector index' : null));
      var rank = m.rank_label || (m.sector_rank != null ? ('No. ' + m.sector_rank + ' by weight') : null);
      var chips = '<div class="ap-market">' + mchip('Index', m.sector_index) + mchip('Weight band', band) + mchip('Sector rank', rank) + '</div>';
      if (m.chart) {
        var caption = m.caption ? '<p class="ap-caption">' + esc(m.caption) + '</p>' : '';
        return wChart(m) + caption + chips
          + '<p class="ap-note">Shape only: which names sit at the cap and how the field falls away below. No price, market capitalisation, weight or absolute figure is shown.</p>';
      }
      return chips + '<p class="ap-note">Membership, band and rank only. No price, market capitalisation, or exact weight is shown.</p>';
    }
    if (m.state === 'token_isolated') return '<div class="ap-prose"><p class="ap-body">' + stateTag('Token isolated') + ' Tokens are held as a research watchlist and never enter an equity index.</p></div>';
    if (m.state === 'private_capital_index') return '<div class="ap-market">' + mchip('Coverage', 'Robotnik Private Capital Index') + '</div>';
    return '<p class="ap-body">Membership: ' + stateTag('Not available') + '</p>';
  }

  // ── the free/pro gate (no blur): one-line summary + structural skeleton, body
  // withheld; ?preview=pro renders the authored body in full. `skel` is a list of
  // {k,v} structural facts that legitimately preview the layer's scope.
  function gate(obj, skel) {
    if (_preview && obj.body) {
      return (obj.teaser ? '<p class="ap-gate-summary">' + esc(obj.teaser) + '</p>' : '')
        + '<div class="ap-prose">' + paras(obj.body) + '</div>'
        + '<p class="ap-preview-banner">Pro layer &#183; review preview</p>';
    }
    if (!(obj && (obj.body || obj.teaser))) {
      return '<p class="ap-body">' + stateTag('Forthcoming') + '</p>';
    }
    var summary = obj.teaser ? '<p class="ap-gate-summary">' + esc(obj.teaser) + '</p>' : '';
    var skeleton = (skel && skel.length)
      ? '<div class="ap-skel">' + skel.map(function (it) { return '<span class="ap-skel-item">' + esc(it) + '</span>'; }).join('') + '</div>'
      : '';
    return summary + skeleton
      + '<div class="ap-gate-tag"><span class="lbl">Full read with Pro</span>'
      + '<a class="ap-cta" href="#" onclick="if(window.openEarlyAccess){openEarlyAccess();}return false;">Contact &rarr;</a></div>';
  }
  function rCapital(d) {
    var cap = d.capital || {};
    var skel = [];
    if (cap.last_round) skel.push('Last round');
    if (cap.total_raised_m != null) skel.push('Total raised');
    return gate(cap, skel);
  }
  function rPolicy(d) { return gate(d.policy || {}, []); }
  function rGeographic(d) {
    var g = d.geographic || {};
    var skel = [];
    if (g.hq_country) skel.push('HQ ' + g.hq_country);
    if (g.hq_city) skel.push(g.hq_city);
    return gate(g, skel);
  }
  function rEditorial(d) { return gate(d.editorial || {}, []); }

  // ── canonical layer order (1-9); free 1-5, pro 6-9; boundary after 5 ──
  var LAYERS = [
    { n: '01', title: 'Identity', tier: 'free', hero: true },
    { n: '02', title: 'Classification', tier: 'free', fn: rClassification },
    { n: '03', title: 'Bottleneck', tier: 'free', fn: rBottleneck, lead: true, crit: true },
    { n: '04', title: 'Dependency', tier: 'free', fn: rDependency, lead: true },
    { n: '05', title: 'Market context', tier: 'free', fn: rMarket },
    { n: '06', title: 'Capital', tier: 'pro', fn: rCapital },
    { n: '07', title: 'Policy', tier: 'pro', fn: rPolicy },
    { n: '08', title: 'Geography', tier: 'pro', fn: rGeographic },
    { n: '09', title: 'Editorial', tier: 'pro', fn: rEditorial }
  ];
  var PRO_NAMES = ['Capital', 'Policy', 'Geography', 'Editorial'];

  function spine(d, critColor) {
    var items = '', i, L;
    for (i = 0; i < LAYERS.length; i++) {
      L = LAYERS[i];
      if (i === 5) items += '<div class="ap-spine-pro">Pro</div>';
      var dot = (L.crit && critColor) ? '<span class="ap-spine-dot" style="background:' + critColor + '"></span>' : '';
      items += '<a class="ap-spine-item' + (L.tier === 'pro' ? ' gated' : '') + '" href="#layer-' + (i + 1) + '" data-spy="' + (i + 1) + '">'
        + '<span class="ap-spine-num">' + L.n + '</span>' + esc(L.title) + dot + '</a>';
    }
    return '<aside class="ap-spine" aria-label="Profile contents">'
      + '<div class="ap-spine-head"><span class="ap-spine-mark">&#9670;</span>Robotnik</div>'
      + '<div class="ap-spine-sub">Equity profile</div>'
      + '<nav class="ap-spine-nav"><span class="ap-spine-prog" aria-hidden="true"></span>' + items + '</nav>'
      + '</aside>';
  }
  function strip(d) {
    var menu = '', i, L;
    for (i = 0; i < LAYERS.length; i++) {
      L = LAYERS[i];
      menu += '<a href="#layer-' + (i + 1) + '"><span class="num">' + L.n + '</span>' + esc(L.title) + '</a>';
    }
    return '<div class="ap-strip">'
      + '<div class="ap-strip-now" id="ap-strip-now"><span class="n">01</span> &#183; Identity <span class="of">&#183; 1 of 9</span></div>'
      + '<details><summary>Layers</summary><div class="ap-strip-menu">' + menu + '</div></details>'
      + '</div>';
  }

  function render(mount, d) {
    var c = d.classification || {}, b = d.bottleneck || {};
    var hue = sectorHue(c.sector);
    var critColor = CRIT[String(b.rating || '').toLowerCase()] || '';

    var sections = hero(d);
    for (var i = 1; i < LAYERS.length; i++) {
      var L = LAYERS[i];
      if (i === 5) {
        sections += '<div class="ap-pro-band">'
          + '<div class="ap-pro-band-tag">Pro</div>'
          + '<div class="ap-pro-band-title">The full read continues with Pro</div>'
          + '<p class="ap-pro-band-list">' + PRO_NAMES.join(' &#183; ') + ' &mdash; the four layers behind the boundary.</p>'
          + '</div>';
      }
      var eyebrow = '<span class="ap-eyebrow"><span class="n">' + L.n + '</span> &#183; ' + esc(L.title) + '</span>';
      sections += '<section class="ap-layer' + (L.lead ? ' lead' : '') + '" id="layer-' + (i + 1) + '" aria-label="' + L.n + ' ' + esc(L.title) + '">'
        + eyebrow
        + '<h2 class="ap-heading">' + esc(L.title) + '</h2>'
        + L.fn(d) + '</section>';
    }

    var previewBanner = _preview
      ? '<p class="ap-preview-banner" style="max-width:none;margin:0 0 1.5rem;">Pro preview mode &#183; authored Pro content shown for review only</p>'
      : '';

    mount.innerHTML = '<div class="ap-root" style="--sector:' + hue + '">'
      + previewBanner
      + '<div class="ap-shell">'
      + spine(d, critColor)
      + '<main class="ap-main">' + strip(d) + sections + '</main>'
      + '</div></div>';

    wireMotion(mount);
  }

  // ── restrained motion: scroll-spy spine + progress, gentle figure fade-in ──
  function wireMotion(mount) {
    var reduce = false;
    try { reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion:reduce)').matches; } catch (e) {}
    var items = {}, i;
    var links = mount.querySelectorAll('.ap-spine-item');
    for (i = 0; i < links.length; i++) items[links[i].getAttribute('data-spy')] = links[i];
    var stripNow = mount.querySelector('#ap-strip-now');
    var prog = mount.querySelector('.ap-spine-prog');
    var nav = mount.querySelector('.ap-spine-nav');
    var sections = mount.querySelectorAll('[id^="layer-"]');

    function setActive(n) {
      for (var k in items) if (items.hasOwnProperty(k)) items[k].classList.toggle('active', k === String(n));
      if (stripNow && LAYERS[n - 1]) {
        stripNow.innerHTML = '<span class="n">' + LAYERS[n - 1].n + '</span> &#183; ' + esc(LAYERS[n - 1].title) + ' <span class="of">&#183; ' + n + ' of 9</span>';
      }
      if (prog && nav) prog.style.height = (nav.scrollHeight * (n / LAYERS.length)) + 'px';
    }

    if ('IntersectionObserver' in window) {
      var spy = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting) {
            var id = en.target.id.replace('layer-', '');
            setActive(parseInt(id, 10));
          }
        });
      }, { rootMargin: '-30% 0px -60% 0px', threshold: 0 });
      for (i = 0; i < sections.length; i++) spy.observe(sections[i]);

      if (!reduce) {
        var fade = new IntersectionObserver(function (entries) {
          entries.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add('in'); fade.unobserve(en.target); } });
        }, { rootMargin: '0px 0px -12% 0px', threshold: 0.05 });
        var figs = mount.querySelectorAll('.ap-fig.fade');
        for (i = 0; i < figs.length; i++) fade.observe(figs[i]);
      } else {
        var figs2 = mount.querySelectorAll('.ap-fig.fade');
        for (i = 0; i < figs2.length; i++) figs2[i].classList.add('in');
      }
    } else {
      var figs3 = mount.querySelectorAll('.ap-fig.fade');
      for (i = 0; i < figs3.length; i++) figs3[i].classList.add('in');
      setActive(1);
    }
    setActive(1);
  }

  function slugFromPath() {
    var seg = (location.pathname || '').split('/').filter(Boolean).pop() || '';
    return seg.replace(/\.html?$/i, '');
  }
  function boot() {
    var mount = document.getElementById('asset-profile');
    if (!mount) return;
    injectFont();
    injectStyles();
    var slug = slugFromPath();
    if (!slug) { mount.innerHTML = '<div class="ap-fail">No asset specified.</div>'; return; }
    try { _preview = /(^|[?&])preview=pro(&|#|$)/.test(location.search || ''); } catch (e) { _preview = false; }
    Promise.all([
      fetch('/data/assets/' + encodeURIComponent(slug) + '.json?v=' + Date.now())
        .then(function (r) { if (!r.ok) throw new Error('shard ' + r.status); return r.json(); }),
      fetch('/data/registries/search_index.json?v=' + Date.now())
        .then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; })
    ]).then(function (res) {
      _resolver = buildResolver(res[1]);
      render(mount, res[0]);
    }).catch(function (e) {
      mount.innerHTML = '<div class="ap-fail">Profile not available yet for <strong>' + esc(slug) + '</strong>.</div>';
      if (window.console) console.warn('[asset-profile]', e);
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
