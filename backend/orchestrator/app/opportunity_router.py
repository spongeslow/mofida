"""Grant / deadline radar — match Tunisian funding calls to the project.

The Go ``grant`` watcher POSTs candidate funding calls to
``/project/{id}/opportunity/observe``; this router LLM-scores each candidate
against the project profile, extracts the apply-by date, and persists matches
(``match_score >= 0.5``) the dashboard renders as deadline-sorted cards.
"""
from __future__ import annotations

import json
import logging
from datetime import date

import asyncpg
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from . import sse
from .llm_json import generate_json
from .state_router import get_pool

router = APIRouter()
logger = logging.getLogger("moufida.opportunity_router")

_MATCH_THRESHOLD = 0.5


def _parse_jsonb(val):
    if isinstance(val, str):
        try:
            return json.loads(val)
        except Exception:
            return {}
    return val if val is not None else {}


class ObserveBody(BaseModel):
    title: str
    source: str
    url: str | None = None
    raw_text: str = ""


def _parse_deadline(raw: str | None):
    if not raw:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except (ValueError, TypeError):
        return None


@router.post("/project/{project_id}/opportunity/observe")
async def observe_opportunity(project_id: str, body: ObserveBody):
    """Daemon hook: score a candidate funding call and persist if it fits."""
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT profile, sector FROM profiles WHERE id = $1::uuid", project_id
    )
    if row is None:
        raise HTTPException(status_code=404, detail="project not found")
    profile = _parse_jsonb(row["profile"])
    sector = row["sector"]

    prompt = (
        "You are a startup funding advisor in Tunisia. Assess whether this funding "
        "opportunity fits the startup, and extract its application deadline.\n\n"
        f"STARTUP SECTOR: {sector}\n"
        f"STARTUP PROFILE: {json.dumps(profile, ensure_ascii=False)[:2000]}\n\n"
        f"OPPORTUNITY TITLE: {body.title}\n"
        f"OPPORTUNITY TEXT: {body.raw_text[:3000]}\n\n"
        "Respond ONLY with valid JSON matching exactly:\n"
        '{"match_score": 0.0, "match_reason": "one concise sentence", '
        '"deadline": "YYYY-MM-DD or null"}\n'
        "match_score is 0..1 (1 = perfect fit). Use null deadline when unknown."
    )
    result = await generate_json(prompt, temperature=0.2)

    try:
        match_score = float(result.get("match_score", 0) or 0)
    except (TypeError, ValueError):
        match_score = 0.0
    match_reason = str(result.get("match_reason", "") or "")
    deadline = _parse_deadline(result.get("deadline"))

    if match_score < _MATCH_THRESHOLD:
        return {"persisted": False, "match_score": match_score}

    try:
        opp_id = await pool.fetchval(
            """
            INSERT INTO opportunities
                (project_id, title, source, url, deadline, match_reason, match_score)
            VALUES ($1::uuid, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (project_id, url) DO UPDATE
                SET title = EXCLUDED.title, deadline = EXCLUDED.deadline,
                    match_reason = EXCLUDED.match_reason, match_score = EXCLUDED.match_score
            RETURNING id
            """,
            project_id, body.title, body.source, body.url,
            deadline, match_reason, match_score,
        )
    except (asyncpg.DataError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    await sse.push_event(project_id, "opportunity_new", {
        "title":    body.title,
        "deadline": deadline.isoformat() if deadline else None,
    })
    try:
        from . import telemetry
        await telemetry.record_daemon_activity(
            project_id=project_id, watcher="grant", activity="grant_found",
            detail={"title": body.title, "source": body.source, "match_score": match_score},
        )
    except Exception:  # noqa: BLE001
        pass
    return {"persisted": True, "opportunity_id": str(opp_id), "match_score": match_score}


@router.get("/project/{project_id}/opportunities")
async def list_opportunities(project_id: str):
    """Active (non-dismissed) opportunities, soonest deadline first."""
    pool = await get_pool()
    try:
        rows = await pool.fetch(
            """
            SELECT id, title, source, url, deadline, match_reason, match_score, created_at
              FROM opportunities
             WHERE project_id = $1::uuid AND dismissed = FALSE
             ORDER BY deadline ASC NULLS LAST, match_score DESC
            """,
            project_id,
        )
    except (asyncpg.DataError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {
        "opportunities": [
            {
                "id":           str(r["id"]),
                "title":        r["title"],
                "source":       r["source"],
                "url":          r["url"],
                "deadline":     r["deadline"].isoformat() if r["deadline"] else None,
                "match_reason": r["match_reason"],
                "match_score":  r["match_score"],
                "created_at":   r["created_at"].isoformat(),
            }
            for r in rows
        ]
    }


@router.post("/project/{project_id}/opportunity/{oid}/dismiss")
async def dismiss_opportunity(project_id: str, oid: str):
    """Hide an opportunity card."""
    pool = await get_pool()
    try:
        updated = await pool.fetchval(
            """
            UPDATE opportunities SET dismissed = TRUE
             WHERE id = $1::uuid AND project_id = $2::uuid
            RETURNING id
            """,
            oid, project_id,
        )
    except (asyncpg.DataError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if updated is None:
        raise HTTPException(status_code=404, detail="opportunity not found")
    return {"opportunity_id": oid, "dismissed": True}
