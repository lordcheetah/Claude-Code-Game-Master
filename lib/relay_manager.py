#!/usr/bin/env python3
"""
relay_manager.py — the file-based bridge for online multiplayer (Phase 2).

The online relay never touches Claude Code internals. It moves text through two
append-only logs in the campaign's relay/ directory:

    relay/inbox.jsonl    player actions  (single writer: the relay server)
    relay/inbox.cursor   last-drained id (single writer: the GM `drain`)
    relay/outbox.jsonl   GM narration    (single writer: the GM `post`)
    relay/server.json    live server info {pid, host, port, code, url}

Because every file has exactly ONE writer, there is no write contention and no
locking is needed — the same single-writer discipline that lets the whole
multiplayer design avoid concurrency control. The GM (one Claude Code session)
`drain`s new player actions at the start of each beat and `post`s its narration
for remote players to read; the server relays both directions over HTTP.

Seats come from players.json (see party_manager). A player may only act from a
seat the GM has created.
"""

import os
import sys
import json
import threading
import argparse
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _age_secs(iso):
    """Seconds since an ISO timestamp, or a large number if unparseable."""
    try:
        then = datetime.fromisoformat(iso)
        if then.tzinfo is None:
            then = then.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - then).total_seconds()
    except (TypeError, ValueError):
        return 1e9


def _slug(s):
    return (s or "").strip().lower().replace(" ", "-")


