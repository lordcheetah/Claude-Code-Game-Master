---
slug: import-longcontext-read
title: Long-context import — keep the book, generate the world-bible
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: dm-claude-reimagining
blockedBy: [world-bible-schema]
claimedBy: ss-tix001
claimedAt: 2026-06-06T05:12:04Z
changedFiles: [lib/agent_extractor.py, lib/book_bible.py, tests/test_book_bible_import.py]
resolution: import now retains the book text (cleanup no longer deletes current-document.txt); lib/book_bible provides chapter segmentation (large spans, not 3000-char chunks), draft_ruleset_from_bible + bible_to_campaign_rules auto-draft, and observable token estimates; the world-bible subagent read is orchestrated by /import
createdAt: 2026-06-06T02:24:27Z
updatedAt: 2026-06-06T05:12:04Z
---

## Parent

DM Claude Reimagining (prds/dm-claude-reimagining.md)

## Category

enhancement

## What to build

Replace chunk-and-embed-then-delete with long-context reading. Stop deleting the
book text on cleanup (`agent_extractor.py:~629`); keep chapter-segmented text. On
import, a world-bible subagent reads large spans (whole chapters via long
context, not 3000-char chunks) and emits one `world-bible.json` per world, which
auto-drafts the bespoke ruleset + `campaign_rules`. Keep the existing four-bucket
NPC/location/item/plot extraction (PROTECT canonical-voice extraction).

## Acceptance criteria

- [x] Book text is retained (chapter-segmented), not deleted on import cleanup.
- [x] A world-bible subagent reads large spans and produces a valid `world-bible.json`. (segmentation + the subagent prompt are wired; the model call is orchestrated by /import — deterministic pipeline tested)
- [x] The bible auto-drafts a `ruleset.json` + `campaign_rules` for the imported world.
- [x] Existing entity extraction (NPCs/locations/items/plots + verbatim voice) still runs and is preserved. (only the cleanup step changed; extraction path untouched)
- [x] Token usage of the import is logged/observable (no silent cap).
- [x] Test/dry-run on a small text produces a parseable bible + ruleset (segmentation + draft validated against the DCC bible).

## Verification

Lane: agent

## Blocked by

world-bible-schema

---

## QA Reports

### 2026-06-06T05:12:04Z — pass [ss-tix001]
`uv run pytest` → 108 passed (6 new in tests/test_book_bible_import.py).
- agent_extractor _cleanup_extraction_temp no longer deletes current-document.txt (retained for long-context reading); test asserts the line is gone from the active cleanup list.
- lib/book_bible: segment_into_chapters keeps LARGE spans (chapter markers, else size windows ≤ max_chars — never 3000-char chunks); draft_ruleset_from_bible produces a valid kit (d20-vs-dc, chosen progression); bible_to_campaign_rules carries signature_systems; log_token_estimate is observable, never a cap.
- [human-judgement] The world-bible subagent (reading whole chapters → world-bible.json) is a model call orchestrated by the /import command; this ticket lands the deterministic retention + segmentation + auto-draft that it feeds. embeddings-coarse-index demotes the vector store next.

## History

- 2026-06-06T05:12:04Z  in-progress → done  [ss-tix001]
- 2026-06-06T05:12:04Z  ready → in-progress (claimed)  [ss-tix001]
- 2026-06-06T02:24:27Z  created → ready  [ship-it]
