---
slug: new-game-orchestration
title: "Rewrite /new-game: seed → skeleton → fan-out → reconcile → ground"
category: enhancement
kind: afk
priority: p0
lane: manual
parentPrd: authored-world-grounding
blockedBy: [world-author-consolidator, worldgen-tool-wrapper, world-author-agent, world-kit-author-agent, world-reconciler-agent]
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

Rewrite `.claude/commands/new-game.md` to orchestrate the full pipeline, plus
define `world-seed.json`. Phases:

- **A. Seed** — genre-aware questionnaire (AskUserQuestion). Beyond tone/magic/
  setting: premise / genre bend. Produce `world-seed.json`: `{premise, tone,
  magic, setting, genre_bend, axes:[{axis, depth:deep|stub, bend}]}`. The axis
  list is ADAPTIVE — derived from genre (tech→infrastructure; sword&sorcery→
  curses+frontier; high-fantasy→lineage+pantheon).
- **B. Skeleton** — main GM agent authors the full bible spine in ONE pass while
  seed is fresh → `world-bible.json` with `confirmed:false`. Present
  `review_summary` to user; gate fan-out on approval (edit-or-accept).
- **C. Fan-out** — launch in parallel (single message, multiple Task calls):
  `world-author` once per axis (passing axis+depth+seed+skeleton+paths) +
  `world-kit-author` once. Mirror import's parallel-Task pattern.
- **D. Reconcile** — `world-reconciler`; apply its patches.
- **E. Ground** — `bash tools/gm-worldgen.sh consolidate`; `compile-canon`;
  `bash tools/gm-extract.sh prepare <canon-file> <campaign>` (embeds → RAG);
  confirm bible (`world_bible.py` confirm); `world-check`.
- **F. Handoff** — summary box → `/create-character`.

Keep the existing ASCII box UX idiom. Preserve the campaign create/switch +
overview + session-log init steps.

## Acceptance criteria

- [ ] `.claude/commands/new-game.md` rewritten through phases A–F
- [ ] Questionnaire produces `world-seed.json` with an ADAPTIVE axis list keyed off genre
- [ ] Skeleton authored in one pass → `world-bible.json` `confirmed:false`, with an explicit user approval gate before fan-out
- [ ] Fan-out launches `world-author` ×N (per axis, deep/stub) + `world-kit-author` as parallel Task calls
- [ ] Reconcile step runs `world-reconciler` and applies patches
- [ ] Ground step: consolidate → compile-canon → `gm-extract.sh prepare` → confirm bible → `world-check`
- [ ] Ends by handing off to `/create-character`
- [ ] Dry run leaves a campaign with `world-bible.json` (confirmed), `ruleset.json`, `current-document.txt`, and populated `locations/npcs/facts.json`

## Verification

Lane: manual

Human dry-run: create an original world; confirm the approval gate, the grounded
artifacts exist, and the world reads + (spot-check) plays distinct. Automated
end-to-end coverage is the `creation-grounding-eval` ticket.

## Blocked by

world-author-consolidator, worldgen-tool-wrapper, world-author-agent, world-kit-author-agent, world-reconciler-agent

---

## QA Reports

## History

- 2026-06-06T19:54:09Z  created → ready  [ship-it]
