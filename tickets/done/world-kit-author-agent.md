---
slug: world-kit-author-agent
title: ".claude/agents/world-kit-author.md owns ruleset.json"
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: authored-world-grounding
blockedBy: []
claimedBy: ss-w7k2m9
claimedAt: 2026-06-06T20:10:42Z
changedFiles: [.claude/agents/world-kit-author.md]
resolution: "kit-author agent: derives stat_schema/progression/signature_systems from seed+skeleton into ruleset.json, never 5e default"
createdAt: 2026-06-06T19:54:09Z
updatedAt: 2026-06-06T20:11:30Z
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

- [x] `.claude/agents/world-kit-author.md` exists with valid frontmatter
- [x] Emitted `ruleset.json` loads via `uv run python lib/world_kit.py` without error
- [x] Body instructs deriving stat_schema/progression/resolution from seed+skeleton, NOT copying 5e defaults
- [x] `signature_systems` encodes the world's distinctive mechanics (named, specific)
- [x] `active_agents` chosen to fit the world (e.g. dnd5eapi agents only for a 5e-like kit)
- [x] Writes only `ruleset.json` (does not touch axis-author files)

## Verification

Lane: agent

Run against a Conan-style seed; assert `ruleset.json` loads via `world_kit.py`
and its `progression`/`signature_systems` are not the generic 5e defaults.

## Blocked by

None.

---

## QA Reports

### 2026-06-06T20:11:30Z — pass [ss-w7k2m9]
Authored `.claude/agents/world-kit-author.md`. Verified a sample kit built to its spec (blood-priced sorcery: attrs `str/agi/wits/nerve`, vitals `hp/corruption`, signature_systems encoding HP+corruption cost, book-first active_agents):
- loads via `WorldKit(world_state_dir=tmp)`; name/stat_schema/progression_model reflect the sample.
- `name != DEFAULT_RULESET["name"]`, attributes non-5e, `spell-caster` excluded from active_agents.
- `signature_systems` present; `make_progression` builds + drives via game_core (level advances).
Agent body covers: derive-don't-default, 3 progression models w/ supplied params, named signature systems, dnd5eapi-only-for-5e agent selection, write-only-ruleset.json rule + self-verify command.

## History

- 2026-06-06T20:11:30Z  ready → done  [ss-w7k2m9]
- 2026-06-06T20:10:42Z  claimed  [ss-w7k2m9]
- 2026-06-06T19:54:09Z  created → ready  [ship-it]
