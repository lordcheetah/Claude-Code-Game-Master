#!/usr/bin/env python3
"""GM adapter for the vendored `conlang` engine (lib/conlang/).

Turns the deterministic language generator into a Game-Master tool: a culture's
whole tongue is minted from a *seed derived from its name*, so "Deep Ones" always
yields the same phonology, words, names, and script — the persistence story is a
single integer. Use it to name NPCs and places, drop a phrase of an alien language
into a scene, or design a faction's writing system, all consistent session to session.

Commands (via tools/gm-conlang.sh):
    generate "<culture>"   [--seed N] [--words N] [--names N] [--no-save]
    name     "<culture>"   [--count N] [--kind person|place]
    word     "<culture>" "<english-gloss>"
    phrase   "<culture>"   (a few showcase sentences)
    list

A per-campaign profile is saved to world-state/campaigns/<active>/languages/<slug>.json
(seed + cached samples) so the language is browseable and reproducible.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

# The vendored engine sits in lib/conlang/ — this script lives in lib/, so it is importable.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from conlang import Language  # noqa: E402

# IPA output contains combining marks Windows' cp1252 console cannot encode.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

BASE = Path(__file__).resolve().parent.parent          # repo root
WORLD = BASE / "world-state"

# Thematic glosses worth surfacing in a GM sketch (intersected with what the language has).
_CORE_GLOSSES = [
    "I", "you", "we", "water", "fire", "sun", "moon", "star", "sea", "sky",
    "earth", "stone", "blood", "bone", "die", "spirit", "god", "dream", "night",
    "day", "man", "woman", "child", "hunt", "kill", "war", "snake", "fish",
    "name", "word", "language", "come", "go", "see", "speak", "know", "eat",
]

# Showcase sentences — glosses chosen to exist in every generated lexicon.
_PHRASES = [
    ("the hunter kills the snake",
     dict(subject="hunter", verb="kill", obj="snake",
          subject_definiteness="def", object_definiteness="def")),
    ("the woman sees the sea",
     dict(subject="woman", verb="see", obj="sea",
          subject_definiteness="def", object_definiteness="def")),
    ("we speak the language",
     dict(subject="we", verb="speak", obj="language", object_definiteness="def")),
    ("the god of fire and blood",
     None),  # rendered as a noun phrase / compound below, not a clause
]


# --------------------------------------------------------------------------- helpers
def _indent(block: str, pad: str) -> str:
    return "\n".join(pad + line for line in block.rstrip("\n").splitlines())


def slugify(name: str) -> str:
    keep = "".join(c if c.isalnum() or c in " -_" else "" for c in name.lower())
    return "-".join(keep.split()) or "language"


def seed_from_name(name: str) -> int:
    """Stable across runs/machines (Python's hash() is salted, so don't use it)."""
    return int(hashlib.sha256(name.strip().lower().encode("utf-8")).hexdigest()[:8], 16)


def active_campaign_dir() -> Path | None:
    ac = WORLD / "active-campaign.txt"
    if ac.exists():
        slug = ac.read_text(encoding="utf-8").strip()
        if slug:
            d = WORLD / "campaigns" / slug
            if d.exists():
                return d
    return None


def languages_dir(campaign: str | None) -> Path:
    if campaign:
        base = WORLD / "campaigns" / campaign
    else:
        base = active_campaign_dir() or WORLD
    d = base / "languages"
    d.mkdir(parents=True, exist_ok=True)
    return d


def mint_names(lang: Language, n: int, rng: random.Random) -> list[dict]:
    words = lang.word_generator.lexicon(n, rng)
    out = []
    for w in words:
        roman = w.roman[:1].upper() + w.roman[1:] if w.roman else w.roman
        out.append({"roman": roman, "ipa": w.ipa})
    return out


def render_phrases(lang: Language) -> list[dict]:
    out = []
    for gloss_en, kwargs in _PHRASES:
        if kwargs is None:
            continue
        try:
            s = lang.make_sentence(**kwargs)
            # .text/.ipa are attributes; .interlinear is a method → call it.
            out.append({"english": gloss_en, "text": s.text,
                        "ipa": s.ipa, "interlinear": s.interlinear()})
        except Exception:
            continue
    return out


def build_profile(name: str, seed: int, n_words: int, n_names: int) -> dict:
    lang = Language.generate(seed=seed)
    d = lang.to_dict()
    lex = d.get("lexicon", {})

    core = {}
    for g in _CORE_GLOSSES:
        e = lex.get(g)
        if e:
            core[g] = {"roman": e["roman"], "ipa": e["ipa"]}

    # a broader word list for the sketch (first n_words glosses, alphabetical for stability)
    extra = {}
    for g in sorted(lex.keys()):
        if g in core or g.isupper():        # skip AUX/Q/REL grammatical placeholders
            continue
        e = lex[g]
        extra[g] = {"roman": e["roman"], "ipa": e["ipa"]}
        if len(extra) >= n_words:
            break

    names_rng = random.Random(seed ^ 0x5EED)   # fixed offset → reproducible name batch
    return {
        "name": name,
        "slug": slugify(name),
        "seed": seed,
        "generator_version": d.get("generator_version"),
        "phonology": d.get("phonology", {}),
        "writing": d.get("writing", {}),
        "numerals": d.get("numerals", {}),
        "summary": lang.summary(),
        "core_vocab": core,
        "vocab": extra,
        "names": mint_names(lang, n_names, names_rng),
        "phrases": render_phrases(lang),
    }


# --------------------------------------------------------------------------- printing
def _print_profile(p: dict, saved_path: Path | None):
    phon = p["phonology"]
    w = p["writing"]
    print(f"═══ LANGUAGE OF: {p['name']}  (seed {p['seed']}) ═══\n")
    print(p["summary"])
    print()
    print(f"Writing: {w.get('type','?')}, {w.get('direction','?')}"
          + (", cursive" if w.get("cursive") else "")
          + (", stacked clusters" if w.get("stack_clusters") else ""))
    nums = p.get("numerals", {})
    if nums.get("samples"):
        s = nums["samples"]
        print(f"Numbers (base {nums.get('base','?')}): "
              + ", ".join(f"{k}={v}" for k, v in list(s.items())[:6]))
    print()

    if p["core_vocab"]:
        print("Core words:")
        wdt = max(len(g) for g in p["core_vocab"])
        for g, e in p["core_vocab"].items():
            print(f"  {g:<{wdt}}  {e['roman']:<12} /{e['ipa']}/")
        print()

    if p["names"]:
        print("Names (people & places):")
        romans = [n["roman"] for n in p["names"]]
        for i in range(0, len(romans), 5):
            print("  " + "   ".join(romans[i:i + 5]))
        print()

    if p["phrases"]:
        print("Phrases:")
        for ph in p["phrases"]:
            print(f"  “{ph['english']}”")
            print(f"     {ph['text']}   /{ph['ipa']}/")
            print(_indent(ph["interlinear"], "     "))
        print()

    if saved_path:
        print(f"[saved] {saved_path}  — reproducible from seed {p['seed']}; "
              f"{len(p['vocab']) + len(p['core_vocab'])} words cached")


# --------------------------------------------------------------------------- commands
def cmd_generate(args) -> int:
    seed = args.seed if args.seed is not None else seed_from_name(args.culture)
    p = build_profile(args.culture, seed, args.words, args.names)
    saved = None
    if not args.no_save:
        saved = languages_dir(args.campaign) / f"{p['slug']}.json"
        saved.write_text(json.dumps(p, ensure_ascii=False, indent=2), encoding="utf-8")
    _print_profile(p, saved)
    return 0


def _load_or_seed(culture: str, campaign: str | None):
    """Return (seed, Language). Prefer a saved profile's seed; else derive from name."""
    path = languages_dir(campaign) / f"{slugify(culture)}.json"
    if path.exists():
        seed = json.loads(path.read_text(encoding="utf-8")).get("seed")
    else:
        seed = seed_from_name(culture)
    return seed, Language.generate(seed=seed)


