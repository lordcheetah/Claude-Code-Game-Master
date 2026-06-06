# World State JSON Schema Reference

This document defines the canonical JSON schemas for all world state files. Managers enforce these schemas when reading and writing data.

---

## Campaign Structure

Each campaign lives in its own folder: `world-state/campaigns/<name>/`

```
<campaign-name>/
├── campaign-overview.json   # Campaign settings and current state
├── npcs.json                # All NPCs
├── locations.json           # All locations
├── facts.json               # World facts by category
├── consequences.json        # Pending/resolved events
├── items.json               # Items (from imports)
├── plots.json               # Plot hooks and quests
├── session-log.md           # Session history
├── character.json           # Player character sheet
└── saves/                   # Snapshot saves
```

---

## campaign-overview.json

```json
{
  "campaign_name": "string",
  "genre": "Fantasy",
  "tone": {
    "horror": 30,
    "comedy": 30,
    "drama": 40
  },
  "current_date": "string (in-game date)",
  "time_of_day": "dawn|morning|midday|afternoon|dusk|evening|night|midnight",
  "player_position": {
    "current_location": "string or null",
    "previous_location": "string or null",
    "arrival_time": "ISO timestamp"
  },
  "current_character": "string (character name)",
  "session_count": 0
}
```

---

## npcs.json

A dictionary keyed by NPC name.

```json
{
  "NPC_NAME": {
    "description": "string (physical/personality description)",
    "attitude": "friendly|neutral|hostile|suspicious|helpful|indifferent|fearful|respectful|dismissive|curious",
    "created": "ISO timestamp",
    "events": [
      {"event": "string describing what happened", "timestamp": "ISO timestamp"}
    ],
    "tags": {
      "locations": ["location name"],
      "quests": ["quest name"]
    },
    "context": ["optional source passages"],
    "enhanced": false,
    "enhanced_at": "ISO timestamp",
    "is_party_member": false,
    "character_sheet": null
  }
}
```

### Party Member Character Sheet

When `is_party_member: true`, the `character_sheet` contains:

```json
{
  "character_sheet": {
    "race": "Human",
    "class": "Fighter",
    "level": 2,
    "hp": {
      "current": 18,
      "max": 22
    },
    "ac": 14,
    "stats": {"str": 14, "dex": 12, "con": 13, "int": 10, "wis": 11, "cha": 10},
    "saves": {"str": 4, "dex": 1, "con": 3, "int": 0, "wis": 0, "cha": 0},
    "skills": {},
    "attack_bonus": 4,
    "damage": "1d8+2",
    "equipment": ["Longsword", "Shield", "Chain Shirt"],
    "features": ["Second Wind", "Fighting Style (Defense)"],
    "conditions": [],
    "xp": 0
  }
}
```

**HP Tracking:** Party members use `hp.current` and `hp.max`. Update with:
```bash
bash tools/gm-npc.sh hp "Name" -5   # Damage
bash tools/gm-npc.sh hp "Name" +3   # Heal
```

### Field Descriptions

| Field | Required | Description |
|-------|----------|-------------|
| description | Yes | Character description |
| attitude | Yes | One of the supported attitude values |
| created | Yes | ISO timestamp when created |
| tags | No | Object with `locations` and `quests` arrays |
| events | No | Array of event objects |
| context | No | Source passages for RAG enhancements |
| enhanced | No | Flag when RAG enhancements applied |
| enhanced_at | No | ISO timestamp when enhanced |
| is_party_member | No | True if NPC is a party member |
| character_sheet | No | Full character sheet if party member (see above)

---

## locations.json

A dictionary keyed by location name.

```json
{
  "LOCATION_NAME": {
    "position": "string (relative position, e.g. 'north of town')",
    "description": "string (what the place looks like)",
    "connections": [
      {"to": "Other Location", "path": "rocky trail"}
    ],
    "discovered": "ISO timestamp",
    "notes": "optional string",
    "source": "optional string"
  }
}
```

### Dungeon Rooms (Extended Schema)

Dungeon rooms (stored in `locations.json`) may include:

```json
{
  "ROOM_NAME": {
    "dungeon": "string (dungeon name)",
    "room_number": 1,
    "description": "string",
    "exits": {
      "north": {"to": "Room 2", "type": "open|door|secret|stairs-up|stairs-down"}
    },
    "state": {"discovered": false, "visited": false, "cleared": false}
  }
}
```

---

## facts.json

A dictionary with category keys, each containing an array of fact strings.

```json
{
  "world_building": [
    "The kingdom has been at peace for 100 years",
    "Dragons are extinct except for one"
  ],
  "session_events": [
    "The party met the king on day 1"
  ],
  "plot_hooks": [
    "A mysterious stranger mentioned a treasure"
  ]
}
```

### Common Categories

- `world_building` - Established world facts
- `session_events` - What happened this session
- `plot_local` - Local storyline facts
- `plot_regional` - Broader mystery/conspiracy facts
- `plot_world` - World-shaking revelations
- `player_choices` - Key decisions made
- `npc_relations` - How NPCs feel about the party

---

## consequences.json

Tracks events that will trigger in the future.

