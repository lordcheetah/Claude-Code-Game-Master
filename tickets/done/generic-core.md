---
slug: generic-core
title: Thin generic resolution core (d20-vs-DC + harm/conditions + progression)
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: dm-claude-reimagining
blockedBy: [test-harness-scaffold]
claimedBy: ss-tix001
claimedAt: 2026-06-06T04:56:09Z
changedFiles: [lib/game_core.py, tests/test_game_core.py]
resolution: new system-agnostic lib/game_core.py — resolve_check/opposed_check (d20-vs-DC via dice.py), apply_harm/heal, add/remove_condition, and three interchangeable progression models (milestone/xp-levels/resource-axis with SUPPLIED thresholds); zero 5e symbols
createdAt: 2026-06-06T02:24:27Z
updatedAt: 2026-06-06T04:56:09Z
---

## Parent

DM Claude Reimagining (prds/dm-claude-reimagining.md)

## Category

enhancement

## What to build

The system-agnostic core every world runs on, with NO D&D 5e assumptions. A thin
core providing: the d20-vs-DC resolution mechanic (reuse `dice.py` + the DC
ladder), a generic contest/opposed-check primitive, abstract HP/harm + conditions
primitives, and three configurable progression frameworks — `milestone`
(default), `resource-axis`, `xp-levels` — selected/configured by a kit. Stat
names, combat feel, and progression specifics stay OUT of core (they're bespoke
per book). PROTECT `dice.py` as the deterministic RNG.

## Acceptance criteria

- [x] A `core` module exposes: resolve_check(modifier, dc), opposed_check(a, b), apply_harm/heal (abstract HP), add/remove condition.
- [x] Three progression strategies implemented behind one interface: milestone, resource-axis, xp-levels; none hardcoded as the only path.
- [x] Zero D&D-5e-specific symbols in core (no six-ability requirement, no level-20 cap, no spell slots).
- [x] `dice.py` reused unchanged as the RNG; advantage/disadvantage still honored.
- [x] Unit tests cover each progression framework + resolution/contest/harm primitives.

## Verification

Lane: agent

## Blocked by

test-harness-scaffold

---

## QA Reports

### 2026-06-06T04:56:09Z — pass [ss-tix001]
`uv run pytest` → 74 passed (10 new in tests/test_game_core.py).
- resolve_check(modifier, dc, advantage): d20-vs-DC via dice.py ('1d20'/'2d20kh1'/'2d20kl1'), returns die/total/success/margin/critical (nat20=hit, nat1=miss). opposed_check for contests. apply_harm/heal clamp; add/remove_condition idempotent on a list.
- Progression interface with MilestoneProgression, XpLevelProgression (thresholds SUPPLIED, no 5e level-20 cap), ResourceAxisProgression (resource+tiers SUPPLIED, e.g. DCC viewers); make_progression factory defaults to milestone.
- Adversarial: a test greps the core source for banned 5e tokens (spell slot, strength, level 20, proficiency) → none present. Crit classification verified over 300 seeded rolls.

## History

- 2026-06-06T04:56:09Z  in-progress → done  [ss-tix001]
- 2026-06-06T04:56:09Z  ready → in-progress (claimed)  [ss-tix001]
- 2026-06-06T02:24:27Z  created → ready  [ship-it]
