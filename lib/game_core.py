#!/usr/bin/env python3
"""
Generic, system-agnostic game core.

NO D&D 5e assumptions live here: no fixed ability names, no level-20 cap, no spell
slots. The core provides only the universal primitives every world runs on:

  - resolution:  resolve_check (d20 vs DC) + opposed_check (contest)
  - harm:        apply_harm / heal on an abstract HP value
  - conditions:  add_condition / remove_condition on a list
  - progression: three interchangeable models (milestone / resource-axis / xp-levels)

Stat names, combat feel, signature systems, and the choice of progression model are
BESPOKE PER WORLD (a World Kit configures them). dice.py is the only RNG.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent))

from dice import DiceRoller

_roller = DiceRoller()

_ADV_NOTATION = {'advantage': '2d20kh1', 'disadvantage': '2d20kl1', None: '1d20'}


# ---------------------------------------------------------------- resolution

def resolve_check(modifier: int = 0, dc: int = 10, advantage: Optional[str] = None) -> Dict[str, Any]:
    """Resolve a d20-vs-DC check. advantage = 'advantage' | 'disadvantage' | None.

    Returns die (the kept d20 face), total, dc, success, margin, critical
    ('hit' on a natural 20, 'miss' on a natural 1, else None).
    """
    notation = _ADV_NOTATION.get(advantage, '1d20')
    r = _roller.roll(notation)
    kept = r.get('kept', r.get('rolls', []))
    die = kept[0] if kept else r['total']
    total = r['total'] + modifier
    critical = 'hit' if die == 20 else 'miss' if die == 1 else None
    return {
        'die': die,
        'modifier': modifier,
        'total': total,
        'dc': dc,
        'success': total >= dc,
        'margin': total - dc,
        'critical': critical,
    }


def opposed_check(modifier_a: int = 0, modifier_b: int = 0,
                  advantage_a: Optional[str] = None, advantage_b: Optional[str] = None) -> Dict[str, Any]:
    """Resolve an opposed contest between A and B. Ties go to neither."""
    a = resolve_check(modifier_a, 0, advantage_a)
    b = resolve_check(modifier_b, 0, advantage_b)
    if a['total'] > b['total']:
        winner = 'a'
    elif b['total'] > a['total']:
        winner = 'b'
    else:
        winner = 'tie'
    return {'a': a['total'], 'b': b['total'], 'winner': winner, 'margin': abs(a['total'] - b['total'])}


# ---------------------------------------------------------------- harm / conditions

def apply_harm(current_hp: int, amount: int) -> int:
    """Reduce HP by amount, floored at 0."""
    return max(0, current_hp - max(0, amount))


def heal(current_hp: int, max_hp: int, amount: int) -> int:
    """Increase HP by amount, capped at max_hp."""
    return min(max_hp, current_hp + max(0, amount))


def add_condition(conditions: List[str], condition: str) -> List[str]:
    """Add a condition (idempotent). Returns a new list."""
    out = list(conditions or [])
    if condition and condition not in out:
        out.append(condition)
    return out


def remove_condition(conditions: List[str], condition: str) -> List[str]:
    """Remove a condition if present. Returns a new list."""
    return [c for c in (conditions or []) if c != condition]


# ---------------------------------------------------------------- progression

class Progression:
    """Interface: advance(state, **kw) -> state; level(state) -> int."""

    name = 'base'

    def advance(self, state: Dict[str, Any], **kw) -> Dict[str, Any]:
        raise NotImplementedError

    def level(self, state: Dict[str, Any]) -> int:
        raise NotImplementedError


class MilestoneProgression(Progression):
    """Story-beat advancement. No XP math; the DM grants milestones."""

    name = 'milestone'

    def advance(self, state, **kw):
        state = dict(state or {})
        state['milestone'] = int(state.get('milestone', 0)) + int(kw.get('count', 1))
        return state

    def level(self, state):
        return int((state or {}).get('milestone', 0))


class XpLevelProgression(Progression):
    """XP-threshold leveling. Thresholds are SUPPLIED (not a hardcoded 5e table)."""

    name = 'xp-levels'

    def __init__(self, thresholds: List[int] = None):
        # thresholds[i] = XP required to reach level i+2 (level 1 starts at 0 xp).
        self.thresholds = list(thresholds or [])

    def advance(self, state, **kw):
        state = dict(state or {})
        state['xp'] = int(state.get('xp', 0)) + int(kw.get('xp', 0))
        state['level'] = self.level(state)
        return state

    def level(self, state):
        xp = int((state or {}).get('xp', 0))
        lvl = 1
        for t in self.thresholds:
            if xp >= t:
                lvl += 1
            else:
                break
        return lvl


class ResourceAxisProgression(Progression):
    """Progression along a world resource/clock (DCC viewers, Dune spice, ...).

    `tiers` are SUPPLIED resource thresholds; level = number of tiers reached.
    """

    name = 'resource-axis'

    def __init__(self, resource: str = 'resource', tiers: List[int] = None):
        self.resource = resource
        self.tiers = list(tiers or [])

    def advance(self, state, **kw):
        state = dict(state or {})
        state[self.resource] = int(state.get(self.resource, 0)) + int(kw.get('amount', 0))
        return state

    def level(self, state):
        value = int((state or {}).get(self.resource, 0))
        return sum(1 for t in self.tiers if value >= t)


def make_progression(model: str, **config) -> Progression:
    """Factory: build a progression model by name. Unknown -> milestone (safe default)."""
    if model == 'xp-levels':
        return XpLevelProgression(thresholds=config.get('thresholds'))
    if model == 'resource-axis':
        return ResourceAxisProgression(resource=config.get('resource', 'resource'),
                                       tiers=config.get('tiers'))
    return MilestoneProgression()
