"""Live web-search evidence via a self-hosted SearXNG instance (free, no API key).

Returns a small list of {title, url, snippet} for the orchestrator to feed into
axis /generate prompts as fresh, citable web evidence. Results are cached briefly
in-process so repeated generation calls for the same project don't re-hit SearXNG.
"""
from __future__ import annotations

import logging
import os
import time

import httpx

SEARXNG_URL = os.getenv("SEARXNG_URL", "http://searxng:8080")
_TIMEOUT = float(os.getenv("WEB_SEARCH_TIMEOUT", "12"))
_CACHE_TTL = float(os.getenv("WEB_SEARCH_CACHE_TTL", "900"))  # 15 min

logger = logging.getLogger("moufida.rag.websearch")

# query -> (expires_at, results)
_CACHE: dict[str, tuple[float, list[dict]]] = {}


def _cache_get(key: str) -> list[dict] | None:
    hit = _CACHE.get(key)
    if hit and hit[0] > time.time():
        return hit[1]
    if hit:
        _CACHE.pop(key, None)
    return None


def _cache_put(key: str, results: list[dict]) -> None:
    _CACHE[key] = (time.time() + _CACHE_TTL, results)


async def web_search(query: str, top_k: int = 3, language: str = "fr") -> list[dict]:
    """Query SearXNG's JSON API and return the top results as evidence dicts.

    Never raises: web evidence is best-effort, so failures return [] and let
    generation fall back to KB-only grounding.
    """
    query = (query or "").strip()
    if not query:
        return []

    cache_key = f"{language}:{top_k}:{query.lower()}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    params = {
        "q": query,
        "format": "json",
        "safesearch": "0",
        "categories": "general",
    }
    # SearXNG accepts a UI language code (e.g. "fr", "en", "ar").
    if language:
        params["language"] = language.split("-")[0]

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as http:
            resp = await http.get(
                f"{SEARXNG_URL}/search",
                params=params,
                headers={"X-Forwarded-For": "127.0.0.1", "X-Real-IP": "127.0.0.1"},
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        logger.warning("web_search failed for %r: %s", query, exc)
        return []

    results: list[dict] = []
    for item in data.get("results", []):
        url = item.get("url")
        title = item.get("title")
        if not url or not title:
            continue
        results.append({
            "title": title,
            "url": url,
            "snippet": (item.get("content") or "")[:280],
            "source": "web",
        })
        if len(results) >= top_k:
            break

    _cache_put(cache_key, results)
    return results
