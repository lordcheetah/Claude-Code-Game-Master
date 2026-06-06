---
slug: bible-confirm-gate
title: Draft-then-confirm review gate for the generated world/ruleset
category: enhancement
kind: hitl
priority: p1
lane: manual
parentPrd: dm-claude-reimagining
blockedBy: [import-longcontext-read]
claimedBy: ss-tix001
claimedAt: 2026-06-06T05:23:51Z
changedFiles: [lib/world_bible.py, tests/test_bible_confirm_gate.py]
resolution: null
createdAt: 2026-06-06T02:24:27Z
updatedAt: 2026-06-06T05:23:51Z
---

## Parent

DM Claude Reimagining (prds/dm-claude-reimagining.md)

## Category

enhancement

## What to build

Quality gate so auto-derived rules don't silently ship generic/wrong. After
import generates the world-bible + drafted ruleset + campaign_rules, present a
review step: show the human the drafted voice/factions/signature-systems +
proposed rules, allow edits, and require confirmation before the world becomes
playable. Middle path between fully-automatic and hand-authored.

## Acceptance criteria

- [x] Import pauses at a review step presenting the drafted bible + ruleset + campaign_rules in human-readable form. (WorldBible.review_summary provides the draft; /import presents it — model flow)
- [x] The human can edit/approve/reject sections before play starts. (edit world-bible.json then confirm(); reject = leave unconfirmed / re-draft)
- [x] An unconfirmed world is not marked playable. (is_playable() False when bible.confirmed == False)
- [x] Confirmation persists the approved artifacts; rejection allows re-draft. (confirm() sets + saves confirmed:true)
- [ ] Manual walkthrough on a sample import shows the gate working end-to-end. (hitl — awaiting your sign-off in in-review)

## Verification

Lane: manual

## Blocked by

import-longcontext-read

---

## QA Reports

### 2026-06-06T05:23:51Z — in-review [ss-tix001]
hitl — implemented; routed to in-review for human sign-off. `uv run pytest` → 132 passed (5 new in tests/test_bible_confirm_gate.py).
- WorldBible.is_confirmed (legacy/no-flag = confirmed; fresh draft = confirmed:false), is_playable (gates only an unconfirmed bible), confirm() (sets+persists), review_summary() (human-facing draft: name/tone/voice/themes/factions/signature_systems).
- Tests: legacy bible playable; confirmed:false → not playable; confirm() → playable after reload; review_summary presents the draft; no-bible campaign playable.
- [human-judgement] The import pause + interactive edit/approve is the /import command's model-driven step on top of these primitives; needs a live walkthrough to sign off.

## History

- 2026-06-06T05:23:51Z  in-progress → in-review  [ss-tix001]
- 2026-06-06T05:23:51Z  ready → in-progress (claimed)  [ss-tix001]
- 2026-06-06T02:24:27Z  created → ready  [ship-it]
