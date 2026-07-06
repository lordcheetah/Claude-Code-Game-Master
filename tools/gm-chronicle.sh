#!/bin/bash
#
# gm-chronicle.sh - compile a played campaign into an illustrated EPUB ebook.
#
# Assembles the campaign's own recorded material (session-log summaries, the
# chronicler's image plates, the character dossier, the NPC roster, the world
# bible's voice) into a Markdown manuscript, then binds it to EPUB with pandoc.
#
# Usage:
#   gm-chronicle.sh [campaign-name]      Compile a campaign (defaults to active)
#   gm-chronicle.sh --cover N            Use the Nth plate (1-based) as the cover
#   gm-chronicle.sh --no-appendix        Omit the beat-by-beat "Chronicle of Record"
#   gm-chronicle.sh --md-only            Write the manuscript .md but skip pandoc
#
set -e
source "$(dirname "$0")/common.sh"

CAMPAIGN=""
COVER=""
APPENDIX="yes"
MD_ONLY="no"

while [ $# -gt 0 ]; do
    case "$1" in
        --cover) COVER="$2"; shift 2 ;;
        --no-appendix) APPENDIX="no"; shift ;;
        --md-only) MD_ONLY="yes"; shift ;;
        -h|--help)
            echo "Usage: gm-chronicle.sh [campaign] [--cover N] [--no-appendix] [--md-only]"
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
MD="$CDIR/chronicle.md"
info "Assembling manuscript from the campaign's log, plates, and bible..."
EXTRA=""
[ "$APPENDIX" = "no" ] && EXTRA="--no-appendix"
INFO=$($PYTHON_CMD "$LIB_DIR/chronicle.py" "$CDIR" --out "$MD" ${COVER:+--cover $COVER} $EXTRA)

# Parse the JSON report (portable — no jq dependency).
read_field() { echo "$INFO" | $PYTHON_CMD -c "import sys,json;print(json.load(sys.stdin).get('$1',''))"; }
COVERFILE=$(read_field cover)
EPUB=$(read_field epub)
TITLE=$(read_field title)
SESS=$(read_field sessions)
PLATES=$(read_field plates)

success "Manuscript written: $MD"
info "  title: $TITLE | chapters: $SESS | plates: $PLATES"

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
( cd "$CDIR" && pandoc "chronicle.md" -o "$EPUB" --toc --toc-depth=1 $COVER_ARG )

if [ -f "$CDIR/$EPUB" ]; then
    SIZE=$(du -h "$CDIR/$EPUB" 2>/dev/null | cut -f1)
    success "Chronicle bound: $EPUB ($SIZE)"
    echo "  Location: $CDIR/$EPUB"
    echo "  Open with any ereader (Apple Books, Calibre); Calibre converts to Kindle."
    echo "file://$CDIR/$EPUB"
else
    error "pandoc did not produce the EPUB. The manuscript is available at: $MD"
    exit 1
fi
