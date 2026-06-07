"""Tests for canvas-view-writer: the agent-authored scene write path."""

import json
from pathlib import Path

from lib.view_manager import ViewManager, sanitize_body, MAX_BODY_CHARS


def _view_path(dcc_world):
    """Resolve the active campaign's view.json under the hermetic world-state."""
    return Path(ViewManager(dcc_world).campaign_dir) / "view.json"


def test_set_scene_round_trip(dcc_world):
    body = "+---+\n| @ |\n+---+"
    ViewManager(dcc_world).set_scene("The Crypt", body)
    # Fresh load from disk simulates the watcher reading the file.
    data = json.loads(_view_path(dcc_world).read_text(encoding="utf-8"))
    assert data["title"] == "The Crypt"
    assert data["body"] == body
    assert data["updated"]  # ISO timestamp stamped


def test_write_is_atomic_no_tmp_left(dcc_world):
    ViewManager(dcc_world).set_scene("X", "art")
    campaign_dir = Path(ViewManager(dcc_world).campaign_dir)
    assert (campaign_dir / "view.json").exists()
    assert not (campaign_dir / "view.tmp").exists(), "temp file must be renamed away"


def test_ansi_color_survives(dcc_world):
    # ESC-based ANSI color must round-trip intact.
    colored = "\x1b[31mRED MAP\x1b[0m"
    ViewManager(dcc_world).set_scene("c", colored)
    data = json.loads(_view_path(dcc_world).read_text(encoding="utf-8"))
    assert data["body"] == colored
    assert "\x1b[31m" in data["body"]


def test_control_chars_stripped_but_structure_kept():
    # CR and BEL dropped; tab and newline kept.
    dirty = "a\r\nb\x07\tc"
    assert sanitize_body(dirty) == "a\nb\tc"


def test_single_trailing_newline_stripped():
    assert sanitize_body("line\n") == "line"
    # Only ONE trailing newline is removed; an inner/extra one stays.
    assert sanitize_body("line\n\n") == "line\n"


def test_body_capped_at_64kb():
    huge = "z" * (MAX_BODY_CHARS + 5000)
    assert len(sanitize_body(huge)) == MAX_BODY_CHARS


def test_clear_blanks_but_keeps_file(dcc_world):
    vm = ViewManager(dcc_world)
    vm.set_scene("Something", "drawn")
    vm.clear_scene()
    path = _view_path(dcc_world)
    assert path.exists(), "clear must keep the file for the watcher placeholder"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["title"] == "" and data["body"] == ""
    assert data["updated"]  # fresh timestamp on clear


# --- canvas-render-compose: read + render path ------------------------------

import re

from lib.view_manager import (
    resolve_campaign_dir,
    load_state,
    compose_frame,
    visible_len,
    clip_visible,
    hp_bar,
    GREEN,
    AMBER,
    RED,
)


def _strip(s):
    return re.sub(r"\x1b\[[0-9;]*m", "", s)


def test_visible_len_ignores_ansi():
    assert visible_len("\x1b[31mhi\x1b[0m") == 2


def test_clip_visible_preserves_escapes_and_resets():
    out = clip_visible("\x1b[31mhello world", 3)
    assert _strip(out) == "hel"
    assert "\x1b[31m" in out  # color escape kept
    assert out.endswith("\x1b[0m")  # RESET appended so color never bleeds


def test_hp_bar_color_thresholds_match_hud():
    assert hp_bar(10, 10).startswith(GREEN)   # 100% -> green
    assert hp_bar(3, 10).startswith(AMBER)    # 30%  -> amber
    assert hp_bar(1, 10).startswith(RED)      # 10%  -> red


def test_hp_bar_zero_max_no_zerodivision():
    bar = hp_bar(0, 0)  # must not raise
    assert _strip(bar) == "░" * 10


