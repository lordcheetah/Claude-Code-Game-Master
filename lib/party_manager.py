#!/usr/bin/env python3
"""
party_manager.py — the multiplayer seat roster (additive, opt-in).

When a campaign turns on multiplayer (preferences.multiplayer), several human
players share one table as PEERS. Each player owns a SEAT with its own character
sheet under players/<slug>/character.json — mirroring the campaign-isolation
pattern, so seats never contend on a shared file. This module owns the roster
(players.json) and the per-seat directories; the per-seat SHEET operations
(hp/xp/gold/conditions/kill) run through PlayerManager(player_slug=<slug>), which
already knows how to read/write players/<slug>/character.json.

Single-player is entirely unaffected: nothing here runs unless the campaign has
opted in and seats exist. The campaign-root character.json is never touched.

Roster shape (players.json):
    {
      "seats": [
        {"player": "Sam", "character": "Iren Calder", "slug": "sam",
         "status": "alive", "joined": "<iso>"}
      ],
      "spotlight": "sam"   # slug of the seat currently in focus, or null
    }
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))

from json_ops import JsonOperations
from character_schema import to_flat


def _slugify(name: str) -> str:
    return (name or "").strip().lower().replace(" ", "-")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hp_bar(hp, max_hp, width: int = 12) -> str:
    """Compact HP bar matching the project's health glyphs."""
    try:
        hp = int(hp)
        max_hp = int(max_hp)
    except (TypeError, ValueError):
        return ""
    if max_hp <= 0:
        return ""
    filled = max(0, min(width, round(width * hp / max_hp)))
    ratio = hp / max_hp
    mark = "✓" if ratio > 0.5 else ("⚠" if ratio > 0.25 else "⚠⚠")
    if hp <= 0:
        mark = "💀"
    return f"{'█' * filled}{'░' * (width - filled)} {hp}/{max_hp} {mark}"


