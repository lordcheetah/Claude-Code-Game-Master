---
slug: canvas-view-writer
title: view.json writer + dm-view.sh scene/clear
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: canvas-view-panel
blockedBy: []
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

The write half of the canvas: a tool the agent uses to push a freeform scene onto the
canvas, persisted to `view.json`. Foundation for every other canvas ticket.

- `lib/view_manager.py` → `class ViewManager(EntityManager)` with:
  - `set_scene(title, body)` → write `view.json` = `{title, body, updated}` via `self.json_ops.save_json`
    (atomic temp+rename, reused — do not reimplement). `updated` from `json_ops.get_timestamp()`.
  - `clear_scene()` → write `{title:"", body:"", updated:ts}` (keep the file so the watcher shows a clean
    placeholder rather than "no view").
  - Body is read from **stdin** in `main()` (avoids multi-line ASCII shell-escaping). Strip C0 control
    chars `< 0x20` EXCEPT `\n`, `\t`, ESC `0x1b` (keep ANSI color, drop CR/BEL). Cap body at ~64 KB.
    Strip a single trailing newline.
  - `main()` argparse subcommands `scene --title <t>` (body via stdin) and `clear`. Follow the house
    `if not args.action: print_help; sys.exit(1)` pattern.
- `tools/dm-view.sh` → wrapper mirroring `tools/dm-location.sh`: source `common.sh`; `scene` and `clear`
  call `require_active_campaign` then dispatch `$PYTHON_CMD "$LIB_DIR/view_manager.py" ...`. `chmod +x`.
  (The `watch`/`render` subcommands are added by later tickets; leave a usage stub or omit for now.)

View file path: `world-state/campaigns/<active>/view.json` (i.e. `self.campaign_dir / "view.json"`).
Already gitignored (`world-state/campaigns/*`, `*.tmp`).

## Acceptance criteria

- [ ] `ViewManager(EntityManager)` writes `view.json = {title, body, updated}` atomically via `json_ops.save_json` (no `.tmp` left behind).
- [ ] `bash tools/dm-view.sh scene "Title"` with a multi-line ASCII body on stdin persists that body verbatim; ANSI ESC sequences survive; CR/BEL and other C0 ctrl chars (except `\n`/`\t`) are stripped; body > ~64 KB is truncated.
- [ ] `bash tools/dm-view.sh clear` empties title/body but keeps the file with a fresh `updated`.
- [ ] `scene`/`clear` fail cleanly via `require_active_campaign` when no campaign is active.
- [ ] pytest covers the round-trip (write → reload → fields intact, ANSI kept, ctrl stripped, cap enforced).

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

<!-- newest first -->

## History

- 2026-06-06T16:06:57Z  created → ready  [ship-it]
