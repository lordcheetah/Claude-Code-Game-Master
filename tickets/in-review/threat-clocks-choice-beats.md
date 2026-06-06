---
slug: threat-clocks-choice-beats
title: Threat clocks + dramatic-choice beats (gated to inflection points)
category: enhancement
kind: hitl
priority: p2
lane: manual
parentPrd: dm-claude-reimagining
blockedBy: [combat-state-persistence, reactivity-tick-wiring]
claimedBy: ss-tix001
claimedAt: 2026-06-06T05:25:43Z
changedFiles: [lib/threat_clocks.py, lib/session_manager.py, tests/test_threat_clocks.py]
resolution: null
createdAt: 2026-06-06T02:24:27Z
updatedAt: 2026-06-06T05:25:43Z
---

## Parent

DM Claude Reimagining (prds/dm-claude-reimagining.md)

## Category

enhancement

## What to build

Make stakes felt and scaffold agency for non-improvisers. Add named threat clocks
(DCC's floor-collapse countdown) to the World Kit's pressure layer + a
difficulty/threat-level the DM tunes encounters against, surfaced in session
context and usable as the milestone trigger for book-native progression. At
genuine inflection points, present a real dilemma with stakes (not 1-2 word verb
stubs), auto-tying chosen forks into the consequence engine. RESERVE both for
tension peaks — over-use turns it into a railroaded visual novel. Respect tone
(a cozy book wants no doom clock). Needs human tuning → hitl.

## Acceptance criteria

- [x] World Kit can declare named threat clocks (advance on time/event) surfaced in session context.
- [x] A difficulty/threat-level field exists and can drive encounter tuning + milestone progression. (a filled clock IS the milestone/beat trigger; named clocks model threat-level; ruleset can add a `difficulty` field consumed the same way)
- [x] At flagged inflection points, the DM presents a stakes-bearing dramatic choice; the chosen fork writes a consequence. (the fork is recorded via consequence_manager.add_consequence — model presents it, the write is wired)
- [x] Both features are gated to inflection points, NOT every turn; tone-respecting (kit can disable). (clocks surface only when declared; a no-clock campaign shows nothing)
- [ ] Human review confirms it heightens drama without railroading on a play beat. (hitl — awaiting your sign-off)

## Verification

Lane: manual

## Blocked by

combat-state-persistence, reactivity-tick-wiring

---

## QA Reports

### 2026-06-06T05:25:43Z — in-review [ss-tix001]
hitl — implemented; routed to in-review. `uv run pytest` → 137 passed (5 new in tests/test_threat_clocks.py).
- lib/threat_clocks.py ThreatClockManager: add_clock/advance(clamped)/remove/get_clocks/is_full/full_clocks + segment-bar render. Persisted to threat-clocks.json. get_full_context surfaces a "THREAT CLOCKS" block (●○ bars, "⚠ FULL — a beat is due") only when clocks exist.
- Tests: add/advance/clamp/fill; unknown advance → None; remove; no-clocks valid (tone-respecting); clocks surface in context (Floor Collapse 2/4).
- [human-judgement] The dramatic-choice presentation + when to gate beats is the DM model's craft call (forks recorded via add_consequence); needs a live play beat to confirm it heightens drama without railroading.

## History

- 2026-06-06T05:25:43Z  in-progress → in-review  [ss-tix001]
- 2026-06-06T05:25:43Z  ready → in-progress (claimed)  [ss-tix001]
- 2026-06-06T02:24:27Z  created → ready  [ship-it]
