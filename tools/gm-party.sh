#!/bin/bash
# gm-party.sh - multiplayer seat roster (additive, opt-in).
#
# Manages the human players sharing a multiplayer table: each player owns a SEAT
# with its own character sheet under players/<slug>/character.json. Logic lives in
# lib/party_manager.py. Per-seat SHEET edits (hp/xp/gold/conditions/kill) go
# through gm-player.sh with `--player <name>`, NOT this tool.
#
# Turn multiplayer on first:  bash tools/gm-session.sh multiplayer on
#
# Usage:
#   gm-party.sh add "<player>" [--character "<name>"] [--sheet '<json>']
#   gm-party.sh list                       Show the roster (party block)
#   gm-party.sh spotlight "<player>"       Set whose turn/focus is active
#   gm-party.sh sheet "<player>" '<json>'  Set/replace a seat's character sheet
#   gm-party.sh mark-dead "<player>" [--cause "..."]   Retire ONE seat (others play on)
#   gm-party.sh remove "<player>"          Remove a seat
#   gm-party.sh block                      Print the GM context party block
# All reads accept --json.

source "$(dirname "$0")/common.sh"
require_active_campaign

ACTION="$1"
shift 2>/dev/null || true

case "$ACTION" in
    add|list|spotlight|remove|mark-dead|sheet|away|back|policy|kick|unkick|block)
        $PYTHON_CMD "$LIB_DIR/party_manager.py" "$ACTION" "$@"
        ;;
    -h|--help|"")
        echo "Multiplayer seat roster"
        echo "Usage: gm-party.sh <action> [args]"
        echo ""
        echo "Actions:"
        echo "  add \"<player>\" [--character \"<name>\"] [--sheet '<json>']  - Add/update a seat"
        echo "  list                              - Show the roster (party block)"
        echo "  spotlight \"<player>\"              - Set whose turn/focus is active"
        echo "  sheet \"<player>\" '<json>'         - Set/replace a seat's character sheet"
        echo "  mark-dead \"<player>\" [--cause X]  - Retire ONE seat (others play on)"
        echo "  away \"<player>\" --gm | --to \"<other>\" | --write-out [--reason X]"
        echo "                                    - Handle a leaving/absent player (GM-run / delegate / write offscreen)"
        echo "  back \"<player>\"                   - A returning player runs their own PC again"
        echo "  remove \"<player>\"                 - Remove a seat"
        echo "  block                             - Print the GM context party block"
        echo ""
        echo "Enable multiplayer first: gm-session.sh multiplayer on"
        echo "Edit a seat's sheet in play: gm-player.sh hp \"<char>\" -3 --player \"<player>\""
        ;;
    *)
        echo "Unknown action: $ACTION"
        echo "Valid: add, list, spotlight, sheet, mark-dead, remove, block"
        exit 1
        ;;
esac

exit $?
