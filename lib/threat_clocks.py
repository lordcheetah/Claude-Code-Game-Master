#!/usr/bin/env python3
"""
Threat clocks — felt, mounting pressure (DCC's floor-collapse countdown).

Named segmented clocks that advance on time or events, surfaced in the session
context so stakes are visible and trustworthy. A filled clock is the trigger for a
dramatic beat / book-native milestone. Tone-respecting: a kit/campaign that wants
no doom clock simply declares none. Dramatic choices made at inflection points are
recorded as consequences (via consequence_manager), tying the fork into the
reactive world.
"""

import sys
from pathlib import Path
from typing import Any, Dict, Optional

sys.path.insert(0, str(Path(__file__).parent))

from entity_manager import EntityManager


class ThreatClockManager(EntityManager):
    def __init__(self, world_state_dir: str = None):
        super().__init__(world_state_dir)
        self.clocks_file = "threat-clocks.json"

    def _load(self) -> Dict[str, Any]:
        return self.json_ops.load_json(self.clocks_file) or {}

    def add_clock(self, name: str, segments: int, advance_on: str = "time") -> Dict[str, Any]:
        data = self._load()
        data[name] = {"current": 0, "max": int(segments), "advance_on": advance_on}
        self.json_ops.save_json(self.clocks_file, data)
        return data[name]

    def advance(self, name: str, ticks: int = 1) -> Optional[Dict[str, Any]]:
        data = self._load()
        c = data.get(name)
        if not c:
            return None
        c["current"] = min(c["max"], int(c.get("current", 0)) + int(ticks))
        self.json_ops.save_json(self.clocks_file, data)
        return c

    def remove_clock(self, name: str) -> bool:
        data = self._load()
        if name in data:
            del data[name]
            self.json_ops.save_json(self.clocks_file, data)
            return True
        return False

    def get_clocks(self) -> Dict[str, Any]:
        return self._load()

    def is_full(self, name: str) -> bool:
        c = self._load().get(name)
        return bool(c and c.get("current", 0) >= c.get("max", 1))

    def full_clocks(self) -> Dict[str, Any]:
        return {n: c for n, c in self._load().items() if c.get("current", 0) >= c.get("max", 1)}

    @staticmethod
    def render(clocks: Dict[str, Any]) -> str:
        """Render clocks as filled/empty segment bars for the DM-visible context."""
        lines = []
        for name, c in clocks.items():
            cur, mx = int(c.get("current", 0)), int(c.get("max", 1))
            bar = "●" * cur + "○" * max(0, mx - cur)
            flag = "  ⚠ FULL" if cur >= mx else ""
            lines.append(f"{name}: [{bar}] {cur}/{mx} (on {c.get('advance_on', 'time')}){flag}")
        return "\n".join(lines)


def main():
    import argparse
    import json
    from cli_output import wants_json, strip_json_flag, emit

    parser = argparse.ArgumentParser(description="Threat clocks")
    sub = parser.add_subparsers(dest="action")
    p = sub.add_parser("add"); p.add_argument("name"); p.add_argument("segments", type=int)
    p.add_argument("--on", default="time")
    p = sub.add_parser("advance"); p.add_argument("name"); p.add_argument("--ticks", type=int, default=1)
    p = sub.add_parser("remove"); p.add_argument("name")
    sub.add_parser("list")

    json_mode = wants_json()
    args = parser.parse_args(strip_json_flag(sys.argv[1:]))
    if not args.action:
        parser.print_help(); sys.exit(1)

    m = ThreatClockManager()
    if args.action == "add":
        out = m.add_clock(args.name, args.segments, advance_on=args.on)
    elif args.action == "advance":
        out = m.advance(args.name, args.ticks)
    elif args.action == "remove":
        out = {"removed": m.remove_clock(args.name)}
    else:
        out = m.get_clocks()

    if json_mode:
        emit(out, json_mode=True)
    else:
        print(json.dumps(out, indent=2))
        if args.action == "list":
            print(m.render(out))


if __name__ == "__main__":
    main()
