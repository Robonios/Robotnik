"""
Robotnik RSS News Aggregator
==============================
Fetches news from ~38 RSS feeds covering robotics, semiconductors,
space technology, AI/ML hardware, and supply chain. Outputs news.json.

Setup:
  pip install feedparser

Usage:
  python fetch_news.py

Output:
  news.json — up to 150 items from last 12 months, sorted newest-first
  archive_news.json — full historical archive
"""

import feedparser
import json
import hashlib
import re
import time
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from config import NEWS_JSON, NEWS_ARCHIVE_JSON
from archive_utils import archive_and_filter

# ── Feed definitions ─────────────────────────────────────────────────────────

FEEDS = [
    # Robotics — industry outlets
    {"url": "https://www.therobotreport.com/feed/", "source": "The Robot Report", "category": "robo", "broad": False},
    {"url": "https://spectrum.ieee.org/feeds/topic/robotics.rss", "source": "IEEE Spectrum Robotics", "category": "robo", "broad": False},
    {"url": "https://robohub.org/feed/", "source": "Robohub", "category": "robo", "broad": False},
    {"url": "https://www.roboticstomorrow.com/rss/news", "source": "Robotics Tomorrow", "category": "robo", "broad": False},
    {"url": "https://www.automate.org/rss/blogs", "source": "Automate.org", "category": "robo", "broad": False},
    {"url": "https://www.automationworld.com/rss", "source": "Automation World", "category": "robo", "broad": False},

    # Semiconductors — industry outlets
    {"url": "https://semiengineering.com/feed/", "source": "SemiEngineering", "category": "semi", "broad": False},
    {"url": "https://www.eetimes.com/feed/", "source": "EE Times", "category": "semi", "broad": False},
    {"url": "https://www.semiconductor-today.com/rss.shtml", "source": "Semiconductor Today", "category": "semi", "broad": False},
    {"url": "https://thelec.net/rss/S1N3.xml", "source": "The Elec", "category": "semi", "broad": False},
    {"url": "https://www.eenewseurope.com/en/feed/", "source": "eeNews Europe", "category": "semi", "broad": False},
    {"url": "https://www.electronicsweekly.com/feed/", "source": "Electronics Weekly", "category": "semi", "broad": False},

    # Deep technical analysis (Substacks)
    {"url": "https://semianalysis.com/feed", "source": "SemiAnalysis", "category": "semi", "broad": False},
    {"url": "https://www.fabricatedknowledge.com/feed", "source": "Fabricated Knowledge", "category": "semi", "broad": False},
    {"url": "https://www.asianometry.com/feed", "source": "Asianometry", "category": "semi", "broad": False},

    # Business/tech press (broad — keyword-filtered)
    {"url": "https://feeds.arstechnica.com/arstechnica/index", "source": "Ars Technica", "category": "ai", "broad": True},
    {"url": "https://techcrunch.com/category/artificial-intelligence/feed/", "source": "TechCrunch AI", "category": "ai", "broad": True},
    {"url": "https://techcrunch.com/tag/robotics/feed/", "source": "TechCrunch Robotics", "category": "robo", "broad": True},
    {"url": "https://venturebeat.com/category/ai/feed/", "source": "VentureBeat AI", "category": "ai", "broad": True},
    {"url": "https://www.theverge.com/rss/robots/index.xml", "source": "The Verge Robotics", "category": "robo", "broad": True},

    # Supply chain
    {"url": "https://www.supplychaindive.com/feeds/news/", "source": "Supply Chain Dive", "category": "supply", "broad": True},

    # Policy & regulation
    {"url": "https://www.commerce.gov/feeds/news", "source": "Commerce Dept", "category": "supply", "broad": True},

    # Company blogs
    {"url": "https://blogs.nvidia.com/feed/", "source": "NVIDIA Blog", "category": "ai", "broad": False},
    {"url": "https://nvidianews.nvidia.com/rss.xml", "source": "NVIDIA Newsroom", "category": "ai", "broad": False},
    {"url": "https://developer.nvidia.com/blog/feed/", "source": "NVIDIA Developer", "category": "ai", "broad": False},
    {"url": "https://bostondynamics.com/feed/", "source": "Boston Dynamics", "category": "robo", "broad": False},
    {"url": "https://community.arm.com/arm-community-blogs/b/announcements/rss", "source": "ARM Community", "category": "semi", "broad": False},
    {"url": "https://pr.tsmc.com/english/rss", "source": "TSMC Newsroom", "category": "semi", "broad": False},

    # Space technology
    {"url": "https://spacenews.com/feed/", "source": "SpaceNews", "category": "space", "broad": False},
    {"url": "https://payloadspace.com/feed/", "source": "Payload Space", "category": "space", "broad": False},
    {"url": "https://www.nasaspaceflight.com/feed/", "source": "NASASpaceflight", "category": "space", "broad": False},
    {"url": "https://www.space.com/feeds/all", "source": "Space.com", "category": "space", "broad": True},
    {"url": "https://www.theverge.com/rss/space/index.xml", "source": "The Verge Space", "category": "space", "broad": True},
    {"url": "https://feeds.arstechnica.com/arstechnica/science", "source": "Ars Technica Science", "category": "space", "broad": True},
    {"url": "https://spaceref.com/feed/", "source": "SpaceRef", "category": "space", "broad": False},
    {"url": "https://www.esa.int/rssfeed/Our_Activities/Space_News", "source": "ESA News", "category": "space", "broad": False},

    # Research aggregators (keyword-filtered)
    {"url": "https://rss.arxiv.org/rss/cs.RO", "source": "arXiv Robotics", "category": "robo", "broad": False},
    {"url": "https://rss.arxiv.org/rss/cs.AI", "source": "arXiv AI", "category": "ai", "broad": True},
]

