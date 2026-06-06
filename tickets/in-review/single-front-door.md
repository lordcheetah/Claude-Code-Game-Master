---
slug: single-front-door
title: Collapse the entry maze into one front door (/dm canonical)
category: enhancement
kind: afk
priority: p2
lane: manual
parentPrd: dm-claude-reimagining
blockedBy: []
claimedBy: ss-tix001
claimedAt: 2026-06-06T04:18:10Z
changedFiles: [.claude/commands/setup.md, CLAUDE.md, .claude/commands/import.md]
resolution: null
createdAt: 2026-06-06T02:24:27Z
updatedAt: 2026-06-06T04:18:10Z
---

## Parent

DM Claude Reimagining (prds/dm-claude-reimagining.md)

## Category

enhancement

## What to build

The "IMPORT/SELECT YOUR ADVENTURE" menu is re-implemented in `setup.md`,
`import.md`, and `dm.md` STEP 0. Make `/dm` the single canonical entry; fold the
duplicated menu logic into one place the others reference. README, CLAUDE.md
first-run, and the welcome screen all point to `/dm`. A confused player at the
threshold should see exactly one obvious door.

## Acceptance criteria

- [x] One canonical entry/menu definition; `setup.md`/`import.md`/`dm.md` reference it instead of re-implementing.
- [x] `/dm` documented as THE entry point in README + CLAUDE.md first-run.
- [x] No contradictory entry instructions remain across the command docs.
- [ ] Manual walkthrough: fresh-ish state lands the player at one clear next step. (manual-lane — awaiting your sign-off in in-review)

## Verification

Lane: manual

## Blocked by

None.

---

## QA Reports

### 2026-06-06T04:18:10Z — in-review [ss-tix001]
Implemented; manual-lane, so routed to in-review for human sign-off rather than auto-done.
- `/dm` STEP 0 confirmed as the complete canonical front door (lists saved campaigns + New Adventure → Create World/`/new-game`, Import Document/`/import`, One-Shot).
- setup.md: removed its duplicated Welcome Screen + Routing + Returning-Players menus; now hands off to `/dm` after install (`✅ DM CLAUDE IS READY → Run /dm`).
- CLAUDE.md first-run: Step 2 (no campaigns) now routes to `/dm` instead of a separate welcome menu; Step 4 routes to `/dm` as the canonical entry.
- import.md: added a "Done → Play with /dm" handoff; its file-picker (import-specific) is left intact.
- README already centers `/dm` ("Run /dm and let the agent guide you", "Run /dm to begin") — no change needed.
- [human-judgement] Remaining: walk a fresh-ish state end-to-end and confirm one obvious next step. Code-doc consolidation is done; only the experiential check is pending.

## History

- 2026-06-06T04:18:10Z  in-progress → in-review  [ss-tix001]
- 2026-06-06T04:18:10Z  ready → in-progress (claimed)  [ss-tix001]
- 2026-06-06T02:24:27Z  created → ready  [ship-it]
