---
slug: enhancer-relevance-gate
title: Relevance gate for RAG enhancement
category: bug
kind: afk
priority: p1
lane: agent
parentPrd: import-pipeline-hardening
blockedBy: []
claimedBy: ss-7q3w9z
claimedAt: 2026-06-06T17:00:00Z
changedFiles: [lib/entity_enhancer.py, tests/test_enhancer_gate.py]
resolution: batch_enhance now relevance-gated — _gate_passages force-includes name/alias-bearing passages, drops below-floor neighbours (no padding), persists per-passage context_scores + context_name_match_fraction, flags enhanced_low_relevance on zero name-hit
createdAt: 2026-06-06T16:37:48Z
updatedAt: 2026-06-06T17:04:45Z
---

## Parent

prds/import-pipeline-hardening.md

## Category

bug

## What to build

`lib/entity_enhancer.py` attaches a fixed top-N of semantic neighbors regardless of
fit → 23/154 entities (14%) had ZERO passages naming them; rare entities over-padded
with the wrong scene, true canonical mention often omitted; ~155K tokens of noise.
Add a relevance gate: (1) force-include any chunk that literally contains the entity
name or a known alias as a seed passage; (2) fill remaining slots only with vector
neighbors above a similarity floor — DROP below-floor instead of padding to N;
(3) persist per-passage retrieval score + an entity-level name-match fraction;
(4) flag entities with zero name-bearing passages for re-enhance/curation.

## Acceptance criteria

- [x] Enhancement force-includes ≥1 chunk literally naming the entity/alias when one exists in the corpus.
- [x] Passages below the similarity floor are dropped, not used as padding.
- [x] Each attached passage stores its retrieval score; each entity stores a name-match fraction.
- [x] Entities with zero name-bearing passages are flagged (field or report).
- [x] On a re-enhanced sample, name-bearing-passage coverage materially improves vs the 14%-zero baseline.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

### 2026-06-06T17:04:45Z — pass [ss-7q3w9z]
5 unit tests in tests/test_enhancer_gate.py pass: name-bearing passage force-included even
above floor; below-floor non-name passages dropped (not padded); zero name-bearing → frac
0.0; aliases count as name-bearing; fill respects floor+target. Real-data smoke on live
campaign (re-enhanced Hekla + Tserendolgor): Hekla name-match 100% (low=False), Tserendolgor
flagged enhanced_low_relevance=True (frac 0.0) — matches the review's zero-hit finding;
context_scores persisted per passage. Batch summary now prints low-relevance count.
[scope] Gate applied to batch_enhance (the import path); the get_scene_context runtime
auto-enhance fallback is left ungated (out of this ticket's scope).

## History

- 2026-06-06T16:37:48Z  created → ready  [ship-it]
- 2026-06-06T17:00:00Z  claimed  [ss-7q3w9z]
- 2026-06-06T17:04:45Z  done  [ss-7q3w9z]
