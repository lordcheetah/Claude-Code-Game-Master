---
name: gm-dungeon
description: Dungeon exploration — lightweight (narrative, default) vs structured (per-room JSON) modes, exit/obstacle handling, and ASCII map symbols. Load when the party enters a cave, ruin, or underground complex.
---

# Dungeon Exploration

| Mode | Best for |
|------|----------|
| **Lightweight** (default) | Fast, narrative; one master location entry with `internal_layout` + `areas_visited` |
| **Structured** | Tactical/revisited 3+ times; separate location per room with a `dungeon` field + `exits` + `state` |

## Lightweight flow
Enter → describe entrance + visible exits → explore (draw a map only when tactically useful, not every room) → combat by zone → on exit update master notes if significant.

## Structured flow
Validate exit (exists? locked/secret?) → handle obstacle (pick/force/key; find secret via Perception) → set destination discovered/visited → `gm-session.sh move "[Dungeon - Room]"` → describe (2-4 sentences) + list exits + creatures.

## ASCII map symbols
`@` current · `+` door · `#` locked door · `△` stairs up · `▽` stairs down · `~` secret (found) · `▓` fog of war.