class PartyManager:
    """Roster of human player seats for a multiplayer campaign.

    Takes an explicit campaign directory (NOT the base world-state dir) so it can
    be constructed both from an active-campaign CLI and directly by SessionManager
    (which already holds self.campaign_dir). Reads/writes are scoped to that dir.
    """

    ROSTER = "players.json"

    def __init__(self, campaign_dir):
        self.campaign_dir = Path(campaign_dir)
        self.json_ops = JsonOperations(str(self.campaign_dir))
        self.players_dir = self.campaign_dir / "players"

    @classmethod
    def for_active(cls, base_dir: str = "world-state"):
        """Construct against the active campaign (for the CLI path)."""
        from campaign_manager import CampaignManager
        active = CampaignManager(base_dir).get_active_campaign_dir()
        if active is None:
            raise RuntimeError("No active campaign. Run /new-game or /import first.")
        return cls(active)

    # ---- roster I/O -------------------------------------------------------

    def _load(self) -> dict:
        r = self.json_ops.load_json(self.ROSTER) or {}
        if not isinstance(r, dict):
            r = {}
        r.setdefault("seats", [])
        r.setdefault("spotlight", None)
        return r

    def _save(self, roster: dict) -> bool:
        return self.json_ops.save_json(self.ROSTER, roster)

    def _find(self, roster: dict, who: str):
        """Resolve a seat by player name or slug; returns the seat dict or None."""
        target = _slugify(who)
        for seat in roster["seats"]:
            if seat.get("slug") == target or _slugify(seat.get("player", "")) == target \
                    or _slugify(seat.get("character", "")) == target:
                return seat
        return None

    # ---- seat operations --------------------------------------------------

    def add_seat(self, player: str, character: str = None, character_json: str = None) -> dict:
        """Add (or update) a seat for a human player. Optionally seed the seat's
        character sheet from a JSON blob (normalized to the flat schema)."""
        if not player or not player.strip():
            raise ValueError("player name is required")
        roster = self._load()
        slug = _slugify(player)
        seat = self._find(roster, slug)
        if seat is None:
            seat = {"player": player.strip(), "character": character or "",
                    "slug": slug, "status": "alive", "control": "self",
                    # The player's standing wish for how to handle their absence.
                    # Defaults to a GM write-out; the player can change it (from
                    # their own client, or the GM on their behalf) to gm/delegate.
                    "absence_policy": {"mode": "write-out"},
                    "joined": _now_iso()}
            roster["seats"].append(seat)
        else:
            if character:
                seat["character"] = character
        if roster.get("spotlight") is None:
            roster["spotlight"] = slug
        self._save(roster)

        if character_json:
            self.set_sheet(slug, character_json)
            # keep the seat's character name in sync with the sheet
            sheet = self.get_sheet(slug) or {}
            if sheet.get("name"):
                seat["character"] = sheet["name"]
                self._save(roster)
        return seat

    def set_sheet(self, who: str, character_json) -> bool:
        """Write a seat's character sheet (players/<slug>/character.json), flat-normalized."""
        roster = self._load()
        seat = self._find(roster, who)
        slug = seat["slug"] if seat else _slugify(who)
        if isinstance(character_json, str):
            data = json.loads(character_json)
        else:
            data = character_json
        (self.players_dir / slug).mkdir(parents=True, exist_ok=True)
        ok = self.json_ops.save_json(f"players/{slug}/character.json", to_flat(data))
        if ok and seat and data.get("name"):
            seat["character"] = data["name"]
            self._save(roster)
        return ok

    def get_sheet(self, who: str) -> dict:
        roster = self._load()
        seat = self._find(roster, who)
        slug = seat["slug"] if seat else _slugify(who)
        return self.json_ops.load_json(f"players/{slug}/character.json") or {}

    def set_spotlight(self, who: str) -> dict:
        roster = self._load()
        seat = self._find(roster, who)
        if seat is None:
            raise ValueError(f"no seat for '{who}'")
        roster["spotlight"] = seat["slug"]
        self._save(roster)
        return seat

    def remove_seat(self, who: str) -> bool:
        roster = self._load()
        seat = self._find(roster, who)
        if seat is None:
            return False
        roster["seats"] = [s for s in roster["seats"] if s is not seat]
        if roster.get("spotlight") == seat["slug"]:
            roster["spotlight"] = roster["seats"][0]["slug"] if roster["seats"] else None
        return self._save(roster)

    def mark_dead(self, who: str, cause: str = None) -> dict:
        """Retire ONE seat non-destructively: flag it dead and archive that seat's
        sheet to players/<slug>/fallen/. Other seats are untouched. (The sheet's
        own hp/status is set via `gm-player.sh kill --player <name>`.)"""
        roster = self._load()
        seat = self._find(roster, who)
        if seat is None:
            raise ValueError(f"no seat for '{who}'")
        slug = seat["slug"]
        seat["status"] = "dead"
        if cause:
            seat["cause_of_death"] = cause
        seat["died_at"] = _now_iso()
        # Archive the seat's current sheet (if any) into its fallen/ vault.
        sheet = self.json_ops.load_json(f"players/{slug}/character.json")
        if sheet:
            (self.players_dir / slug / "fallen").mkdir(parents=True, exist_ok=True)
            stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
            name = _slugify(sheet.get("name") or seat.get("character") or "hero")
            self.json_ops.save_json(f"players/{slug}/fallen/{name}-{stamp}.json", sheet)
        # If the spotlight was on the fallen seat, pass it to a living peer.
        if roster.get("spotlight") == slug:
            living = [s["slug"] for s in roster["seats"] if s.get("status") != "dead"]
            roster["spotlight"] = living[0] if living else None
        self._save(roster)
        return seat

    def set_control(self, who: str, mode: str, delegate_to: str = None,
                    reason: str = None) -> dict:
        """Set how a seat is driven while its player is present or away:
          'self'     — the player runs their own PC (the default; also `back`)
          'gm'       — the GM runs the PC as a party NPC while the player is out
          'delegate' — another seated player runs it (delegate_to = that player)
          'away'     — the PC is written out of the fiction (reason = the excuse)
        Handles join-late/leave-mid-session/whole-session-absent without stalling
        the table or losing the character."""
        roster = self._load()
        seat = self._find(roster, who)
        if seat is None:
            raise ValueError(f"no seat for '{who}'")
        seat.pop("absence_reason", None)
        seat.pop("controlled_by", None)
        if mode == "self":
            seat["control"] = "self"
        elif mode == "gm":
            seat["control"] = "gm"
        elif mode == "delegate":
            d = self._find(roster, delegate_to or "")
            if d is None:
                raise ValueError(f"no seat to delegate to: '{delegate_to}'")
            if d["slug"] == seat["slug"]:
                raise ValueError("cannot delegate a seat to itself")
            seat["control"] = "delegate"
            seat["controlled_by"] = d["slug"]
        elif mode in ("away", "write-out", "writeout"):
            seat["control"] = "away"
            if reason:
                seat["absence_reason"] = reason
        else:
            raise ValueError(f"unknown control mode: {mode}")
        # Don't leave the spotlight on a seat nobody is actively driving.
        if seat["control"] != "self" and roster.get("spotlight") == seat["slug"]:
            active = [s["slug"] for s in roster["seats"]
                      if s.get("status") == "alive"
                      and s.get("control", "self") == "self"
                      and s["slug"] != seat["slug"]]
            if active:
                roster["spotlight"] = active[0]
        self._save(roster)
        return seat

    def kick(self, who: str, reason: str = None) -> dict:
        """Lock a seat: the human is removed and cannot join/act from it until
        `unkick`. Use for a misbehaving player, or to force off a stale 'connected'
        status a background browser tab is keeping alive. GM-only (local). The
        seat and its character remain — handle the now-unmanned PC with `away` if
        you like. The relay server enforces the lock and expires their presence."""
        roster = self._load()
        seat = self._find(roster, who)
        if seat is None:
            raise ValueError(f"no seat for '{who}'")
        seat["locked"] = True
        if reason:
            seat["kicked_reason"] = reason
        if roster.get("spotlight") == seat["slug"]:
            active = [s["slug"] for s in roster["seats"]
                      if s.get("status") == "alive" and not s.get("locked")
                      and s["slug"] != seat["slug"]]
            if active:
                roster["spotlight"] = active[0]
        self._save(roster)
        return seat

    def unkick(self, who: str) -> dict:
        """Clear a seat's lock so the player may rejoin."""
        roster = self._load()
        seat = self._find(roster, who)
        if seat is None:
            raise ValueError(f"no seat for '{who}'")
        seat["locked"] = False
        seat.pop("kicked_reason", None)
        self._save(roster)
        return seat

    def get_policy(self, who: str) -> dict:
        """The player's standing absence preference (defaults to write-out)."""
        roster = self._load()
        seat = self._find(roster, who)
        if seat is None:
            raise ValueError(f"no seat for '{who}'")
        pol = seat.get("absence_policy") or {"mode": "write-out"}
        return pol

    def set_absence_policy(self, who: str, mode: str, delegate_to: str = None,
                           reason: str = None) -> dict:
        """Set the PLAYER's standing wish for how their absence is handled:
          'write-out' (default) — GM writes the PC out of the fiction
          'gm'                  — GM runs the PC as a party NPC
          'delegate'            — a named other player runs it (delegate_to)
        This is a preference, not the live state; `away` (no override) applies it."""
        roster = self._load()
        seat = self._find(roster, who)
        if seat is None:
            raise ValueError(f"no seat for '{who}'")
        if mode in ("write-out", "writeout", "away"):
            pol = {"mode": "write-out"}
            if reason:
                pol["reason"] = reason
        elif mode == "gm":
            pol = {"mode": "gm"}
        elif mode == "delegate":
            d = self._find(roster, delegate_to or "")
            if d is None:
                raise ValueError(f"no seat to delegate to: '{delegate_to}'")
            if d["slug"] == seat["slug"]:
                raise ValueError("cannot delegate a seat to itself")
            pol = {"mode": "delegate", "to": d["slug"], "to_player": d.get("player")}
        else:
            raise ValueError(f"unknown absence policy: {mode}")
        seat["absence_policy"] = pol
        self._save(roster)
        return seat

    def apply_absence(self, who: str) -> dict:
        """Put a player 'away' using THEIR stored preference (the default path)."""
        pol = self.get_policy(who)
        mode = pol.get("mode", "write-out")
        if mode == "gm":
            return self.set_control(who, "gm")
        if mode == "delegate":
            return self.set_control(who, "delegate", delegate_to=pol.get("to"))
        return self.set_control(who, "away", reason=pol.get("reason"))

    def list_seats(self) -> dict:
        return self._load()

    # ---- context block ----------------------------------------------------

    def get_party_block(self) -> str:
        """Formatted roster for the GM's scene context: each human PC, HP, status,
        and the spotlight marker. Empty string if there are no seats."""
        roster = self._load()
        seats = roster.get("seats") or []
        if not seats:
            return ""
        spotlight = roster.get("spotlight")
        # map slug -> player name for delegate labels
        who_by_slug = {s.get("slug"): s.get("player") for s in seats}
        lines = ["THE PARTY (human players — each is a peer, give everyone spotlight):"]
        any_absent = False
        for seat in seats:
            slug = seat.get("slug", "")
            sheet = self.json_ops.load_json(f"players/{slug}/character.json") or {}
            name = sheet.get("name") or seat.get("character") or "(no character yet)"
            marker = "★" if slug == spotlight else "•"
            dead = seat.get("status") == "dead"
            control = seat.get("control", "self")
            bits = [f"{marker} {seat.get('player', slug)} → {name}"]
            if dead:
                bits.append("[FALLEN]")
            elif seat.get("locked"):
                any_absent = True
                bits.append("[player REMOVED — seat locked; unkick to re-open]")
            elif control == "away":
                any_absent = True
                bits.append(f"[offscreen — {seat.get('absence_reason') or 'absent this session'}]")
            else:
                if control == "gm":
                    any_absent = True
                    bits.append("[player away — GM runs as an NPC]")
                elif control == "delegate":
                    any_absent = True
                    bits.append(f"[player away — run by {who_by_slug.get(seat.get('controlled_by'), '?')}]")
                # hp is stored as a scalar in some kits, a {current,max} dict in
                # others — read both shapes so the bar renders either way.
                raw_hp = sheet.get("hp")
                if isinstance(raw_hp, dict):
                    cur, mx = raw_hp.get("current"), raw_hp.get("max")
                else:
                    cur = raw_hp
                    mx = sheet.get("max_hp") or sheet.get("hp_max")
                bar = _hp_bar(cur, mx)
                if bar:
                    bits.append(bar)
                lvl = sheet.get("level")
                if lvl:
                    bits.append(f"L{lvl}")
                conds = sheet.get("conditions") or []
                if conds:
                    bits.append("(" + ", ".join(conds) + ")")
            lines.append("  " + "  ".join(bits))
        lines.append("★ = spotlight (whose turn/focus). Address beats to the acting PC by name.")
        if any_absent:
            lines.append("Absent players are handled as tagged — run GM/delegated PCs, keep "
                         "offscreen ones out of the scene; don't wait on them for turns.")
        return "\n".join(lines)


