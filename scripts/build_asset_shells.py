#!/usr/bin/env python3
"""Build the per-asset profile HTML shells from the published manifest.

A shell (assets/{slug}.html) is a thin, hand-free loader for js/asset-profile.js,
which derives the slug from the path and fetches /data/assets/{slug}.json. This
script is the SINGLE creator and remover of shells: it writes one shell for every
slug in data/assets/published.json and deletes any assets/*.html profile shell
whose slug is not in the manifest. So the set of reachable profiles always equals
the published set — the drift that left 17 shells for 7 published profiles cannot
recur.

Why this exists: nothing used to create or remove shells; they were hand-made, so
unpublished profiles could be reached by direct URL. The manifest
(data/assets/published.json, written by build_asset_profiles.py from the authored
sidecars) is the source of truth; this builder is one of its four readers.

Title / description copy
------------------------
Every shell is byte-identical except the browser title, the meta-description
subject and the slug in the URLs/comment. Most profiles use the registry display
name (the shard's identity.name) verbatim. A few complete profiles carried a
hand-polished SEO name and parenthetical qualifier in their original shell that
exists in NO data source (e.g. "TSMC (Taiwan Semiconductor)"); those are
preserved in SEO_OVERRIDES so regeneration stays byte-identical (no drift). To
publish a new profile with a polished name, add an entry here; otherwise the
registry name is used automatically.

Indexing: a published shell is indexable (no robots meta); the builder emits
<meta name="robots" content="noindex"> only for an unpublished slug. Because it
writes shells solely for published slugs, no shell it writes is noindexed.

Cache-bust: AP_VER is the asset-profile.js version query. Bump it (and re-run
this builder) whenever js/asset-profile.js changes, so returning visitors fetch
the new script.

Reads:   data/assets/published.json, data/assets/{slug}.json (for identity.name)
Writes:  assets/{slug}.html for each published slug
Removes: assets/{slug}.html for any profile shell not in the manifest
Run:     python scripts/build_asset_shells.py            (write + prune)
         python scripts/build_asset_shells.py --check    (report only, no writes)
This script does NOT git-commit or git-add.
"""
import argparse
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLISHED_PATH = ROOT / "data" / "assets" / "published.json"
SHARD_DIR = ROOT / "data" / "assets"
SHELL_DIR = ROOT / "assets"

# asset-profile.js cache-bust version baked into every shell. Keep in step with
# the committed shells; bump when js/asset-profile.js changes.
AP_VER = "20261007a"

# slug -> (title_name, description_qualifier). Hand-curated SEO copy preserved
# from the original hand-made shells; present in no data source. Everything not
# listed uses the shard identity.name verbatim and no parenthetical qualifier.
SEO_OVERRIDES = {
    "TSM":  ("TSMC", "Taiwan Semiconductor"),
    "AVGO": ("Broadcom", "AVGO"),
    "MRVL": ("Marvell Technology", "MRVL"),
    "MU":   ("Micron Technology", "MU"),
}

# A profile shell is identifiable by this marker; the pruner only ever removes a
# file that carries it, so a non-profile .html in assets/ could never be deleted.
SHELL_MARKER = 'id="asset-profile"'

TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<base href="/">
<title>__TITLE__</title>
__ROBOTS__<meta name="description" content="__DESC__">
<!-- Open Graph -->
<meta property="og:type" content="website">
<meta property="og:url" content="https://robotnik.world/assets/__SLUG__.html">
<meta property="og:title" content="__TITLE__">
<meta property="og:description" content="__DESC__">
<meta property="og:image" content="https://robotnik.world/og/default.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:site_name" content="Robotnik">
<!-- Twitter / X Card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="__TITLE__">
<meta name="twitter:description" content="__DESC__">
<meta name="twitter:image" content="https://robotnik.world/og/default.png">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<meta name="theme-color" content="#F5D921">
<link rel="canonical" href="https://robotnik.world/assets/__SLUG__.html">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Mulish:wght@300;400;500;600;700&family=Roboto+Mono:wght@300;400;500;700&family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/css/style.css?v=20260514m4"><link rel="stylesheet" href="/css/typography.css?v=20260421e">
<!-- GoatCounter analytics (privacy-friendly, no cookies) -->
<script data-goatcounter="https://robotnik.goatcounter.com/count"
        async src="//gc.zgo.at/count.js"></script>
</head>
<body data-page="assets">

<div class="bg-layer"></div>
<div id="nav-container"></div>

<div class="main-content">
  <!-- Nine-layer profile rendered client-side by js/asset-profile.js from
       /data/assets/__SLUG__.json. noindex while the surface is dark. -->
  <div id="asset-profile"></div>
</div>

<!-- Persistent footer injected by js/nav.js. -->
<script src="/js/nav.js?v=20260822a"></script>
<script src="/js/asset-profile.js?v=__AP_VER__"></script>
</body>
</html>
'''


def shard_name(slug):
    shard = json.loads((SHARD_DIR / "{}.json".format(slug)).read_text())
    return (shard.get("identity") or {}).get("name") or slug


def render_shell(slug, published=True):
    """Return the exact HTML for a profile shell. SEO_OVERRIDES reproduces the
    hand-polished titles, everything else uses the registry name. A published
    profile is indexable (no robots meta); an unpublished one carries
    <meta name="robots" content="noindex">. The builder only ever writes published
    shells, so no shell it writes is noindexed; the conditional keeps the template
    correct if it is ever asked to render an unpublished shell."""
    if slug in SEO_OVERRIDES:
        disp, qual = SEO_OVERRIDES[slug]
        title_name, subject = disp, "{} ({})".format(disp, qual)
    else:
        title_name = shard_name(slug)
        subject = title_name
    title = html.escape("{} — Robotnik".format(title_name))
    desc = html.escape(
        "Robotnik intelligence profile for {}: identity, classification, "
        "bottleneck exposure, dependencies and market context. "
        "Research preview.".format(subject)
    )
    robots = "" if published else '<meta name="robots" content="noindex">\n'
    return (TEMPLATE.replace("__TITLE__", title)
                    .replace("__DESC__", desc)
                    .replace("__AP_VER__", AP_VER)
                    .replace("__ROBOTS__", robots)
                    .replace("__SLUG__", slug))


def load_published():
    data = json.loads(PUBLISHED_PATH.read_text())
    if isinstance(data, dict):
        data = data.get("published", [])
    return sorted(data)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="report what would be written/removed without touching files")
    args = ap.parse_args()

    published = load_published()
    pubset = set(published)
    SHELL_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Write a shell for every published slug.
    for slug in published:
        shell = SHELL_DIR / "{}.html".format(slug)
        content = render_shell(slug, published=True)
        if args.check:
            cur = shell.read_text() if shell.exists() else None
            print("  WRITE {:28s} {}".format(
                slug, "(identical)" if cur == content else "(CHANGED)" if cur else "(new)"))
        else:
            shell.write_text(content)

    # 2. Remove any profile shell whose slug is not published (identified by the
    #    asset-profile marker, so a non-profile .html is never touched).
    removed = []
    for p in sorted(SHELL_DIR.glob("*.html")):
        if p.stem in pubset:
            continue
        if SHELL_MARKER not in p.read_text():
            continue
        removed.append(p.name)
        if not args.check:
            p.unlink()

    print("shells {}: {} published -> {}".format(
        "to write" if args.check else "written", len(published), published))
    print("orphan shells {}: {} -> {}".format(
        "to remove" if args.check else "removed", len(removed), removed))


if __name__ == "__main__":
    main()
