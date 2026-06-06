#!/bin/bash
# gm-recall.sh - Long-term campaign memory
#
#   gm-recall.sh recall "have we met Remex before?"   # surface relevant prior events
#   gm-recall.sh recall "dragon" --provenance our-story
#   gm-recall.sh memoir                                # tiered arc summary + recent
#   gm-recall.sh refresh                               # rebuild the memory index (auto on save)

source "$(dirname "$0")/common.sh"

require_active_campaign

$PYTHON_CMD "$LIB_DIR/campaign_memory.py" "$@"
