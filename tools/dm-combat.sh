#!/bin/bash
# dm-combat.sh - Persisted combat state (optional; for fights worth tracking)
#
#   dm-combat.sh start
#   dm-combat.sh add-enemy "Orc Warrior" 22 --ac 17 --init 12
#   dm-combat.sh hp "Orc Warrior" -5
#   dm-combat.sh condition "Orc Warrior" add prone
#   dm-combat.sh next-turn
#   dm-combat.sh header        # render the combat header
#   dm-combat.sh end           # clear state (award XP/loot via dm-player afterwards)
#
# Add --json to any command for a structured envelope.

source "$(dirname "$0")/common.sh"

require_active_campaign

$PYTHON_CMD "$LIB_DIR/combat_manager.py" "$@"
