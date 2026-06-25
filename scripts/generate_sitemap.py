#!/usr/bin/env python3
"""Regenerate sitemap.xml from the nav-linked page list.

lastmod is taken from the most recent git commit that touched each file.
Designed to run in CI on every push to main (see .github/workflows/
fetch-data.yml) so the sitemap stays in sync without manual steps.
"""

import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITEMAP_PATH = ROOT / "sitemap.xml"
BASE_URL = "https://robotnik.world"

# Canonical public pages (must match js/nav.js + what we actually want indexed).
# Orphan pages (intelligence.html, tetris.html) are intentionally excluded —
# they're not in the nav and shouldn't be advertised.
# Retired surfaces (report-1Q26.html, thesis.html, the 1Q26 PDF) are hard-excluded
# via the RETIRED set below — never emitted, even if an entry lingers in PAGES.
PAGES = [
    # (path,                                                   priority, changefreq)
    ("",                                                        "1.0",    "daily"),    # homepage (index.html)
    ("about",                                                   "0.6",    "monthly", "about.html"),  # /about (extensionless), lastmod from about.html
    ("news.html",                                               "0.8",    "daily"),
    ("research.html",                                           "0.8",    "monthly"),
    # Reference library articles: extensionless canonical URL served by GitHub
    # Pages; lastmod is read from the .html file via the optional 4th element.
    ("research/frontier-stack-thesis",                          "0.9",    "monthly", "research/frontier-stack-thesis.html"),
    ("research/universe-membership",                            "0.8",    "monthly", "research/universe-membership.html"),
    ("assets.html",                                             "0.8",    "weekly"),
    ("funding.html",                                            "0.8",    "weekly"),
    ("portfolio.html",                                          "0.5",    "yearly"),
    ("signals.html",                                            "0.5",    "yearly"),
    ("commodities.html",                                        "0.5",    "yearly"),
    ("recreation.html",                                         "0.3",    "yearly"),
]


def last_commit_date(relpath: str) -> str:
    """Return the ISO-date of the most recent commit that touched relpath.

    Falls back to today's date if git is unavailable or the file is new.
    """
    src = relpath or "index.html"
    try:
        out = subprocess.check_output(
            ["git", "log", "-1", "--format=%cI", "--", src],
            cwd=ROOT,
            stderr=subprocess.DEVNULL,
        )
        iso = out.decode().strip()
        if iso:
            # Keep the date portion only for sitemap format conformance.
            return iso[:10]
    except Exception:
        pass
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# Retired surfaces — the HTML pages are served as noindex redirect stubs, the PDF
# is simply withdrawn; never advertise any of them in the sitemap. Durable:
# skipped even if an entry is still present in / re-added to PAGES above.
RETIRED = {
    "report-1Q26.html",
    "thesis.html",
    "reports/1Q26-State-of-the-Frontier-Stack.pdf",
}


def build_sitemap() -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for entry in PAGES:
        path, priority, changefreq = entry[0], entry[1], entry[2]
        if path in RETIRED:
            continue
        # Optional 4th element: source file to read lastmod from, used when the
        # public URL is extensionless and so does not match a file on disk.
        src = entry[3] if len(entry) > 3 else path
        url = f"{BASE_URL}/{path}".rstrip("/") if path == "" else f"{BASE_URL}/{path}"
        # Canonical homepage = trailing-slash form
        if path == "":
            url = f"{BASE_URL}/"
        lines.append("  <url>")
        lines.append(f"    <loc>{url}</loc>")
        lines.append(f"    <lastmod>{last_commit_date(src)}</lastmod>")
        lines.append(f"    <changefreq>{changefreq}</changefreq>")
        lines.append(f"    <priority>{priority}</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    xml = build_sitemap()
    SITEMAP_PATH.write_text(xml)
    n = xml.count("<url>")
    print(f"Wrote {SITEMAP_PATH.relative_to(ROOT)} ({n} URLs)")


if __name__ == "__main__":
    main()
