---
name: gm-combat
description: D&D-kit combat mechanics — initiative, attack/damage resolution, XP-by-CR awards, combat modifiers, and death saves. Load when a hostile action is declared or combat starts in a campaign whose World Kit is dnd5e. For non-D&D kits, use the generic core (game_core.py) and the active ruleset instead.
---

# Combat Mechanics (D&D kit)

Persist combat with `bash tools/gm-combat.sh` (start/add-enemy/hp/condition/next-turn/end) so HP and initiative survive resumes.

## Flow
1. Get enemy stats (`features/dnd-api/monsters/dnd_monster.py "[creature]" --combat` or quick: AC 13, HP 15, +3, 1d6+1).
2. Initiative: `uv run python lib/dice.py "1d20+[dex]"` per combatant; order high→low.
3. Each turn: attack `1d20+bonus` vs AC; on hit roll damage; update HP via `gm-combat.sh hp`.
4. Resolution: award XP, handle loot (persist BEFORE narrating), advance time.

## XP by Challenge Rating
| CR | XP | CR | XP | CR | XP |
|----|-----|----|----|----|----|
| 0 | 10 | 4 | 1,100 | 10 | 5,900 |
| 1/8 | 25 | 5 | 1,800 | 11 | 7,200 |
| 1/4 | 50 | 6 | 2,300 | 13 | 10,000 |
| 1/2 | 100 | 7 | 2,900 | 15 | 13,000 |
| 1 | 200 | 8 | 3,900 | 17 | 18,000 |
| 2 | 450 | 9 | 5,000 | 20 | 25,000 |
| 3 | 700 | | | | |

Bonus: clever tactics +25%, creative environment +10-25%, social victory +50%.

## Modifiers
Advantage = 2d20 keep high; Disadvantage = keep low. Half cover +2 AC; 3/4 cover +5. Flanking = advantage (melee). Prone: advantage melee / disadvantage ranged. Crit (nat 20) = double damage dice then add mods. Nat 1 = auto-miss.

## Death & Dying
0 HP → unconscious + death saves (DC 10 Con each turn): 3 successes = stable, 3 failures = death. Nat 20 = 1 HP + conscious. Nat 1 = 2 failures. Damage ≥ max HP = instant death.
