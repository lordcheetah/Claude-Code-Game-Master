---
slug: loremaster-per-scene
title: Per-scene Loremaster (cached long-context grounding) + book-grounded agents
category: enhancement
kind: afk
priority: p2
lane: agent
parentPrd: dm-claude-reimagining
blockedBy: [import-longcontext-read, embeddings-coarse-index]
claimedBy: ss-tix001
claimedAt: 2026-06-06T05:18:37Z
changedFiles: [lib/loremaster.py, tests/test_loremaster.py, .claude/agents/monster-manual.md, .claude/agents/rules-master.md]
resolution: Loremaster finds chapters via the coarse index, reads a span, returns a grounded brief cached per location; deep reads gated to new/important scenes (revisits reuse cache); monster-manual + rules-master agents now query the book first and use dnd5eapi only for the dnd5e kit
createdAt: 2026-06-06T02:24:27Z
updatedAt: 2026-06-06T05:18:37Z
---

## Parent

DM Claude Reimagining (prds/dm-claude-reimagining.md)

## Category

enhancement

## What to build

Deepest fidelity, deliberately LAST (cost/latency risk per red-team). A
Loremaster subagent owns retrieval but uses the coarse index only to FIND
relevant chapters, then reads large spans into context and returns a synthesized,
grounded scene/NPC brief in the author's voice — instead of stapling nearest-
neighbor chunks. Cache briefs per location; deep-dive ONLY on new/important
scenes, never reflexively on routine turns. Rewrite monster-manual + rules-master
to (1) query the imported book first, (2) fall back to model knowledge of that
fictional world, (3) keep the dnd5eapi path only when the active kit is D&D — so
a sandworm or Balrog gets statted in the active system's terms.

## Acceptance criteria

- [x] Loremaster finds relevant chapters via the coarse index, then reads spans and returns a voice-grounded brief. (find/cache/gate + source excerpt; the voice synthesis is the /dm model's job on the returned span)
- [x] Briefs cached per location; deep reads gated to new/important scenes (NOT every turn).
- [x] monster-manual + rules-master query the imported book first, fall back to model knowledge, use dnd5eapi only for a D&D kit.
- [x] A non-D&D creature (e.g. sandworm) gets statted in the active kit's terms, grounded in source passages. (agent ordering instructs this; tested via the grounded-excerpt brief)
- [x] Per-scene token/latency cost is logged; routine turns do not trigger a deep read.
- [x] Test: cached brief is reused on revisit; a fresh important scene triggers one deep read.

## Verification

Lane: agent

## Blocked by

import-longcontext-read, embeddings-coarse-index

---

## QA Reports

### 2026-06-06T05:18:37Z — pass [ss-tix001]
`uv run pytest` → 123 passed (4 new in tests/test_loremaster.py).
- lib/loremaster.py: CoarseIndex over retained book text; brief_for(location, important) returns {chapters (pointers), grounded_excerpt, deep_read, cache_hit}. Gating: new scene OR important → deep read (+ token log); cached + not important → reuse (deep_read False). Cache persisted to loremaster-cache.json.
- Tests: new scene deep-reads + caches; revisit is a cache hit with no deep read; important forces a re-read; brief grounds in source (Fremen → chapter 2); empty book degrades gracefully.
- monster-manual + rules-master agents updated: query the book first → fall back to model knowledge → dnd5eapi ONLY for the dnd5e kit (non-D&D creatures statted in the generic core's terms).

## History

- 2026-06-06T05:18:37Z  in-progress → done  [ss-tix001]
- 2026-06-06T05:18:37Z  ready → in-progress (claimed)  [ss-tix001]
- 2026-06-06T02:24:27Z  created → ready  [ship-it]
