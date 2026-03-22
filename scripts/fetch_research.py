"""
Robotnik OpenAlex Research Fetcher
=====================================
Fetches recent academic papers on robotics, semiconductors, and space
technology from the OpenAlex API. Outputs research.json.

No external dependencies — uses urllib from stdlib.

Usage:
  python fetch_research.py

Output:
  research.json — up to 200 papers from Jan 2023+, sorted newest-first
  archive_research.json — full historical archive
"""

import json
import time
import urllib.request
import urllib.parse
from datetime import datetime
from config import RESEARCH_JSON, RESEARCH_ARCHIVE_JSON
from archive_utils import archive_and_filter

BASE_URL = "https://api.openalex.org/works"

# Targeted search queries across key topic areas
SEARCH_QUERIES = [
    {"query": "robotics autonomous manipulation", "category": "robo"},
    {"query": "humanoid robot locomotion control", "category": "robo"},
    {"query": "semiconductor fabrication EUV lithography", "category": "semi"},
    {"query": "AI accelerator chip design neural", "category": "semi"},
    {"query": "robot foundation model embodied AI", "category": "ai"},
    {"query": "neuromorphic computing spiking neural", "category": "semi"},
    {"query": "collaborative robot industrial automation", "category": "robo"},
    {"query": "semiconductor supply chain resilience", "category": "supply"},
    {"query": "robot perception vision transformer", "category": "robo"},
    {"query": "chiplet advanced packaging integration", "category": "semi"},
    # Space technology
    {"query": "satellite constellation orbital deployment", "category": "space"},
    {"query": "launch vehicle reusable rocket propulsion", "category": "space"},
    {"query": "in-orbit servicing space debris removal", "category": "space"},
    {"query": "radiation hardened semiconductor space", "category": "space"},
    {"query": "space robotics autonomous spacecraft", "category": "space"},
    {"query": "Earth observation satellite remote sensing", "category": "space"},
]

PER_PAGE = 25
MAX_PAPERS = 200


def reconstruct_abstract(inverted_index):
    """Convert OpenAlex abstract_inverted_index to plain text."""
    if not inverted_index:
        return ""
    word_positions = []
    for word, positions in inverted_index.items():
        for pos in positions:
            word_positions.append((pos, word))
    word_positions.sort()
    text = " ".join(w for _, w in word_positions)
    if len(text) > 300:
        text = text[:300].rsplit(" ", 1)[0] + "..."
    return text


def search_openalex(query, category):
    """Run a single search query against OpenAlex."""
    params = urllib.parse.urlencode({
        "search": query,
        "mailto": "data@robotniks.com",
        "filter": "from_publication_date:2023-01-01",
        "sort": "publication_date:desc",
        "per_page": PER_PAGE,
    })
    url = f"{BASE_URL}?{params}"

    req = urllib.request.Request(url, headers={
        "User-Agent": "Robotniks/1.0 (research fetcher)",
        "Accept": "application/json",
    })

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        results = data.get("results", [])
        papers = []
        for work in results:
            title = (work.get("title") or "").strip()
            if not title:
                continue

            # Authors — first 5
            authorships = work.get("authorships", [])
            authors = []
            for a in authorships[:5]:
                name = a.get("author", {}).get("display_name", "")
                if name:
                    authors.append(name)

            # Journal / source
            source_info = work.get("primary_location", {}) or {}
            source_obj = source_info.get("source", {}) or {}
            journal = source_obj.get("display_name", "")

            # Abstract
            abstract = reconstruct_abstract(work.get("abstract_inverted_index"))

            # DOI
            doi = work.get("doi") or ""
            doi_url = doi if doi.startswith("http") else (f"https://doi.org/{doi}" if doi else "")

            # Topics
            topics = []
            for t in (work.get("topics") or [])[:4]:
                name = t.get("display_name", "")
                if name:
                    topics.append(name)

            papers.append({
                "id": work.get("id", ""),
                "title": title,
                "authors": authors,
                "date": (work.get("publication_date") or "")[:10],
                "journal": journal,
                "abstract_snippet": abstract,
                "doi_url": doi_url,
                "citation_count": work.get("cited_by_count", 0),
                "open_access": work.get("open_access", {}).get("is_oa", False),
                "category": category,
                "topics": topics,
            })
        return papers
    except Exception as e:
        print(f"  ERROR for '{query}': {e}")
        return []


def main():
    print("Fetching research papers from OpenAlex...")
    all_papers = []
    seen_ids = set()

    for qdef in SEARCH_QUERIES:
        query = qdef["query"]
        category = qdef["category"]
        print(f"  Searching: {query}")
        papers = search_openalex(query, category)
        for p in papers:
            if p["id"] not in seen_ids:
                seen_ids.add(p["id"])
                all_papers.append(p)
        print(f"    → {len(papers)} results ({len(all_papers)} total unique)")
        time.sleep(0.15)  # respect rate limit

    # Archive all papers, filter for current output (Jan 2023+)
    current_papers = archive_and_filter(
        items=all_papers,
        archive_path=RESEARCH_ARCHIVE_JSON,
        key_field="id",
        current_filter_fn=lambda p: (p.get("date", "") or "") >= "2023-01-01",
        data_key="papers",
    )
    current_papers = current_papers[:MAX_PAPERS]

    output = {
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "source": "OpenAlex",
        "count": len(current_papers),
        "papers": current_papers,
    }

    with open(RESEARCH_JSON, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nWrote {len(current_papers)} papers to {RESEARCH_JSON}")
    print(f"Archive: {RESEARCH_ARCHIVE_JSON}")


if __name__ == "__main__":
    main()
