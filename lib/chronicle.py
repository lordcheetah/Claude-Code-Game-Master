#!/usr/bin/env python3
"""
chronicle.py — compile a played campaign into an illustrated ebook.

Assembles a Markdown manuscript from the campaign's OWN recorded material
(session-log summaries, the chronicler's image plates, the character sheet,
the NPC roster, and the world bible's voice), ready for pandoc to bind into an
EPUB. Deterministic: it arranges what play already produced — it does not invent
prose. The narrative spine is the session-log summaries written at each save.

Usage:
    python lib/chronicle.py <campaign_dir> --out <chronicle.md> [--cover N]
                                           [--no-appendix]
Prints a JSON line: {"md":..., "cover":..., "title":..., "epub":...}
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


def parse_sessions(log_text):
    """Extract ended sessions from session-log.md as ordered chapters."""
    sessions = []
    # Each ended block: "### Session Ended: <ts>\n<summary>\n\n**Session:** N ..."
    blocks = re.split(r"^### Session Ended:.*$", log_text, flags=re.MULTILINE)[1:]
    for b in blocks:
        # summary = text up to the first **Field:** line
        m = re.search(r"\*\*Session:\*\*", b)
        summary = (b[: m.start()] if m else b).strip()
        num = _field(b, "Session")
        loc = _field(b, "Location")
        cliff = _field(b, "Cliffhanger")
        # strip a trailing horizontal rule / stray markers
        summary = re.sub(r"\n-{3,}\s*$", "", summary).strip()
        if not summary:
            continue
        sessions.append({"num": num, "location": loc, "cliffhanger": cliff,
                         "summary": summary})
    return sessions


def _field(block, name):
    m = re.search(rf"\*\*{name}:\*\*\s*(.+)", block)
    return m.group(1).strip() if m else ""


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
                plates.append({"file": f, "title": d.get("title", "").strip(),
                               "chronicler": d.get("chronicler", "").strip()})
    return plates


def find_chronicler(campaign_dir, plates):
    """Best-effort chronicler name for the byline."""
    for p in plates:
        if p.get("chronicler"):
            # gen-log truncates; take the leading name before an em-dash/paren
            c = re.split(r"[—\-(]", p["chronicler"])[0].strip()
            if c:
                return c
    return "the campaign's chronicler"


def esc(s):
    return (s or "").replace("\\", "\\\\").strip()


def build(campaign_dir, out_md, cover_index=None, appendix=True):
    campaign_dir = Path(campaign_dir)
    overview = _load(campaign_dir / "campaign-overview.json", {}) or {}
    bible = _load(campaign_dir / "world-bible.json", {}) or {}
    char = _load(campaign_dir / "character.json", {}) or {}
    npcs = _load(campaign_dir / "npcs.json", {}) or {}
    facts = _load(campaign_dir / "facts.json", {}) or {}
    plates = load_plates(campaign_dir)
    sessions = parse_sessions(_read(campaign_dir / "session-log.md"))

    title = (overview.get("campaign_name") or bible.get("name")
             or campaign_dir.name.replace("-", " ").title())
    genre = overview.get("genre", "")
    author = find_chronicler(campaign_dir, plates)
    hero = char.get("name") or char.get("full_name") or ""

    out = []
    a = out.append

    # --- YAML metadata ---
    a("---")
    a(f'title: "{title}"')
    if hero:
        a(f'subtitle: "A Chronicle of {hero}"')
    a(f'author: "As set down by {author}"')
    a("lang: en")
    a("...")
    a("")

    # --- Title page + epigraph ---
    a(f"# {title}\n")
    if hero:
        a(f"### A Chronicle of {hero}\n")
    if genre:
        a(f"*{genre}*\n")
    a("---\n")
    voice = (bible.get("voice") or {})
    samples = voice.get("sample_passages") or []
    if samples:
        ep = " ".join(samples[0].split())
        a(f"> *{esc(ep)}*\n")
    elif char.get("backstory", {}).get("ideology_beliefs"):
        a(f"> *{esc(char['backstory']['ideology_beliefs'])}*\n")
    a("---\n")

    # --- Dramatis Personae ---
    people = []
    # Skip stat-block templates, corpses, and generic mooks — the roster should
    # read as a cast, not a bestiary.
    _skip = ("template", "generic", "corpse", "stat block", "referenced only",
             "mook", "(unnamed)", "rank-and-file", "test subjects")
    for name, n in (npcs.items() if isinstance(npcs, dict) else []):
        if not isinstance(n, dict):
            continue
        desc = (n.get("role") or n.get("description") or n.get("personality")
                or n.get("notes") or "")
        desc = " ".join(str(desc).split())
        blob = (name + " " + desc).lower()
        if not desc or any(s in blob for s in _skip):
            continue
        people.append((name, desc[:220]))
    if people:
        a("## Dramatis Personae\n")
        if hero:
            hclass = char.get("class") or char.get("occupation") or ""
            a(f"- **{hero}** — {hclass}. The chronicle's protagonist.")
        for name, desc in people[:16]:
            a(f"- **{name}** — {desc}")
        a("")
        a("---\n")

    # --- Character dossier ---
    if char:
        a(f"## The Dossier of {hero}\n")
        bits = []
        for k in ("race", "species", "class", "occupation", "rank", "division"):
            if char.get(k):
                bits.append(str(char[k]))
        if bits:
            a("*" + " · ".join(dict.fromkeys(bits)) + "*\n")
        bs = char.get("backstory")
        # backstory may be a structured dict (D&D/CoC creators) or a prose
        # string (open-schema / hand-authored sheets) — handle both.
        if isinstance(bs, str) and bs.strip():
            a(esc(bs.strip()) + "\n")
            bs = {}
        elif not isinstance(bs, dict):
            bs = {}
        for label, key in (("Beliefs", "ideology_beliefs"),
                           ("Significant people", "significant_people"),
                           ("Treasured", "treasured_possession"),
                           ("Trait", "trait")):
            if bs.get(key):
                a(f"- **{label}:** {esc(bs[key])}")
        a("")
        a("---\n")

    # --- Chapters (session summaries), with plates interleaved ---
    n_ch = max(1, len(sessions))
    # distribute plates across chapters in creation order
    plate_for = {i: [] for i in range(n_ch)}
    if plates and sessions:
        for idx, pl in enumerate(plates):
            plate_for[min(idx * n_ch // max(1, len(plates)), n_ch - 1)].append(pl)

    if sessions:
        for i, s in enumerate(sessions):
            head = f"Chapter {i + 1}"
            if s["location"]:
                head += f" — {s['location']}"
            a(f"# {head}\n")
            a(esc(s["summary"]) + "\n")
            if s["cliffhanger"]:
                a(f"\n*{esc(s['cliffhanger'])}*\n")
            for pl in plate_for.get(i, []):
                cap = pl["title"] or "A plate from the chronicle"
                a(f"\n![{esc(cap)}](images/{pl['file']})\n")
            a("\n---\n")
    else:
        # No played sessions yet — still produce a "world" ebook.
        a("# The World\n")
        if bible.get("themes"):
            a("**Themes.** " + "; ".join(bible["themes"]) + "\n")
        for pl in plates:
            a(f"\n![{esc(pl['title'])}](images/{pl['file']})\n")
        a("\n---\n")

    # --- Appendix: Chronicle of Record (the logged facts) ---
    if appendix and isinstance(facts, dict):
        rows = []
        for cat in ("event", "discovery", "lore", "npc"):
            for item in (facts.get(cat) or []):
                txt = item.get("fact") if isinstance(item, dict) else str(item)
                if txt:
                    rows.append((cat, " ".join(str(txt).split())))
        if rows:
            a("# Appendix — Chronicle of Record\n")
            a("*The beat-by-beat record from which this account was drawn.*\n")
            for cat, txt in rows:
                a(f"- *({cat})* {txt}")
            a("")
            a("---\n")

    # --- Colophon ---
    a("# Colophon\n")
    a(f"Compiled from the chronicle of **{title}**"
      + (f", the record of {hero}," if hero else "")
      + f" and the plates of {author}. "
      + "Assembled by the GM System from the campaign's own session log, "
      + "image gallery, and world bible.\n")

    Path(out_md).write_text("\n".join(out), encoding="utf-8")

    # choose cover: explicit index, else the last plate (usually climactic), else none
    cover = ""
    if plates:
        if cover_index is not None and 1 <= cover_index <= len(plates):
            cover = plates[cover_index - 1]["file"]
        else:
            cover = plates[-1]["file"]
    epub_name = re.sub(r'[<>:"/\\|?*]', "", title) + ".epub"
    return {"md": str(out_md), "cover": cover, "title": title,
            "epub": epub_name, "sessions": len(sessions), "plates": len(plates)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("campaign_dir")
    ap.add_argument("--out", required=True)
    ap.add_argument("--cover", type=int, default=None)
    ap.add_argument("--no-appendix", action="store_true")
    args = ap.parse_args()
    info = build(args.campaign_dir, args.out, cover_index=args.cover,
                 appendix=not args.no_appendix)
    print(json.dumps(info))


if __name__ == "__main__":
    main()
