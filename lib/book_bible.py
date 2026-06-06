#!/usr/bin/env python3
"""
Book Bible import helpers — long-context reading instead of chunk-and-delete.

The import flow keeps the book text (not deleted on cleanup), a world-bible
subagent reads LARGE spans (whole chapters via long context, not 3000-char
chunks) and emits a structured world-bible.json, and that bible AUTO-DRAFTS the
World Kit ruleset + campaign_rules. This module holds the deterministic, testable
pieces: chapter segmentation, the bible→ruleset/campaign_rules draft, and token
observability. The subagent read itself is orchestrated by the /import command.
"""

import re
import sys
from typing import Any, Dict, List

_CHAPTER_RE = re.compile(r'^\s*(chapter\s+\w+|part\s+\w+|\d+\.\s)', re.IGNORECASE | re.MULTILINE)


def segment_into_chapters(text: str, max_chars: int = 20000) -> List[Dict[str, Any]]:
    """Split book text into large spans for long-context reading.

    Prefers real chapter markers; falls back to size-based windows so a span is
    never an arbitrary 3000-char chunk. Returns [{index, title, text}].
    """
    if not text:
        return []
    marks = [m.start() for m in _CHAPTER_RE.finditer(text)]
    spans: List[str] = []
    if len(marks) >= 2:
        bounds = marks + [len(text)]
        for i in range(len(marks)):
            spans.append(text[bounds[i]:bounds[i + 1]])
    else:
        spans = [text]

    # Further split any span that exceeds max_chars (keep spans large, not tiny).
    chapters: List[Dict[str, Any]] = []
    idx = 0
    for span in spans:
        span = span.strip()
        if not span:
            continue
        if len(span) <= max_chars:
            pieces = [span]
        else:
            pieces = [span[i:i + max_chars] for i in range(0, len(span), max_chars)]
        for piece in pieces:
            first_line = piece.strip().splitlines()[0][:60] if piece.strip() else f"Span {idx + 1}"
            chapters.append({"index": idx, "title": first_line, "text": piece})
            idx += 1
    return chapters


def bible_to_campaign_rules(bible: Dict[str, Any]) -> Dict[str, Any]:
    """Map a world-bible's signature systems into a campaign_rules block."""
    systems = bible.get("signature_systems", []) or []
    return {
        "description": f"{bible.get('name', 'This world')} runs on its own systems — follow them exactly.",
        "signature_systems": list(systems),
        "tone": bible.get("tone", ""),
    }


def draft_ruleset_from_bible(bible: Dict[str, Any], progression_model: str = "milestone",
                             **progression_config) -> Dict[str, Any]:
    """Auto-draft a World Kit ruleset.json from a world-bible.

    progression_model is chosen by the importer / human (default milestone, the
    safest book-native option). Resolution defaults to the universal d20-vs-dc core.
    """
    progression = {"model": progression_model}
    progression.update(progression_config)
    return {
        "name": bible.get("name", "Imported World"),
        "stat_schema": {"attributes": [], "vitals": ["hp"]},
        "progression": progression,
        "resolution": {"model": "d20-vs-dc"},
        "active_agents": ["monster-manual", "loot-dropper", "gear-master"],
        "rules_doc": "rules.md",
    }


def log_token_estimate(text: str, label: str = "import") -> int:
    """Observable (never a cap) token estimate, emitted to stderr."""
    approx = len(text or "") // 4
    print(f"[{label}] ~{approx} tokens ({len(text or '')} chars)", file=sys.stderr)
    return approx
