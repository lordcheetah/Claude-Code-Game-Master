#!/usr/bin/env python3
"""
narration_log.py — record the ACTUAL played narration, beat by beat, so the
chronicle ebook can be built from real prose instead of only the end-of-session
summary.

Each recorded beat is one append-only JSONL line in the campaign's
narration-log.jsonl:

    {"id": N, "ts": ISO8601Z, "session": S, "location": "...",
     "text": "<the narration prose>", "images": ["file.png", ...]}

The GM records a beat as part of the core loop (PERSIST -> record -> NARRATE)
whenever preferences.record_narration is on (the default). chronicle.py buckets
these beats into chapters by the session-end timestamps in session-log.md and
interleaves the image plates at the point they were generated.

`ts` uses the same ISO-8601 Z form as the image gen-log (images/_gen-log.jsonl)
so beats and plates sort into one timeline. `location` and `session` auto-fill
from campaign state when the caller omits them, so recording a beat is a single
argument: the prose.

Kit-agnostic; no new dependencies.
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))


def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class NarrationLog:
    def __init__(self, campaign_dir):
        self.campaign_dir = Path(campaign_dir)
        self.path = self.campaign_dir / "narration-log.jsonl"

    @classmethod
    def for_active(cls, base_dir="world-state"):
        from campaign_manager import CampaignManager
        active = CampaignManager(base_dir).get_active_campaign_dir()
        if active is None:
            raise RuntimeError("No active campaign. Run /new-game or /import first.")
        return cls(active)

    # ---- read helpers -----------------------------------------------------

    def beats(self):
        """Every recorded beat, in file (chronological) order."""
        out = []
        if not self.path.exists():
            return out
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue  # tolerate a torn trailing line
        return out

    def count(self):
        return len(self.beats())

    def _last_id(self):
        # small per-campaign logs; a full scan is fine and torn-line tolerant
        last = 0
        for b in self.beats():
            try:
                last = max(last, int(b.get("id", 0)))
            except (TypeError, ValueError):
                pass
        return last

    def _current_location(self):
        try:
            ov = json.loads((self.campaign_dir / "campaign-overview.json")
                            .read_text(encoding="utf-8"))
            pos = ov.get("player_position") or {}
            if isinstance(pos, dict) and pos.get("current_location"):
                return pos["current_location"]
        except Exception:
            pass
        try:
            ch = json.loads((self.campaign_dir / "character.json")
                            .read_text(encoding="utf-8"))
            return ch.get("current_location") or ""
        except Exception:
            return ""

    def _session_number(self):
        """The in-progress session number = (# of ended sessions) + 1."""
        try:
            txt = (self.campaign_dir / "session-log.md").read_text(encoding="utf-8")
            return len(re.findall(r"^### Session Ended:", txt, flags=re.MULTILINE)) + 1
        except Exception:
            return 1

    # ---- record -----------------------------------------------------------

    def record(self, text, location=None, session=None, images=None):
        """Append one narration beat. Returns the stored record.

        `text` is the beat's narrative prose (the story as told) — NOT the status
        bar or the numbered action menu. `location`/`session` auto-fill from
        campaign state when omitted. `images` are plate filenames generated in
        this beat (optional; the chronicle also places plates by timestamp)."""
        text = (text or "").strip()
        if not text:
            raise ValueError("Refusing to record an empty narration beat.")
        rec = {
            "id": self._last_id() + 1,
            "ts": _now_iso(),
            "session": int(session) if session is not None else self._session_number(),
            "location": location or self._current_location(),
            "text": text,
            "images": [os.path.basename(i) for i in (images or []) if i],
        }
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
        return rec


# ------------------------------ CLI --------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="Record the played narration for the chronicle ebook")
    sub = ap.add_subparsers(dest="action")

    p = sub.add_parser("record", help="Record one narration beat (the prose as told)")
    p.add_argument("text", nargs="?", help="Beat prose (or read from stdin if omitted)")
    p.add_argument("--location", help="Override location (default: current location)")
    p.add_argument("--session", type=int, help="Override session number (default: current)")
    p.add_argument("--image", action="append", default=[],
                   help="Plate filename generated in this beat (repeatable)")

    sub.add_parser("list", help="List recorded beats (id · session · location · preview)")
    sub.add_parser("count", help="How many beats are recorded")

    from cli_output import wants_json, strip_json_flag, emit
    json_mode = wants_json()
    args = ap.parse_args(strip_json_flag(sys.argv[1:]))
    if not args.action:
        ap.print_help()
        sys.exit(1)

    log = NarrationLog.for_active()

    if args.action == "record":
        text = args.text
        if text is None:
            text = "" if sys.stdin.isatty() else sys.stdin.read()
        try:
            rec = log.record(text, location=args.location, session=args.session,
                             images=args.image)
        except ValueError as e:
            print(f"[ERROR] {e}", file=sys.stderr)
            sys.exit(1)
        if json_mode:
            emit(rec, json_mode=True)
        else:
            img = f", {len(rec['images'])} image(s)" if rec["images"] else ""
            print(f"Recorded beat #{rec['id']} (session {rec['session']}, "
                  f"{rec['location'] or 'unknown'}{img}).")

    elif args.action == "count":
        n = log.count()
        emit({"count": n}, json_mode=True) if json_mode else print(f"{n} beat(s) recorded.")

    elif args.action == "list":
        beats = log.beats()
        if json_mode:
            emit({"beats": beats}, json_mode=True)
        elif not beats:
            print("(no narration recorded yet — the GM records beats as you play "
                  "when record_narration is on)")
        else:
            for b in beats:
                prev = " ".join((b.get("text") or "").split())[:80]
                print(f"  #{b.get('id')}  s{b.get('session')}  "
                      f"{(b.get('location') or '?')[:24]:24}  {prev}")


if __name__ == "__main__":
    main()
