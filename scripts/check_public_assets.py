#!/usr/bin/env python3
"""
Public-asset guard: only published profiles may be reachable
============================================================
GitHub Pages serves the entire tracked tree, so any profile data file or page in
the repository is public, linked or not. data/assets/published.json is the single
source of truth for which profiles are published (the slugs with an authored
sidecar in data/assets/content/). This check fails when any public surface goes
beyond that list:

  1. data/assets/{slug}.json   every shard must be a published slug
  2. assets/{slug}.html        every profile page must be a published slug
  3. sitemap.xml               every /assets/ URL must be a published slug
  4. data/assets/content/      sidecars and published.json must agree

It also fails when a published slug is missing its shard or its page, because
that profile would be listed but broken.

Run locally:  python3 scripts/check_public_assets.py
Exit codes:   0 clean, 1 violations found.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHARD_DIR = ROOT / "data" / "assets"
CONTENT_DIR = SHARD_DIR / "content"
PUBLISHED_PATH = SHARD_DIR / "published.json"
PAGE_DIR = ROOT / "assets"
SITEMAP_PATH = ROOT / "sitemap.xml"


def main():
    problems = []
    published = set(json.loads(PUBLISHED_PATH.read_text()))

    sidecars = {p.stem for p in CONTENT_DIR.glob("*.json")}
    if sidecars != published:
        problems.append("published.json and content/ sidecars disagree: "
                        "only in published.json {}, only in content/ {}".format(
                            sorted(published - sidecars), sorted(sidecars - published)))

    shards = {p.stem for p in SHARD_DIR.glob("*.json") if p.name != PUBLISHED_PATH.name}
    for slug in sorted(shards - published):
        problems.append("unpublished shard is public: data/assets/{}.json".format(slug))
    for slug in sorted(published - shards):
        problems.append("published profile has no shard: data/assets/{}.json".format(slug))

    pages = {p.stem for p in PAGE_DIR.glob("*.html")}
    for slug in sorted(pages - published):
        problems.append("unpublished profile page is public: assets/{}.html".format(slug))
    for slug in sorted(published - pages):
        problems.append("published profile has no page: assets/{}.html".format(slug))

    if SITEMAP_PATH.exists():
        urls = re.findall(r"/assets/([^/<\s]+)\.html", SITEMAP_PATH.read_text())
        for slug in sorted(set(urls) - published):
            problems.append("sitemap lists an unpublished profile: assets/{}.html".format(slug))

    if problems:
        print("Public-asset guard FAILED ({} problem(s)):".format(len(problems)))
        for p in problems:
            print("  - " + p)
        print("\nOnly the slugs in data/assets/published.json may be public. To publish a "
              "profile, add its sidecar to data/assets/content/ and run "
              "scripts/build_asset_profiles.py.")
        sys.exit(1)

    print("Public-asset guard passed: {} published profile(s); shards, pages and "
          "sitemap all match.".format(len(published)))


if __name__ == "__main__":
    main()
