"""Hybrid retrieval: dense (Qdrant) + BM25 + RRF fusion + sector boost."""
from __future__ import annotations

import logging
import os
from typing import Optional

import httpx
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchAny, MatchValue
from rank_bm25 import BM25Okapi

OLLAMA_BASE_URL = os.environ["OLLAMA_BASE_URL"]
EMBED_MODEL = os.environ["MOUFIDA_EMBED_MODEL"]
QDRANT_URL = os.environ["QDRANT_URL"]
QDRANT_COLLECTION = os.environ["QDRANT_COLLECTION"]

_BM25_POOL = 40   # candidates fetched from Qdrant before BM25 re-ranking
_SECTOR_BOOST = 1.3
_RRF_K = 60

# Axis-direction re-ranking (Phase H, paper 2): blend the fused rank score with
# the chunk's on-axis relevance from the signal probe. Best-effort.
SIGNAL_URL = os.environ.get("SIGNAL_URL", "http://signal:8010")
_PROBE_BLEND = 0.30        # weight given to the on-axis direction score
_RERANK_POOL_MULT = 3      # how many deduped candidates to probe before truncating

logger = logging.getLogger("moufida.rag.retrieve")


async def _probe_rerank(
    candidates: list[dict], current_axis: str, http: httpx.AsyncClient
) -> list[dict]:
    """Blend each candidate's RRF score with its on-axis direction relevance.

    Each candidate carries ``_vector`` (its embedding) and ``score`` (RRF). The
    signal probe maps the embedding to a per-axis relevance; we mix the current
    axis's relevance into the score. If the probe is unavailable, candidates are
    returned untouched (best-effort)."""
    reranked: list[dict] = []
    probe_ok = True
    for cand in candidates:
        vec = cand.get("_vector")
        if probe_ok and vec:
            try:
                resp = await http.post(
                    f"{SIGNAL_URL}/probe/project",
                    json={"embedding": vec, "top_k": 9},
                    timeout=2.0,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    relevance = data.get("axis_relevance", {})
                    on_axis = float(relevance.get(current_axis, 0.5))
                    cand["axis_relevance"] = relevance
                    cand["on_axis_score"] = round(on_axis, 4)
                    cand["score"] = round(
                        (1 - _PROBE_BLEND) * cand["score"] + _PROBE_BLEND * on_axis, 6
                    )
                else:
                    probe_ok = False
            except Exception as exc:  # noqa: BLE001 — best-effort
                logger.debug("probe rerank unavailable: %s", exc)
                probe_ok = False
        reranked.append(cand)
    reranked.sort(key=lambda c: c["score"], reverse=True)
    return reranked


async def _embed_query(query: str, http: httpx.AsyncClient) -> list[float]:
    resp = await http.post(
        f"{OLLAMA_BASE_URL}/api/embed",
        json={"model": EMBED_MODEL, "input": query},
        timeout=60.0,
    )
    resp.raise_for_status()
    data = resp.json()
    emb = data.get("embeddings") or data.get("embedding")
    if emb and isinstance(emb[0], list):
        return emb[0]
    return emb


def _build_filter(stage: Optional[str], dimensions: list[str]) -> Filter:
    must: list = [FieldCondition(key="needs_review", match=MatchValue(value=False))]
    if stage:
        must.append(FieldCondition(key="stage", match=MatchAny(any=[stage])))
    if dimensions:
        must.append(FieldCondition(key="score_dimensions", match=MatchAny(any=dimensions)))
    return Filter(must=must)


def _rrf(
    dense_ids: list[str],
    bm25_pairs: list[tuple[str, float]],
    k: int = _RRF_K,
) -> dict[str, float]:
    scores: dict[str, float] = {}
    for rank, pid in enumerate(dense_ids):
        scores[pid] = scores.get(pid, 0.0) + 1.0 / (k + rank + 1)
    for rank, (pid, _) in enumerate(bm25_pairs):
        scores[pid] = scores.get(pid, 0.0) + 1.0 / (k + rank + 1)
    return scores


async def retrieve(
    query: str,
    stage: Optional[str] = None,
    dimensions: list[str] | None = None,
    sector: Optional[str] = None,
    top_k: int = 3,
    collection: Optional[str] = None,
    current_axis: Optional[str] = None,
) -> list[dict]:
    if dimensions is None:
        dimensions = []

    target_collection = collection or QDRANT_COLLECTION

    qdrant = AsyncQdrantClient(url=QDRANT_URL)
    try:
        async with httpx.AsyncClient() as http:
            query_vec = await _embed_query(query, http)

        qfilter = _build_filter(stage, dimensions)
        try:
            _resp = await qdrant.query_points(
                collection_name=target_collection,
                query=query_vec,
                query_filter=qfilter,
                limit=_BM25_POOL,
                with_payload=True,
                with_vectors=bool(current_axis),
            )
            dense_results = _resp.points
        except Exception as exc:
            # Missing/empty collection — fall back to the main KB so a thin
            # axis corpus never breaks generation.
            logger.warning("retrieve on %s failed (%s); falling back to %s",
                           target_collection, exc, QDRANT_COLLECTION)
            if target_collection == QDRANT_COLLECTION:
                return []
            _resp = await qdrant.query_points(
                collection_name=QDRANT_COLLECTION,
                query=query_vec,
                query_filter=qfilter,
                limit=_BM25_POOL,
                with_payload=True,
                with_vectors=bool(current_axis),
            )
            dense_results = _resp.points
    finally:
        await qdrant.close()

    if not dense_results:
        return []

    # BM25 over the dense pool's chunk texts.
    tokenized = [
        hit.payload.get("chunk_text", "").lower().split() for hit in dense_results
    ]
    bm25 = BM25Okapi(tokenized)
    q_tokens = query.lower().split()
    bm25_raw = bm25.get_scores(q_tokens)
    bm25_ranked = sorted(
        zip([h.id for h in dense_results], bm25_raw),
        key=lambda x: x[1],
        reverse=True,
    )

    dense_ids = [h.id for h in dense_results]
    rrf_scores = _rrf(dense_ids, bm25_ranked)

    # Sector boost: multiply RRF score for matching sector hits.
    if sector:
        for hit in dense_results:
            if sector in hit.payload.get("sector", []):
                rrf_scores[hit.id] = rrf_scores.get(hit.id, 0.0) * _SECTOR_BOOST

    sorted_hits = sorted(
        dense_results, key=lambda h: rrf_scores.get(h.id, 0.0), reverse=True
    )

    # Deduplicate by resource_id, keep highest-scoring chunk per resource. When
    # axis re-ranking is on, keep a larger candidate pool so the probe can
    # reorder it before we truncate to top_k.
    pool_size = top_k * _RERANK_POOL_MULT if current_axis else top_k
    seen: set[str] = set()
    candidates: list[dict] = []
    for hit in sorted_hits:
        rid = hit.payload.get("resource_id")
        if rid in seen:
            continue
        seen.add(rid)
        candidates.append({
            "resource_id": rid,
            "title": hit.payload.get("title"),
            "type": hit.payload.get("type"),
            "url": hit.payload.get("url"),
            "provider": hit.payload.get("provider"),
            "language": hit.payload.get("language"),
            "score": round(rrf_scores.get(hit.id, 0.0), 6),
            "matched_chunk": hit.payload.get("chunk_text", ""),
            "_vector": list(hit.vector) if current_axis and hit.vector else None,
        })
        if len(candidates) >= pool_size:
            break

    if current_axis:
        async with httpx.AsyncClient() as http:
            candidates = await _probe_rerank(candidates, current_axis, http)

    results = candidates[:top_k]
    for r in results:
        r.pop("_vector", None)
    return results