# Keywords for filtering broad feeds
KEYWORDS = [
    "robot", "robotics", "humanoid", "cobot", "automation", "autonomous",
    "semiconductor", "chip", "wafer", "foundry", "fabrication", "silicon",
    "nvidia", "tsmc", "asml", "intel", "amd", "qualcomm", "broadcom",
    "euv", "lithography", "packaging", "mcm", "chiplet",
    "gpu", "ai chip", "ai accelerator", "edge computing", "inference",
    "lidar", "sensor fusion", "actuator", "motor control",
    "supply chain", "fab", "manufacturing",
    "boston dynamics", "figure ai", "tesla bot", "optimus",
    # Space technology
    "satellite", "launch vehicle", "rocket", "orbit", "spacecraft",
    "spacex", "rocket lab", "starlink", "space station", "lunar",
    "mars", "constellation", "spaceport", "reusable rocket",
    "space debris", "earth observation", "cubesat", "smallsat",
]

MAX_ITEMS = 150
DEDUP_THRESHOLD = 0.80


# ── Helpers ──────────────────────────────────────────────────────────────────

def make_id(url):
    return hashlib.sha256(url.encode()).hexdigest()[:12]


def normalize(text):
    return re.sub(r"[^a-z0-9 ]", "", text.lower()).strip()


def is_relevant(entry, feed):
    """For broad feeds, check if the entry matches domain keywords."""
    if not feed.get("broad"):
        return True
    text = ((entry.get("title") or "") + " " + (entry.get("summary") or "")).lower()
    return any(kw in text for kw in KEYWORDS)


def parse_date(entry):
    """Extract and normalize date from a feed entry."""
    for field in ("published_parsed", "updated_parsed"):
        t = entry.get(field)
        if t:
            try:
                return datetime(*t[:6]).strftime("%Y-%m-%d")
            except Exception:
                pass
    for field in ("published", "updated"):
        raw = entry.get(field, "")
        if raw:
            # Try ISO-ish formats
            for fmt in ("%Y-%m-%dT%H:%M:%S", "%a, %d %b %Y %H:%M:%S"):
                try:
                    return datetime.strptime(raw[:19], fmt).strftime("%Y-%m-%d")
                except ValueError:
                    pass
    return ""


def clean_summary(html, max_len=200):
    """Strip HTML tags and truncate."""
    text = re.sub(r"<[^>]+>", "", html or "")
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > max_len:
        text = text[:max_len].rsplit(" ", 1)[0] + "..."
    return text


