"""Tests for loremaster-per-scene: find via coarse index, cache + gate deep reads."""

from lib.loremaster import Loremaster

BOOK = (
    "Chapter One\nArrakis, the desert planet. The spice melange flows beneath the dunes.\n\n"
    "Chapter Two\nThe Fremen live in sietches hidden in the rock, masters of the deep desert.\n\n"
    "Chapter Three\nHouse Harkonnen rules from Giedi Prime with cruelty and guile.\n"
)


def test_deep_read_on_new_scene_then_cached_on_revisit(dcc_world):
    lm = Loremaster(dcc_world, book_text=BOOK)
    first = lm.brief_for("Arrakis")
    assert first["deep_read"] is True and first["grounded_excerpt"]
    again = lm.brief_for("Arrakis")  # routine revisit
    assert again["deep_read"] is False and again["cache_hit"] is True


def test_important_forces_deep_read_even_if_cached(dcc_world):
    lm = Loremaster(dcc_world, book_text=BOOK)
    lm.brief_for("Arrakis")
    forced = lm.brief_for("Arrakis", important=True)
    assert forced["deep_read"] is True


def test_brief_is_grounded_in_source(dcc_world):
    lm = Loremaster(dcc_world, book_text=BOOK)
    brief = lm.brief_for("Fremen sietch")
    assert "Fremen" in brief["grounded_excerpt"]
    assert brief["chapters"] and brief["chapters"][0]["index"] == 1


def test_no_book_text_degrades_gracefully(dcc_world):
    lm = Loremaster(dcc_world, book_text="")
    brief = lm.brief_for("Anywhere")
    assert brief["chapters"] == [] and brief["grounded_excerpt"] == ""
