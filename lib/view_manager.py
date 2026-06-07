#!/usr/bin/env python3
"""
View manager — the canvas.

The canvas is a persistent second-pane surface the GM can *draw* into: maps,
scene art, spatial state that would otherwise vanish on the next turn.

Two halves live here:
  WRITE — ``ViewManager(EntityManager)`` persists the agent-authored scene to
          ``view.json`` (guarded by an active campaign).
  READ  — module-level ``resolve_campaign_dir`` / ``load_state`` / ``compose_frame``
          turn campaign state + the scene into a framed ASCII/ANSI panel. The read
          path must NOT use EntityManager, whose __init__ *raises* with no campaign;
          it resolves the dir directly and degrades to a placeholder instead.

view.json = {"title": str, "body": str, "updated": ISO8601}
Only the agent-authored scene lives here; the PARTY/HERE panels are derived live
from character.json / npcs.json / locations.json / campaign-overview.json — never
stored stale. (The COMBAT panel and the live watch loop are later canvas tickets.)
"""

import re
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime, timezone

# Add lib directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from entity_manager import EntityManager
from campaign_manager import CampaignManager

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


# ---------------------------------------------------------------------------
# READ PATH — campaign-dir resolution + safe state load (no EntityManager).
# ---------------------------------------------------------------------------

# The files the canvas reads, mapped state-key -> filename. Each is loaded
# defensively: a missing or malformed file degrades to {} so the render never
# crashes mid-scene. (Explicit map, not name-mangling — "overview" and "combat"
# don't match their filenames.)
_STATE_FILES = {
    "view": "view.json",
    "character": "character.json",
    "npcs": "npcs.json",
    "locations": "locations.json",
    "overview": "campaign-overview.json",
    "combat": "combat_state.json",
}


def resolve_campaign_dir(world_state_dir: str = "world-state"):
    """Return the active campaign dir as a Path, or None if none is active.

    Uses CampaignManager directly (returns None gracefully) — never
    EntityManager, whose __init__ raises when no campaign is set.
    """
    return CampaignManager(world_state_dir).get_active_campaign_dir()


def load_state(campaign_dir) -> dict:
    """Safe-load the canvas's source files from a campaign dir.

    Every read is wrapped — a missing/corrupt file becomes {} rather than an
    exception. Returns a dict keyed by short name (view/character/npcs/...).
    """
    base = Path(campaign_dir)

    def _safe(filename):
        try:
            return json.loads((base / filename).read_text(encoding="utf-8"))
        except Exception:
            return {}

    state = {key: _safe(fn) for key, fn in _STATE_FILES.items()}
    state["_active"] = True
    return state


# ---------------------------------------------------------------------------
# RENDER — frame state into an ASCII/ANSI panel. 256-color palette + HP-bar
# thresholds ported verbatim from tools/gm-statusline.sh.
# ---------------------------------------------------------------------------

GREEN = "\033[38;5;42m"
AMBER = "\033[38;5;214m"
RED = "\033[38;5;203m"
TEAL = "\033[38;5;51m"
GOLD = "\033[38;5;220m"
DIM = "\033[38;5;244m"
FAINT = "\033[38;5;238m"
BOLD = "\033[1m"
RESET = "\033[0m"

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def visible_len(s: str) -> int:
    """Length of a string ignoring ANSI color escapes (for padding math)."""
    return len(_ANSI_RE.sub("", s))


def clip_visible(s: str, n: int) -> str:
    """Clip to n VISIBLE chars, preserving escape sequences; append RESET.

    Color codes are zero-width and copied through; only printable chars count
    toward n. RESET is appended whenever the string carried color or was cut,
    so a clipped line never bleeds its color into the frame border.
    """
    if n <= 0:
        return ""
    out, count, i, truncated, had_escape = [], 0, 0, False, False
    while i < len(s):
        m = _ANSI_RE.match(s, i)
        if m:
            out.append(m.group())
            had_escape = True
            i = m.end()
            continue
        if count >= n:
            truncated = True
            break
        out.append(s[i])
        count += 1
        i += 1
    res = "".join(out)
    if had_escape or truncated:
        res += RESET
    return res


