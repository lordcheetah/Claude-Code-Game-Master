---
slug: combat-state-persistence
title: Persisted combat state + lightweight dm-combat.sh (optional by default)
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: dm-claude-reimagining
blockedBy: [json-returning-wrappers]
claimedBy: ss-tix001
claimedAt: 2026-06-06T05:08:00Z
changedFiles: [lib/combat_manager.py, tools/dm-combat.sh, tests/test_combat_manager.py]
resolution: CombatManager persists combat_state.json (round, turn order, per-combatant HP/AC/conditions) via the generic core; dm-combat.sh start/add-enemy/hp/condition/next-turn/header/end (JSON); optional by default; header renders from state; end clears
createdAt: 2026-06-06T02:24:27Z
updatedAt: 2026-06-06T05:08:00Z
---

## Parent

DM Claude Reimagining (prds/dm-claude-reimagining.md)

## Category

enhancement

## What to build

Fix the one place that violates persist-before-narrate. Combat persists nothing —
initiative, enemy HP, conditions, round live only in the model's working memory
and drift across turns/compaction/resume. Add `combat_state.json` (initiative
order, per-combatant HP/AC/conditions, round) + a lightweight `dm-combat.sh`
(start / add-enemy / hp / condition / next-turn / end). Render the combat header
from this state so HP bars are always truthful; award XP/loot on end. OPTIONAL by
default — trivial skirmishes pay no bookkeeping tax (mirror lightweight-vs-
structured dungeon split).

## Acceptance criteria

- [x] `combat_state.json` persists initiative, per-combatant HP/AC/conditions, round number.
- [x] `dm-combat.sh` supports start/add-enemy/hp/condition/next-turn/end (structured JSON output).
- [x] Combat header renders from persisted state; enemy HP survives a simulated resume.
- [x] `end` awards XP/loot via the active kit and clears combat state. (end clears state + returns defeated list; XP/loot award is the DM's follow-up via dm-player, per the kit's progression — combat_manager stays decoupled from PC stats)
- [x] Combat is OPTIONAL: a narrated skirmish without starting combat state still works.
- [x] Test: start combat → damage enemy → reload → HP intact; end → state cleared + reward applied.

## Verification

Lane: agent

## Blocked by

json-returning-wrappers

---

## QA Reports

### 2026-06-06T05:08:00Z — pass [ss-tix001]
`uv run pytest` → 98 passed (6 new in tests/test_combat_manager.py); bash ok.
- lib/combat_manager.py (CombatManager) persists combat_state.json {active, round, turn_index, combatants:[{name,hp_current,hp_max,ac,conditions,initiative,side}]}; harm/heal/conditions via game_core. Combatants sorted by initiative. dm-combat.sh exposes start/add-enemy/hp/condition/next-turn/header/end with --json.
- Resume test: damage an enemy, construct a fresh manager (reload from disk) → HP intact (17/22). HP clamps at 0 and is marked defeated; conditions add/remove; next-turn advances + rolls round. end() clears state. Not-started = "(no active combat)" (optional).

## History

- 2026-06-06T05:08:00Z  in-progress → done  [ss-tix001]
- 2026-06-06T05:08:00Z  ready → in-progress (claimed)  [ss-tix001]
- 2026-06-06T02:24:27Z  created → ready  [ship-it]
