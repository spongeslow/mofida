"""Creation mode router — /project/{id}/generate/… endpoints.

Five endpoints drive the axis-by-axis generation loop:
  POST /project/{id}/generate/{axis}          → proposal (not persisted)
  POST /project/{id}/generate/{axis}/approve  → persist live plan_sections row
  POST /project/{id}/generate/{axis}/retry    → fresh proposal (higher temp)
  GET  /project/{id}/plan                     → all live plan_sections
  POST /project/{id}/finalize                 → roadmap + plan_complete=true
"""
from __future__ import annotations

import json
import logging

import asyncpg
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from . import axis_registry, sse
from .generation.runner import load_upstream, persist_section, run_generation_step
from .state_router import get_pool

router = APIRouter()
logger = logging.getLogger("moufida.creation_router")


class GenerateBody(BaseModel):
    constraints: str | None = None


class ApproveBody(BaseModel):
    content: dict = {}
    summary: str | None = None


@router.post("/project/{project_id}/generate/{axis}")
async def generate_axis(project_id: str, axis: str, body: GenerateBody | None = None):
    """Generate a plan section proposal. Not persisted — caller must approve."""
    if axis not in axis_registry.NETWORK_AXES:
        raise HTTPException(status_code=404, detail=f"unknown axis: {axis}")
    pool = await get_pool()
    constraints = body.constraints if body else None
    proposal = await run_generation_step(
        pool, project_id, axis, constraints=constraints, mode="generate"
    )
    if "error" in proposal and not proposal.get("content"):
        raise HTTPException(status_code=502, detail=proposal["error"])
    await sse.push_event(project_id, "generation_step", {
        "axis": axis, "status": "proposal_ready",
    })
    return proposal


@router.post("/project/{project_id}/generate/{axis}/approve")
async def approve_axis(project_id: str, axis: str, body: ApproveBody | None = None):
    """Persist the approved proposal as a live plan_sections row."""
    if axis not in axis_registry.NETWORK_AXES:
        raise HTTPException(status_code=404, detail=f"unknown axis: {axis}")
    pool = await get_pool()

    if body and body.content:
        content = body.content
        summary = body.summary
    else:
        proposal = await run_generation_step(
            pool, project_id, axis, constraints=None, mode="generate"
        )
        content = proposal.get("content", {})
        summary = proposal.get("summary")

    version = await persist_section(pool, project_id, axis, content, summary, source="generate")
    await sse.push_event(project_id, "generation_step", {
        "axis": axis, "status": "approved", "version": version,
    })
    return {"project_id": project_id, "axis": axis, "version": version}


@router.post("/project/{project_id}/generate/{axis}/retry")
async def retry_axis(project_id: str, axis: str):
    """Generate a fresh proposal with higher temperature (mode=regenerate)."""
    if axis not in axis_registry.NETWORK_AXES:
        raise HTTPException(status_code=404, detail=f"unknown axis: {axis}")
    pool = await get_pool()
    proposal = await run_generation_step(
        pool, project_id, axis, constraints=None, mode="regenerate"
    )
    if "error" in proposal and not proposal.get("content"):
        raise HTTPException(status_code=502, detail=proposal["error"])
    await sse.push_event(project_id, "generation_step", {
        "axis": axis, "status": "retried",
    })
    return proposal


@router.get("/project/{project_id}/plan")
async def get_plan(project_id: str):
    """Return all live (not superseded) plan_sections for a project, ordered by creation."""
    pool = await get_pool()
    try:
        rows = await pool.fetch(
            """
            SELECT axis_slug, version, content, summary, approved, source, created_at
              FROM plan_sections
             WHERE project_id = $1::uuid
               AND superseded = false
             ORDER BY created_at ASC
            """,
            project_id,
        )
    except (asyncpg.DataError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"invalid project_id: {exc}")

    sections = []
    for r in rows:
        content = r["content"]
        if isinstance(content, str):
            content = json.loads(content)
        sections.append({
            "axis_slug":  r["axis_slug"],
            "version":    r["version"],
            "content":    content,
            "summary":    r["summary"],
            "approved":   r["approved"],
            "source":     r["source"],
            "created_at": r["created_at"].isoformat(),
        })
    return {"project_id": project_id, "sections": sections}


@router.post("/project/{project_id}/finalize")
async def finalize_plan(project_id: str):
    """Generate the roadmap from approved sections, mark plan_complete=true."""
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

    # Call GTM roadmap service with plan sections as context.
    gtm_host = axis_registry.axis_host("gtm")
    roadmap_result: dict | None = None
    try:
        async with httpx.AsyncClient(timeout=180.0) as http:
            resp = await http.post(
                f"{gtm_host}/roadmap",
                json={
                    "project_id":   project_id,
                    "stage":        "ideation",
                    "sector":       str(profile.get("sector", "cross-sector")),
                    "language":     language,
                    "blockers":     [],
                    "scores":       {},
                    "profile":      {**profile, "plan_sections": upstream},
                },
            )
            resp.raise_for_status()
            roadmap_result = resp.json()
    except Exception as exc:
        logger.warning("roadmap gen failed project=%s: %s", project_id, exc)

    async with pool.acquire() as conn:
        async with conn.transaction():
            if roadmap_result:
                # Persist as plan_sections[axis='roadmap'].
                await conn.execute(
                    """
                    UPDATE plan_sections SET superseded = true
                     WHERE project_id = $1::uuid
                       AND axis_slug  = 'roadmap'
                       AND superseded = false
                    """,
                    project_id,
                )
                max_ver = await conn.fetchval(
                    """
                    SELECT COALESCE(MAX(version), 0)
                      FROM plan_sections
                     WHERE project_id = $1::uuid AND axis_slug = 'roadmap'
                    """,
                    project_id,
                )
                await conn.execute(
                    """
                    INSERT INTO plan_sections
                        (project_id, axis_slug, version, content, summary, approved, superseded, source)
                    VALUES ($1::uuid, 'roadmap', $2, $3::jsonb, 'Generated roadmap', true, false, 'generate')
                    """,
                    project_id, (max_ver or 0) + 1, json.dumps(roadmap_result),
                )
                # Also persist as roadmap_versions for the dashboard RoadmapTimeline.
                rm_ver = await conn.fetchval(
                    "SELECT COALESCE(MAX(version), 0) + 1 FROM roadmap_versions WHERE project_id = $1::uuid",
                    project_id,
                )
                await conn.execute(
                    """
                    INSERT INTO roadmap_versions (project_id, version, roadmap, trigger)
                    VALUES ($1::uuid, $2, $3::jsonb, 'finalize')
                    """,
                    project_id, rm_ver, json.dumps(roadmap_result),
                )

            # Mark plan complete.
            await conn.execute(
                "UPDATE profiles SET plan_complete = true, updated_at = now() WHERE id = $1::uuid",
                project_id,
            )

    await sse.push_event(project_id, "plan_finalized", {
        "roadmap": roadmap_result is not None,
    })
    return {
        "project_id":   project_id,
        "plan_complete": True,
        "roadmap":       roadmap_result,
    }