def _cell(s: str, width: int) -> str:
    """Clip then right-pad a string to exactly `width` visible columns."""
    s = clip_visible(s, width)
    return s + " " * (width - visible_len(s))


def _center(s: str, width: int) -> str:
    """Center a string within `width` visible columns."""
    pad = width - visible_len(s)
    if pad <= 0:
        return clip_visible(s, width)
    left = pad // 2
    return " " * left + s + " " * (pad - left)


def framed_line(content: str, cols: int) -> str:
    """A full-width content row: │ <content padded to inner width> │."""
    inner = cols - 4
    return f"{FAINT}│{RESET} {_cell(content, inner)} {FAINT}│{RESET}"


def top_border(cols: int) -> str:
    return f"{FAINT}╭{'─' * (cols - 2)}╮{RESET}"


def bottom_border(cols: int) -> str:
    return f"{FAINT}╰{'─' * (cols - 2)}╯{RESET}"


def hrule(cols: int, label: str = None) -> str:
    """A full-width labeled section divider: ├─ LABEL ───────────┤."""
    inner = cols - 2
    if label:
        plain = f"─ {label} "
        fill = max(0, inner - len(plain))
        mid = f"{FAINT}─ {TEAL}{BOLD}{label}{RESET}{FAINT} " + "─" * fill
        return f"{FAINT}├{mid}┤{RESET}"
    return f"{FAINT}├{'─' * inner}┤{RESET}"


def hp_bar(cur, mx, width: int = 10) -> str:
    """Colored HP bar — thresholds match gm-statusline.sh (≥50 green, ≥25 amber, else red)."""
    try:
        cur = int(cur)
        mx = int(mx)
    except (TypeError, ValueError):
        cur, mx = 0, 0
    if mx > 0:
        pct = cur * 100 // mx
        filled = cur * width // mx
    else:
        pct, filled = 0, 0
    filled = max(0, min(width, filled))
    empty = width - filled
    color = GREEN if pct >= 50 else AMBER if pct >= 25 else RED
    return f"{color}{'█' * filled}{'░' * empty}{RESET}"


def _relative(ts: str) -> str:
    """Humanize an ISO8601 timestamp as a relative 'Xs/Xm/Xh/Xd ago'."""
    if not ts:
        return "never"
    try:
        t = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        delta = (datetime.now(timezone.utc) - t).total_seconds()
    except Exception:
        return ts
    delta = max(0, delta)
    if delta < 60:
        return f"{int(delta)}s ago"
    if delta < 3600:
        return f"{int(delta // 60)}m ago"
    if delta < 86400:
        return f"{int(delta // 3600)}h ago"
    return f"{int(delta // 86400)}d ago"


def _party_rows(state: dict) -> list:
    """Build PARTY panel rows: the player, then every is_party_member NPC."""
    char = state.get("character") or {}
    rows = []
    if char:
        hp = char.get("hp") or {}
        cur, mx = hp.get("current", 0), hp.get("max", 0)
        name = char.get("name", "?")
        meta = " ".join(
            str(x) for x in (f"Lv{char.get('level', 1)}", char.get("race"), char.get("class")) if x
        )
        row = f"{TEAL}⚔ {BOLD}{name}{RESET} {DIM}{meta}{RESET} {hp_bar(cur, mx)} {cur}/{mx}"
        conds = char.get("conditions") or []  # handles conditions: null
        if conds:
            row += f"  {AMBER}({', '.join(conds)}){RESET}"
        rows.append(row)

    for nm, nd in (state.get("npcs") or {}).items():
        if not isinstance(nd, dict) or not nd.get("is_party_member"):
            continue
        sheet = nd.get("character_sheet")
        if not sheet:
            rows.append(f"{DIM}• {nm}{RESET}")  # no sheet → name only, no bar
            continue
        hp = sheet.get("hp") or {}
        cur, mx = hp.get("current", 0), hp.get("max", 0)
        rows.append(
            f"{DIM}•{RESET} {BOLD}{nm}{RESET} {DIM}Lv{sheet.get('level', 1)}{RESET} "
            f"{hp_bar(cur, mx)} {cur}/{mx}"
        )
    return rows or [f"{FAINT}(no party){RESET}"]


