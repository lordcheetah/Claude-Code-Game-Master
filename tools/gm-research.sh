#!/bin/bash
# gm-research.sh - web research via Tavily (logic in lib/web_research.py).
#
# Used to adapt a KNOWN IP that has no source document: gather canon from the web,
# then feed the text through the normal import pipeline (gm-extract.sh prepare) as
# source material. Needs TAVILY_API_KEY in .env (auto-sourced by common.sh).
#
# Usage:
#   gm-research.sh "<query>" [-n N] [--depth basic|advanced] [--raw] [--json]
#   gm-research.sh "Metroid Chozo lore ruins" -n 8 --depth advanced
#   echo "<query>" | gm-research.sh          # query from stdin
# Prints a readable digest by default (answer + numbered sources); --json for raw.

source "$(dirname "$0")/common.sh"

if [ -z "$TAVILY_API_KEY" ]; then
    warning "TAVILY_API_KEY is not set in .env — web research is unavailable."
    echo "Add TAVILY_API_KEY=... to .env (get a key at https://tavily.com)."
    exit 1
fi

$PYTHON_CMD "$LIB_DIR/web_research.py" "$@"