class RelayManager:
    def __init__(self, campaign_dir):
        self.campaign_dir = Path(campaign_dir)
        self.relay_dir = self.campaign_dir / "relay"
        self.relay_dir.mkdir(parents=True, exist_ok=True)
        self.inbox = self.relay_dir / "inbox.jsonl"
        self.cursor = self.relay_dir / "inbox.cursor"
        self.outbox = self.relay_dir / "outbox.jsonl"
        self.server_state = self.relay_dir / "server.json"
        self.presence_file = self.relay_dir / "presence.json"
        # Guards concurrent presence writes from the server's request threads
        # (one process, many threads). Cross-process is fine: only the server
        # writes presence.json; the GM side only reads it.
        self._presence_lock = threading.Lock()

    @classmethod
    def for_active(cls, base_dir="world-state"):
        from campaign_manager import CampaignManager
        active = CampaignManager(base_dir).get_active_campaign_dir()
        if active is None:
            raise RuntimeError("No active campaign. Run /new-game or /import first.")
        return cls(active)

    # ---- low-level append-only log helpers --------------------------------

    @staticmethod
    def _read_lines(path):
        out = []
        if not path.exists():
            return out
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                # tolerate a torn trailing line from a concurrent reader
                continue
        return out

    @staticmethod
    def _last_id(path):
        last = 0
        for rec in RelayManager._read_lines(path):
            try:
                last = max(last, int(rec.get("id", 0)))
            except (TypeError, ValueError):
                pass
        return last

    @staticmethod
    def _append(path, obj):
        # One complete line, one write — atomic enough for a single-writer log.
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
            f.flush()

    # ---- inbox (players -> GM) --------------------------------------------

    def submit(self, player, text, seat=None):
        """Append a player's action to the inbox. Called by the relay server."""
        rec = {"id": self._last_id(self.inbox) + 1, "ts": _now_iso(),
               "player": player, "seat": seat or _slug(player),
               "text": (text or "").strip()}
        self._append(self.inbox, rec)
        return rec

    def _cursor_val(self):
        try:
            return int(self.cursor.read_text(encoding="utf-8").strip())
        except (ValueError, IOError, FileNotFoundError):
            return 0

    def pending(self):
        """Inbox actions not yet drained (without consuming them)."""
        cur = self._cursor_val()
        return [r for r in self._read_lines(self.inbox) if int(r.get("id", 0)) > cur]

    def drain(self):
        """Return new player actions and advance the cursor past them. The GM
        calls this at the start of each beat. Single writer of the cursor file."""
        new = self.pending()
        if new:
            maxid = max(int(r.get("id", 0)) for r in new)
            tmp = self.cursor.with_suffix(".tmp")
            tmp.write_text(str(maxid), encoding="utf-8")
            tmp.replace(self.cursor)
        return new

    # ---- outbox (GM -> players) -------------------------------------------

    def post(self, text, kind="narration", images=None):
        """Append GM narration for remote players. Single writer (the GM)."""
        rec = {"id": self._last_id(self.outbox) + 1, "ts": _now_iso(),
               "kind": kind, "text": (text or "").rstrip(),
               "images": list(images or [])}
        self._append(self.outbox, rec)
        return rec

    def feed(self, since=0):
        """Outbox entries with id > since (players poll this)."""
        try:
            since = int(since)
        except (TypeError, ValueError):
            since = 0
        return [r for r in self._read_lines(self.outbox) if int(r.get("id", 0)) > since]

    # ---- seats & server state ---------------------------------------------

    def seats(self):
        """Valid seats (player -> character) from players.json."""
        try:
            from party_manager import PartyManager
            roster = PartyManager(str(self.campaign_dir)).list_seats()
        except Exception:
            roster = {"seats": []}
        return [{"player": s.get("player"), "slug": s.get("slug"),
                 "character": s.get("character"), "status": s.get("status", "alive"),
                 "control": s.get("control", "self"),
                 "controlled_by": s.get("controlled_by"),
                 "absence_reason": s.get("absence_reason")}
                for s in roster.get("seats", [])]

    def match_seat(self, who):
        """Resolve a joining name to a seat (by player name, slug, or character)."""
        t = _slug(who)
        for s in self.seats():
            if _slug(s.get("player")) == t or _slug(s.get("slug")) == t \
                    or _slug(s.get("character")) == t:
                return s
        return None

    def write_server_state(self, **kw):
        kw["updated"] = _now_iso()
        self.server_state.write_text(json.dumps(kw, ensure_ascii=False, indent=2),
                                     encoding="utf-8")

    def read_server_state(self):
        try:
            return json.loads(self.server_state.read_text(encoding="utf-8"))
        except (IOError, json.JSONDecodeError, FileNotFoundError):
            return {}

    def clear_server_state(self):
        try:
            self.server_state.unlink()
        except FileNotFoundError:
            pass

    # ---- presence (who is actually connected) -----------------------------

    ACTIVE_WINDOW = 20  # seconds; clients poll every ~2s, so 20s is generous

    def touch_presence(self, seat, player=None):
        """Stamp a seat as seen just now. Called by the server on join/say/poll.
        Single-writer file, thread-locked against the server's own threads."""
        if not seat:
            return
        with self._presence_lock:
            data = {}
            try:
                data = json.loads(self.presence_file.read_text(encoding="utf-8"))
            except (IOError, json.JSONDecodeError, FileNotFoundError):
                data = {}
            data[seat] = {"player": player or data.get(seat, {}).get("player") or seat,
                          "last_seen": _now_iso()}
            tmp = self.presence_file.with_suffix(".tmp")
            tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            tmp.replace(self.presence_file)

    def read_presence(self):
        try:
            return json.loads(self.presence_file.read_text(encoding="utf-8"))
        except (IOError, json.JSONDecodeError, FileNotFoundError):
            return {}

    def presence_view(self):
        """Per-seat view for the GM: is a human connected, and have they acted in
        the current (undrained) beat? 'waiting' = connected but no queued action
        yet — the seats loose timing should wait for. Unmanned seats have no human."""
        pres = self.read_presence()
        pending_seats = {r.get("seat") for r in self.pending()}
        out = []
        for s in self.seats():
            slug = s.get("slug")
            seen = pres.get(slug, {}).get("last_seen")
            connected = seen is not None and _age_secs(seen) <= self.ACTIVE_WINDOW
            has_pending = slug in pending_seats
            # Only WAIT (loose timing) for a live, self-driven, connected player who
            # hasn't acted. GM/delegated/written-out seats are handled, not waited on.
            self_driven = s.get("control", "self") == "self"
            out.append({**s, "connected": connected, "last_seen": seen,
                        "has_pending": has_pending,
                        "waiting": (connected and not has_pending
                                    and s.get("status") == "alive" and self_driven)})
        return out

    def status(self):
        st = self.read_server_state()
        return {"server": st, "pending": len(self.pending()),
                "outbox_count": self._last_id(self.outbox),
                "seats": self.seats(), "presence": self.presence_view()}


