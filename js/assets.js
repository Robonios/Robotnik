/* Frontier Assets listing — progressive enhancement.
 *
 * Operates ENTIRELY on the rows already present in the server-rendered table; it
 * fetches nothing. With JavaScript disabled the full table is still listed (in the
 * default criticality order the generator emitted); this script only adds filtering,
 * sorting and search on top of it.
 *
 * Filters combine: within an axis the selected values are OR'd, across the three axes
 * (sector, value-chain tier, bottleneck rating) they are AND'd, so the cross-cut
 * queries the page is built for (e.g. CRITICAL names within Materials) work.
 *
 * Honours ?q= on load: the global site search routes to assets.html?q=<name-or-ticker>.
 */
(function () {
  "use strict";

  var table = document.getElementById("assets-table");
  if (!table) return;
  var tbody = table.tBodies[0];
  if (!tbody) return;

  var rows = Array.prototype.slice.call(tbody.rows);
  var toolbar = document.querySelector(".assets-toolbar");
  var total = rows.length;
  var searchInput = document.getElementById("assets-search");
  var sortSelect = document.getElementById("assets-sort");
  var clearBtn = document.getElementById("assets-clear");
  var countEl = document.getElementById("assets-count");
  var filterBtns = Array.prototype.slice.call(document.querySelectorAll(".filter-btn"));

  var active = { sector: new Set(), tier: new Set(), rating: new Set() };
  var query = "";

  // Empty-state row, shown only when a query returns nothing.
  var emptyRow = document.createElement("tr");
  emptyRow.className = "assets-empty";
  emptyRow.hidden = true;
  var emptyCell = document.createElement("td");
  emptyCell.colSpan = table.tHead ? table.tHead.rows[0].cells.length : 7;
  emptyCell.textContent = "No entities match these filters.";
  emptyRow.appendChild(emptyCell);
  tbody.appendChild(emptyRow);

  function matches(row) {
    if (row === emptyRow) return false;
    var d = row.dataset;
    if (active.sector.size && !active.sector.has(d.sector)) return false;
    if (active.tier.size && !active.tier.has(d.tier)) return false;
    if (active.rating.size && !active.rating.has(d.rating)) return false;
    if (query && d.name.indexOf(query) === -1 && d.ticker.indexOf(query) === -1) return false;
    return true;
  }

  function apply() {
    var shown = 0;
    for (var i = 0; i < rows.length; i++) {
      var vis = matches(rows[i]);
      rows[i].hidden = !vis;
      if (vis) shown++;
    }
    emptyRow.hidden = shown !== 0;
    if (countEl) countEl.textContent = shown + " of " + total + " entities";
    var anyFilter = active.sector.size || active.tier.size || active.rating.size || query;
    if (clearBtn) clearBtn.hidden = !anyFilter;
  }

  var CRIT = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3, "": 4 };
  function cmp(a, b, keys) {
    for (var i = 0; i < keys.length; i++) {
      var k = keys[i], av, bv;
      if (k === "crit") { av = CRIT[a.dataset.rating] || 4; bv = CRIT[b.dataset.rating] || 4; }
      else { av = a.dataset[k]; bv = b.dataset[k]; }
      if (av < bv) return -1;
      if (av > bv) return 1;
    }
    return 0;
  }

  function sortRows(mode) {
    var keys = mode === "alpha" ? ["name"]
             : mode === "sector" ? ["sector", "crit", "name"]
             : ["crit", "sector", "name"];
    var ordered = rows.slice().sort(function (a, b) { return cmp(a, b, keys); });
    for (var i = 0; i < ordered.length; i++) tbody.insertBefore(ordered[i], emptyRow);
    rows = ordered;
  }

  filterBtns.forEach(function (btn) {
    btn.addEventListener("click", function () {
      var group = btn.closest(".filter-group");
      if (!group) return;
      var axis = group.dataset.axis;
      var value = btn.dataset.value;
      if (active[axis].has(value)) { active[axis].delete(value); btn.classList.remove("active"); }
      else { active[axis].add(value); btn.classList.add("active"); }
      apply();
    });
  });

  if (searchInput) {
    searchInput.addEventListener("input", function () {
      query = searchInput.value.trim().toLowerCase();
      apply();
    });
  }

  if (sortSelect) {
    sortSelect.addEventListener("change", function () { sortRows(sortSelect.value); });
  }

  if (clearBtn) {
    clearBtn.addEventListener("click", function () {
      active.sector.clear(); active.tier.clear(); active.rating.clear();
      query = "";
      filterBtns.forEach(function (b) { b.classList.remove("active"); });
      if (searchInput) searchInput.value = "";
      apply();
    });
  }

  // ?q= on load — the global search routes here with a name or ticker.
  try {
    var q = new URLSearchParams(window.location.search).get("q");
    if (q && searchInput) {
      searchInput.value = q;
      query = q.trim().toLowerCase();
    }
  } catch (e) { /* URLSearchParams unavailable — table still fully listed */ }

  apply();
})();
