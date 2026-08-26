#!/usr/bin/env python3
"""Build the Frontier Assets listing table into assets.html (static, server-rendered).

Phase one of the Frontier Assets listing. Follows the build_asset_profiles.py pattern:
reads the source-of-truth registry + the enrichment (control-point) store, emits STATIC
HTML rows present in the served page (NOT fetched/rendered client-side), and fails the
build if any banned vendor field reaches the output.

It regenerates ONLY the region between the BEGIN/END markers in assets.html, so the
hand-edited page copy (head, hero, intro) above the markers is never clobbered.

HARD CONSTRAINT (ToS + Robotnik served-data rule): no price, percentage change,
sparkline, market cap, P/E, weight, band or rank anywhere in the emitted HTML. The only
surfaces are Robotnik's own structured labels: name, ticker, sector, subsector,
value-chain tier and bottleneck rating.

Columns come from data/registries/entity_registry.json (name, ticker, sector, subsector,
value_chain) and data/markets/enrichment_data.json (bottleneck_risk). The build set is
the ACTIVE PUBLIC universe (status is null and type == "public"), so an entity with a
rating and a tier appears whether or not it carries an index weight.

Run: python scripts/build_assets_page.py
"""
import json
import re
import html
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REG_PATH = ROOT / "data" / "registries" / "entity_registry.json"
ENR_PATH = ROOT / "data" / "markets" / "enrichment_data.json"
PAGE_PATH = ROOT / "assets.html"
CONTENT_DIR = ROOT / "data" / "assets" / "content"

BEGIN = "<!-- BEGIN GENERATED: asset table — scripts/build_assets_page.py — do not hand-edit -->"
END = "<!-- END GENERATED: asset table -->"

# Same discipline as build_asset_profiles.py: any banned vendor field-token in the
# emitted HTML is fatal. These are compound field names / price-derived tokens that
# never occur in a company name, sector, tier or rating label, so the scan cannot
# false-positive on legitimate content but WILL fire if a price/weight/rank column
# is ever added by mistake.
BANNED_KEYS = (
    "weight_pct", "weight_band", "sector_rank", "market_cap", "market_cap_usd",
    "native_price", "change_pct", "sparkline", "pe_ratio", "p/e",
)

# Canonical bottom-up value-chain order for the tier filter (the 8 tiers present in the
# active-public set; the taxonomy's 9th, Launch Services, has no active-public member).
TIER_ORDER = [
    "Upstream Materials",
    "Capital Equipment",
    "Fabrication & Manufacturing",
    "Components & Subsystems",
    "IP & Design",
    "Software & Services",
    "System Integration",
    "Deployment & Operation",
]
SECTOR_ORDER = ["Materials", "Robotics", "Semiconductors", "Space"]
RATING_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
CRIT_RANK = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}  # unrated sorts last (4)

SECTOR_CLASS = {
    "Semiconductors": "semi", "Robotics": "robo", "Space": "space", "Materials": "materials",
}
RATING_CLASS = {"CRITICAL": "crit", "HIGH": "high", "MEDIUM": "med", "LOW": "low"}


def slugify(entity_id):
    """Mirror scripts/build_asset_profiles.py: pure-alphanumeric id verbatim, else
    lowercase, non-alphanumeric runs to '-', trim leading/trailing '-'."""
    if re.fullmatch(r"[A-Za-z0-9]+", entity_id):
        return entity_id
    return re.sub(r"^-+|-+$", "", re.sub(r"[^a-z0-9]+", "-", entity_id.lower()))


def esc(value):
    return html.escape("" if value is None else str(value), quote=True)


def load():
    reg = json.loads(REG_PATH.read_text())
    enr = json.loads(ENR_PATH.read_text())
    authored = {p.stem for p in CONTENT_DIR.glob("*.json")}
    return reg, enr, authored