def _here_rows(state: dict) -> list:
    """Build HERE panel rows: current location + its connections."""
    over = state.get("overview") or {}
    char = state.get("character") or {}
    loc = (over.get("player_position") or {}).get("current_location") or char.get(
        "current_location"
    ) or "Unknown"
    rows = [f"{AMBER}{BOLD}{loc}{RESET}"]
    locdata = (state.get("locations") or {}).get(loc) or {}
    conns = locdata.get("connections") or []
    if conns:
        for c in conns:
            to = c.get("to", "?") if isinstance(c, dict) else str(c)
            path = c.get("path", "") if isinstance(c, dict) else ""
            tail = f" {FAINT}({path}){RESET}" if path else ""
            rows.append(f"{DIM}→{RESET} {to}{tail}")
    else:
        rows.append(f"{FAINT}(no known exits){RESET}")
    return rows


def _combat_rows(combat: dict) -> list:
    """Build COMBAT panel rows from combat_state.json, ordered by initiative.

    The active turn (turn_index) is marked with ▸; sides are color-tagged
    (enemy red, ally/player green). Empty/absent combat → caller hides the panel.
    """
    combatants = combat.get("combatants") or []
    ti = combat.get("turn_index", 0)
    # Mark the active combatant by object identity so duplicate names/ties stay
    # correct even after we re-sort a copy by initiative.
    active = combatants[ti] if 0 <= ti < len(combatants) else None
    ordered = sorted(combatants, key=lambda c: c.get("initiative", 0), reverse=True)

    rows = []
    for c in ordered:
        marker = f"{GOLD}▸{RESET}" if c is active else " "
        name = c.get("name", "?")
        cur, mx = c.get("hp_current", 0), c.get("hp_max", 0)
        side = c.get("side", "enemy")
        side_c = RED if side == "enemy" else GREEN
        conds = c.get("conditions") or []
        cond = f" {AMBER}({', '.join(conds)}){RESET}" if conds else ""
        dead = f" {RED}💀{RESET}" if isinstance(cur, int) and cur <= 0 else ""
        rows.append(
            f"{marker} {BOLD}{name}{RESET} {hp_bar(cur, mx)} {cur}/{mx} "
            f"{side_c}[{side}]{RESET}{cond}{dead}"
        )
    return rows


def _two_col_divider(cols: int, lw: int, rw: int, left_label: str, right_label: str, junction: str) -> str:
    """A column divider with a junction (┬ to open, ┴ to close) and two labels."""
    def seg(label, span):
        if label:
            plain = f"─ {label} "
            fill = max(0, span - len(plain))
            return f"─ {TEAL}{BOLD}{label}{RESET}{FAINT} " + "─" * fill
        return "─" * span
    left = seg(left_label, lw + 2)
    right = seg(right_label, rw + 2)
    return f"{FAINT}├{left}{junction}{right}┤{RESET}"