def deduplicate(items):
    """Remove duplicates by URL and title similarity."""
    seen_urls = set()
    seen_titles = []
    unique = []
    for item in items:
        url = item["url"]
        if url in seen_urls:
            continue
        title_norm = normalize(item["title"])
        is_dup = False
        for prev in seen_titles:
            if SequenceMatcher(None, title_norm, prev).ratio() > DEDUP_THRESHOLD:
                is_dup = True
                break
        if is_dup:
            continue
        seen_urls.add(url)
        seen_titles.append(title_norm)
        unique.append(item)
    return unique


# ── Main ─────────────────────────────────────────────────────────────────────

def fetch_all():
    items = []
    for feed_def in FEEDS:
        url = feed_def["url"]
        source = feed_def["source"]
        category = feed_def["category"]
        try:
            feed = feedparser.parse(url)
            count = 0
            for entry in feed.entries[:30]:
                if not is_relevant(entry, feed_def):
                    continue
                title = (entry.get("title") or "").strip()
                link = (entry.get("link") or "").strip()
                if not title or not link:
                    continue
                items.append({
                    "id": make_id(link),
                    "title": title,
                    "url": link,
                    "source": source,
                    "date": parse_date(entry),
                    "category": category,
                    "summary": clean_summary(entry.get("summary", "")),
                })
                count += 1
            print(f"  [{source}] {count} items")
        except Exception as e:
            print(f"  [{source}] FAILED: {e}")

    # Sort newest first, deduplicate, cap
    items.sort(key=lambda x: x["date"], reverse=True)
    items = deduplicate(items)
    items = items[:MAX_ITEMS]
    return items


def tag_entities(items):
    """Tag each news item with matched entity IDs from the registry."""
    try:
        from match_entities import EntityMatcher
        matcher = EntityMatcher()
    except Exception as e:
        print(f"  Entity tagging skipped (matcher unavailable): {e}")
        return items

    tagged_count = 0
    for item in items:
        # Skip items already tagged (preserve existing tags on re-fetch)
        if item.get("mentioned_entities") and item.get("entity_tagged"):
            continue
        text = (item.get("title", "") + " " + item.get("summary", "")).strip()
        entities = matcher.match(text)
        tickers = matcher.match_tickers_only(text)
        item["mentioned_entities"] = entities
        item["mentioned_tickers"] = tickers
        item["entity_tagged"] = datetime.now().strftime("%Y-%m-%d")
        if entities:
            tagged_count += 1

    total_tagged = sum(1 for i in items if i.get("mentioned_entities"))
    print(f"  Entity tagging: {tagged_count} newly tagged, {total_tagged}/{len(items)} total")
    return items


def merge_existing_tags(items):
    """Preserve entity tags from previously saved items."""
    try:
        with open(NEWS_JSON) as f:
            existing = json.load(f)
        existing_by_id = {i["id"]: i for i in existing.get("items", [])}
    except (FileNotFoundError, json.JSONDecodeError):
        return items

    preserved = 0
    for item in items:
        prev = existing_by_id.get(item["id"])
        if prev and prev.get("entity_tagged"):
            item["mentioned_entities"] = prev.get("mentioned_entities", [])
            item["mentioned_tickers"] = prev.get("mentioned_tickers", [])
            item["entity_tagged"] = prev["entity_tagged"]
            preserved += 1

    if preserved:
        print(f"  Preserved entity tags from {preserved} existing items")
    return items


def main():
    print("Fetching RSS feeds...")
    items = fetch_all()

    # Archive all items, retain only last 12 months for live output
    cutoff = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    current_items = archive_and_filter(
        items=items,
        archive_path=NEWS_ARCHIVE_JSON,
        key_field="id",
        current_filter_fn=lambda n: (n.get("date", "") or "9999") >= cutoff,
        data_key="items",
    )
    current_items = current_items[:MAX_ITEMS]

    # Preserve existing entity tags, then tag untagged items
    current_items = merge_existing_tags(current_items)
    current_items = tag_entities(current_items)

    output = {
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "source": "RSS Aggregation",
        "count": len(current_items),
        "items": current_items,
    }

    with open(NEWS_JSON, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nWrote {len(current_items)} items to {NEWS_JSON}")
    print(f"Archive: {NEWS_ARCHIVE_JSON}")


if __name__ == "__main__":
    main()
