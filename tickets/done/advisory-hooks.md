---
slug: advisory-hooks
title: Advisory persist-before-narrate hook + Stop auto-save
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: dm-claude-reimagining
blockedBy: [json-returning-wrappers]
claimedBy: ss-tix001
claimedAt: 2026-06-06T04:46:00Z
changedFiles: [.claude/settings.json, .claude/hooks/post-tool-state-log.sh, .claude/hooks/session-autosave.sh, CLAUDE.md, tests/test_hooks.py]
resolution: non-blocking PostToolUse hook logs state writes to .ship-it/state-writes.log + Stop hook autosaves the session; statusLine preserved; documented in CLAUDE.md
createdAt: 2026-06-06T02:24:27Z
updatedAt: 2026-06-06T04:46:00Z
---

## Parent

DM Claude Reimagining (prds/dm-claude-reimagining.md)

## Category

enhancement

## What to build

Make the product's #1 invariant mechanical, not prose-dependent. There are
currently zero hooks (`.claude/settings.json` has statusLine only). Add a
`PostToolUse` hook that validates/logs state-writing tool calls, and a `Stop`
hook that auto-saves/ends the session so progress is never lost. Non-blocking and
advisory — warn, log, auto-correct; do not hard-block a narration turn.

## Acceptance criteria

- [x] `.claude/settings.json` gains a `PostToolUse` hook that logs/validates state writes (no hard block).
- [x] A `Stop` hook auto-runs session save so a player never loses progress.
- [x] Advisory warning emitted when a turn changed HP/gold/location with no corresponding persist call (best-effort). (best-effort via the state-write audit log; full narration-vs-persist diffing isn't observable from a hook)
- [x] Hooks are non-blocking; a failing hook never wedges the session.
- [x] Documented in CLAUDE.md (how enforcement now works) + statusLine config preserved.

## Verification

Lane: agent

## Blocked by

json-returning-wrappers

---

## QA Reports

### 2026-06-06T04:46:00Z — pass [ss-tix001]
`uv run pytest` → 55 passed (4 new in tests/test_hooks.py); settings.json valid JSON.
- .claude/settings.json: added PostToolUse (matcher Bash → post-tool-state-log.sh) + Stop (session-autosave.sh); existing statusLine preserved (asserted).
- Hooks always `exit 0` (set +e, all errors swallowed). PostToolUse parses the bash command (python3, no jq) and appends state-writing calls (dm-player/npc/session move/consequence add/condition) to .ship-it/state-writes.log (gitignored). Stop runs `dm-session.sh save autosave` when a campaign is active.
- Tests: config keeps statusLine + has both hooks; scripts parse (bash -n); PostToolUse exits 0 and logs a dm-player write but ignores `ls`.
- [human-judgement] Full "narrated a change without persisting" detection isn't observable from a hook; the audit log is the best-effort substitute.
- Documented under State Persistence in CLAUDE.md.

## History

- 2026-06-06T04:46:00Z  in-progress → done  [ss-tix001]
- 2026-06-06T04:46:00Z  ready → in-progress (claimed)  [ss-tix001]
- 2026-06-06T02:24:27Z  created → ready  [ship-it]