def compose_frame(state: dict, cols: int, rows: int) -> str:
    """Render campaign state + the authored scene into one framed panel string.

    Layout: header (title · clock) → SCENE → PARTY|HERE (side-by-side ≥72 cols,
    else stacked) → footer (updated relative). Every emitted line is exactly
    `cols` visible columns wide. No active campaign → centered placeholder.
    """
    cols = max(40, min(200, cols))
    rows = max(8, rows)

    if not state or not state.get("_active"):
        return _placeholder(cols, rows)

    view = state.get("view") or {}
    over = state.get("overview") or {}
    title = view.get("title") or "Untitled Scene"
    clock = " · ".join(x for x in (over.get("current_date", ""), over.get("time_of_day", "")) if x)

    # --- head: top border + header + SCENE divider --------------------------
    head = [top_border(cols)]
    inner = cols - 4
    header = f"{TEAL}◆ {BOLD}{title}{RESET}"
    right = f"{DIM}{clock}{RESET}"
    gap = inner - visible_len(header) - visible_len(right)
    if gap < 1:
        header = clip_visible(header, max(0, inner - visible_len(right) - 1))
        gap = inner - visible_len(header) - visible_len(right)
    head.append(framed_line(header + " " * max(0, gap) + right, cols))
    head.append(hrule(cols, label="SCENE"))

    # --- tail: PARTY/HERE panels + footer + bottom border -------------------
    party = _party_rows(state)
    here = _here_rows(state)
    footer = framed_line(f"{FAINT}updated {_relative(view.get('updated', ''))}{RESET}", cols)

    if cols >= 72:
        # Side-by-side columns sharing a central │ separator.
        lw = (cols - 7) // 2
        rw = cols - 7 - lw
        tail = [_two_col_divider(cols, lw, rw, "PARTY", "HERE", "┬")]
        for i in range(max(len(party), len(here))):
            l = party[i] if i < len(party) else ""
            r = here[i] if i < len(here) else ""
            tail.append(f"{FAINT}│{RESET} {_cell(l, lw)} {FAINT}│{RESET} {_cell(r, rw)} {FAINT}│{RESET}")
        tail.append(_two_col_divider(cols, lw, rw, "", "", "┴"))
    else:
        tail = [hrule(cols, label="PARTY")]
        tail += [framed_line(r, cols) for r in party]
        tail.append(hrule(cols, label="HERE"))
        tail += [framed_line(r, cols) for r in here]

    # COMBAT panel — only when a fight is active; sits above PARTY/HERE so the
    # most urgent state reads first. Hidden otherwise (layout unchanged).
    combat = state.get("combat") or {}
    if combat.get("combatants"):
        combat_block = [hrule(cols, label=f"COMBAT · Round {combat.get('round', 1)}")]
        combat_block += [framed_line(r, cols) for r in _combat_rows(combat)]
        tail = combat_block + tail

    tail.append(footer)
    tail.append(bottom_border(cols))

    # --- scene region fills the space between head and tail -----------------
    scene_h = rows - len(head) - len(tail)
    if scene_h < 1:
        scene_h = 1
    body = view.get("body") or ""
    body_lines = body.split("\n") if body else []
    scene = []
    if not body_lines:
        scene.append(framed_line(f"{FAINT}(no scene drawn — paint here with gm-view.sh scene){RESET}", cols))
    elif len(body_lines) <= scene_h:
        scene = [framed_line(ln, cols) for ln in body_lines]
    else:
        shown = body_lines[: scene_h - 1]
        hidden = len(body_lines) - len(shown)
        scene = [framed_line(ln, cols) for ln in shown]
        scene.append(framed_line(f"{DIM}… (+{hidden} lines){RESET}", cols))
    # Pad the scene region so the panels anchor at the bottom (cockpit feel).
    while len(scene) < scene_h:
        scene.append(framed_line("", cols))

    return "\n".join(head + scene + tail)


