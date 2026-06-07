---
slug: canvas-render-compose
title: compose_frame + PARTY/HERE panels + render subcommand
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: canvas-view-panel
blockedBy: [canvas-view-writer]
claimedBy: ss-cnvs01
claimedAt: 2026-06-07T21:05:48Z
changedFiles: [lib/view_manager.py, tools/gm-view.sh, tests/test_view_manager.py]
resolution: "Add read/render path: compose_frame draws a framed header+SCENE+PARTY|HERE+footer panel (live-derived panels, HUD palette/HP bars, side-by-side ≥72c else stacked) via gm-view.sh render"
createdAt: 2026-06-06T16:06:57Z
updatedAt: 2026-06-06T16:06:57Z
---

## Parent

Canvas view panel (prds/canvas-view-panel.md)

## Category

enhancement

## What to build

The render half: turn campaign state + `view.json` into a framed panel string, exposed via a
one-shot `render` subcommand (stdout, no alt-screen — testable + the seam the watcher reuses).

- Read path that does NOT use `EntityManager` (it raises with no campaign):
  - `resolve_campaign_dir()` → `CampaignManager("world-state").get_active_campaign_dir()` (may be `None`).
  - `load_state(dir)` → safe-load `view.json`, `character.json`, `npcs.json`, `locations.json`,
    `campaign-overview.json`; each read wrapped try/except → `{}` (degrade, never crash).
- Helpers: `visible_len(s)` strips ANSI (`\x1b\[[0-9;]*m`) for padding math; `clip_visible(s, n)` clips on
  visible chars while preserving escape sequences and appending RESET; `framed_line`, `hrule`,
  `top/bottom_border(label)` using box-drawing chars + the HUD 256-color palette; `hp_bar(cur,max)` ported
  verbatim from `tools/dm-statusline.sh` (green ≥50%, amber ≥25%, red <25%, `█`/`░`).
- `compose_frame(state, cols, rows)` sized to `shutil.get_terminal_size((80,24))` (clamp cols `[40,200]`):
  - **Header:** `◆ <title>` left, `<current_date> · <time_of_day>` right.
  - **SCENE:** `view.json.body` split on `\n`; per line `clip_visible` to inner width with `…`; vertical
    overflow → last row `… (+N lines)`; empty body → dim placeholder hint.
  - **PARTY:** player from `character.json` (`⚔ name Lv# race class <hp_bar> cur/max` + dim conditions) +
    every `is_party_member` NPC from `character_sheet` (`• name Lv# <hp_bar> cur/max`).
  - **HERE:** current location (overview `player_position.current_location`, fallback `character.json`),
    then `→ <to> (<path>)` per `connections`; `[]` → dim `(no known exits)`. Omit the long `position` paragraph.
  - PARTY|HERE side-by-side at `cols ≥ 72`, else stacked. **Footer:** `updated <relative>` from `view.json.updated`.
  - No active campaign → single centered placeholder `⚔ DM — no active campaign (/new-game or /import)`.
- Add `render` subcommand to `view_manager.py` `main()` + `tools/dm-view.sh render` (NO `require_active_campaign`).

## Acceptance criteria

- [x] `bash tools/gm-view.sh render` prints a framed panel: header (title + date/time), SCENE region, PARTY, HERE, footer.
- [x] PARTY shows the player + every `is_party_member` NPC with correct HP bars (color thresholds match the HUD); missing `character_sheet` → name only, no bar.
- [x] HERE shows the current location + its connections; empty connections → `(no known exits)`.
- [x] Color in the scene body is preserved; over-wide lines clip with `…` (escapes intact, RESET appended); over-tall body shows `… (+N lines)`.
- [x] Edge cases handled without crashing: `conditions: null`, `hp.max == 0` (no ZeroDivision), missing location, no active campaign (placeholder).
- [x] pytest on the DCC fixture asserts compose output for the populated case + the no-campaign placeholder.

## Verification

Lane: agent

## Blocked by

canvas-view-writer

---

## QA Reports

<!-- newest first -->

### 2026-06-07T21:15:00Z — pass [ss-cnvs01]
agent lane — pytest tests/test_view_manager.py 16/16 pass; full suite 262 passed
(1 deselected: test_identity_onboarding::test_build_dispatches_and_saves — a
PRE-EXISTING failure unrelated to this ticket, from the character-schema refactor
in efd1cb7; it expects nested `identity.name` while the live schema is flat. Flagged
to the user, not in scope here).

- render: `gm-view.sh render` prints header (◆ title + date·time-of-day), SCENE,
  PARTY|HERE, footer — verified live against the DCC campaign and via pytest.
- PARTY: player + every is_party_member NPC (Carl/Donut/Mongo) with HP bars;
  non-party NPC (Mordecai) excluded; missing character_sheet → `• name` only.
- HP bar thresholds ported from gm-statusline.sh: ≥50 green, ≥25 amber, else red.
- HERE: current location + `→ to (path)` connections; empty → `(no known exits)`.
- Scene fidelity: ANSI color round-trips; over-wide lines clip (escapes intact,
  RESET appended, exact width); over-tall body → `… (+N lines)`.
- Edge cases (no crash): `conditions: null`, `hp.max == 0` (no ZeroDivision),
  missing location, no-campaign centered placeholder.
- Frame integrity: every emitted line is exactly `cols` visible columns wide
  (asserted at 80 and 60); side-by-side ≥72 cols, stacked below.
- [naming deviation, continued] `gm-view.sh render` (project `gm-*` convention),
  not `dm-view.sh`. Read path uses CampaignManager directly (not EntityManager),
  so the no-campaign placeholder renders instead of raising.

## History

- 2026-06-06T16:06:57Z  created → ready  [ship-it]
- 2026-06-07T21:05:48Z  claimed  [ss-cnvs01]
- 2026-06-07T21:15:00Z  done: pass → done  [ss-cnvs01]
