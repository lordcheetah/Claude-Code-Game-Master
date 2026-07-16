#!/usr/bin/env python3
"""
Save D&D character to world-state JSON files
Handles complete character creation with proper calculations
Supports multi-campaign system (saves to active campaign's character.json)

KNOWN LIMITATION -- THIS PATH IS D&D 5e ONLY. It cannot save a character for a
campaign whose World Kit defines its own stat model, and it does not merely
reject one: given a non-5e sheet it would SILENTLY CORRUPT it.

  - save_character() requires ['name', 'race', 'class', 'level', 'stats'].
    A Homeric kit has a lineage and a kleos-grade; a Metroid kit has neither a
    race nor a class. Those worlds have nothing to put in these fields.
  - hp is recomputed as calculate_hp(class, level, con_modifier) -- a D&D hit-die
    lookup keyed on class name, defaulting to d8. It OVERWRITES whatever hp the
    kit's own rules produced.
  - `saves` is derived from D&D class proficiencies, a concept most kits lack.
  - a `gold` field is injected unconditionally. Some kits state outright that a
    gold field on a sheet IS a bug (their economies are honour ledgers, tripods,
    cattle -- not a purse).

So a non-5e PC must currently be written to the campaign's character.json
directly. The rest of the runtime already handles this correctly: player_manager
renders the active kit's stat_schema.vitals, and schemas.validate_character only
demands race/class/level when the kit declares no vitals of its own. This module
is the last hardcoded-5e link in the chain.

Fixing it means deriving the required fields and the vitals from the active
kit's ruleset.json (the pattern player_manager._kit_vitals / _summary_line and
schemas.validate_world_state already use), and leaving the 5e math to run only
when the kit is actually 5e. The /create-character command itself makes the same
assumption end to end -- races, classes, spell slots, gold -- and would want the
same treatment.
"""

import json
import sys
import os
from pathlib import Path

# Add lib directory to path for imports
lib_path = Path(__file__).parent.parent.parent / "lib"
sys.path.insert(0, str(lib_path))

from campaign_manager import CampaignManager
import visual_appearance as va_mod

def calculate_modifier(score):
    """Calculate ability modifier from ability score"""
    return (score - 10) // 2

