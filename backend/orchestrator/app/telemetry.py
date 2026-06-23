"""Observability telemetry (Phase H, H4).

Captures three signals for the admin panel, all best-effort (never break a
request):
  • api_requests  — one row per orchestrator HTTP request (middleware)
  • llm_calls     — one row per Ollama call from the shared ``generate_json``
  • daemon_activities — daemon signals mirrored from the redis consumer

Also keeps an in-memory ring buffer of recent log lines and fans them out to SSE
subscribers for the live Logs view.

A ``request_id`` ContextVar is set by the middleware and read by ``generate_json``
so LLM calls correlate to the request that triggered them.
"""
from __future__ import annotations

import asyncio
import contextvars
import hashlib
import logging
import re
import time
from collections import deque
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("moufida.telemetry")

# ── Correlation context ────────────────────────────────────────────
request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)
project_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("project_id", default=None)

_UUID_RE = re.compile(
    r"/project/([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})"
)


def extract_project_id(path: str) -> str | None:
    m = _UUID_RE.search(path or "")
    return m.group(1) if m else None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── DB writers (best-effort) ───────────────────────────────────────
async def _pool():
    from .state_router import get_pool
    return await get_pool()


async def record_api_request(
    request_id: str, method: str, path: str, status_code: int,
    duration_ms: int, project_id: str | None,
) -> None:
    try:
        pool = await _pool()
        await pool.execute(
            """
            INSERT INTO api_requests
                (request_id, method, path, status_code, duration_ms, project_id)
            VALUES ($1::uuid, $2, $3, $4, $5, $6)
            """,
            request_id, method, path, status_code, duration_ms,
            project_id if project_id else None,
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug("record_api_request failed: %s", exc)


async def record_llm_call(
    *, axis: str | None, model: str, prompt: str, response: str | None,
    duration_ms: int | None, tokens_in: int | None, tokens_out: int | None,
) -> None:
    try:
        pool = await _pool()
        prompt_hash = hashlib.sha256((prompt or "").encode("utf-8")).hexdigest()
        rid = request_id_var.get()
        await pool.execute(
            """
            INSERT INTO llm_calls
                (request_id, axis, model, prompt_hash, prompt_preview,
                 response_preview, duration_ms, tokens_in, tokens_out)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            rid, axis, model, prompt_hash,
            (prompt or "")[:280], (response or "")[:280] if response else None,
            duration_ms, tokens_in, tokens_out,
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug("record_llm_call failed: %s", exc)


async def record_daemon_activity(
    *, project_id: str | None, watcher: str, activity: str, detail: dict | None = None,
) -> None:
    try:
        import json as _json
        pool = await _pool()
        await pool.execute(
            """
            INSERT INTO daemon_activities (project_id, watcher, activity, detail)
            VALUES ($1, $2, $3, $4::jsonb)
            """,
            project_id if project_id else None, watcher, activity,
            _json.dumps(detail or {}),
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug("record_daemon_activity failed: %s", exc)


# ── In-memory log ring buffer + SSE fan-out ────────────────────────
_RING: deque[dict] = deque(maxlen=500)
_subscribers: set[asyncio.Queue] = set()


def recent_logs(limit: int = 200) -> list[dict]:
    items = list(_RING)
    return items[-limit:]


def subscribe_logs() -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue(maxsize=200)
    _subscribers.add(q)
    return q


def unsubscribe_logs(q: asyncio.Queue) -> None:
    _subscribers.discard(q)


class RingBufferHandler(logging.Handler):
    """Logging handler that records recent lines and fans them to SSE queues."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            entry = {
                "ts": _now_iso(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }
        except Exception:  # noqa: BLE001
            return
        _RING.append(entry)
        for q in list(_subscribers):
            try:
                q.put_nowait(entry)
            except Exception:  # noqa: BLE001 — queue full / closed
                pass


def install_log_capture(level: int = logging.INFO) -> None:
    """Attach the ring-buffer handler to the root logger (idempotent)."""
    root = logging.getLogger()
    if any(isinstance(h, RingBufferHandler) for h in root.handlers):
        return
    handler = RingBufferHandler()
    handler.setLevel(level)
    root.addHandler(handler)
    if root.level > level or root.level == logging.NOTSET:
        root.setLevel(level)


# ── Middleware timing context manager ──────────────────────────────
class RequestTimer:
    def __init__(self) -> None:
        self.start = time.perf_counter()

    def elapsed_ms(self) -> int:
        return int((time.perf_counter() - self.start) * 1000)


def now_timer() -> RequestTimer:
    return RequestTimer()
