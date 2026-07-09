"""web_research.py — web search/research via Tavily (for the GM toolchain).

Used when creating a world from a KNOWN IP that has no source document (e.g.
adapting a video-game series): the lore-researcher gathers canon from the web,
then that text is fed through the normal import/RAG pipeline as source material.

Modeled on image_gen.py: a single JSON POST done with stdlib urllib, so the
project gains no new dependency. The API key is read from TAVILY_API_KEY in the
environment (tools/common.sh auto-sources .env for every gm-*.sh tool, so the key
reaches this module the same way GEMINI_API_KEY reaches image_gen.py).

CLI:
    python lib/web_research.py "<query>" [-n N] [--depth basic|advanced]
        [--no-answer] [--raw] [--json]
Prints a readable digest by default (an answer summary + numbered sources with
snippets), or the raw Tavily JSON with --json.
"""

from __future__ import annotations

import os
import sys
import json
import argparse
import urllib.error
import urllib.request

TAVILY_URL = "https://api.tavily.com/search"
REQUEST_TIMEOUT = 60


class ResearchError(Exception):
    """Raised for a bad key, network failure, or unusable response."""


def _format_http_error(e: "urllib.error.HTTPError") -> str:
    detail = ""
    try:
        body = json.loads(e.read().decode("utf-8"))
        detail = body.get("detail") or body.get("error") or ""
        if isinstance(detail, dict):
            detail = detail.get("error") or json.dumps(detail)
    except Exception:
        pass
    if e.code in (401, 403):
        return ("Tavily rejected the API key (HTTP %d). Check TAVILY_API_KEY in "
                ".env. %s" % (e.code, detail)).strip()
    if e.code == 429:
        return "Tavily rate limit / out of credits (HTTP 429). %s" % detail
    if e.code == 432:
        return "Tavily plan limit reached (HTTP 432). %s" % detail
    return "Tavily request failed (HTTP %d). %s" % (e.code, detail)


def research(query: str, *, max_results: int = 5, depth: str = "basic",
             include_answer: bool = True, include_raw: bool = False,
             topic: str = "general", api_key: str = None) -> dict:
    """Run one Tavily search and return the parsed response dict.

    Keys of interest: 'answer' (LLM summary, when include_answer), and 'results'
    (list of {title, url, content, score, raw_content?})."""
    api_key = api_key or os.environ.get("TAVILY_API_KEY", "").strip()
    if not api_key:
        raise ResearchError(
            "No TAVILY_API_KEY set. Add it to .env (get a key at tavily.com).")
    if not query or not query.strip():
        raise ResearchError("Empty query.")

    payload = json.dumps({
        "query": query.strip(),
        "search_depth": "advanced" if depth == "advanced" else "basic",
        "max_results": max(1, min(int(max_results), 20)),
        "include_answer": bool(include_answer),
        "include_raw_content": bool(include_raw),
        "topic": topic,
    }).encode("utf-8")

    req = urllib.request.Request(
        TAVILY_URL,
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
        raise ResearchError(_format_http_error(e)) from e
    except urllib.error.URLError as e:
        raise ResearchError(f"Network error reaching Tavily: {e.reason}") from e
    except json.JSONDecodeError as e:
        raise ResearchError("Unreadable response from Tavily.") from e
    if not isinstance(body, dict):
        raise ResearchError("Unexpected response from Tavily.")
    return body


def _digest(body: dict) -> str:
    """Render a readable digest of a Tavily response for the GM/agent to read."""
    out = []
    q = body.get("query", "")
    if q:
        out.append(f"QUERY: {q}")
    if body.get("answer"):
        out.append("\nANSWER:\n" + body["answer"].strip())
    results = body.get("results") or []
    if results:
        out.append("\nSOURCES:")
        for i, r in enumerate(results, 1):
            title = (r.get("title") or "").strip()
            url = (r.get("url") or "").strip()
            content = " ".join((r.get("content") or "").split())
            out.append(f"\n[{i}] {title}\n    {url}\n    {content}")
            if r.get("raw_content"):
                raw = " ".join(r["raw_content"].split())
                out.append(f"    --- full text ---\n    {raw[:4000]}")
    if not results and not body.get("answer"):
        out.append("(no results)")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description="Web research via Tavily")
    ap.add_argument("query", nargs="?", help="Search query (or read from stdin)")
    ap.add_argument("-n", "--max-results", type=int, default=5)
    ap.add_argument("--depth", choices=["basic", "advanced"], default="basic",
                    help="'advanced' is deeper (costs 2 credits)")
    ap.add_argument("--no-answer", action="store_true", help="Skip the LLM answer summary")
    ap.add_argument("--raw", action="store_true", help="Include full page text per source")
    ap.add_argument("--topic", choices=["general", "news"], default="general")
    ap.add_argument("--json", action="store_true", help="Emit raw Tavily JSON")
    args = ap.parse_args()

    query = args.query if args.query is not None else sys.stdin.read()
    try:
        body = research(query, max_results=args.max_results, depth=args.depth,
                        include_answer=not args.no_answer, include_raw=args.raw,
                        topic=args.topic)
    except ResearchError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(body, ensure_ascii=False, indent=2))
    else:
        print(_digest(body))


if __name__ == "__main__":
    main()
