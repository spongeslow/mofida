"""Roadmap engine router — adaptive, progress-aware, versioned roadmap.

Endpoints:
  POST /project/{id}/roadmap/regenerate   → on-demand regen (records kb_version)
  POST /project/{id}/roadmap/advance      → next-horizon actions on full completion
  POST /project/{id}/kb                   → manual KB addition (bumps kb_version)
  GET  /project/{id}/roadmap/provenance   → KB sources/version for the live roadmap
"""
from __future__ import annotations

import json
import logging

import asyncpg
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from . import axis_registry, sse
from .generation.runner import load_upstream
from .state_router import get_pool

router = APIRouter()
logger = logging.getLogger("moufida.roadmap_router")


async def _call_gtm_roadmap(
    project_id: str,
    profile: dict,
    language: str,
    upstream: dict | None = None,
    horizon_context: dict | None = None,
) -> dict | None:
    gtm_host = axis_registry.axis_host("gtm")
    try:
        payload = {
            "project_id": project_id,
            "stage":      "ideation",
            "sector":     str(profile.get("sector", "cross-sector")),
            "language":   language,
            "blockers":   [],
            "scores":     {},
            "profile":    {**profile, **({"plan_sections": upstream} if upstream else {})},
        }
        if horizon_context:
            payload["horizon_context"] = horizon_context
        async with httpx.AsyncClient(timeout=180.0) as http:
            resp = await http.post(f"{gtm_host}/roadmap", json=payload)
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("roadmap call failed project=%s: %s", project_id, exc)
        return None


async def _persist_roadmap(pool, project_id: str, roadmap: dict, trigger: str, kb_version: int | None = None) -> int:
    """Insert a new roadmap_versions row. Returns version number."""
    async with pool.acquire() as conn:
        version = await conn.fetchval(
            "SELECT COALESCE(MAX(version), 0) + 1 FROM roadmap_versions WHERE project_id = $1::uuid",
            project_id,
        )
        await conn.execute(
            """
            INSERT INTO roadmap_versions (project_id, version, roadmap, trigger, kb_version)
            VALUES ($1::uuid, $2, $3::jsonb, $4, $5)
            """,
            project_id, version, json.dumps(roadmap), trigger, kb_version,
        )
        # Clear stale flag on previous versions.
        await conn.execute(
            "UPDATE roadmap_versions SET stale = false WHERE project_id = $1::uuid AND version < $2",
            project_id, version,
        )
    return version


# ---------------------------------------------------------------------------
# POST /project/{id}/roadmap/regenerate — on-demand regen
# ---------------------------------------------------------------------------

@router.post("/project/{project_id}/roadmap/regenerate")
async def regenerate_roadmap(project_id: str):
    pool = await get_pool()
    try:
        row = await pool.fetchrow(
            "SELECT id, profile, language FROM profiles WHERE id = $1::uuid", project_id
        )
    except (asyncpg.DataError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"invalid project_id: {exc}")
    if row is None:
        raise HTTPException(status_code=404, detail="project not found")

    profile = row["profile"]
    if isinstance(profile, str):
        profile = json.loads(profile or "{}")
    language = row["language"] or "fr"

    upstream = await load_upstream(pool, project_id)

    # Current KB version.
    kb_version = await pool.fetchval(
        "SELECT COALESCE(MAX(kb_version), 0) FROM knowledge_base WHERE project_id IS NULL OR project_id = $1::uuid",
        project_id,
    )

    roadmap = await _call_gtm_roadmap(project_id, profile, language, upstream)
    if roadmap is None:
        raise HTTPException(status_code=502, detail="roadmap generation failed")

    version = await _persist_roadmap(pool, project_id, roadmap, "manual", kb_version)

    await sse.push_event(project_id, "roadmap_update", {
        "version": version,
        "trigger": "manual",
        "kb_version": kb_version,
    })

    return {"project_id": project_id, "version": version, "roadmap": roadmap}


# ---------------------------------------------------------------------------
# POST /project/{id}/roadmap/advance — next-horizon on full completion
# ---------------------------------------------------------------------------

class AdvanceBody(BaseModel):
    horizon: str  # "immediate" | "short_term" | "medium_term"
    completed_actions: list[str] = []  # action texts from the just-completed horizon


