#!/usr/bin/env python3
"""
Loremaster — grounded scene briefs from long-context reading, cached + gated.

Instead of stapling nearest-neighbor chunks, the Loremaster uses the coarse index
to FIND the relevant chapter, then reads a large span and returns a grounded
brief. Briefs are cached PER LOCATION and a deep read is gated to new/important
scenes — routine revisits reuse the cache, so the expensive read never fires every
turn. (The voice-grounded synthesis of the brief is the model's job in /gm; this
module owns the find/cache/gate/observe machinery + the source excerpt.)
"""

import sys
from pathlib import Path
from typing import Any, Dict, Optional

sys.path.insert(0, str(Path(__file__).parent))

from entity_manager import EntityManager
from book_bible import log_token_estimate
from rag.coarse_index import CoarseIndex


class Loremaster(EntityManager):
    def __init__(self, world_state_dir: str = None, book_text: Optional[str] = None):
        super().__init__(world_state_dir)
        self.cache_file = "loremaster-cache.json"
        self.index = CoarseIndex()
        text = book_text if book_text is not None else self._load_book_text()
        if text:
            self.index.build(text)

    def _load_book_text(self) -> str:
        for candidate in ("current-document.txt", "book-text.txt"):
            p = self.campaign_dir / candidate
            if p.exists():
                try:
                    return p.read_text(encoding="utf-8")
                except (IOError, ValueError):
                    return ""
        return ""

    def _cache(self) -> Dict[str, Any]:
        return self.json_ops.load_json(self.cache_file) or {}

    def brief_for(self, location: str, important: bool = False) -> Dict[str, Any]:
        """Grounded brief for a scene. Deep-reads only on a new or important scene."""
        cache = self._cache()
        in_cache = location in cache

        # Routine revisit: reuse the cache, NO deep read (keeps per-turn cost flat).
        if in_cache and not important:
            cached = dict(cache[location])
            cached["cache_hit"] = True
            cached["deep_read"] = False
            return cached

        # New or important scene: find the chapter, read a span, ground the brief.
        pointers = self.index.query(location)
        excerpt = ""
        if pointers:
            chapter = self.index.load_chapter(pointers[0]["index"])
            excerpt = chapter.get("text", "")[:500]
            log_token_estimate(chapter.get("text", ""), label="loremaster")

        brief = {
            "location": location,
            "chapters": pointers,
            "grounded_excerpt": excerpt,
            "deep_read": True,
            "cache_hit": False,
        }
        cache[location] = brief
        self.json_ops.save_json(self.cache_file, cache)
        return brief


def main():
    import argparse
    import json
    from cli_output import wants_json, strip_json_flag, emit

    parser = argparse.ArgumentParser(description="Loremaster scene brief")
    parser.add_argument("location", nargs="+")
    parser.add_argument("--important", action="store_true")
    json_mode = wants_json()
    args = parser.parse_args(strip_json_flag(sys.argv[1:]))

    brief = Loremaster().brief_for(" ".join(args.location), important=args.important)
    if json_mode:
        emit(brief, json_mode=True)
    else:
        print(json.dumps(brief, indent=2))


if __name__ == "__main__":
    main()
