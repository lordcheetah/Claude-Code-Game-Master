#!/usr/bin/env python3
"""
View manager — the write half of the canvas.

The canvas is a persistent second-pane surface the GM can *draw* into: maps,
scene art, spatial state that would otherwise vanish on the next turn. This
module owns the write path only — it persists the agent-authored scene to
``view.json``. The read/watch/render path (auto-derived PARTY/HERE/COMBAT
panels) is added by later canvas tickets and must NOT use EntityManager, whose
__init__ raises when no campaign is active.

view.json = {"title": str, "body": str, "updated": ISO8601}
Only the agent-authored scene lives here; panels are derived live, never stored.
"""

import sys
from pathlib import Path

# Add lib directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from entity_manager import EntityManager

# Keep the canvas file bounded — a runaway scene shouldn't bloat campaign state.
MAX_BODY_CHARS = 64 * 1024

# C0 control chars to PRESERVE in scene bodies: tab, newline, and ESC (so ANSI
# color sequences survive). Everything else below 0x20 (CR, BEL, etc.) is dropped.
_KEEP_CTRL = {0x09, 0x0A, 0x1B}


def sanitize_body(text: str) -> str:
    """Clean a raw scene body for safe persistence and replay.

    - Drops a single trailing newline (stdin almost always appends one).
    - Strips C0 control chars < 0x20 except tab/newline/ESC — keeps ANSI color,
      drops CR/BEL and other terminal-hostile bytes.
    - Caps length at ~64 KB so the canvas file stays bounded.
    """
    if text.endswith("\n"):
        text = text[:-1]
    cleaned = "".join(c for c in text if ord(c) >= 0x20 or ord(c) in _KEEP_CTRL)
    if len(cleaned) > MAX_BODY_CHARS:
        cleaned = cleaned[:MAX_BODY_CHARS]
    return cleaned


class ViewManager(EntityManager):
    """Write the agent-authored scene to the active campaign's canvas."""

    VIEW_FILE = "view.json"

    def set_scene(self, title: str, body: str) -> bool:
        """Push a freeform scene onto the canvas.

        Persists ``{title, body, updated}`` atomically (temp+rename via
        json_ops). The body is sanitized; the title is stored verbatim.
        """
        data = {
            "title": title,
            "body": sanitize_body(body),
            "updated": self.json_ops.get_timestamp(),
        }
        return self.json_ops.save_json(self.VIEW_FILE, data)

    def clear_scene(self) -> bool:
        """Empty the canvas but keep the file.

        The watcher then shows a clean placeholder rather than a "no view"
        error — the canvas stays present, just blank.
        """
        data = {
            "title": "",
            "body": "",
            "updated": self.json_ops.get_timestamp(),
        }
        return self.json_ops.save_json(self.VIEW_FILE, data)


def main():
    """CLI interface for the canvas writer."""
    import argparse

    parser = argparse.ArgumentParser(description="Canvas view writer")
    subparsers = parser.add_subparsers(dest="action", help="Action to perform")

    # scene — body comes from stdin (avoids multi-line ASCII shell-escaping)
    scene_parser = subparsers.add_parser(
        "scene", help="Push a scene to the canvas (body read from stdin)"
    )
    scene_parser.add_argument("--title", default="", help="Scene title")

    # clear — blank the canvas but keep the file
    subparsers.add_parser("clear", help="Clear the canvas (keeps the file)")

    args = parser.parse_args()

    if not args.action:
        parser.print_help()
        sys.exit(1)

    manager = ViewManager()

    if args.action == "scene":
        body = sys.stdin.read()
        if not manager.set_scene(args.title, body):
            sys.exit(1)
        print(f"[SUCCESS] Scene set: {args.title or '(untitled)'}")

    elif args.action == "clear":
        if not manager.clear_scene():
            sys.exit(1)
        print("[SUCCESS] Canvas cleared")


if __name__ == "__main__":
    main()
