#!/usr/bin/env python3
"""
exploration.py — ability-gated map traversal (the metroidvania engine).

A connection in locations.json may carry a `requires: [ability, ...]` list. A
connection is passable only if the active character HOLDS every required ability
(tracked as capability/feature/equipment/inventory flags on character.json). This
module answers three questions:

  * REACHABLE — which locations can the character reach right now, and what sits
    just behind a gate they can't pass yet (and which ability gates it).
  * PASSABLE — is a specific move allowed? (used to enforce moves.)
  * WHAT JUST OPENED — the metroidvania payoff: when an ability is gained, which
    locations become newly reachable, INCLUDING places already visited. This is
    the "the Grapple Beam means you can finally cross the chasm back in the
    frigate" surfacing.

Kit-agnostic: nothing here is Metroid-specific. Any world that declares gates
gets enforced gates + "what just opened."

Ability matching is tolerant by TOKENS: a requirement is met if some held ability
contains all the requirement's words. So `requires: "missile"` is satisfied by a
held "Missile Launcher (...)", and `requires: "morph_ball"` by "Morph Ball" — but
`requires: "wave beam"` is NOT satisfied by "Power Beam" (different words).
"""

import os
import re
import sys
import json
import argparse
from collections import deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

_ABILITY_FIELDS = ("capabilities", "abilities", "features", "equipment", "inventory")


def ability_key(s) -> str:
    """Normalize an ability name to a comparable key (space-separated lowercase tokens)."""
    if not isinstance(s, str):
        s = (s or {}).get("name", "") if isinstance(s, dict) else str(s)
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def held_abilities(char: dict) -> set:
    """The set of normalized ability keys the character holds (across capability/
    feature/equipment/inventory fields)."""
    held = set()
    if not isinstance(char, dict):
        return held
    for field in _ABILITY_FIELDS:
        for item in (char.get(field) or []):
            k = ability_key(item)
            if k:
                held.add(k)
    return held


def _requires(edge) -> list:
    r = edge.get("requires") if isinstance(edge, dict) else None
    return [ability_key(x) for x in r if ability_key(x)] if isinstance(r, list) else []


def _satisfied(req_key: str, held_tokensets: list) -> bool:
    """A requirement is met if some held ability's token-set is a superset of the
    requirement's token-set (so 'missile' ⊆ {missile,launcher})."""
    rt = set(req_key.split())
    return any(rt.issubset(hs) for hs in held_tokensets)


def _held_tokensets(held: set) -> list:
    return [set(h.split()) for h in held]


def edge_passable(edge, held: set) -> bool:
    hts = _held_tokensets(held)
    return all(_satisfied(r, hts) for r in _requires(edge))


def missing_for_edge(edge, held: set) -> list:
    hts = _held_tokensets(held)
    reqs = edge.get("requires") if isinstance(edge, dict) else None
    reqs = reqs if isinstance(reqs, list) else []
    # return the ORIGINAL requirement strings that aren't satisfied (nicer for display)
    out = []
    for orig in reqs:
        if not _satisfied(ability_key(orig), hts):
            out.append(orig)
    return out


def reachable(locations: dict, start: str, held: set):
    """BFS from `start` over passable edges.

    Returns (reachable_set, blocked) where blocked maps a not-yet-reachable
    destination -> the missing ability requirement(s) on the gate that fronts it
    (the smallest such requirement seen on the reachable frontier)."""
    seen = {start}
    blocked = {}
    dq = deque([start])
    while dq:
        cur = dq.popleft()
        loc = locations.get(cur) or {}
        for edge in (loc.get("connections") or []):
            if not isinstance(edge, dict):
                continue
            dest = edge.get("to")
            if not dest:
                continue
            if edge_passable(edge, held):
                if dest not in seen:
                    seen.add(dest)
                    dq.append(dest)
            elif dest not in seen:
                miss = missing_for_edge(edge, held)
                prev = blocked.get(dest)
                if prev is None or len(miss) < len(prev):
                    blocked[dest] = miss
    blocked = {d: m for d, m in blocked.items() if d not in seen}
    return seen, blocked


def newly_reachable(locations: dict, start: str, held_before: set, held_after: set):
    before, _ = reachable(locations, start, held_before)
    after, _ = reachable(locations, start, held_after)
    return sorted(after - before)


def all_gates(locations: dict) -> list:
    """Every gated edge in the map: {from, to, path, requires}."""
    out = []
    for name, loc in (locations or {}).items():
        for edge in (loc.get("connections") or []):
            if isinstance(edge, dict) and edge.get("requires"):
                out.append({"from": name, "to": edge.get("to"),
                            "path": edge.get("path"), "requires": edge.get("requires")})
    return out


# ------------------------------ CLI --------------------------------------

