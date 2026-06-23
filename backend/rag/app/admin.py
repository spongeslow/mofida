"""Admin operations: add resource, flag for review, list all resources."""
from __future__ import annotations

import json
import logging
import os
import pathlib

import httpx
from fastapi import HTTPException
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

from .ingest import _collection_for, ensure_collection, ingest_resource

KB_DIR = pathlib.Path("/srv/knowledge-base/resources")
QDRANT_URL = os.environ["QDRANT_URL"]
QDRANT_COLLECTION = os.environ["QDRANT_COLLECTION"]

REQUIRED_FIELDS = {"id", "title", "type", "stage", "body", "url"}

logger = logging.getLogger("moufida.rag.admin")


async def add_resource(resource: dict) -> dict:
    missing = REQUIRED_FIELDS - set(resource.keys())
    if missing:
        raise HTTPException(status_code=422, detail=f"missing required fields: {sorted(missing)}")

    path = KB_DIR / f"{resource['id']}.json"
    path.write_text(json.dumps(resource, ensure_ascii=False, indent=2))

    qdrant = AsyncQdrantClient(url=QDRANT_URL)
    try:
        async with httpx.AsyncClient() as http:
            await ensure_collection(qdrant, _collection_for(resource))
            n = await ingest_resource(resource, qdrant, http)
    finally:
        await qdrant.close()

    logger.info("added resource %s (%d chunks)", resource["id"], n)
    return {"id": resource["id"], "chunks_ingested": n}


KB_ROOT = pathlib.Path("/srv/knowledge-base")


def list_resources_disk() -> dict:
    """Read the curated KB resources straight from disk (always available,
    independent of Qdrant ingest state). Powers the founder-facing KB browser."""
    items: list[dict] = []
    for path in sorted(KB_DIR.glob("*.json")):
        try:
            d = json.loads(path.read_text())
        except Exception:
            continue
        body = d.get("body") or ""
        items.append({
            "id": d.get("id", path.stem),
            "title": d.get("title"),
            "summary": d.get("summary") or (body[:240] + ("…" if len(body) > 240 else "")),
            "body": body,
            "type": d.get("type"),
            "stage": d.get("stage"),
            "sector": d.get("sector"),
            "score_dimensions": d.get("score_dimensions"),
            "provider": d.get("provider"),
            "url": d.get("url"),
            "language": d.get("language"),
            "last_verified": d.get("last_verified"),
        })
    taxonomy = None
    try:
        taxonomy = json.loads((KB_ROOT / "taxonomy.json").read_text())
    except Exception:
        taxonomy = None
    return {"resources": items, "count": len(items), "taxonomy": taxonomy}


async def _all_collections(qdrant: AsyncQdrantClient) -> list[str]:
    return [c.name for c in (await qdrant.get_collections()).collections]


async def flag_resource(resource_id: str) -> dict:
    qdrant = AsyncQdrantClient(url=QDRANT_URL)
    try:
        for name in await _all_collections(qdrant):
            await qdrant.set_payload(
                collection_name=name,
                payload={"needs_review": True},
                points=Filter(
                    must=[FieldCondition(key="resource_id", match=MatchValue(value=resource_id))]
                ),
            )
    finally:
        await qdrant.close()

    logger.info("flagged resource %s for review", resource_id)
    return {"resource_id": resource_id, "needs_review": True}


async def list_resources() -> list[dict]:
    qdrant = AsyncQdrantClient(url=QDRANT_URL)
    seen: dict[str, dict] = {}
    try:
        for name in await _all_collections(qdrant):
            offset = None
            while True:
                result, offset = await qdrant.scroll(
                    collection_name=name,
                    with_payload=True,
                    limit=100,
                    offset=offset,
                )
                for point in result:
                    rid = point.payload.get("resource_id")
                    if rid and rid not in seen:
                        seen[rid] = {
                            "id": rid,
                            "title": point.payload.get("title"),
                            "url": point.payload.get("url"),
                            "provider": point.payload.get("provider"),
                            "type": point.payload.get("type"),
                            "stage": point.payload.get("stage"),
                            "collection": point.payload.get("collection", name),
                            "needs_review": point.payload.get("needs_review", False),
                        }
                if offset is None:
                    break
    finally:
        await qdrant.close()

    # Augment with last_verified from the on-disk JSON files (not stored in Qdrant).
    resources = list(seen.values())
    for r in resources:
        json_path = KB_DIR / f"{r['id']}.json"
        try:
            data = json.loads(json_path.read_text())
            r["last_verified"] = data.get("last_verified")
        except Exception:
            r.setdefault("last_verified", None)
    return resources
