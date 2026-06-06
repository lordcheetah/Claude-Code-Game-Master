---
slug: authored-world-grounding
title: Authored-World Grounding Pipeline for /new-game
status: active
version: 1
supersedes: null
createdAt: 2026-06-06T19:54:09Z
updatedAt: 2026-06-06T19:54:09Z
---

## Problem Statement

`/new-game` is single-agent, sequential, and generic-by-construction. Verified by
reading the command + a freshly-built campaign (`on-the-sails-of-madness`): it
asks 4 canned menus (tone / magic / setting), then makes a starting location, 6
NPCs in fixed roles, a 3-tier plot, and 3 consequences. It **bypasses every
grounding system the import path already uses**:

- never writes `world-bible.json` (the voice/themes/factions/geography/timeline/
  signature-systems spine — `world_bible.py` exists, but its docstring says only
  "the import pipeline auto-drafts it").
- never writes `ruleset.json` (the World Kit — `world_kit.py`). Combat/magic
  therefore fall back to D&D 5e via the `gm-*` skills.
- never generates a source corpus. `current-document.txt` is absent, so the
  Loremaster (`loremaster.py`) is dead on arrival and RAG (`rag/`) has nothing to
  retrieve.

Result: original worlds drift to generic D&D. A Conan-flavored world reads
atmospheric but plays like d20-fantasy — no blood-priced magic, no curses, no
distinct kit, no retrievable lore to keep narration grounded.

## Solution

Import reads a book to *extract* bible + corpus. Original creation should
*author* a book's worth of canon, then run it through the **same** downstream
pipeline. Write authored canon → `gm-extract.sh prepare` → grounding lights up
identically (it writes `current-document.txt` + `chunks/` + vectors).

A new creation workflow: **seed → skeleton → fan-out → reconcile → ground.**

- **Seed** — a genre-aware questionnaire produces `world-seed.json` including an
  *adaptive axis list* (tech world gets infrastructure; Conan gets curses +
  frontier instead).
- **Skeleton** — the main GM agent authors the full bible spine in ONE pass while
  the seed is fresh (coherence anchor every fan-out agent carries). Written
  `confirmed:false`; user approves before fan-out.
- **Fan-out** — parallel specialist author subagents, one per axis (deep on
  load-bearing axes, stub elsewhere), each writing prose canon + structured
  contributions to its OWN files (race-free). One agent owns the kit.
- **Reconcile** — genericness critic (kicks back anything that could appear in any
  generic fantasy) + kit↔flavor agreement check (does the kit actually encode the
  distinctive magic, or did the world read distinct but play 5e?) + graph
  cross-link.
- **Ground** — serial consolidate of contributions into root files + bible;
  compile canon → embed via `prepare`; confirm bible; `world-check`.

## User Stories

1. As a player creating an original world, I want a genre-aware interview that
   commits to what makes my world distinct, so it does not collapse to generic
   D&D.
2. As a player, I want to approve the world's creative skeleton before the system
   fleshes it out, so I own its identity.
3. As the GM agent at play time, I want a `world-bible.json`, a `ruleset.json`,
   and a retrievable source corpus for an original world — exactly as I get for an
   imported book — so narration and mechanics stay grounded.
4. As a player, I want load-bearing axes built deep and the rest stubbed, so
   creation is rich where it matters and the world-tick can deepen the rest
   lazily.

## Implementation Decisions

Reuses (already done, do not rebuild): `world_bible.py` (validate +
`confirmed:false` draft-gate), `world_kit.py` (`ruleset.json` shape),
`gm-extract.sh prepare` (text → `current-document.txt` + chunks + vectors),
`loremaster.py` + `rag/`, `world-check`, and the import "parallel author → serial
normalize" race-free pattern.

New components:

- **`lib/world_author.py`** — serial consolidator. `consolidate <campaign>`:
  merge every `authored/<axis>.json` into root `locations.json` / `npcs.json` /
  `facts.json` (runtime shapes) + `world-bible.json` graphs (dedupe nodes/edges by
  name). `compile-canon <campaign>`: concatenate skeleton prose + `canon/*.md` →
  a single text file ready for `prepare`. Runs single-threaded after fan-out (no
  concurrent writes to shared files).
- **`tools/gm-worldgen.sh`** — thin wrapper: `consolidate`, `compile-canon`.
  Embed reuses `gm-extract.sh prepare`; validation reuses `world_bible.py` /
  `world-check`.
- **`world-seed.json`** — new per-campaign artifact: premise, tone, magic, genre
  bend, and the adaptive axis list (`{axis, load_bearing: deep|stub, bend}`).
- **`.claude/agents/world-author.md`** — ONE parameterized axis author, invoked
  once per axis (adaptive). Carries seed + skeleton + axis brief + depth. Writes
  ONLY `canon/<axis>.md` (prose) + `authored/<axis>.json` (structured: locations,
  npcs, facts, bible fragments). Never mutates root files.
- **`.claude/agents/world-kit-author.md`** — owns `ruleset.json`. Translates genre
  + magic commitments → kit mechanics (stat schema, progression model, resolution,
  active agents, signature systems). Decision #4: one agent owns the kit.
- **`.claude/agents/world-reconciler.md`** — genericness critic + kit↔flavor
  agreement + graph cross-link. Emits a report + patch instructions applied during
  consolidation.
- **Rewrite `.claude/commands/new-game.md`** — orchestrate seed → skeleton (+
  approval gate) → parallel fan-out (`world-author` ×N + `world-kit-author`) →
  reconcile → ground → confirm → `world-check` → summary → `/create-character`.

`authored/<axis>.json` contract (consumed by consolidator):
`{ "locations": {Name:{position,connections,description}}, "npcs":
{Name:{description,attitude,tags}}, "facts": {plot_*|<key>:[...]}, "bible":
{factions:{nodes,edges}, geography:{nodes,edges}, timeline:[...],
signature_systems:[...], voice:{...}, themes:[...]} }`. Consolidator stamps
timestamps + required runtime fields.

## Testing Decisions

- **agent lane** (most): consolidator produces valid runtime-shape JSON
  (locations/npcs/facts pass existing validators); merged `world-bible.json`
  passes `world_bible.py validate`; `ruleset.json` loads via `world_kit.py`;
  `compile-canon` + `prepare` yields a non-empty `current-document.txt` and a
  RAG index that returns hits; end-to-end `/new-game` dry-run leaves a campaign
  that passes `world-check`. Prior art: import's `gm-extract.sh validate`,
  `world-check`, `world_bible.py validate`.
- **manual lane**: the genericness critic actually catches generic content (judge
  a Conan-seed world reads distinct, plays distinct); the skeleton-approval UX;
  questionnaire feel. Human-judgement notes.

## Out of Scope

- No new RAG/embedding engine — reuse `rag/` as-is.
- No changes to the import path or `gm-*` play-time skills.
- No full gazetteer up front — stubbed axes deepen via the existing
  between-session world-tick.
- No multi-character / multi-campaign creation changes.

## Further Notes

- Race-safety is load-bearing: authors write own files; consolidation is serial.
  Mirrors the proven import `prepare → parallel extract → normalize` flow.
- The skeleton-in-one-pass (decision #3) is the coherence anchor; without it,
  parallel authors drift apart.
- Adaptive axes (decision #1) are the anti-generic lever; a fixed axis set
  reintroduces drift.
