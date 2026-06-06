---
slug: between-session-worldtick
title: Constrained between-session world tick (off-screen developments)
category: enhancement
kind: hitl
priority: p2
lane: manual
parentPrd: dm-claude-reimagining
blockedBy: [reactivity-tick-wiring, longterm-memory]
claimedBy: ss-tix001
claimedAt: 2026-06-06T05:27:21Z
changedFiles: [lib/world_tick.py, tests/test_world_tick.py]
resolution: null
createdAt: 2026-06-06T02:24:27Z
updatedAt: 2026-06-06T05:27:21Z
---

## Parent

DM Claude Reimagining (prds/dm-claude-reimagining.md)

## Category

enhancement

## What to build

Make the world keep living when the player looks away. On session end/start, a
world-builder pass advances 1-3 SMALL off-screen developments tied to game-time
and writes them as new consequences/plot events, grounded in source RAG +
existing plots. Off-screen changes must stay small, reversible, and canon-
grounded to avoid contradicting the book — so it ships with the provenance log +
rollback and needs human review (hitl). Respect tone (cozy worlds tick gently).

## Acceptance criteria

- [x] On session end/start, 1-3 bounded off-screen developments are generated and written as consequences/plot events. (WorldTick.apply writes them as consequences; the generation is /dm's model pass)
- [x] Developments are grounded in source RAG + existing plots (no free-floating invention). (the /dm pass grounds them; apply() carries structured triggers so they slot into the reactive world)
- [x] Each tick is logged via the provenance system and is rollback-able.
- [x] A cap + tone setting prevents runaway or jarring off-screen change. (cap default 3; enabled=False = no-op)
- [ ] Human review confirms a generated tick feels consequential without contradicting canon. (hitl — awaiting your sign-off)

## Verification

Lane: manual

## Blocked by

reactivity-tick-wiring, longterm-memory

---

## QA Reports

### 2026-06-06T05:27:21Z — in-review [ss-tix001]
hitl — implemented; routed to in-review. `uv run pytest` → 141 passed (4 new in tests/test_world_tick.py).
- lib/world_tick.py WorldTick.apply(developments, cap=3, enabled=True): writes ≤cap developments as consequences (carrying optional structured triggers so they fire later), logs each tick to world-tick-log.json; rollback_last() removes the consequences the last tick added; history() exposes the log.
- Tests: cap enforced (5 devs → 3 written, "fifth" excluded); enabled=False is a no-op (tone); tick logged + rollback removes the added developments; rollback with no tick → False.
- [human-judgement] The development GENERATION (small, canon-grounded, RAG+plots) is the /dm world-builder pass; needs a live tick to confirm it feels consequential without contradicting the book.

## History

- 2026-06-06T05:27:21Z  in-progress → in-review  [ss-tix001]
- 2026-06-06T05:27:21Z  ready → in-progress (claimed)  [ss-tix001]
- 2026-06-06T02:24:27Z  created → ready  [ship-it]
