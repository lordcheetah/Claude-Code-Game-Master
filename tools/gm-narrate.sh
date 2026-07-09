#!/bin/bash
# gm-narrate.sh - record the played narration beat-by-beat so the chronicle ebook
# can be built from real prose, not just the end-of-session summary. Logic in
# lib/narration_log.py; beats append to the campaign's narration-log.jsonl.
#
# Usage:
#   gm-narrate.sh record "<prose>" [--location "..."] [--image file.png ...]
#       Record one beat's NARRATIVE prose (the story as told — not the status bar
#       or the numbered action menu). Location/session auto-fill from state.
#   gm-narrate.sh list                 Recorded beats (id · session · location)
#   gm-narrate.sh count                How many beats are recorded
# Add --json for a structured envelope. The GM records a beat as part of the
# core loop when preferences.record_narration is on (default). Toggle with
# `gm-session.sh record on|off`.

source "$(dirname "$0")/common.sh"
require_active_campaign

ACTION="$1"
shift 2>/dev/null || true

case "$ACTION" in
    record)
        if [ -z "$1" ]; then
            echo "Usage: gm-narrate.sh record \"<prose>\" [--location \"...\"] [--image file.png ...]"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/narration_log.py" record "$@"
        ;;
    list|count)
        $PYTHON_CMD "$LIB_DIR/narration_log.py" "$ACTION" "$@"
        ;;
    -h|--help|"")
        echo "Record the played narration for the chronicle ebook"
        echo "Usage: gm-narrate.sh <record|list|count> [args]"
        echo ""
        echo "  record \"<prose>\" [--location ...] [--image f.png ...]   Record one beat"
        echo "  list                                                    Recorded beats"
        echo "  count                                                   Beat count"
        ;;
    *)
        echo "Unknown action: $ACTION"
        echo "Valid: record, list, count"
        exit 1
        ;;
esac

exit $?
