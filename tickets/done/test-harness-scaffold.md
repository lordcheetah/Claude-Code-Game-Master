---
slug: test-harness-scaffold
title: pytest scaffold + DCC golden fixture + seam characterization snapshots
category: enhancement
kind: afk
priority: p0
lane: agent
parentPrd: dm-claude-reimagining
blockedBy: []
claimedBy: ss-tix001
claimedAt: 2026-06-06T02:40:48Z
changedFiles: [pyproject.toml, tests/conftest.py, tests/test_get_full_context.py, tests/test_check_pending.py, tests/fixtures/world-state, CONTRIBUTING.md]
resolution: pytest scaffold + DCC golden fixture + characterization snapshots of get_full_context and check_pending (8 tests green)
createdAt: 2026-06-06T02:24:27Z
updatedAt: 2026-06-06T02:40:48Z
---

## Parent

DM Claude Reimagining (prds/dm-claude-reimagining.md)

## Category

enhancement

## What to build

The move-zero safety net. A pytest setup runnable via `uv`, the Dungeon Crawler
Carl (DCC) campaign frozen as a read-only golden fixture, and characterization
(snapshot) tests that capture CURRENT behavior of the two highest-risk seams —
`session_manager.get_full_context` and `consequence_manager.check_pending` —
before any later ticket changes them. This is the precondition for the whole
reimagining; every schema/behavior ticket below asserts against it.

## Acceptance criteria

- [x] `uv run pytest` runs and is green; pytest config added to `pyproject.toml` (existing `[tool.*]` blocks present).
- [x] A copy of the DCC campaign is checked in under `tests/fixtures/` (or referenced read-only) so tests never mutate the live campaign.
- [x] Characterization test snapshots the current `get_full_context` output for the DCC fixture and asserts on stable substrings (location, character, pending-consequence text).
- [x] Characterization test snapshots `check_pending` current return shape/content for the DCC fixture.
- [x] Tests are hermetic: no network, no writes to `world-state/`, deterministic (seed any RNG).
- [x] README/CONTRIBUTING note: how to run the suite.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

### 2026-06-06T02:40:48Z — pass [ss-tix001]
`uv run pytest` → 8 passed in 0.03s. Coverage:
- get_full_context (seam #1): asserts active character "Tandy", a "PENDING CONSEQUENCES" section, real consequence text surfaces (Squeeks/Nightstalker/Mongo/Sheol) AND the pre-cleanup "Unknown -> triggers" sentinel is absent (regression guard for the consequence-display bug), and DCC campaign_rules (loot_box/audience/interview) appear.
- check_pending (seam #2): asserts list return, ≥1 active item, real schema (`consequence`/`trigger`/`id`, not `event`/`status`), and a known consequence present.
- Hermetic: `dcc_world` fixture copies tests/fixtures/world-state into tmp_path per test; reads only; no network; deterministic. Live campaign untouched.
- Adversarial value: the "Unknown -> triggers" and `consequence`-field assertions would fail against the pre-cleanup buggy code, not just mirror the impl.

## History

- 2026-06-06T02:40:48Z  in-progress → done  [ss-tix001]
- 2026-06-06T02:40:48Z  ready → in-progress (claimed)  [ss-tix001]
- 2026-06-06T02:24:27Z  created → ready  [ship-it]
