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

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://moufida:moufida@postgres:5432/moufida")

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
