#!/bin/bash
# gm-combat.sh - Persisted combat state (optional; for fights worth tracking)
#
#   gm-combat.sh start
#   gm-combat.sh add-enemy "Orc Warrior" 22 --ac 17 --init 12
#   gm-combat.sh add-pc "Iren Calder" 22 --ac 14 --init 15 --player "Sam"   # multiplayer: PC in initiative
#   gm-combat.sh add-ally "Oona" 12 --ac 12 --init 8                         # GM-run ally in initiative
#   gm-combat.sh hp "Orc Warrior" -5
#   # PC damage is authoritative on the seat sheet: gm-player.sh hp "Iren Calder" -5 --player "Sam"
#   gm-combat.sh condition "Orc Warrior" add prone
#   gm-combat.sh next-turn
#   gm-combat.sh header        # render the combat header
#   gm-combat.sh end           # clear state (award XP/loot via gm-player afterwards)
#
# Add --json to any command for a structured envelope.

source "$(dirname "$0")/common.sh"

require_active_campaign

$PYTHON_CMD "$LIB_DIR/combat_manager.py" "$@"
