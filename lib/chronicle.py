#!/usr/bin/env python3
"""
chronicle.py — compile a played campaign into an illustrated ebook.

Assembles a Markdown manuscript from the campaign's OWN recorded material
(the played narration recorded beat-by-beat in narration-log.jsonl, the
chronicler's image plates, the character sheet, the NPC roster, and the world
bible's voice), ready for pandoc to bind into an EPUB. Deterministic: it
arranges what play already produced — it does not invent prose. The narrative
spine is the recorded narration; each chapter is a session, with plates dropped
in where they were generated. Sessions with no recorded prose (played before
narration recording, or with it toggled off) fall back to their session-log
summary, so old campaigns still compile.

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
from datetime import datetime, timezone


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


def _parse_ts(s):
    """Parse the timestamp forms used across the campaign into a UTC datetime:
    the image gen-log's ISO 'Z' form, session-log's 'YYYY-MM-DD HH:MM:SS UTC',
    and narration-log's ISO. Returns None if unparseable."""
    if not s:
        return None
    s = str(s).strip()
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S UTC",
                "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
        except ValueError:
            continue
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
    except Exception:
        return None


_FENCE_RE = re.compile(r"^```.*?^```", re.MULTILINE | re.DOTALL)


def _clean_prose(text):
    """Light scrub of the recorded beat for print: drop fenced code blocks (the
    status-bar / HP-bar headers are always fenced) and collapse runs of blank
    lines. The GM is asked to record prose sans menu, so this is just a net."""
    text = _FENCE_RE.sub("", text or "")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def load_beats(campaign_dir):
    """Recorded narration beats (with parsed ts) in chronological order."""
    path = Path(campaign_dir) / "narration-log.jsonl"
    beats = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                b = json.loads(line)
            except Exception:
                continue
            b["_dt"] = _parse_ts(b.get("ts"))
            beats.append(b)
    return beats


def parse_sessions(log_text):
    """Extract ended sessions from session-log.md as ordered chapters, each with
    the session-end timestamp used to bucket beats/plates into the right chapter."""
    sessions = []
    # Each ended block: "### Session Ended: <ts>\n<summary>\n\n**Session:** N ..."
    heads = list(re.finditer(r"^### Session Ended:\s*(.*)$", log_text, flags=re.MULTILINE))
    for i, h in enumerate(heads):
        start = h.end()
        end = heads[i + 1].start() if i + 1 < len(heads) else len(log_text)
        b = log_text[start:end]
        # summary = text up to the first **Field:** line
        m = re.search(r"\*\*Session:\*\*", b)
        summary = (b[: m.start()] if m else b).strip()
        # strip a trailing horizontal rule / stray markers
        summary = re.sub(r"\n-{3,}\s*$", "", summary).strip()
        sessions.append({"num": _field(b, "Session"),
                         "location": _field(b, "Location"),
                         "cliffhanger": _field(b, "Cliffhanger"),
                         "summary": summary,
                         "end_dt": _parse_ts(h.group(1))})
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
                               "chronicler": d.get("chronicler", "").strip(),
                               "_dt": _parse_ts(d.get("ts"))})
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
    beats = load_beats(campaign_dir)

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

    # --- Chapters: recorded narration prose, plates interleaved where made ---
    #
    # A chapter is a session. Beats and plates are bucketed into the session
    # whose end-timestamp first follows them; anything after the last saved
    # session falls into a trailing "current" chapter so a mid-campaign
    # chronicle still captures unsaved play. Within a chapter, beats and plates
    # are merged by timestamp, so an image lands right where it was generated.
    # When a session has no recorded beats (played before this feature, or
    # recording was off), the chapter falls back to its end-of-session summary.

    def _bucket(dt):
        """Index of the session this timestamp belongs to (len(sessions) = the
        trailing current chapter). Undated items — and anything after the last
        DATED session-end — sort to the trailing chapter. Sessions whose own
        end-timestamp didn't parse are skipped here (they can't bound by time),
        so one unparseable end-stamp can't vacuum every later beat into it."""
        if dt is None:
            return len(sessions)
        for i, s in enumerate(sessions):
            end = s.get("end_dt")
            if end is not None and dt <= end:
                return i
        return len(sessions)

    n_chapters = len(sessions) + (1 if any(_bucket(b.get("_dt")) == len(sessions)
                                           for b in beats) else 0)

    def _sort_key(item):
        # keep original order for undated items via a stable secondary key
        dt = item[0]
        return (0, dt) if dt is not None else (1, 0)

    # Track placed plates GLOBALLY so each plate appears exactly once across the
    # whole chronicle — even if a beat's explicitly-attached plate is bucketed
    # (by timestamp) into a different chapter than the beat that named it.
    placed = set()

    def _emit_chapter(idx, title_loc, summary, cliffhanger):
        head = f"Chapter {idx + 1}"
        if title_loc:
            head += f" — {title_loc}"
        a(f"# {head}\n")
        ch_beats = [b for b in beats if _bucket(b.get("_dt")) == idx]
        ch_plates = [p for p in plates if _bucket(p.get("_dt")) == idx]
        if ch_beats:
            # merge beats + plates on one timeline
            timeline = [(b.get("_dt"), "beat", b) for b in ch_beats] \
                + [(p.get("_dt"), "plate", p) for p in ch_plates]
            timeline.sort(key=_sort_key)
            for dt, kind, obj in timeline:
                if kind == "beat":
                    prose = _clean_prose(obj.get("text", ""))
                    if prose:
                        a(prose + "\n")
                    # a beat may name the plate(s) it made — place them right here,
                    # resolving against ALL plates so an attached plate lands at
                    # its beat even if its own timestamp bucketed it elsewhere.
                    for fn in obj.get("images", []):
                        pl = next((p for p in plates if p["file"] == fn), None)
                        if pl and pl["file"] not in placed:
                            cap = pl["title"] or "A plate from the chronicle"
                            a(f"\n![{esc(cap)}](images/{pl['file']})\n")
                            placed.add(pl["file"])
                else:
                    if obj["file"] in placed:
                        continue
                    cap = obj["title"] or "A plate from the chronicle"
                    a(f"\n![{esc(cap)}](images/{obj['file']})\n")
                    placed.add(obj["file"])
            if cliffhanger:
                a(f"\n*{esc(cliffhanger)}*\n")
        else:
            # no recorded prose for this chapter — fall back to the summary
            if summary:
                a(esc(summary) + "\n")
            if cliffhanger:
                a(f"\n*{esc(cliffhanger)}*\n")
            for pl in ch_plates:
                if pl["file"] in placed:
                    continue
                cap = pl["title"] or "A plate from the chronicle"
                a(f"\n![{esc(cap)}](images/{pl['file']})\n")
                placed.add(pl["file"])
        a("\n---\n")

    if sessions or beats:
        for i, s in enumerate(sessions):
            _emit_chapter(i, s["location"], s["summary"], s["cliffhanger"])
        # trailing chapter for beats after the last saved session (current play)
        if n_chapters > len(sessions):
            trailing = [b for b in beats if _bucket(b.get("_dt")) == len(sessions)]
            loc = (trailing[-1].get("location") if trailing else "") \
                or char.get("current_location") or ""
            _emit_chapter(len(sessions), loc, "", "")
    else:
        # No played sessions and nothing recorded — still produce a "world" ebook.
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
            "epub": epub_name, "sessions": len(sessions), "plates": len(plates),
            "beats": len(beats)}


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
