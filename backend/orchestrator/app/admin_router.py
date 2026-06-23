"""Admin / observability API (Phase H, H4).

Read-only endpoints under ``/api/admin/*`` powering the standalone admin SPA:
service health, request log + distributed trace, LLM-call log, daemon-activity
log, KB health, and a live log SSE stream.

Auth: if ``ADMIN_TOKEN`` is set, every route requires it (Bearer header, or
``?token=`` for the SSE stream). If unset, auth is disabled (local-only).
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time

import httpx
from fastapi import APIRouter, Header, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from . import telemetry
from .state_router import get_pool

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger("moufida.admin")

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
SEARXNG_URL = os.getenv("SEARXNG_URL", "http://searxng:8080")
SIGNAL_URL = os.getenv("SIGNAL_URL", "http://signal:8010")
_ALIVE_WINDOW_S = 90


def _check_token(authorization: str | None, token: str | None) -> None:
    if not ADMIN_TOKEN:
        return
    provided = token or ""
    if authorization and authorization.lower().startswith("bearer "):
        provided = authorization[7:]
    if provided != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="invalid or missing admin token")


# ── Health ─────────────────────────────────────────────────────────
async def _timed(coro):
    start = time.perf_counter()
    try:
        await coro
        return {"status": "ok", "latency_ms": int((time.perf_counter() - start) * 1000)}
    except Exception as exc:  # noqa: BLE001
        return {"status": "down", "error": str(exc)[:160],
                "latency_ms": int((time.perf_counter() - start) * 1000)}


async def _pg_health(pool) -> dict:
    return await _timed(pool.fetchval("SELECT 1"))


async def _redis_health() -> dict:
    async def _ping():
        import redis.asyncio as aioredis
        r = aioredis.from_url(REDIS_URL)
        try:
            await r.ping()
        finally:
            await r.aclose()
    return await _timed(_ping())


async def _http_health(url: str, extra: dict | None = None) -> dict:
    start = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=5.0) as http:
            resp = await http.get(url)
            resp.raise_for_status()
            out = {"status": "ok", "latency_ms": int((time.perf_counter() - start) * 1000)}
            if extra:
                out.update(extra(resp) if callable(extra) else extra)
            return out
    except Exception as exc:  # noqa: BLE001
        return {"status": "down", "error": str(exc)[:160],
                "latency_ms": int((time.perf_counter() - start) * 1000)}


async def _qdrant_health() -> dict:
    start = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=5.0) as http:
            resp = await http.get(f"{QDRANT_URL}/collections")
            resp.raise_for_status()
            cols = resp.json().get("result", {}).get("collections", [])
            total = 0
            for c in cols:
                try:
                    info = await http.get(f"{QDRANT_URL}/collections/{c['name']}")
                    total += info.json().get("result", {}).get("points_count", 0) or 0
                except Exception:  # noqa: BLE001
                    pass
            return {
                "status": "ok", "latency_ms": int((time.perf_counter() - start) * 1000),
                "collection_count": len(cols), "total_vectors": total,
            }
    except Exception as exc:  # noqa: BLE001
        return {"status": "down", "error": str(exc)[:160]}


async def _ollama_health() -> dict:
    start = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=5.0) as http:
            resp = await http.get(f"{OLLAMA_BASE}/api/tags")
            resp.raise_for_status()
            models = [m.get("name") for m in resp.json().get("models", [])]
            return {"status": "ok", "latency_ms": int((time.perf_counter() - start) * 1000),
                    "loaded_models": models}
    except Exception as exc:  # noqa: BLE001
        return {"status": "down", "error": str(exc)[:160]}


async def _daemon_health(pool) -> dict:
    try:
        row = await pool.fetchrow(
            "SELECT paused, focus_project_id, last_beat FROM daemon_control WHERE id = TRUE"
        )
    except Exception as exc:  # noqa: BLE001
        return {"status": "unknown", "error": str(exc)[:160]}
    if not row or not row["last_beat"]:
        return {"alive": False, "paused": bool(row["paused"]) if row else False,
                "focus_project_id": None, "last_beat": None}
    import datetime as _dt
    age = (_dt.datetime.now(_dt.timezone.utc) - row["last_beat"]).total_seconds()
    return {
        "alive": age <= _ALIVE_WINDOW_S,
        "paused": bool(row["paused"]),
        "focus_project_id": str(row["focus_project_id"]) if row["focus_project_id"] else None,
        "last_beat": row["last_beat"].isoformat(),
        "last_beat_age_s": int(age),
    }


@router.get("/health")
async def admin_health(authorization: str | None = Header(default=None),
                       token: str | None = Query(default=None)):
    _check_token(authorization, token)
    pool = await get_pool()
    pg, redis_h, qdrant_h, ollama_h, searx_h, signal_h, daemon_h, kb = await asyncio.gather(
        _pg_health(pool), _redis_health(), _qdrant_health(), _ollama_health(),
        _http_health(f"{SEARXNG_URL}/healthz"), _http_health(f"{SIGNAL_URL}/health"),
        _daemon_health(pool), _kb_health_data(),
    )
    return {
        "services": {
            "postgres": pg, "redis": redis_h, "qdrant": qdrant_h, "ollama": ollama_h,
            "searxng": searx_h, "signal": signal_h, "daemon": daemon_h,
        },
        "kb": kb,
    }


# ── KB health ──────────────────────────────────────────────────────
async def _kb_health_data() -> dict:
    try:
        async with httpx.AsyncClient(timeout=5.0) as http:
            resp = await http.get(f"{QDRANT_URL}/collections")
            resp.raise_for_status()
            cols = resp.json().get("result", {}).get("collections", [])
            out = {}
            total = 0
            for c in cols:
                name = c["name"]
                info = await http.get(f"{QDRANT_URL}/collections/{name}")
                count = info.json().get("result", {}).get("points_count", 0) or 0
                total += count
                # Sample a few titles.
                titles: list[str] = []
                try:
                    scroll = await http.post(
                        f"{QDRANT_URL}/collections/{name}/points/scroll",
                        json={"limit": 3, "with_payload": True},
                    )
                    for p in scroll.json().get("result", {}).get("points", []):
                        t = (p.get("payload") or {}).get("title")
                        if t:
                            titles.append(t)
                except Exception:  # noqa: BLE001
                    pass
                out[name] = {"doc_count": count, "sample_titles": titles}
            return {"collections": out, "total_vectors": total}
    except Exception as exc:  # noqa: BLE001
        return {"collections": {}, "total_vectors": 0, "error": str(exc)[:160]}


@router.get("/kb/health")
async def kb_health(authorization: str | None = Header(default=None),
                    token: str | None = Query(default=None)):
    _check_token(authorization, token)
    return await _kb_health_data()


# ── Request log + trace ────────────────────────────────────────────
@router.get("/requests")
async def list_requests(
    limit: int = Query(default=50, le=500),
    path_prefix: str | None = None,
    authorization: str | None = Header(default=None),
    token: str | None = Query(default=None),
):
    _check_token(authorization, token)
    pool = await get_pool()
    if path_prefix:
        rows = await pool.fetch(
            """SELECT request_id, method, path, status_code, duration_ms, project_id, created_at
                 FROM api_requests WHERE path LIKE $1 ORDER BY created_at DESC LIMIT $2""",
            f"{path_prefix}%", limit,
        )
    else:
        rows = await pool.fetch(
            """SELECT request_id, method, path, status_code, duration_ms, project_id, created_at
                 FROM api_requests ORDER BY created_at DESC LIMIT $1""",
            limit,
        )
    return {"rows": [_req_row(r) for r in rows], "count": len(rows)}


def _req_row(r) -> dict:
    return {
        "request_id": str(r["request_id"]),
        "method": r["method"], "path": r["path"],
        "status_code": r["status_code"], "duration_ms": r["duration_ms"],
        "project_id": str(r["project_id"]) if r["project_id"] else None,
        "created_at": r["created_at"].isoformat() if r["created_at"] else None,
    }


def _llm_row(r) -> dict:
    return {
        "id": str(r["id"]),
        "request_id": str(r["request_id"]) if r["request_id"] else None,
        "axis": r["axis"], "model": r["model"],
        "prompt_preview": r["prompt_preview"], "response_preview": r["response_preview"],
        "duration_ms": r["duration_ms"], "tokens_in": r["tokens_in"], "tokens_out": r["tokens_out"],
        "created_at": r["created_at"].isoformat() if r["created_at"] else None,
    }


@router.get("/trace/{request_id}")
async def get_trace(request_id: str, authorization: str | None = Header(default=None),
                    token: str | None = Query(default=None)):
    _check_token(authorization, token)
    pool = await get_pool()
    req = await pool.fetchrow(
        """SELECT request_id, method, path, status_code, duration_ms, project_id, created_at
             FROM api_requests WHERE request_id = $1::uuid ORDER BY created_at DESC LIMIT 1""",
        request_id,
    )
    llm = await pool.fetch(
        """SELECT id, request_id, axis, model, prompt_preview, response_preview,
                  duration_ms, tokens_in, tokens_out, created_at
             FROM llm_calls WHERE request_id = $1::uuid ORDER BY created_at ASC""",
        request_id,
    )
    return {
        "request": _req_row(req) if req else None,
        "llm_calls": [_llm_row(r) for r in llm],
    }


@router.get("/llm")
async def list_llm(
    limit: int = Query(default=30, le=200),
    axis: str | None = None,
    authorization: str | None = Header(default=None),
    token: str | None = Query(default=None),
):
    _check_token(authorization, token)
    pool = await get_pool()
    if axis:
        rows = await pool.fetch(
            """SELECT id, request_id, axis, model, prompt_preview, response_preview,
                      duration_ms, tokens_in, tokens_out, created_at
                 FROM llm_calls WHERE axis = $1 ORDER BY created_at DESC LIMIT $2""",
            axis, limit,
        )
    else:
        rows = await pool.fetch(
            """SELECT id, request_id, axis, model, prompt_preview, response_preview,
                      duration_ms, tokens_in, tokens_out, created_at
                 FROM llm_calls ORDER BY created_at DESC LIMIT $1""",
            limit,
        )
    return {"rows": [_llm_row(r) for r in rows], "count": len(rows)}


@router.get("/daemon/activity")
async def list_daemon_activity(
    limit: int = Query(default=100, le=500),
    watcher: str | None = None,
    authorization: str | None = Header(default=None),
    token: str | None = Query(default=None),
):
    _check_token(authorization, token)
    pool = await get_pool()
    if watcher:
        rows = await pool.fetch(
            """SELECT id, project_id, watcher, activity, detail, created_at
                 FROM daemon_activities WHERE watcher = $1 ORDER BY created_at DESC LIMIT $2""",
            watcher, limit,
        )
    else:
        rows = await pool.fetch(
            """SELECT id, project_id, watcher, activity, detail, created_at
                 FROM daemon_activities ORDER BY created_at DESC LIMIT $1""",
            limit,
        )
    out = []
    for r in rows:
        detail = r["detail"]
        if isinstance(detail, str):
            try:
                detail = json.loads(detail)
            except Exception:  # noqa: BLE001
                detail = {}
        out.append({
            "id": str(r["id"]),
            "project_id": str(r["project_id"]) if r["project_id"] else None,
            "watcher": r["watcher"], "activity": r["activity"], "detail": detail,
            "created_at": r["created_at"].isoformat() if r["created_at"] else None,
        })
    return {"rows": out, "count": len(out)}


# ── Live log stream ────────────────────────────────────────────────
@router.get("/logs/recent")
async def logs_recent(limit: int = Query(default=200, le=500),
                      authorization: str | None = Header(default=None),
                      token: str | None = Query(default=None)):
    _check_token(authorization, token)
    return {"logs": telemetry.recent_logs(limit)}


@router.get("/logs/stream")
async def logs_stream(request: Request, token: str | None = Query(default=None),
                      authorization: str | None = Header(default=None)):
    _check_token(authorization, token)
    q = telemetry.subscribe_logs()

    async def gen():
        try:
            # Replay the recent buffer first.
            for entry in telemetry.recent_logs(100):
                yield f"data: {json.dumps(entry)}\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    entry = await asyncio.wait_for(q.get(), timeout=15.0)
                    yield f"data: {json.dumps(entry)}\n\n"
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            telemetry.unsubscribe_logs(q)

    return StreamingResponse(gen(), media_type="text/event-stream")
