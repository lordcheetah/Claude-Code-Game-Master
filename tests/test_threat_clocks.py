"""Tests for threat-clocks-choice-beats: named segmented pressure clocks."""

from lib.threat_clocks import ThreatClockManager
from lib.session_manager import SessionManager


def test_add_advance_and_fill(dcc_world):
    m = ThreatClockManager(dcc_world)
    m.add_clock("Floor Collapse", segments=4, advance_on="time")
    assert not m.is_full("Floor Collapse")
    m.advance("Floor Collapse", 3)
    assert not m.is_full("Floor Collapse")
    m.advance("Floor Collapse", 5)  # clamps at max
    c = m.get_clocks()["Floor Collapse"]
    assert c["current"] == 4
    assert m.is_full("Floor Collapse")
    assert "Floor Collapse" in m.full_clocks()


def test_advance_unknown_clock_returns_none(dcc_world):
    assert ThreatClockManager(dcc_world).advance("nope") is None


def test_remove_clock(dcc_world):
    m = ThreatClockManager(dcc_world)
    m.add_clock("Doom", 6)
    assert m.remove_clock("Doom") is True
    assert "Doom" not in m.get_clocks()


def test_no_clocks_is_valid_tone_respecting(dcc_world):
    # A campaign that wants no doom clock simply has none.
    assert ThreatClockManager(dcc_world).get_clocks() == {}


def test_clocks_surface_in_session_context(dcc_world):
    ThreatClockManager(dcc_world).add_clock("Floor Collapse", segments=4)
    ThreatClockManager(dcc_world).advance("Floor Collapse", 2)
    ctx = SessionManager(dcc_world).get_full_context()
    assert "THREAT CLOCKS" in ctx
    assert "Floor Collapse" in ctx and "2/4" in ctx
