#!/bin/bash
# gm-view.sh - Canvas view panel (thin wrapper for view_manager.py)
#
# The canvas is a persistent second-pane game view the GM draws into.
# This wrapper owns the write path: push a scene, or clear it.
# (watch / render subcommands are added by later canvas tickets.)

source "$(dirname "$0")/common.sh"

if [ "$#" -lt 1 ]; then
    echo "Usage: gm-view.sh <action> [args]"
    echo ""
    echo "Actions:"
    echo "  scene --title <title>    - Push a scene onto the canvas (body read from stdin)"
    echo "  clear                    - Clear the canvas (keeps the file)"
    echo ""
    echo "Examples:"
    echo "  echo \"\$MAP_ART\" | gm-view.sh scene --title \"The Sunken Crypt\""
    echo "  gm-view.sh clear"
    exit 1
fi

require_active_campaign

ACTION="$1"
shift

case "$ACTION" in
    scene)
        # Body is read from stdin; pass through --title and any flags.
        $PYTHON_CMD "$LIB_DIR/view_manager.py" scene "$@"
        ;;

    clear)
        $PYTHON_CMD "$LIB_DIR/view_manager.py" clear
        ;;

    *)
        echo "Unknown action: $ACTION"
        echo "Valid actions: scene, clear"
        exit 1
        ;;
esac

# Propagate Python exit code
exit $?
