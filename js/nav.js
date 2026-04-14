(function() {
  const currentPage = document.body.dataset.page || 'home';

  const navItems = [
    { href: 'index.html', page: 'home', label: 'Home', online: true },
    { href: 'news.html', page: 'news', label: 'News', online: true },
    { href: 'intelligence.html', page: 'intelligence', label: 'Intelligence', online: true },
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
          <span style="color:var(--yellow)">ROBOTNIK</span> <span style="color:var(--text)">RE-ENTRY</span><br>
          <span style="color:var(--text)">IN PROGRESS</span><span class="animated-dots" style="color:var(--text)"></span>
          <div style="margin-top:0.4rem;color:var(--text-muted);line-height:1.5;">The intelligence layer<br>for the frontier<br>technology stack</div>
        </div>
      </div>
    </aside>
  `;

  const topBar = `
    <header class="top-bar">
      <div class="top-bar-left">
        <input type="text" class="top-search" placeholder="Search assets, news, research..." />
      </div>
      <div class="top-bar-right">
        <a href="index.html#signup" class="btn-y">Request Enterprise Clearance</a>
      </div>
    </header>
  `;

  document.getElementById('nav-container').innerHTML = sidebar + topBar;
})();