def rating_for(entity_id, rec, enr):
    """Bottleneck rating via id, then public_ticker/entity_id (recovers names whose
    registry id is a slug but whose enrichment record is keyed by ticker, e.g.
    cerebras-systems -> CBRS)."""
    for key in (entity_id, rec.get("public_ticker"), rec.get("entity_id")):
        if key and isinstance(enr.get(key), dict) and enr[key].get("bottleneck_risk"):
            return enr[key]["bottleneck_risk"]
    return None


def build_rows(reg, enr, authored):
    rows = []
    for entity_id, rec in reg.items():
        if rec.get("status") is not None or rec.get("type") != "public":
            continue
        slug = slugify(entity_id)
        rating = rating_for(entity_id, rec, enr)
        rows.append({
            "name": rec.get("name") or entity_id,
            "ticker": rec.get("public_ticker") or entity_id,
            "sector": rec.get("sector") or "",
            "subsector": rec.get("subsector") or "",
            "tier": rec.get("value_chain") or "",
            "rating": rating,
            "crit": CRIT_RANK.get(rating, 4),
            "slug": slug,
            "authored": slug in authored,
        })
    # Default sort: bottleneck criticality, then sector, then name.
    rows.sort(key=lambda r: (r["crit"], r["sector"], r["name"].lower()))
    return rows


def filter_group(axis, legend, values):
    buttons = "\n".join(
        '        <button type="button" class="filter-btn" data-value="{v}">{label}</button>'.format(
            v=esc(v), label=esc(v)
        )
        for v in values
    )
    return (
        '      <div class="filter-group" data-axis="{axis}">\n'
        '        <span class="filter-legend">{legend}</span>\n'
        "{buttons}\n"
        "      </div>"
    ).format(axis=axis, legend=esc(legend), buttons=buttons)


def render_row(r):
    sector_cls = SECTOR_CLASS.get(r["sector"], "cross")
    if r["sector"]:
        sector_cell = '<span class="sector-tag sector-{cls}">{s}</span>'.format(
            cls=sector_cls, s=esc(r["sector"])
        )
    else:
        sector_cell = '<span class="asset-none">—</span>'
    subsector_cell = esc(r["subsector"]) if r["subsector"] else '<span class="asset-none">—</span>'
    tier_cell = esc(r["tier"]) if r["tier"] else '<span class="asset-none">—</span>'
    if r["rating"]:
        rating_cell = '<span class="rating-tag rating-{cls}">{lab}</span>'.format(
            cls=RATING_CLASS[r["rating"]], lab=esc(r["rating"])
        )
    else:
        rating_cell = '<span class="rating-tag rating-none">Unrated</span>'
    if r["authored"]:
        profile_cell = '<a class="asset-profile-link" href="/assets/{slug}.html">View →</a>'.format(
            slug=esc(r["slug"])
        )
    else:
        profile_cell = '<span class="asset-none">—</span>'
    return (
        '        <tr data-name="{dname}" data-ticker="{dticker}" data-sector="{sector}"'
        ' data-tier="{tier}" data-rating="{rating}" data-crit="{crit}">\n'
        "          <td class=\"asset-name\">{name}</td>\n"
        "          <td class=\"ticker\">{ticker}</td>\n"
        "          <td>{sector_cell}</td>\n"
        "          <td class=\"asset-sub\">{subsector_cell}</td>\n"
        "          <td class=\"asset-tier\">{tier_cell}</td>\n"
        "          <td>{rating_cell}</td>\n"
        "          <td class=\"asset-profile-cell\">{profile_cell}</td>\n"
        "        </tr>"
    ).format(
        dname=esc(r["name"].lower()),
        dticker=esc(str(r["ticker"]).lower()),
        sector=esc(r["sector"]),
        tier=esc(r["tier"]),
        rating=esc(r["rating"] or ""),
        crit=r["crit"],
        name=esc(r["name"]),
        ticker=esc(r["ticker"]),
        sector_cell=sector_cell,
        subsector_cell=subsector_cell,
        tier_cell=tier_cell,
        rating_cell=rating_cell,
        profile_cell=profile_cell,
    )


