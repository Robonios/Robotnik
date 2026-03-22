"""
Robotnik Industry Reports Scraper
====================================
Scrapes press releases from IFR, SEMI, SIA, Satellite Industry Association,
Space Foundation, and BryceTech. Outputs reports.json.

Setup:
  pip install beautifulsoup4 lxml

Usage:
  python fetch_reports.py

Output:
  reports.json — industry press releases with summaries
  archive_reports.json — full historical archive
"""

import json
import hashlib
import re
import time
import urllib.request
from datetime import datetime
from config import REPORTS_JSON, REPORTS_ARCHIVE_JSON
from archive_utils import archive_and_filter

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    print("WARNING: beautifulsoup4 not installed. Run: pip install beautifulsoup4 lxml")

# Browser-like User-Agent for sites that block simple agents
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 "
    "Robotniks/1.0 (robotniks.com)"
)

# Non-article titles to filter out from IFR
IFR_BLOCKLIST = {
    "press releases", "press contact", "press photos",
    "press newsletter", "press release",
}


def fetch_html(url):
    """Fetch HTML content from a URL."""
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="replace")


def make_id(url):
    return hashlib.sha256(url.encode()).hexdigest()[:12]


def clean_text(text, max_len=250):
    text = re.sub(r"<[^>]+>", "", text or "")
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > max_len:
        text = text[:max_len].rsplit(" ", 1)[0] + "..."
    return text


def fetch_article_summary(url):
    """Follow an article link and extract the first substantial paragraph."""
    try:
        html = fetch_html(url)
        soup = BeautifulSoup(html, "lxml")
        # Try common content containers
        for sel in ["article", ".content", ".post-content", "main", ".entry-content"]:
            content = soup.select_one(sel)
            if content:
                for p in content.find_all("p"):
                    text = clean_text(p.get_text())
                    if len(text) > 40:
                        return text
        # Fallback: try any <p> in body
        for p in soup.find_all("p"):
            text = clean_text(p.get_text())
            if len(text) > 40:
                return text
    except Exception:
        pass
    return ""


# ── IFR (International Federation of Robotics) ──────────────────────────────

def fetch_ifr():
    """Scrape IFR press releases with article summaries."""
    url = "https://ifr.org/ifr-press-releases"
    print(f"  [IFR] Fetching {url}")
    try:
        html = fetch_html(url)
        soup = BeautifulSoup(html, "lxml")
        items = []

        for el in soup.select("a[href*='/ifr-press-releases/']"):
            link = el.get("href", "")
            if not link:
                continue
            if not link.startswith("http"):
                link = "https://ifr.org" + link

            title = el.get_text(strip=True)
            if not title or len(title) < 10:
                continue

            # Filter out non-article entries
            if title.lower().strip() in IFR_BLOCKLIST:
                continue

            items.append({
                "id": make_id(link),
                "title": title,
                "url": link,
                "source": "IFR",
                "date": "",
                "summary": "",
                "category": "robo",
            })

        # Deduplicate by URL
        seen = set()
        unique = []
        for item in items:
            if item["url"] not in seen:
                seen.add(item["url"])
                unique.append(item)

        # Fetch summaries for first 10 articles
        for item in unique[:10]:
            summary = fetch_article_summary(item["url"])
            if summary:
                item["summary"] = summary
            time.sleep(0.5)  # be polite

        print(f"  [IFR] {len(unique)} press releases")
        return unique[:20]
    except Exception as e:
        print(f"  [IFR] FAILED: {e}")
        return []


# ── SEMI ─────────────────────────────────────────────────────────────────────

def fetch_semi():
    """Scrape SEMI newsroom (browser-like headers)."""
    url = "https://www.semi.org/en/news-media-press/semi-press-releases"
    print(f"  [SEMI] Fetching {url}")
    try:
        html = fetch_html(url)
        soup = BeautifulSoup(html, "lxml")
        items = []

        for el in soup.select("a[href*='/press-release']"):
            link = el.get("href", "")
            if not link:
                continue
            if not link.startswith("http"):
                link = "https://www.semi.org" + link

            title = el.get_text(strip=True)
            if not title or len(title) < 10:
                continue

            items.append({
                "id": make_id(link),
                "title": title,
                "url": link,
                "source": "SEMI",
                "date": "",
                "summary": "",
                "category": "semi",
            })

        seen = set()
        unique = []
        for item in items:
            if item["url"] not in seen:
                seen.add(item["url"])
                unique.append(item)

        print(f"  [SEMI] {len(unique)} press releases")
        return unique[:20]
    except Exception as e:
        print(f"  [SEMI] FAILED: {e}")
        return []


