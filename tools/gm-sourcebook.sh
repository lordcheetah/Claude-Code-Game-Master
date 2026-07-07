#!/bin/bash
#
# gm-sourcebook.sh - compile a world's REFERENCE material into a table-ready
# TTRPG sourcebook EPUB (the boxed-set inverse of gm-chronicle.sh).
#
# Where gm-chronicle.sh sets down what a campaign PLAYED, this assembles what a
# GM needs to RUN the world at a table with no computer: the setting (world
# bible), the rules of play (the World Kit rendered as readable rules), the cast
# (NPC roster + stat blocks), a gazetteer with a travel table, a bestiary, a
# treasury, an adventure front, and appendices (pregens, random tables, the
# world's tongues, an art-plate gallery).
#
# Deterministic core: it arranges the campaign's own structured data. The
# `sourcebook-author` agent enriches it by writing sourcebook-prose.json (rules
# taught in plain language, GM guidance, voiced intros, gap-filled stat blocks,
# pregens, random tables, a starter adventure) — picked up automatically if it
# sits in the campaign dir, or pointed at with --prose.
#
# Usage:
#   gm-sourcebook.sh [campaign-name]     Compile a campaign's sourcebook (defaults to active)
#   gm-sourcebook.sh --prose FILE        Use a specific prose companion JSON
#   gm-sourcebook.sh --cover N           Use the Nth plate (1-based) as the cover
#   gm-sourcebook.sh --no-adventure      Omit the Adventure Front (hooks + starter)
#   gm-sourcebook.sh --md-only           Write the manuscript .md but skip pandoc
#
set -e
source "$(dirname "$0")/common.sh"

CAMPAIGN=""
PROSE=""
COVER=""
ADVENTURE="yes"
MD_ONLY="no"

while [ $# -gt 0 ]; do
    case "$1" in
        --prose) PROSE="$2"; shift 2 ;;
        --cover) COVER="$2"; shift 2 ;;
        --no-adventure) ADVENTURE="no"; shift ;;
        --md-only) MD_ONLY="yes"; shift ;;
        -h|--help)
            echo "Usage: gm-sourcebook.sh [campaign] [--prose FILE] [--cover N] [--no-adventure] [--md-only]"
            exit 0 ;;
        *) CAMPAIGN="$1"; shift ;;
    esac
done

# Resolve the campaign directory (named, or the active one).
if [ -n "$CAMPAIGN" ]; then
    slug=$(echo "$CAMPAIGN" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]/-/g')
    CDIR="$CAMPAIGNS_DIR/$slug"
else
    CDIR=$(get_campaign_dir) || CDIR=""
fi
if [ -z "$CDIR" ] || [ ! -d "$CDIR" ]; then
    error "Campaign not found${CAMPAIGN:+: $CAMPAIGN}. Specify a campaign name, or switch to one first."
    exit 1
fi

# Build the manuscript.
MD="$CDIR/sourcebook.md"
info "Assembling sourcebook from the world's kit, bible, cast, and gazetteer..."
[ -n "$PROSE" ] && [ ! -f "$PROSE" ] && warning "Prose companion not found: $PROSE (assembling reference-only)."
EXTRA=""
[ "$ADVENTURE" = "no" ] && EXTRA="--no-adventure"
INFO=$($PYTHON_CMD "$LIB_DIR/sourcebook.py" "$CDIR" --out "$MD" \
    ${PROSE:+--prose "$PROSE"} ${COVER:+--cover $COVER} $EXTRA)

# Parse the JSON report (portable — no jq dependency).
read_field() { echo "$INFO" | $PYTHON_CMD -c "import sys,json;print(json.load(sys.stdin).get('$1',''))"; }
COVERFILE=$(read_field cover)
EPUB=$(read_field epub)
TITLE=$(read_field title)
NPCS=$(read_field npcs)
LOCS=$(read_field locations)
PLATES=$(read_field plates)
HAS_PROSE=$(read_field prose)

success "Manuscript written: $MD"
info "  title: $TITLE | cast: $NPCS | locations: $LOCS | plates: $PLATES"
[ "$HAS_PROSE" = "True" ] || warning "  No prose companion — reference-only tome. Run the sourcebook-author agent to add taught rules, pregens, tables, and a starter adventure."

if [ "$MD_ONLY" = "yes" ]; then
    echo "$MD"
    exit 0
fi

# Bind to EPUB with pandoc.
if ! command -v pandoc >/dev/null 2>&1; then
    warning "pandoc is not installed — cannot bind the EPUB."
    warning "Install pandoc (https://pandoc.org), or use the manuscript directly:"
    echo "  $MD"
    exit 1
fi

COVER_ARG=""
[ -n "$COVERFILE" ] && COVER_ARG="--epub-cover-image=images/$COVERFILE"

# Run pandoc from the campaign dir so image paths (images/*.png) resolve.
# toc-depth 2 so Parts and their chapters both list.
( cd "$CDIR" && pandoc "sourcebook.md" -o "$EPUB" --toc --toc-depth=2 $COVER_ARG )

if [ -f "$CDIR/$EPUB" ]; then
    SIZE=$(du -h "$CDIR/$EPUB" 2>/dev/null | cut -f1)
    success "Sourcebook bound: $EPUB ($SIZE)"
    echo "  Location: $CDIR/$EPUB"
    echo "  Open with any ereader (Apple Books, Calibre); Calibre converts to Kindle or PDF for print."
    echo "file://$CDIR/$EPUB"
else
    error "pandoc did not produce the EPUB. The manuscript is available at: $MD"
    exit 1
fi
