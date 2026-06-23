"""Tools integration router — CRUD for user-configured external tool integrations.

Endpoints:
  GET  /tools              list all registered tools with their current state
  GET  /tools/{slug}       get one tool's state
  PUT  /tools/{slug}       save enabled flag + credentials
  POST /tools/{slug}/test  test connection without persisting
  POST /tools/{slug}/sync  manual sync trigger (push tools re-push latest data)
"""
from __future__ import annotations

import json
import logging
import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .state_router import get_pool

logger = logging.getLogger("moufida.tools_router")

router = APIRouter(prefix="/tools", tags=["tools"])

COMPOSIO_REDIRECT_URL = os.getenv("COMPOSIO_REDIRECT_URL", "https://app.composio.dev/redirect")


def _get_manager():
    from toolkit import ToolManager
    return ToolManager()


def _composio_client():
    from toolkit.tools.composio import client as composio
    return composio


class SaveRequest(BaseModel):
    enabled: bool
    config: dict = {}


class TestRequest(BaseModel):
    config: dict


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@router.get("")
async def list_tools():
    pool = await get_pool()
    manager = _get_manager()
    states = await manager.list_states(pool)
    return {"tools": [s.model_dump() for s in states]}


@router.get("/{slug}")
async def get_tool(slug: str):
    pool = await get_pool()
    manager = _get_manager()
    state = await manager.get_state(pool, slug)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Unknown tool: {slug}")
    return state.model_dump()


@router.put("/{slug}")
async def save_tool(slug: str, body: SaveRequest):
    pool = await get_pool()
    manager = _get_manager()
    state = await manager.get_state(pool, slug)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Unknown tool: {slug}")
    await manager.save(pool, slug, body.enabled, body.config)
    return {"saved": True, "slug": slug, "enabled": body.enabled}


@router.post("/{slug}/test")
async def test_tool(slug: str, body: TestRequest):
    manager = _get_manager()
    from toolkit import get as _get_cls
    if _get_cls(slug) is None:
        raise HTTPException(status_code=404, detail=f"Unknown tool: {slug}")
    result = await manager.test(slug, body.config)
    return result


# ------------------------------------------------------------------ #
# Composio managed-OAuth connect flow (no credentials pasted)         #
# ------------------------------------------------------------------ #

@router.post("/{slug}/connect")
async def connect_tool(slug: str):
    """Initiate a Composio managed-OAuth connection; return the hosted OAuth URL."""
    pool = await get_pool()
    manager = _get_manager()
    if await manager.get_state(pool, slug) is None:
        raise HTTPException(status_code=404, detail=f"Unknown tool: {slug}")
    composio = _composio_client()
    if not composio.is_available():
        raise HTTPException(status_code=503, detail="Composio not configured (set COMPOSIO_API_KEY)")
    try:
        result = composio.initiate_connection(slug, COMPOSIO_REDIRECT_URL)
    except composio.ComposioUnavailable as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    # Persist the pending connection id (disabled until the OAuth completes).
    await manager.save(pool, slug, enabled=False, config={
        "connection_id": result["connection_id"],
        "connected": False,
    })
    return {"redirect_url": result["redirect_url"], "connection_id": result["connection_id"]}


@router.get("/{slug}/connection")
async def tool_connection(slug: str):
    """Poll the Composio connection status; activate the tool once authorised."""
    pool = await get_pool()
    manager = _get_manager()
    state = await manager.get_state(pool, slug)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Unknown tool: {slug}")

    conn_id = (state.config or {}).get("connection_id")
    if not conn_id:
        return {"connected": False, "status": "not_started"}

    composio = _composio_client()
    if not composio.is_available():
        raise HTTPException(status_code=503, detail="Composio not configured")
    try:
        status = composio.connection_status(conn_id)
    except composio.ComposioUnavailable as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    if status["connected"] and not state.enabled:
        # First time we see it active: enable, register inbound triggers, sync.
        triggers = composio.enable_triggers(slug, conn_id)
        await manager.save(pool, slug, enabled=True, config={
            "connection_id": conn_id,
            "account_id": status["account_id"],
            "connected": True,
            "triggers": triggers,
        })
        await manager.record_sync(pool, slug)

    return {"connected": status["connected"], "status": status["status"]}


@router.post("/{slug}/disconnect")
async def disconnect_tool(slug: str):
    """Disable a Composio tool locally (keeps the row, clears connected flag)."""
    pool = await get_pool()
    manager = _get_manager()
    state = await manager.get_state(pool, slug)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Unknown tool: {slug}")
    await manager.save(pool, slug, enabled=False, config={
        **(state.config or {}),
        "connected": False,
    })
    return {"slug": slug, "connected": False}


@router.post("/{slug}/sync")
async def sync_tool(slug: str):
    """Re-trigger the push dispatch for the latest diagnostic data of every project."""
    pool = await get_pool()
    manager = _get_manager()
    state = await manager.get_state(pool, slug)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Unknown tool: {slug}")
    if not state.enabled:
        raise HTTPException(status_code=400, detail="Tool is not enabled")
    if state.direction == "pull":
        return {"synced": False, "message": "Pull tools enrich data at diagnostic time — run a diagnostic to refresh"}

    # Fetch the most recent diagnostic result across all projects
    rows = await pool.fetch(
        """
        SELECT p.id::text AS project_id, p.profile,
               array_agg(s.score_name || ':' || s.score::text ORDER BY s.score_name) AS scores,
               dh.blockers
          FROM profiles p
          JOIN score_snapshots s ON s.project_id = p.id
          JOIN LATERAL (
              SELECT blockers FROM diagnostic_history
               WHERE project_id = p.id
               ORDER BY created_at DESC LIMIT 1
          ) dh ON TRUE
         WHERE p.state = 'EXISTING'
         GROUP BY p.id, p.profile, dh.blockers
        """
    )

    synced_projects = 0
    for row in rows:
        project_id = row["project_id"]
        profile = row["profile"]
        if isinstance(profile, str):
            profile = json.loads(profile or "{}")
        scores = {}
        for token in (row["scores"] or []):
            name, _, val = token.partition(":")
            try:
                scores[name] = float(val)
            except ValueError:
                pass
        blockers = row["blockers"]
        if isinstance(blockers, str):
            blockers = json.loads(blockers or "[]")

        await manager.dispatch_diagnostic(pool, project_id, profile, scores, blockers, None)
        synced_projects += 1

    return {"synced": True, "slug": slug, "projects_synced": synced_projects}
