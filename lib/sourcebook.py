#!/usr/bin/env python3
"""
sourcebook.py — compile a world's REFERENCE material into a table-ready TTRPG
sourcebook (the boxed-set inverse of chronicle.py).

Where chronicle.py sets down what a campaign *played*, sourcebook.py assembles
everything a GM needs to *run* the world at a table with no computer: the setting
(world bible), the rules of play (the World Kit rendered as readable rules), the
cast (NPC roster + stat blocks), a gazetteer (locations + a travel table drawn
from their connections), a bestiary, a treasury, an adventure front (hooks), and
appendices (pregens, random tables, the world's tongues, an art-plate gallery).

Deterministic at the core: it arranges the campaign's own structured data. The
`sourcebook-author` agent enriches it by writing an optional prose companion file
(sourcebook-prose.json) — the rules taught in plain language, GM guidance, voiced
section intros, gap-filled stat blocks, pregens, random tables, and a starter
adventure. When that file is absent this still produces a full reference tome; the
prose file is what turns it into a runnable boxed set.

Usage:
    python lib/sourcebook.py <campaign_dir> --out <sourcebook.md>
        [--prose <sourcebook-prose.json>] [--cover N] [--no-adventure]
Prints a JSON line: {"md":..., "cover":..., "title":..., "epub":..., counts...}
"""

import json
import re
import sys
import argparse
from pathlib import Path


