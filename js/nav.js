(function() {
  const currentPage = document.body.dataset.page || 'home';

  const navItems = [
    { href: 'index.html', page: 'home', label: 'Home', online: true },
    { href: 'intelligence.html', page: 'intelligence', label: 'Intelligence', online: true },
    { href: 'signals.html', page: 'signals', label: 'Market Signals', online: false },
    { href: 'funding.html', page: 'funding', label: 'Funding Ops', online: false },
    { href: 'thesis.html', page: 'thesis', label: 'Thesis', online: true },
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
    const tooltip = isDisabled ? ' title="Module calibrating..."' : '';
    const tag = isDisabled ? 'span' : 'a';
    const hrefAttr = isDisabled ? '' : ` href="${item.href}"`;
    return `<${tag}${hrefAttr} class="${cls}"${tooltip}>
      <span class="nav-label">${item.label}</span>
      ${dot}
    </${tag}>`;
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
        <div class="sidebar-version">v0.1 // Pre-launch</div>
        <div class="sidebar-attrib">Data by <a href="https://www.coingecko.com" target="_blank" rel="noopener">CoinGecko</a></div>
      </div>
    </aside>
  `;

  const topBar = `
    <header class="top-bar">
      <div class="top-bar-left">
        <input type="text" class="top-search" placeholder="Search assets, news, research..." />
      </div>
      <div class="top-bar-right">
        <a href="thesis.html#signup" class="btn-y">Request clearance</a>
      </div>
    </header>
  `;

  document.getElementById('nav-container').innerHTML = sidebar + topBar;
})();
