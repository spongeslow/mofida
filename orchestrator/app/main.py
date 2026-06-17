"""Moufida Orchestrator -- FastAPI + LangGraph brain (port 8001).

Phase 0 scaffold: exposes /health and a static description of the axis routing
topology. The state router, adaptive intake, diagnostic runner, LangGraph state
machine and Redis consumer are filled in across Phases 2 and 5.
"""
from __future__ import annotations

import json
import os

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from . import sse
from .axis_registry import AXES, diagnostic_order
from .diagnostic_router import router as diagnostic_router
from .intake_router import router as intake_router
from .lang_detect import detect_language
from .state_router import close_pool, get_pool, router as state_router

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "mistral")

app = FastAPI(title="Moufida Orchestrator")
app.include_router(state_router, prefix="/api/v1")
app.include_router(intake_router, prefix="/api/v1")
app.include_router(diagnostic_router, prefix="/api/v1")


# Re-export so callers can ``from .main import push_event`` while the registry
# lives in the import-cycle-free sse module.
push_event = sse.push_event


@app.get("/api/v1/project/{project_id}/events")
async def project_events(project_id: str):
    """Server-Sent Events stream of live project events.

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
    """Grounded chat: answer strictly from the project's diagnostic results."""
    detected_lang = detect_language(req.message)
    context = await _load_diagnostic_context(req.project_id)

    system_prompt = (
        "You are Moufida, an AI assistant for Tunisian entrepreneurs. "
        "Answer ONLY based on the following diagnostic results and scores. "
        "Do not give generic advice. "
        f"Respond in {req.lang}.\n\n"
        f"Diagnostic results:\n{json.dumps(context, ensure_ascii=False, default=str)}"
    )

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

    return {"reply": reply, "detected_lang": detected_lang}


@app.on_event("shutdown")
async def _shutdown():
    await close_pool()


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
