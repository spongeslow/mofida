"""Events router — event feed, act/manual/ignore, manual section edits, what's new.

Endpoints:
  GET  /project/{id}/events                → filterable event feed
  POST /project/{id}/section/{axis}        → manual edit (Source A)
  POST /event/{id}/act                     → auto-apply event suggestion
  POST /event/{id}/manual                  → mark manual (user will edit)
  POST /event/{id}/ignore                  → mark ignored
  GET  /event/{id}/diff                    → before/after content diff
  GET  /project/{id}/whats-new            → LLM summary of recent events
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any

import asyncpg
import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from . import sse
from .generation.runner import persist_section, run_generation_step
from .state_router import get_pool
from .updates.pipeline import apply_update

router = APIRouter()
logger = logging.getLogger("moufida.events_router")

_OLLAMA_BASE  = os.environ.get("OLLAMA_BASE_URL",  "http://ollama:11434")
_OLLAMA_MODEL = os.environ.get("OLLAMA_CHAT_MODEL", os.environ.get("OLLAMA_MODEL", "llama3.1:8b"))


def _parse_jsonb(val: Any) -> Any:
    if isinstance(val, str):
        try:
            return json.loads(val)
        except Exception:
            return {}
    return val or {}


# ---------------------------------------------------------------------------
# GET /project/{id}/events — filterable event feed
# ---------------------------------------------------------------------------

@router.get("/project/{project_id}/events")
async def list_events(
    project_id: str,
    source:   str | None = Query(None),
    axis:     str | None = Query(None),
    severity: str | None = Query(None),
    status:   str | None = Query(None),
    limit:    int = Query(50, le=200),
):
    pool = await get_pool()
    try:
        rows = await pool.fetch(
            """
            SELECT id, source, type, severity, summary, detail,
                   axes_affected, diff, suggestion, status, created_at
              FROM events
             WHERE project_id = $1::uuid
               AND ($2::text IS NULL OR source = $2)
               AND ($3::text IS NULL OR $3 = ANY(axes_affected))
               AND ($4::text IS NULL OR severity = $4)
               AND ($5::text IS NULL OR status = $5)
             ORDER BY created_at DESC
             LIMIT $6
            """,
            project_id, source, axis, severity, status, limit,
        )
    except (asyncpg.DataError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {
        "events": [
            {
                "id":           str(r["id"]),
                "source":       r["source"],
                "type":         r["type"],
                "severity":     r["severity"],
                "summary":      r["summary"],
                "detail":       r["detail"],
                "axes_affected": r["axes_affected"] or [],
                "diff":         _parse_jsonb(r["diff"]),
                "suggestion":   _parse_jsonb(r["suggestion"]),
                "status":       r["status"],
                "created_at":   r["created_at"].isoformat(),
            }
            for r in rows
        ]
    }


# ---------------------------------------------------------------------------
# POST /project/{id}/section/{axis} — Source A: manual edit
# ---------------------------------------------------------------------------

class SectionEditBody(BaseModel):
    content: dict = {}
    summary: str | None = None


@router.post("/project/{project_id}/section/{axis}")
async def manual_section_edit(project_id: str, axis: str, body: SectionEditBody):
    """User edits a plan section in PlanDocument → persist + pipeline."""
    pool = await get_pool()

    # Load the old content for diff.
    old_row = await pool.fetchrow(
        """
        SELECT content FROM plan_sections
         WHERE project_id = $1::uuid AND axis_slug = $2 AND superseded = false
        """,
        project_id, axis,
    )
    old_content = _parse_jsonb(old_row["content"]) if old_row else {}

    version = await persist_section(
        pool, project_id, axis, body.content, body.summary, source="manual"
    )

    diff = {"axis": axis, "before": old_content, "after": body.content}

    event_id, downstream = await apply_update(
        pool, project_id,
        changed_axes=[axis],
        summary=f"Section {axis} mise à jour manuellement",
        source="manual",
        severity="info",
        suggestion={
            "action": "rerun_axes",
            "axes": downstream,
            "description": f"Les axes dépendants de {axis} peuvent nécessiter une mise à jour",
        },
        diff=diff,
        auto_persist=False,
    )

    return {
        "project_id": project_id,
        "axis": axis,
        "version": version,
        "event_id": event_id,
        "downstream_axes": downstream,
    }


# ---------------------------------------------------------------------------
# Act / Manual / Ignore
# ---------------------------------------------------------------------------

@router.post("/event/{event_id}/act")
async def act_on_event(event_id: str):
    """Auto-apply the event's suggestion (re-run affected axes as proposals)."""
    pool = await get_pool()
    try:
        row = await pool.fetchrow(
            "SELECT id, project_id, suggestion, axes_affected, status FROM events WHERE id = $1::uuid",
            event_id,
        )
    except (asyncpg.DataError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if row is None:
        raise HTTPException(status_code=404, detail="event not found")
    if row["status"] != "new":
        raise HTTPException(status_code=409, detail=f"event already {row['status']}")

    project_id = str(row["project_id"])
    suggestion = _parse_jsonb(row["suggestion"])
    axes_to_run = suggestion.get("axes", row["axes_affected"] or [])

    # Generate proposals for affected axes (non-blocking — stored as plan_sections proposals).
    proposals = []
    for axis in axes_to_run:
        try:
            proposal = await run_generation_step(pool, project_id, axis, constraints=None, mode="generate")
            proposals.append({"axis": axis, "proposal": proposal})
        except Exception as exc:
            logger.warning("act rerun failed axis=%s: %s", axis, exc)

    # Mark event as acted.
    await pool.execute(
        "UPDATE events SET status = 'acted' WHERE id = $1::uuid",
        event_id,
    )

    await sse.push_event(project_id, "event_acted", {
        "event_id": event_id,
        "axes_run": axes_to_run,
        "proposals": [p["axis"] for p in proposals],
    })

    return {"event_id": event_id, "status": "acted", "proposals": proposals}


@router.post("/event/{event_id}/manual")
async def manual_event(event_id: str):
    """Mark event as 'manual' — user will handle it themselves."""
    pool = await get_pool()
    row = await pool.fetchrow(
        "UPDATE events SET status = 'manual' WHERE id = $1::uuid RETURNING project_id, axes_affected",
        event_id,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="event not found")
    await sse.push_event(str(row["project_id"]), "event_manual", {"event_id": event_id})
    return {"event_id": event_id, "status": "manual", "axes": row["axes_affected"]}


@router.post("/event/{event_id}/ignore")
async def ignore_event(event_id: str):
    """Mark event as 'ignored' — revisitable from the feed."""
    pool = await get_pool()
    row = await pool.fetchrow(
        "UPDATE events SET status = 'ignored' WHERE id = $1::uuid RETURNING project_id",
        event_id,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="event not found")
    await sse.push_event(str(row["project_id"]), "event_ignored", {"event_id": event_id})
    return {"event_id": event_id, "status": "ignored"}


# ---------------------------------------------------------------------------
# GET /event/{id}/diff — before/after field-level diff
# ---------------------------------------------------------------------------

@router.get("/event/{event_id}/diff")
async def event_diff(event_id: str):
    pool = await get_pool()
    try:
        row = await pool.fetchrow(
            "SELECT diff, axes_affected, summary FROM events WHERE id = $1::uuid",
            event_id,
        )
    except (asyncpg.DataError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if row is None:
        raise HTTPException(status_code=404, detail="event not found")

    return {
        "event_id":     event_id,
        "axes_affected": row["axes_affected"] or [],
        "summary":      row["summary"],
        "diff":         _parse_jsonb(row["diff"]),
    }


# ---------------------------------------------------------------------------
# GET /project/{id}/whats-new — LLM summary of recent events
# ---------------------------------------------------------------------------

@router.get("/project/{project_id}/whats-new")
async def whats_new(project_id: str, since: str | None = None, language: str = "fr"):
    """Summarise recent events ranked by severity for voice/chat 'what changed?' queries."""
    pool = await get_pool()

    since_dt: datetime | None = None
    if since:
        try:
            since_dt = datetime.fromisoformat(since)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"invalid 'since' timestamp: {exc}")

    try:
        rows = await pool.fetch(
            """
            SELECT id, source, severity, summary, axes_affected, created_at
              FROM events
             WHERE project_id = $1::uuid
               AND ($2::timestamptz IS NULL OR created_at > $2::timestamptz)
               AND status != 'ignored'
             ORDER BY
               CASE severity WHEN 'critical' THEN 0 WHEN 'warning' THEN 1 ELSE 2 END,
               created_at DESC
             LIMIT 10
            """,
            project_id,
            since_dt,
        )
    except (asyncpg.DataError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if not rows:
        return {"summary": None, "events": []}

    bullets = "\n".join(
        f"- [{r['severity'].upper()}] {r['summary']} ({', '.join(r['axes_affected'] or [])})"
        for r in rows
    )

    prompt = (
        f"Summarise the following startup project updates for the founder in 2–3 sentences. "
        f"Be concise, prioritise critical items first. Language: {language}.\n\n{bullets}"
    )
    summary_text = bullets  # fallback
    try:
        async with httpx.AsyncClient(timeout=60.0) as http:
            resp = await http.post(
                f"{_OLLAMA_BASE}/api/generate",
                json={"model": _OLLAMA_MODEL, "prompt": prompt, "stream": False},
            )
            resp.raise_for_status()
            summary_text = resp.json().get("response", "").strip() or bullets
    except Exception as exc:
        logger.warning("whats-new LLM failed: %s", exc)

    return {
        "summary": summary_text,
        "events": [
            {
                "id":           str(r["id"]),
                "severity":     r["severity"],
                "summary":      r["summary"],
                "axes_affected": r["axes_affected"] or [],
                "created_at":   r["created_at"].isoformat(),
            }
            for r in rows
        ],
    }
