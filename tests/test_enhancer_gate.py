"""Tests for enhancer-relevance-gate: _gate_passages relevance filtering."""

from lib.entity_enhancer import EntityEnhancer


def _p(text, distance):
    return {"text": text, "distance": distance}


def test_name_bearing_force_included_even_above_floor():
    # A passage that names the entity but has poor (high) distance must survive.
    passages = [
        _p("Hekla raised her crossbow.", 1.4),   # names entity, above 1.0 floor
        _p("unrelated scenery prose", 0.3),       # close but no name
    ]
    kept, frac = EntityEnhancer._gate_passages("Hekla", [], passages, floor=1.0, keep_target=4)
    texts = [p["text"] for p in kept]
    assert "Hekla raised her crossbow." in texts, "name-bearing passage must be force-included"
    assert frac > 0


def test_below_floor_non_name_passages_dropped_not_padded():
    passages = [
        _p("Hekla spoke.", 0.4),          # name-bearing
        _p("far-off noise", 1.3),         # no name, above floor -> dropped
        _p("more noise", 1.6),            # no name, above floor -> dropped
    ]
    kept, frac = EntityEnhancer._gate_passages("Hekla", [], passages, floor=1.0, keep_target=4)
    assert len(kept) == 1, "should NOT pad with below-floor noise"
    assert frac == 1.0


def test_zero_name_bearing_yields_zero_fraction():
    passages = [_p("a passage about someone else", 0.5), _p("another", 0.6)]
    kept, frac = EntityEnhancer._gate_passages("Tserendolgor", [], passages, floor=1.0)
    assert frac == 0.0, "no passage names the entity -> fraction 0 (flagged for curation)"


def test_aliases_count_as_name_bearing():
    passages = [_p("Princess Donut shrieked.", 0.7)]
    kept, frac = EntityEnhancer._gate_passages("Donut", ["Princess Donut"], passages, floor=1.0)
    assert frac == 1.0


def test_fill_respects_floor_and_target():
    passages = [
        _p("Carl did a thing.", 0.2),     # name
        _p("close scene A", 0.5),         # under floor
        _p("close scene B", 0.9),         # under floor
        _p("close scene C", 0.95),        # under floor (would exceed target)
    ]
    kept, frac = EntityEnhancer._gate_passages("Carl", [], passages, floor=1.0, keep_target=3)
    # 1 name-bearing + fill to target 3 => 3 total, lowest-distance others first
    assert len(kept) == 3
    assert kept[0]["distance"] == 0.2
