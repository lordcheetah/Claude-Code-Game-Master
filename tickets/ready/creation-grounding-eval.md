---
slug: creation-grounding-eval
title: "End-to-end creation grounding verification"
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: authored-world-grounding
blockedBy: [new-game-orchestration]
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

Automated eval proving an original world comes out grounded — the agent-lane
counterpart to the manual `/new-game` dry-run. Drive the pipeline against a fixed
seed (no interactive questionnaire — supply a `world-seed.json` fixture + a
pre-authored skeleton, or invoke the lib/agent steps directly) into a throwaway
campaign, then assert the grounding contract. Fits the existing test harness
(test-harness-scaffold).

## Acceptance criteria

- [ ] Eval drives consolidate + compile-canon + prepare for a fixture seed into a temp campaign
- [ ] Asserts `world-bible.json` exists, is `confirmed:true`, and passes `world_bible.py validate`
- [ ] Asserts `ruleset.json` loads via `world_kit.py` and is NOT the generic 5e default (distinct progression/signature_systems)
- [ ] Asserts `current-document.txt` is non-empty and a RAG query returns ≥1 hit
- [ ] Asserts `locations.json`/`npcs.json`/`facts.json` populated in valid runtime shapes
- [ ] Asserts the campaign passes `world-check`
- [ ] Eval is runnable headless and cleans up its temp campaign

## Verification

Lane: agent

The eval itself is the verification; CI/local run passes green against the
fixture.

## Blocked by

new-game-orchestration

---

## QA Reports

## History

- 2026-06-06T19:54:09Z  created → ready  [ship-it]
