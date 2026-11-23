#!/usr/bin/env python3
"""Assemble the public site into _site/ for the Pages deploy (task 54). Stdlib only.

GitHub Pages used to serve every tracked file, so the rating store, the registry and the
pipeline's other inputs were public along with the pages. The site now deploys from _site/
alone: the pages, their styles, scripts and images, and the data files the pages read.
Everything else stays in the repository.

What is published
  pages   every tracked *.html at the root, under research/, and under assets/ (the
          published asset profiles; check_public_assets.py keeps those to published.json)
  static  css/, js/, og/, assets/fonts/, assets/robot/ and the figures in assets/, and the
          root's icons, manifest and crawler files (ROOT_FILES)
  data    DATA; the series file of each index in data/index/index_summary.json, which
          the index charts read (its _meta.sources); and each published profile's
          data/assets/<slug>.json

The charts read only a series file's rows, so SERIES_ONLY files are published as
{"series": [...]} with each row's date or month, value and calibration flag. The rest of
such a file (constituent weights, the bottleneck ratings behind them, leg anchors) stays in
the repository. The funding page reads the private-capital file in full.

Only tracked files are copied: a gitignored file in the working tree never ships, and a
listed file that isn't tracked fails the build. scripts/check_site.py checks the result.

Usage:
    python scripts/build_site.py [--out _site]
"""
import argparse
import json
import shutil
import subprocess
import sys
from fnmatch import fnmatch
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PAGES = ["*.html", "research/*.html", "assets/*.html"]
STATIC_DIRS = ["css", "js", "og", "assets/fonts", "assets/robot"]
STATIC_GLOBS = ["assets/*.svg"]
ROOT_FILES = ["CNAME", "robots.txt", "sitemap.xml", "llms.txt", "BingSiteAuth.xml", "site.webmanifest",
              "favicon.ico", "favicon.svg", "apple-touch-icon.png", "icon-192.png", "icon-512.png",
              "robotlogo.png"]
# The data files the pages fetch, with the page or script that reads each.
DATA = [
    "data/index/index_summary.json",          # front door, index charts, research pages
    "data/index/rpci_scope.json",             # funding page
    "data/funding/rounds.json",               # funding page, global search
    "data/funding/summary.json",              # funding page
    "data/registries/search_index.json",      # global search, asset profiles
    "data/frontier_conditions.json",          # frontier-conditions widget
    "data/assets/published.json",             # asset profiles
]
SUMMARY = "data/index/index_summary.json"
SERIES_ONLY = {"data/index/robotnik_index.json", "data/index/bottleneck_weighted_composite.json",
               "data/index/composite_index.json", "data/index/commodities_index.json"}
ROW_KEYS = ("date", "month", "value", "calibration")


def tracked(root=ROOT):
    out = subprocess.run(["git", "-C", str(root), "ls-files", "-z"], capture_output=True,
                         check=True).stdout.decode("utf-8")
    return {p for p in out.split("\0") if p}


def series_files(root=ROOT):
    """The series file of each charted index: _meta.sources, for the indexes the summary
    holds. Its other sources (the sector sub-indices, the stack) describe inputs, and no
    page fetches them."""
    summary = json.loads((root / SUMMARY).read_text(encoding="utf-8"))
    sources = summary.get("_meta", {}).get("sources", {})
    return sorted({sources[k] for k in summary.get("indexes", {})
                   if isinstance(sources.get(k), str) and sources[k].endswith(".json")})


def series_only(path):
    """A series file as the charts read it: its rows' dates, values and calibration flags."""
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    return {"series": [{k: row[k] for k in ROW_KEYS if k in row} for row in doc.get("series", [])]}


def profile_files(root=ROOT):
    slugs = json.loads((root / "data/assets/published.json").read_text(encoding="utf-8"))
    return ["data/assets/{}.json".format(s) for s in slugs]


def site_files(root=ROOT):
    """Every repository path the site publishes. Raises if a listed file isn't tracked."""
    files = tracked(root)
    chosen = {p for p in files if any(fnmatch(p, g) and p.count("/") == g.count("/")
                                      for g in PAGES + STATIC_GLOBS)}
    chosen |= {p for p in files if any(p.startswith(d + "/") for d in STATIC_DIRS)}
    listed = ROOT_FILES + DATA + series_files(root) + profile_files(root)
    missing = sorted(p for p in listed if p not in files)
    if missing:
        raise SystemExit("build_site: listed but not tracked: " + ", ".join(missing))
    return sorted(chosen | set(listed))


def build(out, root=ROOT):
    if out.exists():
        shutil.rmtree(out)
    paths = site_files(root)
    for p in paths:
        dest = out / p
        dest.parent.mkdir(parents=True, exist_ok=True)
        if p in SERIES_ONLY:
            dest.write_text(json.dumps(series_only(root / p), separators=(",", ":")) + "\n", encoding="utf-8")
        else:
            shutil.copy2(root / p, dest)
    return paths


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=str(ROOT / "_site"))
    args = ap.parse_args()
    paths = build(Path(args.out))
    data = [p for p in paths if p.startswith("data/")]
    print("build_site: {} files, {} of them data: {}".format(len(paths), len(data), ", ".join(data)))


if __name__ == "__main__":
    sys.exit(main())
