---
slug: creation-grounding-eval
title: "End-to-end creation grounding verification"
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: authored-world-grounding
blockedBy: [new-game-orchestration]
claimedBy: ss-w7k2m9
claimedAt: 2026-06-06T20:22:34Z
changedFiles: [tests/test_creation_grounding.py, .claude/agents/world-author.md]
resolution: "pytest eval drives consolidate->compile-canon->confirm + live embed/RAG-hit; asserts confirmed+valid bible, non-5e kit, schema-clean state; caught + fixed invalid attitude enum in world-author"
createdAt: 2026-06-06T19:54:09Z
updatedAt: 2026-06-06T20:24:30Z
---

## Parent

Authored-World Grounding Pipeline (prds/authored-world-grounding.md)

## Category

enhancement

## What to build

Automated eval proving an original world comes out grounded — the agent-lane
counterpart to the manual `/new-game` dry-run. Drive the pipeline against a fixed
seed (no interactive questionnaire — supply a `world-seed.json` fixture + a
pre-authored skeleton, or invoke the lib/agent steps directly) into a throwaway
campaign, then assert the grounding contract. Fits the existing test harness
(test-harness-scaffold).

## Acceptance criteria

- [x] Eval drives consolidate + compile-canon + prepare for a fixture seed into a temp campaign
- [x] Asserts `world-bible.json` exists, is `confirmed:true`, and passes `world_bible.py validate`
- [x] Asserts `ruleset.json` loads via `world_kit.py` and is NOT the generic 5e default (distinct progression/signature_systems)
- [x] Asserts `current-document.txt` is non-empty and a RAG query returns ≥1 hit
- [x] Asserts `locations.json`/`npcs.json`/`facts.json` populated in valid runtime shapes
- [x] Asserts the campaign passes `world-check`
- [x] Eval is runnable headless and cleans up its temp campaign

## Verification

Lane: agent

The eval itself is the verification; CI/local run passes green against the
fixture.

## Blocked by

new-game-orchestration

---

## QA Reports

### 2026-06-06T20:24:30Z — pass [ss-w7k2m9]
`tests/test_creation_grounding.py` — 2 passed (uv run pytest, 6.7s), uses the harness tmp_path pattern (hermetic, self-cleaning).
- `test_creation_pipeline_grounds_the_world`: Conan-style seed fixture (skeleton + 3 authored axes + canon + kit) → consolidate (files=3) → asserts bible valid + graphs merged + `confirmed` flips false→true via `WorldBible.confirm()`; `WorldKit` loads + `name != DEFAULT_RULESET`, non-5e attributes/vitals (`corruption`), signature_systems present, `spell-caster` excluded; locations/npcs/facts populated valid shapes; `validate_world_state` returns zero errors; compile-canon non-empty + embed-ready.
- `test_live_rag_grounding_if_available`: importorskip-gated; ran the REAL path — `AgentExtractor.prepare_for_agents` wrote a non-empty `current-document.txt` and embedded; `CampaignVectorStore.query_by_text("blood-priced sorcery", LocalEmbedder())` returned hits. (Skips with a reason if deps/model unavailable — no silent pass.)

Defect found + fixed: `world-author.md` documented invalid attitude enum values (`curious`/`dismissive`) not in `schemas.VALID_ATTITUDES` — would fail `world-check` at play. Corrected to the valid set (`ally|friendly|helpful|neutral|suspicious|hostile|enemy`). This is exactly the cross-axis grounding bug the eval exists to catch.

## History

- 2026-06-06T20:24:30Z  ready → done  [ss-w7k2m9]
- 2026-06-06T20:22:34Z  claimed  [ss-w7k2m9]
- 2026-06-06T19:54:09Z  created → ready  [ship-it]