def cmd_name(args) -> int:
    seed, lang = _load_or_seed(args.culture, args.campaign)
    # fresh names each call (for on-the-fly NPCs) unless --reproducible
    rng = random.Random(seed ^ 0x5EED) if args.reproducible else random.Random()
    names = mint_names(lang, args.count, rng)
    label = "place" if args.kind == "place" else "person"
    print(f"{args.culture} — {label} names:")
    for n in names:
        print(f"  {n['roman']:<14} /{n['ipa']}/")
    return 0


def cmd_word(args) -> int:
    seed, lang = _load_or_seed(args.culture, args.campaign)
    gloss = args.gloss.strip().lower()
    lex = lang.to_dict().get("lexicon", {})
    entry = lex.get(gloss) or lex.get(args.gloss.strip())
    if entry:
        print(f'{args.culture}: "{args.gloss}" = {entry["roman"]}  /{entry["ipa"]}/'
              f'  ({entry.get("pos","?")})')
    else:
        # not in the core lexicon — coin a plausible new word in this language
        w = lang.word_generator.lexicon(1, random.Random(seed_from_name(gloss) ^ seed))[0]
        print(f'{args.culture}: "{args.gloss}" (coined) = {w.roman}  /{w.ipa}/')
    return 0


def cmd_phrase(args) -> int:
    _seed, lang = _load_or_seed(args.culture, args.campaign)
    phrases = render_phrases(lang)
    if not phrases:
        print("(no showcase phrases could be built for this language)")
        return 0
    print(f"{args.culture} — phrases:")
    for ph in phrases:
        print(f"  “{ph['english']}”")
        print(f"     {ph['text']}   /{ph['ipa']}/")
        print(_indent(ph["interlinear"], "     "))
    return 0


