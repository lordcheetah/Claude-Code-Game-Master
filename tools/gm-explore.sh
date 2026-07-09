#!/bin/bash
# gm-explore.sh - the metroidvania engine: ability-gated reachability + "what just
# opened" backtracking (logic in lib/exploration.py). Reads the active campaign's
# locations.json (connection `requires`) against the active PC's held capabilities.
#
# Usage:
#   gm-explore.sh reachable [--from "<loc>"]   What the PC can reach now + what's gated
#   gm-explore.sh gained "<ability>"           What that ability just opened (incl. visited)
#   gm-explore.sh gates                        Every gate on the map; open/locked for the PC
#   gm-explore.sh can-move "<dest>"            Is a move from current -> dest allowed?
# Add --json for a structured envelope.
#
# Declare gates with:  gm-location.sh gate "<from>" "<to>" --requires "morph_ball,grapple"
# The GM runs `gained` right after a capability is awarded to surface backtracking.

source "$(dirname "$0")/common.sh"
require_active_campaign

ACTION="$1"
shift 2>/dev/null || true

case "$ACTION" in
    reachable|gained|gates|can-move)
        $PYTHON_CMD "$LIB_DIR/exploration.py" "$ACTION" "$@"
        ;;
    -h|--help|"")
        echo "Metroidvania exploration engine (ability-gated map)"
        echo "Usage: gm-explore.sh <reachable|gained|gates|can-move> [args]"
        echo ""
        echo "  reachable [--from \"<loc>\"]   What the PC can reach now + what's gated"
        echo "  gained \"<ability>\"           What that ability just opened (run after an upgrade)"
        echo "  gates                        Every gate on the map; open/locked for the PC"
        echo "  can-move \"<dest>\"            Is a move from current -> dest allowed?"
        echo ""
        echo "Declare a gate:  gm-location.sh gate \"<from>\" \"<to>\" --requires \"morph_ball\""
        ;;
    *)
        echo "Unknown action: $ACTION"
        echo "Valid: reachable, gained, gates, can-move"
        exit 1
        ;;
esac

exit $?
