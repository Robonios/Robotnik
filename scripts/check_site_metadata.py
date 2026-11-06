#!/usr/bin/env python3
"""Guard llms.txt and the pages' structured data (task 4d). Exits 1 on any failure.

llms.txt tells language models what Robotnik publishes, so it may list only pages that
are public: each link must
  - resolve to a page in this repository;
  - be indexable (no robots noindex) and listed in sitemap.xml;
  - carry a canonical link equal to the listed URL;
  - carry schema.org structured data: at least one JSON-LD block, each one valid JSON
    with "@context": "https://schema.org" and a "@type", at the top or in its "@graph".

Every JSON-LD block on every page must also be valid JSON, listed or not, so a broken
block can't reach search engines unnoticed.

Run from the repository root: python scripts/check_site_metadata.py
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://robotnik.world"
LINK = re.compile(r"\[[^\]]+\]\((https://robotnik\.world[^)\s]*)\)")
LD = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
CANONICAL = re.compile(r'<link rel="canonical" href="([^"]+)"')
NOINDEX = re.compile(r'<meta name="robots" content="[^"]*noindex', re.I)
LOC = re.compile(r"<loc>([^<]+)</loc>")


def page_for(url):
    """https://robotnik.world/research/x -> research/x.html; / -> index.html."""
    path = url[len(SITE):].split("#")[0].split("?")[0].lstrip("/")
    if not path:
        return "index.html"
    return path if path.endswith(".html") else path + ".html"


def has_type(node):
    if isinstance(node, dict):
        if node.get("@type"):
            return True
        return any(has_type(n) for n in node.get("@graph") or [])
    return False


def ld_problems(rel, text):
    out, blocks = [], LD.findall(text)
    for i, b in enumerate(blocks, 1):
        try:
            doc = json.loads(b)
        except json.JSONDecodeError as e:
            out.append("{}: JSON-LD block {} is not valid JSON ({})".format(rel, i, e))
            continue
        if not isinstance(doc, dict) or doc.get("@context") != "https://schema.org":
            out.append("{}: JSON-LD block {} lacks \"@context\": \"https://schema.org\"".format(rel, i))
        elif not has_type(doc):
            out.append("{}: JSON-LD block {} has no @type".format(rel, i))
    return blocks, out


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def check():
    errors = []
    sitemap = set(LOC.findall(read("sitemap.xml")))
    listed = LINK.findall(read("llms.txt"))
    if not listed:
        errors.append("llms.txt lists no robotnik.world pages")
    for url in listed:
        rel = page_for(url)
        if not os.path.isfile(os.path.join(ROOT, rel)):
            errors.append("llms.txt: {} has no page ({} missing)".format(url, rel))
            continue
        text = read(rel)
        if NOINDEX.search(text):
            errors.append("llms.txt: {} is marked noindex".format(url))
        if url not in sitemap:
            errors.append("llms.txt: {} is not in sitemap.xml".format(url))
        canon = CANONICAL.search(text)
        if not canon or canon.group(1) != url:
            errors.append("llms.txt: {} has canonical {}".format(url, canon.group(1) if canon else "none"))
        blocks, problems = ld_problems(rel, text)
        if not blocks:
            errors.append("llms.txt: {} carries no schema.org structured data".format(url))
    for rel in sorted(glob.glob("*.html", root_dir=ROOT) + glob.glob("research/*.html", root_dir=ROOT)):
        errors += ld_problems(rel, read(rel))[1]
    return listed, errors


def main():
    listed, errors = check()
    for e in errors:
        print("::error::" + e if os.environ.get("GITHUB_ACTIONS") == "true" else "ERROR: " + e)
    if errors:
        sys.exit(1)
    print("llms.txt: {} pages, each public, in the sitemap and carrying schema.org markup; "
          "every JSON-LD block parses.".format(len(listed)))


if __name__ == "__main__":
    main()
