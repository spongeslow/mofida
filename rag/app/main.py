"""Moufida Knowledge Base RAG service (port 8300).

Phase 0 scaffold: /health plus stubbed ingest/retrieve/admin endpoints. The
metadata-filtered hybrid retrieval pipeline (Qdrant + BM25 + RRF) lands in Phase 3.
"""
from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Moufida RAG")


class RetrieveRequest(BaseModel):
    query: str
    stage: str | None = None
    dimensions: list[str] = []
    sector: str | None = None
    top_k: int = 3


@app.get("/health")
def health():
    return {"status": "ok", "service": "rag"}


@app.post("/retrieve")
def retrieve(req: RetrieveRequest):
    """Metadata-filtered hybrid retrieval (Phase 3)."""
    return {"query": req.query, "results": [], "status": "not_implemented"}


@app.post("/ingest")
def ingest():
    """Chunk + embed resources into Qdrant (Phase 3)."""
    return {"status": "not_implemented"}


@app.post("/admin/resource")
def add_resource(resource: dict):
    """Add or flag a knowledge-base resource (Phase 3)."""
    return {"status": "not_implemented"}