def cmd_list(args) -> int:
    d = languages_dir(args.campaign)
    files = sorted(d.glob("*.json"))
    if not files:
        print(f"(no saved languages in {d})")
        return 0
    print(f"Saved languages in {d}:")
    for f in files:
        try:
            p = json.loads(f.read_text(encoding="utf-8"))
            print(f"  {p.get('name', f.stem):<24} seed {p.get('seed','?')}  "
                  f"({p.get('phonology',{}).get('syllables',['?'])})")
        except Exception:
            print(f"  {f.stem}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="gm-conlang",
                                 description="Deterministic conlang generation for the GM.")
    ap.add_argument("--campaign", help="campaign slug (default: active campaign)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("generate", help="mint a culture's whole language from its name")
    g.add_argument("culture")
    g.add_argument("--seed", type=int, default=None, help="override the name-derived seed")
    g.add_argument("--words", type=int, default=24, help="extra vocab words to cache")
    g.add_argument("--names", type=int, default=15, help="names to mint")
    g.add_argument("--no-save", action="store_true", help="print only, don't save a profile")
    g.set_defaults(func=cmd_generate)

    n = sub.add_parser("name", help="mint names in a culture's language")
    n.add_argument("culture")
    n.add_argument("--count", type=int, default=8)
    n.add_argument("--kind", choices=["person", "place"], default="person")
    n.add_argument("--reproducible", action="store_true",
                   help="same batch every call (default: fresh names)")
    n.set_defaults(func=cmd_name)

    w = sub.add_parser("word", help="translate one English gloss into the language")
    w.add_argument("culture")
    w.add_argument("gloss")
    w.set_defaults(func=cmd_word)

    ph = sub.add_parser("phrase", help="show a few sentences in the language")
    ph.add_argument("culture")
    ph.set_defaults(func=cmd_phrase)

    ls = sub.add_parser("list", help="list saved languages for the campaign")
    ls.set_defaults(func=cmd_list)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