# ── SIA (Semiconductor Industry Association) ─────────────────────────────────

def fetch_sia():
    """Try SIA RSS feed first, fall back to web scraping."""
    print("  [SIA] Trying RSS feed...")
    try:
        import feedparser
        feed = feedparser.parse("https://www.semiconductors.org/feed/")
        if feed.entries:
            items = []
            for entry in feed.entries[:20]:
                title = (entry.get("title") or "").strip()
                link = (entry.get("link") or "").strip()
                if not title or not link:
                    continue
                # Parse date
                date = ""
                for field in ("published_parsed", "updated_parsed"):
                    t = entry.get(field)
                    if t:
                        try:
                            date = datetime(*t[:6]).strftime("%Y-%m-%d")
                        except Exception:
                            pass
                summary = clean_text(entry.get("summary", ""))
                items.append({
                    "id": make_id(link),
                    "title": title,
                    "url": link,
                    "source": "SIA",
                    "date": date,
                    "summary": summary,
                    "category": "semi",
                })
            print(f"  [SIA] {len(items)} items via RSS")
            return items
    except ImportError:
        print("  [SIA] feedparser not available, skipping RSS")
    except Exception as e:
        print(f"  [SIA] RSS failed: {e}")

    # Fallback: try web scraping
    url = "https://www.semiconductors.org/category/press-releases/"
    print(f"  [SIA] Trying web scrape: {url}")
    try:
        html = fetch_html(url)
        soup = BeautifulSoup(html, "lxml")
        items = []

        for article in soup.select("article, .post, .entry, h2 a, h3 a"):
            if article.name in ("a",):
                link = article.get("href", "")
                title = article.get_text(strip=True)
            else:
                link_el = article.select_one("a[href]")
                if not link_el:
                    continue
                link = link_el.get("href", "")
                title = link_el.get_text(strip=True)

            if not title or not link or len(title) < 10:
                continue

            date = ""
            if article.name not in ("a",):
                date_el = article.select_one("time, .date, .entry-date, .post-date")
                if date_el:
                    date = date_el.get("datetime", "") or date_el.get_text(strip=True)
                    for fmt in ("%Y-%m-%d", "%B %d, %Y", "%b %d, %Y"):
                        try:
                            date = datetime.strptime(date[:10], fmt).strftime("%Y-%m-%d")
                            break
                        except ValueError:
                            pass

            summary = ""
            if article.name not in ("a",):
                excerpt_el = article.select_one(".excerpt, .entry-summary, p")
                if excerpt_el:
                    summary = clean_text(excerpt_el.get_text())

            items.append({
                "id": make_id(link),
                "title": title,
                "url": link,
                "source": "SIA",
                "date": date if re.match(r"\d{4}-\d{2}-\d{2}", date or "") else "",
                "summary": summary,
                "category": "semi",
            })

        seen = set()
        unique = []
        for item in items:
            if item["url"] not in seen:
                seen.add(item["url"])
                unique.append(item)

        print(f"  [SIA] {len(unique)} press releases via scrape")
        return unique[:20]
    except Exception as e:
        print(f"  [SIA] FAILED: {e}")
        return []


# ── Satellite Industry Association (SIA — space) ──────────────────────────────

