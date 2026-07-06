"""image_gen.py — GM scene illustration (OpenAI gpt-image-2 OR Google Gemini).

The GM calls this at high-impact beats (new location, boss reveal, big loot) to
show the player a real image. The image is saved into the active campaign's
``images/`` folder and the path is handed back so the caller can show the player
a clickable link. Every generation is logged with an estimated cost so spend is
auditable.

Two providers are supported and chosen automatically:
  * gemini — Google's ``gemini-2.5-flash-image`` (Nano Banana). FREE on the
    Gemini API free tier. Used when GEMINI_API_KEY (or GOOGLE_API_KEY) is set.
  * openai — ``gpt-image-2``. Used when only OPENAI_API_KEY is set.
Set GM_IMAGE_PROVIDER=gemini|openai to force one when both keys are present
(default preference: gemini, since the free tier costs nothing).

Display path: we DON'T try to render pixels in the terminal. We save a PNG and
return its path; the VS Code terminal linkifies the path so the player clicks to
open it.

No third-party SDK — each request is a single JSON POST, done with stdlib urllib
so the project gains no new dependency.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import base64
import urllib.error
import urllib.request
from pathlib import Path

from campaign_manager import CampaignManager
import visual_appearance as va_mod


def resolve_campaign_dir(world_state_dir: str = "world-state"):
    """Return the active campaign dir as a Path, or None if none is active."""
    return CampaignManager(world_state_dir).get_active_campaign_dir()


def appearance_line(name: str, campaign_dir=None) -> str:
    """Return the 'character bible' line for a character by name.

    Looks up the active PC (character.json) first, then NPCs (npcs.json), and
    renders the canonical visual_appearance block as one prompt-ready line.
    Returns "" if the name is unknown or has no appearance authored yet.
    """
    campaign_dir = campaign_dir or resolve_campaign_dir()
    if campaign_dir is None or not name:
        return ""
    campaign_dir = Path(campaign_dir)

    # PC first.
    char_path = campaign_dir / "character.json"
    if char_path.exists():
        try:
            char = json.loads(char_path.read_text(encoding="utf-8"))
            if str(char.get("name", "")).strip().lower() == name.strip().lower():
                return va_mod.format_line(char.get("name", name),
                                          char.get("visual_appearance"))
        except (OSError, ValueError):
            pass

    # Then NPCs (case-insensitive key match).
    npcs_path = campaign_dir / "npcs.json"
    if npcs_path.exists():
        try:
            npcs = json.loads(npcs_path.read_text(encoding="utf-8"))
            if isinstance(npcs.get("npcs"), dict):
                npcs = npcs["npcs"]
            for key, data in npcs.items():
                if key.strip().lower() == name.strip().lower() and isinstance(data, dict):
                    return va_mod.format_line(key, data.get("visual_appearance"))
        except (OSError, ValueError):
            pass

    return ""


CHRONICLER_FILE = "chronicler.json"


def _chronicler_path(campaign_dir) -> Path:
    return Path(campaign_dir) / CHRONICLER_FILE


def load_chronicler(campaign_dir=None):
    """Return this campaign's chronicler dict {name, style, persona}, or None."""
    campaign_dir = campaign_dir or resolve_campaign_dir()
    if campaign_dir is None:
        return None
    p = _chronicler_path(campaign_dir)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def save_chronicler(*, name=None, style=None, persona=None, campaign_dir=None) -> dict:
    """Merge-update the campaign's chronicler. Only provided fields change."""
    campaign_dir = campaign_dir or resolve_campaign_dir()
    if campaign_dir is None:
        raise ImageGenError("No active campaign. Run /new-game or /import first.")
    data = load_chronicler(campaign_dir) or {}
    if name is not None:
        data["name"] = name
    if style is not None:
        data["style"] = style
    if persona is not None:
        data["persona"] = persona
    _chronicler_path(campaign_dir).write_text(
        json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return data


API_URL = "https://api.openai.com/v1/images/generations"
DEFAULT_MODEL = os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-2")
DEFAULT_QUALITY = os.environ.get("OPENAI_IMAGE_QUALITY", "medium")
DEFAULT_SIZE = os.environ.get("OPENAI_IMAGE_SIZE", "1536x1024")  # cinematic landscape
REQUEST_TIMEOUT = 180  # gpt-image-2 can take up to ~2 min on complex prompts

# --- Gemini (Google Generative Language API) -------------------------------
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
GEMINI_MODEL = os.environ.get("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
# Free tier costs nothing; log 0 by default. Override if you move to paid
# (gemini-2.5-flash-image is ~$0.039/image on the paid tier).
GEMINI_COST = float(os.environ.get("GEMINI_IMAGE_COST_USD", "0") or 0)


def active_provider() -> str:
    """Which image backend to use: 'gemini', 'openai', or '' if none configured.

    GM_IMAGE_PROVIDER forces a choice; otherwise we prefer Gemini (free tier)
    when its key is present, then fall back to OpenAI.
    """
    forced = os.environ.get("GM_IMAGE_PROVIDER", "").strip().lower()
    if forced in ("gemini", "openai"):
        return forced
    if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
        return "gemini"
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    return ""


# Published gpt-image-2 per-image USD pricing (docs). Used only to LOG estimated
# spend — not billed here. Unknown size/quality combos report None (logged as ?).
_COST = {
    "low":    {"1024x1024": 0.006, "1536x1024": 0.005, "1024x1536": 0.005},
    "medium": {"1024x1024": 0.053, "1536x1024": 0.041, "1024x1536": 0.041},
    "high":   {"1024x1024": 0.211, "1536x1024": 0.165, "1024x1536": 0.165},
}


def estimate_cost(quality: str, size: str):
    """Return the published per-image USD cost, or None if not in the table."""
    return _COST.get(quality, {}).get(size)


# Map our pixel sizes to the aspect ratios Gemini's imageConfig accepts.
_GEMINI_ASPECT = {
    "1536x1024": "3:2",   # cinematic landscape (our default)
    "1024x1536": "2:3",   # portrait
    "1024x1024": "1:1",   # square
}


def _size_to_aspect(size: str) -> str:
    return _GEMINI_ASPECT.get(size, "16:9")


SLUG_MAX = 32  # keep filenames (and the file:// link) short enough not to line-wrap


def _slug(title: str) -> str:
    """A filesystem-safe, short slug from a scene title.

    Capped at SLUG_MAX chars, trimmed on a word boundary so names never cut
    mid-word (e.g. '...reads-the-dead-i'). Long titles keep their leading words.
    """
    s = re.sub(r"[^a-z0-9]+", "-", (title or "scene").lower()).strip("-")
    if len(s) > SLUG_MAX:
        s = s[:SLUG_MAX].rsplit("-", 1)[0]  # drop the partial trailing word
    return s.strip("-") or "scene"


def _next_path(images_dir: Path, title: str, ext: str = ".png") -> Path:
    """Sequenced filename: NNNN-slug<ext>, continuing the highest existing index.

    Indexing counts every NNNN-*.* image (png, jpg, …) so generated and imported
    pictures share one monotonic sequence.
    """
    images_dir.mkdir(parents=True, exist_ok=True)
    highest = 0
    for p in images_dir.glob("[0-9][0-9][0-9][0-9]-*.*"):
        try:
            highest = max(highest, int(p.name[:4]))
        except ValueError:
            continue
    return images_dir / f"{highest + 1:04d}-{_slug(title)}{ext}"


def _detect_image_ext(data: bytes) -> str:
    """Return the file extension for known image bytes, or '' if unrecognized."""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if data[:3] == b"\xff\xd8\xff":
        return ".jpg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    if data[:4] == b"GIF8":
        return ".gif"
    return ""


# Short, shallow symlink dir so the clickable file:// link never line-wraps.
# The deep campaign path (~110 chars) wraps in the terminal and the wrap kills
# the click target; a symlink at /tmp/gm-img/<tag>-NNNN.png resolves to the real
# PNG when clicked while staying ~30 chars on one line.
SHORTLINK_DIR = Path("/tmp/gm-img")


def _short_link(out_path: Path, campaign_dir: str) -> Path | None:
    """Create a short symlink to ``out_path`` and return it (None on failure).

    Name: <campaign-initials>-<NNNN>.png — the descriptive slug stays in the real
    filename for browsing; the symlink is purely the clickable handle.
    """
    try:
        tag = "".join(w[:1] for w in Path(campaign_dir).name.split("-"))[:6] or "gm"
        seq = out_path.name[:4]
        SHORTLINK_DIR.mkdir(parents=True, exist_ok=True)
        link = SHORTLINK_DIR / f"{tag}-{seq}.png"
        if link.is_symlink() or link.exists():
            link.unlink()
        link.symlink_to(out_path.resolve())
        return link
    except OSError:
        return None  # fall back to the absolute path


def _log_generation(images_dir: Path, record: dict) -> None:
    """Append one JSON line to the per-campaign generation/spend log."""
    try:
        with (images_dir / "_gen-log.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except OSError:
        pass  # logging must never break a successful generation


class ImageGenError(Exception):
    """Raised for user-correctable failures (missing key, moderation, bad request)."""


class ProviderUnavailable(ImageGenError):
    """Provider failed transiently (429 quota/rate limit, 5xx, network).

    These are the cases another provider might succeed at, so generate_image
    catches this to fall back (e.g. Gemini free tier → OpenAI). Subclasses
    ImageGenError so callers that don't fall back still report it cleanly.
    """


def _generate_openai_bytes(final_prompt: str, *, quality: str, size: str,
                           model: str, api_key: str) -> bytes:
    """POST to OpenAI's image API and return the decoded PNG bytes."""
    payload = json.dumps({
        "model": model,
        "prompt": final_prompt,
        "size": size,
        "quality": quality,
        "n": 1,
    }).encode("utf-8")

    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise ImageGenError(_format_http_error(e)) from e
    except urllib.error.URLError as e:
        raise ImageGenError(f"Network error reaching OpenAI: {e.reason}") from e

    try:
        return base64.b64decode(body["data"][0]["b64_json"])
    except (KeyError, IndexError, ValueError) as e:
        raise ImageGenError("Unexpected response from image API (no image data).") from e


def _generate_gemini_bytes(final_prompt: str, *, size: str, model: str,
                           api_key: str) -> bytes:
    """POST to the Gemini image model and return the decoded PNG bytes."""
    payload = json.dumps({
        "contents": [{"parts": [{"text": final_prompt}]}],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            "imageConfig": {"aspectRatio": _size_to_aspect(size)},
        },
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{GEMINI_API_BASE}/models/{model}:generateContent",
        data=payload,
        headers={
            "x-goog-api-key": api_key,
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        code = e.code
        msg = _format_gemini_error(e)  # consumes the body
        # 429 (quota/rate limit) and 5xx are worth a fallback to another provider.
        if code == 429 or 500 <= code < 600:
            raise ProviderUnavailable(msg) from e
        raise ImageGenError(msg) from e
    except urllib.error.URLError as e:
        raise ProviderUnavailable(f"Network error reaching Gemini: {e.reason}") from e

    # A blocked prompt comes back with no usable candidate — surface why.
    candidates = body.get("candidates") or []
    if not candidates:
        block = (body.get("promptFeedback") or {}).get("blockReason")
        if block:
            raise ImageGenError(
                f"Gemini blocked the prompt ({block}). Revise the prompt and retry.")
        raise ImageGenError("Gemini returned no image (empty response).")

    parts = (candidates[0].get("content") or {}).get("parts") or []
    for part in parts:
        inline = part.get("inlineData") or part.get("inline_data")
        if inline and inline.get("data"):
            try:
                return base64.b64decode(inline["data"])
            except ValueError as e:
                raise ImageGenError("Gemini returned malformed image data.") from e

    finish = candidates[0].get("finishReason")
    if finish and finish != "STOP":
        raise ImageGenError(f"Gemini produced no image (finishReason={finish}).")
    raise ImageGenError("Gemini response contained no image data.")


def generate_image(prompt: str, *, title: str = "", quality: str = DEFAULT_QUALITY,
                   size: str = DEFAULT_SIZE, model: str | None = None,
                   characters=None) -> dict:
    """Generate one image and save it under the active campaign's images/ dir.

    The provider (Gemini or OpenAI) is chosen by ``active_provider()``. ``model``
    defaults to that provider's image model when left as None.

    ``characters`` is an optional list of character names in frame; each one's
    canonical visual_appearance block is auto-injected into the prompt so the PC
    and NPCs render CONSISTENTLY image-to-image, even on direct/fallback calls.

    Returns {path, rel_path, cost, model, provider, quality, size, title}. Raises
    ImageGenError for actionable problems (no campaign, no key, moderation).
    """
    provider = active_provider()
    if not provider:
        raise ImageGenError(
            "No image API key set. Add GEMINI_API_KEY (free tier — "
            "aistudio.google.com/apikey) or OPENAI_API_KEY to .env to enable images.")

    if provider == "gemini":
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        model = model or GEMINI_MODEL
    else:
        api_key = os.environ.get("OPENAI_API_KEY")
        model = model or DEFAULT_MODEL

    campaign_dir = resolve_campaign_dir()
    if campaign_dir is None:
        raise ImageGenError("No active campaign. Run /new-game or /import first.")

    if not prompt or not prompt.strip():
        raise ImageGenError("Empty prompt — describe the scene to illustrate.")

    final_prompt = prompt

    # Auto-inject each named character's canonical look so the PC/NPCs render
    # consistently every time. Skipped if the caller already spelled it out.
    for cname in (characters or []):
        line = appearance_line(cname, campaign_dir)
        if line and cname.strip().lower() not in prompt.lower():
            final_prompt = f"{final_prompt.rstrip()}\n\nCharacter (render exactly): {line}"

    # Lock the campaign's art-style signature into every prompt so the gallery
    # reads like one artbook even if the caller forgets to restate the style.
    chronicler = load_chronicler(campaign_dir)
    style = (chronicler or {}).get("style", "").strip()
    if style and style.lower() not in final_prompt.lower():
        final_prompt = f"{final_prompt.rstrip()}\n\nConsistent art style (campaign signature): {style}."

    if provider == "gemini":
        try:
            image_bytes = _generate_gemini_bytes(final_prompt, size=size, model=model,
                                                 api_key=api_key)
            cost = GEMINI_COST
        except ProviderUnavailable as e:
            # Gemini hit its limit (free tier = 0 image quota, or a real rate
            # limit). Fall back to OpenAI if a key is available so images still
            # render; otherwise surface the original error.
            oa_key = os.environ.get("OPENAI_API_KEY")
            if not oa_key:
                raise
            sys.stderr.write(f"[INFO] Gemini unavailable ({e}). Falling back to OpenAI.\n")
            provider = "openai"
            model = DEFAULT_MODEL
            image_bytes = _generate_openai_bytes(final_prompt, quality=quality, size=size,
                                                 model=model, api_key=oa_key)
            cost = estimate_cost(quality, size)
    else:
        image_bytes = _generate_openai_bytes(final_prompt, quality=quality, size=size,
                                             model=model, api_key=api_key)
        cost = estimate_cost(quality, size)

    images_dir = Path(campaign_dir) / "images"
    out_path = _next_path(images_dir, title)
    out_path.write_bytes(image_bytes)

    record = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "file": out_path.name,
        "title": title,
        "provider": provider,
        "model": model,
        "quality": quality,
        "size": size,
        "est_cost_usd": cost,
        "chronicler": (chronicler or {}).get("name"),
        "prompt": final_prompt[:500],
    }
    _log_generation(images_dir, record)

    short = _short_link(out_path, campaign_dir)
    return {
        "path": str(out_path),
        "rel_path": os.path.relpath(out_path, Path.cwd()),
        "short_path": str(short) if short else str(out_path),
        "cost": cost,
        "model": model,
        "provider": provider,
        "quality": quality,
        "size": size,
        "title": title,
    }


def import_image(src_path: str, *, title: str = "", campaign_dir=None) -> dict:
    """Copy an externally-made image into the campaign gallery (cost $0).

    For pictures generated by hand elsewhere — e.g. Nano Banana in the Gemini
    app via a Pro subscription — so they slot into the same sequenced gallery,
    shortlink, and spend log as generated ones. Returns the same dict shape as
    generate_image (provider='import', cost 0).
    """
    campaign_dir = campaign_dir or resolve_campaign_dir()
    if campaign_dir is None:
        raise ImageGenError("No active campaign. Run /new-game or /import first.")

    src = Path(src_path).expanduser()
    if not src.exists() or not src.is_file():
        raise ImageGenError(f"File not found: {src_path}")

    data = src.read_bytes()
    ext = _detect_image_ext(data)
    if not ext:
        raise ImageGenError(
            f"'{src.name}' is not a recognized image (expected PNG, JPG, WEBP, or GIF).")

    images_dir = Path(campaign_dir) / "images"
    out_path = _next_path(images_dir, title or src.stem, ext=ext)
    out_path.write_bytes(data)

    chronicler = load_chronicler(campaign_dir)
    record = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "file": out_path.name,
        "title": title,
        "provider": "import",
        "model": "imported",
        "quality": "-",
        "size": "-",
        "est_cost_usd": 0.0,
        "chronicler": (chronicler or {}).get("name"),
        "source": str(src),
    }
    _log_generation(images_dir, record)

    short = _short_link(out_path, campaign_dir)
    return {
        "path": str(out_path),
        "rel_path": os.path.relpath(out_path, Path.cwd()),
        "short_path": str(short) if short else str(out_path),
        "cost": 0.0,
        "model": "imported",
        "provider": "import",
        "quality": "-",
        "size": "-",
        "title": title,
    }


def _format_http_error(e: "urllib.error.HTTPError") -> str:
    """Turn an OpenAI HTTP error into an actionable one-line message."""
    try:
        err = json.loads(e.read().decode("utf-8")).get("error", {})
    except Exception:
        err = {}
    code = err.get("code")
    msg = err.get("message", "")
    if code == "moderation_blocked":
        stage = (err.get("moderation_details") or {}).get("moderation_stage", "input")
        return f"Image blocked by content moderation ({stage}). Revise the prompt and retry."
    if e.code == 401:
        return "OpenAI rejected the API key (401). Check OPENAI_API_KEY in .env."
    if e.code == 429:
        return "OpenAI rate limit / quota hit (429). Wait and retry, or check billing."
    return f"OpenAI error {e.code}: {msg or 'request failed'}"


def _format_gemini_error(e: "urllib.error.HTTPError") -> str:
    """Turn a Gemini HTTP error into an actionable one-line message."""
    try:
        err = json.loads(e.read().decode("utf-8")).get("error", {})
    except Exception:
        err = {}
    msg = err.get("message", "")
    if e.code == 400 and ("API key not valid" in msg or "API_KEY_INVALID" in str(err)):
        return "Gemini rejected the API key (400). Check GEMINI_API_KEY in .env."
    if e.code in (401, 403):
        return ("Gemini denied access (%d). Check GEMINI_API_KEY and that the "
                "Generative Language API is enabled for it." % e.code)
    if e.code == 429:
        return ("Gemini rate limit / free-tier quota hit (429). Wait and retry "
                "(free tier is rate-limited per minute/day).")
    if e.code == 404:
        return (f"Gemini model not found (404): {GEMINI_MODEL}. Set GEMINI_IMAGE_MODEL "
                "to an available image model.")
    return f"Gemini error {e.code}: {msg or 'request failed'}"


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate a scene image (Gemini gemini-2.5-flash-image or OpenAI gpt-image-2)")
    parser.add_argument("--prompt", help="Scene description (or read from stdin if omitted)")
    parser.add_argument("--title", default="", help="Scene title (used in filename + canvas)")
    parser.add_argument("--character", action="append", default=[], metavar="NAME",
                        help="Character in frame; auto-injects their visual_appearance. Repeatable.")
    parser.add_argument("--import-file", metavar="PATH",
                        help="Copy an existing image file into the campaign gallery (cost $0) and exit")
    parser.add_argument("--appearance", metavar="NAME",
                        help="Print one character's visual_appearance bible line and exit")
    parser.add_argument("--quality", default=DEFAULT_QUALITY, choices=["low", "medium", "high", "auto"])
    parser.add_argument("--size", default=DEFAULT_SIZE, help="e.g. 1536x1024, 1024x1024, auto")
    parser.add_argument("--json", action="store_true", help="Emit the result as JSON")
    parser.add_argument("--show-chronicler", action="store_true",
                        help="Print the campaign's chronicler (name/style/persona) and exit")
    parser.add_argument("--set-chronicler", action="store_true",
                        help="Save/merge the campaign's chronicler from the fields below, then exit")
    parser.add_argument("--name", help="Chronicler name (with --set-chronicler)")
    parser.add_argument("--style", help="Locked art-style signature (with --set-chronicler)")
    parser.add_argument("--persona", help="Chronicler persona/voice (with --set-chronicler)")
    args = parser.parse_args()

    if args.import_file is not None:
        try:
            result = import_image(args.import_file, title=args.title)
        except ImageGenError as e:
            print(f"[ERROR] {e}", file=sys.stderr)
            sys.exit(1)
        print(json.dumps(result) if args.json else result["path"])
        return

    if args.appearance is not None:
        line = appearance_line(args.appearance)
        if args.json:
            print(json.dumps({"name": args.appearance, "appearance": line}))
        elif line:
            print(line)
        else:
            print(f"No visual_appearance set for '{args.appearance}' "
                  "(set it via gm-npc.sh set-appearance / gm-player.sh set-appearance).")
        return

    if args.show_chronicler:
        chronicler = load_chronicler()
        if args.json:
            print(json.dumps(chronicler or {}))
        elif not chronicler:
            print("No chronicler set for this campaign yet.")
        else:
            print(f"Chronicler: {chronicler.get('name', '(unnamed)')}")
            if chronicler.get("persona"):
                print(f"  persona: {chronicler['persona']}")
            if chronicler.get("style"):
                print(f"  style:   {chronicler['style']}")
        return

    if args.set_chronicler:
        if args.name is None and args.style is None and args.persona is None:
            print("[ERROR] --set-chronicler needs at least one of --name/--style/--persona",
                  file=sys.stderr)
            sys.exit(1)
        try:
            data = save_chronicler(name=args.name, style=args.style, persona=args.persona)
        except ImageGenError as e:
            print(f"[ERROR] {e}", file=sys.stderr)
            sys.exit(1)
        print(json.dumps(data) if args.json else f"Chronicler saved: {data.get('name', '(unnamed)')}")
        return

    prompt = args.prompt if args.prompt is not None else sys.stdin.read()

    try:
        result = generate_image(prompt, title=args.title, quality=args.quality,
                                size=args.size, characters=args.character)
    except ImageGenError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(result))
    else:
        print(result["path"])


if __name__ == "__main__":
    main()
