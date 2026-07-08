---
name: gm-multiplayer
description: Running a multi-PC table — several human players as peers at one shared session. Load when scene context reports "Multiplayer: ON". Covers seat/roster management, per-player action attribution, spotlight rotation, group-vs-split scenes, multi-PC initiative, and the non-destructive death hand-off (retire one seat, others play on). Kit-agnostic; layers on top of the normal core loop.
---

# Running a Multiplayer Table

Several humans share ONE game session as PEERS. The core loop is unchanged
(CONTEXT → DECIDE → EXECUTE → PERSIST → NARRATE); this skill is the etiquette and
plumbing for more than one player character. Load it whenever scene context says
`Multiplayer: ON`. It is additive — none of it fires in single-player.

## The players and their seats
- Each human owns a **seat**: their own character sheet at
  `players/<slug>/character.json`, tracked in `players.json`. The campaign-root
  `character.json` is NOT the party in multiplayer — the seats are.
- Scene context prints **THE PARTY** block: `player → character`, HP, level,
  conditions, and a `★` on the current **spotlight** seat. Read it every beat.
- Manage seats with `bash tools/gm-party.sh`:
  - `add "<player>" --sheet '<json>'` — add a seat (seed the sheet, or leave it
    and have them build a PC via `create-character`, then
    `gm-party.sh sheet "<player>" '<json>'`).
  - `list` — the party block. `spotlight "<player>"` — set whose turn/focus.
  - `mark-dead "<player>" --cause "..."` — retire ONE seat (see Death, below).

## Attribute every action to the player who took it
Input arrives tagged with a player (in local play they say who they are; the
online relay prefixes actions, e.g. `[Sam] I ask the lantern to gutter`). Always:
- Resolve and persist against **that player's seat**, never a shared PC. Every
  `gm-player.sh` command takes `--player "<player>"`:
  - HP: `bash tools/gm-player.sh hp "<char>" -5 --player "Sam"`
  - XP / gold / conditions / appearance / kill: same `--player` flag.
- Address the narration to the acting character **by name** so the table knows
  who did what: *"Iren, the grain flares white in your palm —"*.

## Players come and go — join late, leave early, miss a session
Real tables aren't fixed. Handle it so the game never stalls and no one loses a
character:

- **Join mid-session:** add a seat live — `gm-party.sh add "<player>" --sheet '<json>'`
  (or `add` then have them build a PC via `create-character` and
  `gm-party.sh sheet ...`). Then BRIDGE them into the fiction — a new arrival, a
  reinforcement, someone who was here all along — don't just pop them onstage.
- **Leave mid-session / absent for a session:** each player owns a standing
  choice for how THEIR absence is handled — they set it themselves (there's an
  "If I'm away" selector on the relay client), or the GM sets it for them with
  `gm-party.sh policy "<player>" --write-out | --gm | --to "<other>"`. The default
  is **write-out**. When the player is actually gone, just run
  **`gm-party.sh away "<player>"`** — it applies THEIR choice:
  1. **write-out** (default) — the PC exits the fiction with an in-world reason
     (called away, taken ill, chasing another lead); offscreen until they return.
  2. **gm** — the PC stays in the scene and you voice them as a party NPC; keep
     them supportive, not spotlight-stealing (it's someone else's hero).
  3. **delegate** — the named other player runs the PC; resolve its actions on
     the absent seat (`gm-player.sh ... --player "<absent player>"`).
  (You can still override for one instance: `away "<player>" --gm|--to|--write-out`.)
  `gm-relay.sh who` shows a disconnected player's stored choice so you can honor
  it without asking.
- **They come back:** `gm-party.sh back "<player>"` — they resume their own PC;
  bridge them back into the scene.

The party block and `gm-relay.sh who` show each seat's state, and loose timing
**never waits on an absent seat** — only on connected, self-driven players who
haven't acted. A GM/delegated PC is played; a written-out PC is offstage.

## Turn timing — LOOSE by default, STRICT only when you announce it
This is the rule that makes or breaks a multi-PC table. Two modes:

**LOOSE (the default — exploration, social, investigation, most scenes):**
Time does NOT advance until every player who wants to act in the beat has had the
chance. Players' actions are allowed to **overlap and coordinate** — one player
sets up, another follows, a third capitalizes, all in the "same moment" of
fiction. So:
- **Collect before you resolve.** Present the situation, then let the table
  declare. Resolve the beat as a coordinated whole once everyone who wants in has
  spoken (or explicitly passes). Do not resolve player 1 and jump the clock
  forward before players 2 and 3 have moved.
- **Never spring a consequence on a player who hasn't had a turn.** Do NOT let a
  danger tighten, an NPC act, or a clock tick *between* one PC's action and
  another's unless you have declared strict timing. (Anti-example: narrating a boy
  about to finish a lethal asking — a live clock — before one of the PCs has even
  acted. That silently forced strict timing and pressured a player out of turn.)
- This matters even MORE for the online relay: remote players send actions in
  separate messages and cannot batch "all three at once," so the GM MUST gather
  the table's intentions and resolve together, at the table's pace.

**STRICT (only when the fiction has a real, ticking clock — combat, a chase, a
trap counting down, a collapsing bridge):**
- **Announce the switch, out loud, before it binds.** e.g. *"⏱ This is now a
  timed situation — order matters from here."* Say what the ordering rule is
  (per the active World Kit: roll initiative and act high→low, or
  simultaneous-declare-then-resolve), and say when it ENDS and you're back to
  loose. Players must always know which mode they're in.
