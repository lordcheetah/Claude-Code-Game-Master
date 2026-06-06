"""End-to-end eval: an original world comes out GROUNDED.

Drives the authored-world pipeline (consolidate -> compile-canon -> confirm) over
a fixed seed fixture into a hermetic temp world-state, then asserts the grounding
contract that stops drift to generic D&D: a valid+confirmed world-bible, a non-5e
World Kit, populated runtime state that passes the schema validator, and an
embed-ready corpus. The heavy live-RAG assertion (real embedding + a vector hit)
runs only when sentence-transformers + chromadb import AND the model loads;
otherwise it skips with a reason (never a silent pass).
"""

import json
import sys
from pathlib import Path

import pytest

LIB = str(Path(__file__).resolve().parent.parent / "lib")
if LIB not in sys.path:
    sys.path.insert(0, LIB)

from world_author import WorldAuthor
from world_bible import WorldBible, validate_bible
from world_kit import WorldKit, DEFAULT_RULESET
from schemas import validate_world_state


def _build_fixture(tmp_path):
    """A Conan-style seed already fanned-out: skeleton + authored/* + canon/* + kit."""
    ws = tmp_path / "world-state"
    camp = ws / "campaigns" / "cinderworld"
    (camp / "authored").mkdir(parents=True)
    (camp / "canon").mkdir(parents=True)
    (ws / "active-campaign.txt").write_text("cinderworld")

    (camp / "world-seed.json").write_text(json.dumps({
        "premise": "Conan but on a drowned, ash-choked coast",
        "tone": "sword-and-sorcery", "magic": "rare", "setting": "coastal port",
        "genre_bend": "magic is blood-priced and villainous; bronze-age tech",
        "axes": [
            {"axis": "geography", "depth": "deep", "bend": "ash coast"},
            {"axis": "factions", "depth": "deep", "bend": "toll-sworn vs free divers"},
            {"axis": "magic-lore", "depth": "deep", "bend": "blood-priced curses"},
        ],
    }))
    # Skeleton authored in one pass, confirmed:false (awaiting approval)
    (camp / "world-bible.json").write_text(json.dumps({
        "name": "The Ashfall Coast", "voice": {"style": "grim, terse", "vocab": ["toll-sworn"]},
        "tone": "sword-and-sorcery", "themes": ["rust", "debt"],
        "factions": {"nodes": [], "edges": []}, "geography": {"nodes": [], "edges": []},
        "signature_systems": [{"name": "Blood-priced sorcery", "summary": "spells cost blood"}],
        "timeline": [], "confirmed": False,
    }))
    (camp / "authored" / "geography.json").write_text(json.dumps({
        "locations": {"Ashfall Reach": {"position": "crater-rim port", "connections": [
            {"to": "The Cinder Gate", "path": "down the slag road"}], "description": "A port in a dead volcano, black sand and rust."}},
        "bible": {"geography": {"nodes": [{"name": "Ashfall Reach"}], "edges": [
            {"from": "Ashfall Reach", "to": "The Cinder Gate", "type": "road"}]}, "themes": ["rust"]},
    }))
    (camp / "authored" / "factions.json").write_text(json.dumps({
        "npcs": {"Warden Olm": {"description": "Iron-fisted toll keeper of the Cinder Gate.",
                                 "attitude": "suspicious", "tags": {"locations": ["Ashfall Reach"], "quests": []}}},
        "facts": {"plot_local": ["The Cinder Gate toll tripled overnight and divers are vanishing."]},
        "bible": {"factions": {"nodes": [{"name": "The Toll-Sworn"}], "edges": [
            {"from": "The Toll-Sworn", "to": "Free Divers", "type": "rivalry"}]}, "themes": ["debt"]},
    }))
    (camp / "authored" / "magic-lore.json").write_text(json.dumps({
        "facts": {"lore_magic": ["Sorcery is paid in blood; each working scars the caster with rust-rot."]},
        "bible": {"signature_systems": [{"name": "Rust-rot corruption", "summary": "casting accrues corruption"}]},
    }))
    (camp / "canon" / "geography.md").write_text("## Ashfall Reach\nA crater-rim port of black sand where the sea returns the drowned.")
    (camp / "canon" / "magic-lore.md").write_text("## Blood-priced sorcery\nNo spell is free; the Ashfall mages pay in blood and rust-rot.")
    (camp / "ruleset.json").write_text(json.dumps({
        "name": "The Ashfall Coast (blood-sorcery pulp)",
        "stat_schema": {"attributes": ["str", "agi", "wits", "nerve"], "vitals": ["hp", "corruption"]},
        "progression": {"model": "milestone"}, "resolution": {"model": "d20-vs-dc"},
        "active_agents": ["monster-manual", "rules-master", "gear-master", "loot-dropper", "npc-builder"],
        "signature_systems": [{"name": "Blood-priced sorcery", "summary": "spells cost HP + corruption", "rules": "no slots"}],
    }))
    return ws, camp


