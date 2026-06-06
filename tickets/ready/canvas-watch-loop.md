---
slug: canvas-watch-loop
title: run_watch polling loop + alt-screen + dm-view.sh watch
category: enhancement
kind: afk
priority: p1
lane: manual
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

The live pane: a long-running watcher that redraws `compose_frame` whenever state changes. This is
the first daemon-style process in the repo (all other tools are one-shot) — it's a user-launched
process, not an agent-called tool.

- `run_watch()` in `view_manager.py`:
  - Enter alternate screen `\033[?1049h`, hide cursor `\033[?25l`. `try/finally` + SIGINT/SIGTERM
    handler → restore (`\033[?25h`, `\033[?1049l`) so Ctrl+C returns the pane's normal scrollback clean.
  - Loop every **0.25 s**: compute a signature = (active campaign name, `get_terminal_size()`, and
    `st_mtime_ns` of each relevant file — `view.json`, `character.json`, `npcs.json`, `locations.json`,
    `campaign-overview.json`, **and `combat_state.json`** — sentinel if absent). Redraw only on change.
  - Redraw = cursor home `\033[H` + frame + clear-to-end `\033[J` (no full clear → no flicker).
  - Polling, not `watchdog`/inotify (zero new deps; atomic temp+rename writes make a single read coherent).
  - Too-small terminal → degraded compact panel.
- `watch` subcommand in `main()` + `tools/dm-view.sh watch` → `exec $PYTHON_CMD "$LIB_DIR/view_manager.py" watch`
  (exec so signals reach Python). **No `require_active_campaign`** — the watcher must start before a
  campaign exists, show the placeholder, and auto-populate when one activates.

## Acceptance criteria

- [ ] `bash tools/dm-view.sh watch` takes over the pane with the framed panel and redraws within ~250 ms when a watched file changes (e.g. `bash tools/dm-player.sh hp Tandy -55` flips the bar amber/red).
- [ ] Pushing a new scene while watching updates the SCENE region and the footer "updated … ago".
- [ ] Alternate-screen buffer is used; Ctrl+C restores the cursor and the pane's previous scrollback.
- [ ] Pane resize re-lays-out (PARTY|HERE two-column ↔ stacked).
- [ ] Started with no active campaign → placeholder; activating a campaign auto-populates without restart.
- [ ] Signature includes `combat_state.json` so the COMBAT panel appears/updates live during combat.

## Verification

Lane: manual

Interactive/visual: human runs the watcher in a VS Code split pane and eyeballs live redraw, alt-screen
enter/exit, Ctrl+C restore, and resize. Cannot be asserted in code.

## Blocked by

canvas-render-compose

---

## QA Reports

<!-- newest first -->

## History

- 2026-06-06T16:06:57Z  created → ready  [ship-it]
