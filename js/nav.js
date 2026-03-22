(function() {
  const currentPage = document.body.dataset.page || 'home';

  const navItems = [
    { href: 'index.html', page: 'home', label: 'Home' },
    { href: 'signals.html', page: 'signals', label: 'Market Signals' },
    { href: 'funding.html', page: 'funding', label: 'Funding Operations' },
    { href: 'intelligence.html', page: 'intelligence', label: 'Intelligence' },
    { href: 'thesis.html', page: 'thesis', label: 'Thesis' },
    { href: 'recreation.html', page: 'recreation', label: 'Recreation Bay' },
  ];

  const links = navItems.map(item => {
    const activeClass = (item.page === currentPage) ? ' active' : '';
    return `<li><a href="${item.href}" class="hm${activeClass}">${item.label}</a></li>`;
  }).join('');

  document.getElementById('nav-container').innerHTML = `
    <nav>
      <a class="logo" href="index.html">
        <div class="logo-mark"><img src="robotlogo.png" alt="Robotnik"></div>
        <span class="logo-text">Robotnik</span>
      </a>
      <ul class="nav-links">
        ${links}
        <li><a href="thesis.html#signup" class="btn-y">Request clearance</a></li>
      </ul>
    </nav>
  `;
})();
