---
slug: world-reconciler-agent
title: ".claude/agents/world-reconciler.md critic + agreement + crosslink"
category: enhancement
kind: afk
priority: p1
lane: manual
parentPrd: authored-world-grounding
blockedBy: [world-author-agent, world-kit-author-agent]
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

The anti-drift pass. Subagent that runs after fan-out, before consolidate. Reads
seed + skeleton + all `authored/*.json` + `canon/*.md` + `ruleset.json`. Performs
three checks and emits a patch report (`reconcile-report.json` or applied edits
to the authored files):

1. **Genericness critic** — flag any content that could appear in any generic
   fantasy world (no world-specific noun, no genre bend). Kick back / rewrite to
   the seed's distinct commitments.
2. **Kit↔flavor agreement** — verify `ruleset.json` actually encodes the magic /
   tech the lore describes (e.g. lore says blood-priced curses but kit still has
   Vancian slots → flag). The world must PLAY distinct, not just READ distinct.
3. **Graph cross-link** — connect faction/geography/npc graphs across axes:
   NPCs → factions, faction edges → geography, dangling references resolved.

Frontmatter + body like the other agents.

## Acceptance criteria

- [ ] `.claude/agents/world-reconciler.md` exists with valid frontmatter
- [ ] Body specifies the three checks (genericness, kit↔flavor, cross-link) with concrete kick-back criteria
- [ ] Emits a machine-readable report (or applies edits) the orchestration can act on
- [ ] Cross-link rules connect NPCs↔factions↔geography across separate `authored/*.json`
- [ ] Genericness criterion is concrete enough to catch a generic NPC/location (manual judgement note)

## Verification

Lane: manual

Human judgement: run against a deliberately-generic authored set and a distinct
one; confirm the critic flags the generic and passes the distinct, and that
kit↔flavor disagreement is caught. Log as human-judgement note.

## Blocked by

world-author-agent, world-kit-author-agent

---

## QA Reports

## History

- 2026-06-06T19:54:09Z  created → ready  [ship-it]
