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
