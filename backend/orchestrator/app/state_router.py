"""State router: project lifecycle (STATE_NEW vs STATE_EXISTING) backed by
PostgreSQL via asyncpg.

The ``profiles`` table stores ``state`` as ``'NEW'`` / ``'EXISTING'`` (the DB
CHECK constraint), while the conversation graph speaks in ``MoufidaState.mode``
of ``'STATE_NEW'`` / ``'STATE_EXISTING'``. The two helpers below map between
them so neither side leaks the other's vocabulary.
"""
from __future__ import annotations

import json
import os
from typing import Optional

import asyncpg
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .graph.state import MoufidaState

router = APIRouter()

DATABASE_URL = os.environ["DATABASE_URL"]

# DB state column  <->  MoufidaState.mode
_DB_TO_MODE = {"NEW": "STATE_NEW", "EXISTING": "STATE_EXISTING"}
# DB language column -> MoufidaState.active_lang
_LANG_TO_ACTIVE = {"fr": "fr", "ar": "ar-TN"}

_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    """Lazily create and cache the asyncpg connection pool."""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)
    return _pool


async def close_pool() -> None:
    """Dispose the pool on application shutdown."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


class NewProjectRequest(BaseModel):
    name: Optional[str] = None
    sector: str = "cross-sector"
    language: str = "fr"
    profile: dict = {}


class ProfilePatchRequest(BaseModel):
    """Intake completion patch: a nested StartupProfile fragment to deep-merge."""
    patch: dict = {}


def _deep_merge(base: dict, patch: dict) -> dict:
    """Recursively merge ``patch`` into ``base`` (mutates and returns ``base``).

    Nested dicts are merged key-by-key; every other value (scalars, lists)
    overwrites. Used to fold an intake ``profile_patch`` into the stored profile
    without clobbering sibling branches.
    """
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def _row_to_state(row: asyncpg.Record) -> MoufidaState:
    """Build a fresh MoufidaState snapshot from a profiles row."""
    profile = row["profile"]
    if isinstance(profile, str):  # asyncpg returns JSONB as str unless a codec is set
        profile = json.loads(profile or "{}")

    return MoufidaState(
        project_id=str(row["id"]),
        mode=_DB_TO_MODE.get(row["state"], "STATE_NEW"),
        profile=profile or {},
        conversation_history=[],
        active_lang=_LANG_TO_ACTIVE.get(row["language"], "other"),
        intake_answers={},
        current_wave=0,
        axis_outputs={},
        maturity_stage=None,
        self_assessed_stage=(profile or {}).get("self_assessed_stage"),
        perception_gap=None,
        blockers=[],
        anomalies=[],
        scores={},
        score_breakdowns={},
        roadmap=None,
        sse_queue=[],
    )


@router.post("/project/new")
async def create_project(req: NewProjectRequest | None = None):
    """Create a new profile row (STATE_NEW) and return its id."""
    req = req or NewProjectRequest()
    pool = await get_pool()
    project_id = await pool.fetchval(
        """
        INSERT INTO profiles (name, state, sector, language, profile)
        VALUES ($1, 'NEW', $2, $3, $4::jsonb)
        RETURNING id
        """,
        req.name,
        req.sector,
        req.language,
        json.dumps(req.profile),
    )
    return {"project_id": str(project_id), "mode": "STATE_NEW"}


@router.get("/projects")
async def list_projects(limit: int = 20):
    """List recent projects (most-recently-updated first).

    Returns ``mode`` (creation|diagnosis) derived from ``state``,
    ``plan_complete`` for creation-mode projects, and the latest
    maturity stage from diagnostic_history when one exists.
    """
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT p.id, p.name, p.sector, p.state, p.plan_complete, p.created_at,
               dh.maturity_stage
          FROM profiles p
          LEFT JOIN LATERAL (
              SELECT maturity_stage
                FROM diagnostic_history
               WHERE project_id = p.id
               ORDER BY created_at DESC
               LIMIT 1
          ) dh ON TRUE
         WHERE p.archived = false
         ORDER BY p.updated_at DESC
         LIMIT $1
        """,
        limit,
    )
    return {
        "projects": [
            {
                "project_id":    str(r["id"]),
                "name":          r["name"],
                "sector":        r["sector"],
                "state":         r["state"],
                "mode":          "creation" if r["state"] == "NEW" else "diagnosis",
                "plan_complete": bool(r["plan_complete"]),
                "maturity_stage": r["maturity_stage"],
                "created_at":    r["created_at"].isoformat(),
            }
            for r in rows
        ]
    }


