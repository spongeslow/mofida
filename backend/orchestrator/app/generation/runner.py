"""Generation runner — creation mode fan-out.

Mirrors diagnostic/runner.py but calls each axis's POST /generate endpoint
instead of /diagnose. Does NOT persist — the caller (creation_router) persists
only on Approve.

Public API
----------
run_generation_step(pool, project_id, axis_slug, *, constraints, mode) -> dict
    Call one axis /generate. Returns the raw proposal (content, summary, …).

persist_section(pool, project_id, axis_slug, content, summary, source) -> int
    Supersede the current live row and insert a new version. Returns version number.

load_upstream(pool, project_id) -> dict[str, dict]
    Load all currently-approved plan sections for a project (for the upstream
    context fed to each axis's /generate call).
"""
from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from ..axis_registry import axis_host, GENERATION_ORDER
from ..state_router import get_pool
from .evidence import fetch_evidence

logger = logging.getLogger("moufida.generation.runner")

_TIMEOUT = 360.0


# ---------------------------------------------------------------------------
# Upstream loader
# ---------------------------------------------------------------------------

async def load_upstream(pool, project_id: str) -> dict[str, Any]:
    """Return {axis_slug: content} for all approved live sections."""
    rows = await pool.fetch(
        """
        SELECT axis_slug, content
          FROM plan_sections
         WHERE project_id = $1
           AND superseded = false
           AND approved = true
        """,
        project_id,
    )
    result: dict[str, Any] = {}
    for row in rows:
        content = row["content"]
        if isinstance(content, str):
            content = json.loads(content)
        result[row["axis_slug"]] = content
    return result


# ---------------------------------------------------------------------------
# Single-axis generation call
# ---------------------------------------------------------------------------

async def run_generation_step(
    pool,
    project_id: str,
    axis_slug: str,
    *,
    constraints: str | None = None,
    mode: str = "generate",
) -> dict[str, Any]:
    """Call one axis /generate and return the proposal. Never persists."""
    # Load project profile + approved upstream sections.
    row = await pool.fetchrow(
        "SELECT profile, language FROM profiles WHERE id = $1",
        project_id,
    )
    if row is None:
        return {"axis": axis_slug, "error": "project not found"}

    profile = row["profile"]
    if isinstance(profile, str):
        profile = json.loads(profile or "{}")
    language = row["language"] or "fr"

    upstream = await load_upstream(pool, project_id)

    # Extract raw idea from the profile (stored under raw_idea key by creation flow).
    idea = str(profile.get("raw_idea", ""))

    # Ground the axis prompt in curated KB + fresh web evidence (best-effort).
    evidence = await fetch_evidence(axis_slug, idea, profile, language)

    body: dict[str, Any] = {
        "language":    language,
        "idea":        idea,
        "profile":     profile,
        "upstream":    upstream,
        "constraints": constraints,
        "mode":        mode,
        "evidence":    evidence,
    }

    url = f"{axis_host(axis_slug)}/generate"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(url, json=body)
            resp.raise_for_status()
            proposal = resp.json()
            # Fold citations into content under a reserved key so they survive
            # the edit→approve→persist round-trip (the frontend echoes content
            # back on approve). Known-axis renderers ignore underscore keys.
            citations = proposal.get("citations") or []
            if isinstance(proposal.get("content"), dict):
                proposal["content"]["_citations"] = citations
            return proposal
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("generate step failed axis=%s: %s", axis_slug, exc)
        return {"axis": axis_slug, "error": str(exc), "content": {}, "summary": ""}


# ---------------------------------------------------------------------------
# Persist (Approve action)
# ---------------------------------------------------------------------------

async def persist_section(
    pool,
    project_id: str,
    axis_slug: str,
    content: dict,
    summary: str | None = None,
    source: str = "generate",
) -> int:
    """Supersede any existing live row and insert a new approved version.

    Returns the new version number.
    Write rule: only one row per (project_id, axis_slug) may have superseded=false
    (enforced by the unique index in 007_plan_sections.sql).
    """
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Flip current live row (if any) to superseded.
            await conn.execute(
                """
                UPDATE plan_sections
                   SET superseded = true
                 WHERE project_id = $1
                   AND axis_slug  = $2
                   AND superseded = false
                """,
                project_id,
                axis_slug,
            )
            # Determine next version number.
            max_ver = await conn.fetchval(
                """
                SELECT COALESCE(MAX(version), 0)
                  FROM plan_sections
                 WHERE project_id = $1 AND axis_slug = $2
                """,
                project_id,
                axis_slug,
            )
            version = max_ver + 1
            content_json = json.dumps(content)
            await conn.execute(
                """
                INSERT INTO plan_sections
                    (project_id, axis_slug, version, content, summary, approved, superseded, source)
                VALUES ($1, $2, $3, $4::jsonb, $5, true, false, $6)
                """,
                project_id,
                axis_slug,
                version,
                content_json,
                summary,
                source,
            )
    return version