def _placeholder(cols: int, rows: int) -> str:
    """Centered placeholder shown when no campaign is active."""
    msg = f"{TEAL}⚔ DM{RESET} {DIM}— no active campaign{RESET} {FAINT}(/new-game or /import){RESET}"
    lines = [top_border(cols)]
    body_h = rows - 2
    pad_top = max(0, (body_h - 1) // 2)
    for _ in range(pad_top):
        lines.append(framed_line("", cols))
    lines.append(framed_line(_center(msg, cols - 4), cols))
    for _ in range(body_h - pad_top - 1):
        lines.append(framed_line("", cols))
    lines.append(bottom_border(cols))
    return "\n".join(lines)


def render() -> None:
    """One-shot render of the current canvas to stdout (no alt-screen)."""
    campaign_dir = resolve_campaign_dir()
    if campaign_dir is None:
        state = {"_active": False}
    else:
        state = load_state(campaign_dir)
    cols, rows = shutil.get_terminal_size((80, 24))
    print(compose_frame(state, cols, rows))


# ---------------------------------------------------------------------------
# WATCH — the live pane. A long-running, user-launched process (NOT an
# agent-called tool) that redraws the frame whenever campaign state changes.
# Polling, not inotify/watchdog: zero new deps, and the writer's atomic
# temp+rename means any single read is coherent.
# ---------------------------------------------------------------------------

# Terminal control sequences.
_ALT_ENTER = "\033[?1049h"  # switch to alternate screen buffer
_ALT_LEAVE = "\033[?1049l"  # restore the previous buffer (and scrollback)
_CURSOR_HIDE = "\033[?25l"
_CURSOR_SHOW = "\033[?25h"
_CURSOR_HOME = "\033[H"
_CLEAR_TO_END = "\033[J"

WATCH_POLL_SECONDS = 0.25


def _watch_signature(campaign_dir, cols, rows) -> str:
    """A cheap change-token: campaign + terminal size + mtime of each watched file.

    Any change flips the signature so the loop redraws; nothing changing means no
    redraw (no flicker, near-zero CPU). A missing file uses a '-' sentinel, so a
    file appearing/disappearing (e.g. combat starting) also flips it.
    """
    parts = [str(campaign_dir), str(cols), str(rows)]
    if campaign_dir is not None:
        base = Path(campaign_dir)
        for filename in _STATE_FILES.values():
            try:
                parts.append(str((base / filename).stat().st_mtime_ns))
            except OSError:
                parts.append("-")
    return "|".join(parts)


def run_watch(poll: float = WATCH_POLL_SECONDS) -> None:
    """Take over the pane and live-redraw the canvas until interrupted.

    Uses the alternate screen so the user's scrollback is untouched, and restores
    the cursor + buffer cleanly on Ctrl+C / SIGTERM / any exit.
    """
    import time
    import signal

    out = sys.stdout

    def _restore(*_):
        out.write(_CURSOR_SHOW + _ALT_LEAVE)
        out.flush()
        raise SystemExit(0)

    signal.signal(signal.SIGINT, _restore)
    signal.signal(signal.SIGTERM, _restore)

    out.write(_ALT_ENTER + _CURSOR_HIDE)
    out.flush()
    last_sig = None
    try:
        while True:
            campaign_dir = resolve_campaign_dir()
            cols, rows = shutil.get_terminal_size((80, 24))
            sig = _watch_signature(campaign_dir, cols, rows)
            if sig != last_sig:
                last_sig = sig
                if campaign_dir is None:
                    state = {"_active": False}
                else:
                    state = load_state(campaign_dir)
                frame = compose_frame(state, cols, rows)
                # Home → draw → clear-to-end: overwrite in place, wipe any taller
                # previous frame's leftovers. No full clear, so no flicker.
                out.write(_CURSOR_HOME + frame + _CLEAR_TO_END)
                out.flush()
            time.sleep(poll)
    finally:
        out.write(_CURSOR_SHOW + _ALT_LEAVE)
        out.flush()


def main():
    """CLI interface for the canvas."""
    import argparse

    parser = argparse.ArgumentParser(description="Canvas view panel")
    subparsers = parser.add_subparsers(dest="action", help="Action to perform")

    # scene — body comes from stdin (avoids multi-line ASCII shell-escaping)
    scene_parser = subparsers.add_parser(
        "scene", help="Push a scene to the canvas (body read from stdin)"
    )
    scene_parser.add_argument("--title", default="", help="Scene title")

    # clear — blank the canvas but keep the file
    subparsers.add_parser("clear", help="Clear the canvas (keeps the file)")

    # render — one-shot framed panel to stdout (no active-campaign guard)
    subparsers.add_parser("render", help="Render the canvas panel to stdout")

    # watch — live, long-running pane (user-launched; no active-campaign guard)
    subparsers.add_parser("watch", help="Live-redraw the canvas pane (Ctrl+C to exit)")

    args = parser.parse_args()

    if not args.action:
        parser.print_help()
        sys.exit(1)

    if args.action == "render":
        render()
        return

    if args.action == "watch":
        run_watch()
        return

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