@router.delete("/project/{project_id}")
async def delete_project(project_id: str):
    """Archive a project (soft-delete via plan_complete flag).

    Uses CASCADE: plan_sections, events, diagnostic_history, score_snapshots,
    roadmap_versions are all ON DELETE CASCADE in the FK definitions.
    Hard-delete is intentional — the user confirmed in the UI.
    """
    pool = await get_pool()
    try:
        deleted = await pool.fetchval(
            "DELETE FROM profiles WHERE id = $1::uuid RETURNING id",
            project_id,
        )
    except (asyncpg.DataError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"invalid project_id: {exc}")
    if deleted is None:
        raise HTTPException(status_code=404, detail="project not found")
    return {"project_id": project_id, "deleted": True}


@router.patch("/project/{project_id}/profile")
async def patch_profile(project_id: str, req: ProfilePatchRequest):
    """Deep-merge an intake ``profile_patch`` into the stored StartupProfile.

    Keeps the ``sector`` column in sync with the JSONB profile so the projects
    list and the diagnostic pass agree on the declared sector.
    """
    pool = await get_pool()
    try:
        row = await pool.fetchrow(
            "SELECT profile FROM profiles WHERE id = $1::uuid", project_id
        )
    except (asyncpg.DataError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"invalid project_id: {exc}")
    if row is None:
        raise HTTPException(status_code=404, detail="project not found")

    profile = row["profile"]
    if isinstance(profile, str):
        profile = json.loads(profile or "{}")
    merged = _deep_merge(profile or {}, req.patch or {})

    sector = merged.get("sector")
    await pool.execute(
        """
        UPDATE profiles
           SET profile = $2::jsonb,
               sector = COALESCE($3, sector),
               updated_at = now()
         WHERE id = $1::uuid
        """,
        project_id,
        json.dumps(merged),
        sector if isinstance(sector, str) else None,
    )

    # Phase F5: if the daemon is watching this project, re-derive its adaptive
    # watch targets in the background (profile_hash caching makes this a no-op
    # when nothing relevant changed). Best-effort; never blocks the patch.
    await _maybe_refresh_watch_targets(pool, project_id)

    return {"project_id": project_id, "profile": merged}


async def _maybe_refresh_watch_targets(pool: asyncpg.Pool, project_id: str) -> None:
    try:
        focused = await pool.fetchval(
            "SELECT focus_project_id FROM daemon_control WHERE id = TRUE"
        )
    except Exception:
        return
    if focused is None or str(focused) != project_id:
        return
    import asyncio
    from .watch_targets_router import refresh_watch_targets  # lazy: avoid cycle
    asyncio.create_task(_safe_refresh(refresh_watch_targets, project_id))


async def _safe_refresh(refresh_fn, project_id: str) -> None:
    try:
        await refresh_fn(project_id)
    except Exception:
        pass


@router.post("/project/{project_id}/diagnose")
async def start_diagnose(project_id: str):
    """Flip a project into STATE_EXISTING so the diagnostic pass can run."""
    pool = await get_pool()
    try:
        updated = await pool.fetchval(
            """
            UPDATE profiles
               SET state = 'EXISTING', updated_at = now()
             WHERE id = $1::uuid
            RETURNING id
            """,
            project_id,
        )
    except (asyncpg.DataError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"invalid project_id: {exc}")
    if updated is None:
        raise HTTPException(status_code=404, detail="project not found")
    return {"project_id": str(updated), "mode": "STATE_EXISTING"}


@router.get("/project/{project_id}")
async def get_project(project_id: str):
    """Load a profile and return the current MoufidaState snapshot."""
    pool = await get_pool()
    try:
        row = await pool.fetchrow(
            "SELECT id, state, sector, language, profile FROM profiles WHERE id = $1::uuid",
            project_id,
        )
    except (asyncpg.DataError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"invalid project_id: {exc}")
    if row is None:
        raise HTTPException(status_code=404, detail="project not found")
    return _row_to_state(row)
