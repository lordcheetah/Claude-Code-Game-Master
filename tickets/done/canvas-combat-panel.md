---
slug: canvas-combat-panel
title: Auto COMBAT panel from combat_state.json
category: enhancement
kind: afk
priority: p2
lane: agent
parentPrd: canvas-view-panel
blockedBy: [canvas-render-compose]
claimedBy: ss-cnvs01
claimedAt: 2026-06-07T21:31:55Z
changedFiles: [lib/view_manager.py, tests/test_view_manager.py]
resolution: "Add auto COMBAT panel: when combat_state.json is active, compose_frame renders Round N + combatants by initiative with HP bars, side tags, conditions, ▸ active-turn marker; hidden when no combat"
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

- [x] With an active `combat_state.json`, `render` shows a COMBAT panel: `Round N`, combatants ordered by initiative, HP bars, side tag, conditions, active-turn marker.
- [x] With no active combat (file absent or empty `combatants`), no COMBAT panel renders and the base PARTY/HERE layout is unchanged.
- [x] HP bar colors match the HUD thresholds; `hp_max == 0` does not crash.
- [x] pytest seeds a `combat_state.json` fixture and asserts the COMBAT panel content + the hidden case.

## Verification

Lane: agent

## Blocked by

canvas-render-compose

---

## QA Reports

<!-- newest first -->

### 2026-06-07T21:38:00Z — pass [ss-cnvs01]
agent lane — pytest tests/test_view_manager.py 22/22; full suite 268 passed
(1 deselected: the pre-existing identity-onboarding failure, unrelated).

- COMBAT panel renders above PARTY/HERE when `combat_state.json` has combatants:
  `COMBAT · Round N`, ordered by initiative desc, HP bars (HUD thresholds),
  `[side]` tag (enemy red / ally-player green), conditions, and a ▸ marker on the
  active turn. Verified the marker tracks `turn_index` by object identity (correct
  even after the init-desc re-sort, and with duplicate names/ties).
- Hidden in all no-combat cases: missing key, `{}`, and `{active:false, combatants:[]}`
  — base PARTY/HERE layout unchanged.
- `hp_max == 0` combatant renders `0/0` with an empty bar, no ZeroDivision.
- load_state now also reads `combat_state.json` under key `combat`.
- [fix-forward] Found & fixed a render-compose defect in the same function:
  load_state mangled `campaign-overview` → key `campaign_overview`, but compose
  reads `overview`, so the header date/time-of-day silently never appeared.
  Replaced the blind `-`→`_` mangle with an explicit name→key map; added a
  regression test (`test_overview_key_loads_under_overview`).
- Coordination note for canvas-watch-loop: `combat_state.json` is now in
  `_STATE_FILES`, so the watcher's mtime signature can derive from that map and
  the COMBAT panel will update live.

## History

- 2026-06-06T16:06:57Z  created → ready  [ship-it]
- 2026-06-07T21:31:55Z  claimed  [ss-cnvs01]
- 2026-06-07T21:38:00Z  done: pass → done  [ss-cnvs01]
