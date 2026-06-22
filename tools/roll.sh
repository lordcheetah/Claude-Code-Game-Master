#!/bin/bash
# roll.sh - thin, allowlist-safe wrapper around the dice roller.
#
# Dice are rolled every beat, but the raw `uv run python lib/dice.py ...` form
# can't be safely allowlisted (a `uv run *` rule would permit arbitrary code).
# This fixed, read-only wrapper does exactly one thing — roll dice and print the
# result — so it can be allowlisted as `Bash(bash tools/roll.sh*)` without that risk.
#
# Usage: bash tools/roll.sh "1d20+5"   (one dice-notation string, same as dice.py)
source "$(dirname "$0")/common.sh"
exec $PYTHON_CMD "$LIB_DIR/dice.py" "$@"