# ------------------------------ CLI --------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Multiplayer seat roster")
    sub = parser.add_subparsers(dest="action")

    p_add = sub.add_parser("add", help="Add/update a player seat")
    p_add.add_argument("player", help="Player (human) name")
    p_add.add_argument("--character", help="Character name for the seat")
    p_add.add_argument("--sheet", help="Character sheet JSON to seed the seat")

    sub.add_parser("list", help="List seats")

    p_spot = sub.add_parser("spotlight", help="Set the spotlight seat")
    p_spot.add_argument("who", help="Player name or slug")

    p_rm = sub.add_parser("remove", help="Remove a seat")
    p_rm.add_argument("who", help="Player name or slug")

    p_dead = sub.add_parser("mark-dead", help="Retire a seat (non-destructive)")
    p_dead.add_argument("who", help="Player name or slug")
    p_dead.add_argument("--cause", help="How the character died")

    p_sheet = sub.add_parser("sheet", help="Set a seat's character sheet from JSON")
    p_sheet.add_argument("who", help="Player name or slug")
    p_sheet.add_argument("json", help="Character sheet JSON")

    p_away = sub.add_parser("away", help="Mark a player away (applies THEIR policy unless overridden)")
    p_away.add_argument("who", help="Player name or slug going away")
    g = p_away.add_mutually_exclusive_group(required=False)
    g.add_argument("--gm", action="store_true", help="Override: GM runs their PC as a party NPC")
    g.add_argument("--to", metavar="PLAYER", help="Override: delegate their PC to another player")
    g.add_argument("--write-out", action="store_true", help="Override: write the PC out of the fiction")
    p_away.add_argument("--reason", help="In-fiction excuse for a write-out")

    p_pol = sub.add_parser("policy", help="Set a PLAYER's standing choice for how their absence is handled")
    p_pol.add_argument("who", help="Player name or slug")
    gp = p_pol.add_mutually_exclusive_group(required=True)
    gp.add_argument("--write-out", action="store_true", help="Default: GM writes them out")
    gp.add_argument("--gm", action="store_true", help="GM runs their PC as a party NPC")
    gp.add_argument("--to", metavar="PLAYER", help="A named other player runs it")
    p_pol.add_argument("--reason", help="Preferred in-fiction excuse for a write-out")

    p_back = sub.add_parser("back", help="A player returns; they run their own PC again")
    p_back.add_argument("who", help="Player name or slug returning")

    p_kick = sub.add_parser("kick", help="Remove a player from a seat (lock it against join/act)")
    p_kick.add_argument("who", help="Player name or slug to remove")
    p_kick.add_argument("--reason", help="Why (logged on the seat)")

    p_unkick = sub.add_parser("unkick", help="Unlock a kicked seat so the player may rejoin")
    p_unkick.add_argument("who", help="Player name or slug to re-open")

    sub.add_parser("block", help="Print the party context block")

    from cli_output import wants_json, strip_json_flag, emit
    json_mode = wants_json()
    args = parser.parse_args(strip_json_flag(sys.argv[1:]))
    if not args.action:
        parser.print_help()
        sys.exit(1)

    mgr = PartyManager.for_active()

    if args.action == "add":
        seat = mgr.add_seat(args.player, character=args.character, character_json=args.sheet)
        if json_mode:
            emit(seat, json_mode=True)
        else:
            print(f"Seat added: {seat['player']} → {seat.get('character') or '(no character yet)'} "
                  f"[{seat['slug']}]")
    elif args.action == "list":
        roster = mgr.list_seats()
        if json_mode:
            emit(roster, json_mode=True)
        else:
            block = mgr.get_party_block()
            print(block or "No seats yet. Add one with: gm-party.sh add \"<player>\"")
    elif args.action == "spotlight":
        seat = mgr.set_spotlight(args.who)
        print(f"Spotlight → {seat['player']} ({seat.get('character') or seat['slug']}).")
    elif args.action == "remove":
        ok = mgr.remove_seat(args.who)
        print("Seat removed." if ok else f"No seat for '{args.who}'.")
    elif args.action == "mark-dead":
        seat = mgr.mark_dead(args.who, cause=args.cause)
        print(f"{seat['player']}'s character has fallen. The seat is retired; "
              f"offer them a hand-off. Other players play on.")
    elif args.action == "sheet":
        ok = mgr.set_sheet(args.who, args.json)
        print("Sheet saved." if ok else "Failed to save sheet.")
    elif args.action == "away":
        char = None
        if args.gm:
            seat = mgr.set_control(args.who, "gm")
            print(f"{seat['player']} is away — the GM now runs {seat.get('character') or seat['slug']} as a party NPC.")
        elif args.to:
            seat = mgr.set_control(args.who, "delegate", delegate_to=args.to)
            print(f"{seat['player']} is away — {args.to} now runs {seat.get('character') or seat['slug']}.")
        elif args.write_out:
            seat = mgr.set_control(args.who, "away", reason=args.reason)
            print(f"{seat['player']} is away — {seat.get('character') or seat['slug']} is written offscreen"
                  + (f": {args.reason}" if args.reason else ".") )
        else:
            # No override — apply the player's own standing preference.
            seat = mgr.apply_absence(args.who)
            ctl = seat.get("control")
            char = seat.get("character") or seat["slug"]
            if ctl == "gm":
                print(f"{seat['player']} is away — by their choice, the GM runs {char} as a party NPC.")
            elif ctl == "delegate":
                who_by = {s['slug']: s['player'] for s in mgr.list_seats().get('seats', [])}
                print(f"{seat['player']} is away — by their choice, {who_by.get(seat.get('controlled_by'),'?')} runs {char}.")
            else:
                print(f"{seat['player']} is away — by their choice, {char} is written offscreen"
                      + (f": {seat.get('absence_reason')}" if seat.get('absence_reason') else "."))
    elif args.action == "policy":
        if args.gm:
            seat = mgr.set_absence_policy(args.who, "gm")
            print(f"{seat['player']}'s choice when away: the GM runs their character.")
        elif args.to:
            seat = mgr.set_absence_policy(args.who, "delegate", delegate_to=args.to)
            print(f"{seat['player']}'s choice when away: {args.to} runs their character.")
        else:
            seat = mgr.set_absence_policy(args.who, "write-out", reason=args.reason)
            print(f"{seat['player']}'s choice when away: the GM writes them out"
                  + (f" ({args.reason})" if args.reason else ".") )
    elif args.action == "back":
        seat = mgr.set_control(args.who, "self")
        print(f"Welcome back — {seat['player']} runs {seat.get('character') or seat['slug']} again.")
    elif args.action == "kick":
        seat = mgr.kick(args.who, reason=args.reason)
        print(f"Removed {seat['player']} from {seat.get('character') or seat['slug']} — seat locked."
              + (f" ({args.reason})" if args.reason else "")
              + " Handle the now-unmanned PC with `away` if needed; `unkick` to re-open.")
    elif args.action == "unkick":
        seat = mgr.unkick(args.who)
        print(f"Seat re-opened — {seat['player']} may rejoin.")
    elif args.action == "block":
        print(mgr.get_party_block())


if __name__ == "__main__":
    main()