def render_region(rows):
    total = len(rows)
    filters = "\n".join([
        filter_group("sector", "Sector", [s for s in SECTOR_ORDER if any(r["sector"] == s for r in rows)]),
        filter_group("tier", "Value-chain tier", [t for t in TIER_ORDER if any(r["tier"] == t for r in rows)]),
        filter_group("rating", "Bottleneck", RATING_ORDER),
    ])
    body = "\n".join(render_row(r) for r in rows)
    return (
        '<div class="assets-toolbar" data-total="{total}">\n'
        '  <div class="assets-filters">\n'
        "{filters}\n"
        "  </div>\n"
        '  <div class="assets-controls">\n'
        '    <input type="search" id="assets-search" class="assets-search" placeholder="Search name or ticker" aria-label="Search assets by name or ticker">\n'
        '    <label class="assets-sort-label">Sort\n'
        '      <select id="assets-sort" class="assets-sort" aria-label="Sort assets">\n'
        '        <option value="criticality">Bottleneck criticality</option>\n'
        '        <option value="alpha">Alphabetical</option>\n'
        '        <option value="sector">Sector</option>\n'
        "      </select>\n"
        "    </label>\n"
        '    <button type="button" id="assets-clear" class="assets-clear" hidden>Clear</button>\n'
        "  </div>\n"
        '  <div class="assets-count" id="assets-count" aria-live="polite">{total} of {total} entities</div>\n'
        "</div>\n\n"
        '<div class="assets-table-wrap">\n'
        '  <table class="market-table assets-table" id="assets-table">\n'
        "    <thead>\n"
        "      <tr>\n"
        '        <th data-sort="name">Entity</th>\n'
        '        <th data-sort="ticker">Ticker</th>\n'
        '        <th data-sort="sector">Sector</th>\n'
        '        <th data-sort="subsector">Subsector</th>\n'
        '        <th data-sort="tier">Value-chain tier</th>\n'
        '        <th data-sort="rating">Bottleneck</th>\n'
        "        <th>Profile</th>\n"
        "      </tr>\n"
        "    </thead>\n"
        "    <tbody>\n"
        "{body}\n"
        "    </tbody>\n"
        "  </table>\n"
        "</div>"
    ).format(total=total, filters=filters, body=body)


def guard(region_html):
    lowered = region_html.lower()
    leaks = [tok for tok in BANNED_KEYS if tok in lowered]
    if leaks:
        sys.exit("FATAL: banned vendor field(s) in emitted assets table: {}. "
                 "No price-derived surface may be published.".format(", ".join(leaks)))


def splice(region_html):
    page = PAGE_PATH.read_text()
    if BEGIN not in page or END not in page:
        sys.exit("FATAL: markers not found in assets.html. Expected:\n  {}\n  {}\n"
                 "The hand-authored shell must contain both markers.".format(BEGIN, END))
    pattern = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END), re.DOTALL)
    replacement = BEGIN + "\n" + region_html + "\n" + END
    PAGE_PATH.write_text(pattern.sub(lambda _m: replacement, page, count=1))


def main():
    reg, enr, authored = load()
    rows = build_rows(reg, enr, authored)
    region = render_region(rows)
    guard(region)
    splice(region)
    rated = sum(1 for r in rows if r["rating"])
    linked = sum(1 for r in rows if r["authored"])
    print("assets.html table regenerated: {} rows".format(len(rows)))
    print("  rated: {}  unrated: {}  profile links: {}".format(rated, len(rows) - rated, linked))
    by_sector = {}
    for r in rows:
        by_sector[r["sector"]] = by_sector.get(r["sector"], 0) + 1
    print("  by sector: " + ", ".join("{}={}".format(k, v) for k, v in sorted(by_sector.items())))


if __name__ == "__main__":
    main()
