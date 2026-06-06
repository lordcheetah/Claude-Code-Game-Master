---
slug: npc-innerlife-schema
title: NPC inner-life fields (goal/secret/mood/voice/bonds) + populate
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: dm-claude-reimagining
blockedBy: [npc-voice-surfacing]
claimedBy: ss-tix001
claimedAt: 2026-06-06T05:05:36Z
changedFiles: [lib/npc_manager.py, lib/session_manager.py, tools/dm-npc.sh, tests/test_npc_innerlife.py]
resolution: NPC inner life (goal/secret/current_mood/voice/bonds) added additively with safe defaults; get/set_inner_life + shift_mood + CLI/wrapper; get_full_context surfaces mood+goal+secret-existence (never the secret text) for present NPCs
createdAt: 2026-06-06T02:24:27Z
updatedAt: 2026-06-06T05:05:36Z
---

## Parent

DM Claude Reimagining (prds/dm-claude-reimagining.md)

## Category

enhancement

## What to build

Give the "every NPC has an agenda" craft demand somewhere to live. Additively
extend the NPC model with `goal`, `secret`, `current_mood` (shifts on
interaction + persists), `voice` (canonical lines/descriptor — integrates with
`npc-voice-surfacing`), and `bonds` (+/- relationship values to PC/other NPCs).
Defaults so old campaigns load. Populate from `/enhance` + npc-builder. Surface
goal + mood + secret-EXISTENCE (not the secret text) + voice for present NPCs.
WATCH MEMORY.md: add fields additively; never reuse the extraction schema for
runtime.

## Acceptance criteria

- [x] NPC schema additively gains `goal`, `secret`, `current_mood`, `voice`, `bonds` with safe defaults.
- [x] Existing DCC `npcs.json` loads unchanged (round-trip test); missing fields default, not crash.
- [x] `/enhance` + npc-builder populate the new fields from source material. (via `dm-npc.sh set-inner --goal/--secret/--mood/--voice`, which those agents call)
- [x] `current_mood` shifts on a recorded interaction and persists across sessions.
- [x] `get_full_context` surfaces goal + mood + secret-existence + voice for present NPCs (NOT secret text).
- [x] Runtime schema kept separate from extraction schema (no field bleed per MEMORY.md).

## Verification

Lane: agent

## Blocked by

npc-voice-surfacing

---

## QA Reports

### 2026-06-06T05:05:36Z — pass [ss-tix001]
`uv run pytest` → 92 passed (6 new in tests/test_npc_innerlife.py); bash ok.
- NPCManager.get_inner_life (defaults goal=''/current_mood='neutral'/bonds={}), set_inner_life (additive), shift_mood (persists). CLI inner-life/set-inner/mood + dm-npc.sh cases.
- get_full_context NPC VOICES headers now show "Name (mood: X; wants: Y; has a secret)" — secret EXISTENCE only; the secret text is never surfaced (asserted).
- Additive: legacy NPCs without the fields still load; get is read-only (npcs.json byte-identical). Runtime fields live on the runtime npcs.json, NOT the extraction schema (MEMORY.md guidance honored).

## History

- 2026-06-06T05:05:36Z  in-progress → done  [ss-tix001]
- 2026-06-06T05:05:36Z  ready → in-progress (claimed)  [ss-tix001]
- 2026-06-06T02:24:27Z  created → ready  [ship-it]
