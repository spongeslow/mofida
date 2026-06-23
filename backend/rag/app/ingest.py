"""Chunk resources, embed via Ollama, upsert to Qdrant."""
from __future__ import annotations

import json
import logging
import os
import pathlib
import uuid

import httpx
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

OLLAMA_BASE_URL = os.environ["OLLAMA_BASE_URL"]
EMBED_MODEL = os.environ["MOUFIDA_EMBED_MODEL"]
QDRANT_URL = os.environ["QDRANT_URL"]
QDRANT_COLLECTION = os.environ["QDRANT_COLLECTION"]

KB_DIR = pathlib.Path("/srv/knowledge-base/resources")
# bge-m3 (multilingual: AR/FR/EN) emits 1024-dim vectors. nomic-embed-text was 768.
VECTOR_DIM = int(os.getenv("MOUFIDA_EMBED_DIM", "1024"))

# Axis-direction auto-tagging (Phase H, paper 2). Best-effort: until the probe
# directions have been computed (which happens *from* ingested vectors), this
# returns nothing and chunks simply carry no auto_axes.
SIGNAL_URL = os.environ.get("SIGNAL_URL", "http://signal:8010")

logger = logging.getLogger("moufida.rag.ingest")


async def _tag_axes(embedding: list[float], http: httpx.AsyncClient) -> list[str]:
    """Return the top-2 diagnostic axes for an embedding via the signal probe."""
    try:
        resp = await http.post(
            f"{SIGNAL_URL}/probe/project",
            json={"embedding": embedding, "top_k": 2},
            timeout=2.0,
        )
        if resp.status_code != 200:
            return []
        return [ax for ax, _ in resp.json().get("top_axes", [])]
    except Exception:  # noqa: BLE001 — best-effort
        return []


def _collection_for(resource: dict) -> str:
    """Resource may declare its own collection; default to the main KB collection."""
    return resource.get("collection") or QDRANT_COLLECTION


def _chunk_body(body: str) -> list[str]:
    return [p.strip() for p in body.split("\n\n") if p.strip()]


def _point_id(resource_id: str, chunk_index: int) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{resource_id}::{chunk_index}"))


async def _embed(text: str, http: httpx.AsyncClient) -> list[float]:
    resp = await http.post(
        f"{OLLAMA_BASE_URL}/api/embed",
        json={"model": EMBED_MODEL, "input": text},
        timeout=60.0,
    )
    resp.raise_for_status()
    data = resp.json()
    # /api/embed returns {"embeddings": [[...768...]]}
    # older /api/embeddings returns {"embedding": [...768...]}
    emb = data.get("embeddings") or data.get("embedding")
    if emb and isinstance(emb[0], list):
        return emb[0]
    return emb


async def ensure_collection(qdrant: AsyncQdrantClient, name: str) -> None:
    existing = {c.name for c in (await qdrant.get_collections()).collections}
    if name not in existing:
        await qdrant.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
        )
        logger.info("created Qdrant collection %s (dim=%d)", name, VECTOR_DIM)
        return

    # Collection exists — verify its vector size matches the current embed model.
    # Switching embedding models (e.g. nomic 768 -> bge-m3 1024) changes the dim,
    # so recreate the collection to avoid upsert dimension-mismatch errors.
    try:
        info = await qdrant.get_collection(name)
        current_dim = info.config.params.vectors.size
    except Exception as exc:
        logger.warning("could not read collection %s config: %s", name, exc)
        return
    if current_dim != VECTOR_DIM:
        logger.warning("collection %s dim %d != %d — recreating", name, current_dim, VECTOR_DIM)
        await qdrant.delete_collection(name)
        await qdrant.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
        )


async def ingest_resource(
    resource: dict,
    qdrant: AsyncQdrantClient,
    http: httpx.AsyncClient,
) -> int:
    rid = resource["id"]
    collection = _collection_for(resource)
    chunks = _chunk_body(resource.get("body", ""))
    if not chunks:
        return 0

    points: list[PointStruct] = []
    for i, chunk in enumerate(chunks):
        vec = await _embed(chunk, http)
        auto_axes = await _tag_axes(vec, http)
        points.append(
            PointStruct(
                id=_point_id(rid, i),
                vector=vec,
                payload={
                    "resource_id": rid,
                    "chunk_index": i,
                    "chunk_text": chunk,
                    "title": resource.get("title", ""),
                    "type": resource.get("type", ""),
                    "stage": resource.get("stage", []),
                    "sector": resource.get("sector", []),
                    "score_dimensions": resource.get("score_dimensions", []),
                    "auto_axes": auto_axes,
                    "url": resource.get("url", ""),
                    "provider": resource.get("provider", ""),
                    "language": resource.get("language", "fr"),
                    "collection": collection,
                    "needs_review": False,
                },
            )
        )

    await qdrant.upsert(collection_name=collection, points=points)
    return len(points)


async def ingest_all() -> dict:
    if not KB_DIR.exists():
        return {"resources": 0, "chunks": 0, "errors": [{"error": f"KB dir not found: {KB_DIR}"}]}

    qdrant = AsyncQdrantClient(url=QDRANT_URL)
    total_chunks = 0
    total_resources = 0
    errors: list[dict] = []

    ensured: set[str] = set()
    per_collection: dict[str, int] = {}
    try:
        async with httpx.AsyncClient() as http:
            for path in sorted(KB_DIR.glob("*.json")):
                try:
                    resource = json.loads(path.read_text())
                    collection = _collection_for(resource)
                    if collection not in ensured:
                        await ensure_collection(qdrant, collection)
                        ensured.add(collection)
                    n = await ingest_resource(resource, qdrant, http)
                    total_chunks += n
                    total_resources += 1
                    per_collection[collection] = per_collection.get(collection, 0) + n
                    logger.info("ingested %s (%d chunks) -> %s", path.name, n, collection)
                except Exception as exc:
                    logger.error("ingest failed for %s: %s", path.name, exc)
                    errors.append({"file": path.name, "error": str(exc)})
    finally:
        await qdrant.close()

    return {
        "resources": total_resources,
        "chunks": total_chunks,
        "collections": per_collection,
        "errors": errors,
    }
