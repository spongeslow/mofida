"""Moufida Orchestrator -- FastAPI + LangGraph brain (port 8001)."""
from __future__ import annotations

import asyncio
import json
import os

import httpx
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from . import redis_consumer as _redis_consumer
from . import sse
from .admin_router import router as admin_router
from .axis_registry import AXES, diagnostic_order
from .cbm.router import router as cbm_router
from .competitor_router import router as competitor_router
from .creation_router import router as creation_router
from .daemon_router import router as daemon_router
from .diagnostic_router import router as diagnostic_router
from .events_router import router as events_router
from .history_router import router as history_router
from .integrations_router import router as integrations_router
from .intake_router import router as intake_router
from .kb_router import router as kb_router
from .lang_detect import detect_language
from .opportunity_router import router as opportunity_router
from .persona_router import router as persona_router
from .pitch_router import router as pitch_router
from .roadmap_router import router as roadmap_router
from .scenario_router import router as scenario_router
from .state_router import close_pool, get_pool, router as state_router
from .tools_router import router as tools_router
from .watch_targets_router import router as watch_targets_router

OLLAMA_BASE_URL = os.environ["OLLAMA_BASE_URL"]
OLLAMA_CHAT_MODEL = os.environ["OLLAMA_CHAT_MODEL"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Capture logs into the ring buffer for the admin Logs view (Phase H).
    try:
        from . import telemetry
        telemetry.install_log_capture()
    except Exception:  # noqa: BLE001
        pass
    task = asyncio.create_task(_redis_consumer.consume())
    # Seed the dependency graph mirror table on startup (idempotent).
    try:
        from .dependency import seed_db_mirror
        pool = await get_pool()
        await seed_db_mirror(pool)
    except Exception as _exc:
        import logging as _logging
        _logging.getLogger("moufida.main").warning("dependency_graph seed skipped: %s", _exc)
    # Catch up on any tool_signals that arrived while we were down (Phase G).
    try:
        from . import signals as _signals
        drained = await _signals.drain_unprocessed()
        if drained:
            import logging as _logging
            _logging.getLogger("moufida.main").info("drained %d pending tool_signals", drained)
    except Exception as _exc:
        import logging as _logging
        _logging.getLogger("moufida.main").warning("tool_signals drain skipped: %s", _exc)
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        await close_pool()


app = FastAPI(title="Moufida Orchestrator", lifespan=lifespan)

# Observability: record every request + correlate downstream LLM calls (Phase H).
from .telemetry_middleware import TelemetryMiddleware  # noqa: E402
app.add_middleware(TelemetryMiddleware)

# The Tauri webview hits the orchestrator without browser CORS enforcement, but
# the Vite dev server (and the `--profile web` browser build) are a different
# origin (localhost:5173/5174). Allow any localhost origin plus the Tauri
# custom-protocol origins so fetch()/EventSource calls aren't blocked.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^(https?://(localhost|127\.0\.0\.1)(:\d+)?|tauri://localhost|https?://tauri\.localhost)$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(state_router, prefix="/api/v1")
app.include_router(intake_router, prefix="/api/v1")
app.include_router(kb_router, prefix="/api/v1")
app.include_router(creation_router, prefix="/api/v1")
app.include_router(diagnostic_router, prefix="/api/v1")
app.include_router(history_router, prefix="/api/v1")
app.include_router(events_router, prefix="/api/v1")
app.include_router(roadmap_router, prefix="/api/v1")
app.include_router(tools_router, prefix="/api/v1")
app.include_router(daemon_router, prefix="/api/v1")
app.include_router(competitor_router, prefix="/api/v1")
app.include_router(opportunity_router, prefix="/api/v1")
app.include_router(watch_targets_router, prefix="/api/v1")
app.include_router(integrations_router, prefix="/api/v1")
app.include_router(cbm_router, prefix="/api/v1")
app.include_router(pitch_router, prefix="/api/v1")
app.include_router(persona_router, prefix="/api/v1")
app.include_router(scenario_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api")  # → /api/admin/*


# Re-export so callers can ``from .main import push_event`` while the registry
# lives in the import-cycle-free sse module.
push_event = sse.push_event


@app.post("/api/v1/sse/push/{project_id}")
async def push_sse_event(project_id: str, body: dict):
    """Internal endpoint: axis services POST here to broadcast an SSE alert."""
    await sse.push_event(project_id, body.get("event", "alert"), body.get("payload", {}))
    return {"pushed": True}


@app.get("/api/v1/project/{project_id}/events/stream")
async def project_events(project_id: str):
    """Server-Sent Events stream of live project events.

    NOTE: distinct path from the REST list endpoint
    (``GET /project/{id}/events`` in events_router) to avoid a route collision
    that previously shadowed this stream — they share the ``/events`` prefix.

    Emits ``score_update``, ``alert``, ``roadmap_update``, ``review_ready`` and
    ``maturity_update`` frames as ``data: {json}\\n\\n``.
    """
    return StreamingResponse(sse.event_stream(project_id), media_type="text/event-stream")


class ChatRequest(BaseModel):
    project_id: str
    message: str
    lang: str = "fr"


async def _load_diagnostic_context(project_id: str) -> dict:
    """Load the latest diagnostic snapshot + current scores for a project."""
    pool = await get_pool()
    diag = await pool.fetchrow(
        """
        SELECT maturity_stage, self_assessed, perception_gap, confidence,
               evidence, blockers, anomalies
          FROM diagnostic_history
         WHERE project_id = $1::uuid
         ORDER BY created_at DESC
         LIMIT 1
        """,
        project_id,
    )
    scores = await pool.fetch(
        """
        SELECT DISTINCT ON (score_name) score_name, score, breakdown
          FROM score_snapshots
         WHERE project_id = $1::uuid
         ORDER BY score_name, created_at DESC
        """,
        project_id,
    )
    return {
        "diagnostic": dict(diag) if diag else {},
        "scores": {r["score_name"]: r["score"] for r in scores},
    }


@app.post("/api/v1/chat")
async def chat(req: ChatRequest):
    """Grounded chat: answer from diagnostic results + detect update intent.

    If the message is asserting a change ("I hired a CTO"), run interpret_chat_update(),
    log an event, and include the scope in the response for frontend review.
    """
    from .generation.runner import load_upstream
    from .updates.pipeline import apply_update, interpret_chat_update

    detected_lang = detect_language(req.message)
    context = await _load_diagnostic_context(req.project_id)

    # 1. Try intent detection (non-blocking; degrade gracefully).
    pool = await get_pool()
    plan_sections = await load_upstream(pool, req.project_id)
    intent = await interpret_chat_update(
        OLLAMA_BASE_URL, OLLAMA_CHAT_MODEL,
        req.message, plan_sections, req.lang,
    )

    event_id: str | None = None
    proposed_scope: list[str] = []

    if intent.get("is_update") and intent.get("changed_axes"):
        event_id, downstream = await apply_update(
            pool, req.project_id,
            changed_axes=intent["changed_axes"],
            section_patches=intent.get("section_patches") or {},
            summary=intent.get("summary") or req.message[:200],
            source="chat",
            severity="info",
            suggestion={
                "action": "rerun_axes",
                "axes": downstream,
                "description": intent.get("summary", ""),
            },
            auto_persist=False,
        )
        proposed_scope = intent.get("suggested_extra_axes", [])

    # 2. Generate contextual reply grounded in diagnostic results.
    system_prompt = (
        "You are Moufida, an AI assistant for Tunisian entrepreneurs. "
        "Answer ONLY based on the following diagnostic results and scores. "
        "Do not give generic advice. "
        f"Respond in {req.lang}.\n\n"
        f"Diagnostic results:\n{json.dumps(context, ensure_ascii=False, default=str)}"
    )

    reply = ""
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": OLLAMA_CHAT_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": req.message},
                    ],
                    "stream": False,
                },
            )
            resp.raise_for_status()
            reply = resp.json().get("message", {}).get("content", "").strip()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"LLM backend error: {exc}")

    return {
        "reply": reply,
        "detected_lang": detected_lang,
        "event_id": event_id,
        "proposed_scope": proposed_scope,
        "is_update": bool(intent.get("is_update")),
    }


@app.get("/health")
def health():
    return {"status": "ok", "service": "orchestrator"}


@app.get("/topology")
def topology():
    """The axis map the diagnostic pass and Redis consumer rely on."""
    return {
        "axes": AXES,
        "diagnostic_order": diagnostic_order(),
    }


@app.get("/state/{project_id}")
def get_state(project_id: str):
    """Returns STATE_NEW / STATE_EXISTING for a project (Phase 2)."""
    return {"project_id": project_id, "state": "unknown", "status": "not_implemented"}