def _load(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return default


def _read(path, default=""):
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception:
        return default


def _demojibake(s):
    """Repair UTF-8-decoded-as-cp1252 double-encoding (â€" → em dash).

    The campaign JSON files store some strings mojibake'd (e.g. an em dash shows
    up as the three chars â‚¬"). Only strings carrying the tell-tale markers are
    touched, and only if the round-trip decodes cleanly — otherwise the original
    is returned untouched, so plain text is never corrupted.
    """
    if not s or not isinstance(s, str):
        return s
    if not any(m in s for m in ("Ã", "â€", "â\x80", "Â\xa0", "Â ")):
        return s
    try:
        return s.encode("cp1252", errors="strict").decode("utf-8", errors="strict")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s


def esc(s):
    """Clean a value for Markdown: repair mojibake, collapse whitespace, trim."""
    if s is None:
        return ""
    return _demojibake(" ".join(str(s).split())).replace("\\", "\\\\").strip()


def _nodes(section):
    """Return the node list from a bible graph section ({'nodes':[...]}) or a list."""
    if isinstance(section, dict):
        return section.get("nodes") or []
    if isinstance(section, list):
        return section
    return []


def _items(coll):
    """Yield (name, record) pairs from a dict-keyed-by-name or a list collection."""
    if isinstance(coll, dict):
        for name, rec in coll.items():
            yield name, rec
    elif isinstance(coll, list):
        for rec in coll:
            if isinstance(rec, dict):
                yield rec.get("name") or rec.get("id") or "", rec


# --- section renderers ----------------------------------------------------

def _appearance_line(rec):
    """One-line physical read from a visual_appearance block, if present."""
    va = rec.get("visual_appearance") if isinstance(rec, dict) else None
    if not isinstance(va, dict):
        return ""
    order = ("sex", "age", "race", "species", "hair", "eyes", "face",
             "clothing", "gear", "demeanor", "size")
    bits = [esc(va[k]) for k in order if va.get(k)]
    return "; ".join(b for b in bits if b)


def _statblock(rec):
    """Render a creature/NPC stat block from whatever stat fields exist."""
    if not isinstance(rec, dict):
        return []
    # Accept a pre-formatted markdown block from the prose companion first.
    if isinstance(rec.get("stat_block"), str) and rec["stat_block"].strip():
        return [esc_block(rec["stat_block"])]
    stats = rec.get("stats") if isinstance(rec.get("stats"), dict) else {}
    combat = rec.get("combat") if isinstance(rec.get("combat"), dict) else {}
    src = {**stats, **combat}
    for k in ("hp", "max_hp", "ac", "cr", "level", "attack", "damage",
              "speed", "initiative"):
        if rec.get(k) is not None and k not in src:
            src[k] = rec[k]
    if not src:
        return []
    order = [("hp", "HP"), ("max_hp", "Max HP"), ("ac", "AC"), ("cr", "CR"),
             ("level", "Level"), ("attack", "Attack"), ("damage", "Damage"),
             ("speed", "Speed"), ("initiative", "Init")]
    seen = set()
    parts = []
    for key, label in order:
        if src.get(key) not in (None, "") and key not in seen:
            parts.append(f"**{label}** {esc(src[key])}")
            seen.add(key)
    for key, val in src.items():
        if key in seen or val in (None, "", [], {}):
            continue
        parts.append(f"**{esc(key.replace('_', ' ').title())}** {esc(val)}")
    return ["> " + " · ".join(parts)] if parts else []


def esc_block(s):
    """Repair mojibake in a multi-line markdown block without collapsing its lines."""
    if not s:
        return ""
    return "\n".join(_demojibake(line) for line in str(s).splitlines()).strip()


def _demote(md, levels=1):
    """Push every ATX heading down `levels` (# -> ##) so an embedded document
    nests under its host section instead of surfacing as a top-level part.
    Capped at H6."""
    out = []
    for line in str(md).splitlines():
        m = re.match(r"^(#{1,6})(\s)", line)
        if m:
            new = "#" * min(6, len(m.group(1)) + levels)
            line = new + line[len(m.group(1)):]
        out.append(line)
    return "\n".join(out)


def _skip_npc(name, rec):
    """Filter stat-block templates, corpses, and generic mooks from the cast."""
    desc = ""
    if isinstance(rec, dict):
        desc = (rec.get("description") or rec.get("role") or rec.get("personality")
                or rec.get("notes") or "")
    blob = (str(name) + " " + str(desc)).lower()
    skip = ("template", "generic mook", "corpse", "(unnamed)", "rank-and-file",
            "test subjects", "referenced only")
    return not str(name).strip() or any(s in blob for s in skip)


def load_plates(campaign_dir):
    """Read the chronicler's image plates (title + file) in creation order."""
    log = campaign_dir / "images" / "_gen-log.jsonl"
    plates = []
    if log.exists():
        for line in log.read_text(encoding="utf-8").splitlines():
            try:
                d = json.loads(line)
            except Exception:
                continue
            f = d.get("file")
            if f and (campaign_dir / "images" / f).exists():
                plates.append({"file": f, "title": esc(d.get("title", "")),
                               "chronicler": esc(d.get("chronicler", ""))})
    return plates


def build(campaign_dir, out_md, prose_path=None, cover_index=None,
          adventure=True):
    campaign_dir = Path(campaign_dir)
    overview = _load(campaign_dir / "campaign-overview.json", {}) or {}
    bible = _load(campaign_dir / "world-bible.json", {}) or {}
    ruleset = _load(campaign_dir / "ruleset.json", {}) or {}
    npcs = _load(campaign_dir / "npcs.json", {}) or {}
    locations = _load(campaign_dir / "locations.json", {}) or {}
    items = _load(campaign_dir / "items.json", {}) or {}
    plots = _load(campaign_dir / "plots.json", {}) or {}
    facts = _load(campaign_dir / "facts.json", {}) or {}
    chronicler = _load(campaign_dir / "chronicler.json", {}) or {}
    plates = load_plates(campaign_dir)

    # Prose companion (agent-authored). Default to the conventional path.
    if prose_path is None:
        default_prose = campaign_dir / "sourcebook-prose.json"
        prose_path = str(default_prose) if default_prose.exists() else None
    prose = _load(prose_path, {}) if prose_path else {}
    prose = prose or {}
    intros = prose.get("section_intros") or {}
    npc_notes = prose.get("npc_notes") or {}

    title = (prose.get("title") or ruleset.get("name")
             or overview.get("campaign_name") or bible.get("name")
             or campaign_dir.name.replace("-", " ").title())
    title = esc(title)
    genre = esc(overview.get("genre", ""))
    subtitle = esc(prose.get("subtitle") or "A Sourcebook for the Table")
    author = esc(prose.get("author") or "the Loremasters of the House")

    out = []
    a = out.append

    def part(heading):
        a(f"# {heading}\n")

    def intro(key):
        if intros.get(key):
            a(esc_block(intros[key]) + "\n")

    # --- YAML metadata ---
    a("---")
    a(f'title: "{title}"')
    a(f'subtitle: "{subtitle}"')
    a(f'author: "Compiled by {author}"')
    a("lang: en")
    a("...")
    a("")

    # --- Title page + epigraph ---
    a(f"# {title}\n")
    a(f"### {subtitle}\n")
    if genre:
        a(f"*{genre}*\n")
    a("---\n")
    voice = bible.get("voice") or {}
    samples = voice.get("sample_passages") or []
    epigraph = ""
    if samples:
        epigraph = esc(samples[0])
    elif bible.get("themes"):
        epigraph = esc(bible["themes"][0])
    if epigraph:
        a(f"> *{epigraph}*\n")
    a("---\n")

    # --- Preface: How to Use This Book ---
    a("# How to Use This Book\n")
    if prose.get("preface"):
        a(esc_block(prose["preface"]) + "\n")
    else:
        a("This sourcebook holds everything needed to run this world at the "
          "table. **Part I** describes the world; **Part II** teaches how to "
          "play it; the later parts are the reference you reach for in play — "
          "the cast, the map, the monsters, the treasure, and the hooks that "
          "start an adventure.\n")
    a("---\n")

    # ===================== PART I — THE WORLD =====================
    part("Part I · The World")
    intro("setting")
    if not intros.get("setting"):
        tagline = bible.get("premise") or overview.get("premise") or ""
        if tagline:
            a(esc(tagline) + "\n")

    if bible.get("themes"):
        a("## Themes\n")
        for t in bible["themes"]:
            a(f"- {esc(t)}")
        a("")

    tone = bible.get("tone")
    if isinstance(tone, dict) and tone:
        mix = ", ".join(f"{esc(k.replace('_', ' '))} {v}%"
                        for k, v in tone.items())
        a(f"**Tone.** {mix}.\n")
    if isinstance(voice.get("style"), str) and voice["style"].strip():
        a(f"**Voice.** {esc(voice['style'])}\n")

    timeline = bible.get("timeline")
    if isinstance(timeline, list) and timeline:
        a("## History\n")
        for entry in timeline:
            if isinstance(entry, dict):
                when = esc(entry.get("when") or entry.get("era") or entry.get("date"))
                event = esc(entry.get("event") or entry.get("description") or "")
                a(f"- **{when}** — {event}" if when else f"- {event}")
            else:
                a(f"- {esc(entry)}")
        a("")

    geo = _nodes(bible.get("geography"))
    if geo:
        a("## The Lay of the Land\n")
        for n in geo:
            if not isinstance(n, dict):
                continue
            nm = esc(n.get("name") or n.get("id"))
            if nm:
                a(f"**{nm}.** {esc(n.get('description'))}\n")

    fac = _nodes(bible.get("factions"))
    if fac:
        a("## Powers & Factions\n")
        for n in fac:
            if not isinstance(n, dict):
                continue
            nm = esc(n.get("name") or n.get("id"))
            if nm:
                a(f"**{nm}.** {esc(n.get('description'))}\n")

    sig = bible.get("signature_systems") or ruleset.get("signature_systems")
    if isinstance(sig, list) and sig:
        a("## What Makes This World Itself\n")
        for s in sig:
            a(f"- {esc(s)}")
        a("")
    a("---\n")

    # ===================== PART II — HOW TO PLAY =====================
    part("Part II · How to Play")
    if prose.get("how_to_play"):
        # The agent's taught-rules chapter is the primary rules text.
        a(esc_block(prose["how_to_play"]) + "\n")
    else:
        # Deterministic fallback: render the World Kit as reference rules.
        _render_kit(a, ruleset, campaign_dir)
    if prose.get("gm_guidance"):
        a("## Guidance for the Game Master\n")
        a(esc_block(prose["gm_guidance"]) + "\n")
    a("---\n")

    # ===================== PART III — THE CAST =====================
    cast = [(nm, r) for nm, r in _items(npcs)
            if isinstance(r, dict) and not _skip_npc(nm, r)]
    if cast:
        part("Part III · The Cast")
        intro("npcs")
        for nm, r in cast:
            a(f"## {esc(nm)}\n")
            role = esc(r.get("role") or r.get("occupation") or "")
            attitude = esc(r.get("attitude") or "")
            meta = " · ".join(x for x in (role, attitude and f"disposition: {attitude}") if x)
            if meta:
                a(f"*{meta}*\n")
            look = _appearance_line(r)
            if look:
                a(f"**Appearance.** {look}\n")
            desc = esc(r.get("description") or r.get("personality") or "")
            if desc:
                a(desc + "\n")
            for line in _statblock(r):
                a(line + "\n")
            if npc_notes.get(nm):
                a(f"**Running {esc(nm)}.** {esc_block(npc_notes[nm])}\n")
        a("---\n")

    # ===================== PART IV — GAZETTEER =====================
    locs = [(nm, r) for nm, r in _items(locations) if isinstance(r, dict) and nm]
    if locs:
        part("Part IV · Gazetteer")
        intro("gazetteer")
        for nm, r in locs:
            a(f"## {esc(nm)}\n")
            if r.get("position"):
                a(f"*{esc(r['position'])}*\n")
            if r.get("description"):
                a(esc(r["description"]) + "\n")
            conns = r.get("connections")
            if isinstance(conns, list) and conns:
                a("**Travel from here:**\n")
                a("| To | Route |")
                a("| --- | --- |")
                for c in conns:
                    if isinstance(c, dict) and c.get("to"):
                        a(f"| {esc(c['to'])} | {esc(c.get('path') or '—')} |")
                a("")
        a("---\n")

    # ===================== PART V — BESTIARY =====================
    bestiary = prose.get("bestiary") or []
    if isinstance(bestiary, list) and bestiary:
        part("Part V · Bestiary")
        intro("bestiary")
        for m in bestiary:
            if not isinstance(m, dict):
                continue
            a(f"## {esc(m.get('name'))}\n")
            if m.get("description"):
                a(esc(m["description"]) + "\n")
            for line in _statblock(m):
                a(line + "\n")
            if m.get("tactics"):
                a(f"**Tactics.** {esc(m['tactics'])}\n")
        a("---\n")

    # ===================== PART VI — TREASURY =====================
    treasure = list(_items(items))
    prose_treasure = prose.get("treasury") or []
    if treasure or prose_treasure:
        part("Part VI · Treasury")
        intro("treasury")
        for nm, r in treasure:
            if not isinstance(r, dict) or not nm:
                continue
            a(f"**{esc(nm)}.** " + esc(r.get("description") or r.get("effect") or "") )
            for line in _statblock(r):
                a("\n" + line)
            a("")
        for t in prose_treasure:
            if isinstance(t, dict) and t.get("name"):
                a(f"**{esc(t['name'])}.** {esc_block(t.get('description', ''))}\n")
        a("---\n")

    # ===================== PART VII — ADVENTURE FRONT =====================
    if adventure:
        hooks = []
        for _, r in _items(plots):
            if isinstance(r, dict):
                h = r.get("hook") or r.get("summary") or r.get("description") or r.get("name")
                if h:
                    hooks.append(esc(h))
        if isinstance(facts, dict):
            for cat in ("lore", "discovery", "event"):
                for it in (facts.get(cat) or [])[:8]:
                    txt = it.get("fact") if isinstance(it, dict) else str(it)
                    if txt:
                        hooks.append(esc(txt))
        starter = prose.get("starter_adventure")
        if hooks or starter:
            part("Part VII · The Adventure Front")
            intro("adventure")
            if hooks:
                a("## Hooks & Rumors\n")
                for h in dict.fromkeys(hooks):  # dedupe, keep order
                    a(f"- {h}")
                a("")
            if starter:
                a("## Starter Adventure\n")
                a(esc_block(starter) + "\n")
            a("---\n")

    # ===================== APPENDICES =====================
    pregens = prose.get("pregens") or []
    if isinstance(pregens, list) and pregens:
        part("Appendix A · Pregenerated Characters")
        for p in pregens:
            if not isinstance(p, dict):
                continue
            a(f"## {esc(p.get('name'))}\n")
            tag = " · ".join(esc(p[k]) for k in ("race", "species", "class",
                             "role", "occupation") if p.get(k))
            if tag:
                a(f"*{tag}*\n")
            if p.get("sheet"):
                a(esc_block(p["sheet"]) + "\n")
            else:
                for line in _statblock(p):
                    a(line + "\n")
                if p.get("description"):
                    a(esc(p["description"]) + "\n")
        a("---\n")

    tables = prose.get("random_tables") or []
    if isinstance(tables, list) and tables:
        part("Appendix B · Random Tables")
        for t in tables:
            if not isinstance(t, dict):
                continue
            a(f"## {esc(t.get('title'))}\n")
            entries = t.get("entries") or []
            a("| d%d | Result |" % max(len(entries), 1) if entries else "| Roll | Result |")
            a("| --- | --- |")
            for i, e in enumerate(entries, 1):
                a(f"| {i} | {esc(e)} |")
            a("")
        a("---\n")

    tongues = _load_tongues(campaign_dir)
    if tongues:
        part("Appendix C · Tongues of the World")
        for t in tongues:
            a(f"## {esc(t['culture'])}\n")
            if t.get("samples"):
                for s in t["samples"][:8]:
                    a(f"- {esc(s)}")
                a("")
        a("---\n")

    if plates:
        part("Appendix D · Plates")
        a("*Illustrations set down for this world.*\n")
        for pl in plates:
            cap = pl["title"] or "A plate"
            a(f"![{esc(cap)}](images/{pl['file']})\n")
        a("---\n")

    # --- Colophon ---
    a("# Colophon\n")
    a(f"A sourcebook for **{title}**, compiled by the GM System from the world's "
      f"own kit, bible, cast, and gazetteer" +
      (f", with plates by {esc(chronicler.get('name'))}" if chronicler.get("name") else "") +
      ". Everything here is drawn from the world as recorded; bring dice.\n")

    Path(out_md).write_text("\n".join(out), encoding="utf-8")

    cover = ""
    if plates:
        if cover_index is not None and 1 <= cover_index <= len(plates):
            cover = plates[cover_index - 1]["file"]
        else:
            cover = plates[0]["file"]  # first plate — usually the establishing shot
    epub_name = re.sub(r'[<>:"/\\|?*]', "", title) + " — Sourcebook.epub"
    return {"md": str(out_md), "cover": cover, "title": title,
            "epub": epub_name, "npcs": len(cast) if cast else 0,
            "locations": len(locs) if locs else 0,
            "bestiary": len(bestiary) if isinstance(bestiary, list) else 0,
            "pregens": len(pregens) if isinstance(pregens, list) else 0,
            "plates": len(plates), "prose": bool(prose)}


def _render_kit(a, ruleset, campaign_dir=None):
    """Deterministic fallback rules chapter, straight from ruleset.json."""
    if not ruleset:
        a("*No World Kit was found for this campaign; supply the rules of play "
          "here.*\n")
        return
    schema = ruleset.get("stat_schema") or {}
    attrs = schema.get("attributes") or []
    notes = schema.get("attribute_notes") or {}
    if attrs:
        a("## Attributes\n")
        for at in attrs:
            note = esc(notes.get(at, ""))
            a(f"- **{esc(str(at).title())}**" + (f" — {note}" if note else ""))
        a("")
    vitals = schema.get("vitals") or []
    vnotes = schema.get("vitals_notes") or {}
    if vitals:
        a("## Vitals\n")
        for v in vitals:
            note = esc(vnotes.get(v, ""))
            a(f"- **{esc(str(v).upper())}**" + (f" — {note}" if note else ""))
        a("")

    res = ruleset.get("resolution") or {}
    if res:
        a("## Making Rolls\n")
        model = esc(res.get("model", ""))
        if model:
            a(f"**Resolution model:** {model}.\n")
        if res.get("notes"):
            a(esc(res["notes"]) + "\n")

    prog = ruleset.get("progression") or {}
    if prog:
        a("## Advancement\n")
        model = esc(prog.get("model", ""))
        resource = esc(prog.get("resource", ""))
        if model:
            a(f"**Model:** {model}" + (f" (tracked as *{resource}*)" if resource else "") + ".\n")
        if prog.get("rationale"):
            a(esc(prog["rationale"]) + "\n")
        grades = prog.get("grades")
        tiers = prog.get("tiers")
        if isinstance(grades, list) and grades:
            a("**Ranks:**\n")
            for g in grades:
                a(f"- {esc(g)}")
            a("")
        elif isinstance(tiers, list) and tiers:
            a("**Thresholds:** " + ", ".join(str(t) for t in tiers) + ".\n")

    sig = ruleset.get("signature_systems")
    if isinstance(sig, list) and sig:
        a("## Signature Systems\n")
        for s in sig:
            if isinstance(s, dict):
                nm = esc(s.get("name"))
                dsc = esc(s.get("description") or s.get("summary"))
                a(f"- **{nm}.** {dsc}" if nm else f"- {dsc}")
            else:
                a(f"- {esc(s)}")
        a("")

    rules_doc = ruleset.get("rules_doc")
    if isinstance(rules_doc, str) and rules_doc.strip():
        # rules_doc may be inline rules text, or a filename pointing at the
        # campaign's rules.md — resolve the reference to the actual document.
        stripped = rules_doc.strip()
        if campaign_dir and re.fullmatch(r"[\w.\-/]+\.md", stripped):
            resolved = _read(Path(campaign_dir) / stripped, "").strip()
            rules_doc = resolved or ""
        if rules_doc and len(rules_doc) < 20000:
            a("## The Rules in Full\n")
            # Demote the embedded doc's headings so its own H1 doesn't become a
            # sibling of the Parts in the table of contents.
            a(_demote(esc_block(rules_doc), 2) + "\n")


def _load_tongues(campaign_dir):
    """Pull conlang sample lines from languages/*.json for the appendix."""
    langdir = campaign_dir / "languages"
    tongues = []
    if not langdir.is_dir():
        return tongues
    for f in sorted(langdir.glob("*.json")):
        d = _load(f, {}) or {}
        culture = d.get("culture") or f.stem.replace("-", " ").title()
        samples = []
        for key in ("samples", "phrases", "sample_phrases", "cached_samples"):
            v = d.get(key)
            if isinstance(v, list):
                for entry in v:
                    if isinstance(entry, str):
                        samples.append(entry)
                    elif isinstance(entry, dict):
                        native = entry.get("native") or entry.get("word") or ""
                        gloss = entry.get("gloss") or entry.get("english") or ""
                        if native and gloss:
                            samples.append(f"{native} — {gloss}")
                        elif native:
                            samples.append(native)
        if samples:
            tongues.append({"culture": culture, "samples": samples})
    return tongues


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("campaign_dir")
    ap.add_argument("--out", required=True)
    ap.add_argument("--prose", default=None)
    ap.add_argument("--cover", type=int, default=None)
    ap.add_argument("--no-adventure", action="store_true")
    args = ap.parse_args()
    info = build(args.campaign_dir, args.out, prose_path=args.prose,
                 cover_index=args.cover, adventure=not args.no_adventure)
    print(json.dumps(info))


if __name__ == "__main__":
    main()