def test_creation_pipeline_grounds_the_world(tmp_path):
    ws, camp = _build_fixture(tmp_path)
    wa = WorldAuthor(world_state_dir=str(ws), campaign="cinderworld")

    rep = wa.consolidate()
    assert rep["files"] == 3 and rep["npcs"] >= 1 and rep["facts"] >= 2 and rep["bible_merged"], rep

    # bible: valid, graphs merged, then confirm flips the gate
    bible = json.loads((camp / "world-bible.json").read_text())
    ok, errs = validate_bible(bible); assert ok, errs
    assert any(n["name"] == "Ashfall Reach" for n in bible["geography"]["nodes"])
    assert any(n["name"] == "The Toll-Sworn" for n in bible["factions"]["nodes"])
    assert bible["confirmed"] is False
    WorldBible(world_state_dir=str(ws)).confirm()
    assert json.loads((camp / "world-bible.json").read_text())["confirmed"] is True

    # World Kit: loads + is NOT the generic 5e/default kit
    kit = WorldKit(world_state_dir=str(ws))
    assert kit.name() != DEFAULT_RULESET["name"]
    assert kit.stat_schema().get("attributes") and "corruption" in kit.stat_schema().get("vitals", [])
    assert kit.ruleset.get("signature_systems")
    assert "spell-caster" not in kit.active_agents()

    # runtime state populated in valid shapes
    locs = json.loads((camp / "locations.json").read_text())
    npcs = json.loads((camp / "npcs.json").read_text())
    facts = json.loads((camp / "facts.json").read_text())
    assert "Ashfall Reach" in locs and locs["Ashfall Reach"]["discovered"]
    assert npcs["Warden Olm"]["attitude"] == "suspicious" and npcs["Warden Olm"]["created"]
    assert facts["plot_local"] and facts["lore_magic"]

    # world-check / schema validator: no errors anywhere
    results = validate_world_state(str(camp))
    bad = {f: e for f, e in results.items() if e}
    assert not bad, bad

    # corpus is embed-ready (this text becomes current-document.txt via `prepare`)
    out = wa.compile_canon()
    text = (camp / "authored-canon.md").read_text()
    assert out["bytes"] > 0 and "Ashfall Reach" in text and "blood" in text.lower()


def test_live_rag_grounding_if_available(tmp_path):
    """Real grounding path: embed the canon and confirm a query returns a hit."""
    pytest.importorskip("sentence_transformers")
    pytest.importorskip("chromadb")
    ws, camp = _build_fixture(tmp_path)
    wa = WorldAuthor(world_state_dir=str(ws), campaign="cinderworld")
    wa.consolidate()
    canon_path = wa.compile_canon()["path"]

    try:
        from agent_extractor import AgentExtractor
        ax = AgentExtractor(world_state_dir=str(ws), campaign_name="cinderworld")
        ax.prepare_for_agents(canon_path)
    except Exception as e:  # offline model download, backend init, etc.
        pytest.skip(f"RAG embed unavailable in this environment: {e}")

    doc = camp / "current-document.txt"
    assert doc.exists() and doc.read_text().strip(), "prepare must write a non-empty current-document.txt"

    try:
        from rag.vector_store import CampaignVectorStore
        from rag.embedder import LocalEmbedder
        store = CampaignVectorStore(str(camp))
        hits = store.query_by_text("blood-priced sorcery", LocalEmbedder(), n_results=3)
    except Exception as e:
        pytest.skip(f"vector query unavailable: {e}")
    assert hits.get("documents"), "RAG query for an authored concept must return at least one hit"
