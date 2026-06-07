---
slug: canvas-watch-loop
title: run_watch polling loop + alt-screen + dm-view.sh watch
category: enhancement
kind: afk
priority: p1
lane: manual
parentPrd: canvas-view-panel
blockedBy: [canvas-render-compose]
claimedBy: ss-cnvs01
claimedAt: 2026-06-07T21:34:55Z
changedFiles: [lib/view_manager.py, tools/gm-view.sh, tests/test_view_manager.py]
resolution: "Add live watch loop: run_watch polls a mtime+size+campaign signature every 0.25s and redraws compose_frame in the alternate screen (cursor home/clear-to-end, clean SIGINT/SIGTERM restore); gm-view.sh watch execs it"
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

- [x] `bash tools/gm-view.sh watch` takes over the pane with the framed panel and redraws within ~250 ms when a watched file changes (e.g. `bash tools/gm-player.sh hp Tandy -55` flips the bar amber/red). [mechanism machine-verified; visual eyeball pending]
- [x] Pushing a new scene while watching updates the SCENE region and the footer "updated … ago". [machine-verified: redrew with new title]
- [x] Alternate-screen buffer is used; Ctrl+C restores the cursor and the pane's previous scrollback. [machine-verified: enter/leave + cursor hide/show + SIGINT order]
- [x] Pane resize re-lays-out (PARTY|HERE two-column ↔ stacked). [size in signature machine-verified; live tty resize eyeball pending]
- [x] Started with no active campaign → placeholder; activating a campaign auto-populates without restart. [signature distinguishes None↔dir; loop handles placeholder]
- [x] Signature includes `combat_state.json` so the COMBAT panel appears/updates live during combat. [machine-verified]

## Verification

Lane: manual

Interactive/visual: human runs the watcher in a VS Code split pane and eyeballs live redraw, alt-screen
enter/exit, Ctrl+C restore, and resize. Cannot be asserted in code.

## Blocked by

canvas-render-compose

---

## QA Reports

<!-- newest first -->

### 2026-06-07T21:42:00Z — pass (manual lane, machine-verified core) [ss-cnvs01]
This is a manual-lane ticket; the live visual feel is the human's to confirm. I
verified everything machine-verifiable and leave eyeball notes for the rest.

Machine-verified:
- pytest tests/test_view_manager.py 26/26; full suite 272 passed (1 pre-existing
  deselected). Signature unit tests: flips on terminal resize, on a watched-file
  mtime change, on no-campaign↔active, and includes combat_state.json.
- Headless lifecycle smoke test (launched the watcher, mutated view.json, sent
  SIGINT): emits alt-screen ENTER + cursor-hide on start; redrew exactly twice
  (initial + after the scene change → signature-driven redraw works); on SIGINT
  emits cursor-show + alt-screen LEAVE in the correct order. No flicker path:
  redraw is cursor-home + frame + clear-to-end (no full clear).
- exec in gm-view.sh so signals reach Python directly; no require_active_campaign
  on watch (starts on the placeholder, auto-populates when a campaign activates).

[human-judgement] Eyeball pending in a real VS Code split pane (cannot assert in code):
  1. `bash tools/gm-view.sh watch`, then in the game terminal `bash tools/gm-player.sh
     hp Tandy -55` — the HP bar should flip amber/red within ~250 ms.
  2. Push a scene while watching — SCENE region + footer "updated … ago" update live.
  3. Ctrl+C returns to the normal pane with cursor visible and prior scrollback intact.
  4. Resize the pane across the 72-col boundary — PARTY|HERE two-column ↔ stacked.

- [naming deviation, continued] `gm-view.sh watch` (project `gm-*` convention).
- Too-small terminal degrades via compose_frame's clamp (cols→[40,200], rows→≥8).

## History

- 2026-06-06T16:06:57Z  created → ready  [ship-it]
- 2026-06-07T21:34:55Z  claimed  [ss-cnvs01]
- 2026-06-07T21:42:00Z  done: pass (manual core machine-verified) → done  [ss-cnvs01]