def calculate_hp(class_name, level, con_modifier):
    """Calculate HP based on class hit die and constitution"""
    hit_dice = {
        'barbarian': 12,
        'fighter': 10, 'paladin': 10, 'ranger': 10,
        'bard': 8, 'cleric': 8, 'druid': 8, 'monk': 8, 'rogue': 8, 'warlock': 8,
        'artificer': 8,
        'sorcerer': 6, 'wizard': 6
    }
    
    hit_die = hit_dice.get(class_name.lower(), 8)
    
    # Level 1: max hit die + con modifier
    # Higher levels: average of hit die + con modifier per level
    if level == 1:
        return hit_die + con_modifier
    else:
        base_hp = hit_die + con_modifier
        additional_hp = (level - 1) * ((hit_die // 2) + 1 + con_modifier)
        return base_hp + additional_hp

def calculate_saves(class_name, level, stats):
    """Calculate saving throw bonuses based on class proficiencies"""
    prof_bonus = 2 + ((level - 1) // 4)  # Proficiency bonus progression
    
    # Class proficiencies
    proficiencies = {
        'barbarian': ['str', 'con'],
        'bard': ['dex', 'cha'],
        'cleric': ['wis', 'cha'],
        'druid': ['int', 'wis'],
        'fighter': ['str', 'con'],
        'monk': ['str', 'dex'],
        'paladin': ['wis', 'cha'],
        'ranger': ['str', 'dex'],
        'rogue': ['dex', 'int'],
        'sorcerer': ['con', 'cha'],
        'warlock': ['wis', 'cha'],
        'wizard': ['int', 'wis'],
        'artificer': ['con', 'int']
    }
    
    class_profs = proficiencies.get(class_name.lower(), [])
    
    saves = {}
    for stat in ['str', 'dex', 'con', 'int', 'wis', 'cha']:
        modifier = calculate_modifier(stats[stat])
        if stat in class_profs:
            saves[stat] = modifier + prof_bonus
        else:
            saves[stat] = modifier
    
    return saves

def create_character_id(name):
    """Convert character name to file-safe ID"""
    return name.lower().replace(' ', '-').replace("'", '').replace('"', '')

def save_character(character_data):
    """Save character to campaign's character.json file"""

    # Validate required fields
    required_fields = ['name', 'race', 'class', 'level', 'stats']
    for field in required_fields:
        if field not in character_data:
            return {"error": f"Missing required field: {field}"}

    # Generate character ID
    char_id = create_character_id(character_data['name'])

    # Calculate derived values
    con_modifier = calculate_modifier(character_data['stats']['con'])

    # Build complete character object
    character = {
        "id": char_id,
        "name": character_data['name'],
        "race": character_data['race'],
        "class": character_data['class'],
        "level": character_data['level'],
        "hp": {
            "current": calculate_hp(character_data['class'], character_data['level'], con_modifier),
            "max": calculate_hp(character_data['class'], character_data['level'], con_modifier)
        },
        "ac": character_data.get('ac', 10),  # Default AC, can be overridden
        "stats": character_data['stats'],
        "saves": calculate_saves(character_data['class'], character_data['level'], character_data['stats']),
        "skills": character_data.get('skills', {}),
        "equipment": character_data.get('equipment', []),
        "features": character_data.get('features', []),
        "background": character_data.get('background', ''),
        "alignment": character_data.get('alignment', ''),
        "bonds": character_data.get('bonds', ''),
        "flaws": character_data.get('flaws', ''),
        "ideals": character_data.get('ideals', ''),
        "traits": character_data.get('traits', ''),
        "notes": character_data.get('notes', []),
        "gold": character_data.get('gold', 0),
        "xp": character_data.get('xp', {"current": 0, "next_level": 300}),
        # Canonical look-of-the-character for consistent image generation.
        "visual_appearance": va_mod.normalize(character_data.get('visual_appearance'))
    }

    # Get the active campaign directory
    campaign_mgr = CampaignManager()
    campaign_dir = campaign_mgr.get_active_campaign_dir()

    # Determine save path based on campaign system
    if campaign_mgr.get_active():
        # New format: save to character.json in campaign folder
        file_path = campaign_dir / "character.json"
    else:
        # Legacy format: save to characters/<name>.json
        characters_dir = Path("world-state/characters")
        characters_dir.mkdir(parents=True, exist_ok=True)
        file_path = characters_dir / f"{char_id}.json"

    try:
        with open(file_path, 'w') as f:
            json.dump(character, f, indent=2)

        return {
            "success": True,
            "character_id": char_id,
            "file_path": str(file_path),
            "campaign": campaign_mgr.get_active() or "legacy",
            "character": character
        }

    except Exception as e:
        return {"error": f"Failed to save character: {str(e)}"}

def main():
    """CLI interface for character saving"""
    
    if len(sys.argv) < 2:
        print("Usage: save_character.py '<character_json>' or save_character.py --stdin")
        print("Example: save_character.py '{\"name\":\"Thorin\",\"race\":\"Dwarf\",\"class\":\"Fighter\",\"level\":1,\"stats\":{\"str\":16,\"dex\":12,\"con\":15,\"int\":10,\"wis\":13,\"cha\":8}}'")
        sys.exit(1)
    
    try:
        if sys.argv[1] == '--stdin':
            # Read from stdin
            character_json = sys.stdin.read().strip()
        else:
            # Read from argument
            character_json = sys.argv[1]
        
        character_data = json.loads(character_json)
        result = save_character(character_data)
        
        print(json.dumps(result, indent=2))
        
        if "error" in result:
            sys.exit(1)
            
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON: {str(e)}"}, indent=2))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": f"Unexpected error: {str(e)}"}, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()