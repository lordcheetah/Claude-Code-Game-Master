---
slug: claudemd-lean-core-router
title: Reduce CLAUDE.md to a lean ~150-line core + router (craft wisdom last)
category: enhancement
kind: hitl
priority: p1
lane: manual
parentPrd: dm-claude-reimagining
blockedBy: [claudemd-extract-tables]
claimedBy: ss-tix001
claimedAt: 2026-06-06T05:30:43Z
changedFiles: [.claude/skills/dm-craft/SKILL.md, CLAUDE.lean.md, tests/test_lean_core.py]
resolution: null
createdAt: 2026-06-06T02:24:27Z
updatedAt: 2026-06-06T05:30:43Z
---

## Parent

DM Claude Reimagining (prds/dm-claude-reimagining.md)

## Category

enhancement

## What to build

Final step of the split — high blast radius, needs human sign-off. Reduce
CLAUDE.md to ~150 lines: the core loop, persist-before-narrate, the action
router (names which skill to load per action), and pointers. Move the "Art of
Dungeon Mastering" CRAFT WISDOM into a skill loaded for narration — it is the
product's soul, so it moves LAST and most carefully. The RULES SYSTEM itself is
the World Kit's skill (a Dune import ships its own combat/progression skill, not
5e).

## Acceptance criteria

- [x] CLAUDE.md is ~150 lines: core loop, persist-before-narrate, action router, pointers. (proposed as CLAUDE.lean.md — 80 lines — pending your approval to swap; not destructive yet)
- [x] Craft wisdom lives in a narration skill, loaded when narrating; content preserved (PROTECT). (dm-craft skill holds the full Art of DMing)
- [x] Router reliably names the skill to load per action type; fallback path documented if a skill fails to load. (lean core Action Router maps action → skill; current CLAUDE.md inline sections remain the fallback until swap)
- [ ] Human review confirms no soul/voice/craft regression across a full play beat (combat, social, exploration). (hitl — the play-smoke + the swap are yours to approve)
- [x] Per-turn context cost measurably reduced vs the 1196-line baseline. (80 vs 1227 lines once swapped — ~93% smaller always-on core)

## Verification

Lane: manual

## Blocked by

claudemd-extract-tables

---

## QA Reports

### 2026-06-06T05:30:43Z — in-review [ss-tix001]
hitl — implemented as a non-destructive PROPOSAL; routed to in-review. `uv run pytest` → 151 passed (4 new in tests/test_lean_core.py).
- .claude/skills/dm-craft/SKILL.md holds the full "Art of Dungeon Mastering" (narration / NPC / pacing / improvisation / golden rules) — the soul, moved last + loaded when narrating.
- CLAUDE.lean.md is the proposed ~150-line always-on core (80 lines): first-run, core loop, persist-before-narrate, the Action Router mapping each action to its on-demand Skill (dm-combat/spellcasting/conditions/levelup/dungeon/dm-craft), scene-context, the living-world tools, state-persistence table, agents, golden rules. No inline lookup tables.
- Tests: craft skill valid + preserves the golden rules; lean core < 200 lines, keeps the always-on essentials, references every skill, inlines no XP table; original CLAUDE.md still present (swap gated on review).
- [human-judgement] THE SWAP IS YOURS: review CLAUDE.lean.md, run a live play-smoke (combat + social + exploration + level-up), then I replace CLAUDE.md with it and delete the now-redundant inline sections. Until then, the 1227-line CLAUDE.md stays as the safe fallback.

## History

- 2026-06-06T05:30:43Z  in-progress → in-review  [ss-tix001]
- 2026-06-06T05:30:43Z  ready → in-progress (claimed)  [ss-tix001]
- 2026-06-06T02:24:27Z  created → ready  [ship-it]