def _load_active():
    """Load (locations, character, current_location) for the active campaign."""
    from campaign_manager import CampaignManager
    cdir = CampaignManager("world-state").get_active_campaign_dir()
    if cdir is None:
        raise RuntimeError("No active campaign.")
    cdir = Path(cdir)

    def _j(p, d):
        try:
            return json.loads((cdir / p).read_text(encoding="utf-8"))
        except Exception:
            return d
    locations = _j("locations.json", {}) or {}
    char = _j("character.json", {}) or {}
    overview = _j("campaign-overview.json", {}) or {}
    current = (overview.get("player_position", {}) or {}).get("current_location") \
        or char.get("current_location") or ""
    return locations, char, current


def main():
    ap = argparse.ArgumentParser(description="Ability-gated exploration (metroidvania engine)")
    sub = ap.add_subparsers(dest="action")

    p = sub.add_parser("reachable", help="What the active PC can reach now, and what's gated")
    p.add_argument("--from", dest="start", help="Start location (default: current)")

    p = sub.add_parser("gained", help="What an ability opened (newly reachable, incl. visited)")
    p.add_argument("ability", help="The ability the PC just gained")
    p.add_argument("--from", dest="start", help="Start location (default: current)")

    sub.add_parser("gates", help="List every gate on the map and whether the PC can pass it")

    p = sub.add_parser("can-move", help="Is a move from current to a destination allowed?")
    p.add_argument("dest")

    from cli_output import wants_json, strip_json_flag, emit
    json_mode = wants_json()
    args = ap.parse_args(strip_json_flag(sys.argv[1:]))
    if not args.action:
        ap.print_help()
        sys.exit(1)

    locations, char, current = _load_active()
    held = held_abilities(char)
    start = getattr(args, "start", None) or current
    if not start:
        print("[ERROR] No current location and no --from given.", file=sys.stderr)
        sys.exit(1)

    if args.action == "reachable":
        seen, blocked = reachable(locations, start, held)
        if json_mode:
            emit({"from": start, "reachable": sorted(seen),
                  "blocked": {d: m for d, m in blocked.items()}}, json_mode=True)
        else:
            print(f"Reachable from {start} ({len(seen)}):")
            for loc in sorted(seen):
                print(f"  · {loc}" + ("  (here)" if loc == start else ""))
            if blocked:
                print("\nGated — just out of reach until you gain:")
                for d, m in sorted(blocked.items()):
                    print(f"  ✗ {d}  ← needs: {', '.join(m)}")
            else:
                print("\nNothing gated on the immediate frontier.")

    elif args.action == "gained":
        before = set(held)
        gained_key = ability_key(args.ability)
        # held-before = held minus the gained ability (token-superset removal)
        before = {h for h in held if not set(gained_key.split()).issubset(set(h.split()))}
        opened = newly_reachable(locations, start, before, held)
        if json_mode:
            emit({"ability": args.ability, "from": start, "opened": opened}, json_mode=True)
        elif opened:
            print(f"Gaining '{args.ability}' opens {len(opened)} place(s) — go back for:")
            for loc in opened:
                print(f"  ▸ {loc}")
        else:
            print(f"'{args.ability}' opens nothing newly reachable from {start} "
                  "(no gates on the map yet require it, or they're already reachable).")

    elif args.action == "gates":
        gates = all_gates(locations)
        if json_mode:
            passable = []
            for g in gates:
                edge = {"requires": g["requires"]}
                g2 = dict(g); g2["passable"] = edge_passable(edge, held)
                g2["missing"] = missing_for_edge(edge, held)
                passable.append(g2)
            emit({"gates": passable}, json_mode=True)
        elif not gates:
            print("No gates declared on this map. Add them with: gm-location.sh gate <from> <to> --requires ...")
        else:
            print(f"Gates on the map ({len(gates)}):")
            for g in gates:
                ok = edge_passable({"requires": g["requires"]}, held)
                mark = "✓ open" if ok else "✗ locked"
                need = "" if ok else f"  (needs: {', '.join(missing_for_edge({'requires': g['requires']}, held))})"
                print(f"  [{mark}] {g['from']} → {g['to']} via {g.get('path') or '?'}{need}")

    elif args.action == "can-move":
        loc = locations.get(start) or {}
        edge = next((e for e in (loc.get("connections") or [])
                     if isinstance(e, dict) and e.get("to") == args.dest), None)
        if edge is None:
            result = {"allowed": True, "reason": "no declared connection (unrestricted/new)"}
        else:
            ok = edge_passable(edge, held)
            result = {"allowed": ok, "missing": missing_for_edge(edge, held) if not ok else []}
        if json_mode:
            emit(result, json_mode=True)
        else:
            if result["allowed"]:
                print(f"Move {start} → {args.dest}: allowed.")
            else:
                print(f"Move {start} → {args.dest}: BLOCKED — needs {', '.join(result['missing'])}.")


if __name__ == "__main__":
    main()
