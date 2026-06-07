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
