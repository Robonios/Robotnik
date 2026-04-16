# SEO Setup — Manual Steps

All the technical SEO foundations are already in place in the repo
(`sitemap.xml`, `robots.txt`, Open Graph tags, favicon suite, structured
data). Three things still require you to sign in and click buttons.
Allow about 15 minutes total.

---

## 1. Google Search Console  (~5 min)

Gets Robotnik indexed by Google and lets you submit the sitemap.

1. Go to <https://search.google.com/search-console>.
2. Click **Add property**, choose **Domain** (the left option, not "URL prefix"), and enter `robotnik.world`.
3. Google will show a **TXT record** that looks like `google-site-verification=XXXXXXXXXXXX`. Copy it.
4. In Cloudflare:
   - Dashboard → **robotnik.world** → **DNS** → **Records** → **Add record**.
   - Type: **TXT**
   - Name: `@`  (means the apex — `robotnik.world` itself)
   - Content: paste the `google-site-verification=...` string
   - Proxy status: **DNS only** (gray cloud — TXT records don't proxy)
   - Save.
5. Wait ~5 minutes for DNS to propagate, then back in Search Console click **Verify**. Expect a green check and the property dashboard loads.
6. In the left nav of Search Console: **Sitemaps** → **Add a new sitemap** → type `sitemap.xml` → **Submit**. Expect status **Success** within a few minutes. Robotnik lists nine URLs so that's what should appear.
7. In the left nav: **URL Inspection** → paste `https://robotnik.world/` → click **Request indexing**. Repeat for `/news.html`, `/research.html`, `/assets.html`, `/funding.html`. Optional but it nudges Google to crawl sooner than it would on its own.

Google typically takes 24–72 hours to start showing the site in search for non-branded queries.

---

## 2. Bing Webmaster Tools  (~3 min)

Gets Robotnik into Bing (and therefore ChatGPT Search, which uses Bing as a data source — relevant for AI visibility).

Easiest path: **import from Google Search Console** once GSC is verified.

1. Go to <https://www.bing.com/webmasters>.
2. Sign in with a Google account (or Microsoft account).
3. When prompted for sites, click **Import from Google Search Console**. Pick `robotnik.world`. Bing copies the property across and inherits verification — no second TXT record needed.
4. Once it appears in your property list, open it and go to **Sitemaps** → **Submit sitemap** → enter `https://robotnik.world/sitemap.xml` → Submit.

Alternative (if the GSC import path doesn't work): Bing will give you its own TXT string starting `bing-verify=...`. Same Cloudflare flow as step 1.4 above. Both TXT records can coexist on `@` — just add a second one.

---

## 3. Optional: AI-specific search

These are still beta-era and may or may not exist by the time you read this, but worth a check:

- **ChatGPT Search:** no console to submit to. It crawls via Bing and via OpenAI's own bot (GPTBot). `robots.txt` permits GPTBot, so no action needed.
- **Perplexity:** crawled by PerplexityBot. Also permitted by `robots.txt`.
- **Claude / Anthropic:** crawled by ClaudeBot. Permitted.
- **Google AI Overviews (SGE):** uses Google's main index. If GSC verification and sitemap submission are done, you're covered.

If you later want to **block** any of these, add lines to `robots.txt` like:

```
User-agent: GPTBot
Disallow: /

User-agent: ClaudeBot
Disallow: /
```

For Robotnik's current positioning (publicly-distributed intelligence that benefits from showing up in AI answers), leaving these open is the right call.

---

## 4. Verify the live site

After committing and pushing, confirm each of these loads correctly (cache-bust with `?v=N` if you've just pushed):

- <https://robotnik.world/sitemap.xml> — should render clean XML, nine URLs
- <https://robotnik.world/robots.txt> — should show the `Allow: /` + Sitemap line
- <https://robotnik.world/favicon.ico> — small yellow-Robotnik icon
- <https://robotnik.world/apple-touch-icon.png> — 180×180 version
- <https://robotnik.world/site.webmanifest> — JSON manifest

Preview cards — paste the homepage URL into each and check the card renders:

- LinkedIn: <https://www.linkedin.com/post-inspector/>
- X: <https://cards-dev.twitter.com/validator> (redirects to a tweet composer these days; just tweet the URL into a draft and confirm the card looks right — don't post)
- OpenGraph.xyz: <https://www.opengraph.xyz/> — paste `https://robotnik.world/` and check Facebook + LinkedIn + X previews at once
- Slack: paste the URL into any Slack channel with link preview enabled

If an OG image doesn't appear, the usual cause is caching on the platform side. LinkedIn's Post Inspector has a **Clear cache** button — use that once after any OG image change.

---

## 5. Open Graph image — follow-up

The current OG images in `/og/` (`default.png`, `home.png`, `research.png`, `frontier-assets.png`) are composed from `cosmonaut-bg.png` plus a wordmark overlay. They're functional but if you want higher-production versions:

- The design spec is **1200×630 PNG**. LinkedIn and X use the same dimensions.
- Per-page variants for News, Funding, Portfolio, Signals, Commodities, Recreation Bay would be nice-to-have — currently those all point to `/og/default.png`.
- Drop replacement PNGs in `/og/` with the same filenames and commit — no HTML edits needed.

---

## 6. Where the automation lives

- `robots.txt` and `sitemap.xml` sit at the repo root, served directly by GitHub Pages.
- `sitemap.xml` is regenerated automatically by `.github/workflows/sitemap.yml` on every push to `main` that touches an HTML file. `<lastmod>` is derived from git commit dates — no manual maintenance.
- `scripts/generate_sitemap.py` is the one-file generator. If you add a new page, edit the `PAGES` list at the top and push.
- Favicons and OG images live in the repo root and `/og/` respectively — they're static assets, no build step.
