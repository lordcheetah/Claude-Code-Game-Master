#!/bin/bash
# gm-view.sh - Canvas view panel (thin wrapper for view_manager.py)
#
# The canvas is a persistent second-pane game view the GM draws into.
#   scene/clear : write the agent-authored scene (needs an active campaign).
#   render      : draw the framed panel to stdout (degrades to a placeholder
#                 with no campaign, so NO require_active_campaign).
# (The live `watch` loop is a later canvas ticket.)

source "$(dirname "$0")/common.sh"

if [ "$#" -lt 1 ]; then
    echo "Usage: gm-view.sh <action> [args]"
    echo ""
    echo "Actions:"
    echo "  scene --title <title>    - Push a scene onto the canvas (body read from stdin)"
    echo "  clear                    - Clear the canvas (keeps the file)"
    echo "  render                   - Render the canvas panel to stdout (one-shot)"
    echo ""
    echo "Examples:"
    echo "  echo \"\$MAP_ART\" | gm-view.sh scene --title \"The Sunken Crypt\""
    echo "  gm-view.sh clear"
    echo "  gm-view.sh render"
    exit 1
fi

ACTION="$1"
shift

case "$ACTION" in
    scene)
        require_active_campaign
        # Body is read from stdin; pass through --title and any flags.
        $PYTHON_CMD "$LIB_DIR/view_manager.py" scene "$@"
        ;;

    clear)
        require_active_campaign
        $PYTHON_CMD "$LIB_DIR/view_manager.py" clear
        ;;

    render)
        # No campaign guard: render shows a placeholder when none is active.
        $PYTHON_CMD "$LIB_DIR/view_manager.py" render
        ;;

    *)
        echo "Unknown action: $ACTION"
        echo "Valid actions: scene, clear, render"
        exit 1
        ;;
esac

# Propagate Python exit code
exit $?
