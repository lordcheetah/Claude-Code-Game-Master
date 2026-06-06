---
slug: connection-key-normalize
title: Normalize location connection targets to real keys
category: bug
kind: afk
priority: p2
lane: agent
parentPrd: import-pipeline-hardening
blockedBy: [alias-runtime-resolver]
claimedBy: ss-7q3w9z
claimedAt: 2026-06-06T17:21:00Z
changedFiles: [lib/connection_normalize.py, tools/dm-extract.sh, .claude/commands/import.md, tests/test_connection_normalize.py]
resolution: dm-extract.sh normalize-connections canonicalizes connection.to via the alias resolver and moves routing rule-phrases (ending in / any line / via / upper level) into notes; precise rule detection keeps real places like "Transfer Station 89"; runs before reconcile
createdAt: 2026-06-06T16:37:48Z
updatedAt: 2026-06-06T17:23:00Z
---

## Parent

prds/import-pipeline-hardening.md

## Category

bug

## What to build

~18 of ~65 location connection edges don't resolve: key-name mismatches ("Station
435 (end of line)" vs "…(End of the Line)", "Desperado Club (Station 131)" vs
"Desperado Club", three Trainyard spellings) and descriptive phrases stored as
targets ("Any line", "Transfer stations ending in 1", "Upper level via central
stairs"). Normalize every `connections.to` to an exact existing location key via the
shared alias normalizer; move pattern/rule statements out of `connections.to` into
`features`/`notes`. Reserve `connections.to` for real location keys only.

## Acceptance criteria

- [x] All `connections.to` values are exact existing location keys after normalization (rule-phrases removed; only genuinely-missing places remain, handed to reconcile).
- [x] Rule/pattern phrases are relocated to features/notes, not left as connection targets.
- [x] Connection-edge resolution rate ≈100% post-pass (resolvable canonicalized; rules→notes; missing→reconcile stubs).
- [x] Reuses the shared normalizer (no duplicate matching logic).

## Verification

Lane: agent

## Blocked by

alias-runtime-resolver

---

## QA Reports

### 2026-06-06T17:23:00Z — pass [ss-7q3w9z]
5 unit tests in tests/test_connection_normalize.py pass: precise rule detection (flags
"Transfer stations ending in 1"/"Any line"/"Upper level via central stairs" but NOT real
"Transfer Station 89"); drifted target canonicalized via resolver; rule-phrase moved to
notes + removed from connections; missing real place left for reconcile; run writes file.
Reuses entity_aliases.resolve_entity_name. Wired before reconcile in import.

## History

- 2026-06-06T16:37:48Z  created → ready  [ship-it]
- 2026-06-06T17:21:00Z  claimed  [ss-7q3w9z]
- 2026-06-06T17:23:00Z  done  [ss-7q3w9z]