def test_compose_populated_from_fixture(dcc_world):
    # Seed a scene, then render real DCC state.
    ViewManager(dcc_world).set_scene("The Crypt", "MAP\nART")
    state = load_state(resolve_campaign_dir(dcc_world))
    out = compose_frame(state, 80, 24)
    flat = _strip(out)
    # Header, all three regions, footer.
    assert "The Crypt" in flat
    assert "SCENE" in flat and "PARTY" in flat and "HERE" in flat
    assert "updated" in flat
    # Player + the is_party_member NPCs (Carl, Donut, Mongo) are listed; a
    # non-party NPC (Mordecai) is not.
    assert "Tandy" in flat and "Carl" in flat and "Princess Donut" in flat
    assert "Mordecai" not in flat
    # Current location + a real connection are shown.
    assert "Warehouse Street Level" in flat
    assert "Warehouse Rooftop" in flat
    # Every line is exactly 80 visible columns (frame integrity).
    assert {visible_len(l) for l in out.splitlines()} == {80}


def test_compose_no_campaign_placeholder():
    out = compose_frame({"_active": False}, 80, 24)
    flat = _strip(out)
    assert "no active campaign" in flat
    assert {visible_len(l) for l in out.splitlines()} == {80}


def test_compose_handles_edge_cases_without_crashing():
    state = {
        "_active": True,
        "view": {"title": "Edge", "body": "", "updated": ""},
        "character": {"name": "H", "hp": {"current": 0, "max": 0}, "conditions": None},
        "npcs": {
            "NoSheet": {"is_party_member": True},  # missing character_sheet
            "Bear": {"is_party_member": True, "character_sheet": {"level": 2, "hp": {"current": 5, "max": 20}}},
        },
        "locations": {},  # current location missing from the map
        "overview": {},
    }
    out = compose_frame(state, 80, 20)
    flat = _strip(out)
    assert "0/0" in flat            # hp.max==0 rendered, no ZeroDivision
    assert "• NoSheet" in flat      # name-only, no bar
    assert "(no known exits)" in flat
    assert {visible_len(l) for l in out.splitlines()} == {80}


def test_compose_clips_wide_lines_and_overflows_tall_body():
    body = ("Z" * 300) + "\n" + "\n".join(f"r{i}" for i in range(50))
    state = {
        "_active": True,
        "view": {"title": "T", "body": body, "updated": ""},
        "character": {"name": "A", "hp": {"current": 1, "max": 1}},
        "npcs": {}, "locations": {}, "overview": {},
    }
    out = compose_frame(state, 80, 16)
    flat = _strip(out)
    assert re.search(r"\(\+\d+ lines\)", flat)  # vertical overflow marker
    assert {visible_len(l) for l in out.splitlines()} == {80}  # wide line clipped


def test_compose_stacks_when_narrow():
    state = {
        "_active": True,
        "view": {"title": "T", "body": "x", "updated": ""},
        "character": {"name": "A", "hp": {"current": 1, "max": 1}},
        "npcs": {}, "locations": {}, "overview": {},
    }
    out = compose_frame(state, 60, 20)
    # Stacked layout uses full-width PARTY then HERE dividers (no ┬ junction).
    assert "┬" not in out
    assert {visible_len(l) for l in out.splitlines()} == {60}


# --- canvas-combat-panel: auto COMBAT panel from combat_state.json ----------

import json as _json

from lib.view_manager import GOLD


def _base_state(**over):
    state = {
        "_active": True,
        "view": {"title": "T", "body": "x", "updated": ""},
        "character": {"name": "Tandy", "hp": {"current": 40, "max": 80}},
        "npcs": {}, "locations": {},
        "overview": {"current_date": "Day 4", "time_of_day": "Dusk"},
    }
    state.update(over)
    return state


def test_overview_key_loads_under_overview(dcc_world):
    # Regression: load_state must expose campaign-overview.json under "overview"
    # (not "campaign_overview"), or the header clock silently vanishes.
    state = load_state(resolve_campaign_dir(dcc_world))
    assert "overview" in state
    assert "campaign_overview" not in state
    assert isinstance(state["overview"], dict) and state["overview"]


def test_load_state_includes_combat(dcc_world):
    state = load_state(resolve_campaign_dir(dcc_world))
    assert "combat" in state  # present even if {} when no combat file


