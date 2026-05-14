(function() {
  const currentPage = document.body.dataset.page || 'home';

  const navItems = [
    { href: 'index.html', page: 'home', label: 'Home', online: true },
    { href: 'assets.html', page: 'assets', label: 'Frontier Assets', online: true },
    { href: 'funding.html', page: 'funding', label: 'Funding Ops', online: true },
    { href: 'portfolio.html', page: 'portfolio', label: 'Portfolio', online: false },
    { href: 'signals.html', page: 'signals', label: 'Frontier Signals', online: false },
    { href: 'commodities.html', page: 'commodities', label: 'Commodities', online: false },
    { href: 'recreation.html', page: 'recreation', label: 'Recreation Bay', online: true },
  ];

  const links = navItems.map(item => {
    const isActive = item.page === currentPage;
    const isDisabled = !item.online;
    let cls = 'nav-item';
    if (isActive) cls += ' active';
    if (isDisabled) cls += ' disabled';
    const dot = item.online
      ? '<span class="status-dot online"></span>'
      : '<span class="status-dot offline"></span>';
    const soonBadge = isDisabled
      ? '<span style="font-size:8px;color:#5A6178;border:1px solid #2A2F3A;padding:1px 4px;border-radius:2px;margin-left:6px">SOON</span>'
      : '';
    return `<a href="${item.href}" class="${cls}">
      <span class="nav-label">${item.label}${soonBadge}</span>
      ${dot}
    </a>`;
  }).join('');

  const sidebar = `
    <aside class="sidebar">
      <div class="sidebar-top">
        <a href="index.html" class="sidebar-logo">
          <img src="robotlogo.png" alt="Robotnik" class="sidebar-logo-img">
          <span class="sidebar-logo-text">ROBOTNIK</span>
        </a>
        <nav class="sidebar-nav">
          ${links}
        </nav>
      </div>
      <div class="sidebar-bottom">
        <div class="sidebar-tagline">
          <span style="color:var(--yellow)">ROBOTNIK</span><br>
          <span style="color:var(--text)">Live: private market data.</span><br>
          <span style="color:var(--text)">Coming: more.</span><span class="animated-dots" style="color:var(--text)"></span>
          <div style="margin-top:0.4rem;color:var(--text-muted);line-height:1.5;">The intelligence layer<br>for the frontier<br>technology stack</div>
        </div>
      </div>
    </aside>
  `;

  const topBar = `
    <header class="top-bar">
      <div class="top-bar-left">
        <input type="text" class="top-search" placeholder="Search assets, funding..." />
      </div>
    </header>
  `;

  document.getElementById('nav-container').innerHTML = sidebar + topBar;

  // Early Access modal (shared across all pages)
  // Submissions POST to a Google Apps Script web app bound to a
  // private Sheet in Robert's Workspace. See scripts/apps-script.gs
  // for the server side. The URL below is set after deployment.
  var EARLY_ACCESS_URL = 'https://script.google.com/macros/s/AKfycbwwfRNzBJ-Nv607kbjhadO7g68x5jO2typxdP5tQ7lluZYTaB9CZ43HZbc2F6SXctRD5w/exec';
  var modalDiv = document.createElement('div');
  modalDiv.id = 'early-access-modal';
  modalDiv.style.cssText = 'display:none;position:fixed;inset:0;z-index:1000;background:rgba(0,0,0,0.8);align-items:flex-start;justify-content:center;overflow-y:auto;padding:3rem 1rem;';
  var inputStyle = "width:100%;padding:0.55rem 0.65rem;background:#111;border:1px solid #333;color:#E0E0E0;border-radius:3px;font-family:'Mulish',sans-serif;font-size:12px;box-sizing:border-box;";
  var labelStyle = "display:block;color:#8B92A5;font-size:10px;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:0.25rem;font-family:'Space Grotesk',sans-serif;";
  var reqDot = '<span style="color:#F5D921;margin-left:3px;">*</span>';
  modalDiv.innerHTML = '' +
    '<div style="background:#0A0A0F;border:1px solid #333;border-radius:8px;padding:1.75rem 2rem 1.5rem;max-width:520px;width:100%;position:relative;font-family:\'Mulish\',sans-serif;margin:auto;">' +
      '<button type="button" id="ea-close-btn" aria-label="Close" style="position:absolute;top:12px;right:16px;background:none;border:none;color:#888;font-size:18px;cursor:pointer;line-height:1;">&#10005;</button>' +
      '<h3 style="color:#F5D921;font-size:12px;letter-spacing:0.1em;margin:0 0 0.5rem;font-family:\'Space Grotesk\',sans-serif;">REQUEST EARLY ACCESS</h3>' +
      '<p style="color:#8B92A5;font-size:11px;line-height:1.55;margin:0 0 1.25rem;">' +
        'Join the Robotnik early access programme. Enterprise operatives receive the full Intelligence data layer, funding database, news archive, data export, and priority access to Portfolio Intelligence, Frontier Signals, and Commodities as they launch.' +
      '</p>' +
      '<form id="early-access-form" novalidate style="display:flex;flex-direction:column;gap:0.9rem;">' +
        '<div style="display:grid;grid-template-columns:1fr 1fr;gap:0.75rem;">' +
          '<div><label style="' + labelStyle + '" for="ea-name">Full name' + reqDot + '</label>' +
            '<input type="text" id="ea-name" name="name" required autocomplete="name" style="' + inputStyle + '"></div>' +
          '<div><label style="' + labelStyle + '" for="ea-email">Work email' + reqDot + '</label>' +
            '<input type="email" id="ea-email" name="email" required autocomplete="email" style="' + inputStyle + '"></div>' +
          '<div><label style="' + labelStyle + '" for="ea-org">Organisation' + reqDot + '</label>' +
            '<input type="text" id="ea-org" name="organisation" required autocomplete="organization" placeholder="Company, firm, or institution" style="' + inputStyle + '"></div>' +
          '<div><label style="' + labelStyle + '" for="ea-role">Role' + reqDot + '</label>' +
            '<input type="text" id="ea-role" name="role" required autocomplete="organization-title" placeholder="Your job title" style="' + inputStyle + '"></div>' +
        '</div>' +
        '<div><label style="' + labelStyle + '" for="ea-linkedin">LinkedIn profile' + reqDot + '</label>' +
          '<input type="url" id="ea-linkedin" name="linkedin" required placeholder="https://linkedin.com/in/yourname" style="' + inputStyle + '"></div>' +
        '<div><label style="' + labelStyle + '" for="ea-usecase">What would you use Robotnik for?' + reqDot + '</label>' +
          '<textarea id="ea-usecase" name="use_case" required rows="4" placeholder="Briefly describe how Robotnik would support your work. What sectors are you most interested in? What types of analysis do you need?" style="' + inputStyle + 'resize:vertical;min-height:84px;line-height:1.5;"></textarea></div>' +
        '<div><label style="' + labelStyle + '" for="ea-heard">How did you hear about Robotnik?' + reqDot + '</label>' +
          '<select id="ea-heard" name="how_did_you_hear" required style="' + inputStyle + 'appearance:none;">' +
            '<option value="" disabled selected hidden>Select one</option>' +
            '<option value="LinkedIn">LinkedIn</option>' +
            '<option value="Twitter/X">Twitter / X</option>' +
            '<option value="Referral">Referral</option>' +
            '<option value="Search">Search</option>' +
            '<option value="News article">News article</option>' +
            '<option value="Other">Other</option>' +
          '</select></div>' +
        '<input type="hidden" name="source_page" id="ea-source-page">' +
        '<div id="ea-error" role="alert" style="display:none;color:#ef4444;font-size:11px;line-height:1.4;"></div>' +
        '<button type="submit" id="ea-submit-btn" style="margin-top:0.25rem;padding:0.7rem;background:#F5D921;color:#0A0A0F;font-family:\'Space Grotesk\',sans-serif;font-weight:700;font-size:11px;letter-spacing:0.08em;border:none;border-radius:3px;cursor:pointer;text-transform:uppercase;">Request Early Access</button>' +
      '</form>' +
      '<div id="ea-success" style="display:none;padding:1rem 0 0.25rem;">' +
        '<p style="color:#22c55e;font-size:13px;font-weight:600;margin:0 0 0.5rem;">Thank you for your interest.</p>' +
        '<p style="color:#8B92A5;font-size:11px;line-height:1.5;margin:0;">Robert will be in touch shortly.</p>' +
      '</div>' +
      '<p style="color:#5A6178;font-size:9px;line-height:1.5;margin:1rem 0 0;">' +
        'Submissions are stored in Robert\'s Google Workspace solely to respond to your enquiry. No IP address or cookies are logged.' +
      '</p>' +
    '</div>';
  document.body.appendChild(modalDiv);

  document.getElementById('ea-close-btn').addEventListener('click', function() {
    modalDiv.style.display = 'none';
  });
  modalDiv.addEventListener('click', function(e) { if (e.target === modalDiv) modalDiv.style.display = 'none'; });

  var form = document.getElementById('early-access-form');
  var submitBtn = document.getElementById('ea-submit-btn');
  var errorBox = document.getElementById('ea-error');
  var successBox = document.getElementById('ea-success');

  form.addEventListener('submit', function(ev) {
    ev.preventDefault();
    errorBox.style.display = 'none';
    errorBox.textContent = '';
    // Browser-native validation for required + email format first.
    if (!form.checkValidity()) {
      form.reportValidity();
      return;
    }
    var data = {
      name:             document.getElementById('ea-name').value.trim(),
      email:            document.getElementById('ea-email').value.trim(),
      organisation:     document.getElementById('ea-org').value.trim(),
      role:             document.getElementById('ea-role').value.trim(),
      linkedin:         document.getElementById('ea-linkedin').value.trim(),
      use_case:         document.getElementById('ea-usecase').value.trim(),
      how_did_you_hear: document.getElementById('ea-heard').value,
      source_page:      window.location.pathname || '/',
      user_agent:       (navigator && navigator.userAgent) || '',
    };
    submitBtn.disabled = true;
    var originalLabel = submitBtn.textContent;
    submitBtn.textContent = 'Submitting…';
    // Content-Type text/plain keeps the POST a CORS-simple request so
    // Apps Script can respond without a preflight. The server still
    // reads JSON from postData.contents.
    fetch(EARLY_ACCESS_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain;charset=utf-8' },
      body: JSON.stringify(data),
    }).then(function(resp) {
      return resp.json().catch(function() { return { status: 'error', message: 'Unreadable response' }; });
    }).then(function(result) {
      if (result && result.status === 'ok') {
        form.style.display = 'none';
        successBox.style.display = 'block';
        setTimeout(function() {
          modalDiv.style.display = 'none';
          // Reset for a subsequent open: show form again, clear fields.
          setTimeout(function() {
            form.reset();
            form.style.display = 'flex';
            successBox.style.display = 'none';
            submitBtn.disabled = false;
            submitBtn.textContent = originalLabel;
          }, 400);
        }, 3000);
      } else {
        var msg = (result && result.message) ? result.message :
                  'Something went wrong. Please try again, or email robert@robotnik.world directly.';
        errorBox.textContent = msg;
        errorBox.style.display = 'block';
        submitBtn.disabled = false;
        submitBtn.textContent = originalLabel;
      }
    }).catch(function() {
      errorBox.textContent = 'Something went wrong. Please try again, or email robert@robotnik.world directly.';
      errorBox.style.display = 'block';
      submitBtn.disabled = false;
      submitBtn.textContent = originalLabel;
    });
  });

  // ─────────────────────────────────────────────────────────────────
  // Top-bar search
  // ─────────────────────────────────────────────────────────────────
  // Client-side substring match across existing datasets. The
  // Messari-style command palette (cmd+K, LLM query routing, etc.)
  // is the separate Q2 "Intelligence Queries" project — intentionally
  // out of scope here. Keep this stub: load JSON on first keystroke,
  // cache in memory, rank results per category (Research → Assets →
  // Funding), cap at 10 total.
  var searchInput = document.querySelector('.top-search');
  var searchHost = document.querySelector('.top-bar-left');
  if (searchInput && searchHost) {
    searchInput.setAttribute('autocomplete', 'off');
    searchInput.setAttribute('placeholder', 'Search assets, funding...');
    searchHost.style.position = 'relative';

    var dropdown = document.createElement('div');
    dropdown.className = 'search-dropdown';
    dropdown.style.display = 'none';
    searchHost.appendChild(dropdown);

    // Hardcoded for now — the only published research is the 1Q26 report.
    var RESEARCH = [{
      title: '1Q26 State of the Frontier Stack',
      desc: 'Inaugural quarterly report — semiconductors, robotics, space, critical materials',
      tags: ['1q26', 'report', 'quarterly', 'frontier stack', 'state of the frontier', 'nvidia', 'waymo', 'rare earth', 'rare earths'],
      url: 'report-1Q26.html',
    }];

    var _datasets = null;
    function loadDatasets() {
      if (_datasets) return Promise.resolve(_datasets);
      return Promise.all([
        fetch('data/markets/robotnik_public_markets.json').then(function(r){return r.ok?r.json():null;}).catch(function(){return null;}),
        fetch('data/funding/rounds.json').then(function(r){return r.ok?r.json():null;}).catch(function(){return null;}),
      ]).then(function(out){
        _datasets = { pm: out[0], rounds: out[1] };
        return _datasets;
      });
    }

    function escHtml(s) {
      return String(s == null ? '' : s).replace(/[&<>"']/g, function(c){
        return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
      });
    }

    function searchAll(q, ds) {
      var ql = q.toLowerCase();
      var out = [];

      // 1. Research (hardcoded)
      RESEARCH.forEach(function(r){
        var hay = (r.title + ' ' + r.desc + ' ' + (r.tags || []).join(' ')).toLowerCase();
        if (hay.indexOf(ql) !== -1) {
          out.push({
            category: 'Research',
            primary: r.title,
            secondary: r.desc,
            url: r.url,
          });
        }
      });

      // 2. Assets
      if (ds.pm && ds.pm.entities) {
        var assetMatches = [];
        var tickers = Object.keys(ds.pm.entities);
        for (var i = 0; i < tickers.length; i++) {
          var ticker = tickers[i];
          var ent = ds.pm.entities[ticker];
          var tl = String(ticker || '').toLowerCase();
          var nl = String(ent.name || '').toLowerCase();
          var sl = String(ent.sector || '').toLowerCase();
          if (tl.indexOf(ql) !== -1 || nl.indexOf(ql) !== -1 || sl.indexOf(ql) !== -1) {
            // Rank: exact-ticker > ticker-prefix > name-prefix > substring.
            var rank = 3;
            if (tl === ql) rank = 0;
            else if (tl.indexOf(ql) === 0) rank = 1;
            else if (nl.indexOf(ql) === 0) rank = 2;
            assetMatches.push({
              category: 'Assets',
              primary: ent.name || ticker,
              secondary: ticker + (ent.sector ? (' · ' + ent.sector) : ''),
              url: 'assets.html?q=' + encodeURIComponent(ticker),
              _rank: rank,
            });
          }
        }
        assetMatches.sort(function(a,b){ return a._rank - b._rank; });
        out.push.apply(out, assetMatches);
      }

      // 3. Funding
      if (ds.rounds && Array.isArray(ds.rounds.rounds)) {
        for (var k = 0; k < ds.rounds.rounds.length; k++) {
          var rnd = ds.rounds.rounds[k];
          var co = String(rnd.company || '').toLowerCase();
          var lead = String(rnd.lead_investors || '').toLowerCase();
          var rsec = String(rnd.sector || '').toLowerCase();
          if (co.indexOf(ql) !== -1 || lead.indexOf(ql) !== -1 || rsec.indexOf(ql) !== -1) {
            var amt = rnd.amount_m ? ('$' + rnd.amount_m + 'm') : '';
            var secStr = [amt, rnd.round, rnd.date].filter(Boolean).join(' · ');
            out.push({
              category: 'Funding',
              primary: rnd.company,
              secondary: secStr,
              url: 'funding.html',
            });
          }
        }
      }

      return out.slice(0, 10);
    }

    var _results = [];
    var _activeIdx = -1;

    function rowNodes() {
      return dropdown.querySelectorAll('.search-dropdown__row');
    }

    function updateActive() {
      var nodes = rowNodes();
      for (var i = 0; i < nodes.length; i++) {
        nodes[i].classList.toggle('search-dropdown__row--active', i === _activeIdx);
      }
      if (_activeIdx >= 0 && nodes[_activeIdx]) {
        nodes[_activeIdx].scrollIntoView({ block: 'nearest' });
      }
    }

    var EMPTY_EXAMPLES = ['NVIDIA', 'rare earths', 'Waymo', '1Q26 report'];

    function renderEmptyState() {
      var html = '<div class="search-dropdown__empty">' +
                 '<span class="search-dropdown__try-label">Try:</span>';
      for (var i = 0; i < EMPTY_EXAMPLES.length; i++) {
        html += '<a class="search-dropdown__try-example" data-example="' +
                escHtml(EMPTY_EXAMPLES[i]) + '" href="#">' +
                escHtml(EMPTY_EXAMPLES[i]) + '</a>';
      }
      html += '</div>';
      dropdown.innerHTML = html;
      dropdown.style.display = 'block';
    }

    function renderResults(results, query) {
      _results = results;
      _activeIdx = -1;
      if (!results.length) {
        dropdown.innerHTML = '<div class="search-dropdown__no-results">' +
          'No results for "' + escHtml(query || '') + '".</div>';
        dropdown.style.display = 'block';
        return;
      }
      // Count per category for the header labels.
      var counts = {};
      for (var c = 0; c < results.length; c++) {
        counts[results[c].category] = (counts[results[c].category] || 0) + 1;
      }
      var html = '';
      var lastCat = '';
      for (var i = 0; i < results.length; i++) {
        var r = results[i];
        if (r.category !== lastCat) {
          html += '<div class="search-dropdown__category">' +
                  '<span>' + escHtml(r.category) + '</span>' +
                  '<span class="search-dropdown__category-count">(' + counts[r.category] + ')</span>' +
                  '</div>';
          lastCat = r.category;
        }
        var tgt = r.external ? ' target="_blank" rel="noopener"' : '';
        html += '<a class="search-dropdown__row" data-idx="' + i + '" href="' +
                escHtml(r.url) + '"' + tgt + '>' +
                '<div class="search-dropdown__row-primary">' + escHtml(r.primary) + '</div>' +
                '<div class="search-dropdown__row-secondary">' + escHtml(r.secondary) + '</div>' +
                '</a>';
      }
      dropdown.innerHTML = html;
      dropdown.style.display = 'block';
    }

    function closeDropdown() {
      dropdown.style.display = 'none';
      _activeIdx = -1;
    }

    function runQuery(q) {
      loadDatasets().then(function(ds){
        // Guard against stale responses if user kept typing.
        if (searchInput.value.trim() !== q) return;
        renderResults(searchAll(q, ds), q);
      });
    }

    searchInput.addEventListener('input', function(){
      var q = searchInput.value.trim();
      if (!q) { renderEmptyState(); return; }
      runQuery(q);
    });

    searchInput.addEventListener('focus', function(){
      if (!searchInput.value.trim()) renderEmptyState();
      else if (_results.length) renderResults(_results, searchInput.value.trim());
    });

    searchInput.addEventListener('keydown', function(e){
      var nodes = rowNodes();
      var n = nodes.length;
      if (e.key === 'ArrowDown') {
        if (!n) return;
        e.preventDefault();
        _activeIdx = (_activeIdx + 1) % n;
        updateActive();
      } else if (e.key === 'ArrowUp') {
        if (!n) return;
        e.preventDefault();
        _activeIdx = (_activeIdx - 1 + n) % n;
        updateActive();
      } else if (e.key === 'Enter') {
        if (_activeIdx >= 0 && nodes[_activeIdx]) {
          e.preventDefault();
          nodes[_activeIdx].click();
        }
      } else if (e.key === 'Escape') {
        e.preventDefault();
        closeDropdown();
        searchInput.blur();
      }
    });

    // Click-outside closes the dropdown.
    document.addEventListener('click', function(e){
      if (!searchHost.contains(e.target)) closeDropdown();
    });

    // Clicking a "Try:" example fills the input and runs the search.
    dropdown.addEventListener('click', function(e){
      var tgt = e.target.closest('.search-dropdown__try-example');
      if (!tgt) return;
      e.preventDefault();
      var val = tgt.dataset.example || tgt.textContent;
      searchInput.value = val;
      searchInput.focus();
      runQuery(val.trim());
    });
  }
})();

// Global function to open early access modal
function openEarlyAccess() {
  var m = document.getElementById('early-access-modal');
  if (!m) return;
  // Refresh the source_page hidden field in case the user navigated
  // between pages since the nav rendered.
  var sp = document.getElementById('ea-source-page');
  if (sp) sp.value = window.location.pathname || '/';
  m.style.display = 'flex';
  // Focus the first input for keyboard users.
  setTimeout(function() {
    var first = document.getElementById('ea-name');
    if (first) first.focus();
  }, 50);
}
