/* Robotnik front door (index.html), from approved mock v6 of 27 October 2026.
   - The index tiles and the index family read data/index/index_summary.json. Every
     figure on them comes from that feed; the page computes none.
   - The tier marquee, the stack map with its illustrative trace, the walkthrough poster.
   - Two robots, layered from the files in assets/robot/ and placed by robot.json.
   - Every Request access button, and Contact, opens the request-access form that
     js/nav.js builds (openEarlyAccess). */
(function () {
  'use strict';
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function $(id) { return document.getElementById(id); }
  function isNum(x) { return typeof x === 'number' && isFinite(x); }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  /* ---------- request access ---------- */
  [].forEach.call(document.querySelectorAll('[data-access]'), function (b) {
    b.addEventListener('click', function (e) {
      e.preventDefault();
      if (typeof window.openEarlyAccess === 'function') window.openEarlyAccess();
    });
  });

  /* ---------- the index family: tiles and rows from index_summary.json ---------- */
  var SUMMARY = 'data/index/index_summary.json';
  var MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  // Each index is coloured by its latest move at its own cadence.
  var PERIOD = { daily: '1D', weekly: '1W', monthly: '1M' };
  var PERIOD_WORDS = { '1D': 'one day', '1W': 'one week', '1M': 'one month' };
  // Copy only. Levels, moves and series come from the feed; until it loads the tiles hold
  // their place, and an index or a move the feed lacks reads n/a.
  var IDX = [
    { key: 'composite', name: 'Composite', full: 'Robotnik Composite Index', what: 'Equities and commodities, weighted 75 to 25', since: 'Weekly, from 17 Jun 2026', cadence: 'weekly' },
    { key: 'public', name: 'Public Equities', full: 'Public Equities', what: 'The listed companies across the four sectors', since: 'Each weekday', cadence: 'daily' },
    { key: 'bottleneck', name: 'Bottleneck-Weighted', full: 'Bottleneck-Weighted', what: 'The same universe, weighted by bottleneck criticality', since: 'Each weekday', cadence: 'daily' },
    { key: 'commodities', name: 'Commodities', full: 'Commodities', what: 'The materials the stack depends on, with a 12% single-name cap', since: 'Weekly, from 17 Jun 2026', cadence: 'weekly' },
    { key: 'private', name: 'Private Market', full: 'Private Market', what: 'Private funding across the frontier stack', since: 'Monthly', cadence: 'monthly' }
  ];
  IDX.forEach(function (d) { d.per = PERIOD[d.cadence]; d.v = null; d.c = null; d.s = []; d.stale = false; d.age = ''; d.fresh = ''; });
  var state = 'loading', asof = '';

  function fmtNum(v) { return v.toLocaleString('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }
  function fmtDate(s) {                       // "2026-10-26" -> "26 Oct 2026"; "2026-09" -> "Sep 2026"
    var m = /^(\d{4})-(\d{2})(?:-(\d{2}))?/.exec(String(s || ''));
    if (!m) return '';
    return (m[3] ? parseInt(m[3], 10) + ' ' : '') + MON[+m[2] - 1] + ' ' + m[1];
  }
  function cap(s) { return s ? s.charAt(0).toUpperCase() + s.slice(1) : ''; }
  // Age of a stale entry's last value: from its fresh_through date to today, in days,
  // or in months for the monthly index, whose fresh_through is a month.
  function ageOf(ft) {
    var m = /^(\d{4})-(\d{2})(?:-(\d{2}))?/.exec(String(ft || '')), now = new Date(), n, unit;
    if (!m) return '';
    if (m[3]) {
      n = Math.round((Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()) - Date.UTC(+m[1], +m[2] - 1, +m[3])) / 864e5);
      unit = 'day';
    } else {
      n = (now.getUTCFullYear() * 12 + now.getUTCMonth()) - (+m[1] * 12 + (+m[2] - 1));
      unit = 'month';
    }
    n = Math.max(0, n);
    return n + ' ' + unit + (n === 1 ? '' : 's');
  }
  function dirOf(d) { return !isNum(d.c) || d.c === 0 ? '' : (d.c > 0 ? 'up' : 'dn'); }
  function chgText(d) {
    if (!isNum(d.c)) return 'n/a';
    if (d.c === 0) return '0.00%';
    return (d.c > 0 ? '▲ +' : '▼ −') + Math.abs(d.c).toFixed(2) + '%';
  }
  function chgWords(d) {
    var over = PERIOD_WORDS[d.per] || d.per;
    if (!isNum(d.c)) return 'move over ' + over + ' not available';
    if (d.c === 0) return 'unchanged over ' + over;
    return (d.c > 0 ? 'up ' : 'down ') + Math.abs(d.c).toFixed(2) + ' per cent over ' + over;
  }
  function delayed(d) { return d.stale ? '<b class="dl">Delayed' + (d.age ? ', ' + d.age : '') + '</b>' : ''; }
  function spark(s) {
    var box = '<svg viewBox="0 0 200 52" preserveAspectRatio="none" aria-hidden="true">';
    if (s.length < 2) return box + '</svg>';
    var mn = Math.min.apply(0, s), mx = Math.max.apply(0, s), n = s.length;
    var l = 'M' + s.map(function (v, k) {
      return (k / (n - 1) * 200).toFixed(1) + ' ' + (48 - (v - mn) / ((mx - mn) || 1) * 40).toFixed(1);
    }).join('L');
    return box + '<path class="ar" d="' + l + 'L200 52L0 52Z"/><path class="ln" d="' + l + '"/></svg>';
  }

  function tileHTML(d, i) {
    var busy = state === 'loading', has = isNum(d.v);
    var cls = ['tile', dirOf(d), d.stale ? 'stale' : ''].join(' ').replace(/\s+/g, ' ').trim();
    var label = busy ? d.full + ', loading'
      : d.full + ', ' + (has ? fmtNum(d.v) : 'not available') + ', ' + chgWords(d) +
        (d.stale ? ', delayed: last value ' + fmtDate(d.fresh) + (d.age ? ', ' + d.age + ' old' : '') : '');
    return '<a class="' + cls + '" href="#ix' + i + '" data-i="' + i + '" aria-label="' + esc(label) + '">' +
      '<div class="top"><span class="nm">' + esc(d.name) + '</span><span class="cd">' + esc(cap(d.cadence)) + '</span></div>' +
      '<div class="v num">' + (has ? fmtNum(d.v) : (busy ? '&nbsp;' : 'n/a')) + '</div>' +
      '<div class="ch num">' + (busy ? '&nbsp;'
        : '<span' + (isNum(d.c) ? '' : ' class="na"') + '>' + chgText(d) + '</span><i>' + d.per + '</i>' + delayed(d)) + '</div>' +
      '<span class="go" aria-hidden="true">Open →</span>' + spark(d.s) + '</a>';
  }
  function rowHTML(d, i) {
    var busy = state === 'loading', has = isNum(d.v);
    return '<div class="row" id="ix' + i + '" tabindex="-1">' +
      '<span class="n">' + esc(d.full) + '</span><span class="w">' + esc(d.what) + '</span><span class="c">' + esc(d.since) + '</span>' +
      '<span class="x num">' + (has ? fmtNum(d.v) : (busy ? '&nbsp;' : 'n/a')) +
        '<span class="' + (isNum(d.c) ? dirOf(d) : 'na') + '">' + (busy ? '&nbsp;' : chgText(d) + ' ' + d.per) + '</span>' +
        delayed(d) + '</span></div>';
  }
  function renderIdx() {
    var busy = state === 'loading';
    $('tiles').innerHTML = IDX.map(tileHTML).join('');
    $('fam').innerHTML = IDX.map(rowHTML).join('');
    $('tiles').setAttribute('aria-busy', busy ? 'true' : 'false');
    $('fam').setAttribute('aria-busy', busy ? 'true' : 'false');
    $('asof').textContent = asof;
  }
  // A tile scrolls to the index family and highlights its row.
  function openIdx(i) {
    $('indexes').scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' });
    var row = $('ix' + i);
    if (!row) return;
    row.focus({ preventScroll: true });
    row.classList.add('flash');
    setTimeout(function () { row.classList.remove('flash'); }, 1300);
  }
  $('tiles').addEventListener('click', function (e) {
    var a = e.target.closest('.tile');
    if (!a) return;
    e.preventDefault();
    openIdx(+a.getAttribute('data-i'));
  });

  renderIdx();
  fetch(SUMMARY, { cache: 'no-cache' })
    .then(function (r) { if (!r.ok) throw new Error(SUMMARY + ': HTTP ' + r.status); return r.json(); })
    .then(function (j) {
      var ix = (j && j.indexes) || {}, latest = '';
      IDX.forEach(function (d) {
        var e = ix[d.key];
        if (!e) return;
        if (PERIOD[e.cadence]) { d.cadence = e.cadence; d.per = PERIOD[e.cadence]; }
        d.v = isNum(e.value) ? e.value : null;
        // a missing period, or {"null": true, "reason": ...}, reads n/a
        var ret = e.returns ? e.returns[d.per] : null;
        d.c = isNum(ret) ? ret : null;
        d.s = (Array.isArray(e.series) ? e.series : []).slice(-48)
          .map(function (p) { return p ? p.value : null; }).filter(isNum);
        d.fresh = e.fresh_through || '';
        // freshness_rule: a stale entry shows its last value, marked delayed, with its age
        d.stale = e.status === 'stale' && d.v !== null;
        d.age = d.stale ? ageOf(d.fresh) : '';
        if (/^\d{4}-\d{2}-\d{2}$/.test(d.fresh) && d.fresh > latest) latest = d.fresh;
      });
      state = IDX.some(function (d) { return d.v !== null; }) ? 'ready' : 'error';
      asof = state === 'ready' ? (latest ? 'As of ' + fmtDate(latest) : '') : 'Index data unavailable';
      renderIdx();
    })
    .catch(function () {
      state = 'error';
      asof = 'Index data unavailable';
      renderIdx();
    });

  /* ---------- marquee of the eight tiers ---------- */
  var TIERS = ['Upstream Materials', 'IP & Design', 'Capital Equipment', 'Fabrication & Manufacturing', 'Components & Subsystems', 'System Integration', 'Deployment & Operation', 'Software & Services'];
  var once = TIERS.map(function (n, i) { return '<span><small>0' + (i + 1) + '</small>' + esc(n) + '</span>'; }).join('');
  $('marq').innerHTML = once + once;

  /* ---------- the stack map: index members per cell, tiers in the locked order ---------- */
  // STOPGAP: these per-cell counts are hard-coded from the v1 data inventory, as in the
  // mock. They belong in a feed (market_layer.json, or counts from the entity registry)
  // and should be read from it once it exists. Rows run Materials, Semiconductors,
  // Robotics, Space; columns follow TIERS.
  var SECT = [
    { n: 'Materials', k: '--ma', c: [30, 0, 0, 1, 0, 0, 0, 0] },
    { n: 'Semiconductors', k: '--se', c: [1, 32, 18, 13, 15, 0, 0, 1] },
    { n: 'Robotics', k: '--ro', c: [0, 0, 0, 0, 22, 34, 1, 7] },
    { n: 'Space', k: '--sp', c: [0, 0, 0, 0, 6, 17, 13, 0] }
  ];
  var map = $('map'), h = '<div class="th" aria-hidden="true"></div>';
  TIERS.forEach(function (n, i) { h += '<div class="th"><b>0' + (i + 1) + '</b><span>' + esc(n) + '</span></div>'; });
  SECT.forEach(function (s, r) {
    h += '<div class="sl" style="--sc:var(' + s.k + ')"><i style="background:var(' + s.k + ')"></i>' + s.n + '</div>';
    s.c.forEach(function (v, c) {
      var id = 'm' + r + '_' + c;
      if (v >= 3) h += '<div class="cell full" id="' + id + '" style="--sc:var(' + s.k + ')"><div class="n">' + v + '</div><div class="u">companies</div></div>';
      else if (v > 0) h += '<div class="cell thin" id="' + id + '"><div class="n">' + v + ' company</div><div class="u">Figures withheld</div></div>';
      else h += '<div class="cell" id="' + id + '"></div>';
    });
  });
  map.innerHTML = h + '<svg class="trace" id="trace" aria-hidden="true"></svg>';

  // ILLUSTRATIVE trace, labelled as such on the page: an export control on semiconductor
  // capital equipment, followed downstream. To be replaced by a real dated event once
  // events.json exists (task 3b).
  var SRC = [1, 2], HITS = [[1, 3], [1, 4], [2, 4], [3, 4], [2, 5], [3, 5]];
  var EDGES = [[[1, 2], [1, 3]], [[1, 3], [1, 4]], [[1, 4], [2, 4], 0.34], [[1, 4], [3, 4], 0.6], [[2, 4], [2, 5]], [[3, 4], [3, 5]]];
  var SRCID = 'm' + SRC[0] + '_' + SRC[1];
  $(SRCID).insertAdjacentHTML('beforeend', '<span class="tag">Export control</span>');
  var trace = $('trace');
  function cellBox(rc) { var el = $('m' + rc[0] + '_' + rc[1]); return { x: el.offsetLeft, y: el.offsetTop, w: el.offsetWidth, h: el.offsetHeight }; }
  function drawTrace() {
    var p = '';
    EDGES.forEach(function (e, i) {
      var a = cellBox(e[0]), b = cellBox(e[1]), f = e[2], d, hd, st, dl = i * 0.42 + 0.2;
      if (e[0][0] === e[1][0]) {
        var y = Math.round(a.y + a.h * 0.76), x1 = a.x + a.w - 34, x2 = b.x + 20;
        d = 'M' + x1 + ' ' + y + 'H' + x2; hd = 'M' + (x2 + 9) + ' ' + y + 'l-10 -5.5v11z'; st = [x1, y];
      } else {
        var x = Math.round(a.x + a.w * f), y1 = a.y + a.h - 20, y2 = b.y + 16;
        d = 'M' + x + ' ' + y1 + 'V' + y2; hd = 'M' + x + ' ' + (y2 + 9) + 'l-5.5 -10h11z'; st = [x, y1];
      }
      p += '<circle class="hd" cx="' + st[0] + '" cy="' + st[1] + '" r="3.5" style="transition-delay:' + dl.toFixed(2) + 's"/>' +
        '<path class="ln" pathLength="1" style="transition-delay:' + dl.toFixed(2) + 's" d="' + d + '"/>' +
        '<path class="hd" style="transition-delay:' + (dl + 0.34).toFixed(2) + 's" d="' + hd + '"/>';
    });
    trace.innerHTML = p;
  }
  drawTrace();
  // The cells change size with the viewport and again when the web fonts arrive.
  if ('ResizeObserver' in window) new ResizeObserver(drawTrace).observe(map);
  else window.addEventListener('resize', drawTrace);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(drawTrace);

  var timers = [];
  function play() {
    timers.forEach(clearTimeout); timers = [];
    map.classList.remove('on');
    $(SRCID).classList.remove('src');
    HITS.forEach(function (rc) { $('m' + rc[0] + '_' + rc[1]).classList.remove('hit'); });
    void map.offsetWidth;
    $(SRCID).classList.add('src');
    map.classList.add('on');
    if (reduce) { HITS.forEach(function (rc) { $('m' + rc[0] + '_' + rc[1]).classList.add('hit'); }); return; }
    var at = [0.55, 0.97, 1.39, 1.39, 1.81, 1.81];
    HITS.forEach(function (rc, i) {
      timers.push(setTimeout(function () { $('m' + rc[0] + '_' + rc[1]).classList.add('hit'); }, at[i] * 1000));
    });
  }
  // The trace plays on arrival and replays every 15 seconds while the map is on screen.
  var cycle = 0, REPLAY = 15000, SEEN = 0.45, onScreen = false;
  function loopOn() { if (cycle || reduce) return; cycle = setInterval(play, REPLAY); }
  function loopOff() { clearInterval(cycle); cycle = 0; }
  if ('IntersectionObserver' in window) {
    // Watch the scroller: on phones the map itself is wider than the screen.
    new IntersectionObserver(function (en) {
      var e = en[en.length - 1];
      onScreen = e.isIntersecting && e.intersectionRatio >= SEEN - 0.001;
      if (onScreen) { if (!cycle) { play(); loopOn(); } }
      else loopOff();
    }, { threshold: [0, SEEN] }).observe($('mapscroll'));
  } else play();
  document.addEventListener('visibilitychange', function () {
    if (document.hidden) loopOff();
    else if (onScreen) loopOn();
  });
  $('replay').addEventListener('click', function () { loopOff(); play(); loopOn(); });

  /* ---------- walkthrough poster: the map in miniature ---------- */
  var vp = '';
  SECT.forEach(function (s, r) {
    s.c.forEach(function (v, c) {
      var hit = (r === 1 && c >= 2 && c <= 4) || ((r === 2 || r === 3) && (c === 4 || c === 5));
      vp += '<i class="' + (hit ? 'h' : v >= 3 ? 'f' : '') + '"></i>';
    });
  });
  $('vposter').innerHTML = vp;

  /* ---------- the robots: head sheet inside a glass helmet; glances, blinks, spins on click ---------- */
  var BOT = 'assets/robot/';
  var stages = [].slice.call(document.querySelectorAll('.stage'));
  if (reduce) {
    // He stays still, so the label offers no spin.
    stages.forEach(function (st) {
      var b = st.querySelector('.robot');
      if (b) b.setAttribute('aria-label', b.getAttribute('aria-label').replace(/ Press to make him spin his head\.$/, ''));
    });
  }
  // The head sheet is requested once the page has first appeared: after the load event,
  // or after 3 seconds if a slow third-party script holds that event back.
  function afterFirstLoad(fn) {
    var done = false;
    function go() { if (!done) { done = true; fn(); } }
    if (document.readyState === 'complete') setTimeout(go, 0);
    else { window.addEventListener('load', go); setTimeout(go, 3000); }
  }
  function setUp(cfg) {
    var W = cfg.body[0], H = cfg.body[1], cols = cfg.cols, rows = cfg.rows, N = cfg.n, BL = cfg.blink;
    var heads = [];
    function box(el, x, y, w, hh) {
      el.style.left = (x / W * 100).toFixed(4) + '%';
      el.style.top = (y / H * 100).toFixed(4) + '%';
      el.style.width = (w / W * 100).toFixed(4) + '%';
      el.style.height = (hh / H * 100).toFixed(4) + '%';
    }
    function wrap(f) { return ((f % N) + N) % N; }
    function delta(a, b) { var d = wrap(b - a); return d > N / 2 ? d - N : d; }
    function frameFor(deg) { return wrap(Math.round(deg / (360 / N))); }
    function easeOut(u) { return 1 - Math.pow(1 - u, 3); }

    stages.forEach(function (stage) {
      var btn = stage.querySelector('.robot'), head = stage.querySelector('.rb-h'), glass = stage.querySelector('.rb-g');
      if (!btn || !head || !glass) return;
      btn.style.aspectRatio = W + ' / ' + H;
      box(head, cfg.head[0], cfg.head[1], cfg.frame[0], cfg.frame[1]);
      head.style.backgroundSize = (cols * 100) + '% ' + (rows * 100) + '%';
      box(glass, cfg.glass[0], cfg.glass[1], cfg.glass[2], cfg.glass[3]);
      glass.style.backgroundImage = 'url(' + BOT + 'robot-glass.webp)';
      heads.push(head);

      var rest = +stage.getAttribute('data-rest') || 0;
      var gl = (stage.getAttribute('data-glances') || '0').split(',').map(Number);
      var t0 = performance.now();
      var R = { cur: rest, tgt: rest, spin: null, blink: 0, nextBlink: t0 + 1800 + Math.random() * 2000, step: 0, gi: -1, nextGlance: t0 + 2400, vis: true, raf: 0, shown: -1 };
      // Frame k of the sheet: angles 0 to N-1 in 360/N degree steps, then the blink frames.
      function show() {
        var k = R.cur;
        if (R.blink) { var b = BL.indexOf(R.cur); if (b >= 0) k = N + b; }
        if (k === R.shown) return;
        R.shown = k;
        head.style.backgroundPosition = (k % cols) * (100 / (cols - 1)) + '% ' + Math.floor(k / cols) * (100 / (rows - 1)) + '%';
      }
      function tick(now) {
        if (R.spin) {
          var u = (now - R.spin.t0) / 1150;
          if (u >= 1) { R.spin = null; R.cur = R.tgt; } else R.cur = wrap(R.spin.from + Math.round(easeOut(u) * N));
        } else {
          if (now > R.nextGlance) {
            R.gi = (R.gi + 1) % gl.length;
            R.tgt = frameFor(gl[R.gi]);
            R.nextGlance = now + (gl[R.gi] === 0 || R.tgt === rest ? 4200 + Math.random() * 2400 : 1700);
          }
          if (R.cur !== R.tgt && now - R.step > 38) { R.cur = wrap(R.cur + Math.sign(delta(R.cur, R.tgt))); R.step = now; }
        }
        if (!R.blink && now > R.nextBlink && !R.spin) R.blink = now;
        if (R.blink && now - R.blink > 130) { R.blink = 0; R.nextBlink = now + 2400 + Math.random() * 3600; }
        show();
        R.raf = R.vis ? requestAnimationFrame(tick) : 0;
      }
      // A full turn of the head on click, Enter or tap.
      btn.addEventListener('click', function () {
        if (reduce || R.spin) return;
        R.spin = { t0: performance.now(), from: R.cur };
        R.tgt = R.cur;
      });
      show();
      if (!reduce) {
        if ('IntersectionObserver' in window) {
          new IntersectionObserver(function (en) {
            R.vis = en[en.length - 1].isIntersecting;
            if (R.vis && !R.raf) R.raf = requestAnimationFrame(tick);
          }).observe(stage);
        }
        R.raf = requestAnimationFrame(tick);
      }
    });

    afterFirstLoad(function () {
      var img = new Image(), src = BOT + 'robot-head.webp';
      img.src = src;
      (img.decode ? img.decode() : new Promise(function (ok, no) { img.onload = ok; img.onerror = no; }))
        .then(function () {
          heads.forEach(function (hd) { hd.style.backgroundImage = 'url(' + src + ')'; });
          requestAnimationFrame(function () { heads.forEach(function (hd) { hd.classList.add('on'); }); });
        })
        .catch(function () {});
    });
  }
  fetch(BOT + 'robot.json')
    .then(function (r) { if (!r.ok) throw new Error(BOT + 'robot.json: HTTP ' + r.status); return r.json(); })
    .then(setUp)
    .catch(function () {});
})();