def fetch_sat_sia():
    """Scrape Satellite Industry Association press releases."""
    url = "https://sia.org/news-resources/press-releases/"
    print(f"  [SAT-SIA] Fetching {url}")
    try:
        html = fetch_html(url)
        soup = BeautifulSoup(html, "lxml")
        items = []
        for el in soup.select("a[href*='press-release'], a[href*='news'], h2 a, h3 a"):
            link = el.get("href", "")
            if not link:
                continue
            if not link.startswith("http"):
                link = "https://sia.org" + link
            title = el.get_text(strip=True)
            if not title or len(title) < 10:
                continue
            items.append({
                "id": make_id(link),
                "title": title,
                "url": link,
                "source": "Satellite Industry Association",
                "date": "",
                "summary": "",
                "category": "space",
            })
        seen = set()
        unique = []
        for item in items:
            if item["url"] not in seen:
                seen.add(item["url"])
                unique.append(item)
        print(f"  [SAT-SIA] {len(unique)} press releases")
        return unique[:15]
    except Exception as e:
        print(f"  [SAT-SIA] FAILED: {e}")
        return []


def fetch_space_foundation():
    """Scrape Space Foundation news."""
    url = "https://www.spacefoundation.org/news/"
    print(f"  [SpaceFdn] Fetching {url}")
    try:
        html = fetch_html(url)
        soup = BeautifulSoup(html, "lxml")
        items = []
        for el in soup.select("article a, .post a, h2 a, h3 a"):
            link = el.get("href", "")
            if not link:
                continue
            if not link.startswith("http"):
                link = "https://www.spacefoundation.org" + link
            title = el.get_text(strip=True)
            if not title or len(title) < 10:
                continue
            items.append({
                "id": make_id(link),
                "title": title,
                "url": link,
                "source": "Space Foundation",
                "date": "",
                "summary": "",
                "category": "space",
            })
        seen = set()
        unique = []
        for item in items:
            if item["url"] not in seen:
                seen.add(item["url"])
                unique.append(item)
        print(f"  [SpaceFdn] {len(unique)} articles")
        return unique[:15]
    except Exception as e:
        print(f"  [SpaceFdn] FAILED: {e}")
        return []


def fetch_brycetech():
    """Scrape BryceTech reports/news."""
    url = "https://brycetech.com/reports"
    print(f"  [BryceTech] Fetching {url}")
    try:
        html = fetch_html(url)
        soup = BeautifulSoup(html, "lxml")
        items = []
        for el in soup.select("a[href*='report'], a[href*='briefing'], h2 a, h3 a"):
            link = el.get("href", "")
            if not link:
                continue
            if not link.startswith("http"):
                link = "https://brycetech.com" + link
            title = el.get_text(strip=True)
            if not title or len(title) < 10:
                continue
            items.append({
                "id": make_id(link),
                "title": title,
                "url": link,
                "source": "BryceTech",
                "date": "",
                "summary": "",
                "category": "space",
            })
        seen = set()
        unique = []
        for item in items:
            if item["url"] not in seen:
                seen.add(item["url"])
                unique.append(item)
        print(f"  [BryceTech] {len(unique)} reports")
        return unique[:15]
    except Exception as e:
        print(f"  [BryceTech] FAILED: {e}")
        return []


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    if not HAS_BS4:
        print("ERROR: beautifulsoup4 is required. Run: pip install beautifulsoup4 lxml")
        return

    print("Fetching industry reports...")
    all_reports = []
    all_reports.extend(fetch_ifr())
    all_reports.extend(fetch_semi())
    all_reports.extend(fetch_sia())

    # Space industry sources (continue on error — scraping can be flaky)
    for fetcher, label in [(fetch_sat_sia, "SAT-SIA"), (fetch_space_foundation, "SpaceFdn"), (fetch_brycetech, "BryceTech")]:
        try:
            all_reports.extend(fetcher())
        except Exception as e:
            print(f"  [{label}] SKIPPED (error): {e}")

    # Archive all reports
    current_reports = archive_and_filter(
        items=all_reports,
        archive_path=REPORTS_ARCHIVE_JSON,
        key_field="id",
        current_filter_fn=lambda r: True,  # keep all (reports lack reliable dates)
        data_key="reports",
    )

    # Sort by date descending (items without dates go last)
    current_reports.sort(key=lambda x: x["date"] or "0000", reverse=True)

    output = {
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "source": "IFR / SEMI / SIA",
        "count": len(current_reports),
        "reports": current_reports,
    }

    with open(REPORTS_JSON, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nWrote {len(current_reports)} reports to {REPORTS_JSON}")
    print(f"Archive: {REPORTS_ARCHIVE_JSON}")


if __name__ == "__main__":
    main()
