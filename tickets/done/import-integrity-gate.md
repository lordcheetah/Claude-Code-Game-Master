---
slug: import-integrity-gate
title: Post-extraction reconciliation + fail-on-unresolved gate
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: import-pipeline-hardening
blockedBy: [alias-runtime-resolver]
claimedBy: ss-7q3w9z
claimedAt: 2026-06-06T16:57:00Z
changedFiles: [lib/integrity_gate.py, tools/dm-extract.sh, .claude/commands/import.md, tests/test_integrity_gate.py]
resolution: dm-extract.sh integrity canonicalizes plot/npc/location cross-refs to real keys via the alias resolver (records variants as aliases, e.g. Donut←Princess Donut); strict by default → exits 1 on unresolved; reuses entity_aliases
createdAt: 2026-06-06T16:37:48Z
updatedAt: 2026-06-06T16:58:51Z
---

## Parent

prds/import-pipeline-hardening.md

## Category

enhancement

## What to build

Add a post-extraction integrity pass (new `dm-extract.sh` subcommand or step in the
normalize flow) that, after cap + before play: collects every cross-reference
(plot.npcs, plot.locations, npc.location_tags, location.connections.to) and
canonicalizes each to a real entity key using the shared alias normalizer. If a ref
matches an entity via alias, rewrite it to the canonical key OR record the variant
in that entity's `aliases`. Specifically set Donut's canonical key + alias so all
21 "Princess Donut" plot refs resolve. The gate FAILS the import (non-zero exit +
clear report) if any ref is still unresolved after alias matching and after the
missing-location reconcile.

## Acceptance criteria

- [x] New integrity step runs in the import flow after cap-extraction-30.
- [x] Every plot/npc/location cross-reference resolves to a canonical key or is recorded as an alias.
- [x] Donut entity carries canonical key + "Princess Donut" alias; all plot refs to her resolve.
- [x] Unresolved refs cause the gate to fail with a report listing each (file, entity, ref).
- [x] Reuses the shared normalizer from alias-runtime-resolver (no duplicate logic).
- [x] import.md documents the gate as a required step.

## Verification

Lane: agent

## Blocked by

alias-runtime-resolver

---

## QA Reports

### 2026-06-06T16:58:51Z — pass [ss-7q3w9z]
6 unit tests in tests/test_integrity_gate.py pass: "Princess Donut" plot ref rewritten to
"Donut" + variant added to aliases; connection.to + location_tags canonicalized;
unresolved ref reported; strict gate raises SystemExit(1) on unresolved; --no-strict
returns report; clean refs pass strict + persist. Smoke on capped real-data copy:
53 refs rewritten (Donut aliases=["Princess Donut"]), 167 unresolved correctly flagged
(missing-location refs — handed to missing-location-reconcile before the strict fail).
Reuses entity_aliases.resolve_entity_name (no duplicate logic).

## History

- 2026-06-06T16:37:48Z  created → ready  [ship-it]
- 2026-06-06T16:57:00Z  claimed  [ss-7q3w9z]
- 2026-06-06T16:58:51Z  done  [ss-7q3w9z]
