---
slug: canvas-agent-integration
title: CLAUDE.md optional view-panel note + launch docs
category: enhancement
kind: afk
priority: p2
lane: manual
parentPrd: canvas-view-panel
blockedBy: [canvas-watch-loop, canvas-combat-panel]
claimedBy: ss-cnvs01
claimedAt: 2026-06-07T21:45:00Z
changedFiles: [CLAUDE.md, README.md, .claude/commands/help.md]
resolution: "Document the canvas: optional view-panel note in lean CLAUDE.md (Output Format), launch UX in README + /help (gm-view.sh watch in a second pane), supersedes the old no-auto-enemy-HP guidance"
createdAt: 2026-06-06T16:06:57Z
updatedAt: 2026-06-06T16:06:57Z
---

## Parent

Canvas view panel (prds/canvas-view-panel.md)

## Category

enhancement

## What to build

Teach the DM (agent) to use the canvas, and document how a player launches it. Keep agent discipline
minimal — auto panels (PARTY/HERE/COMBAT) need nothing; the agent only ever writes the freeform scene.

- Add one optional block to the **lean** `CLAUDE.md`. The old "When to Draw Maps" anchor is gone post
  lean-core — place it near **Output Format**, or push the detail into the `dm-dungeon` / `dm-craft`
  skill and leave a one-line pointer in `CLAUDE.md`. Content:
  > **Optional view panel.** If the player runs the canvas (`bash tools/dm-view.sh watch` in a second
  > pane), push scene art with: `printf '%s' "<ascii/art, color ok>" | bash tools/dm-view.sh scene "Title"`.
  > Use for dungeon maps, combat positioning, key scene art. PARTY/HERE update automatically, and the
  > COMBAT panel auto-tracks enemy HP **when you run `dm-combat`** — so prefer `dm-combat` for fights worth
  > a live tracker; otherwise draw enemy HP into the scene. Never draw HP bars/exits yourself. Clear with
  > `bash tools/dm-view.sh clear`.
- Document the launch UX (README or help): VS Code **split terminal** → `bash tools/dm-view.sh watch`
  (terminal-agnostic; works in Warp / any second tab). Note it starts before a campaign is active.

Supersedes the original plan's "enemy HP is not auto-tracked" guidance — combat-state-persistence +
canvas-combat-panel make it auto when `dm-combat` is used.

## Acceptance criteria

- [x] `CLAUDE.md` gains a concise optional view-panel note (or a one-line pointer to a skill that holds it) consistent with lean-core structure — no bloat, no revival of the removed 5e map section.
- [x] The note states the `scene`/`clear` commands and that PARTY/HERE/COMBAT are auto-derived (COMBAT via `gm-combat`).
- [x] Launch instructions (VS Code split terminal → `gm-view.sh watch`) are documented where a player will find them.

## Verification

Lane: manual

Doc/wording review — human confirms the note fits lean-core tone and the launch steps are accurate.

## Blocked by

canvas-watch-loop, canvas-combat-panel

---

## QA Reports

<!-- newest first -->

### 2026-06-07T21:48:00Z — pass (manual/doc lane) [ss-cnvs01]
Doc-only ticket; verification is wording review (yours to confirm).

- `CLAUDE.md` → one tight bullet under **Output Format**: optional view panel,
  the `scene --title`/`clear` commands, PARTY/HERE auto + COMBAT auto via
  `gm-combat`, "never draw HP bars/exits yourself", and "if no one's watching,
  ignore it". No revival of the removed 5e "When to Draw Maps" section; lean tone.
- `README.md` → new **The Live Canvas** subsection (launch UX: second terminal /
  VS Code split → `gm-view.sh watch`, what the panels show, ~250ms redraw, starts
  pre-campaign, Ctrl+C clean) + a `gm-view.sh` row in the Bash Tools table.
- `.claude/commands/help.md` → `gm-view.sh` in the CLI tool list + a LIVE CANVAS
  block under QUICK START.
- All documented commands verified against the shipped wrapper (`scene --title`,
  `clear`, `render`, `watch`). Supersedes the original "enemy HP is not
  auto-tracked" guidance — now auto when `gm-combat` is used.
- [naming] Ticket text used `dm-view.sh`/`dm-combat`; documented as `gm-*` to
  match the project's actual tool names.

## History

- 2026-06-06T16:06:57Z  created → ready  [ship-it]
- 2026-06-07T21:45:00Z  claimed  [ss-cnvs01]
- 2026-06-07T21:48:00Z  done: pass → done  [ss-cnvs01]