- Ordering comes from the KIT's resolution model — initiative for d20/D&D,
  whatever the active ruleset specifies otherwise. In strict mode the clock DOES
  advance between turns; that's the whole point, and it's fair because you warned
  them.

When unsure, default to LOOSE. Strict timing without an announcement is the
single most common way a multi-PC scene feels unfair.

## Give everyone spotlight (pacing)
The cardinal sin of a multi-PC table is one player soloing while the rest watch.
- **Go around.** After resolving one PC's action, turn to another by name:
  *"While Iren steadies the flame — Della, the archivist is looking straight at
  you. What do you do?"* Update `gm-party.sh spotlight` as focus moves.
- **Action menu OFF-feel even when ON:** in multiplayer, prefer ending a beat by
  naming **who is up next** over a generic 1/2/3 menu, unless one PC is mid-scene.
- **Group checks:** when the whole party does one thing (sneak, search), each
  player rolls their own PC; report per-player margins. Don't collapse to one roll.

## Split the party (optional)
Players may separate. Track each PC's location per-seat in the fiction and
intercut like a TV show — a beat with group A, then a beat with group B, ending
each on a small hook. Keep beats SHORT when split so no one waits long. (Location
is still narrated per the fiction; the shared `move` reflects the main scene.)

## Combat with multiple PCs
Combat is the archetypal STRICT-timing situation (see Turn timing) — say so as it
begins (*"⏱ Roll initiative — we're in rounds now"*) so everyone knows the mode
changed. Put the PCs in the SAME initiative order as the enemies:
1. `bash tools/gm-combat.sh start`
2. Each PC rolls initiative (`roll.sh "1d20+<mod>"`); add them:
   `gm-combat.sh add-pc "<char>" <hp> --ac <n> --init <roll> --player "<player>"`.
   Add GM allies with `add-ally`, enemies with `add-enemy`.
3. `next-turn` cycles the whole order high→low. On each PC's turn, prompt THAT
   player by name.
4. **PC damage is authoritative on the seat sheet:**
   `gm-player.sh hp "<char>" -N --player "<player>"` (the combat tracker's PC HP
   is only a turn-order snapshot). Enemy damage stays in `gm-combat.sh hp`.
5. A PC at 0 HP enters the kit's dying gate (D&D: death saves — `gm-combat`
   skill). Death only on the kit's trigger or when the fiction makes survival
   absurd — the same Stakes & Death rules as single-player, per player.

## Death is non-destructive here (important)
Single-player hands the ONE slot to a new hero (`become`). **Multiplayer never
does that** — retiring one seat must not evict anyone else. When a PC dies:
1. Persist the death on THAT seat: `gm-player.sh kill "<char>" --cause "..." --player "<player>"`, then `gm-party.sh mark-dead "<player>" --cause "..."` (flags the seat dead, archives that sheet to `players/<slug>/fallen/`). Log it (`gm-note.sh`).
2. Narrate the death with weight. The rest of the party is still in the scene —
   let them react, mourn, avenge, loot.
3. Offer **that one player** the hand-off (the others keep playing):
   1. Take over a party NPC as a NEW seat character.
   2. Roll a fresh character who arrives in the story.
   3. Step in as a canon figure from the source.
   Build it (`create-character`), then `gm-party.sh sheet "<player>" '<json>'`
   (or `add` if they'd been spectating). Bridge them into the fiction.
4. The fallen hero stays in the world's memory — referenced, mourned, avenged.

## Playing online (optional — the relay)
Local hot-seat needs nothing extra. To let players join from other machines, the
host runs a thin relay (`tools/gm-relay.sh`) — a small self-hosted web page. It
NEVER touches your reasoning; it just moves text between the players' browsers and
two log files. You (one Claude Code session) stay the whole GM.

Setup (host, once): `gm-session.sh multiplayer on`, add the seats
(`gm-party.sh add ...`), then `bash tools/gm-relay.sh serve --lan --code <word>`
and share the printed URL + room code. Players open it, pick their seat, and type.

The relay-aware beat loop (this is the online expression of LOOSE timing):
1. **Drain** the table's actions at the start of the beat:
   `bash tools/gm-relay.sh drain` → prints queued `[player] text` lines (and
   advances its cursor so you never re-read them). Also playable by the host at
   the keyboard as a seat.
2. **Wait for the table — but only for who's actually there.** Run
   `bash tools/gm-relay.sh who`: it shows each seat as ● connected / ○ unmanned /
   ✗ fallen, and whether a connected player has ✓ acted or is still … waiting.
   Gather every CONNECTED player who hasn't acted (re-`drain`/`who` as more
   arrive) before resolving — do not resolve one player and jump the clock.
   **Unmanned seats (○)** have no human this session: run that PC as a GM-voiced
   ally or keep them offstage; never stall the beat waiting on an empty chair.
   Online, this loose-timing gather is mandatory, not optional.
3. Resolve the beat, persist per seat (below).
4. **Post** your narration so the players see it:
   `bash tools/gm-relay.sh post "<your narration text>" [--image <plate.png>]`.
   Attach any Perpetua-Venn-style plate by its `images/` basename — the relay
   serves it to remote players (who can't open a host `file://` link).
5. `gm-relay.sh status` shows the URL, code, pending count, and seats;
   `gm-relay.sh stop` ends it. Optional: drive the cadence with `/loop` so you
   drain-and-respond whenever new actions arrive.

## Persist before narrating — per seat
The golden rule still holds, now per player: resolve → persist to the acting
player's seat (and to shared world state: NPCs, locations, facts, consequences) →
THEN narrate. Shared world files (`npcs.json`, `locations.json`, `facts.json`)
are written by the single GM session, so there is no write contention — one
table, one narrator, many heroes.
