---
name: gm-exploration
description: Running an ability-gated (metroidvania) world — where the map is the plot and capabilities are keys that open regions already glimpsed but unreachable. Load when the active World Kit's signature system is ability-gated exploration (e.g. a Metroid-grammar campaign), or whenever a location is sealed behind a required ability. Covers gate enforcement, the "what just opened" backtracking surfacing, scan-for-weakness, and consumable vitals.
---

# Running an Ability-Gated World (metroidvania)

The world is one connected space full of obstacles that each name a required
capability. The player grows **spatially** — the map expands because they became
more, not because they walked further. Your job is to make that loop *felt*:
explore → hit a wall → find the key → return changed. The engine
(`lib/exploration.py` / `tools/gm-explore.sh`) enforces the gates and computes the
backtracking so you don't have to track it by hand.

## Gates are DATA, and the world enforces them
A connection in `locations.json` can carry `requires: [ability, ...]`. Declare
gates as you author or discover the map:
```bash
# a symmetric gate (needed both ways — a morph tunnel, an ice-frozen platform):
bash tools/gm-location.sh connect "<A>" "<B>" "<path>" --requires "morph_ball"
# gate an EXISTING connection (or clear it by omitting --requires):
bash tools/gm-location.sh gate "<A>" "<B>" --requires "grapple_beam,gravity_suit"
bash tools/gm-location.sh gate "<A>" "<B>" --requires "" --direction forward   # one-way
```
Ability names are matched tolerantly by words: `requires: "missile"` is satisfied
by a held "Missile Launcher"; `requires: "wave beam"` is NOT satisfied by "Power
Beam". Abilities live on the character as capabilities/features/equipment.

**Enforcement is automatic.** `gm-session.sh move "<dest>"` REFUSES a gated move
the PC can't make and prints `[BLOCKED] … needs: <ability>`. When that happens,
do NOT walk them through — **narrate the gate**: the tunnel too small to stand in,
the chasm too wide to leap, the door keyed to an energy they don't carry. The
withholding is the teaching. (New/unmapped destinations are never gated —
exploration is free.) For a rare narrative exception, `move … --force` overrides.

## THE PAYOFF — surface what just opened
The instant the PC gains a capability, run:
```bash
bash tools/gm-explore.sh gained "<ability>"
```
It returns the locations that ability makes **newly reachable — including places
already visited** — and you announce them in the world's voice: *"the Grapple
Beam means you can finally cross the chasm back in the crashed frigate."* This is
the soul of the genre; never let a new capability land without telling the player
what door in their memory just unlocked.

Two more reads for framing a scene:
- `bash tools/gm-explore.sh reachable` — what the PC can reach now, and what sits
  just behind a gate they can't pass yet (use it to seed longing: let them
  *glimpse* the gated place — "you can see it; you can't reach it yet").
- `bash tools/gm-explore.sh gates` — the whole lock map (open/locked for this PC).

## Gaining a capability (the ceremony)
Abilities are item/feature flags, not a level. Award one by adding it to the
character (`gm-player.sh loot`/`inventory add`, or the character's capabilities),
persist the milestone/spectacle (`gm-player.sh award --tier …`), then IMMEDIATELY
run `gm-explore.sh gained`. Make the acquisition land: the Suit accepting the
gift, the world quietly rearranging behind them.

## Scan-for-Weakness (puzzles, not damage-races)
Tough enemies are puzzles. A `scan` (Systems/the kit's read stat) reveals a
creature/mechanism's history AND its vulnerability: a stalker you survive by
evasion until you recover the one weapon that answers it; a boss armored except a
phase-gated weak point. Read the world before you fight it; reward the read.

## Consumable vitals (missiles / energy / ammo)
Track spendable resources with `gm-player.sh resource <name> <vital> ±N`:
```bash
bash tools/gm-player.sh resource "<pc>" missiles -1    # fired a missile
bash tools/gm-player.sh resource "<pc>" missiles +5    # a Missile Tank pickup
```
An "Energy Tank"-style pickup that raises MAX life is an HP-max increase, not a
resource restock. Scarcity is tension — make the player feel each shot.

## Pacing the loop
- Let gates be **seen before they're solvable** — a glimpsed room, a door the
  wrong color — so the key, when found, pays off a remembered frustration.
- When the PC is stuck, `reachable` shows every gated frontier and its missing
  ability — a gentle, diegetic nudge ("what have you not been able to reach, and
  what did it want?").
- Backtracking is not filler; it's the reward. A returned-to place should have
  changed (new threat, new lore, the thing you couldn't get, now gettable).
