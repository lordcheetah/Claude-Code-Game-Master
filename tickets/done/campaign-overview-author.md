---
slug: campaign-overview-author
title: Author campaign-overview + campaign_rules; fix rules_doc pointer
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: import-pipeline-hardening
blockedBy: []
claimedBy: ss-7q3w9z
claimedAt: 2026-06-06T17:09:00Z
changedFiles: [lib/overview_seed.py, .claude/commands/import.md, tests/test_overview_seed.py]
resolution: overview_seed.seed_overview writes book overview fields + campaign_rules; fix_rules_doc nulls a dangling rules_doc; import Step 6.6 authors them; applied to live (6 DCC campaign_rules keys, WorldKit reads them, rules_doc nulled)
createdAt: 2026-06-06T16:37:48Z
updatedAt: 2026-06-06T17:10:36Z
---

## Parent

prds/import-pipeline-hardening.md

## Category

enhancement

## What to build

Import copies/creates ruleset.json (Step 6.5) but leaves campaign-overview.json as
the default scaffold (genre "Fantasy", date "Year 1", no campaign_rules) → signature
book systems live nowhere the DM tooling reads. Also ruleset.json copied from a
sibling kit can carry a dangling `rules_doc: "rules.md"` with no file on disk.
Add a mandatory post-kit authoring step to import: write a real campaign-overview
(campaign_name, genre, tone weights, in-world date) AND a `campaign_rules` block
capturing the book's signature systems (for DCC: loot boxes, viewers economy, train
mechanics, prime-station stairwells). Resolve `rules_doc`: write the file or set null.

## Acceptance criteria

- [x] After import, campaign-overview.json has a book-appropriate name/genre/tone/date (not the default scaffold).
- [x] campaign-overview.json contains a non-empty `campaign_rules` block surfaced by `world_kit.campaign_rules()` / scene context.
- [x] ruleset.json `rules_doc` either points at an existing file or is null (no dangling pointer).
- [x] import.md documents this as a required step (follow-on to Step 6.5).
- [x] Verified on a fresh import: overview + campaign_rules + valid rules_doc all present.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

### 2026-06-06T17:10:36Z — pass [ss-7q3w9z]
4 unit tests in tests/test_overview_seed.py pass: seed sets fields + campaign_rules while
preserving player_position/session_count; fix_rules_doc nulls a dangling pointer; leaves a
valid pointer; campaign_rules readable in WorldKit's overview.get shape. Applied to the live
anarchists-cookbook: overview now campaign_name "The Iron Tangle", genre "LitRPG /
Comedy-Horror", 6 campaign_rules keys (progression/loot_boxes/saferooms/iron_tangle_trains/
stairwells/collapse_clock); WorldKit().campaign_rules() returns them; dangling rules_doc
"rules.md" nulled. import Step 6.6 documents the authoring step.
[handoff] rules-doc-authoring will write substantive rules.md prose and re-point rules_doc.

## History

- 2026-06-06T16:37:48Z  created → ready  [ship-it]
- 2026-06-06T17:09:00Z  claimed  [ss-7q3w9z]
- 2026-06-06T17:10:36Z  done  [ss-7q3w9z]
