---
slug: json-wrappers-player
title: --json mode for player_manager (sheet read + hp/xp/gold/inventory write)
category: enhancement
kind: afk
priority: p2
lane: agent
parentPrd: dm-claude-reimagining
blockedBy: [json-returning-wrappers]
claimedBy: ss-tix001
claimedAt: 2026-06-06T04:52:40Z
changedFiles: [lib/player_manager.py, tools/dm-player.sh, tests/test_json_wrappers_player.py]
resolution: player_manager --json envelopes get (read, char sheet) and hp (write, modify result); hp's prints suppressed in json mode; dm-player.sh forwards --json on get/hp
createdAt: 2026-06-06T04:10:42Z
updatedAt: 2026-06-06T04:52:40Z
---

## Parent

DM Claude Reimagining (prds/dm-claude-reimagining.md)

## Category

enhancement

## What to build

Wire the shared `cli_output` envelope into player_manager. Add `--json` for a
representative read (character sheet) and a representative write (`hp`). Returning
structured results lets the loop confirm stat changes without scraping text.

## Acceptance criteria

- [x] A sheet read with `--json` emits the success envelope.
- [x] `hp --json` (a representative write) emits structured before/after + ok/error.
- [x] Human output unchanged without `--json`.
- [x] `dm-player.sh` passes `--json` through.
- [x] Tests assert envelope shape for the read and the write (hermetic, DCC fixture).

## Verification

Lane: agent

## Blocked by

json-returning-wrappers

---

## QA Reports

### 2026-06-06T04:52:40Z — pass [ss-tix001]
`uv run pytest` → 61 passed (2 new). get --json → {"data": {character sheet}} (name=Tandy); hp --json → {"data": {success, ...}} with the method's prints suppressed. dm-player.sh hp/get now shift name/amount and forward "$@". Hermetic CLI subprocess test runs from the fixture's world-state root.

## History

- 2026-06-06T04:52:40Z  in-progress → done  [ss-tix001]
- 2026-06-06T04:52:40Z  ready → in-progress (claimed)  [ss-tix001]
- 2026-06-06T04:10:42Z  created → ready  [ss-tix001]
