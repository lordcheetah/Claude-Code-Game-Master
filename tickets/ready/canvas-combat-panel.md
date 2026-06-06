---
slug: canvas-combat-panel
title: Auto COMBAT panel from combat_state.json
category: enhancement
kind: afk
priority: p2
lane: agent
parentPrd: canvas-view-panel
blockedBy: [canvas-render-compose]
claimedBy: null
claimedAt: null
changedFiles: []
resolution: null
createdAt: 2026-06-06T16:06:57Z
updatedAt: 2026-06-06T16:06:57Z
---

## Parent

Canvas view panel (prds/canvas-view-panel.md)

## Category

enhancement

## What to build

Add an auto-derived COMBAT panel to `compose_frame`, fed by the already-shipped
`combat_state.json` (from `combat-state-persistence` / `lib/combat_manager.py`). This is the
truthful, drift-free enemy tracker that the original plan said was impossible — now there's a
real data source.

- Extend `load_state` to also read `combat_state.json` (try/except → `{}`).
- When `combat_state.get("combatants")` is non-empty (active combat), render a COMBAT panel:
  - Title row: `COMBAT · Round <round>`.
  - Combatants sorted by `initiative` (desc); each: `name`, `<hp_bar> hp_current/hp_max`, a side tag
    (e.g. player/ally vs enemy via `side`), and conditions if any. Reuse the ported `hp_bar`.
  - Mark the active turn (`turn_index`) with a caret/`▸`.
- When no active combat (`{}` or empty `combatants`), the COMBAT panel is hidden — layout falls back to
  the PARTY/HERE arrangement from canvas-render-compose.
- Watcher signature (canvas-watch-loop) must include `combat_state.json` mtime — coordinate / note it.

Schema (existing): `{active, round, turn_index, combatants:[{name,hp_current,hp_max,ac,conditions,initiative,side}]}`.

## Acceptance criteria

- [ ] With an active `combat_state.json`, `render` shows a COMBAT panel: `Round N`, combatants ordered by initiative, HP bars, side tag, conditions, active-turn marker.
- [ ] With no active combat (file absent or empty `combatants`), no COMBAT panel renders and the base PARTY/HERE layout is unchanged.
- [ ] HP bar colors match the HUD thresholds; `hp_max == 0` does not crash.
- [ ] pytest seeds a `combat_state.json` fixture and asserts the COMBAT panel content + the hidden case.

## Verification

Lane: agent

## Blocked by

canvas-render-compose

---

## QA Reports

<!-- newest first -->

## History

- 2026-06-06T16:06:57Z  created → ready  [ship-it]
