"""Tests for claudemd-lean-core-router: craft skill + proposed lean core draft."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_craft_skill_exists_with_frontmatter():
    p = ROOT / ".claude" / "skills" / "dm-craft" / "SKILL.md"
    assert p.exists()
    text = p.read_text(encoding="utf-8")
    assert text.startswith("---") and "name: dm-craft" in text
    # The soul moved verbatim-in-spirit: the golden rules + key craft principles.
    assert "Yes, and" in text and "Persist before narrating" in text


def test_proposed_lean_core_is_lean_and_complete():
    p = ROOT / "CLAUDE.lean.md"
    assert p.exists()
    text = p.read_text(encoding="utf-8")
    # Lean: the always-on core should be far smaller than the 1227-line CLAUDE.md.
    assert len(text.splitlines()) < 200
    # Complete: keeps the essentials always-on.
    assert "## The Core Loop" in text
    assert "Persist before narrating" in text or "PERSIST" in text
    assert "Action Router" in text


def test_lean_core_routes_to_skills_not_inline_tables():
    text = (ROOT / "CLAUDE.lean.md").read_text(encoding="utf-8")
    for skill in ("dm-combat", "dm-spellcasting", "dm-conditions", "dm-levelup", "dm-dungeon", "dm-craft"):
        assert skill in text
    # It should NOT inline a big lookup table (e.g. the XP-by-CR numbers).
    assert "25,000" not in text


def test_original_claudemd_still_present_until_swap():
    # The destructive swap is gated on human review; the original stays for now.
    assert (ROOT / "CLAUDE.md").exists()
