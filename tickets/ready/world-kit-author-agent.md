---
slug: world-kit-author-agent
title: ".claude/agents/world-kit-author.md owns ruleset.json"
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: authored-world-grounding
blockedBy: []
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

Specialist subagent that owns `ruleset.json` (the World Kit) for an original
world — decision #4, one agent owns the kit. Frontmatter + body like the other
agents.

Receives seed + skeleton (esp. magic/cosmology commitments + genre bend). Emits a
valid `ruleset.json` in the `world_kit.py` shape: `name`, `stat_schema`
(`attributes`, `vitals`), `progression` (`model`: milestone | xp-threshold |
resource-axis, + params), `resolution` (`model`), `active_agents`, and
`signature_systems` (the per-world rules meat). Mechanics must DERIVE from the
world, not default to 5e — e.g. blood-priced magic → casting costs HP/corruption,
no Vancian slots; a tech world → its own axes/resource.

Writes `ruleset.json` to the campaign root (single owner → no race with the axis
authors, which never touch it).

## Acceptance criteria

- [ ] `.claude/agents/world-kit-author.md` exists with valid frontmatter
- [ ] Emitted `ruleset.json` loads via `uv run python lib/world_kit.py` without error
- [ ] Body instructs deriving stat_schema/progression/resolution from seed+skeleton, NOT copying 5e defaults
- [ ] `signature_systems` encodes the world's distinctive mechanics (named, specific)
- [ ] `active_agents` chosen to fit the world (e.g. dnd5eapi agents only for a 5e-like kit)
- [ ] Writes only `ruleset.json` (does not touch axis-author files)

## Verification

Lane: agent

Run against a Conan-style seed; assert `ruleset.json` loads via `world_kit.py`
and its `progression`/`signature_systems` are not the generic 5e defaults.

## Blocked by

None.

---

## QA Reports

## History

- 2026-06-06T19:54:09Z  created → ready  [ship-it]
