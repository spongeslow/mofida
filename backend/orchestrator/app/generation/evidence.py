"""Evidence assembly for creation-mode generation.

Centralizes RAG + live-web evidence gathering so the nine axis services stay
thin: the orchestrator fetches per-axis curated KB hits (axis Qdrant collection,
dimension/sector filtered) AND fresh web results (SearXNG via RAG /web_search),
then injects them into the axis /generate body. Each axis weaves the evidence
into its prompt and echoes the cited sources back as `citations`.

Best-effort by design: any failure returns empty lists so generation degrades
to ungrounded output rather than erroring.
"""
from __future__ import annotations

import asyncio
import logging
import os

import httpx

from ..axis_registry import AXES

RAG_URL = os.getenv("RAG_URL", "http://rag:8300")

logger = logging.getLogger("moufida.generation.evidence")

# Per-axis evidence config: Qdrant collection + topic terms for the query.
# Collections are created on demand by the RAG ingest; retrieve falls back to
# the main KB collection when an axis collection is missing or empty.
AXIS_EVIDENCE: dict[str, dict] = {
    "ideation":       {"collection": "ideation",       "topic": "startup ideation maturity validation problem solution fit"},
    "market":         {"collection": "market",         "topic": "market analysis TAM SAM SOM competitors customer segments"},
    "product":        {"collection": "product",        "topic": "product offering MVP value proposition pricing features"},
    "brand":          {"collection": "brand",          "topic": "branding innovation differentiation positioning intellectual property"},
    "business-model": {"collection": "business-model", "topic": "business model revenue streams unit economics scalability funding"},
    "legal":          {"collection": "legal",          "topic": "legal compliance regulation data protection company registration Tunisia"},
    "operations":     {"collection": "operations",     "topic": "operations supply chain hiring processes infrastructure"},
    "marketing":      {"collection": "marketing",      "topic": "marketing channels customer acquisition brand awareness content"},
    "sales":          {"collection": "sales",          "topic": "sales pipeline partnerships distribution channels conversion"},
}


def _dimensions_for(slug: str) -> list[str]:
    score = AXES.get(slug, {}).get("score")
    return [score] if score else []


async def _rag_retrieve(http: httpx.AsyncClient, query: str, collection: str,
                        dimensions: list[str], sector: str | None,
                        current_axis: str | None = None) -> list[dict]:
    try:
        resp = await http.post(
            f"{RAG_URL}/retrieve",
            json={"query": query, "dimensions": dimensions, "sector": sector,
                  "collection": collection, "top_k": 3, "current_axis": current_axis},
            timeout=30.0,
        )
        resp.raise_for_status()
        return resp.json().get("results", [])
    except Exception as exc:
        logger.warning("RAG retrieve failed (collection=%s): %s", collection, exc)
        return []


async def _web_search(http: httpx.AsyncClient, query: str, language: str) -> list[dict]:
    try:
        resp = await http.post(
            f"{RAG_URL}/web_search",
            json={"query": query, "top_k": 3, "language": language},
            timeout=20.0,
        )
        resp.raise_for_status()
        return resp.json().get("results", [])
    except Exception as exc:
        logger.warning("web_search failed: %s", exc)
        return []


async def fetch_evidence(axis_slug: str, idea: str, profile: dict, language: str) -> dict:
    """Return {"kb": [...], "web": [...]} evidence for one axis generation call."""
    cfg = AXIS_EVIDENCE.get(axis_slug)
    if cfg is None:
        return {"kb": [], "web": []}

    sector = profile.get("sector")
    idea_short = (idea or "").strip()[:200]
    rag_query = f"{cfg['topic']} {idea_short}".strip()
    web_query = f"{idea_short} {cfg['topic']} Tunisia startup".strip()
    dimensions = _dimensions_for(axis_slug)

    async with httpx.AsyncClient() as http:
        kb, web = await asyncio.gather(
            _rag_retrieve(http, rag_query, cfg["collection"], dimensions, sector, axis_slug),
            _web_search(http, web_query, language),
        )
    logger.info("evidence axis=%s kb=%d web=%d", axis_slug, len(kb), len(web))
    return {"kb": kb, "web": web}