```json
{
  "active": [
    {
      "id": "8-char-uuid",
      "consequence": "string (what will happen)",
      "trigger": "string (free-text, when it triggers)",
      "created": "ISO timestamp",

      "trigger_type": "on_location | on_npc | on_time | on_event   (OPTIONAL, structured)",
      "match": "string compared against world state (location name / npc / time keyword / event keyword)",
      "expiry": "string date or condition after which it ages out   (OPTIONAL)"
    }
  ],
  "resolved": [
    {
      "id": "8-char-uuid",
      "consequence": "string",
      "trigger": "string",
      "created": "ISO timestamp",
      "resolved": "ISO timestamp"
    }
  ]
}
```

**Structured triggers** (`trigger_type`/`match`/`expiry`) are additive and
optional. When present, the reactivity engine fires the consequence automatically
when world state matches (and expires it past `expiry`); when absent, the
consequence is a legacy free-text entry matched fuzzily. A campaign may mix both.

---

## plots.json

A dictionary keyed by plot name.

```json
{
  "PLOT_NAME": {
    "type": "main|side|mystery|threat",
    "status": "active|completed|failed|dormant",
    "description": "string (what the quest is about)",
    "npcs": ["involved", "npc", "names"],
    "locations": ["relevant", "locations"],
    "objectives": ["optional objective strings"],
    "rewards": "optional string",
    "consequences": "optional string",
    "events": [
      {"event": "progress update", "timestamp": "ISO timestamp"}
    ],
    "completed_at": "ISO timestamp or null",
    "failed_at": "ISO timestamp or null"
  }
}
```

---

## items.json

A dictionary keyed by item name. Typically populated by `/import`.

```json
{
  "ITEM_NAME": {
    "name": "string",
    "description": "string",
    "type": "weapon|armor|potion|scroll|wondrous|treasure|equipment|prop|artifact",
    "rarity": "common|uncommon|rare|very rare|legendary|artifact",
    "mechanics": "optional string",
    "value": "optional string",
    "location": "optional string",
    "attunement": false,
    "cursed": false,
    "source": "optional string"
  }
}
```

---

## character.json

The player character sheet.

```json
{
  "name": "string",
  "race": "string",
  "class": "string",
  "level": 1,
  "background": "string",

  "stats": {
    "str": 10,
    "dex": 10,
    "con": 10,
    "int": 10,
    "wis": 10,
    "cha": 10
  },

  "hp": {"current": 10, "max": 10},

  "ac": 10,
  "skills": {},
  "saves": {"str": 0, "dex": 0, "con": 0, "int": 0, "wis": 0, "cha": 0},

  "equipment": ["item", "names"],
  "features": ["class", "features"],
  "background": "string",
  "alignment": "string",
  "bonds": "string",
  "flaws": "string",
  "ideals": "string",
  "traits": "string",
  "notes": [],
  "gold": 0,
  "xp": {"current": 0, "next_level": 300}
}
```

---

## Save Files (saves/*.json)

Snapshots of world state at a point in time.

```json
{
  "name": "string (save name)",
  "created": "ISO timestamp",
  "session_number": 5,
  "snapshot": {
    "campaign_overview": {},
    "npcs": {},
    "locations": {},
    "facts": {},
    "consequences": {},
    "characters": {}
  }
}
```

---

## Validation Notes

- All timestamps use ISO 8601 format with timezone
- Entity names serve as dictionary keys (case-sensitive)
- Empty arrays `[]` are preferred over `null` for list fields
- Boolean fields default to `false` if omitted
- The `created` field is auto-set by managers when entities are created

## ruleset.json (World Kit)

Per-campaign ruleset that drives play through the generic `game_core`. Declares
how a world plays without baking in D&D 5e.

```json
{
  "name": "Dungeon Crawler Carl",
  "stat_schema": { "attributes": ["str","con","dex","int"], "vitals": ["hp"] },
  "progression": { "model": "milestone | xp-levels | resource-axis", "...": "model config (thresholds/tiers/resource)" },
  "resolution": { "model": "d20-vs-dc" },
  "active_agents": ["monster-manual", "loot-dropper"],
  "rules_doc": "rules.md"
}
```

- `stat_schema.attributes` is open and kit-defined (no fixed six abilities).
- `progression.model` selects one of the core's three models; its config
  (`thresholds` for xp-levels, `resource`+`tiers` for resource-axis) is supplied here.
- World-flavor systems (loot boxes, viewers) stay in campaign-overview `campaign_rules`.

## world-bible.json (Book Bible)

The structured fidelity spine of a world, loaded at session start. Auto-drafted at
import; captures what makes a book feel like itself.

```json
{
  "name": "string",
  "voice": { "style": "string", "vocab": ["..."], "sample_passages": ["..."] },
  "tone": "string",
  "themes": ["..."],
  "factions":  { "nodes": [{"id","name"}], "edges": [{"from","to","relation"}] },
  "geography": { "nodes": [{"id","name"}], "edges": [{"from","to","adjacency"}] },
  "timeline": ["..."],
  "signature_systems": ["..."]
}
```

Required: name, voice, tone, themes, factions (graph), geography (graph),
signature_systems. The bible auto-generates the World Kit ruleset + campaign_rules.