@router.post("/project/{project_id}/roadmap/advance")
async def advance_roadmap(project_id: str, body: AdvanceBody):
    """Generate next-horizon actions when a horizon is fully completed."""
    pool = await get_pool()
    try:
        row = await pool.fetchrow(
            "SELECT id, profile, language FROM profiles WHERE id = $1::uuid", project_id
        )
    except (asyncpg.DataError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"invalid project_id: {exc}")
    if row is None:
        raise HTTPException(status_code=404, detail="project not found")

    profile = row["profile"]
    if isinstance(profile, str):
        profile = json.loads(profile or "{}")
    language = row["language"] or "fr"

    upstream = await load_upstream(pool, project_id)

    next_horizon_map = {
        "immediate": "short_term",
        "short_term": "medium_term",
        "medium_term": None,
    }
    next_horizon = next_horizon_map.get(body.horizon)

    horizon_context = {
        "completed_horizon": body.horizon,
        "completed_actions": body.completed_actions,
        "generate_next_horizon": next_horizon,
    }

    roadmap = await _call_gtm_roadmap(project_id, profile, language, upstream, horizon_context)
    if roadmap is None:
        raise HTTPException(status_code=502, detail="roadmap advance failed")

    version = await _persist_roadmap(pool, project_id, roadmap, "completion")

    # Companion celebration event.
    await sse.push_event(project_id, "horizon_complete", {
        "completed_horizon": body.horizon,
        "next_horizon": next_horizon,
        "version": version,
    })

    return {
        "project_id": project_id,
        "completed_horizon": body.horizon,
        "next_horizon": next_horizon,
        "version": version,
        "roadmap": roadmap,
    }


# ---------------------------------------------------------------------------
# POST /project/{id}/kb — manual KB addition
# ---------------------------------------------------------------------------

class KbAddBody(BaseModel):
    content: str
    title: str | None = None


@router.post("/project/{project_id}/kb")
async def add_kb_entry(project_id: str, body: KbAddBody):
    """Add a manual note/link to the project knowledge base. Bumps kb_version."""
    pool = await get_pool()
    try:
        kb_version = await pool.fetchval(
            """
            SELECT COALESCE(MAX(kb_version), 0) + 1
              FROM knowledge_base
             WHERE project_id IS NULL OR project_id = $1::uuid
            """,
            project_id,
        )
        kb_id = await pool.fetchval(
            """
            INSERT INTO knowledge_base (project_id, source, content, kb_version)
            VALUES ($1::uuid, $2, $3, $4)
            RETURNING id
            """,
            project_id,
            f"manual:{body.title or 'note'}",
            body.content,
            kb_version,
        )
        # Mark the live roadmap stale so user sees the "regenerate?" prompt.
        await pool.execute(
            """
            UPDATE roadmap_versions SET stale = true
             WHERE project_id = $1::uuid
               AND version = (SELECT MAX(version) FROM roadmap_versions WHERE project_id = $1::uuid)
            """,
            project_id,
        )
    except (asyncpg.DataError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    await sse.push_event(project_id, "kb_updated", {
        "kb_version": kb_version,
        "source": "manual",
    })

    return {"kb_id": str(kb_id), "kb_version": kb_version}


# ---------------------------------------------------------------------------
# GET /project/{id}/roadmap/provenance — KB sources behind live roadmap
# ---------------------------------------------------------------------------

@router.get("/project/{project_id}/roadmap/provenance")
async def roadmap_provenance(project_id: str):
    """Return KB sources + version used to generate the current live roadmap."""
    pool = await get_pool()

    rm_row = await pool.fetchrow(
        """
        SELECT version, kb_version, trigger, created_at, stale
          FROM roadmap_versions
         WHERE project_id = $1::uuid
         ORDER BY version DESC
         LIMIT 1
        """,
        project_id,
    )
    if rm_row is None:
        return {"roadmap_version": None, "kb_version": None, "sources": [], "stale": False}

    kb_version = rm_row["kb_version"]
    sources: list[dict] = []
    if kb_version:
        rows = await pool.fetch(
            """
            SELECT source, created_at
              FROM knowledge_base
             WHERE (project_id IS NULL OR project_id = $1::uuid)
               AND kb_version <= $2
             ORDER BY created_at DESC
             LIMIT 20
            """,
            project_id, kb_version,
        )
        sources = [{"source": r["source"], "created_at": r["created_at"].isoformat()} for r in rows]

    return {
        "roadmap_version": rm_row["version"],
        "kb_version":      kb_version,
        "trigger":         rm_row["trigger"],
        "generated_at":    rm_row["created_at"].isoformat(),
        "stale":           bool(rm_row["stale"]),
        "sources":         sources,
    }
