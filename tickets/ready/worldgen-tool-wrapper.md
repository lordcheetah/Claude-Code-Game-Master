---
slug: worldgen-tool-wrapper
title: "tools/gm-worldgen.sh wrapper"
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: authored-world-grounding
blockedBy: [world-author-consolidator]
claimedBy: null
claimedAt: null
changedFiles: []
resolution: null
createdAt: 2026-06-06T19:54:09Z
updatedAt: 2026-06-06T19:54:09Z
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

- [ ] `tools/gm-worldgen.sh` exists, executable, sources `common.sh`
- [ ] `consolidate` and `compile-canon` subcommands dispatch to `world_author.py`
- [ ] `--json` flag passes through
- [ ] No-arg / unknown-arg prints usage with the two subcommands
- [ ] Follows the same shape as a peer wrapper (e.g. `gm-extract.sh`)

## Verification

Lane: agent

`bash tools/gm-worldgen.sh` prints usage; `consolidate`/`compile-canon` invoke the
lib against the fixture campaign and return success + `--json`.

## Blocked by

world-author-consolidator

---

## QA Reports

## History

- 2026-06-06T19:54:09Z  created → ready  [ship-it]
