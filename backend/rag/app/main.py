"""Moufida Knowledge Base RAG service (port 8300).

Endpoints:
  GET  /health
  POST /retrieve          — hybrid retrieval (dense + BM25 + RRF + sector boost)
  POST /ingest            — chunk + embed all KB resources into Qdrant
  POST /admin/resource    — add a single resource (validate + ingest)
  POST /admin/flag/{id}   — mark resource needs_review=True
  GET  /admin/resources   — list all resources (for daemon staleness checker)
"""
from __future__ import annotations

import logging

from fastapi import FastAPI
from pydantic import BaseModel

from . import admin as _admin
from . import ingest as _ingest
from . import retrieve as _retrieve
from . import websearch as _websearch

app = FastAPI(title="Moufida RAG")
logger = logging.getLogger("moufida.rag")


class RetrieveRequest(BaseModel):
    query: str
    stage: str | None = None
    dimensions: list[str] = []
    sector: str | None = None
    top_k: int = 3
    collection: str | None = None
    # When set, blend each chunk's on-axis direction relevance (signal probe)
    # into the rank score (Phase H, paper 2).
    current_axis: str | None = None


class WebSearchRequest(BaseModel):
    query: str
    top_k: int = 3
    language: str = "fr"


@app.get("/health")
def health():
    return {"status": "ok", "service": "rag"}


@app.post("/retrieve")
async def retrieve(req: RetrieveRequest):
    results = await _retrieve.retrieve(
        query=req.query,
        stage=req.stage,
        dimensions=req.dimensions,
        sector=req.sector,
        top_k=req.top_k,
        collection=req.collection,
        current_axis=req.current_axis,
    )
    return {"query": req.query, "results": results, "count": len(results)}


@app.post("/web_search")
async def web_search(req: WebSearchRequest):
    results = await _websearch.web_search(req.query, top_k=req.top_k, language=req.language)
    return {"query": req.query, "results": results, "count": len(results)}


@app.post("/ingest")
async def ingest():
    return await _ingest.ingest_all()


@app.post("/admin/resource")
async def add_resource(resource: dict):
    return await _admin.add_resource(resource)


@app.post("/admin/flag/{resource_id}")
async def flag_resource(resource_id: str):
    return await _admin.flag_resource(resource_id)


@app.get("/admin/resources")
async def list_resources():
    resources = await _admin.list_resources()
    return {"resources": resources, "count": len(resources)}


@app.get("/resources")
def list_resources_disk():
    """Curated KB resources read from disk (full metadata + body + taxonomy)."""
    return _admin.list_resources_disk()
