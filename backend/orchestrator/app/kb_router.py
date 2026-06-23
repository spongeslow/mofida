"""Knowledge Base browsing — proxies the RAG service's curated resource list
so the desktop app can show founders what Moufida already knows (analysis §23).

  GET /kb/resources → { resources: [...], count, taxonomy }
"""
from __future__ import annotations

import logging
import os

import httpx
from fastapi import APIRouter

RAG_URL = os.getenv("RAG_URL", "http://rag:8300")

router = APIRouter()
logger = logging.getLogger("moufida.kb_router")


@router.get("/kb/resources")
async def kb_resources():
    """Best-effort proxy to the RAG disk-based resource list."""
    try:
        async with httpx.AsyncClient(timeout=10) as http:
            resp = await http.get(f"{RAG_URL}/resources")
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:  # pragma: no cover - best-effort
        logger.warning("kb resources fetch failed: %s", exc)
        return {"resources": [], "count": 0, "taxonomy": None}
