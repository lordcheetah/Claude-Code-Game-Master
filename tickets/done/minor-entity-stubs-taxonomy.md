---
slug: minor-entity-stubs-taxonomy
title: Stub referenced minor entities; fix plot taxonomy
category: bug
kind: afk
priority: p2
lane: agent
parentPrd: import-pipeline-hardening
blockedBy: [import-integrity-gate]
claimedBy: ss-7q3w9z
claimedAt: 2026-06-06T17:26:00Z
changedFiles: [lib/minor_stubs.py, tools/dm-extract.sh, .claude/commands/import.md, tests/test_minor_stubs.py]
resolution: dm-extract.sh stub-npcs creates minimal NPC stubs for plot-referenced NPCs dropped by the cap (rewriting refs to canonical keys) and normalizes off-enum plot types to side; full pipeline now passes the strict integrity gate (0 unresolved)
createdAt: 2026-06-06T16:37:48Z
updatedAt: 2026-06-06T17:27:15Z
---

## Parent

prds/import-pipeline-hardening.md

## Category

bug

## What to build

A few referenced antagonists have no backing entity (Ji-Hoon assassin, Blister/Wrath
Ghouls, ram-headed Club Vanquisher cleric, Rusalka Station 84); one plot uses
off-taxonomy `type: optional`. For named threats referenced by plots/NPCs but absent
from npcs.json: create minimal monster/NPC stubs (or convert to generic monster
references the monster-manual agent can stat on demand). Fix plot taxonomy: reclassify
"Build the Royal Court" from `optional` to `side` (or add `optional` to the documented
enum) so all plot types are valid.

## Acceptance criteria

- [x] Named threats referenced but missing get a minimal stub or a generic monster reference.
- [x] No plot uses an off-enum `type`; either reclassified or the enum is extended + documented.
- [x] Runs within / after the integrity gate so new stubs satisfy reference resolution.
- [x] Overlap with enhancer relevance gate noted, not duplicated.

## Verification

Lane: agent

## Blocked by

import-integrity-gate

---

## QA Reports

### 2026-06-06T17:27:15Z — pass [ss-7q3w9z]
5 unit tests in tests/test_minor_stubs.py pass: unresolved plot.npc stubbed; resolvable ref
canonicalized not stubbed; `optional` kept (valid documented enum); off-enum type→side; run
makes all plot.npcs resolve. FULL-CHAIN smoke on real-data copy (cap→normalize-connections→
reconcile→stub-npcs→integrity STRICT): exit 0, 0 unresolved — every cross-reference resolves.
Live apply stubbed 14 plot-referenced NPCs the cap dropped (Bautista, Chaco the Bard, Ji-Hoon,
Blister Ghouls, etc.). [note] `optional` is already in the documented enum (main/side/personal/
world/optional), so no DCC reclassification was needed; the validator is a generic safety net.
Stub overlap with enhancer relevance gate noted (stubs carry no RAG context; not duplicated).

## History

- 2026-06-06T16:37:48Z  created → ready  [ship-it]
- 2026-06-06T17:26:00Z  claimed  [ss-7q3w9z]
- 2026-06-06T17:27:15Z  done  [ss-7q3w9z]
