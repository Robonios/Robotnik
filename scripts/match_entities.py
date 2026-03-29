"""
Entity Matcher — matches text against the Robotnik entity registry.

Usage:
  python3 scripts/match_entities.py "TSMC expands CoWoS for NVIDIA"
  → ["TSM", "NVDA"]

Also importable:
  from match_entities import EntityMatcher
  matcher = EntityMatcher()
  matches = matcher.match("TSMC expands CoWoS for NVIDIA")
"""

import json, re, os, sys

REGISTRY_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'entities', 'registry.json')

# Short tickers that need context to avoid false positives
AMBIGUOUS_SHORT = {'ON', 'ARM', 'AI', 'MP', 'GE', 'HP', 'AM', 'IT', 'BE', 'OR'}

# Context words that make short ticker matches more likely
TECH_CONTEXT = {
    'ON': ['semiconductor', 'semi', 'onsemi', 'silicon carbide', 'sic', 'power'],
    'ARM': ['chip', 'semiconductor', 'processor', 'cpu', 'mobile', 'holdings', 'architecture', 'cortex', 'neoverse', 'licensing'],
    'AI': ['artificial intelligence'],
    'MP': ['materials', 'rare earth', 'mining', 'magnet'],
}


class EntityMatcher:
    def __init__(self, registry_path=None):
        path = registry_path or REGISTRY_PATH
        with open(path) as f:
            self.registry = json.load(f)
        self._build_index()

    def _build_index(self):
        """Build inverted index: alias → entity_id, sorted longest-first."""
        self.alias_map = {}
        for eid, ent in self.registry.items():
            for alias in ent.get('aliases', []):
                a_lower = alias.lower().strip()
                if len(a_lower) < 2:
                    continue
                # Prefer longer/more specific aliases; don't overwrite if existing is from same entity
                if a_lower not in self.alias_map or len(eid) > len(self.alias_map[a_lower]):
                    self.alias_map[a_lower] = eid

        # Sort aliases longest-first for greedy matching
        self.sorted_aliases = sorted(self.alias_map.keys(), key=len, reverse=True)

    def match(self, text):
        """Return list of matched entity IDs from text."""
        if not text:
            return []
        text_lower = text.lower()
        matched = set()
        consumed = set()  # Track consumed character ranges

        for alias in self.sorted_aliases:
            # Skip very short aliases (1-2 chars)
            if len(alias) <= 2:
                continue

            # Find word-boundary matches
            pattern = r'(?<![a-zA-Z])' + re.escape(alias) + r'(?![a-zA-Z])'
            for m in re.finditer(pattern, text_lower):
                start, end = m.start(), m.end()
                # Check if this range overlaps with already-consumed text
                if any(start < ce and end > cs for cs, ce in consumed):
                    continue

                eid = self.alias_map[alias]

                # Handle ambiguous short tickers
                ticker = eid.upper()
                if ticker in AMBIGUOUS_SHORT and len(alias) <= 3:
                    # Require tech context nearby (within 100 chars)
                    context_words = TECH_CONTEXT.get(ticker, [])
                    if context_words:
                        window = text_lower[max(0, start-100):min(len(text_lower), end+100)]
                        if not any(cw in window for cw in context_words):
                            continue

                matched.add(eid)
                consumed.add((start, end))

        return sorted(matched)

    def match_tickers_only(self, text):
        """Return only public company tickers (not private entity IDs)."""
        all_matches = self.match(text)
        return [eid for eid in all_matches if self.registry.get(eid, {}).get('type') == 'public']


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 match_entities.py \"text to match\"")
        sys.exit(1)
    matcher = EntityMatcher()
    text = ' '.join(sys.argv[1:])
    matches = matcher.match(text)
    print(json.dumps(matches))
