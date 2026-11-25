#!/usr/bin/env python3
"""Check the assembled site in _site/ before it is deployed (task 54). Exits 1 on any failure.

  references  every local link in the site resolves to a file in it: href, src and srcset
              in the pages (against the page's <base href> when it has one), the og:image
              and other absolute robotnik.world URLs in meta tags, url() in the styles
              (against the stylesheet), each string-literal fetch() in the scripts, and
              each robotnik.world URL in sitemap.xml, robots.txt and llms.txt.
              A script's relative fetch resolves against the site root: every page that
              loads a script is at the root or sets <base href="/">, which is checked too.
              A path without an extension resolves as GitHub Pages serves it: as
              <path>.html or <path>/index.html.
  withheld    no file the site must not serve: the rating store, the registry, the
              weights, prices, the pipeline's other inputs, scripts, docs or notes.
  vendor      no JSON file carries a raw vendor field (check_published_vendor_fields.py's
              detection, with no allowance).

Fetches built from variables (the robot's robot.json, a profile's shard, an index's series
file) can't be read from the script text; build_site.py lists those files and fails if one
is missing. Stdlib only.

Usage:
    python scripts/check_site.py [--site _site]
"""
import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import check_published_vendor_fields as vendor  # noqa: E402

HOST = "robotnik.world"
WITHHELD = [
    re.compile(r"^data/(markets|prices|intel|private|quarantine|mappings|news|filings|reports)/"),
    re.compile(r"^data/registries/(?!search_index\.json$)"),
    re.compile(r"^data/index/(weights|market_caps|base_date|quarantine|sub_indices|summary|index_metrics)"),
    re.compile(r"^data/(news|research|filings|reports|home)\.json$"),
    re.compile(r"^data/assets/content/"),
    re.compile(r"^(scripts|docs|prompts|archive|\.github|\.githooks)/"),
    re.compile(r"\.(py|md|log|csv|pyc)$"),
    re.compile(r"^(CLAUDE\.md|requirements\.txt|repomix\.config\.json|\.gitignore|\.gitattributes)$"),
]
FETCH = re.compile(r"""fetch\(\s*(['"])([^'"]+)\1""")
SITE_URL = re.compile(r"https?://(?:www\.)?robotnik\.world/[^\s<>\")\]]*")
CRAWLER_FILES = ("sitemap.xml", "robots.txt", "llms.txt")
CSS_URL = re.compile(r"""url\(\s*['"]?([^'")]+)['"]?\s*\)""")
SKIP = re.compile(r"^(#|mailto:|tel:|javascript:|data:|blob:|about:)", re.I)


class Refs(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.refs, self.base, self.scripts = [], None, []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "base" and a.get("href"):
            self.base = a["href"]
            return
        if tag == "script" and a.get("src"):
            self.scripts.append(a["src"])
        for k in ("href", "src"):
            if a.get(k):
                self.refs.append(a[k])
        if a.get("srcset"):
            self.refs += [part.strip().split(" ")[0] for part in a["srcset"].split(",") if part.strip()]
        if tag == "meta" and (a.get("content") or "").startswith(("https://" + HOST + "/", "http://" + HOST + "/")):
            self.refs.append(a["content"])


def local_path(ref, page, site):
    """The site path a reference points to, or None when it leaves the site or is only the
    start of a path a script builds (it ends in a slash)."""
    ref = ref.strip()
    if not ref or SKIP.match(ref) or "${" in ref or "{{" in ref:
        return None
    u = urlsplit(ref)
    if u.scheme in ("http", "https") or ref.startswith("//"):
        if u.netloc.lower() not in (HOST, "www." + HOST):
            return None
        path = u.path
    elif u.scheme:
        return None
    else:
        path = u.path
    if not path:
        return None
    path = unquote(path)
    base = Path("/") if path.startswith("/") else Path("/" + page).parent
    parts = []
    for seg in (base / path.lstrip("/")).as_posix().split("/"):
        if seg in ("", "."):
            continue
        if seg == "..":
            if parts:
                parts.pop()
        else:
            parts.append(seg)
    return "/".join(parts)


def resolves(path, files):
    if path == "":
        return "index.html" in files
    return any(c in files for c in (path, path + ".html", path.rstrip("/") + "/index.html"))


def check(site):
    files = {p.relative_to(site).as_posix() for p in site.rglob("*") if p.is_file()}
    errors = []
    for f in sorted(files):
        if any(rx.search(f) for rx in WITHHELD):
            errors.append("withheld file in the site: " + f)
    for f in sorted(files):
        text = None
        where = f
        if f.endswith(".html"):
            text = (site / f).read_text(encoding="utf-8", errors="replace")
            parser = Refs()
            parser.feed(text)
            refs = parser.refs + [m.group(2) for m in FETCH.finditer(text)]
            if parser.base:
                where = (local_path(parser.base, f, site) or "").rstrip("/") + "/index.html"
            local_scripts = [r for r in parser.scripts if local_path(r, f, site) is not None]
            if "/" in f and local_scripts and parser.base != "/":
                errors.append("{}: loads scripts below the site root without <base href=\"/\">".format(f))
        elif f.endswith(".css"):
            refs = CSS_URL.findall((site / f).read_text(encoding="utf-8", errors="replace"))
        elif f.endswith(".js"):
            refs = [m.group(2) for m in FETCH.finditer((site / f).read_text(encoding="utf-8", errors="replace"))]
            where = "index.html"
        elif f in CRAWLER_FILES:
            refs = SITE_URL.findall((site / f).read_text(encoding="utf-8", errors="replace"))
        else:
            continue
        for ref in refs:
            if ref.split("?")[0].endswith("/") and f.endswith(".js"):
                continue
            path = local_path(ref, where, site)
            if path is not None and not resolves(path, files):
                errors.append("{}: {} does not resolve in the site".format(f, ref))
    for f in sorted(p for p in files if p.endswith((".json", ".webmanifest"))):
        try:
            doc = json.loads((site / f).read_text(encoding="utf-8"))
        except ValueError as e:
            errors.append("{}: not valid JSON ({})".format(f, str(e)[:60]))
            continue
        found = {}
        if vendor.PRICE_PATH.search(f) and vendor._dated_rows(doc):
            vendor._note(found, vendor.SERIES_LABEL, "<top level>")
        vendor._scan(doc, "", found)
        errors += ["{}: raw vendor field {} x{} (first at {})".format(f, k, n, first)
                   for k, (n, first) in sorted(found.items())]
    return files, errors


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--site", default=str(ROOT / "_site"))
    args = ap.parse_args()
    site = Path(args.site)
    if not site.is_dir():
        raise SystemExit("check_site: {} not found; run scripts/build_site.py first".format(site))
    files, errors = check(site)
    if errors:
        for e in errors:
            print("::error::" + e if __import__("os").environ.get("GITHUB_ACTIONS") == "true" else "ERROR " + e)
        raise SystemExit("check_site: {} problem(s); nothing may be deployed".format(len(errors)))
    print("check_site: {} files; every reference resolves, nothing withheld is published, "
          "no raw vendor field".format(len(files)))


if __name__ == "__main__":
    main()
