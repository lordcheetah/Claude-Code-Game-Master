---
slug: world-author-consolidator
title: "lib/world_author.py: serial consolidate + compile-canon"
category: enhancement
kind: afk
priority: p0
lane: agent
parentPrd: authored-world-grounding
blockedBy: []
claimedBy: ss-w7k2m9
claimedAt: 2026-06-06T20:02:24Z
changedFiles: [lib/world_author.py]
resolution: "serial consolidate (authored/*.json -> locations/npcs/facts.json + deduped bible graphs, confirmed preserved) + compile-canon"
createdAt: 2026-06-06T19:54:09Z
updatedAt: 2026-06-06T20:05:25Z
---

## Parent

Authored-World Grounding Pipeline (prds/authored-world-grounding.md)

## Category

enhancement

## What to build

Core race-free engine that turns parallel author outputs into grounded world
state. New module `lib/world_author.py` + CLI `main()` (argparse, `--json` via
`cli_output`), mirroring sibling libs (`world_bible.py`, `agent_extractor.py`).

Two commands, both single-threaded (run AFTER fan-out — no concurrent writers):

- `consolidate <campaign>` — read every `authored/<axis>.json`, merge into root
  files in their runtime shapes:
  - `locations.json`: `{Name:{position, connections:[{to,path}], description,
    discovered}}` — stamp `discovered` (UTC), keep existing entries.
  - `npcs.json`: `{Name:{description, attitude, created, events:[], tags:
    {locations:[],quests:[]}, current_mood?}}` — stamp `created`, default
    `events:[]`/`tags`.
  - `facts.json`: `{<category>:[{fact,timestamp}]}` — append, stamp `timestamp`
    (reuse `note_manager` add_fact semantics or replicate).
  - `world-bible.json`: deep-merge `bible` fragments into the skeleton —
    factions/geography graphs union nodes+edges deduped by node `name` /
    edge `(from,to,type)`; timeline/themes/signature_systems append-dedupe;
    voice merge. Preserve `confirmed` flag.
- `compile-canon <campaign>` — concatenate skeleton prose + all `canon/*.md`
  (stable axis order) into one text artifact (e.g. `authored-canon.md` in the
  campaign dir), ready to hand to `gm-extract.sh prepare`. Return the path.

Use `JsonOperations` (`load_json`/`save_json`) + `CampaignManager`
(`get_active_campaign_dir`). Accept a campaign arg or fall back to active.

## Acceptance criteria

- [x] `lib/world_author.py` exists with `consolidate` + `compile-canon` CLI subcommands and `--json` support
- [x] `consolidate` merges `authored/*.json` into `locations.json`, `npcs.json`, `facts.json` in correct runtime shapes with stamped timestamps + required default fields
- [x] Bible graph merge dedupes nodes by `name` and edges by `(from,to,type)`; appends themes/timeline/signature_systems without dupes; preserves `confirmed`
- [x] Merged `world-bible.json` passes `uv run python lib/world_bible.py validate`
- [x] `compile-canon` writes a non-empty text file from skeleton + `canon/*.md` and prints its path
- [x] Existing campaign files untouched when no `authored/*.json` present (no crash on empty input)
- [x] Idempotent re-run does not duplicate entities or graph nodes/edges

## Verification

Lane: agent

Build a tiny fixture campaign with 2 `authored/*.json` files + a skeleton bible,
run both commands, assert merged shapes + `world_bible.py validate` pass + canon
file non-empty. Re-run to assert idempotency.

## Blocked by

None.

---

## QA Reports

### 2026-06-06T20:05:25Z — pass [ss-w7k2m9]
Adversarial fixture test (`/tmp/test_world_author.py`): 2 authored/*.json + skeleton bible + canon/*.md.
- consolidate: locations=1, npcs=1, facts=1, bible_merged — all runtime shapes correct, `discovered`/`created`/`timestamp` stamped, `events:[]`/`tags` defaulted.
- bible merge: themes deduped (`ash and memory`,`debt`), geography+factions nodes unioned, `confirmed:false` preserved; `validate_bible` passes.
- compile-canon: non-empty, contains bible preamble (`Cinderworld`) + canon prose.
- idempotent re-run: 0 added, no dup nodes/themes.
- empty campaign (no authored/): files=0, no crash, canon file still written.
CLI help/`--json` flag OK.

## History

- 2026-06-06T20:05:25Z  ready → done  [ss-w7k2m9]
- 2026-06-06T20:02:24Z  claimed  [ss-w7k2m9]
- 2026-06-06T19:54:09Z  created → ready  [ship-it]