def test_combat_panel_active_render():
    combat = {
        "active": True, "round": 3, "turn_index": 1,
        "combatants": [
            {"name": "Goblin", "hp_current": 3, "hp_max": 12, "initiative": 18, "side": "enemy", "conditions": ["prone"]},
            {"name": "Tandy", "hp_current": 40, "hp_max": 80, "initiative": 20, "side": "player", "conditions": []},
            {"name": "Dead Orc", "hp_current": 0, "hp_max": 15, "initiative": 5, "side": "enemy"},
        ],
    }
    out = compose_frame(_base_state(combat=combat), 80, 24)
    flat = _strip(out)
    assert "COMBAT · Round 3" in flat
    # Ordered by initiative desc: Tandy (20) before Goblin (18) before Dead Orc (5).
    assert flat.index("Tandy") < flat.index("Goblin") < flat.index("Dead Orc")
    assert "[enemy]" in flat and "[player]" in flat
    assert "(prone)" in flat            # conditions shown
    assert "▸" in out                   # active-turn marker
    assert {visible_len(l) for l in out.splitlines() if "💀" not in l} == {80}


def test_combat_active_turn_marker_tracks_turn_index():
    # turn_index points at the SECOND stored combatant; after init-desc sort it
    # is the highest-initiative one — the marker must follow the object, not the slot.
    combat = {
        "active": True, "round": 1, "turn_index": 1,
        "combatants": [
            {"name": "Low", "hp_current": 5, "hp_max": 5, "initiative": 1, "side": "enemy"},
            {"name": "High", "hp_current": 5, "hp_max": 5, "initiative": 99, "side": "enemy"},
        ],
    }
    out = compose_frame(_base_state(combat=combat), 80, 20)
    line = [l for l in out.splitlines() if "High" in l][0]
    assert "▸" in line          # the marked combatant is High (the turn_index target)
    low = [l for l in out.splitlines() if "Low" in l][0]
    assert "▸" not in low


def test_combat_hidden_when_inactive():
    # No combat key, empty combatants, and explicit inactive all hide the panel.
    assert "COMBAT" not in _strip(compose_frame(_base_state(), 80, 18))
    assert "COMBAT" not in _strip(compose_frame(_base_state(combat={}), 80, 18))
    assert "COMBAT" not in _strip(compose_frame(_base_state(combat={"active": False, "combatants": []}), 80, 18))


def test_combat_hp_max_zero_no_crash():
    combat = {"active": True, "round": 1, "turn_index": 0,
              "combatants": [{"name": "Wraith", "hp_current": 0, "hp_max": 0, "initiative": 1, "side": "enemy"}]}
    out = compose_frame(_base_state(combat=combat), 80, 18)  # must not raise
    assert "0/0" in _strip(out)


# --- canvas-watch-loop: change-signature (live behavior is manual-lane) ------

from pathlib import Path as _Path

from lib.view_manager import _watch_signature, _STATE_FILES


def test_signature_changes_on_terminal_resize(dcc_world):
    d = resolve_campaign_dir(dcc_world)
    assert _watch_signature(d, 80, 24) != _watch_signature(d, 100, 24)
    assert _watch_signature(d, 80, 24) != _watch_signature(d, 80, 40)


def test_signature_distinguishes_no_campaign(dcc_world):
    d = resolve_campaign_dir(dcc_world)
    assert _watch_signature(None, 80, 24) != _watch_signature(d, 80, 24)


def test_signature_changes_when_watched_file_changes(dcc_world):
    d = resolve_campaign_dir(dcc_world)
    before = _watch_signature(d, 80, 24)
    # A scene write bumps view.json's mtime -> signature must flip (live redraw).
    ViewManager(dcc_world).set_scene("New", "art")
    assert _watch_signature(d, 80, 24) != before


def test_signature_includes_combat_state(dcc_world):
    # combat_state.json must be watched so the COMBAT panel updates live.
    assert "combat_state.json" in _STATE_FILES.values()
    d = resolve_campaign_dir(dcc_world)
    before = _watch_signature(d, 80, 24)
    # Creating the combat file (sentinel '-' -> real mtime) flips the signature.
    (_Path(d) / "combat_state.json").write_text('{"active":true,"combatants":[]}', encoding="utf-8")
    assert _watch_signature(d, 80, 24) != before