# ------------------------------ CLI --------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Online-multiplayer relay bridge")
    sub = ap.add_subparsers(dest="action")

    sub.add_parser("drain", help="Pull new player actions (advances the cursor)")
    sub.add_parser("pending", help="Show queued player actions without consuming")

    p = sub.add_parser("post", help="Post GM narration to remote players")
    p.add_argument("text", help="Narration text")
    p.add_argument("--image", action="append", default=[],
                   help="Image filename (basename in the campaign images/) to attach; repeatable")

    p = sub.add_parser("say", help="(local/testing) inject a player action")
    p.add_argument("player")
    p.add_argument("text")

    sub.add_parser("status", help="Server + queue status")
    sub.add_parser("who", help="Who is connected, and who still owes an action")
    sub.add_parser("feed", help="Dump the outbox (what players have seen)")

    from cli_output import wants_json, strip_json_flag, emit
    json_mode = wants_json()
    args = ap.parse_args(strip_json_flag(sys.argv[1:]))
    if not args.action:
        ap.print_help()
        sys.exit(1)

    m = RelayManager.for_active()

    if args.action == "drain":
        new = m.drain()
        if json_mode:
            emit({"actions": new}, json_mode=True)
        elif not new:
            print("(no new player actions)")
        else:
            print(f"{len(new)} new player action(s):")
            for r in new:
                print(f"  [{r.get('player')}] {r.get('text')}")
    elif args.action == "pending":
        new = m.pending()
        if json_mode:
            emit({"actions": new}, json_mode=True)
        else:
            print(f"{len(new)} pending action(s).")
            for r in new:
                print(f"  [{r.get('player')}] {r.get('text')}")
    elif args.action == "post":
        rec = m.post(args.text, images=[os.path.basename(i) for i in args.image])
        print(f"Posted to relay (#{rec['id']}"
              + (f", {len(rec['images'])} image(s)" if rec['images'] else "") + ").")
    elif args.action == "say":
        seat = m.match_seat(args.player)
        rec = m.submit(args.player, args.text, seat=seat.get("slug") if seat else None)
        print(f"Injected action #{rec['id']} from {args.player}"
              + ("" if seat else "  (warning: not a known seat)"))
    elif args.action == "status":
        st = m.status()
        if json_mode:
            emit(st, json_mode=True)
        else:
            srv = st["server"]
            if srv.get("url"):
                print(f"Relay server: {srv.get('url')}  (code: {srv.get('code') or '(none)'}, pid {srv.get('pid')})")
            else:
                print("Relay server: not running (start with gm-relay.sh serve).")
            print(f"Pending player actions: {st['pending']}")
            seat_bits = []
            for s in st["seats"]:
                label = f"{s['player']}→{s['character']}"
                if s.get("status") != "alive":
                    label += f" [{s['status']}]"
                seat_bits.append(label)
            print("Seats: " + (", ".join(seat_bits) or "(none)"))
    elif args.action == "who":
        view = m.presence_view()
        if json_mode:
            emit({"presence": view}, json_mode=True)
        else:
            waiting = [v for v in view if v["waiting"]]
            by_slug = {v.get("slug"): v.get("player") for v in view}
            for v in view:
                control = v.get("control", "self")
                if v.get("status") != "alive":
                    dot, note = "✗", "fallen"
                elif control == "gm":
                    dot, note = "◐", "player away — GM runs as NPC"
                elif control == "delegate":
                    dot, note = "◐", f"player away — run by {by_slug.get(v.get('controlled_by'), '?')}"
                elif control == "away":
                    dot, note = "○", f"offscreen — {v.get('absence_reason') or 'absent'}"
                elif not v["connected"]:
                    dot, note = "○", "not connected — set away? (gm-party.sh away ...)"
                elif v["has_pending"]:
                    dot, note = "●", "✓ acted this beat"
                else:
                    dot, note = "●", "… waiting on their action"
                print(f"  {dot} {v['player']} → {v.get('character') or '(no character)'}   {note}")
            if waiting:
                print(f"\nLoose timing: still waiting on {', '.join(v['player'] for v in waiting)} "
                      f"before you resolve the beat.")
            else:
                print("\nEveryone connected has acted — safe to resolve the beat.")
    elif args.action == "feed":
        for r in m.feed(0):
            tag = r.get("kind", "narration")
            print(f"#{r['id']} ({tag}): {r['text'][:200]}")


if __name__ == "__main__":
    main()
