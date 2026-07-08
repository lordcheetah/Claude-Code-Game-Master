#!/bin/bash
# gm-relay.sh - online-multiplayer relay bridge (Phase 2).
#
# Lets remote players join a multiplayer table from a browser. The relay is a
# THIN, dependency-free HTTP server that never touches Claude Code: players' typed
# actions land in relay/inbox.jsonl; the GM `drain`s them each beat and `post`s
# narration to relay/outbox.jsonl, which players poll back. The GM (one Claude
# Code session) stays the whole brain. Turn multiplayer on first
# (gm-session.sh multiplayer on) and add seats (gm-party.sh add ...).
#
# Usage:
#   gm-relay.sh serve [--port N] [--code WORD] [--lan]   Start the server
#       --lan          bind 0.0.0.0 so players on your network can reach it
#       --code WORD    require a room code to join
#       (reach the open internet by pointing a tunnel — cloudflared/ngrok — at it)
#   gm-relay.sh drain     Pull new player actions into the session (GM, each beat)
#   gm-relay.sh pending   Show queued actions without consuming
#   gm-relay.sh post "<narration>" [--image FILE.png ...]   Send narration to players
#   gm-relay.sh status    Server URL, room code, pending actions, seats
#   gm-relay.sh stop      Stop a running server
# All reads accept --json.

source "$(dirname "$0")/common.sh"
require_active_campaign

CDIR=$(get_campaign_dir)
ACTION="$1"
shift 2>/dev/null || true

case "$ACTION" in
    serve)
        HOST="127.0.0.1"; PORT="8787"; CODE=""
        while [ $# -gt 0 ]; do
            case "$1" in
                --lan) HOST="0.0.0.0"; shift ;;
                --host) HOST="$2"; shift 2 ;;
                --port) PORT="$2"; shift 2 ;;
                --code) CODE="$2"; shift 2 ;;
                *) shift ;;
            esac
        done
        exec $PYTHON_CMD "$LIB_DIR/relay_server.py" --campaign-dir "$CDIR" \
            --host "$HOST" --port "$PORT" ${CODE:+--code "$CODE"}
        ;;
    drain|pending|post|status|feed|say)
        $PYTHON_CMD "$LIB_DIR/relay_manager.py" "$ACTION" "$@"
        ;;
    stop)
        # Read the pid straight from the server-state file (no envelope to unwrap).
        PID=$($PYTHON_CMD -c "import json,io,sys
try:
    print(json.load(io.open(sys.argv[1], encoding='utf-8')).get('pid',''))
except Exception:
    print('')" "$CDIR/relay/server.json" 2>/dev/null)
        if [ -n "$PID" ]; then
            # taskkill for native Windows python; kill as the POSIX fallback.
            if command -v taskkill >/dev/null 2>&1 && taskkill //PID "$PID" //F >/dev/null 2>&1; then
                echo "Stopped relay server (pid $PID)."
            elif kill "$PID" 2>/dev/null; then
                echo "Stopped relay server (pid $PID)."
            else
                echo "Could not signal pid $PID (already stopped?)."
            fi
            rm -f "$CDIR/relay/server.json"
        else
            echo "No running relay server recorded."
        fi
        ;;
    -h|--help|"")
        echo "Online-multiplayer relay bridge"
        echo "Usage: gm-relay.sh <serve|drain|pending|post|status|stop> [args]"
        echo ""
        echo "  serve [--lan] [--port N] [--code WORD]  Start the browser relay"
        echo "  drain                                   Pull new player actions (GM, each beat)"
        echo "  pending                                 Show queued actions (no consume)"
        echo "  post \"<narration>\" [--image FILE.png]   Send narration to players"
        echo "  status                                  URL, code, pending, seats"
        echo "  stop                                    Stop the server"
        echo ""
        echo "First: gm-session.sh multiplayer on  &&  gm-party.sh add \"<player>\" ..."
        ;;
    *)
        echo "Unknown action: $ACTION"
        echo "Valid: serve, drain, pending, post, status, stop"
        exit 1
        ;;
esac
