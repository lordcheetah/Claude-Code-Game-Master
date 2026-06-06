---
slug: world-author-agent
title: ".claude/agents/world-author.md parameterized axis author"
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: authored-world-grounding
blockedBy: [world-author-consolidator]
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

ONE parameterized specialist author subagent, invoked once per axis (adaptive).
Frontmatter (`name: world-author`, `tools: Bash, Read, Write`, model, color) +
markdown body, in the style of `extractor-*.md` / `world-builder.md`.

The agent receives (via its launch prompt): the `world-seed.json`, the approved
skeleton (`world-bible.json`), its axis name + bend, depth (`deep` | `stub`), and
output paths. It writes ONLY two files — never mutates root campaign files (this
is what keeps the parallel fan-out race-free):

- `canon/<axis>.md` — authored prose canon for this axis (the corpus body that
  later gets embedded). Deep axes get rich prose; stubs get a short seed.
- `authored/<axis>.json` — structured contributions in the consolidator contract:
  `{locations:{...}, npcs:{...}, facts:{<category>:[...]}, bible:{factions:
  {nodes,edges}, geography:{nodes,edges}, timeline:[...], signature_systems:[...],
  voice:{...}, themes:[...]}}`. Only the keys this axis owns.

Body must instruct: stay coherent with the skeleton (it is canon); produce
named, world-specific nouns (anti-generic); ALWAYS write both files (empty-but-
valid if nothing for a key); honor deep-vs-stub depth.

## Acceptance criteria

- [ ] `.claude/agents/world-author.md` exists with valid frontmatter (`name: world-author`, tools incl. Write)
- [ ] Body documents the axis/seed/skeleton/depth inputs and the two output paths
- [ ] `authored/<axis>.json` shape matches the consolidator contract exactly (keys + nesting)
- [ ] Explicit "write ONLY canon/<axis>.md and authored/<axis>.json; never edit root files" rule
- [ ] Explicit anti-generic + skeleton-coherence + always-write-both-files instructions
- [ ] deep vs stub depth behavior described

## Verification

Lane: agent

Schema check: a hand-run of the agent against a sample seed+skeleton produces an
`authored/<axis>.json` the consolidator ingests without error. Verify it writes
no root files.

## Blocked by

world-author-consolidator

---

## QA Reports

## History

- 2026-06-06T19:54:09Z  created → ready  [ship-it]
