---
slug: world-kit-schema
title: World Kit — ruleset.json + campaign-scoped rules Skill loader
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: dm-claude-reimagining
blockedBy: [generic-core]
claimedBy: ss-tix001
claimedAt: 2026-06-06T04:58:44Z
changedFiles: [lib/world_kit.py, tests/test_world_kit.py, tests/fixtures/world-state/campaigns/dungeon-crawler-carl/ruleset.json, tests/fixtures/world-state/campaigns/dungeon-crawler-carl/rules.md, world-state/campaigns/dungeon-crawler-carl/ruleset.json, world-state/campaigns/dungeon-crawler-carl/rules.md, docs/schema-reference.md]
resolution: WorldKit loads per-campaign ruleset.json (stat schema/progression/resolution/agents/rules_doc) and drives play through game_core; shipped the DCC kit (resource-axis viewers, no 5e XP) + rules.md; campaign_rules preserved; schema documented
createdAt: 2026-06-06T02:24:27Z
updatedAt: 2026-06-06T04:58:44Z
---

## Parent

DM Claude Reimagining (prds/dm-claude-reimagining.md)

## Category

enhancement

## What to build

The per-book ruleset layer on top of the generic core. Define `ruleset.json`
(stat schema, progression model, resolution model, active specialist agents) and
a campaign-scoped rules **Skill** holding that world's mechanics/prose, loaded on
demand. `campaign_rules` stays for world-flavor systems (loot boxes, viewers).
Ship the DCC ruleset as the first real kit (resource-axis: viewers + floor
descent), proving the core + kit split end-to-end. PROTECT the `campaign_rules`
engine.

## Acceptance criteria

- [x] `ruleset.json` schema defined + documented (stat schema, progression model, resolution model, active agents).
- [x] A campaign's rules Skill loads on demand and drives play through the generic core. (rules_doc -> campaign rules.md, loaded on demand; full CLAUDE.md-as-Skill split is the claudemd-* tickets)
- [x] DCC ships as a working kit (resource-axis progression) without a 5e XP track.
- [x] `campaign_rules` (loot boxes, audience, interview systems) preserved and consumed by the kit.
- [x] Test: DCC kit resolves a check + advances progression via its declared model, not 5e leveling.

## Verification

Lane: agent

## Blocked by

generic-core

---

## QA Reports

### 2026-06-06T04:58:44Z — pass [ss-tix001]
`uv run pytest` → 79 passed (5 new in tests/test_world_kit.py); live `lib/world_kit.py info` returns the DCC kit.
- WorldKit reads ruleset.json (defaults to a milestone generic kit if absent); builds the progression via game_core.make_progression; resolve() delegates to game_core.resolve_check.
- DCC kit shipped (fixture + live world-state): resource-axis on `viewers` (tiers 1M/100M/1B), d20-vs-dc, agents monster-manual/loot-dropper/gear-master, rules_doc=rules.md.
- Tests: loads DCC ruleset; resolves through core; progression is resource-axis (advancing `xp` does nothing — proves it's NOT 5e-leveled); campaign_rules (loot_box/audience) preserved; rules.md loads on demand.
- ruleset.json schema documented in docs/schema-reference.md. Note: "rules Skill" is realized as the campaign rules_doc loaded on demand; the global CLAUDE.md→Skills split is claudemd-extract-tables/lean-core.

## History

- 2026-06-06T04:58:44Z  in-progress → done  [ss-tix001]
- 2026-06-06T04:58:44Z  ready → in-progress (claimed)  [ss-tix001]
- 2026-06-06T02:24:27Z  created → ready  [ship-it]
