---
slug: structured-trigger-schema
title: Structured consequence trigger schema (+ DCC migration)
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: dm-claude-reimagining
blockedBy: [test-harness-scaffold]
claimedBy: ss-tix001
claimedAt: 2026-06-06T04:25:55Z
changedFiles: [lib/consequence_manager.py, tools/dm-consequence.sh, tests/fixtures/world-state/campaigns/dungeon-crawler-carl/consequences.json, tests/test_structured_triggers.py, docs/schema-reference.md]
resolution: consequences gain optional trigger_type/match/expiry (additive); dm-consequence.sh forwards the flags; DCC fixture migrated to exercise all four types + a legacy entry; schema documented
createdAt: 2026-06-06T02:24:27Z
updatedAt: 2026-06-06T04:25:55Z
---

## Parent

DM Claude Reimagining (prds/dm-claude-reimagining.md)

## Category

enhancement

## What to build

Replace free-text-only triggers with a small structured schema that the engine
can evaluate, additively (old free-text triggers still parse). Each consequence
gains an optional structured trigger: `trigger_type` (on_location | on_npc |
on_time | on_event) + `match` value + optional `expiry`. Keep the existing
`consequence`/`trigger`/`created` fields. Light-migrate the DCC consequences so
the fixture exercises both structured and free-text forms.

## Acceptance criteria

- [x] Consequence schema additively supports `trigger_type`, `match`, `expiry` (all optional; absent = legacy free-text).
- [x] `dm-consequence.sh add` accepts structured trigger args while preserving the free-text path.
- [x] DCC consequences migrated: at least one of each `trigger_type` present in the fixture.
- [x] Round-trip load test: existing DCC `consequences.json` loads unchanged under the new schema (defaults applied).
- [x] Schema documented in `docs/schema-reference.md`.

## Verification

Lane: agent

## Blocked by

test-harness-scaffold

---

## QA Reports

### 2026-06-06T04:25:55Z — pass [ss-tix001]
`uv run pytest` → 33 passed (4 new in tests/test_structured_triggers.py); fixture JSON valid; `bash -n tools/dm-consequence.sh` ok.
- consequence_manager: add_consequence gains optional trigger_type/match/expiry (TRIGGER_TYPES = on_location/on_npc/on_time/on_event); fields written only when provided. CLI `add` gains `--trigger-type/--match/--expiry`. dm-consequence.sh forwards extra flags via `add "$DESC" "$TRIG" "$@"`.
- DCC fixture migrated: on_npc (Squeeks→"friendly"), on_time (Nightstalker→"night"), on_location (Sheol→"Floor 4"), on_event (Mongo frenzy→"combat", expiry "Floor 4"); Mongo-training left legacy free-text.
- Tests: structured add round-trips all fields; legacy add omits them; fixture exercises all 4 types + a legacy; existing consequences still load with consequence/trigger intact.
- Schema documented in docs/schema-reference.md. Sets up reactivity-engine (next) to fire/expire on these.

## History

- 2026-06-06T04:25:55Z  in-progress → done  [ss-tix001]
- 2026-06-06T04:25:55Z  ready → in-progress (claimed)  [ss-tix001]
- 2026-06-06T02:24:27Z  created → ready  [ship-it]
