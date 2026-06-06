---
slug: worldgen-tool-wrapper
title: "tools/gm-worldgen.sh wrapper"
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: authored-world-grounding
blockedBy: [world-author-consolidator]
claimedBy: ss-w7k2m9
claimedAt: 2026-06-06T20:13:00Z
changedFiles: [tools/gm-worldgen.sh]
resolution: "gm-worldgen.sh wrapper: consolidate + compile-canon dispatch to world_author.py, --json passthrough, usage"
createdAt: 2026-06-06T19:54:09Z
updatedAt: 2026-06-06T20:15:31Z
---

## Parent

Authored-World Grounding Pipeline (prds/authored-world-grounding.md)

## Category

enhancement

## What to build

Thin bash wrapper `tools/gm-worldgen.sh` over `lib/world_author.py`, matching the
existing `tools/gm-*.sh` idiom (source `common.sh`, `$PYTHON_CMD`, `$LIB_DIR`,
`case "$1"` dispatch, usage block, `--json` passthrough).

Subcommands:
- `consolidate [campaign]` → `world_author.py consolidate`
- `compile-canon [campaign]` → `world_author.py compile-canon`

Embed + validation are NOT re-wrapped — `gm-extract.sh prepare` and
`world-check` / `world_bible.py` already cover those; the orchestration command
calls them directly.

## Acceptance criteria

- [x] `tools/gm-worldgen.sh` exists, executable, sources `common.sh`
- [x] `consolidate` and `compile-canon` subcommands dispatch to `world_author.py`
- [x] `--json` flag passes through
- [x] No-arg / unknown-arg prints usage with the two subcommands
- [x] Follows the same shape as a peer wrapper (e.g. `gm-extract.sh`)

## Verification

Lane: agent

`bash tools/gm-worldgen.sh` prints usage; `consolidate`/`compile-canon` invoke the
lib against the fixture campaign and return success + `--json`.

## Blocked by

world-author-consolidator

---

## QA Reports

### 2026-06-06T20:15:31Z — pass [ss-w7k2m9]
`bash -n` clean; sources common.sh; executable. No-arg → usage; `bogus` → usage + exit 1.
`consolidate --json` → `{ok:true, data:{files:0,...}}`; `compile-canon --json` → `{ok:true, data:{path,bytes,sections}}` — both dispatch to world_author.py with --json passthrough. Mirrors gm-extract.sh shape (set -e, source common.sh, case dispatch, show_usage). Cleaned stray empty authored-canon.md written during smoke.

## History

- 2026-06-06T20:15:31Z  ready → done  [ss-w7k2m9]
- 2026-06-06T20:13:00Z  claimed  [ss-w7k2m9]
- 2026-06-06T19:54:09Z  created → ready  [ship-it]
