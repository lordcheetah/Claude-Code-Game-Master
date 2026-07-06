#!/bin/bash
# gm-conlang.sh - thin, allowlist-safe wrapper around the vendored conlang engine.
#
# Generates a culture's constructed language deterministically from its name, for
# consistent NPC/place names, alien phrases, and writing systems across a campaign.
# A fixed, read-only wrapper so it can be allowlisted as `Bash(bash tools/gm-conlang.sh*)`.
#
# Usage:
#   bash tools/gm-conlang.sh generate "Deep Ones"      # mint & save the whole tongue
#   bash tools/gm-conlang.sh name "Deep Ones" --count 6
#   bash tools/gm-conlang.sh word "Deep Ones" "sea"
#   bash tools/gm-conlang.sh phrase "Deep Ones"
#   bash tools/gm-conlang.sh list
source "$(dirname "$0")/common.sh"
exec $PYTHON_CMD "$LIB_DIR/conlang_gm.py" "$@"
