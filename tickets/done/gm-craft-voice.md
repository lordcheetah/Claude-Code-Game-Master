---
slug: gm-craft-voice
title: "gm-craft narrates to the NARRATIVE VOICE block"
category: enhancement
kind: afk
priority: p1
lane: manual
parentPrd: narrative-voice-fidelity
blockedBy: [voice-context-surfacing]
claimedBy: ss-w7k2m9
claimedAt: 2026-06-06T20:36:12Z
changedFiles: [.claude/skills/gm-craft/SKILL.md]
resolution: "gm-craft adds a Narrative Voice section: narrate to the NARRATIVE VOICE block (rhythm/diction/imagery), world voice vs NPC dialogue, in-voice self-check"
createdAt: 2026-06-06T20:29:20Z
updatedAt: 2026-06-06T20:36:35Z
---

## Parent

Narrative Voice Fidelity (prds/narrative-voice-fidelity.md)

## Category

enhancement

## What to build

Close the loop in the narration craft skill. Update `.claude/skills/gm-craft/SKILL.md`
to instruct the GM: when scene context includes a `--- NARRATIVE VOICE ---` block,
treat its `Style` + `sample_passages` as the prose target — match the author's
rhythm, diction, and imagery in narration (distinct from NPC dialogue, which uses
NPC canonical lines). Add a short, concrete reminder to self-check voice when a beat
reads generic.

## Acceptance criteria

- [x] `gm-craft/SKILL.md` references the `NARRATIVE VOICE` block as the narration prose target
- [x] Distinguishes world/author prose voice from per-NPC dialogue voice
- [x] Includes a brief in-voice self-check cue
- [x] Guidance is concrete (not "write better") — names matching rhythm/diction/imagery to the sample passages

## Verification

Lane: manual

Human-judgement: read the updated craft guidance; confirm it actionably directs the
GM to narrate in the surfaced voice. Live efficacy judged at a /gm dry-run with a
voiced world.

## Blocked by

voice-context-surfacing

---

## QA Reports

### 2026-06-06T20:36:35Z — pass (manual lane) [ss-w7k2m9]
Added a `## Narrative Voice` section to `gm-craft/SKILL.md`: treat the `--- NARRATIVE VOICE ---` block as the prose target (match rhythm/diction/imagery, imitate cadence not text), explicitly separates world/author prose voice from per-NPC dialogue (NPC VOICES), and adds an in-voice self-check for generic-reading beats. Structural checks all green.

[human-judgement] Live efficacy — does the GM actually narrate in-voice at a `/gm` session with a voiced world (Howard vs Tolkien reads distinct)? — needs a human dry-run. Logged for manual review.

## History

- 2026-06-06T20:36:35Z  ready → done  [ss-w7k2m9]
- 2026-06-06T20:36:12Z  claimed  [ss-w7k2m9]
- 2026-06-06T20:29:20Z  created → ready  [ship-it]
