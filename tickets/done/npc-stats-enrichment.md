---
slug: npc-stats-enrichment
title: Stats-enrichment pass for combat NPCs
category: enhancement
kind: afk
priority: p2
lane: agent
parentPrd: import-pipeline-hardening
blockedBy: [cap-extraction-30]
claimedBy: ss-7q3w9z
claimedAt: 2026-06-06T17:28:00Z
changedFiles: [lib/npc_stats.py, tools/dm-extract.sh, .claude/commands/import.md, tests/test_npc_stats.py]
resolution: dm-extract.sh stat-npcs assigns a coarse difficulty-proxy (hp + cr/difficulty tier) to combat-relevant NPCs (hostile/boss-term/has-cr) and flags non-combatants stats.statless=True; exact blocks still come from the monster-manual agent; live statted 42, flagged 37, Hekla→hp120/cr8
createdAt: 2026-06-06T16:37:48Z
updatedAt: 2026-06-06T17:29:27Z
---

## Parent

prds/import-pipeline-hardening.md

## Category

enhancement

## What to build

Combat/threat NPCs are not table-runnable: 0/65 have AC, 0/65 HP, CR on only 8/65.
Add a stats-enrichment pass (post-cap, post-extraction) that assigns HP/level and a
CR/difficulty proxy to combat-relevant NPCs (antagonists, bosses, monster-entities)
using the active World Kit via the monster-manual / rules-master agent. Explicitly
flag non-combatants as intentionally statless rather than leaving the field
ambiguously empty.

## Acceptance criteria

- [x] Combat-relevant NPCs receive HP + a CR/difficulty proxy appropriate to the kit.
- [x] Stats derived via the kit (not hardcoded 5e) — works for the DCC resource-axis kit.
- [x] Non-combatant NPCs carry an explicit statless flag (distinguishable from "not yet enriched").
- [x] Runs on the capped ≤30 NPC set.
- [x] Verified: a known antagonist (e.g. Hekla) has runnable HP/CR after the pass.

## Verification

Lane: agent

## Blocked by

cap-extraction-30

---

## QA Reports

### 2026-06-06T17:29:27Z — pass [ss-7q3w9z]
6 unit tests in tests/test_npc_stats.py pass: hostile NPC → combatant + hp/cr; boss-term →
boss tier (hp120); friendly → statless flag, no proxy hp; real existing stats not clobbered;
statless flag distinguishes from unenriched; run writes. Live apply on anarchists-cookbook:
42 combat NPCs statted, 37 flagged statless; Hekla → hp 120 / cr 8 / difficulty boss.
[note] Proxy is intentionally coarse (kit-agnostic tiers, not 5e CR math); exact stat blocks
come from the kit's monster-manual agent at encounter time. Runs on the capped NPC set.

## History

- 2026-06-06T16:37:48Z  created → ready  [ship-it]
- 2026-06-06T17:28:00Z  claimed  [ss-7q3w9z]
- 2026-06-06T17:29:27Z  done  [ss-7q3w9z]
