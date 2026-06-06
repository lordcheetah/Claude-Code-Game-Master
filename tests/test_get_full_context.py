"""Characterization tests for SessionManager.get_full_context — seam #1.

These snapshot the CURRENT (post-cleanup) behavior so later reimagining tickets
(story-spine-context, untruncate-campaign-rules, ...) can change it deliberately
and see exactly what moved. They also lock in the consequence-display fix.
"""

from lib.session_manager import SessionManager


def _context(dcc_world):
    ctx = SessionManager(dcc_world).get_full_context()
    assert isinstance(ctx, str) and ctx, "get_full_context must return a non-empty string"
    return ctx


def test_context_includes_active_character(dcc_world):
    assert "Tandy" in _context(dcc_world)


def test_context_has_pending_consequences_section(dcc_world):
    assert "PENDING CONSEQUENCES" in _context(dcc_world)


def test_pending_consequences_render_real_text_not_unknown(dcc_world):
    """Regression guard for the consequence-display bug.

    The pre-cleanup code iterated the wrong structure and read non-existent
    fields, so every consequence rendered as 'Unknown' (or the section showed
    '(none)'). Real consequence text must appear and the 'Unknown' sentinel
    must not.
    """
    ctx = _context(dcc_world)
    assert any(name in ctx for name in ("Squeeks", "Nightstalker", "Mongo", "Sheol")), (
        "expected at least one real DCC consequence to surface"
    )
    # The bug rendered each consequence as "[id] Unknown -> triggers: ...".
    assert "Unknown -> triggers" not in ctx


def test_context_includes_campaign_rules_block(dcc_world):
    """DCC's bespoke rules should be present (untruncate-campaign-rules will
    later assert they are present IN FULL; here we just pin that they appear)."""
    ctx = _context(dcc_world)
    assert any(
        rule in ctx for rule in ("loot_box_system", "audience_system", "interview_system")
    ), "expected DCC campaign_rules to appear in the context"
